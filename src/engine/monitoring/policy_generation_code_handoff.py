"""Report-only capability projection across an exactly reviewed code successor.

Ownership: monitoring, separate from native report/policy publication. Original
contracts and source bytes remain historical; no strategy authority is granted.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import policy_generation_validation as validation

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
    'entry_cancel_wait': (
        'd8583947a62ffe15318b2819f6f4824b8835a7fc5865c5b00f85b8eb427620b0',
        '4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db'),
    'rising_missed': (
        'dfe2d56deef10ebaf4f2aa6e3edd6215f769d08ba8ac123808459c2cc8fb720f',
        '676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962'),
    'auxiliary': (
        '88a496105946f292ae3c85028be6276009738742a0916f7c9965c9c9ba6959df',
        '2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4'),
    'holding_vote': (
        'b2087e97e70fc145620d3440c4fddafd633ab8e45d3aa492fffec17a7b04bcab',
        '8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf'),
}

# The next dated native report already carries the formerly reviewed successor.
# Preserve that report too; do not relabel it as the older source generation.
REVIEWED_PRESERVED_SOURCE_SUCCESSORS = {
    # Exact 10/15 native reports retained after source-census and residual
    # custody repairs. Revalidate their original fixtures and source bodies;
    # current capability does not promote their comparison/selection state.
    'entry_cancel_wait': (
        'b2a2017deb606554fbe1c9d481426786b3a8ab463c948ee84cd8ab856eddfca0',
        '4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db'),
    'rising_missed': (
        'dde49a32b7299deabf981e9f3a734a9da3019ba3f4e3eb7abbaff91dd3d01fa3',
        '676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962'),
    'holding_vote': (
        '5658a73a4aeb866c3124370eddc500ce27dd2e15589ba2ef4d7c35c7231a83c2',
        '8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf'),
}


# The actual 4c65523b2 source generation is also preserved if already reported.
REVIEWED_DEPLOYED_SOURCE_SUCCESSORS = {
    'entry_cancel_wait': ('6d6a294941f6337d48420514d40e36891d25b44dc09bd914be0831d897794d4c', '4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db'),
    'rising_missed': ('0f6c455328de656c920956be0b2a24fec57db08f8b4e7b3e2fa7db43249ff7ed', '676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962'),
    'auxiliary': ('711184e6d93f27e3d8f4bdd97598f4880f752332f850763b32b434560b460f8e', '2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4'),
    'holding_vote': ('e213bbe524aa7575f8e9c784cf43db77b9c194dee5bfc03b943a8175fc655278', '8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf'),
}


# Delay situation/zero-cell observer repair touches shared handler metadata.
# Preserve the selected predecessor's report generation and require a new fixture.
# Review: docs/audits/pre-submit-semantic-implementation-review-2026-10-16.md.
REVIEWED_DELAY_SOURCE_SUCCESSORS = {'rising_missed': ('ea1ac91b6e080d96f3a0d61dca47575c101862ba6fe77fed36fc6170687f3e08', '676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962'), 'holding_vote': ('dfd762fa2b9d15799e4951bc5624effa58f8efdec29cb85939ba9d5e21765d58', '8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf')}


REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS = {'entry_cancel_wait': ('2e0ba14946a5e9e191a95529971e103136679957ddd7458678ed6c27a0e4a234', '4ba29d895111f69ebfda0eb72076270579f4a49af0b46b74cf16e762ea9647db'), 'rising_missed': ('e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874', '676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962'), 'auxiliary': ('d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0', '2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4'), 'holding_vote': ('057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce', '8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf')}


# Exact original 10/16 report to the reviewed auxiliary input/research reader.
# Preserve the prior prepared pair and its historical fixtures independently.
# This is code capability only: a fresh exact-generation fixture remains
# mandatory, and comparison/selection state and runtime authority stay intact.
# Review: docs/audits/main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md.
REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS = {
    'auxiliary': (
        'd04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0',
        'dea0b4f9d124372e48413635f5f82fbf3f0fbd6477a4f1beaca6769a68e9990b'),
}


# Exact original 10/16 reports to the reviewed post-auxiliary guard repair.
# Only shared entry-handler bytes changed in these family generations. Keep
# their original contracts, states and fixtures; independently validate the
# current capability without granting selection, runtime or profit authority.
# Review: docs/audits/main-post-auxiliary-priority-repair-review-2026-10-17.md.
REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS = {
    'rising_missed': (
        'e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874',
        'b47474ed46cc63f090ccf14ce40b6d53b1d1518cba43211e648a1ee1b0f2aa36'),
    'holding_vote': (
        '057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce',
        '02b637bfb01bb9f01b4d8b33672d2ae0d9be74ff07c3ee972608f0c55beaf2e5'),
}


# Direct original 10/16 report to the reviewed quantity cost reader. Its
# research-only projection changes shared code identities, not actual holding
# economics. Preserve every older target and independently require the exact
# current holding fixture; do not chain earlier historical contracts forward.
# Review: docs/proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md section 8.
REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS = {
    'holding_vote': (
        '057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce',
        '6c4734c5e4204b36faf3d72ee873a429147d7a6e5a3a019d55fee29f4e145137'),
}


# Original 10/16 report generations to the reviewed delay observation repair
# and bounded shard reader. Numeric policies and historical results retain
# their own contracts; independent exact-current fixtures remain mandatory.
# Review: docs/audits/pre-submit-delay-situation-research-implementation-review-2026-10-17.md.
REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS = {
    'rising_missed': (
        'e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874',
        '5f8cd733ba9fb8b4733f3bafbc5a9431d45d6638713934daf74ba144844d74a5'),
    'holding_vote': (
        '057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce',
        'e06ee4b2d6d09410dd81d88cb661b6a18df2ca1dea2e7e81823a7d6e03d24b46'),
}


# Direct frozen 10/16 native reports to the reviewed integrated research code.
# The shared Claim helper is now a capability dependency, so all four families
# have new fixture paths. Preserve every previous pair and receipt; this is
# source/reader capability, not economic selection or runtime/performance PASS.
# Review: docs/audits/main-research-integrated-p5-p6-deployment-review-2026-10-18.md.
REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS = {
    'entry_cancel_wait': (
        '2e0ba14946a5e9e191a95529971e103136679957ddd7458678ed6c27a0e4a234',
        '4bf8bb24955fa5889d9090bcbbee1fd317493f0841d2a5a46566453291a5e907'),
    'rising_missed': (
        'e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874',
        '7fa7a62c8bd2f75b7218cee881ea1cffd41c4ade083b97fc73c0559693447aeb'),
    'auxiliary': (
        'd04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0',
        'a249dbc9baa7fb5e05a36481cf476083de6c8b7ad369e3b26ceb7f3ba74373b5'),
    'holding_vote': (
        '057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce',
        'e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea'),
}


# Read-only startup preparation changes auxiliary's V6 reader bytes. Preserve
# the original 10/16 report and every prior target; this separate exact pair
# requires both the original fixture and an independent current fixture.
REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS = {
    'auxiliary': (
        'd04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0',
        '00e4f1813805e520e9daed86fa1b71b55c06f76c7128b4ad7762d978ab956822'),
}


# Reviewed cleanup successor, bound directly to the preserved 10/16 reports.
# A historical fixture and an independent current fixture are both mandatory.
REVIEWED_CLEANUP_SOURCE_SUCCESSORS = {'auxiliary': ('d04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0',
               'b54dc1696e819566a5c9c785c24d171caed2887aace05297e391bd1722ea995d'),
 'entry_cancel_wait': ('2e0ba14946a5e9e191a95529971e103136679957ddd7458678ed6c27a0e4a234',
                       '47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff'),
 'holding_vote': ('e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea',
                  '791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b'),
 'rising_missed': ('e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874',
                   'd23d80552d0453697e61757b2f0f1081509316868c02166afdb7adf848b20b32')}


# Exact reviewed receipt/identity repair; source bytes and prior fixtures stay sealed.
REVIEWED_RECEIPT_CUSTODY_SOURCE_SUCCESSORS = {'auxiliary': ('80497557e7be71c0eafcdaa4bd7256250c66899a791510efa2f98f81cbcbbc05',
               'b54dc1696e819566a5c9c785c24d171caed2887aace05297e391bd1722ea995d'),
 'entry_cancel_wait': ('3acc183fa1d6675d4113b6f8faeccbb52bb58e214461508578e5b7e475cd6270',
                       '47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff'),
 'holding_vote': ('69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11',
                  '791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b'),
 'rising_missed': ('1f524a5ad98e623501eaaa2d7c81773ac0ad6328237d72ea0c95c0c8cd1251bb',
                   'd23d80552d0453697e61757b2f0f1081509316868c02166afdb7adf848b20b32')}

# Fresh native fixtures are mandatory for the frozen-input/census successor.
# Each historical source retains its own original fixture and semantic state.
REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS = {'holding_vote': (
    ('69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11',
     '3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc'),
    ('e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea',
     '3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc'),
    ('791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b',
     '3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc'),
    ('69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11',
     'bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db'),
    ('e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea',
     'bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db'),
    ('791757cb183525948b6378ee41deaa3ab03828ee4bdaea851bdfb653b804804b',
     'bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db'),
    ('3eeed519ccccdc4f3f0285577f1a6a22c217a505b5157a64577fe09d8b2ffafc',
     'bf082809aeb6ea19715f20951d6459f9c015413dd8277c23d1b5b92d9aa4e4db'),
)}

# SourceReadReduction1020: preserved native reports need independent fixtures
# for the exact report-reader successor, never a rewritten historical contract.
REVIEWED_SOURCE_READER_SUCCESSORS = {
    'rising_missed': ('1f524a5ad98e623501eaaa2d7c81773ac0ad6328237d72ea0c95c0c8cd1251bb',
                      'c71f1a1954a515f59bf551c8ea6e674415c2fd96f5e8e7a742fb85a56fa7493a'),
    'auxiliary': ('80497557e7be71c0eafcdaa4bd7256250c66899a791510efa2f98f81cbcbbc05',
                  'cc663fc62f34bd39f01591c15b13977aa50043f2fe1579291bf719ed3fb496e7'),
}

# Delay-v4 identity diagnostics and unreachable PYRAMID helper removal. Keep
# issued pairs above; these exact successors require independent fresh fixtures
# while preserving the original native report and its historical fixture.
REVIEWED_DELAY_CLEANUP_SUCCESSORS = {
    'rising_missed': ('1f524a5ad98e623501eaaa2d7c81773ac0ad6328237d72ea0c95c0c8cd1251bb',
                      '8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d'),
    'auxiliary': ('80497557e7be71c0eafcdaa4bd7256250c66899a791510efa2f98f81cbcbbc05',
                  '4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac'),
    'holding_vote': ('69b00417b7396d7a15840c7f0a53ef91399d755d430fb3017a9d0596127d8b11',
                     'b447ff4c7e39ed9f1d1884c3d032b567225d51b92d121c91e24c280c9e84c72b'),
}


# d7d353b4a repairs holding-source republication in runtime_approval_summary.
# That shared summary dependency changes these two capability generations;
# their own producer/selection/publisher/reader bytes are unchanged. Preserve
# the original 10/20 contracts and require both old and fresh native fixtures.
# Review: docs/audits/postclose-root-cause-recovery-review-2026-10-19.md.
REVIEWED_HOLDING_REPUBLICATION_SUCCESSORS = {
    'entry_cancel_wait': (
        '47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff',
        'e1c56d2cfc3612794fe8cc4d638b25c72f7643cb8f894a88a2a46f532df12b82'),
    'auxiliary': (
        '4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac',
        'a2c47ec94d9ae8e1866af911d9de2426cf04a394f41a5dca893e90e16fc12a93'),
}

# Exact source-only historical decision disposition; fresh fixtures remain mandatory.
REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS = {
    'holding_vote': ('48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3',
                     'f1aa713f7fd76467bd78c17fb0890eee55421d4ed18c865eeca0a8edc03518db'),
}


# Exact revived-watch observation metadata successor; historical reports stay sealed.
REVIEWED_FIXED_WAIT_SUCCESSORS = {'rising_missed': ('8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d',
                   '349dd5b7e1286c462ad418ed2b8332dd95020b95b19e164720ce311439ddc646'),
 'holding_vote': ('48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3',
                  '0065b34f2b56538b406ac2a2e78b2ee57fb76a88bcd3bf1e315a2d090bdb2733')}


# Exact residual receipt custody and unit-leg inventory recovery successor.
REVIEWED_ENTRY_RECEIPT_SUCCESSORS = {'entry_cancel_wait': ('47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff',
                       'ef7a5a2134321f14b1c64a45a7f0987807a70f5623a450197e086978e1b9818e'),
 'rising_missed': ('8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d',
                   '12fc26d917da97f6c8478e1639f531d161cfd4085a283db372ea9ee1efd8a53a'),
 'holding_vote': ('48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3',
                  '4a2b6c4e105eb2ca538807222ce0b49ad189829f7a64d1d18dd4828b94a5e94f')}


# Completed owned-entry recovery also persists its native holding BUY identity.
REVIEWED_BUY_IDENTITY_SUCCESSORS = {'entry_cancel_wait': (
    '47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff',
    '2382694e568af306027b58857aa2b5dff6fa0093347f4c8220a8ae6be001adef')}


# Exact quantity capture/context projection successor. Both original report
# and independent current fixture remain required; no historical verdict reuse.
REVIEWED_QUANTITY_CAPTURE_SUCCESSORS = {
    'rising_missed': ('8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d',
                     'dbfecb3ffb0a046b87010972feda7f88a9c1a538e1fdf38f4c807b1d9d355b9c'),
    'holding_vote': ('48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3',
                     'e94a9f0baa91f88041c52474b79238fca6ef71f528ff4bc07c9f832303c11d01'),
}


# Exact integrated source/receipt/cost and validation-owner successor.
# Original report/fixture and independent current fixture remain mandatory.
REVIEWED_ENTRY_COST_SUCCESSORS = {'auxiliary': ('4de7ce95386f5c05863e8e3fb56899c71ef16da99bdf75cd0e3aa426a150eeac',
               '581c21738b7a098e1900fcec2063e257b7f8ab71cce046ef4a8eb0b6fe41e8bd'),
 'entry_cancel_wait': ('47eb1ef2e45d3c48e663f6b3df505bc95da07fc6bcd168394441840af4764fff',
                       '88275729dd03ed1f0de7bb562a85fab49e1212447da4a268fb3cd9e175389313'),
 'holding_vote': ('48b92485c831e215a1d7fe1ef8664113d68186e040a768087cbcb18ab0892ac3',
                  '6890da33a6cad5b8e34280b9c39ccb6d478d81d1ad1c52aea222a296486502de'),
 'rising_missed': ('8c2725f4e329c95b79a74df8167bc5bbab80d6e08fe80fb6d7e4aaaa4d4c6e8d',
                   'b6d966e440e92d57a8874814c3fcc2dfe9c0eab54603d8c9c6f2e93734b240f7')}


REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS = {'auxiliary': ('a2c47ec94d9ae8e1866af911d9de2426cf04a394f41a5dca893e90e16fc12a93',
               '581c21738b7a098e1900fcec2063e257b7f8ab71cce046ef4a8eb0b6fe41e8bd'),
 'entry_cancel_wait': ('2382694e568af306027b58857aa2b5dff6fa0093347f4c8220a8ae6be001adef',
                       '88275729dd03ed1f0de7bb562a85fab49e1212447da4a268fb3cd9e175389313'),
 'holding_vote': ('e51ef1e839e2bf60aa7ecb7dd4eaed2d701c01816dc37298402701de9b75a9cd',
                  '6890da33a6cad5b8e34280b9c39ccb6d478d81d1ad1c52aea222a296486502de'),
 'rising_missed': ('75040f633f59cdadf8302ea2e68efdc05b1174f92c3caa73780d71e8e37bcd7e',
                   'b6d966e440e92d57a8874814c3fcc2dfe9c0eab54603d8c9c6f2e93734b240f7')}


def _historical_fixture(contract, data, family, *, late_report=None):
    """Preserve a prior fixture without using it to certify the successor."""
    reference = contract.get('fixture_receipt')
    if reference is None and late_report is None:
        return None
    path = Path(data)/'report/postclose_generation_validation'/(
        family+'_'+contract['code_sha256']+'.json')
    referenced = Path(str((reference or {}).get('path') or '')) if isinstance(reference, dict) else Path('.')
    if not referenced.is_absolute():
        referenced = Path(data).parent / referenced
    if reference is not None and (not isinstance(reference, dict) or referenced.resolve() != path.resolve()):
        raise ValueError('successor_historical_fixture_path_invalid')
    payload, sha = validation.bounded_object(path, 65536)
    if (path.is_symlink() or reference is not None and sha != reference.get('sha256')
            or payload.get('schema') != 'postclose_generation_fixture_receipt_v1'
            or payload.get('family') != family or payload.get('status') != 'pass'
            or payload.get('code_sha256') != contract['code_sha256']
            or not payload.get('closure_tests') or payload.get('unresolved_findings') != []
            or payload.get('receipt_sha256') != generation.digest(
                {k:v for k,v in payload.items() if k != 'receipt_sha256'})
            or payload.get('runtime_effect') is not False
            or payload.get('actual_pid_consumed') is not False
            or payload.get('actual_profit_verified') is not False
            or payload.get('allowed_runtime_apply', False) is not False):
        raise ValueError('successor_historical_fixture_invalid')
    if reference is None:
        # A native fixture may be published after an immutable report. Accept
        # only this exact reviewed successor and the fixture's own protected
        # original report binding; do not invent a reference in that report.
        report_path, report_sha = late_report
        run = Path(payload.get('validation_run', ''))
        evidence = payload.get('evidence') or {}
        historical_plan = validation.plan_identity(family)
        if payload.get('validation_plan') != historical_plan:
            # A later fixture-validator repair does not rewrite the original
            # native evidence. Bind that plan to its exact clean issuer tree.
            from src.engine.infrastructure import runtime_release_router as router
            issuer = Path(str(payload.get('release_root') or ''))
            revision = payload.get('git_commit')
            router.validate_release(Path(data).resolve().parent, dict(
                schema='runtime_release_selection_v1',workspace=str(Path(data).resolve().parent),
                release_root=str(issuer),git_commit=revision))
            # Original object bytes include their terminal newlines.
            import subprocess
            historical_plan = {name:hashlib.sha256(subprocess.check_output(
                ['git','-C',str(issuer),'show',revision+':'+name],timeout=10)).hexdigest()
                for name in historical_plan}
        if (payload.get('protected_unchanged') is not True
                or payload.get('protected_artifact_sha256', {}).get(str(report_path)) != report_sha
                or payload.get('validation_plan') != historical_plan
                or payload.get('closure_tests') != validation.PLANS[family]
                or any(payload.get(k) is not False for k in validation.AUTHORITY_FALSE)
                or type(payload.get('provider_calls')) is not int or payload['provider_calls'] != 0
                or type(payload.get('orders')) is not int or payload['orders'] != 0
                or run.is_symlink() or run.resolve().parent != (Path(data)/'report/postclose_generation_validation/runs').resolve()
                or set(evidence) != {'tests.log', 'tests.xml', 'network.json'}):
            raise ValueError('successor_late_fixture_unbound')
        raw = {name: validation.file_bytes(run/name) for name in evidence}
        if (any(hashlib.sha256(raw[name]).hexdigest() != sha for name,sha in evidence.items())
                or json.loads(raw['network.json']) != {'blocked_attempts': 0}
                or type(payload.get('passed_tests')) is not int
                or validation.junit_counts(run/'tests.xml', family, raw=raw['tests.xml']) != payload['passed_tests']):
            raise ValueError('successor_late_fixture_evidence_invalid')
    return dict(path=str(path), sha256=sha)


def current_fixture_observation(observed, data):
    family = observed.get('family')
    pair = REVIEWED_SUCCESSORS.get(family)
    actual_pair = (observed.get('code_sha256'), generation.code_generation(family))
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
    integrated_match = (integrated is not None and actual_pair == integrated
                        and observed.get('source_date') == '2026-10-16')
    if integrated_match:
        pair = integrated
    readonly = REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS.get(family)
    readonly_match = (readonly is not None and actual_pair == readonly
                     and observed.get('source_date') == '2026-10-16')
    if readonly_match:
        pair = readonly
    cleanup = REVIEWED_CLEANUP_SOURCE_SUCCESSORS.get(family)
    cleanup_match = (cleanup is not None and actual_pair == cleanup
                     and observed.get('source_date') == '2026-10-16')
    if cleanup_match:
        pair = cleanup
    custody = REVIEWED_RECEIPT_CUSTODY_SOURCE_SUCCESSORS.get(family)
    custody_match = custody is not None and actual_pair == custody
    if custody_match:
        pair = custody
    frozen_match=actual_pair in REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS.get(family, ())
    if frozen_match:
        pair = actual_pair

    reader = REVIEWED_SOURCE_READER_SUCCESSORS.get(family)
    reader_match = ((reader is not None and actual_pair == reader)
                    or actual_pair == REVIEWED_DELAY_CLEANUP_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_HOLDING_REPUBLICATION_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_FIXED_WAIT_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_ENTRY_RECEIPT_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_BUY_IDENTITY_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_QUANTITY_CAPTURE_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_ENTRY_COST_SUCCESSORS.get(family)
                    or actual_pair == REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS.get(family))
    if reader_match:
        pair = actual_pair
    if not pair or actual_pair != pair:
        return validation.current_fixture_observation(observed, data)
    if (observed.get('status') != 'unverified' or observed.get('findings') != ['policy_generation_unverified']
            or observed.get('missing_components') != [] or observed.get('observation_complete') is not True
            or observed.get('native_validated') is not False):
        return observed
    try:
        data = Path(data)
        fixture, reference = validation.verify_fixture(data, family)
        path = validation.native_report_path(data, family, observed['source_date'])
        if Path(observed['artifact']) != path:
            raise ValueError('successor_report_path_invalid')
        payload, report_sha = validation.bounded_object(path, 8*1024*1024)
        native = payload['holding_path_vote_replay'] if family == 'holding_vote' else payload
        contract = native['policy_generation']
        if observed.get('binding_repair') is not None:
            if family != 'holding_vote':
                raise ValueError('successor_binding_family_invalid')
            contract, binding = generation._read_holding_code_rebinding(
                data, observed['source_date'], report_sha, payload)
            if binding != observed['binding_repair']:
                raise ValueError('successor_binding_changed')
        original = generation.inspect(contract, family=family, day=observed['source_date'],
                                      payload=native, data_root=data)
        keys = ('status','findings','missing_components','observation_complete','source_generation',
                'code_sha256','contract_sha256','source_state','comparison_state','handoff_state')
        if (any(original[k] != observed.get(k) for k in keys)
                or report_sha != observed.get('report_sha256') or contract['code_sha256'] != pair[0]
                or fixture['code_sha256'] != pair[1]):
            raise ValueError('successor_historical_contract_changed')
        late_report = ((path, report_sha) if any(actual_pair == successors.get(family)
            for successors in (REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS,
                               REVIEWED_FIXED_WAIT_SUCCESSORS, REVIEWED_ENTRY_RECEIPT_SUCCESSORS,
                               REVIEWED_BUY_IDENTITY_SUCCESSORS, REVIEWED_QUANTITY_CAPTURE_SUCCESSORS,
                               REVIEWED_ENTRY_COST_SUCCESSORS, REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS)) else None)
        historical_fixture = _historical_fixture(contract, data, family, late_report=late_report)
        if (integrated_match or readonly_match or cleanup_match or custody_match or reader_match or frozen_match) and historical_fixture is None:
            raise ValueError('successor_integrated_historical_fixture_required')
        current = generation.native(native, family=family, day=observed['source_date'], data_root=data,
            source_state=contract['source_state'], comparison_state=contract['comparison_state'],
            handoff_state=contract['handoff_state'])
        verified = generation.inspect(current, family=family, day=observed['source_date'], payload=native, data_root=data)
        if (verified['status'] != 'verified' or current['fixture_receipt'] != reference
                or verified['source_generation'] != original['source_generation']
                or current['code_sha256'] != pair[1] or validation.file_sha(path) != report_sha):
            raise ValueError('successor_current_reader_unverified')
        if historical_fixture and validation.file_sha(historical_fixture['path']) != historical_fixture['sha256']:
            raise ValueError('successor_historical_fixture_changed')
        result = deepcopy(observed)
        result.update(status='verified', findings=[], native_validated=False,
            current_code_capability_verified=True, historical_contract_status='unverified',
            verification_basis='reviewed_code_successor_fixture_for_preserved_native_report',
            current_fixture=reference, current_capability_contract_sha256=current['contract_sha256'],
            current_capability_code_sha256=pair[1], reviewed_code_pair=list(pair))
        if historical_fixture:
            result['preserved_historical_fixture'] = historical_fixture
        result['scopes'] = {family:{k:v for k,v in result.items() if k not in {'scopes','family','source_date','artifact'}}}
        return result
    except (OSError, ValueError, KeyError, TypeError, validation.ET.ParseError) as exc:
        return dict(observed, current_fixture_status='invalid', current_fixture_reason=str(exc))
