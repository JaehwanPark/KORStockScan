"""Report-only capability projection across an exactly reviewed code successor.

Ownership: monitoring, separate from native report/policy publication. Original
contracts and source bytes remain historical; no strategy authority is granted.
"""

from copy import deepcopy
import ast
import hashlib
import json
from pathlib import Path
import subprocess

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import policy_generation_validation as validation


def reviewed_source_transition(path, *, consumer_family=None):
    """Authenticate one reviewed source delta and derive every affected family.

    The operator's immutable review is code-capability evidence only. Both
    generations still need their own native fixtures at the consuming reader.
    """
    if consumer_family is not None and consumer_family not in generation.COMPONENTS:
        raise ValueError("source_review_consumer_family_invalid")
    path = Path(path)
    if not path.is_absolute() or path.is_symlink() or path.resolve() != path:
        raise ValueError("source_review_path_invalid")
    review, sha = validation.bounded_object(path, 2 * 1024 * 1024)
    if (
        path.is_symlink()
        or path.name != sha + ".json"
        or review.get("schema") != "postclose_generation_source_review_v1"
        or review.get("verification_scope") != "report_only_code_capability"
        or any(review.get(k) is not False for k in validation.AUTHORITY_FALSE)
        or type(review.get("provider_calls")) is not int
        or review["provider_calls"] != 0
        or type(review.get("orders")) is not int
        or review["orders"] != 0
    ):
        raise ValueError("source_review_identity_or_authority_invalid")
    current = Path(review["current_release_root"])
    origin = Path(review["origin_release_root"])
    if current == origin:
        raise ValueError("source_review_current_root_invalid")
    inventories = []
    source_hashes = {}
    for role, root in (("origin", origin), ("current", current)):
        if root.is_symlink() or not root.is_absolute() or root.resolve() != root:
            raise ValueError("source_review_root_invalid")
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=10
        ).strip()
        if commit != review[role + "_git_commit"]:
            raise ValueError("source_review_commit_changed")
        registry = root / "src/engine/monitoring/policy_generation_contract.py"
        declarations = {}
        for node in ast.parse(validation.file_bytes(registry).decode()).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {
                        "COMPONENTS", "COMMON_CODE_COMPONENTS"
                    }:
                        declarations[target.id] = ast.literal_eval(node.value)
        components = declarations["COMPONENTS"]
        common = declarations["COMMON_CODE_COMPONENTS"]
        if set(components) != set(generation.COMPONENTS):
            raise ValueError("source_review_family_registry_changed")
        families, relatives = {}, set()
        for family, names in components.items():
            values = {}
            for name in dict.fromkeys((*names, *common, *generation.COMMON_CODE_COMPONENTS)):
                source = root / "src/engine" / name
                relative = source.resolve().relative_to(root.resolve()).as_posix()
                ancestor = source
                while ancestor != root:
                    if ancestor.is_symlink():
                        raise ValueError("source_review_source_alias_invalid")
                    ancestor = ancestor.parent
                key = str(source.resolve())
                if key not in source_hashes:
                    source_hashes[key] = validation.file_sha(source)
                value = source_hashes[key]
                if name in names or name in common:
                    values[name] = value
                relatives.add(relative)
            families[family] = generation.digest(values)
        dirty = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD", "--", *sorted(relatives)],
            cwd=root, text=True, timeout=10,
        )
        if dirty.strip():
            raise ValueError("source_review_uncommitted_components")
        tracked = subprocess.check_output(
            ["git", "ls-files", "--", *sorted(relatives)],
            cwd=root, text=True, timeout=10,
        ).splitlines()
        if set(tracked) != relatives:
            raise ValueError("source_review_untracked_components")
        inventories.append((families, relatives, (components, common)))
    old, new = inventories
    # The sole admitted membership extension binds this existing capability
    # reader into future fixture generations. Family/execution owners cannot
    # change through a source review. Old hashes retain their original members.
    reviewer = "monitoring/policy_generation_code_handoff.py"
    if (
        old[1] != new[1]
        or old[2][0] != new[2][0]
        or tuple(n for n in old[2][1] if n != reviewer)
        != tuple(n for n in new[2][1] if n != reviewer)
        or (reviewer in old[2][1] and reviewer not in new[2][1])
        or new[2][1] != generation.COMMON_CODE_COMPONENTS
    ):
        raise ValueError("source_review_component_membership_changed")
    delta = {}
    for relative in sorted(old[1]):
        before = source_hashes[str(origin / relative)]
        after = source_hashes[str(current / relative)]
        if before != after:
            delta[relative] = dict(before=before, after=after)
    affected = sorted(f for f in new[0] if old[0][f] != new[0][f])
    # Authenticate the entire immutable review, then bind only the requested
    # consumer. Another family's later successor cannot invalidate unchanged
    # code, and this scoped result cannot authorize that other family.
    consumed = affected if consumer_family is None else [consumer_family]
    if (
        not affected
        or review.get("reviewed_files") != delta
        or review.get("reviewed_families") != affected
        or any(f not in affected for f in consumed)
        or any(new[0][f] != generation.code_generation(f) for f in consumed)
    ):
        raise ValueError("source_review_incomplete_change_inventory")
    evidence = review.get("review_evidence") or {}
    if (
        not evidence.get("path")
        or validation.file_sha(Path(evidence["path"])) != evidence.get("sha256")
    ):
        raise ValueError("source_review_evidence_changed")
    return dict(
        reference=dict(path=str(path), sha256=sha),
        pairs={family: [old[0][family], new[0][family]] for family in consumed},
        source_hashes=source_hashes,
        review_evidence=evidence,
    )


def consumer_inventory(root, day, *, data_root=None):
    """One native report-capability census for deployment and later health."""
    data = Path(data_root) if data_root is not None else Path(root) / "data"
    observed = {x["family"]: x for x in generation.observations(root, day, data_root=data)}
    if set(validation.PLANS) != set(generation.COMPONENTS):
        raise ValueError("capability_consumer_registry_incomplete")
    return [
        dict(
            family=family, role="report_only", source_date=day,
            code_sha256=generation.code_generation(family),
            observation=(current_fixture_observation(observed[family], data)
                         if family in observed else None),
        )
        for family in generation.COMPONENTS
    ]

# 92785b7da and the reviewed 86f789693 native-arm completion successor change
# entry paths in the shared handler, not either family publication or policy.
# The carried-stop reader partitions future unconsumed observations; 40b931254
# scopes the approved Main weak vetoes without changing either family producer.
# All components remain bound by the complete generation hashes; current fixture
# evidence is independently required. No historical contract is reclassified.
# Review: docs/audits/main-cumulative-holding-integration-deployment-2026-10-15.md.
# Preset/cost-clock and cumulative auxiliary changes extend exact review to
# entry-cancel-wait and auxiliary; every successor needs new isolated fixtures.
# The holding-context snapshot successor changes only the source-only observer's
# concurrent reads. Rising/holding require fresh fixtures for the new bytes.
# Review: docs/audits/main-holding-context-dictionary-race-repair-2026-10-15.md.
# The carried-stop reader now locks future-only vote snapshots; the holding
# capability remains bound to a fresh exact-generation fixture.
# Review: docs/audits/main-finalization-live-vote-read-race-repair-2026-10-15.md.
# Async session-boundary rejection changes shared-handler bytes only. Preserve
# route/order guards and require fresh rising/holding fixtures for this successor.
# Review: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
# The terminal KST/custody repair changes shared-handler bytes. Verify fresh
# fixtures while retaining all original reports and unresolved terminal evidence.
# The reviewed sealed-prefix and overnight terminal receipt successor preserves
# historical source bytes and requires its own fresh holding capability fixture.
# Source-gap and mandatory first-crossing repair: exact code pairs only.
# Fresh network-denied fixtures attest every changed generation.
# Review: docs/audits/main-postclose-source-gap-final-release-review-2026-10-16.md.
# Probe partial custody repair changes shared handler/receipt bytes only.
# Fresh fixtures bind the successor; historical source reports remain unchanged.
# Review: docs/audits/main-probe-partial-integrated-deployment-review-2026-10-16.md.
# Exact nonfixed continuity changes entry source readiness in shared Main/handler
# bytes only. Family producers and historical contracts remain unchanged; require
# fresh rising/holding fixtures before consuming this reviewed successor.
# Review: docs/audits/nonfixed-source-continuity-review-2026-10-16.md.
# Long4/fixed-watch and 04c holding/replay integration; original reports stay unchanged.
# Review: docs/audits/long4-source-retention-integration-review-2026-10-16.md.
# Lossless logical-source readers and checkpoint-relative current custody were
# reviewed after the 10/16 close. Keep every original source generation and
# require independent current fixtures; this never certifies historical results.
# Review: docs/audits/postclose-semantic-recovery-review-2026-10-16.md.
# Reviewed original dated native readers and compressed handoff renew only
# exact capability targets. Preserve prior hashes and every historical
# report/fixture; independent current fixtures remain mandatory.
# Review: docs/audits/postclose-complete-semantic-repair-2026-10-17.md.
# Quote-delivery consumer successor: retain original reports and require fresh fixtures.
REVIEWED_SUCCESSORS = {
    "entry_cancel_wait": (
        "d8583947a62ffe15318b2819f6f4824b8835a7fc5865c5b00f85b8eb427620b0",
        "4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db",
    ),
    "rising_missed": (
        "dfe2d56deef10ebaf4f2aa6e3edd6215f769d08ba8ac123808459c2cc8fb720f",
        "676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962",
    ),
    "auxiliary": (
        "88a496105946f292ae3c85028be6276009738742a0916f7c9965c9c9ba6959df",
        "2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4",
    ),
    "holding_vote": (
        "b2087e97e70fc145620d3440c4fddafd633ab8e45d3aa492fffec17a7b04bcab",
        "8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf",
    ),
}

