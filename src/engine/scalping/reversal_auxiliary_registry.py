"""Immutable reviewed auxiliary prompt definitions; no policy activation authority.

Owned by scalping, outside historical v5 module pins. Existing typed projectors
and validators retain their original bytes and contract.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from src.engine.scalping import reversal_operating_auxiliary as A
from src.engine.scalping import continuous_reversal_postclose as P

SCHEMA = "main_auxiliary_prompt_registry_v1"
SCHEMA_V2 = "main_auxiliary_prompt_registry_v2"
IDENTITY_SCHEMA = "entry_auxiliary_policy_identity_v1"


def identity_json(value):
    """The async carrier freezes nested maps; log canonical JSON, never repr."""
    from collections.abc import Mapping
    import json

    def thaw(item):
        if isinstance(item, Mapping):
            return {k: thaw(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [thaw(v) for v in item]
        return item

    if isinstance(value, str):
        value = json.loads(value)
    return json.dumps(
        thaw(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def response_contract_shape(value, path=()):
    """Exclude request-local citation aliases while retaining risk/schema semantics."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            logical_fact = any(
                p in {"supporting_fact_ids", "contradicting_fact_ids", "fact_ids"}
                for p in path
            )
            wire_fact = (
                path[-2:] == ("properties", "fact")
                and isinstance(item, list)
                and bool(item)
                and all(
                    isinstance(v, str) and re.fullmatch(r"f[1-9][0-9]*", v)
                    for v in item
                )
            )
            result[key] = (
                ["SOURCE_FACT_ID"]
                if key == "enum" and (logical_fact or wire_fact)
                else response_contract_shape(item, path + (key,))
            )
        return result
    if isinstance(value, list):
        return [response_contract_shape(v, path) for v in value]
    return value


def timing_compatibility_identity(value):
    """Derive a research equivalence key; preserve the original identity/receipt."""
    value = validate_identity(value)
    semantic = copy.deepcopy(value["semantic"])
    if "reversal_auxiliary_wire.py" in semantic["projector_validator_sha256"]:
        semantic["response_contract"] = response_contract_shape(
            semantic.get("response_contract")
        )
    return P.digest(semantic)


def provider_identity(payload, context):
    """Freeze actual request semantics without request-specific fact enums.

    Dynamic schema bytes and input stay in provenance. Projector/validator code
    owns the allowlist semantics; registry research notes are not policy inputs.
    """
    from src.engine.scalping.mechanistic_entry_runtime_policy import (
        _source_hash,
        _signature,
    )

    modules = {
        "continuous_reversal_policy_v1": "reversal_auxiliary_contract",
        "continuous_reversal_policy_v2": "reversal_auxiliary_phases",
        "continuous_reversal_policy_v3": "reversal_auxiliary_phases",
        "continuous_reversal_policy_v4": "reversal_path_auxiliary",
        "continuous_reversal_policy_v5": "reversal_operating_auxiliary",
        "continuous_reversal_policy_v6": "reversal_extended_union",
    }
    version = context.get("policy_version")
    if version not in modules or not isinstance(payload.get("instructions"), str):
        raise ValueError("auxiliary_identity_definition_missing")
    paths = [
        Path(__file__).with_name(name + ".py")
        for name in sorted(
            set(
                (
                    modules[version],
                    "reversal_auxiliary_contract",
                    "continuous_reversal_policy",
                )
            )
        )
    ]
    if context.get("registry_sha256"):
        paths.append(Path(__file__).with_name("reversal_auxiliary_wire.py"))
    semantic = dict(
        schema=IDENTITY_SCHEMA,
        provider="openai",
        prompt=payload["instructions"],
        model=payload["model"],
        response_contract=response_contract_shape(payload.get("text")),
        options={
            k: payload[k]
            for k in ("max_output_tokens", "temperature", "reasoning")
            if k in payload
        },
        input_contract=version,
        normalizer_version="continuous_reversal_effective_screen_v1",
        projector_validator_sha256={
            p.name: _source_hash(str(p), _signature(p)) for p in paths
        },
    )
    if "production_input_contract" in context:
        from src.engine.scalping import reversal_auxiliary_production_input as M

        semantic["production_input_contract"] = copy.deepcopy(
            M.validate(context["production_input_contract"])
        )
    identity = dict(
        schema=IDENTITY_SCHEMA,
        semantic=semantic,
        identity_sha256=P.digest(semantic),
        provenance={
            k: context.get(k)
            for k in ("registry_sha256", "overlay_sha256", "bundle_sha256")
        },
    )
    identity["provenance"].update(
        request_payload_sha256=P.digest(payload),
        response_schema_sha256=P.digest(payload.get("text")),
    )
    return identity


