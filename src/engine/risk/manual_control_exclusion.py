"""Operator-controlled stock manual management exclusion.

This guard stops bot control for explicitly excluded symbols so the operator
can manage them manually.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from src.utils.constants import DATA_DIR

EXCLUDED_CODES_ENV = "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES"
EXCLUDED_CODES_FILE_ENV = "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE"
LEGACY_WATCH_EXCLUDED_CODES_ENV = "KORSTOCKSCAN_WATCH_EXCLUDED_CODES"
LEGACY_WATCH_EXCLUDED_CODES_FILE_ENV = "KORSTOCKSCAN_WATCH_EXCLUDED_CODES_FILE"
DEFAULT_EXCLUDED_CODES_FILE = DATA_DIR / "config" / "manual_control_excluded_codes.txt"

_CODE_TOKEN_RE = re.compile(r"[,\s;]+")
_COMMENT_RE = re.compile(r"(?:#|//).*$")
_AUTO_EXCLUSION_SOURCES = frozenset(
    {
        "auto_open_loss",
        "auto_scale_in_qty_guard_block",
        "auto_hard_stop_handoff",
    }
)
_MANUAL_OPERATOR_EXCLUSION_SOURCES = frozenset({"manual_operator"})
_MACHINE_OWNER_SCOPE_SOURCES = frozenset({"machine_owner_scope"})
LEGACY_MACHINE_OWNER_SCOPE_LABELS = {
    "002900": "tym_low_price_two_leg_owner",
    "005930": "samsung_electronics",
    "006800": "mirae_asset_low_price_two_leg_owner",
    "010140": "samsung_heavy_low_price_two_leg_owner",
    "015760": "kepco_low_price_two_leg_owner",
    "017670": "sk_telecom_low_price_two_leg_owner",
    "028050": "samsung_ea_low_price_two_leg_owner",
    "028670": "fan_ocean_low_price_two_leg_owner",
    "034020": "doosan_widget_and_episode_independent_owners",
    "035720": "kakao_low_price_two_leg_owner",
    "042660": "hanwha_widget_and_episode_independent_owners",
    "079160": "cj_cgv_low_price_two_leg_owner",
    "080220": "jeju_semiconductor_low_price_two_leg_owner",
    "105630": "hanse_low_price_two_leg_owner",
    "111770": "youngone_low_price_two_leg_owner",
    "137310": "sd_biosensor_low_price_two_leg_owner",
    "181710": "nhn_low_price_two_leg_owner",
    "475150": "sk_eternix_low_price_two_leg_owner",
}
_FILE_CACHE = {
    "path": None,
    "mtime_ns": None,
    "codes": frozenset(),
}
_WRITE_LOCK = threading.RLock()


@dataclass(frozen=True)
class ManualControlExclusionDecision:
    excluded: bool
    code: str
    reason: str
    source: str

    def as_log_fields(self) -> dict[str, object]:
        return {
            "manual_control_exclusion_applied": self.excluded,
            "manual_control_exclusion_code": self.code
            or "not_applicable_manual_control_exclusion_code",
            "manual_control_exclusion_reason": self.reason
            or "not_applicable_manual_control_exclusion_reason",
            "manual_control_exclusion_source": self.source
            or "not_applicable_manual_control_exclusion_source",
            "metric_role": "operator_runtime_guard",
            "decision_authority": "operator_manual_control_exclusion_no_bot_action",
            "window_policy": "intraday_operator_control",
            "sample_floor": "not_applicable_operator_guard",
            "primary_decision_metric": "operator_manual_control_excluded_symbol_match",
            "source_quality_gate": "not_applicable_operator_config",
            "runtime_effect": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": (
                "bot_buy_order,bot_sell_order,bot_cancel_order,bot_scale_in_order,"
                "score_threshold_change,provider_route_change,quantity_or_cap_change,"
                "broker_guard_relaxation,real_execution_quality_approval"
            ),
        }


@dataclass(frozen=True)
class ManualControlExclusionRemoval:
    removed: bool
    code: str
    reason: str
    source: str


def normalize_manual_control_exclusion_code(value: object) -> str:
    raw = str(value or "").strip().upper()
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return digits[-6:].zfill(6)
    return raw


def _split_codes(raw: str) -> Iterable[str]:
    for token in _CODE_TOKEN_RE.split(str(raw or "")):
        code = normalize_manual_control_exclusion_code(token)
        if code:
            yield code


def _env_codes() -> frozenset[str]:
    return frozenset(
        (
            *_split_codes(os.getenv(EXCLUDED_CODES_ENV, "")),
            *_split_codes(os.getenv(LEGACY_WATCH_EXCLUDED_CODES_ENV, "")),
        )
    )


def _file_path() -> Path:
    raw_path = str(
        os.getenv(EXCLUDED_CODES_FILE_ENV, "")
        or os.getenv(LEGACY_WATCH_EXCLUDED_CODES_FILE_ENV, "")
        or ""
    ).strip()
    return Path(raw_path).expanduser() if raw_path else DEFAULT_EXCLUDED_CODES_FILE


def _invalidate_file_cache() -> None:
    _FILE_CACHE.update({"path": None, "mtime_ns": None, "codes": frozenset()})


def _sanitize_append_comment(value: object) -> str:
    text = re.sub(r"[\r\n#]+", " ", str(value or "")).strip()
    return "".join(ch if 32 <= ord(ch) < 127 else "_" for ch in text)[:160]


def _split_line_comment(line: str) -> tuple[str, str]:
    match = _COMMENT_RE.search(line)
    if not match:
        return line, ""
    return line[: match.start()], line[match.start() :]


def _auto_exclusion_source_from_comment(comment: object) -> str:
    text = str(comment or "").strip()
    if text.startswith("#"):
        text = text[1:].strip()
    elif text.startswith("//"):
        text = text[2:].strip()
    source = text.split(maxsplit=1)[0].lower() if text else ""
    return source if source in _AUTO_EXCLUSION_SOURCES else ""


def _manual_operator_exclusion_source_from_comment(comment: object) -> str:
    text = str(comment or "").strip()
    if text.startswith("#"):
        text = text[1:].strip()
    elif text.startswith("//"):
        text = text[2:].strip()
    source = text.split(maxsplit=1)[0].lower() if text else ""
    return source if source in _MANUAL_OPERATOR_EXCLUSION_SOURCES else ""


def _machine_owner_scope_source_from_comment(comment: object) -> str:
    text = str(comment or "").strip()
    if text.startswith("#"):
        text = text[1:].strip()
    elif text.startswith("//"):
        text = text[2:].strip()
    source = text.split(maxsplit=1)[0].lower() if text else ""
    return source if source in _MACHINE_OWNER_SCOPE_SOURCES else ""


def _current_machine_owner_scope_source_from_row(code: object, comment: object) -> str:
    """Recognize only the exact reviewed current machine-scope marker."""

    norm_code = normalize_manual_control_exclusion_code(code)
    label = LEGACY_MACHINE_OWNER_SCOPE_LABELS.get(norm_code)
    if not label:
        return ""
    body = str(comment or "").lstrip("#/ ").strip()
    return "machine_owner_scope" if body == f"machine_owner_scope {label}" else ""


def _legacy_machine_owner_scope_source_from_row(code: object, comment: object) -> str:
    """Recognize only the exact reviewed pre-migration machine marker."""

    norm_code = normalize_manual_control_exclusion_code(code)
    label = LEGACY_MACHINE_OWNER_SCOPE_LABELS.get(norm_code)
    if not label:
        return ""
    body = str(comment or "").lstrip("#/ ").strip()
    return "legacy_machine_owner_scope" if body == f"manual_operator {label}" else ""


def _load_file_codes(path: Path) -> frozenset[str]:
    codes: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return frozenset()
    except OSError:
        return frozenset()
    for line in text.splitlines():
        uncommented = _COMMENT_RE.sub("", line)
        codes.update(_split_codes(uncommented))
    return frozenset(codes)


def _file_exclusion_snapshot(code: object) -> tuple[frozenset[str], str]:
    """Classify matching rows from one consistent file read."""

    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return frozenset(), ""
    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return frozenset(), ""
        except OSError as exc:
            return frozenset(), type(exc).__name__
    kinds: set[str] = set()
    for line in original_text.splitlines():
        uncommented, comment = _split_line_comment(line)
        codes = list(_split_codes(uncommented))
        if norm_code not in codes:
            continue
        if _auto_exclusion_source_from_comment(comment):
            kinds.add("auto")
        elif len(codes) == 1 and _current_machine_owner_scope_source_from_row(
            norm_code, comment
        ):
            kinds.add("machine_owner_scope")
        elif len(codes) == 1 and _legacy_machine_owner_scope_source_from_row(
            norm_code, comment
        ):
            kinds.add("legacy_machine_owner_scope")
        elif _manual_operator_exclusion_source_from_comment(comment):
            kinds.add("manual_operator")
        else:
            kinds.add("generic_veto")
    # After conversion, even a user row reusing an old machine label is a
    # manual veto. It must never be eligible for a second migration.
    if "machine_owner_scope" in kinds and "legacy_machine_owner_scope" in kinds:
        kinds.discard("legacy_machine_owner_scope")
        kinds.add("manual_operator")
    return frozenset(kinds), ""


def _file_exclusion_kinds(code: object) -> frozenset[str]:
    """Classify every matching file row without collapsing duplicate sources."""

    return _file_exclusion_snapshot(code)[0]


def _file_codes() -> frozenset[str]:
    path = _file_path()
    try:
        stat = path.stat()
        mtime_ns = stat.st_mtime_ns
    except FileNotFoundError:
        mtime_ns = None
    except OSError:
        mtime_ns = None
    cache_path = _FILE_CACHE.get("path")
    if cache_path == path and _FILE_CACHE.get("mtime_ns") == mtime_ns:
        return _FILE_CACHE["codes"]
    codes = _load_file_codes(path) if mtime_ns is not None else frozenset()
    _FILE_CACHE.update({"path": path, "mtime_ns": mtime_ns, "codes": codes})
    return codes


def configured_manual_control_exclusion_codes() -> frozenset[str]:
    return frozenset((*_file_codes(), *_env_codes()))


def manual_control_auto_exclusion_source(code: object) -> str:
    """Return the file-backed auto registration source for a symbol, if any."""
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ""
    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
    for line in original_text.splitlines():
        uncommented, comment = _split_line_comment(line)
        if norm_code not in set(_split_codes(uncommented)):
            continue
        auto_source = _auto_exclusion_source_from_comment(comment)
        if auto_source:
            return auto_source
    return ""


def manual_control_operator_exclusion_source(code: object) -> str:
    """Return the explicit operator source that owns an exclusion, if any.

    Environment-configured exclusions are explicit operator configuration.
    File-backed exclusions qualify only when their comment starts with the
    protected ``manual_operator`` marker and is not an exact reviewed legacy
    machine-scope row. Automatic loss/safety and transitional machine markers
    therefore cannot silently transfer manual order ownership.
    """
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ""
    explicit_env_codes = frozenset(_split_codes(os.getenv(EXCLUDED_CODES_ENV, "")))
    if norm_code in explicit_env_codes:
        return EXCLUDED_CODES_ENV
    current_machine_scope = bool(machine_owner_scope_source(norm_code))
    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
    for line in original_text.splitlines():
        uncommented, comment = _split_line_comment(line)
        if norm_code not in set(_split_codes(uncommented)):
            continue
        if not current_machine_scope and _legacy_machine_owner_scope_source_from_row(
            norm_code, comment
        ):
            continue
        if _manual_operator_exclusion_source_from_comment(comment):
            return "manual_operator"
    return ""


def machine_owner_scope_source(code: object) -> str:
    """Return the non-veto widget/episode ownership-scope marker, if present."""

    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ""
    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
    for line in original_text.splitlines():
        uncommented, comment = _split_line_comment(line)
        codes = list(_split_codes(uncommented))
        if len(codes) != 1 or codes[0] != norm_code:
            continue
        if _current_machine_owner_scope_source_from_row(norm_code, comment):
            return "machine_owner_scope"
    return ""


def legacy_machine_owner_scope_source(code: object) -> str:
    """Return exact reviewed legacy scope without weakening the main veto."""

    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ""
    if machine_owner_scope_source(norm_code):
        return ""
    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
    for line in original_text.splitlines():
        uncommented, comment = _split_line_comment(line)
        codes = list(_split_codes(uncommented))
        if len(codes) != 1 or codes[0] != norm_code:
            continue
        source = _legacy_machine_owner_scope_source_from_row(norm_code, comment)
        if source:
            return source
    return ""


def migrate_legacy_machine_owner_scope_markers(
    expected_legacy_labels: Mapping[str, str],
) -> dict[str, object]:
    """Atomically separate known legacy machine scope from operator veto rows.

    Only an exact ``CODE # manual_operator LABEL`` row supplied by the caller is
    migrated. Any other manual/operator row is preserved as an explicit veto.
    The migration is safe to retry and is intended for the quiescent PREOPEN
    owner-policy producer, never an active trading process.
    """

    expected = {
        normalize_manual_control_exclusion_code(code): str(label or "").strip()
        for code, label in expected_legacy_labels.items()
        if normalize_manual_control_exclusion_code(code) and str(label or "").strip()
    }
    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
            original_mode = path.stat().st_mode & 0o777
        except FileNotFoundError:
            original_text = ""
            original_mode = 0o600
        before_sha256 = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
        current_markers = set()
        for line in original_text.splitlines():
            uncommented, comment = _split_line_comment(line)
            codes = list(_split_codes(uncommented))
            if len(codes) == 1 and _current_machine_owner_scope_source_from_row(
                codes[0], comment
            ):
                current_markers.add(codes[0])
        output_lines: list[str] = []
        migrated: list[str] = []
        already_migrated: list[str] = []
        preserved_operator_vetoes: list[str] = []
        for line in original_text.splitlines():
            uncommented, comment = _split_line_comment(line)
            codes = list(_split_codes(uncommented))
            if len(codes) != 1 or codes[0] not in expected:
                output_lines.append(line)
                continue
            code = codes[0]
            label = expected[code]
            body = str(comment or "").lstrip("#/ ").strip()
            if body == f"manual_operator {label}" and code not in current_markers:
                output_lines.append(f"{code} # machine_owner_scope {label}")
                migrated.append(code)
                continue
            if body == f"machine_owner_scope {label}":
                output_lines.append(line)
                already_migrated.append(code)
                continue
            if _manual_operator_exclusion_source_from_comment(comment):
                preserved_operator_vetoes.append(code)
            output_lines.append(line)

        suffix = "\n" if output_lines and original_text.endswith("\n") else ""
        updated_text = "\n".join(output_lines) + suffix
        if updated_text != original_text:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(updated_text)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary, original_mode)
                os.replace(temporary, path)
                directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
            _invalidate_file_cache()
        after_sha256 = hashlib.sha256(updated_text.encode("utf-8")).hexdigest()

    return {
        "schema": "machine_owner_scope_marker_migration_v1",
        "path": str(path.resolve()),
        "migrated_symbols": sorted(set(migrated)),
        "already_migrated_symbols": sorted(set(already_migrated)),
        "preserved_operator_veto_symbols": sorted(set(preserved_operator_vetoes)),
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "changed": before_sha256 != after_sha256,
        "runtime_effect": False,
    }


def evaluate_manual_control_exclusion(code: object) -> ManualControlExclusionDecision:
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionDecision(False, "", "", "")
    env_codes = _env_codes()
    if norm_code in env_codes:
        return ManualControlExclusionDecision(
            True,
            norm_code,
            "operator_manual_control_excluded_symbol",
            EXCLUDED_CODES_ENV,
        )
    file_codes = _file_codes()
    if norm_code in file_codes:
        return ManualControlExclusionDecision(
            True,
            norm_code,
            "operator_manual_control_excluded_symbol",
            str(_file_path()),
        )
    return ManualControlExclusionDecision(False, norm_code, "", "")


def evaluate_main_bot_control_exclusion(
    code: object,
    *,
    target_date: object = None,
    new_entry: bool = True,
) -> ManualControlExclusionDecision:
    """Resolve the main-bot veto without weakening manual ownership by default.

    Explicit operator and automatic safety exclusions are unconditional vetoes.
    Only the separate ``machine_owner_scope`` compatibility marker may be
    replaced by an exact-date, activated coexistence policy. Policy
    parse/hash/date errors fail closed as an exclusion.
    """

    norm_code = normalize_manual_control_exclusion_code(code)
    exclusion_path = _file_path()
    file_kinds, file_read_error = _file_exclusion_snapshot(norm_code)
    if file_read_error:
        return ManualControlExclusionDecision(
            True,
            norm_code,
            f"manual_control_exclusion_file_fail_closed:{file_read_error}",
            str(exclusion_path),
        )
    env_veto = bool(norm_code and norm_code in _env_codes())
    decision = ManualControlExclusionDecision(
        bool(env_veto or file_kinds),
        norm_code,
        "operator_manual_control_excluded_symbol" if env_veto or file_kinds else "",
        EXCLUDED_CODES_ENV if env_veto else str(exclusion_path) if file_kinds else "",
    )
    machine_scope_source = "machine_owner_scope" in file_kinds
    non_scope_file_veto = bool(file_kinds - {"machine_owner_scope"})
    if decision.excluded and (env_veto or non_scope_file_veto):
        # Explicit user control and automatic loss/hard-safety handoffs always
        # outrank a same-symbol coexistence policy.
        return decision
    if decision.excluded and not machine_scope_source:
        # Generic file/env vetoes are also fail-closed even when their comment
        # predates the structured provenance markers.
        return decision
    try:
        from src.trading.config.symbol_owner_policy import (
            SymbolOwnerPolicyError,
            resolve_symbol_owner_policy,
        )

        owner_policy = resolve_symbol_owner_policy(code, target_date=target_date)
    except (SymbolOwnerPolicyError, OSError, ValueError) as exc:
        return ManualControlExclusionDecision(
            True,
            decision.code,
            f"symbol_owner_policy_fail_closed:{type(exc).__name__}",
            decision.source,
        )
    if owner_policy.symbol_selected:
        if owner_policy.owner_allowed("main_scalping", new_entry=new_entry):
            try:
                if owner_policy.coexistence_enabled:
                    from src.trading.order.owner_custody_registry import (
                        OwnerRegistryError,
                        default_order_owner_registry,
                    )

                    registry = default_order_owner_registry()
                    if not registry.decision_activation_matches(owner_policy):
                        return ManualControlExclusionDecision(
                            True,
                            decision.code,
                            "coexistence_policy_activation_missing_or_mismatched",
                            owner_policy.source_path,
                        )
            except OwnerRegistryError as exc:
                return ManualControlExclusionDecision(
                    True,
                    decision.code,
                    f"owner_registry_fail_closed:{type(exc).__name__}",
                    owner_policy.source_path,
                )
            return ManualControlExclusionDecision(
                False,
                decision.code,
                (
                    "exact_date_coexistence_policy_allows_main_bot"
                    if owner_policy.coexistence_enabled
                    else "exact_date_owner_policy_allows_main_bot"
                ),
                owner_policy.source_path,
            )
        return ManualControlExclusionDecision(
            True,
            decision.code,
            (
                "exact_date_owner_policy_blocks_main_bot_entry"
                if new_entry
                else "exact_date_owner_policy_blocks_main_bot_custody"
            ),
            owner_policy.source_path,
        )
    return decision


def independent_machine_ownership_source(
    code: object,
    *,
    owner: str,
    target_date: object = None,
    new_entry: bool = True,
) -> str:
    """Return the exact ownership authority for an independent machine.

    Legacy deployments use the non-veto ``machine_owner_scope`` marker.
    Explicit ``manual_operator`` rows belong only to the main-bot operator veto
    and never grant a machine order authority. A coexistence deployment may
    replace the machine marker only when the exact-date policy authorizes the
    requested machine owner and confirms migration.
    PREOPEN custody preflight passes ``new_entry=False`` so an exit-only
    rollback can keep reconciling and closing already-owned positions while
    the runtime entry gate still rejects every new BUY.
    """

    legacy = machine_owner_scope_source(code) or legacy_machine_owner_scope_source(code)
    try:
        from src.trading.config.symbol_owner_policy import (
            SymbolOwnerPolicyError,
            resolve_symbol_owner_policy,
        )

        owner_policy = resolve_symbol_owner_policy(code, target_date=target_date)
    except (SymbolOwnerPolicyError, OSError, ValueError):
        return ""
    normalized_owner = str(owner or "").strip().lower()
    if owner_policy.symbol_selected:
        if owner_policy.owner_allowed(normalized_owner, new_entry=new_entry):
            try:
                if owner_policy.coexistence_enabled:
                    from src.trading.order.owner_custody_registry import (
                        OwnerRegistryError,
                        default_order_owner_registry,
                    )

                    registry = default_order_owner_registry()
                    if not registry.decision_activation_matches(owner_policy):
                        return ""
            except OwnerRegistryError:
                return ""
            return (
                f"symbol_owner_policy:{owner_policy.policy_id}:"
                f"{owner_policy.policy_hash}"
            )
        return ""
    return legacy


def add_manual_control_exclusion_code(
    code: object,
    *,
    comment: object = "",
) -> ManualControlExclusionDecision:
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionDecision(
            False, "", "invalid_manual_control_exclusion_code", ""
        )

    suffix = _sanitize_append_comment(comment)
    if _machine_owner_scope_source_from_comment(suffix) or (
        _legacy_machine_owner_scope_source_from_row(norm_code, suffix)
    ):
        return ManualControlExclusionDecision(
            False, norm_code, "manual_control_registration_requires_veto_source", ""
        )
    requested_auto_source = _auto_exclusion_source_from_comment(suffix)
    requested_manual = bool(_manual_operator_exclusion_source_from_comment(suffix))
    path = _file_path()
    with _WRITE_LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a+", encoding="utf-8") as fp:
                fp.seek(0)
                original_text = fp.read()
                for line in original_text.splitlines():
                    uncommented, existing_comment = _split_line_comment(line)
                    codes = list(_split_codes(uncommented))
                    if norm_code not in codes:
                        continue
                    if len(codes) == 1 and (
                        _current_machine_owner_scope_source_from_row(
                            norm_code, existing_comment
                        )
                        or _legacy_machine_owner_scope_source_from_row(
                            norm_code, existing_comment
                        )
                    ):
                        continue
                    existing_auto = _auto_exclusion_source_from_comment(
                        existing_comment
                    )
                    existing_manual = bool(
                        _manual_operator_exclusion_source_from_comment(existing_comment)
                    )
                    same_source = (
                        existing_auto == requested_auto_source
                        if requested_auto_source
                        else existing_manual if requested_manual else not existing_auto
                    )
                    if same_source:
                        return ManualControlExclusionDecision(
                            True,
                            norm_code,
                            "operator_manual_control_excluded_symbol",
                            str(path),
                        )
                # Persist each veto source independently: releasing an automatic
                # exclusion or an environment override must not erase a later
                # explicit operator registration.
                fp.seek(0, os.SEEK_END)
                if original_text and not original_text.endswith("\n"):
                    fp.write("\n")
                fp.write(f"{norm_code}{f' # {suffix}' if suffix else ''}\n")
                fp.flush()
                os.fsync(fp.fileno())
        except OSError as exc:
            return ManualControlExclusionDecision(
                False,
                norm_code,
                f"manual_control_exclusion_append_failed:{exc.__class__.__name__}",
                str(path),
            )

        _invalidate_file_cache()
    return ManualControlExclusionDecision(
        True,
        norm_code,
        "operator_manual_control_excluded_symbol",
        str(path),
    )


def remove_manual_control_exclusion_code(
    code: object,
    *,
    reason: object = "",
) -> ManualControlExclusionRemoval:
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionRemoval(
            False,
            "",
            "invalid_manual_control_exclusion_code",
            "",
        )

    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_exclusion_file_missing",
                str(path),
            )
        except OSError as exc:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                f"manual_control_exclusion_remove_failed:{exc.__class__.__name__}",
                str(path),
            )

        removed = False
        manual_operator_protected = False
        auto_exclusion_protected = False
        machine_owner_scope_protected = False
        output_lines: list[str] = []
        for line in original_text.splitlines():
            uncommented, comment = _split_line_comment(line)
            codes = list(_split_codes(uncommented))
            if norm_code not in codes:
                output_lines.append(line)
                continue

            if _legacy_machine_owner_scope_source_from_row(norm_code, comment):
                machine_owner_scope_protected = True
                output_lines.append(line)
                continue

            if _manual_operator_exclusion_source_from_comment(comment):
                manual_operator_protected = True
                output_lines.append(line)
                continue

            if _auto_exclusion_source_from_comment(comment):
                auto_exclusion_protected = True
                output_lines.append(line)
                continue

            if _machine_owner_scope_source_from_comment(comment):
                machine_owner_scope_protected = True
                output_lines.append(line)
                continue

            removed = True
            remaining = [item for item in codes if item != norm_code]
            if remaining:
                rebuilt = ",".join(remaining)
                if comment:
                    rebuilt = f"{rebuilt} {comment.strip()}"
                output_lines.append(rebuilt)

        if manual_operator_protected:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_exclusion_manual_operator_protected",
                str(path),
            )

        if auto_exclusion_protected:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_auto_exclusion_average_price_release_required",
                str(path),
            )

        if machine_owner_scope_protected and not removed:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_machine_owner_scope_protected",
                str(path),
            )

        if not removed:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_exclusion_code_not_in_file",
                str(path),
            )

        try:
            suffix = "\n" if output_lines and original_text.endswith("\n") else ""
            path.write_text("\n".join(output_lines) + suffix, encoding="utf-8")
        except OSError as exc:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                f"manual_control_exclusion_remove_failed:{exc.__class__.__name__}",
                str(path),
            )

        _invalidate_file_cache()

    suffix = _sanitize_append_comment(reason)
    return ManualControlExclusionRemoval(
        True,
        norm_code,
        f"manual_control_exclusion_removed{f':{suffix}' if suffix else ''}",
        str(path),
    )


def remove_auto_manual_control_exclusion_code(
    code: object,
    *,
    reason: object = "",
    sources: Iterable[str] | None = None,
) -> ManualControlExclusionRemoval:
    """Remove only file rows carrying a supported ``auto_*`` provenance comment."""
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionRemoval(
            False,
            "",
            "invalid_manual_control_exclusion_code",
            "",
        )
    if norm_code in _env_codes():
        return ManualControlExclusionRemoval(
            False,
            norm_code,
            "manual_control_auto_exclusion_env_override_active",
            EXCLUDED_CODES_ENV,
        )

    selected_sources = (
        _AUTO_EXCLUSION_SOURCES
        if sources is None
        else frozenset(sources) & _AUTO_EXCLUSION_SOURCES
    )
    path = _file_path()
    removed_sources: set[str] = set()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_exclusion_file_missing",
                str(path),
            )
        except OSError as exc:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                f"manual_control_exclusion_remove_failed:{exc.__class__.__name__}",
                str(path),
            )

        output_lines: list[str] = []
        for line in original_text.splitlines():
            uncommented, comment = _split_line_comment(line)
            codes = list(_split_codes(uncommented))
            auto_source = _auto_exclusion_source_from_comment(comment)
            if norm_code not in codes or auto_source not in selected_sources:
                output_lines.append(line)
                continue

            removed_sources.add(auto_source)
            remaining = [item for item in codes if item != norm_code]
            if remaining:
                rebuilt = ",".join(remaining)
                if comment:
                    rebuilt = f"{rebuilt} {comment.strip()}"
                output_lines.append(rebuilt)

        if not removed_sources:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_auto_exclusion_code_not_in_file",
                str(path),
            )

        try:
            suffix = "\n" if output_lines and original_text.endswith("\n") else ""
            path.write_text("\n".join(output_lines) + suffix, encoding="utf-8")
        except OSError as exc:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                f"manual_control_exclusion_remove_failed:{exc.__class__.__name__}",
                str(path),
            )
        _invalidate_file_cache()

    reason_suffix = _sanitize_append_comment(reason)
    source_suffix = ",".join(sorted(removed_sources))
    return ManualControlExclusionRemoval(
        True,
        norm_code,
        (
            f"manual_control_auto_exclusion_removed:{source_suffix}"
            f"{f':{reason_suffix}' if reason_suffix else ''}"
        ),
        str(path),
    )