# The next dated native report already carries the formerly reviewed successor.
# Preserve that report too; do not relabel it as the older source generation.
REVIEWED_PRESERVED_SOURCE_SUCCESSORS = {
    # Exact 10/15 native reports retained after source-census and residual
    # custody repairs. Revalidate their original fixtures and source bodies;
    # current capability does not promote their comparison/selection state.
    "entry_cancel_wait": (
        "b2a2017deb606554fbe1c9d481426786b3a8ab463c948ee84cd8ab856eddfca0",
        "4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db",
    ),
    "rising_missed": (
        "dde49a32b7299deabf981e9f3a734a9da3019ba3f4e3eb7abbaff91dd3d01fa3",
        "676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962",
    ),
    "holding_vote": (
        "5658a73a4aeb866c3124370eddc500ce27dd2e15589ba2ef4d7c35c7231a83c2",
        "8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf",
    ),
}


# The actual 4c65523b2 source generation is also preserved if already reported.
REVIEWED_DEPLOYED_SOURCE_SUCCESSORS = {
    "entry_cancel_wait": (
        "6d6a294941f6337d48420514d40e36891d25b44dc09bd914be0831d897794d4c",
        "4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db",
    ),
    "rising_missed": (
        "0f6c455328de656c920956be0b2a24fec57db08f8b4e7b3e2fa7db43249ff7ed",
        "676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962",
    ),
    "auxiliary": (
        "711184e6d93f27e3d8f4bdd97598f4880f752332f850763b32b434560b460f8e",
        "2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4",
    ),
    "holding_vote": (
        "e213bbe524aa7575f8e9c784cf43db77b9c194dee5bfc03b943a8175fc655278",
        "8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf",
    ),
}


# Delay situation/zero-cell observer repair touches shared handler metadata.
# Preserve the selected predecessor's report generation and require a new fixture.
# Review: docs/audits/pre-submit-semantic-implementation-review-2026-10-16.md.
REVIEWED_DELAY_SOURCE_SUCCESSORS = {
    "rising_missed": (
        "ea1ac91b6e080d96f3a0d61dca47575c101862ba6fe77fed36fc6170687f3e08",
        "676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962",
    ),
    "holding_vote": (
        "dfd762fa2b9d15799e4951bc5624effa58f8efdec29cb85939ba9d5e21765d58",
        "8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf",
    ),
}


REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS = {
    "entry_cancel_wait": (
        "2e0ba14946a5e9e191a95529971e103136679957ddd7458678ed6c27a0e4a234",
        "4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db",
    ),
    "rising_missed": (
        "e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874",
        "676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962",
    ),
    "auxiliary": (
        "d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0",
        "2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4",
    ),
    "holding_vote": (
        "057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce",
        "8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf",
    ),
}


# Exact original 10/16 report to the reviewed auxiliary input/research reader.
# Preserve the prior prepared pair and its historical fixtures independently.
# This is code capability only: a fresh exact-generation fixture remains
# mandatory, and comparison/selection state and runtime authority stay intact.
# Review: docs/audits/main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md.
REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS = {
    "auxiliary": (
        "d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0",
        "dea0b4f9d124372e48413635f5f82fbf3f0fbd6477a4f1beaca6769a68e9990b",
    ),
}


# Exact original 10/16 reports to the reviewed post-auxiliary guard repair.
# Only shared entry-handler bytes changed in these family generations. Keep
# their original contracts, states and fixtures; independently validate the
# current capability without granting selection, runtime or profit authority.
# Review: docs/audits/main-post-auxiliary-priority-repair-review-2026-10-17.md.
REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS = {
    "rising_missed": (
        "e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874",
        "b47474ed46cc63f090ccf14ce40b6d53b1d1518cba43211e648a1ee1b0f2aa36",
    ),
    "holding_vote": (
        "057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce",
        "02b637bfb01bb9f01b4d8b33672d2ae0d9be74ff07c3ee972608f0c55beaf2e5",
    ),
}


# Direct original 10/16 report to the reviewed quantity cost reader. Its
# research-only projection changes shared code identities, not actual holding
# economics. Preserve every older target and independently require the exact
# current holding fixture; do not chain earlier historical contracts forward.
# Review: docs/proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md section 8.
REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS = {
    "holding_vote": (
        "057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce",
        "6c4734c5e4204b36faf3d72ee873a429147d7a6e5a3a019d55fee29f4e145137",
    ),
}


# Original 10/16 report generations to the reviewed delay observation repair
# and bounded shard reader. Numeric policies and historical results retain
# their own contracts; independent exact-current fixtures remain mandatory.
# Review: docs/audits/pre-submit-delay-situation-research-implementation-review-2026-10-17.md.
REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS = {
    "rising_missed": (
        "e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874",
        "5f8cd733ba9fb8b4733f3bafbc5a9431d45d6638713934daf74ba144844d74a5",
    ),
    "holding_vote": (
        "057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce",
        "e06ee4b2d6d09410dd81d88cb661b6a18df2ca1dea2e7e81823a7d6e03d24b46",
    ),
}


# Direct frozen 10/16 native reports to the reviewed integrated research code.
# The shared Claim helper is now a capability dependency, so all four families
# have new fixture paths. Preserve every previous pair and receipt; this is
# source/reader capability, not economic selection or runtime/performance PASS.
# Review: docs/audits/main-research-integrated-p5-p6-deployment-review-2026-10-18.md.
REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS = {
    "entry_cancel_wait": (
        "2e0ba14946a5e9e191a95529971e103136679957ddd7458678ed6c27a0e4a234",
        "4bf8bb24955fa5889d9090bcbbee1fd317493f0841d2a5a46566453291a5e907",
    ),
    "rising_missed": (
        "e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874",
        "7fa7a62c8bd2f75b7218cee881ea1cffd41c4ade083b97fc73c0559693447aeb",
    ),
    "auxiliary": (
        "d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0",
        "a249dbc9baa7fb5e05a36481cf476083de6c8b7ad369e3b26ceb7f3ba74373b5",
    ),
    "holding_vote": (
        "057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce",
        "e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea",
    ),
}


# Read-only startup preparation changes auxiliary's V6 reader bytes. Preserve
# the original 10/16 report and every prior target; this separate exact pair
# requires both the original fixture and an independent current fixture.
REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS = {
    "auxiliary": (
        "d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0",
        "00e4f1813805e520e9daed86fa1b71b55c06f76c7128b4ad7762d978ab956822",
    ),
}