def validate_identity(value):
    if (
        not isinstance(value, dict)
        or value.get("schema") != IDENTITY_SCHEMA
        or not isinstance(value.get("semantic"), dict)
        or value["semantic"].get("schema") != IDENTITY_SCHEMA
        or value.get("identity_sha256") != P.digest(value["semantic"])
        or not isinstance(value.get("provenance"), dict)
    ):
        raise ValueError("auxiliary_identity_contract_invalid")
    semantic = value["semantic"]
    provenance = value["provenance"]
    if (
        semantic.get("provider") != "openai"
        or not isinstance(semantic.get("prompt"), str)
        or not semantic["prompt"].isascii()
        or not semantic["prompt"].strip()
        or not isinstance(semantic.get("model"), str)
        or not semantic["model"]
        or not isinstance(semantic.get("options"), dict)
        or semantic.get("normalizer_version")
        != "continuous_reversal_effective_screen_v1"
        or not isinstance(semantic.get("projector_validator_sha256"), dict)
        or not semantic["projector_validator_sha256"]
        or any(
            not re.fullmatch("[a-f0-9]{64}", str(v))
            for v in semantic["projector_validator_sha256"].values()
        )
        or any(
            not re.fullmatch("[a-f0-9]{64}", str(provenance.get(k)))
            for k in ("request_payload_sha256", "response_schema_sha256")
        )
    ):
        raise ValueError("auxiliary_identity_definition_invalid")
    if "production_input_contract" in semantic:
        from src.engine.scalping import reversal_auxiliary_production_input as M

        M.validate(semantic["production_input_contract"])
    return value


def projector(version=None):
    if version is None or version == A.VERSION:
        return A
    from src.engine.scalping import reversal_extended_union as E

    if version == E.VERSION:
        return E
    raise ValueError("auxiliary_registry_input_version_unsupported")


def projector_hash(version=None):
    from src.engine.scalping.mechanistic_entry_runtime_policy import (
        _source_hash,
        _signature,
    )

    path = Path(projector(version).__file__)
    return _source_hash(str(path), _signature(path))


def directory(data_root):
    return Path(data_root) / "runtime/mechanistic_entry_policy/auxiliary/registry"


def definition(
    arm,
    *,
    prompt=None,
    hypothesis="Historical registered wording",
    development_keys=(),
    input_version=None,
):
    A = projector(input_version)
    binding = A.binding(arm)
    body = dict(
        schema=SCHEMA,
        base_arm=arm,
        prompt=prompt if prompt is not None else A.PROMPT + A.ARM_SUFFIXES[arm],
        hypothesis=hypothesis,
        development_keys=sorted(set(development_keys)),
        input_version=A.VERSION,
        validator_version=A.VERSION,
        response_schema_version=A.VERSION,
        provider="openai",
        model="gpt-5.4-nano",
        max_output_tokens=1024,
        reasoning_effort="none",
        projector_sha256=projector_hash(A.VERSION),
    )
    body["registry_sha256"] = P.digest(body)
    validate(body)
    return body


