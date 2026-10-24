"""Exact-source reader compatibility receipts for auxiliary-only code handoff.

Owned by scalping policy readers, not the machine policy or bootstrap authority.
Receipts attest reviewed v1 parity and retain original artifacts and identities.
"""

from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P

SCHEMA = "auxiliary_reader_compatibility_v1"

# Exact reviewed reader repairs after the formatting-only transition. These
# pairs are comparison authority for frozen contracts, never physical hashes.
REVIEWED_CONTRACT_SOURCE_PAIRS = {
    "src/engine/scalping/reversal_auxiliary_wire.py": (
        (
            "6f3de130bc8ca5670a4588c8c274399f79b68408ed3312523bdbbe7e0018d578",
            "e10a29e96d65e5a00da11bbb5b248b1263fd34a10f8c4bcec39337802c2a021f",
        ),
        "7751d8cbeb4d1fdfe8411aefee2b0adaf25079abb8ebdf5800222b4fe7c42600",
    ),
    "src/engine/scalping/reversal_auxiliary_production_input.py": (
        (
            "ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a",
            "29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003",
        ),
        "324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464",
    ),
}


def _source_generations(source):
    source = Path(source).resolve()
    actual = P.file_hash(source)
    root = Path(__file__).resolve().parents[3]
    try:
        name = source.relative_to(root).as_posix()
    except ValueError:
        return (actual, actual, actual)
    from src.engine.automation.intraday_release_handoff import (
        reviewed_formatting_predecessor,
    )

    pair = REVIEWED_CONTRACT_SOURCE_PAIRS.get(name)
    if pair is not None and actual == pair[1]:
        return (actual, pair[0][1], pair[0][0])
    return (actual, actual, reviewed_formatting_predecessor(name, actual))


def source_matches(expected, source):
    return expected in _source_generations(source)


def contract_matches(expected, actual, sources):
    """Compare frozen code identities without rewriting any contract field."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return False
    if expected == actual:
        return True
    views = [dict(actual) for _ in range(3)]
    for field, source in sources.items():
        generations = _source_generations(source)
        if actual.get(field) != generations[0]:
            return False
        for view, digest in zip(views, generations):
            view[field] = digest
    return expected in views


def path(data_root, bundle, source, new_hashes):
    key = P.digest([bundle["bundle_sha256"], P.file_hash(source), new_hashes])
    return (
        Path(data_root)
        / "runtime/mechanistic_entry_policy/auxiliary/compatibility"
        / (key + ".json")
    )


def validate(data_root, bundle, source, old_hashes, new_hashes):
    from src.engine.scalping import reversal_auxiliary_intraday as I

    target = path(data_root, bundle, source, new_hashes)
    receipt = I.read(target)
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("base_bundle_sha256") != bundle["bundle_sha256"]
        or receipt.get("source_sha256") != P.file_hash(source)
        or receipt.get("old_reader_hashes") != old_hashes
        or receipt.get("new_reader_hashes") != new_hashes
    ):
        raise ValueError("auxiliary_reader_compatibility_invalid")
    original = I.read(source)
    if (
        P.digest(
            original.get("auxiliary_registry_bindings", original.get("bindings", {}))
        )
        != receipt["v1_bindings_sha256"]
    ):
        raise ValueError("auxiliary_reader_binding_evidence_changed")
    evidence = I.read(receipt["evidence_path"])
    if (
        P.file_hash(receipt["evidence_path"]) != receipt["evidence_sha256"]
        or evidence.get("status") != "pass"
        or evidence.get("new_reader_hashes") != new_hashes
        or evidence.get("base_bundle_sha256") != bundle["bundle_sha256"]
        or evidence.get("source_sha256") != receipt["source_sha256"]
        or evidence.get("v1_bindings_sha256") != receipt["v1_bindings_sha256"]
    ):
        raise ValueError("auxiliary_reader_parity_evidence_invalid")
    for item in receipt["frozen_readers"]:
        if P.file_hash(item["path"]) != old_hashes.get(Path(item["path"]).name):
            raise ValueError("auxiliary_frozen_reader_changed")
    if {Path(x["path"]).name for x in receipt["frozen_readers"]} != set(old_hashes):
        raise ValueError("auxiliary_frozen_reader_incomplete")
    return receipt


def issue(
    data_root, bundle, source, old_hashes, new_hashes, *, evidence, frozen_readers
):
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    proof = I.read(evidence)
    body = P.seal(
        dict(
            schema=SCHEMA,
            base_bundle_sha256=bundle["bundle_sha256"],
            source_path=str(Path(source).resolve()),
            source_sha256=P.file_hash(source),
            old_reader_hashes=old_hashes,
            new_reader_hashes=new_hashes,
            v1_bindings_sha256=proof["v1_bindings_sha256"],
            evidence_path=str(Path(evidence).resolve()),
            evidence_sha256=P.file_hash(evidence),
            frozen_readers=frozen_readers,
            actual_pid_consumed=False,
            actual_order_submitted=False,
        )
    )
    dest = path(data_root, bundle, source, new_hashes)
    if dest.exists() and I.read(dest) != body:
        raise ValueError("auxiliary_compatibility_immutable_conflict")
    N._atomic_write_json(dest, body)
    validate(data_root, bundle, source, old_hashes, new_hashes)
    return body