# Reviewed cleanup successor, bound directly to the preserved 10/16 reports.
# A historical fixture and an independent current fixture are both mandatory.
REVIEWED_CLEANUP_SOURCE_SUCCESSORS = {
    "auxiliary": (
        "d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0",
        "b54dc1696e819566a5c9c785c24d171caed2887aace05297e391bd1722ea995d",
    ),
    "entry_cancel_wait": (
        "2e0ba14946a5e9e191a95529971e103136679957ddd7458678ed6c27a0e4a234",
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
    ),
    "holding_vote": (
        "e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea",
        "791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b",
    ),
    "rising_missed": (
        "e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874",
        "d23d80552d0453697e61757b2f0f1081509316868c02166afdb7adf848b20b32",
    ),
}


# Exact reviewed receipt/identity repair; source bytes and prior fixtures stay sealed.
REVIEWED_RECEIPT_CUSTODY_SOURCE_SUCCESSORS = {
    "auxiliary": (
        "80497557e7be71c0eafcdaa4bd7256250c66899a791510efa2f98f81cbcbbc05",
        "b54dc1696e819566a5c9c785c24d171caed2887aace05297e391bd1722ea995d",
    ),
    "entry_cancel_wait": (
        "3acc183fa1d6675d4113b6f8faeccbb52bb58e214461508578e5b7e475cd6270",
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
    ),
    "holding_vote": (
        "69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11",
        "791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b",
    ),
    "rising_missed": (
        "1f524a5ad98e623501eaaa2d7c81773ac0ad6328237d72ea0c95c0c8cd1251bb",
        "d23d80552d0453697e61757b2f0f1081509316868c02166afdb7adf848b20b32",
    ),
}

# Fresh native fixtures are mandatory for the frozen-input/census successor.
# Each historical source retains its own original fixture and semantic state.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS = {
    "holding_vote": (
        (
            "69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11",
            "3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc",
        ),
        (
            "e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea",
            "3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc",
        ),
        (
            "791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b",
            "3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc",
        ),
        (
            "69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11",
            "bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db",
        ),
        (
            "e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea",
            "bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db",
        ),
        (
            "791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b",
            "bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db",
        ),
        (
            "3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc",
            "bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db",
        ),
    )
}

# SourceReadReduction1020: preserved native reports need independent fixtures
# for the exact report-reader successor, never a rewritten historical contract.
REVIEWED_SOURCE_READER_SUCCESSORS = {
    "rising_missed": (
        "1f524a5ad98e623501eaaa2d7c81773ac0ad6328237d72ea0c95c0c8cd1251bb",
        "c71f1a1954a515f59bf551c8ea6e674415c2fd96f5e8e7a742fb85a56fa7493a",
    ),
    "auxiliary": (
        "80497557e7be71c0eafcdaa4bd7256250c66899a791510efa2f98f81cbcbbc05",
        "cc663fc62f34bd39f01591c15b13977aa50043f2fe1579291bf719ed3fb496e7",
    ),
}

# Delay-v4 identity diagnostics and unreachable PYRAMID helper removal. Keep
# issued pairs above; these exact successors require independent fresh fixtures
# while preserving the original native report and its historical fixture.
REVIEWED_DELAY_CLEANUP_SUCCESSORS = {
    "rising_missed": (
        "1f524a5ad98e623501eaaa2d7c81773ac0ad6328237d72ea0c95c0c8cd1251bb",
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
    ),
    "auxiliary": (
        "80497557e7be71c0eafcdaa4bd7256250c66899a791510efa2f98f81cbcbbc05",
        "4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac",
    ),
    "holding_vote": (
        "69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11",
        "b447ff4c7e39ed9f1d1884c3d032b567225d51b92d121c91e24c280c9e84c72b",
    ),
}


# d7d353b4a repairs holding-source republication in runtime_approval_summary.
# That shared summary dependency changes these two capability generations;
# their own producer/selection/publisher/reader bytes are unchanged. Preserve
# the original 10/20 contracts and require both old and fresh native fixtures.
# Review: docs/audits/postclose-root-cause-recovery-review-2026-10-19.md.
REVIEWED_HOLDING_REPUBLICATION_SUCCESSORS = {
    "entry_cancel_wait": (
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
        "e1c56d2cfc3612794fe8cc4d638b25c72f7643cb8f894a88a2a46f532df12b82",
    ),
    "auxiliary": (
        "4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac",
        "a2c47ec94d9ae8e1866af911d9de2426cf04a394f41a5dca893e90e16fc12a93",
    ),
}

# Exact source-only historical decision disposition; fresh fixtures remain mandatory.
REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS = {
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "f1aa713f7fd76467bd78c17fb0890eee55421d4ed18c865eeca0a8edc03518db",
    ),
}


# Exact revived-watch observation metadata successor; historical reports stay sealed.
REVIEWED_FIXED_WAIT_SUCCESSORS = {
    "rising_missed": (
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
        "349dd5b7e1286c462ad418ed2b8332dd95020b95b19e164720ce311439ddc646",
    ),
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "0065b34f2b56538b406ac2a2e78b2ee57fb76a88bcd3bf1e315a2d090bdb2733",
    ),
}


# Exact residual receipt custody and unit-leg inventory recovery successor.
REVIEWED_ENTRY_RECEIPT_SUCCESSORS = {
    "entry_cancel_wait": (
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
        "ef7a5a2134321f14b1c64a45a7f0987807a70f5623a450197e086978e1b9818e",
    ),
    "rising_missed": (
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
        "12fc26d917da97f6c8478e1639f531d161cfd4085a283db372ea9ee1efd8a53a",
    ),
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "4a2b6c4e105eb2ca538807222ce0b49ad189829f7a64d1d18dd4828b94a5e94f",
    ),
}


# Completed owned-entry recovery also persists its native holding BUY identity.
REVIEWED_BUY_IDENTITY_SUCCESSORS = {
    "entry_cancel_wait": (
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
        "2382694e568af306027b58857aa2b5dff6fa0093347f4c8220a8ae6be001adef",
    )
}


# Exact quantity capture/context projection successor. Both original report
# and independent current fixture remain required; no historical verdict reuse.
REVIEWED_QUANTITY_CAPTURE_SUCCESSORS = {
    "rising_missed": (
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
        "dbfecb3ffb0a046b87010972feda7f88a9c1a538e1fdf38f4c807b1d9d355b9c",
    ),
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "e94a9f0baa91f88041c52474b79238fca6ef71f528ff4bc07c9f832303c11d01",
    ),
}


# Exact integrated source/receipt/cost and validation-owner successor.
# Original report/fixture and independent current fixture remain mandatory.
REVIEWED_ENTRY_COST_SUCCESSORS = {
    "auxiliary": (
        "4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac",
        "581c21738b7a098e1900fcec2063e257b7f8ab71cce046ef4a8eb0b6fe41e8bd",
    ),
    "entry_cancel_wait": (
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
        "88275729dd03ed1f0de7bb562a85fab49e1212447da4a268fb3cd9e175389313",
    ),
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "aa14bd6051d104461b5830b24df8ea0576402b4687fd9a808c707eb69b0e02ea",
    ),
    "rising_missed": (
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
        "b6d966e440e92d57a8874814c3fcc2dfe9c0eab54603d8c9c6f2e93734b240f7",
    ),
}


REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS = {
    "auxiliary": (
        "a2c47ec94d9ae8e1866af911d9de2426cf04a394f41a5dca893e90e16fc12a93",
        "581c21738b7a098e1900fcec2063e257b7f8ab71cce046ef4a8eb0b6fe41e8bd",
    ),
    "entry_cancel_wait": (
        "2382694e568af306027b58857aa2b5dff6fa0093347f4c8220a8ae6be001adef",
        "88275729dd03ed1f0de7bb562a85fab49e1212447da4a268fb3cd9e175389313",
    ),
    "holding_vote": (
        "e51ef1e839e2bf60aa7ecb7dd4eaed2d701c01816dc37298402701de9b75a9cd",
        "aa14bd6051d104461b5830b24df8ea0576402b4687fd9a808c707eb69b0e02ea",
    ),
    "rising_missed": (
        "75040f633f59cdadf8302ea2e68efdc05b1174f92c3caa73780d71e8e37bcd7e",
        "b6d966e440e92d57a8874814c3fcc2dfe9c0eab54603d8c9c6f2e93734b240f7",
    ),
}