def validate(value):
    A = (
        projector(value.get("input_version"))
        if isinstance(value, dict)
        else globals()["A"]
    )
    if (
        not isinstance(value, dict)
        or value.get("schema") not in {SCHEMA, SCHEMA_V2}
        or value.get("registry_sha256")
        != P.digest({k: v for k, v in value.items() if k != "registry_sha256"})
        or value.get("base_arm") not in A.V1.ARMS
        or value.get("input_version") != A.VERSION
        or value.get("validator_version") != A.VERSION
        or value.get("response_schema_version")
        != (
            A.VERSION
            if value.get("schema") == SCHEMA
            else "auxiliary_compact_citations_v1"
        )
        or value.get("projector_sha256") != projector_hash(A.VERSION)
        or value.get("provider") != "openai"
        or value.get("model") != "gpt-5.4-nano"
        or value.get("max_output_tokens") != 1024
        or value.get("reasoning_effort") != "none"
        or not isinstance(value.get("prompt"), str)
        or not value["prompt"].strip()
        or not value["prompt"].isascii()
        or len(value["prompt"]) > 16000
        or not isinstance(value.get("hypothesis"), str)
        or not value["hypothesis"].strip()
        or not isinstance(value.get("development_keys"), list)
        or any(not isinstance(k, str) for k in value["development_keys"])
    ):
        raise ValueError("auxiliary_registry_contract_invalid")
    if value["schema"] == SCHEMA_V2:
        from src.engine.scalping import reversal_auxiliary_wire as W

        if (
            value.get("wire_contract") != W.contract()
            or value["input_version"] != "continuous_reversal_union_auxiliary_v3"
            or value.get("temperature_policy") != "omit"
            or value.get("logical_response_schema_version") != A.VERSION
            or not re.fullmatch(
                "[a-f0-9]{64}", value.get("research_registry_sha256", "")
            )
            or not isinstance(value.get("research_wire_contract"), dict)
        ):
            raise ValueError("auxiliary_registry_wire_contract_invalid")
    if (
        "production_input_contract" in value
        or "production_parent_registry_sha256" in value
    ):
        from src.engine.scalping import reversal_auxiliary_production_input as M

        if (
            value["schema"] != SCHEMA_V2
            or value["input_version"] != M.U.VERSION
            or not re.fullmatch(
                "[a-f0-9]{64}", str(value.get("production_parent_registry_sha256"))
            )
        ):
            raise ValueError("auxiliary_registry_production_input_invalid")
        M.validate(value.get("production_input_contract"))
    return value


def compact_definition(research_value, *, research_wire_contract):
    validate(research_value)
    if research_value["schema"] != SCHEMA:
        raise ValueError("auxiliary_research_registry_version_invalid")
    from src.engine.scalping import reversal_auxiliary_wire as W

    body = copy.deepcopy(research_value)
    body.update(
        schema=SCHEMA_V2,
        response_schema_version=W.VERSION,
        logical_response_schema_version=research_value["input_version"],
        wire_contract=W.contract(),
        temperature_policy="omit",
        research_registry_sha256=research_value["registry_sha256"],
        research_wire_contract=copy.deepcopy(research_wire_contract),
    )
    body.pop("registry_sha256")
    body["registry_sha256"] = P.digest(body)
    return validate(body)


def register(data_root, value):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _atomic_write_json

    validate(value)
    path = directory(data_root) / (value["registry_sha256"] + ".json")
    if path.exists():
        if P.digest(__import__("json").loads(path.read_text())) != P.digest(value):
            raise ValueError("auxiliary_registry_immutable_conflict")
    else:
        _atomic_write_json(path, value)
    return value["registry_sha256"]


def production_definition(compact_value, *, scope_ids):
    """Build a separate scoped opt-in; never rewrite or register its parent."""
    validate(compact_value)
    if (
        compact_value["schema"] != SCHEMA_V2
        or "production_input_contract" in compact_value
    ):
        raise ValueError("auxiliary_production_parent_invalid")
    from src.engine.scalping import reversal_auxiliary_production_input as M

    body = copy.deepcopy(compact_value)
    body.update(
        production_input_contract=M.contract(scope_ids),
        production_parent_registry_sha256=compact_value["registry_sha256"],
    )
    body.pop("registry_sha256")
    body["registry_sha256"] = P.digest(body)
    return validate(body)


def load(data_root, ident):
    if not isinstance(ident, str) or not re.fullmatch("[a-f0-9]{64}", ident):
        raise ValueError("auxiliary_registry_id_invalid")
    from src.engine.scalping.mechanistic_entry_runtime_policy import _read

    value = validate(_read(directory(data_root) / (ident + ".json")))
    if value["registry_sha256"] != ident:
        raise ValueError("auxiliary_registry_identity_changed")
    if value["schema"] == SCHEMA_V2:
        original = validate(
            _read(directory(data_root) / (value["research_registry_sha256"] + ".json"))
        )
        if (
            original["schema"] != SCHEMA
            or original["registry_sha256"] != value["research_registry_sha256"]
        ):
            raise ValueError("auxiliary_registry_research_identity_changed")
        expected = compact_definition(
            original, research_wire_contract=value["research_wire_contract"]
        )
        if "production_input_contract" in value:
            parent = validate(
                _read(
                    directory(data_root)
                    / (value["production_parent_registry_sha256"] + ".json")
                )
            )
            if parent != expected:
                raise ValueError("auxiliary_production_parent_changed")
            expected = production_definition(
                parent, scope_ids=value["production_input_contract"]["scope_ids"]
            )
        if expected != value:
            raise ValueError("auxiliary_registry_research_binding_changed")
    return value