# Exact shutdown/normalization successor; retain original and consumed profiles.
REVIEWED_SHUTDOWN_SUCCESSORS = {
    "auxiliary": (
        "4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac",
        "1927f855e079e75ce460568448233f873edaef8fd1c2f066007e5a588fe7784c",
    ),
    "entry_cancel_wait": (
        "47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff",
        "2c7807836c1b0a76f2c44d16bea190d82243ef9abe672eaddac81fccb40e24d4",
    ),
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "52a1ae1dd40b2d739f74ead84308148b5f0e5f800e0a93f0bd4c6ed6e2732202",
    ),
    "rising_missed": (
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
        "45d8e54cc7dc029c9c5e20d888e00cc9997ea7e7d2c2ddaaa2b3d8a2983d3a59",
    ),
}
REVIEWED_SHUTDOWN_SOURCE_SUCCESSORS = {
    "auxiliary": (
        "a2c47ec94d9ae8e1866af911d9de2426cf04a394f41a5dca893e90e16fc12a93",
        "1927f855e079e75ce460568448233f873edaef8fd1c2f066007e5a588fe7784c",
    ),
    "entry_cancel_wait": (
        "2382694e568af306027b58857aa2b5dff6fa0093347f4c8220a8ae6be001adef",
        "2c7807836c1b0a76f2c44d16bea190d82243ef9abe672eaddac81fccb40e24d4",
    ),
    "holding_vote": (
        "e51ef1e839e2bf60aa7ecb7dd4eaed2d701c01816dc37298402701de9b75a9cd",
        "52a1ae1dd40b2d739f74ead84308148b5f0e5f800e0a93f0bd4c6ed6e2732202",
    ),
    "rising_missed": (
        "75040f633f59cdadf8302ea2e68efdc05b1174f92c3caa73780d71e8e37bcd7e",
        "45d8e54cc7dc029c9c5e20d888e00cc9997ea7e7d2c2ddaaa2b3d8a2983d3a59",
    ),
}
REVIEWED_SHUTDOWN_CONSUMED_SUCCESSORS = {
    "auxiliary": (
        "581c21738b7a098e1900fcec2063e257b7f8ab71cce046ef4a8eb0b6fe41e8bd",
        "1927f855e079e75ce460568448233f873edaef8fd1c2f066007e5a588fe7784c",
    ),
    "entry_cancel_wait": (
        "e289f5a37b37b84bf50e39cd8bdd3153f3fa54ef68d8545465507077f77eb402",
        "2c7807836c1b0a76f2c44d16bea190d82243ef9abe672eaddac81fccb40e24d4",
    ),
    "holding_vote": (
        "68cfad9c0ac263930de8bbde42b3cdaf0d64994b23d3a593bfe8d955ab98ebe8",
        "52a1ae1dd40b2d739f74ead84308148b5f0e5f800e0a93f0bd4c6ed6e2732202",
    ),
    "rising_missed": (
        "92427c4782da75ebe71bee3dde8923fa19e04e14c26e14b8a80d2a831fd2296c",
        "45d8e54cc7dc029c9c5e20d888e00cc9997ea7e7d2c2ddaaa2b3d8a2983d3a59",
    ),
}

# Exact native selection diagnostics; the prior report generations stay sealed.
REVIEWED_NATIVE_SELECTION_SUCCESSORS = {
    "rising_missed": (
        "8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d",
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
    ),
    "holding_vote": (
        "48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3",
        "5a0c5cfb039defc00eac4d057638b7b7ac2f394b86f6a030fd08a76b84d814ee",
    ),
}
REVIEWED_NATIVE_SELECTION_SOURCE_SUCCESSORS = {
    family: (REVIEWED_SHUTDOWN_SOURCE_SUCCESSORS[family][0], pair[1])
    for family, pair in REVIEWED_NATIVE_SELECTION_SUCCESSORS.items()
}
REVIEWED_NATIVE_SELECTION_CONSUMED_SUCCESSORS = {
    family: (REVIEWED_SHUTDOWN_SUCCESSORS[family][1], pair[1])
    for family, pair in REVIEWED_NATIVE_SELECTION_SUCCESSORS.items()
}

# Direct original source22 reports to the reviewed explicit-entry-route and
# archived-source reader repairs. Only the shared entry handler changed for
# rising; holding also changed the archived master-source equality reader.
# Original reports/fixtures and independent current fixtures remain required.
# Review: docs/audits/postclose-root-cause-recovery-review-2026-10-19.md.
REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS = {
    "rising_missed": (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "b8583110470210c0d71035a472d95bc8379ea5d53b56e7217897f397e4490a56",
    ),
    "holding_vote": (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "a3cc6a2a30d98cc9445c40b9a51cd07203d0cc01693fd6474a5be24d343c1205",
    ),
}
# Exact actually consumed parent; original report and independent current fixture are mandatory.
REVIEWED_PRE_SUBMIT_CONSUMED_SUCCESSORS = {
    "holding_vote": (
        "f658caee8304f4461764301dc54774aef42c2867ff0bb340dc4f39b92fc28179",
        "a3cc6a2a30d98cc9445c40b9a51cd07203d0cc01693fd6474a5be24d343c1205",
    ),
    "rising_missed": (
        "6d493cf1a74732175bfeb2e27af9c53de44d8a001bc0b1d01296888671da22de",
        "b8583110470210c0d71035a472d95bc8379ea5d53b56e7217897f397e4490a56",
    ),
}

# Source22 reports retain their native fixtures across the reviewed lossless
# archive census reader and the bounded research-retention inventory addition.
# Both original fixtures and independent current fixtures are still mandatory.
REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS = {
    "entry_cancel_wait": (
        "60620f4b8fbe73f3c0506eed8f49c27c031d74a643b68667ca7421c6512d6f57",
        "5ec9def232f1e0f792a0de280f7124c47473b74c0a1015afa89c7fec155eff0b",
    ),
    "holding_vote": (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "f658caee8304f4461764301dc54774aef42c2867ff0bb340dc4f39b92fc28179",
    ),
}


# Exact combined submit, lossless observation and native research consumer review.
REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS = {
    "holding_vote": (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "9cfde364c304b164f837f527091cb92a573af531f69d1613e4c2caffaa808339",
    ),
    "rising_missed": (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "5d5fcf214f83b8c32a99225b4319defe3ca1f9d3f891be34c36c835165e12637",
    ),
}
REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS = {
    "holding_vote": (
        "f658caee8304f4461764301dc54774aef42c2867ff0bb340dc4f39b92fc28179",
        "9cfde364c304b164f837f527091cb92a573af531f69d1613e4c2caffaa808339",
    ),
    "rising_missed": (
        "6d493cf1a74732175bfeb2e27af9c53de44d8a001bc0b1d01296888671da22de",
        "5d5fcf214f83b8c32a99225b4319defe3ca1f9d3f891be34c36c835165e12637",
    ),
}


# Submit-local latency/identity changes preserve policy and historical reports.
# Independent current-generation fixtures remain mandatory.
REVIEWED_SUBMIT_FRESH_SOURCE_SUCCESSORS = {
    "rising_missed": (
        "28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922",
        "211e66b1be20bfe4470e65e7c9d6f710c5fb480908bae3c112460e7177c0a06b",
    ),
    "holding_vote": (
        "7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386",
        "efba28203d17ad1a8d8b11ce08e504a3203134ba3c931cbf7bb3500fbc235d69",
    ),
}
REVIEWED_SUBMIT_FRESH_CONSUMED_SUCCESSORS = {
    "rising_missed": (
        "1a206224114b7dc0b03fdce56db85a99e1e70cb4e44b4deacd0bd73c6ea4514c",
        "211e66b1be20bfe4470e65e7c9d6f710c5fb480908bae3c112460e7177c0a06b",
    ),
    "holding_vote": (
        "231d058214999b2b9aa417be8b5b528e98c4499a7a54303503c44e1834e10831",
        "efba28203d17ad1a8d8b11ce08e504a3203134ba3c931cbf7bb3500fbc235d69",
    ),
}


def _historical_fixture(contract, data, family, *, late_report=None):
    """Preserve a prior fixture without using it to certify the successor."""
    reference = contract.get("fixture_receipt")
    if reference is None and late_report is None:
        return None
    path = (
        Path(data)
        / "report/postclose_generation_validation"
        / (family + "_" + contract["code_sha256"] + ".json")
    )
    referenced = (
        Path(str((reference or {}).get("path") or ""))
        if isinstance(reference, dict)
        else Path(".")
    )
    if not referenced.is_absolute():
        referenced = Path(data).parent / referenced
    if reference is not None and (
        not isinstance(reference, dict) or referenced.resolve() != path.resolve()
    ):
        raise ValueError("successor_historical_fixture_path_invalid")
    payload, sha = validation.bounded_object(path, 65536)
    if (
        path.is_symlink()
        or reference is not None
        and sha != reference.get("sha256")
        or payload.get("schema") != "postclose_generation_fixture_receipt_v1"
        or payload.get("family") != family
        or payload.get("status") != "pass"
        or payload.get("code_sha256") != contract["code_sha256"]
        or not payload.get("closure_tests")
        or payload.get("unresolved_findings") != []
        or payload.get("receipt_sha256")
        != generation.digest(
            {k: v for k, v in payload.items() if k != "receipt_sha256"}
        )
        or payload.get("runtime_effect") is not False
        or payload.get("actual_pid_consumed") is not False
        or payload.get("actual_profit_verified") is not False
        or payload.get("allowed_runtime_apply", False) is not False
    ):
        raise ValueError("successor_historical_fixture_invalid")
    if reference is None:
        # A native fixture may be published after an immutable report. Accept
        # only this exact reviewed successor and the fixture's own protected
        # original report binding; do not invent a reference in that report.
        report_path, report_sha = late_report
        run = Path(payload.get("validation_run", ""))
        evidence = payload.get("evidence") or {}
        historical_plan = validation.plan_identity(family)
        if payload.get("validation_plan") != historical_plan:
            # A later fixture-validator repair does not rewrite the original
            # native evidence. Bind that plan to its exact clean issuer tree.
            from src.engine.infrastructure import runtime_release_router as router

            issuer = Path(str(payload.get("release_root") or ""))
            revision = payload.get("git_commit")
            router.validate_release(
                Path(data).resolve().parent,
                dict(
                    schema="runtime_release_selection_v1",
                    workspace=str(Path(data).resolve().parent),
                    release_root=str(issuer),
                    git_commit=revision,
                ),
            )
            # Original object bytes include their terminal newlines.
            import subprocess

            historical_plan = {
                name: hashlib.sha256(
                    subprocess.check_output(
                        ["git", "-C", str(issuer), "show", revision + ":" + name],
                        timeout=10,
                    )
                ).hexdigest()
                for name in historical_plan
            }
        if (
            payload.get("protected_unchanged") is not True
            or payload.get("protected_artifact_sha256", {}).get(str(report_path))
            != report_sha
            or payload.get("validation_plan") != historical_plan
            or payload.get("closure_tests") != validation.PLANS[family]
            or any(payload.get(k) is not False for k in validation.AUTHORITY_FALSE)
            or type(payload.get("provider_calls")) is not int
            or payload["provider_calls"] != 0
            or type(payload.get("orders")) is not int
            or payload["orders"] != 0
            or run.is_symlink()
            or run.resolve().parent
            != (Path(data) / "report/postclose_generation_validation/runs").resolve()
            or set(evidence) != {"tests.log", "tests.xml", "network.json"}
        ):
            raise ValueError("successor_late_fixture_unbound")
        raw = {name: validation.file_bytes(run / name) for name in evidence}
        if (
            any(
                hashlib.sha256(raw[name]).hexdigest() != sha
                for name, sha in evidence.items()
            )
            or json.loads(raw["network.json"]) != {"blocked_attempts": 0}
            or type(payload.get("passed_tests")) is not int
            or validation.junit_counts(run / "tests.xml", family, raw=raw["tests.xml"])
            != payload["passed_tests"]
        ):
            raise ValueError("successor_late_fixture_evidence_invalid")
    return dict(path=str(path), sha256=sha)


# Verified native parent consumption and private fixture output; original reports remain strict.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[
    "entry_cancel_wait"
] = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get("entry_cancel_wait", ()) + (
    (
        "60620f4b8fbe73f3c0506eed8f49c27c031d74a643b68667ca7421c6512d6f57",
        "473cd48023ef70c1ed83a5cebbcbb1ee736888a177869f5b9a1d1ee95c1b4de1",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[
    "rising_missed"
] = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get("rising_missed", ()) + (
    (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "4b2ee77abed6bb9e88e87f668523b6a8b90213ecfc0643aea6ca5ebf05c070b4",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[
    "holding_vote"
] = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get("holding_vote", ()) + (
    (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "7bd73742e266ed69ddbe0705ae1f330ce58d7e960b78ec3a26a56f626ad24cc3",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[
    "auxiliary"
] = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get("auxiliary", ()) + (
    (
        "507700d07f88f668f1b467678615656db7af893e0c3e6dbf8148d5c918ed9120",
        "618c3e354a84a5b2ac6afb2887d2882f4bf9ea99321ad894eeeeda8c62af6974",
    ),
)

# Reviewed continuous holding observation producer and terminal consumer.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[
    "rising_missed"
] = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get("rising_missed", ()) + (
    (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "14e336d1cf91e37ca131a21da7735d05cb69527e96f14dab35b8c87f3e834808",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[
    "holding_vote"
] = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get("holding_vote", ()) + (
    (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "5ea5f8ab8fc464227886ccf60226e668c59f90063453b684dafc2e61a2541094",
    ),
)

# d53c36e59 binds cumulative completed bars to the frozen research source.
# Only current code capability is projected; original source/results stay intact.
# Review: docs/audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "507700d07f88f668f1b467678615656db7af893e0c3e6dbf8148d5c918ed9120",
        "8659bf2145e1b617359c6d02b3b703d4f222f3f7bdad8c8e43b5ad6a495b867a",
    ),
)


# Exact shared numeric dependency closure; fresh family fixtures remain mandatory.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["entry_cancel_wait"] += (
    (
        "60620f4b8fbe73f3c0506eed8f49c27c031d74a643b68667ca7421c6512d6f57",
        "5fa218b7b916b6b2a98a7a395573dac80ff96d2345edae3b64f9f99e3574125d",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "95023d087c8e3d03d9e2a523b93cfe620170f58b67306851f9b174f1909a0679",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "9ccabcfbfb2f0bc9f408954a6dc76c0f88b9bdf7528f4e827c83804bbf15084f",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "507700d07f88f668f1b467678615656db7af893e0c3e6dbf8148d5c918ed9120",
        "8f7446efe983c1ad88ba90c3ca72114fe9e90d045356e8c7d74acd0d4ceb62fd",
    ),
)

# Reviewed KRX listing/SOR entry-only successor; historical native reports remain unchanged.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "d48f497b194c96ca5776bacf2910a08de4c0c3a6a323c5cde1d8a30c171c15e4",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "7ea8d358191c970b16384b182f2feaa66c4486f1082f4c36cb54616df4485a81",
    ),
)


# Exact formatting successors; fresh family fixtures and original report checks remain mandatory.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["entry_cancel_wait"] += (
    (
        "60620f4b8fbe73f3c0506eed8f49c27c031d74a643b68667ca7421c6512d6f57",
        "ef975d927eb257ebce35a83fa72f79182aa9e11b763cc761e0ae34c251a1c205",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5",
        "e3107fd43332462fb9dfcbd023fbb761857ed7de5aef81387f403f7c3b712302",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "507700d07f88f668f1b467678615656db7af893e0c3e6dbf8148d5c918ed9120",
        "5b50ef4c3dcc75d943bc566219a65c66f9e237a456617e44977f78f1453d1ad8",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee",
        "d20ee98c614b51edd0c763369429c48c0c49e95deaee849faa43b45e3144e893",
    ),
)


# Reviewed 10/23 source and calculation repairs: capability alone never
# authenticates old calculation results. Native sources and fresh fixtures
# remain mandatory; affected producers are regenerated before final closure.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["entry_cancel_wait"] += (
    (
        "5fa218b7b916b6b2a98a7a395573dac80ff96d2345edae3b64f9f99e3574125d",
        "d51f14088df87ad258d719b2a4668814b6ceababd1369f8259bd188eab3b7d3f",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "d48f497b194c96ca5776bacf2910a08de4c0c3a6a323c5cde1d8a30c171c15e4",
        "fd0fe0fdc9e75ac854dca2ef5ebc1a2633409af9c10e1b4be12072588814d32d",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "7ea8d358191c970b16384b182f2feaa66c4486f1082f4c36cb54616df4485a81",
        "6f8601e48045a18659778b7ba2a942de3dde2657f96e4c3cbc9ac474ad05461a",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "8f7446efe983c1ad88ba90c3ca72114fe9e90d045356e8c7d74acd0d4ceb62fd",
        "545cdb221837794354c9031d6e7b69ef7e80c381999db833e54f0a2eadb2fa6a",
    ),
)