def binding(value):
    validate(value)
    A = projector(value["input_version"])
    arm = value["base_arm"]
    if value["schema"] == SCHEMA and value["prompt"] == A.PROMPT + A.ARM_SUFFIXES[arm]:
        return A.binding(arm)
    return dict(
        A.binding(arm),
        prompt_version=value["schema"] + ":" + value["registry_sha256"],
        prompt_sha256=P.digest(value["prompt"]),
        registry_sha256=value["registry_sha256"],
    )


def production_request(snapshot, value):
    validate(value)
    A = projector(value["input_version"])
    event, source = snapshot
    inp, _, schema = A.production_request(source, value["base_arm"], event=event)
    if "production_input_contract" in value:
        from src.engine.scalping import reversal_auxiliary_production_input as M

        inp = M.project(inp, expected_contract=value["production_input_contract"])
        schema = A.response_schema(inp)
    return inp, value["prompt"], schema


def request(snapshot, value):
    # Preserve historical exact request IDs for eligible actual-response reuse.
    from src.engine.scalping.continuous_reversal_operating_postclose import (
        request as old_request,
    )

    validate(value)
    req = copy.deepcopy(old_request(snapshot, value["base_arm"]))
    if req["candidate_input"]["schema"] != value["input_version"]:
        raise ValueError("auxiliary_registry_snapshot_version_mismatch")
    req["candidate"].update(
        system_prompt=value["prompt"], prompt_version=binding(value)["prompt_version"]
    )
    if "production_input_contract" in value:
        inp, _, schema = production_request(snapshot, value)
        req.update(candidate_input=inp, candidate_input_sha256=P.digest(inp))
        req["candidate"].update(
            response_schema=schema,
            response_schema_sha256=P.digest(schema),
            production_input_contract=copy.deepcopy(value["production_input_contract"]),
        )
    req["paired_replay_id"] = P.digest(
        [
            A.opportunity(snapshot[0]),
            "UNION",
            {k: req[k] for k in ("candidate_input", "candidate", "control", "stage")},
        ]
    )
    if value["schema"] == SCHEMA_V2:
        from src.engine.scalping import reversal_auxiliary_wire as W

        req = W.request(
            req, production_request(snapshot, value)[0], value["wire_contract"]
        )
    return req


def envelope(logical_input, value):
    validate(value)
    if "production_input_contract" in value:
        from src.engine.scalping import reversal_auxiliary_production_input as M

        M.validate_projected(
            logical_input, expected_contract=value["production_input_contract"]
        )
    schema = projector(value["input_version"]).response_schema(logical_input)
    if value["schema"] == SCHEMA_V2:
        from src.engine.scalping import reversal_auxiliary_wire as W

        return W.envelope(logical_input, value["prompt"], schema)
    return dict(
        logical_input=logical_input,
        logical_prompt=value["prompt"],
        logical_schema=schema,
        wire_input=logical_input,
        wire_schema=schema,
        final_prompt=value["prompt"],
        hashes={},
    )


def decode_response(raw, logical_input, value):
    validate(value)
    if "production_input_contract" in value:
        from src.engine.scalping import reversal_auxiliary_production_input as M

        M.validate_projected(
            logical_input, expected_contract=value["production_input_contract"]
        )
    if value["schema"] == SCHEMA_V2:
        from src.engine.scalping import reversal_auxiliary_wire as W

        return W.decode(raw, logical_input, value["base_arm"])
    return raw


def main(argv=None):
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--arm", choices=A.V1.ARMS, required=True)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--input-version", default=A.VERSION)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--development-key", action="append", default=[])
    args = parser.parse_args(argv)
    value = definition(
        args.arm,
        prompt=args.prompt_file.read_text() if args.prompt_file else None,
        hypothesis=args.hypothesis,
        development_keys=args.development_key,
        input_version=args.input_version,
    )
    print(
        json.dumps(
            dict(registry_sha256=register(args.data_root, value), runtime_applied=False)
        )
    )


if __name__ == "__main__":
    main()