# Exact frozen auxiliary reader repair and shared capability inventory.
# Original reports remain unmodified; every family needs a fresh native fixture.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["entry_cancel_wait"] += (
    (
        "5fa218b7b916b6b2a98a7a395573dac80ff96d2345edae3b64f9f99e3574125d",
        "1a5f1647c8640688497416bc41eca31a029a583beb4638e30505be509d758b2b",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "d48f497b194c96ca5776bacf2910a08de4c0c3a6a323c5cde1d8a30c171c15e4",
        "b6d68e2d8af215eddfc43260e751802605eb139402f73704eea488191617b0ae",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "7ea8d358191c970b16384b182f2feaa66c4486f1082f4c36cb54616df4485a81",
        "f418aa6f7c047c947c60b1bf9f75e328dd041b00757d37a60cda04d31be9675c",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "8f7446efe983c1ad88ba90c3ca72114fe9e90d045356e8c7d74acd0d4ceb62fd",
        "40a5beb1a6cb36dafffd4fe4ac8b0d34107aa522208b80c6e508e8454fe1ca4a",
    ),
)


# Reviewed archive receipt succession and stopped workflow producer identity.
# Current source producers and fresh fixtures are still required.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["entry_cancel_wait"] += (
    (
        "5fa218b7b916b6b2a98a7a395573dac80ff96d2345edae3b64f9f99e3574125d",
        "06ec0dfd84a0865ac044ced0839f69bfe5f8f912c619d2d99861ae2a321743ae",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "d48f497b194c96ca5776bacf2910a08de4c0c3a6a323c5cde1d8a30c171c15e4",
        "6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "7ea8d358191c970b16384b182f2feaa66c4486f1082f4c36cb54616df4485a81",
        "2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "8f7446efe983c1ad88ba90c3ca72114fe9e90d045356e8c7d74acd0d4ceb62fd",
        "846bc2c07fc4742338ed17db282d913a6b14f8eab9723c9e1656d61f5f2abf23",
    ),
)


# Reviewed cancel report cache capability dependency.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["entry_cancel_wait"] += (
    (
        "5fa218b7b916b6b2a98a7a395573dac80ff96d2345edae3b64f9f99e3574125d",
        "08489f10c33b2972a0d6b86b5b5696d4558d78e51d488ea47525a55a9d0510aa",
    ),
)


# Preserve authenticated frozen wire identity through the shared envelope owner.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "8f7446efe983c1ad88ba90c3ca72114fe9e90d045356e8c7d74acd0d4ceb62fd",
        "357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd",
    ),
)


# Reviewed prepared-versus-consumed metadata only; selection and trading
# components retain their bytes. Keep both prior and current native fixtures.
REVIEWED_PREPARED_STATE_SOURCE_SUCCESSORS = {'entry_cancel_wait': ('08489f10c33b2972a0d6b86b5b5696d4558d78e51d488ea47525a55a9d0510aa', '94903d6b941788b03166eeecf842eef2cf9cc96ea613e13b6ecdd8281a7380b3'), 'rising_missed': ('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', 'c04fd6d33bc3183ee42eb9dd681be92ea94c59dfba09a9d809e7916e6429691a'), 'auxiliary': ('357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd', '82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f'), 'holding_vote': ('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', 'cfc14c1c37893a02c003674416339cdd8b9a8aec4791bb211c9c2ccefe2890a1')}
for _family, (_previous, _current) in REVIEWED_PREPARED_STATE_SOURCE_SUCCESSORS.items():
    _retained = REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[_family]
    REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[_family] += (
        (_previous, _current),
        *((old, _current) for old, current in _retained if current == _previous),
    )


# Reviewed submission timing instrumentation in the shared handler. Original
# 10/23 reports and their fixtures remain sealed; both exact current fixtures
# are independently mandatory. No family selection or trading rule changed.
# Review: docs/audits/postclose-root-cause-recovery-review-2026-10-19.md.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    ("6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7",
     "28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922"),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    ("2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0",
     "7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386"),
)


# Reviewed 95def holding-only market eligibility and exact 0B/custody repair.
# Shared handler bytes change capability generations, not these family reports.
# Bind the preserved 10/23 and 10/26 originals directly; fresh exact-generation
# fixtures remain mandatory, with their original contracts and null economics.
# Review: postclose-root-cause-recovery-review-2026-10-19.md, 2026-10-27 integration.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    ("6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7",
     "9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791"),
    ("28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922",
     "9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791"),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    ("2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0",
     "05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf"),
    ("7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386",
     "05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf"),
)


# Static native assessment proof reuse changes this declared auxiliary dependency.
# Only reviewed 10/23 and 10/26 originals may use a fresh current fixture;
# the historical report, source generation, null economics and guards stay sealed.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    ("357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd",
     "9fb5d5b0bbe17b72ca832a883b059522d725f3234fca853324308beedf73bacc"),
    ("82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f",
     "9fb5d5b0bbe17b72ca832a883b059522d725f3234fca853324308beedf73bacc"),
)


# Verified identifier and epoch-isolation reader successor. Preserve the exact
# 10/23 and 10/26 reports; fresh native fixtures are independently mandatory.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["rising_missed"] += (
    (
        "28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922",
        "995891232bb4b4274cf5a600b3b5289ed78720c9740b5375f46b73f2cb712fec",
    ),
    (
        "6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7",
        "995891232bb4b4274cf5a600b3b5289ed78720c9740b5375f46b73f2cb712fec",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["auxiliary"] += (
    (
        "357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd",
        "1bc3ca151fbde9dbee1ed28482e0fd712617542fda9cf68ccd824d405b76b8dd",
    ),
    (
        "82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f",
        "1bc3ca151fbde9dbee1ed28482e0fd712617542fda9cf68ccd824d405b76b8dd",
    ),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS["holding_vote"] += (
    (
        "2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0",
        "5a451bcdf8fee3a6a8247e51ae44c39409869de304d07ce06c2fa832a9ddf335",
    ),
    (
        "7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386",
        "5a451bcdf8fee3a6a8247e51ae44c39409869de304d07ce06c2fa832a9ddf335",
    ),
)


# Same frozen reports after preclaim diagnostic-only handler edits.
# Native fresh fixtures and original source/economic nulls remain mandatory.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', '77005017209bc2c64ee43ba0d5281fc67d40d9fb129fc053f65093401b7a174a'), ('28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922', '77005017209bc2c64ee43ba0d5281fc67d40d9fb129fc053f65093401b7a174a'))
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', 'cca052a101ebb25cbcc0ca92a50247477e8069dd9908f99c6b690c1d50170eee'), ('7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386', 'cca052a101ebb25cbcc0ca92a50247477e8069dd9908f99c6b690c1d50170eee'))

# Integrated reviewed identifier and preclaim diagnostics; preserve both originals.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', 'eaac7494caa26c3352a5331206b6e0a70272477678eb49c4b10ea51444920ee4'), ('28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922', 'eaac7494caa26c3352a5331206b6e0a70272477678eb49c4b10ea51444920ee4'))
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', '8e067cd38af5413cc51a9b8cd8ad8b166029c6685e7838439ba04190889afb27'), ('7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386', '8e067cd38af5413cc51a9b8cd8ad8b166029c6685e7838439ba04190889afb27'))

# Reviewed first-invalidation/cadence diagnostics only. Preserve original reports
# and every issued fixture; fresh exact-generation fixtures remain mandatory.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (
    ('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', '9600db0722b362ccb2eb926197ae5425b57b352d191c54f73ad51e736d89d6b3'),
    ('28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922', '9600db0722b362ccb2eb926197ae5425b57b352d191c54f73ad51e736d89d6b3'),
    ('9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791', '9600db0722b362ccb2eb926197ae5425b57b352d191c54f73ad51e736d89d6b3'),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (
    ('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', '272fd392f86ee32f42ee9a8b3b189ec0221da0250a75cfdf3adffc6706782810'),
    ('7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386', '272fd392f86ee32f42ee9a8b3b189ec0221da0250a75cfdf3adffc6706782810'),
    ('05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf', '272fd392f86ee32f42ee9a8b3b189ec0221da0250a75cfdf3adffc6706782810'),
)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['auxiliary'] += (
    ('357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd', '6a9572dc3c2bd9f7ec1897c068615b2b507b7a3794df89ac071485938898e731'),
    ('82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f', '6a9572dc3c2bd9f7ec1897c068615b2b507b7a3794df89ac071485938898e731'),
    ('9fb5d5b0bbe17b72ca832a883b059522d725f3234fca853324308beedf73bacc', '6a9572dc3c2bd9f7ec1897c068615b2b507b7a3794df89ac071485938898e731'),
)


# Integrated reviewed identifier and preclaim diagnostics; preserve both originals.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', '7849bf719462f6795bc44d19f7622309bff1c38859de133c41335fb04def509f'), ('28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922', '7849bf719462f6795bc44d19f7622309bff1c38859de133c41335fb04def509f'), ('9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791', '7849bf719462f6795bc44d19f7622309bff1c38859de133c41335fb04def509f'))
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', '24402a92575502c11660b5b72148d660f4e2d4e0961285614d046a2af2c90094'), ('7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386', '24402a92575502c11660b5b72148d660f4e2d4e0961285614d046a2af2c90094'), ('05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf', '24402a92575502c11660b5b72148d660f4e2d4e0961285614d046a2af2c90094'))
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['auxiliary'] += (('357573bd61c06c26c208be7ab5447eff3805a8efa21cf1bbf9df201be7c14ddd', '43d45b2c9d2564d25c04868f2249f14ec2220b12da00994ffa31131ad031d080'), ('82a2c8b410c97dc89db45269ee865b21e2a1ba824d55448183bdb1c25769c06f', '43d45b2c9d2564d25c04868f2249f14ec2220b12da00994ffa31131ad031d080'), ('9fb5d5b0bbe17b72ca832a883b059522d725f3234fca853324308beedf73bacc', '43d45b2c9d2564d25c04868f2249f14ec2220b12da00994ffa31131ad031d080'))
# Integrated preclaim and cadence diagnostics; original frozen inputs and
# fresh exact-generation fixture checks are retained.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (('28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922', 'b050a51dc792070ac3c28c9c81bb5b8a5d86e6dd74bffb504df3c37026bb7459'), ('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', 'b050a51dc792070ac3c28c9c81bb5b8a5d86e6dd74bffb504df3c37026bb7459'), ('77005017209bc2c64ee43ba0d5281fc67d40d9fb129fc053f65093401b7a174a', 'b050a51dc792070ac3c28c9c81bb5b8a5d86e6dd74bffb504df3c37026bb7459'), ('9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791', 'b050a51dc792070ac3c28c9c81bb5b8a5d86e6dd74bffb504df3c37026bb7459'), ('9600db0722b362ccb2eb926197ae5425b57b352d191c54f73ad51e736d89d6b3', 'b050a51dc792070ac3c28c9c81bb5b8a5d86e6dd74bffb504df3c37026bb7459'))
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (('05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf', '4cc888f24e47ab76fee5b9e67d5af44025093b2ed9b0f62de724264c2115b53d'), ('272fd392f86ee32f42ee9a8b3b189ec0221da0250a75cfdf3adffc6706782810', '4cc888f24e47ab76fee5b9e67d5af44025093b2ed9b0f62de724264c2115b53d'), ('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', '4cc888f24e47ab76fee5b9e67d5af44025093b2ed9b0f62de724264c2115b53d'), ('7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386', '4cc888f24e47ab76fee5b9e67d5af44025093b2ed9b0f62de724264c2115b53d'), ('cca052a101ebb25cbcc0ca92a50247477e8069dd9908f99c6b690c1d50170eee', '4cc888f24e47ab76fee5b9e67d5af44025093b2ed9b0f62de724264c2115b53d'))


# Report-only collection serialization/session and exact market ord_uv context.
# Only the retained native reports are reviewed; history is not transitive.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (('6d662d9e2cc6f67ec9945dfa3d9da37e3acd22765cc48a1c30d95b892a432eb7', '1a206224114b7dc0b03fdce56db85a99e1e70cb4e44b4deacd0bd73c6ea4514c'), ('28baa874610d6f76379c6be1fe4f76accbbfbc5f473b0c4ffcb2f323cdf75922', '1a206224114b7dc0b03fdce56db85a99e1e70cb4e44b4deacd0bd73c6ea4514c'), ('9019999ecd6e980cf5dfe689bed7815c08b16632c65a879b6d202c4e305bd791', '1a206224114b7dc0b03fdce56db85a99e1e70cb4e44b4deacd0bd73c6ea4514c'))
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (('2c8493a70cb399e336773c02f3d292d2f5d225fe742750089049b63ecc1a23b0', '231d058214999b2b9aa417be8b5b528e98c4499a7a54303503c44e1834e10831'), ('7f30d09769b17801ad614d2403ca5742c5a45d4e56fb27212447de1384829386', '231d058214999b2b9aa417be8b5b528e98c4499a7a54303503c44e1834e10831'), ('05037a9d11e962bb160d3fa3e589935f36ab2290d5e087b25a98f8ed5f6e81cf', '231d058214999b2b9aa417be8b5b528e98c4499a7a54303503c44e1834e10831'))

# Exact actually consumed 3178 predecessor capability.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['rising_missed'] += (('7849bf719462f6795bc44d19f7622309bff1c38859de133c41335fb04def509f', '1a206224114b7dc0b03fdce56db85a99e1e70cb4e44b4deacd0bd73c6ea4514c'),)
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS['holding_vote'] += (('24402a92575502c11660b5b72148d660f4e2d4e0961285614d046a2af2c90094', '231d058214999b2b9aa417be8b5b528e98c4499a7a54303503c44e1834e10831'),)


def current_fixture_observation(observed, data):
    if observed.get("status") == "verified" and observed.get("native_validated") is True:
        return observed
    family = observed.get("family")
    pair = REVIEWED_SUCCESSORS.get(family)
    actual_pair = (observed.get("code_sha256"), generation.code_generation(family))
    preserved = REVIEWED_PRESERVED_SOURCE_SUCCESSORS.get(family)
    if preserved and actual_pair == preserved:
        pair = preserved
    deployed = REVIEWED_DEPLOYED_SOURCE_SUCCESSORS.get(family)
    if deployed and actual_pair == deployed:
        pair = deployed
    delay = REVIEWED_DELAY_SOURCE_SUCCESSORS.get(family)
    if delay and actual_pair == delay:
        pair = delay
    prepared = REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS.get(family)
    if prepared and actual_pair == prepared:
        pair = prepared
    auxiliary_input = REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS.get(family)
    if auxiliary_input and actual_pair == auxiliary_input:
        pair = auxiliary_input
    post_aux_guard = REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS.get(family)
    if post_aux_guard and actual_pair == post_aux_guard:
        pair = post_aux_guard
    quantity_cost = REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS.get(family)
    if quantity_cost and actual_pair == quantity_cost:
        pair = quantity_cost
    delay_research = REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS.get(family)
    if delay_research and actual_pair == delay_research:
        pair = delay_research
    integrated = REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS.get(family)
    integrated_match = (
        integrated is not None
        and actual_pair == integrated
        and observed.get("source_date") == "2026-10-16"
    )
    if integrated_match:
        pair = integrated
    readonly = REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS.get(family)
    readonly_match = (
        readonly is not None
        and actual_pair == readonly
        and observed.get("source_date") == "2026-10-16"
    )
    if readonly_match:
        pair = readonly
    cleanup = REVIEWED_CLEANUP_SOURCE_SUCCESSORS.get(family)
    cleanup_match = (
        cleanup is not None
        and actual_pair == cleanup
        and observed.get("source_date") == "2026-10-16"
    )
    if cleanup_match:
        pair = cleanup
    custody = REVIEWED_RECEIPT_CUSTODY_SOURCE_SUCCESSORS.get(family)
    custody_match = custody is not None and actual_pair == custody
    if custody_match:
        pair = custody
    frozen_match = actual_pair in REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get(
        family, ()
    )
    if frozen_match:
        pair = actual_pair

    reader = REVIEWED_SOURCE_READER_SUCCESSORS.get(family)
    reader_match = (
        (reader is not None and actual_pair == reader)
        or actual_pair == REVIEWED_DELAY_CLEANUP_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_HOLDING_REPUBLICATION_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_FIXED_WAIT_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_ENTRY_RECEIPT_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_BUY_IDENTITY_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_QUANTITY_CAPTURE_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_ENTRY_COST_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_SHUTDOWN_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_SHUTDOWN_SOURCE_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_SHUTDOWN_CONSUMED_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_NATIVE_SELECTION_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_NATIVE_SELECTION_SOURCE_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_NATIVE_SELECTION_CONSUMED_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_PRE_SUBMIT_CONSUMED_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_SUBMIT_FRESH_CONSUMED_SUCCESSORS.get(family)
        or actual_pair == REVIEWED_SUBMIT_FRESH_SOURCE_SUCCESSORS.get(family)
    )
    if reader_match:
        pair = actual_pair
    source_review = None
    if (not pair or actual_pair != pair) and family in validation.PLANS:
        # A single reviewed source inventory covers every affected family.
        # It never replaces either generation's independently verified fixture.
        try:
            fixture_path = validation.fixture_path(data, family)
            candidate = (validation.bounded_object(fixture_path, 65536)[0]
                         if fixture_path.is_file() else {})
            references = candidate.get("reviewed_source_transitions", [])
            if not isinstance(references, list):
                raise ValueError("source_review_references_invalid")
            if references:
                fixture, _ = validation.verify_fixture(data, family)
            for reference in references:
                reviewed = reviewed_source_transition(reference["path"], consumer_family=family)
                if reviewed["reference"] != reference:
                    raise ValueError("source_review_reference_changed")
                if reviewed["pairs"].get(family) == list(actual_pair):
                    pair = actual_pair
                    reader_match = True
                    source_review = reviewed
        except (OSError, ValueError, KeyError, TypeError, SyntaxError,
                subprocess.SubprocessError) as exc:
            # Keep the original unverified result and the exact failure. A
            # missing new fixture must not authorize an unreviewed successor.
            return dict(observed, current_fixture_status="unverified",
                        current_fixture_reason=str(exc))
    if not pair or actual_pair != pair:
        if (
            family in validation.PLANS
            and actual_pair[0] != actual_pair[1]
            and observed.get("status") == "unverified"
            and observed.get("findings") == ["policy_generation_unverified"]
            and observed.get("missing_components") == []
            and observed.get("observation_complete") is True
            and observed.get("native_validated") is False
        ):
            return dict(
                observed,
                current_fixture_status="unverified",
                current_fixture_reason="successor_code_pair_unreviewed",
            )
        return validation.current_fixture_observation(observed, data)
    if (
        observed.get("status") != "unverified"
        or observed.get("findings") != ["policy_generation_unverified"]
        or observed.get("missing_components") != []
        or observed.get("observation_complete") is not True
        or observed.get("native_validated") is not False
    ):
        return observed
    try:
        data = Path(data)
        fixture, reference = validation.verify_fixture(data, family)
        path = validation.native_report_path(data, family, observed["source_date"])
        if Path(observed["artifact"]) != path:
            raise ValueError("successor_report_path_invalid")
        payload, report_sha = validation.read_native_report(
            data, family, observed["source_date"]
        )
        native = (
            payload["holding_path_vote_replay"] if family == "holding_vote" else payload
        )
        contract = native["policy_generation"]
        if observed.get("binding_repair") is not None:
            if family != "holding_vote":
                raise ValueError("successor_binding_family_invalid")
            contract, binding = generation._read_holding_code_rebinding(
                data, observed["source_date"], report_sha, payload
            )
            if binding != observed["binding_repair"]:
                raise ValueError("successor_binding_changed")
        original = generation.inspect(
            contract,
            family=family,
            day=observed["source_date"],
            payload=native,
            data_root=data,
        )
        keys = (
            "status",
            "findings",
            "missing_components",
            "observation_complete",
            "source_generation",
            "code_sha256",
            "contract_sha256",
            "source_state",
            "comparison_state",
            "handoff_state",
        )
        if (
            any(original[k] != observed.get(k) for k in keys)
            or report_sha != observed.get("report_sha256")
            or contract["code_sha256"] != pair[0]
            or fixture["code_sha256"] != pair[1]
        ):
            raise ValueError("successor_historical_contract_changed")
        late_report = (
            (path, report_sha)
            if any(
                actual_pair == successors.get(family)
                for successors in (
                    REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS,
                    REVIEWED_FIXED_WAIT_SUCCESSORS,
                    REVIEWED_ENTRY_RECEIPT_SUCCESSORS,
                    REVIEWED_BUY_IDENTITY_SUCCESSORS,
                    REVIEWED_QUANTITY_CAPTURE_SUCCESSORS,
                    REVIEWED_ENTRY_COST_SUCCESSORS,
                    REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS,
                    REVIEWED_SHUTDOWN_SUCCESSORS,
                    REVIEWED_SHUTDOWN_SOURCE_SUCCESSORS,
                    REVIEWED_SHUTDOWN_CONSUMED_SUCCESSORS,
                    REVIEWED_NATIVE_SELECTION_SUCCESSORS,
                    REVIEWED_NATIVE_SELECTION_SOURCE_SUCCESSORS,
                    REVIEWED_NATIVE_SELECTION_CONSUMED_SUCCESSORS,
                    REVIEWED_SUBMIT_FRESH_CONSUMED_SUCCESSORS,
                    REVIEWED_SUBMIT_FRESH_SOURCE_SUCCESSORS,
                )
            )
            else None
        )
        historical_fixture = _historical_fixture(
            contract, data, family, late_report=late_report
        )
        if (
            integrated_match
            or readonly_match
            or cleanup_match
            or custody_match
            or reader_match
            or frozen_match
        ) and historical_fixture is None:
            raise ValueError("successor_integrated_historical_fixture_required")
        current = generation.native(
            native,
            family=family,
            day=observed["source_date"],
            data_root=data,
            source_state=contract["source_state"],
            comparison_state=contract["comparison_state"],
            handoff_state=contract["handoff_state"],
        )
        verified = generation.inspect(
            current,
            family=family,
            day=observed["source_date"],
            payload=native,
            data_root=data,
        )
        if (
            verified["status"] != "verified"
            or current["fixture_receipt"] != reference
            or verified["source_generation"] != original["source_generation"]
            or current["code_sha256"] != pair[1]
            or validation.read_native_report(data, family, observed["source_date"])[1]
            != report_sha
        ):
            raise ValueError("successor_current_reader_unverified")
        if (
            historical_fixture
            and validation.file_sha(historical_fixture["path"])
            != historical_fixture["sha256"]
        ):
            raise ValueError("successor_historical_fixture_changed")
        if source_review and reviewed_source_transition(
            source_review["reference"]["path"], consumer_family=family
        ) != source_review:
            raise ValueError("source_review_changed_during_observation")
        result = deepcopy(observed)
        result.update(
            status="verified",
            findings=[],
            native_validated=False,
            current_code_capability_verified=True,
            historical_contract_status="unverified",
            verification_basis="reviewed_code_successor_fixture_for_preserved_native_report",
            current_fixture=reference,
            current_capability_contract_sha256=current["contract_sha256"],
            current_capability_code_sha256=pair[1],
            reviewed_code_pair=list(pair),
        )
        if historical_fixture:
            result["preserved_historical_fixture"] = historical_fixture
        if source_review:
            result["reviewed_source_transition"] = source_review["reference"]
        result["scopes"] = {
            family: {
                k: v
                for k, v in result.items()
                if k not in {"scopes", "family", "source_date", "artifact"}
            }
        }
        return result
    except (OSError, ValueError, KeyError, TypeError, validation.ET.ParseError) as exc:
        return dict(
            observed, current_fixture_status="invalid", current_fixture_reason=str(exc)
        )
