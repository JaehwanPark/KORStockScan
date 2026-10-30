"""One-process, read-only code compatibility inside real startup isolation.

The trusted parent authenticates native origin and source-delta proofs before
launch. This child rebinds those proofs to its actual request, kernel boundary,
Git identity and unchanged bytes. It issues no operational handoff or PID claim.
"""

from __future__ import annotations

import ast
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

SCHEMA = "main_startup_validation_code_context_v1"
PROOF_SCHEMA = "main_startup_validation_consumer_code_handoff_v1"
REQUEST_SCHEMA = "main_policy_load_exit_validation_v1"
ROOT = Path(__file__).resolve().parents[3]
_FAMILIES = {
    "pre_submit_delay": ("pre_submit_delay_handoff", "policy_sha256"),
    "main_stop": ("main_stop_confirmation_receipt", "policy_sha256"),
    "holding_vote": ("holding_path_vote_policy_receipt", "bundle_sha256"),
}
_CONTEXT = None
_MAX_JSON = 8 * 1024 * 1024
# Exact source-only cold preparation repairs. Filled with reviewed Git bytes;
# no AST fallback, runtime authority, or policy resealing is granted here.
REVIEWED_PREPARATION_SOURCES = {
    "src/engine/scalping/continuous_reversal_policy_v4.py": (
        "9b1e7ba3fefb6df1c6dc20a0c336f30b006ce982f38764c819a91f5e3f091e4f",
        "85b0611a73c4d7fbbc3b2c2e264a0f7858f78f604f8e58e5face4f760ad4b437",
    ),
    "src/engine/scalping/continuous_reversal_policy_v5.py": (
        "aad55bc63fbca8ac95d5ec451dea2c741cb857d324959241e5d809b40b7b5278",
        "5f0ce37100b6453c0d143c79007ca45ba77466ffad40f7298a802709c926acb8",
    ),
    "src/engine/scalping/continuous_reversal_policy_v6.py": (
        "b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79",
        "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
    ),
    "src/engine/scalping/entry_machine_source_recovery.py": (
        "0445f51d0cef807be7639cc41d83581efc015922379c5000fd852b5545f89693",
        "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
    ),
    "src/engine/scalping/reversal_anchor_index.py": (
        "db0c746e27c1f7b914d9250a7336f9fdbb0040756209590e13ff0b309b045dd1",
        "1070133ec9af5500ab139a25f77f2ad9aef3049e9232d341d89188a689a7c37b",
    ),
    "src/engine/scalping/reversal_auxiliary_input_transition.py": (
        "9e1a206b22e83512eb544201c92b707aca965ef195f8a3698da138a248ccb8cb",
        "07f6af4e43b8fb69a9f1e414d60a4930c7063074f78ffdb0a80789987070cbcb",
    ),
    "src/engine/scalping/reversal_auxiliary_next_session.py": (
        "c1dffd84447b3b8d5d23eece11d0e48fece8e0467dc439c6f2458ca6fd89b726",
        "c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1",
    ),
    "src/engine/scalping/reversal_current_backend.py": (
        "341b69b19717fa4b994619bb9ea28f76b13362e379f4c494929ad9d4d33ac329",
        "c831b0366ee488eddb9f709ef7811c44cceef58646c1b1e00b2bcc3eb55f4153",
    ),
    "src/engine/scalping/reversal_evaluation_context.py": (
        "c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43",
        "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
    ),
    "src/engine/scalping/reversal_extended_runtime.py": (
        "718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc",
        "f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b",
    ),
    "src/engine/scalping/reversal_operating_backend.py": (
        "9ed32405a902a2de68aa9e5e9ed995d81425d6d76e3279c775d60448e57686f8",
        "df60d4ef78cca385b9b7b57a9c82a74efb8d943da6855ac34dd6bf1ebb24b0a6",
    ),
    "src/engine/scalping/reversal_operating_runtime.py": (
        "06d73bedadc04750c9679e2ff7c1e082e7c889972f5398490da6d0163865bb56",
        "344a03decd050bbd6767e0073c96b8da6384b9ad329e41a70e1ad7f62066533e",
    ),
    "src/engine/scalping/reversal_path_runtime.py": (
        "476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced",
        "ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36",
    ),
}
MAIN_PROOF_SCHEMA = "startup_main_preparation_code_handoff_v1"

# Preserve both the issued preparation and its reviewed same-day stopped carry.
# Evidence: docs/audits/preopen-alert-repair-2026-10-19.md.
REVIEWED_PREPARATION_HISTORY = {
    # Issued native invalidation receipt lineage; source rejection is preserved.
    "src/engine/scalping/entry_machine_source_recovery.py": {
        (
            "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "a78c70c5c49169ccb57069df7a524a540a33b615617a49195ddbc343ff9602a5",
        ),
    },
    "src/engine/scalping/reversal_code_handoff.py": {
        (
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
        )
    },
    # 0255 source-reader successor: identical cumulative selection over a
    # one-symbol-at-a-time frozen source; require the exact reviewed bytes.
    "src/engine/scalping/reversal_cumulative_postclose.py": {
        (
            "708ee7428c494f67a7407e5093771f8ddf45ba67227073bea05ff5d87a172493",
            "6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87",
        ),
    },
    # Reviewed Main SOR eligibility union; exact native signal parity is
    # required separately by the active-policy handoff before any drain.
    "src/trading/market/session_contract.py": {
        (
            "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "dfd0ff3b2a28d8d6581a44762e5b618ae807fdc1c45d7f8cd3128b76be83573c",
        ),
    },
    # Startup log consolidation only; fixed compact model selection is unchanged.
    "src/engine/ai_engine_openai.py": {
        # Source-invalid provenance from the consumed fc51 adapter, no promotion.
        # Local deadline terminals preserve capture/request identity without sending.
        (
            "3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7",
            "9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56",
        ),
        (
            "3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7",
            "808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25",
        ),
        (
            "194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584",
            "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
        ),
        # Issued role-latency successor, already bound by the active handoff.
        (
            "194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584",
            "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
        ),
    },
    "src/engine/scalping/ai_decision_trace.py": {
        # Preserve raw failed input without an unperformed quote outcome label.
        (
            "dfbb14a03971bcfa1f8a0b4c1f3b712d45e7da7fa7259cac125db7f5bb8747a0",
            "ad480ce1fb75ce2ec9217e4623e5de31dfd83e9ff62520934ab0317da60e973b",
        ),
    },
    "src/engine/scalping/reversal_auxiliary_next_session.py": {
        (
            "c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1",
            "eacdffe20114a954e7111026b02ff9c8bdaeb03383e8effa2f78a45a5566e02f",
        ),
        (
            "c1dffd84447b3b8d5d23eece11d0e48fece8e0467dc439c6f2458ca6fd89b726",
            "301bbe9cc29efa2be9ed9f84b4d919ab1f9adaeae7b2e36ec45a58f3842bdefa",
        ),
        (
            "301bbe9cc29efa2be9ed9f84b4d919ab1f9adaeae7b2e36ec45a58f3842bdefa",
            "c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1",
        ),
    },
}


# Reviewed stopped-origin custody/source recovery; original runtime guards stay unchanged.
REVIEWED_PREPARATION_HISTORY["src/engine/scalping/reversal_code_handoff.py"].update(
    {
        (
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
        ),
        (
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
        ),
    }
)

REVIEWED_PREPARATION_HISTORY["src/engine/scalping/reversal_code_handoff.py"].update(
    {
        (
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
        ),
        (
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
        ),
        (
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
        ),
        (
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
        ),
    }
)


REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_policy_v6.py", set()
).update(
    {
        (
            "b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79",
            "b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2",
        ),
        (
            "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
            "b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2",
        ),
    }
)

REVIEWED_PREPARATION_HISTORY["src/engine/scalping/reversal_code_handoff.py"].update(
    {
        (
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
        ),
        (
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
        ),
        (
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
        ),
        (
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
        ),
        (
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
        ),
    }
)

# Reviewed role-based native rollover ancestry for the identical future policy.
REVIEWED_PREPARATION_HISTORY["src/engine/scalping/reversal_code_handoff.py"].update(
    {
        (
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
        ),
        (
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
        ),
        (
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
        ),
    }
)

REVIEWED_PREPARATION_HISTORY["deploy/run_threshold_cycle_postclose.sh"] = {
    (
        "c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470",
        "dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067",
    )
}
# Reviewed source quarantine -> native index -> cost consumer handoff.
REVIEWED_PREPARATION_HISTORY["deploy/run_threshold_cycle_postclose.sh"].update(
    {
        (old, "ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac")
        for old in (
            "c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470",
            "dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067",
        )
    }
)


# Reviewed immutable auxiliary snapshots and explicit native active-parent source closure.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_code_handoff.py", set()
).update(
    {
        (
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
            "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
        ),
        (
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
            "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
        ),
        (
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
            "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_tuning.py", set()
).update(
    {
        (
            "a8ac3de954b2d6e89e3a46bb49501edc0d35df47621900a1d22b6d8492672412",
            "0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a",
        )
    }
)

# Exact indexed-reader health successor; historical targets remain independent.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/submission_bottleneck_monitor.py", set()
).update(
    {
        (old, "808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57")
        for old in (
            "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
            "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
            "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
        )
    }
)

# Reviewed9a8 -> sentinel/972 source-contract integration; no policy changes.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/buy_funnel_sentinel.py", set()
).update(
    {
        (
            "4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1",
            "40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a",
        ),
        (
            "6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993",
            "40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a",
        ),
        (
            "b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7",
            "40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/holding_exit_sentinel.py", set()
).update(
    {
        (
            "a02066a6f6538f7b4f855c5cc93ed3b5b4e661f4516c6191cd4859542cc5afdb",
            "7ae845b51d16bf425337e4758d1f83047f1f4e1c3479d39875523f0e2748012a",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/submission_bottleneck_monitor.py", set()
).update(
    {
        (
            "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
        ),
        (
            "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
        ),
        (
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
        ),
        (
            "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/sentinel_summary_contract.py", set()
).update(
    {
        (
            "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
            "182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb",
        ),
        (
            "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
            "182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb",
        ),
        (
            "28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565",
            "182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb",
        ),
        (
            "c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117",
            "182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_sniper_v2.py", set()).update(
    {
        (
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
            "02ecf7b4a55042fbcd2a7b4f59bf8602bed6020730f0a8bb326b41d5d6418866",
        ),
        (
            "f88f16a8747ba64edc7594e5936dcf6d7e636fd07d852932635204c44384d4a8",
            "02ecf7b4a55042fbcd2a7b4f59bf8602bed6020730f0a8bb326b41d5d6418866",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_websocket.py", set()).update(
    {
        (
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
            "ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
        ),
        (
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
        ),
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
        ),
        (
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/pre_submit_delay_observation.py", set()
).update(
    {
        (
            "99d7b8d5e57ad886433747cee55f8f12c9a71d539577d94adff03543a8ff724d",
            "225bf41983835e7ab53febd50d0cb42d13ce5b296322887a519a53e24281e8ff",
        )
    }
)

# Exact frozen-master gzip source repair; original policy/custody stay unchanged.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/main_trailing_source_reuse.py", set()
).update(
    {
        (
            "4c38cd9add7e87e7a50529f1a0ad379dde4b786fb8405bf02ee1c7e117a280ec",
            "bdbfff175232f9595b5180bd64b1f288f659e8964d4f7306311d7c45f3c940ba",
        ),
        (
            "88faf62cd0e01d4b32f5f36ca96b37fdf3a4bd2432e0adcab8ca1c9d8cfd8ac5",
            "bdbfff175232f9595b5180bd64b1f288f659e8964d4f7306311d7c45f3c940ba",
        ),
        (
            "acf252905da4704ff54a3adffdd74ecf7c6b9ab056b52b6719fab8be91866b97",
            "bdbfff175232f9595b5180bd64b1f288f659e8964d4f7306311d7c45f3c940ba",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/main_trailing_source_assembler.py", set()
).update(
    {
        (
            "947171df074a8074ebb3d9bcca5710a2b001ccc00a211c58d99113ab5317e77b",
            "b951b49987a039de6b9746f40ae9f3190facb4c42dd28265a1585d02c52ef413",
        ),
        (
            "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
            "b951b49987a039de6b9746f40ae9f3190facb4c42dd28265a1585d02c52ef413",
        ),
        (
            "d76ee7b7c79ea1d420f4432f9026690b3155f7e815f0dbf1fec66016b51d8e26",
            "b951b49987a039de6b9746f40ae9f3190facb4c42dd28265a1585d02c52ef413",
        ),
    }
)

# Exact historical weakness native-source repair; original policy/custody stay unchanged.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/main_market_weakness_research.py", set()
).update(
    {
        (
            "375f13bd830a42de09cb9fae28879ab69459f76013e47dd4365207d28d976309",
            "ad97af89ce2480978e7c5286b05af8d9cb30dd81fad8d62152f7258eb646912b",
        ),
        (
            "9e704cce559ff4d7cc714feece733ca64380b440a7c3490a219170412656bce8",
            "ad97af89ce2480978e7c5286b05af8d9cb30dd81fad8d62152f7258eb646912b",
        ),
        (
            "c7fc0eacb9ec937d28c507a4b7586d1d71425a3719a08c1d8ada65e0404071f9",
            "ad97af89ce2480978e7c5286b05af8d9cb30dd81fad8d62152f7258eb646912b",
        ),
        (
            "e78122825224eee72bb3301fd2df7c22230645c5b88103fd32009a186316909b",
            "ad97af89ce2480978e7c5286b05af8d9cb30dd81fad8d62152f7258eb646912b",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/market_weakness_research.py", set()
).update(
    {
        (
            "8e124bee20aadb75fc399b752973434f9ccd0df7c1de675ca5b70af2aa8ab59c",
            "a98076e2d27f17fc50b25335d9b79b4019d828c4d4b8ade2aa985911af1d5677",
        )
    }
)

# Exact observer-canary byte-closure deployment repair; original policy/custody stay unchanged.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/ordered_intraday_deploy.py", set()
).update(
    {
        (
            "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "d56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
        (
            "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ),
    }
)

# Exact observer IO/P5/b67, logical-archive and research-retention successors.
for _relative, _origins in {
    "src/engine/automation/entry_cancel_wait_tuning.py": (
        ["bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e"],
        "49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4",
    ),
    "src/engine/automation/ordered_intraday_deploy.py": (
        [
            "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
            "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
            "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
            "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
            "afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab",
            "d56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af",
            "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
        ],
        "7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026",
    ),
    "src/engine/error_detectors/artifact_freshness.py": (
        ["3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc"],
        "6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9",
    ),
    "src/engine/lifecycle/research_storage.py": (
        ["18c0644ea2a6805b9027b2bce4bc7a1b89dbc5e10925d104b38a05a9423b4c35"],
        "448514a835975dd28266a985492ff3c352a566b71e18426214498b1f9fd1bf13",
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        ["b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841"],
        "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        [
            "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
            "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
            "808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57",
            "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
        ],
        "f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902",
    ),
    "src/engine/scalping/mechanistic_entry_runtime_policy.py": (
        ["215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867"],
        "2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08",
    ),
}.items():
    REVIEWED_PREPARATION_HISTORY.setdefault(_relative, set()).update(
        (_origin, _origins[1]) for _origin in _origins[0]
    )


# Native BUY cost and its complete observation-reader dependency closure.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/lifecycle/broker_cost_allocation.py", set()
).update(
    {
        (
            "404a1fb1f49683eba1e0443b74758cda11fd8b62452e49f229808b7e5769afae",
            "7d2954281bc187ba3778ce3587631a6980929536856a73111cbf78ac8f8fdfea",
        ),
        (
            "e392d3e79ad63fe1502a7921aca590ce93c3134d9d3e4d488d42775dd20cf349",
            "7d2954281bc187ba3778ce3587631a6980929536856a73111cbf78ac8f8fdfea",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/initial_quantity_monitor_projection.py", set()
).update(
    {
        (
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
            "87f78306653fc9f51d890a3531752301589782639b1832ad38a24f7c29c4215d",
        ),
        (
            "81a69a5f6a4d512ab7578b196fcddcf08d56ceb791ee8d2d1d3a9bdfdb926327",
            "87f78306653fc9f51d890a3531752301589782639b1832ad38a24f7c29c4215d",
        ),
        (
            "c0ac0738df35657d770b4c7a1a7c0490a0ab4bc8756aa1c19215ad2661dead8b",
            "87f78306653fc9f51d890a3531752301589782639b1832ad38a24f7c29c4215d",
        ),
        (
            "ef78c5ae7aa9dd7eab7e7ce3575329943713750fc70b248f6e992766511fd114",
            "87f78306653fc9f51d890a3531752301589782639b1832ad38a24f7c29c4215d",
        ),
    }
)

# Reviewed final-submit view and fresh native successor; no policy change.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
        ),
        (
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
        ),
        (
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
        ),
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
        ),
        (
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_evaluation_context.py", set()
).update(
    {
        (
            "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458",
        ),
        (
            "c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43",
            "7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458",
        ),
        (
            "fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654",
            "7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/runtime_performance.py", set()
).update(
    {
        (
            "3414c2eee58fc8c5547b11ad6786f1775b20d4cfb6e9b0ce78ed16e17a34e5d4",
            "ad937198678bef9cc5ef62e6aa41d9b980a0427d456608a94a1317b4fcd3cb39",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/trading/entry/physical_send_guard.py", set()
).update(
    {
        (
            "73b332cc40d021cd1b62b00cf140b8ee2abdca19007fd161d4b17ab57056e946",
            "1d5d6f7feb0fba4062d770db52dc74d0a8fca8dbdd10b48e0485c9ec80865c27",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
        ),
    }
)


# Reviewed combined zero-context observation and dated capability successors.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
        ),
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
        ),
        (
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
        (
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/scanners/scalping_scanner.py", set()
).update(
    {
        (
            "ea6188939ecc11462923d4746d27d38042aadd06f4dcd02d14cea7b2e5f8123b",
            "e3b93e6526caab14d4870bc2550c7efdbb841d86b65abc9cd1f36b8d7c21f90c",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/utils/pipeline_event_logger.py", set()
).update(
    {
        (
            "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
            "67fa82fe4f022123a529f13efa14a0b13a20ef1975210c45b2a5deae3b675b3d",
        )
    }
)


# Reviewed native BUY policy lineage and exact probe collector outcomes.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/lifecycle/broker_cost_allocation.py", set()
).update(
    {
        (
            "404a1fb1f49683eba1e0443b74758cda11fd8b62452e49f229808b7e5769afae",
            "021f0a60d6569d0fe02dd619333b7af2f8bcfa0858601b30d93f2847be1c11c9",
        ),
        (
            "7d2954281bc187ba3778ce3587631a6980929536856a73111cbf78ac8f8fdfea",
            "021f0a60d6569d0fe02dd619333b7af2f8bcfa0858601b30d93f2847be1c11c9",
        ),
        (
            "e392d3e79ad63fe1502a7921aca590ce93c3134d9d3e4d488d42775dd20cf349",
            "021f0a60d6569d0fe02dd619333b7af2f8bcfa0858601b30d93f2847be1c11c9",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/initial_quantity_policy.py", set()
).update(
    {
        (
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
            "0dc2ed9f75960006ec08e4f5eb7606dc1ee5b501ebcaf3507e0af6f8c8d12dca",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_websocket.py", set()).update(
    {
        (
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
            "ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730",
        ),
        (
            "ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377",
            "ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/scanners/zero_base_discovery_runtime.py", set()
).update(
    {
        (
            "dc058e9520482506a7659ae9cbefe1e7ce2a3ac0f2dde0b8b053742aec0535f4",
            "b27a13a0e24a3b07b3161defb97271a73bcc4d214ce2ff419d10d09bc46ce606",
        )
    }
)


# Reviewed consumed-parent closure and sealed summary/test-write custody.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/holding_path_vote_policy.py", set()
).update(
    {
        (
            "7e7ebfded9809b0944e3eb97d63d1cc9439eaa8b95c9aca91030d0aef0d2667b",
            "6aaf70d617961fee9a8aa18a3db19efd54cedcefc9a51aa1bce02ed91abd430e",
        ),
        (
            "f66fa049d9f15c51169015bd44c0464d4de540726d164d0c610e8fb9c51d8c85",
            "6aaf70d617961fee9a8aa18a3db19efd54cedcefc9a51aa1bce02ed91abd430e",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/runtime_approval_summary.py", set()
).update(
    {
        (
            "a79d492129b3222a25711d1f1086b37c2714f50c3920b2973e74f518a97ef43d",
            "cabe6bfd2bcde43ff81988905dc2149e48c809e80f535b03d28b0338bc11b1fe",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/infrastructure/startup_validation_isolation.py", set()
).update(
    {
        (
            "475bbdf7f45d7979e7cb687fe8a68a86e4d4c3e42fe54deb90d8bc049801f7ae",
            "42715b0545c044c2ccee975c6109f42195092adc3595a0e16c2535957ec283cb",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/policy_generation_fixture_validation.py", set()
).update(
    {
        (
            "28ec0362fddac74b6a1ad9230b4729879faccdf1e67ab9245e27eae5c4b45331",
            "65a54013574589331515057cba2c28abca8d794aebec133bb7f51395a0ab555c",
        ),
        (
            "88e251b6268e1814ad2e1ff6882381edb5c733973de72ad1b377ec3335cde058",
            "65a54013574589331515057cba2c28abca8d794aebec133bb7f51395a0ab555c",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/tuning_performance_control_tower.py", set()
).update(
    {
        (
            "9172370837eed5724bc16fcd483cdaaa9ea2144a92f06ba55d10df91369569b1",
            "3f47b1381a43e0ef5f44fe99ebc8774e8666fabe3e81578694fbdf2772762f8d",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/main_startup_validation.py", set()
).update(
    {
        (
            "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54",
            "e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64",
        ),
        (
            "fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c",
            "e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
        (
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        ),
    }
)

# Reviewed continuous holding observation producer and terminal consumer.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/main_trailing_source_assembler.py", set()
).update(
    {
        (
            "947171df074a8074ebb3d9bcca5710a2b001ccc00a211c58d99113ab5317e77b",
            "1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52",
        ),
        (
            "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
            "1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52",
        ),
        (
            "b951b49987a039de6b9746f40ae9f3190facb4c42dd28265a1585d02c52ef413",
            "1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52",
        ),
        (
            "d76ee7b7c79ea1d420f4432f9026690b3155f7e815f0dbf1fec66016b51d8e26",
            "1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/pre_submit_delay_research_review.py", set()
).update(
    {
        (
            "7dc2c312ce3fe14d5f3343d668e22d90f083a214e5ed25144f446e26f6dec8d3",
            "79fd3246300d7636c2e8d0c4ba33cbd2d26cf6cbc9a431b1d87f02e0725076d0",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_sniper_v2.py", set()).update(
    {
        (
            "02ecf7b4a55042fbcd2a7b4f59bf8602bed6020730f0a8bb326b41d5d6418866",
            "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
        ),
        (
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
            "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
        ),
        (
            "f88f16a8747ba64edc7594e5936dcf6d7e636fd07d852932635204c44384d4a8",
            "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/lifecycle/research_json_stream.py", set()
).update(
    {
        (
            "8fd211dc5409ee6a5bdd619bef772255c07687e921b075d473f50f70303a6201",
            "cfaf531c495730a6ae2f159601153749f8dc53ab297576250e03de61decf796b",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/holding_decision_context.py", set()
).update(
    {
        (
            "5d7577896850988b6419996a76db24344f7a612c59ecac339331ca2e841607d2",
            "afbcc348707d87032e8dcdc01c2c84c7712fa69e8cbe387342c3708fdd09e49b",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/trailing_threshold_policy.py", set()
).update(
    {
        (
            "ce1171456cba2374a001ea31d1cda60a4ee2593e4a5c7fca6426c6ed37b4ef1a",
            "ff2211f487c9475494e711f26cb1dae0ba11b90b40f6e6790e10c74483a3260b",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/universal_trailing_replay.py", set()
).update(
    {
        (
            "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
            "2de2182dcf57d4d3f850b57e6583ad3a48eba4618ebf254525970a2da668850a",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_execution_receipts.py", set()
).update(
    {
        (
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
            "83e2d110d5219698c3caf502fe96beb3f24018399706b574076902f63c36647f",
        ),
        (
            "f7210ea376fcd04d19e1592d72d0bc4a8261b799422e6161e511a338052eebb1",
            "83e2d110d5219698c3caf502fe96beb3f24018399706b574076902f63c36647f",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
        (
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/utils/pipeline_event_logger.py", set()
).update(
    {
        (
            "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
            "402e7391e0083ee87fdcaa248e9a46aaabd960d8b967a3df419d67b8b735b624",
        ),
        (
            "67fa82fe4f022123a529f13efa14a0b13a20ef1975210c45b2a5deae3b675b3d",
            "402e7391e0083ee87fdcaa248e9a46aaabd960d8b967a3df419d67b8b735b624",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
        (
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        ),
    }
)


# Reviewed native REST history outcome producer and frozen research consumers.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal.py", set()
).update(
    {
        (
            "17b73fbd524814faa53895148364758716aac406ca41761768cb69d430178030",
            "7c1d8a3f8f093ec3fde3d8deda7c411ddb3230bb3115086a28b5f811204879cc",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_branch_postclose.py", set()
).update(
    {
        (
            "7525d0c8bb68b9eb57d4bdc29462b33d5f35bc6b62f48b41d9a2e0a2c58b4c4c",
            "cf39f092eae8557ed031c82e4e24cfc32cc31279e60eb9069ae789e2500c43f8",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_operating_postclose.py", set()
).update(
    {
        (
            "2fc75be21c110341ac4596f08f8a3bcdb42adfd4e3ba8322f601337b84ab8441",
            "60b420adf69789175491963858bad6ad26d38399d00294010de2079612e6b194",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_path_postclose.py", set()
).update(
    {
        (
            "ce4f350b3e372e6287d86ed8e070f8eb4679282964ab2a64b6b626c364269af2",
            "7c8530c2419ca0465ec530c2cdde6125b4984326babd1ff2bbff05e32f150f5b",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_postclose.py", set()
).update(
    {
        (
            "d294d3fab9ef36e29b0b15007b0d22c47e1572f3b36de25d72802873f2568dda",
            "212965dc89048c663bad5083d0f3a9fb21fb315825359a9a347428c20926d69c",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_registered_postclose.py", set()
).update(
    {
        (
            "e725b5d63af61268760ebdbf760d150f38f5d19790261d6f978f803a48f86b29",
            "65f2cd48607abfae735836d5f4c5f60bad9d8866e0d4386b1c8e22756516899d",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_cumulative_postclose.py", set()
).update(
    {
        (
            "6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87",
            "990d9dd982e2fe6976fe070588e39e6a2aa46830344e3ea449ce77c93c4b68fc",
        ),
        (
            "708ee7428c494f67a7407e5093771f8ddf45ba67227073bea05ff5d87a172493",
            "990d9dd982e2fe6976fe070588e39e6a2aa46830344e3ea449ce77c93c4b68fc",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/trading/market/completed_history.py", set()
).update(
    {
        (
            "dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7",
            "381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5",
        )
    }
)


# Exact report-only auxiliary capability successor; preserve all original fixtures.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
        (
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        ),
    }
)


# Numeric consolidation and import-only replay repair; no policy or order change.
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_sniper_v2.py", set()).update(
    {
        (
            "02ecf7b4a55042fbcd2a7b4f59bf8602bed6020730f0a8bb326b41d5d6418866",
            "51b75d2cd21cc8a66c9fc5bcda6119c102d0f2256b6f569ea5e05194e15f1ce4",
        ),
        (
            "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
            "51b75d2cd21cc8a66c9fc5bcda6119c102d0f2256b6f569ea5e05194e15f1ce4",
        ),
        (
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
            "51b75d2cd21cc8a66c9fc5bcda6119c102d0f2256b6f569ea5e05194e15f1ce4",
        ),
        (
            "f88f16a8747ba64edc7594e5936dcf6d7e636fd07d852932635204c44384d4a8",
            "51b75d2cd21cc8a66c9fc5bcda6119c102d0f2256b6f569ea5e05194e15f1ce4",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
        (
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/sniper_scale_in.py", set()).update(
    {
        (
            "11d6a2313c16d28e257cb0fc0cd4e2a44b7e6c2d29eb8c692509735bfdb08be3",
            "4a60e43a414c26b2e4f8d809b45bb339c2d8c04c16ca229fa8c334868c29a506",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/lifecycle/avg_down_policy_replay.py", set()
).update(
    {
        (
            "26ec5374924617f9beef1bda42a7b2433c583abbae73407da360e4d866ed35cd",
            "7e11c813a94653b142f2682946b78a9bda3fd700c9300f4112e7209771787096",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/log_archive_service.py", set()
).update(
    {
        (
            "18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af",
            "1a3f94cc9e50ab7768cd7b7fb2953a3c0787a15f5b99e7a9f40231a41f8b81f2",
        )
    }
)


# Reviewed source flush, completed candle deadline and performance spans.
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/ai_engine_openai.py", set()).update(
    {
        (
            "194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584",
            "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
        ),
        (
            "3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7",
            "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
        ),
        (
            "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
            "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
        ),
        (
            "808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25",
            "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
        ),
        (
            "9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56",
            "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
        ),
        (
            "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
            "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/runtime_performance.py", set()
).update(
    {
        (
            "3414c2eee58fc8c5547b11ad6786f1775b20d4cfb6e9b0ce78ed16e17a34e5d4",
            "a0223bb985173ed7029ff26cabf1db76d45db690fff22bbf0cf336640a1a4ada",
        ),
        (
            "ad937198678bef9cc5ef62e6aa41d9b980a0427d456608a94a1317b4fcd3cb39",
            "a0223bb985173ed7029ff26cabf1db76d45db690fff22bbf0cf336640a1a4ada",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/entry_candle_context.py", set()
).update(
    {
        (
            "754f9ddcdead55df23259ba21cef5f324023831bf1eaa06e44b5275efa0c48b1",
            "1acd9a0b1c5fee0cb25835b6a249381e766aff3d54a0481e257466327c1d6f5f",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/mechanistic_entry_runtime_policy.py", set()
).update(
    {
        (
            "215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867",
            "439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951",
        ),
        (
            "2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08",
            "439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/micro_reversion/path_journal.py", set()
).update(
    {
        (
            "5d8e09413c104fc7392bca32c0804ee4d0142a61ecfb2674cf207089dc943dd6",
            "91308bcba1d7162cdedcd47918b50400bc5a8e1f8afee66aa50b8f975b5672d1",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_evaluation_context.py", set()
).update(
    {
        (
            "7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458",
            "fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2",
        ),
        (
            "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2",
        ),
        (
            "c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43",
            "fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2",
        ),
        (
            "fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654",
            "fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2",
        ),
    }
)


# Preserve abrupt-exit custody without granting normal source closure.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/ordered_intraday_deploy.py", set()
).update(
    {
        (
            "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "d56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
        (
            "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
            "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
        ),
    }
)


# Complete numeric capability dependency inventory.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_contract.py", set()
).update(
    {
        (
            "ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028",
            "9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
        (
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        ),
    }
)


# Complete reviewed KRX/SOR successor over the consumed numeric/source repair.
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_orders.py", set()).update(
    {
        (
            "32e93c49a880e1f3a393ec0367cf1339dbc3ef00c689c821b45b159872c423d9",
            "8b256c9e5802ad9afdf3b8806ce77420c3b425b107bb4aa6abedcd2e73f6ccbc",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
        (
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/trading/market/aftermarket_eligibility.py", set()
).update(
    {
        (
            "f28f3dd45c2d9b1aee2dcb64898d8cbecb85798bb812b058741d7f011fb45a2b",
            "63d81fe30f23cca232304c84a3f4e0c4e9e23a2f447c74d6b356798471417d4a",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/trading/market/session_contract.py", set()
).update(
    {
        (
            "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "52a9574a5e12b2437a727607c1f6fea93480861e1abb37076e9bb39ea920398c",
        ),
        (
            "dfd0ff3b2a28d8d6581a44762e5b618ae807fdc1c45d7f8cd3128b76be83573c",
            "52a9574a5e12b2437a727607c1f6fea93480861e1abb37076e9bb39ea920398c",
        ),
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/utils/kiwoom_utils.py", set()).update(
    {
        (
            "498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323",
            "ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95",
        )
    }
)

# Exact capability consumer update; preserve every issued source pair.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
        (
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        ),
    }
)


# Signed preflight history classification only; no policy consumption is invented.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/submission_bottleneck_monitor.py", set()
).update(
    {
        (
            "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
        (
            "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
        (
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
        (
            "808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
        (
            "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
        (
            "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
        (
            "f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902",
            "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
        ),
    }
)


# Closed scanner diagnostic only; retain both issued predecessor generations.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/error_detectors/artifact_freshness.py", set()
).update(
    {
        (old, "a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27")
        for old in (
            "3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc",
            "6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9",
        )
    }
)


# Native EOD local-KST clock interpretation; observer clocks stay strict.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/error_detectors/artifact_freshness.py", set()
).update(
    {
        (old, "6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa")
        for old in (
            "a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27",
            "3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc",
            "6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9",
        )
    }
)

# Completed postclose code custody retains the native whole-chain verifier.
REVIEWED_PREPARATION_HISTORY["src/engine/scalping/reversal_code_handoff.py"].update(
    {
        (
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
        (
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        ),
    }
)


# Reviewed source repairs through 58efa8cb9 and closed-weekend custody repair.
# Exact historical origins only; no transitive or arbitrary code acceptance.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/entry_cancel_wait_tuning.py", set()
).update(
    {
        (old, "860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe")
        for old in (
            "49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4",
            "bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e",
            "d557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault("src/engine/kiwoom_websocket.py", set()).update(
    {
        (old, "cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637")
        for old in (
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
            "5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5",
            "ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730",
            "ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/ai_action_outcome_calibration.py", set()
).update(
    {
        (old, "c570880da2ac0a96fdab41a07aea9ddc8bdf9740d9ba542d364e8b5a4e469486")
        for old in (
            "25ea9329d8473808b1b1d3fc09b256a329f1887f3bb50675dd11de625dc4f192",
            "a300563f9c78eb6365a24eb1c2afa67872aaf2fc287ac7d4c8aad69907bb5aed",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_tuning.py", set()
).update(
    {
        (old, "252aeca80423c1f9881ef6a26dc8baa1c18dad18be8c446cbc7c990b5e3f058a")
        for old in (
            "0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a",
            "a8ac3de954b2d6e89e3a46bb49501edc0d35df47621900a1d22b6d8492672412",
            "fe5d737f446e95028a6d5135cfa0f7c76f7047ea108aa89c737d7e5283f64e34",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_cumulative_postclose.py", set()
).update(
    {
        (old, "f24f1cd9dba38de51a7e3193b506cb8b0e02a8b53fbc94348bf432140782e1f9")
        for old in (
            "048afe98a0e4dd7a6d1c487b52c3f5e9e45030533abc84bb7d38480e1cc0b84c",
            "6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87",
            "708ee7428c494f67a7407e5093771f8ddf45ba67227073bea05ff5d87a172493",
            "990d9dd982e2fe6976fe070588e39e6a2aa46830344e3ea449ce77c93c4b68fc",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/sniper_state_handlers.py", set()
).update(
    {
        (old, "f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d")
        for old in (
            "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
            "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
            "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
            "73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd",
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
            "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
            "bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54",
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            "e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847",
            "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_code_handoff.py", set()
).update(
    {
        (old, "a54226c0232b8a12f049940bc810d5fd6161b9fc7b9154ce66063de3f55b34ec")
        for old in (
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
            "65fb740d0ddc41cfb8b5c7e0319ed442287cc0c14fd62ef1514c8378a820948c",
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (old, "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d")
        for old in (
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
        )
    }
)

# Reviewed immutable auxiliary contract readers after source formatting.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_compatibility.py", set()
).update(
    {
        (old, "77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34")
        for old in (
            "05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef",
            "9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_production_input.py", set()
).update(
    {
        (old, "324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464")
        for old in (
            "29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003",
            "ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_registry.py", set()
).update(
    {
        (old, "8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651")
        for old in (
            "7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719",
            "80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_wire.py", set()
).update(
    {
        (old, "7751d8cbeb4d1fdfe8411aefee2b0adaf25079abb8ebdf5800222b4fe7c42600")
        for old in (
            "6f3de130bc8ca5670a4588c8c274399f79b68408ed3312523bdbbe7e0018d578",
            "e10a29e96d65e5a00da11bbb5b248b1263fd34a10f8c4bcec39337802c2a021f",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_contract.py", set()
).update(
    {
        (old, "afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4")
        for old in (
            "9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9",
            "e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489",
            "ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (old, "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411")
        for old in (
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
        )
    }
)

# Reviewed stopped postclose workflow readers after native cold selection.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/continuous_reversal_policy.py", set()
).update(
    {
        (old, "7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744")
        for old in (
            "2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd",
            "7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744",
            "82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/main_startup_validation.py", set()
).update(
    {
        (old, "e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604")
        for old in (
            "14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7",
            "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54",
            "e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64",
            "fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/next_preopen_readiness.py", set()
).update(
    {
        (old, "a391fd0e9c500cb7ca222f9e6bfd2984a3891b242033f9f9edc99095246b1eff")
        for old in (
            "2e34f2a99ec94609674d7cf267763d651e5b3d4d3e030b8267dd282f325d5c69",
            "ea29654d0456212dc462275e1474b84f023a3784991e4cff9aabc1da1583b6dd",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/runtime_policy_bootstrap.py", set()
).update(
    {
        (old, "1d353dac40e7bbace49e6860dffe50965244ac35defb37468970419a76a156e0")
        for old in (
            "c7fc85190018ece3a859ba5d569596285a3bb1b21c40a79ab166ee0b2d22f433",
            "f852c630ead01b4895eaac2d66b3717907f4a1a99657bb327331ee2b3f2fd883",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_tuning.py", set()
).update(
    {
        (old, "265a06e3b26c59f616e2819a58dbd27935a4190a7eeea95aaaba6e3e2b1c7992")
        for old in (
            "0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a",
            "252aeca80423c1f9881ef6a26dc8baa1c18dad18be8c446cbc7c990b5e3f058a",
            "a8ac3de954b2d6e89e3a46bb49501edc0d35df47621900a1d22b6d8492672412",
            "fe5d737f446e95028a6d5135cfa0f7c76f7047ea108aa89c737d7e5283f64e34",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_code_handoff.py", set()
).update(
    {
        (old, "b1fdf211b0318caaddeda2ccfdb63710c839c61edb89030633143bdf730396b7")
        for old in (
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
            "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
            "65fb740d0ddc41cfb8b5c7e0319ed442287cc0c14fd62ef1514c8378a820948c",
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
            "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
            "a54226c0232b8a12f049940bc810d5fd6161b9fc7b9154ce66063de3f55b34ec",
            "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
            "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
            "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
        )
    }
)

# Reviewed bootstrap producer identity.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/runtime_policy_bootstrap.py", set()
).update(
    {
        (old, "8df8fa94ae94370b483ab816d3c35a51464f15f193458429f252379d536f01e4")
        for old in (
            "1d353dac40e7bbace49e6860dffe50965244ac35defb37468970419a76a156e0",
            "c7fc85190018ece3a859ba5d569596285a3bb1b21c40a79ab166ee0b2d22f433",
            "f852c630ead01b4895eaac2d66b3717907f4a1a99657bb327331ee2b3f2fd883",
        )
    }
)

# Reviewed native compressed-report receipt succession.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_validation.py", set()
).update(
    {
        (old, "caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a")
        for old in (
            "bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238",
            "d925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0",
            "f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (old, "d54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b")
        for old in (
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
            "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
        )
    }
)

# Reviewed cancel cache capability generation.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/automation/entry_cancel_wait_tuning.py", set()
).update(
    {
        (old, "7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5")
        for old in (
            "38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa",
            "49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4",
            "860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe",
            "bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e",
            "d557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa",
            "e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (old, "bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f")
        for old in (
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
            "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "d54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b",
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
        )
    }
)


# Reviewed frozen auxiliary envelope identity and capability successor.
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/scalping/reversal_auxiliary_registry.py", set()
).update(
    {
        (old, "e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77")
        for old in (
            "7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719",
            "80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0",
            "8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/monitoring/policy_generation_code_handoff.py", set()
).update(
    {
        (old, "02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04")
        for old in (
            "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
            "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
            "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
            "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411",
            "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
            "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
            "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
            "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
            "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
            "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
            "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
            "bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f",
            "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
            "d54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b",
            "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
        )
    }
)


# Reviewed protected database configuration and native launcher generation.
REVIEWED_PREPARATION_HISTORY.setdefault("src/utils/constants.py", set()).update(
    {
        (old, "6fad50da635c7c4b694afb1d59205d9f901f15d197db2156f489e4829750e8bb")
        for old in (
            "91b7840994ca13114176ced7cbc0ed23f9ecf53aad5dd9497956b9c991990252",
            "a7fd2722df4e74270e87ee9489c1e696f540f43a996fcc034e5265ec5b67946e",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/error_detectors/artifact_freshness.py", set()
).update(
    {
        (old, "8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665")
        for old in (
            "09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9",
            "3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc",
            "6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9",
            "6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa",
            "756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2",
            "a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27",
            "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
        )
    }
)
REVIEWED_PREPARATION_HISTORY.setdefault(
    "src/engine/infrastructure/runtime_release_router.py", set()
).update(
    {
        (old, "a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d")
        for old in (
            "02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63",
            "58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308",
            "ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962",
        )
    }
)


# Reviewed explicit issue/activation date separation; preserve every predecessor.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/reversal_code_handoff.py', set()).update(
    {(old, 'e1da1e26b3f8bcfff6e3182cf20889cf083ceee6987748571edcbd8c606f3bed') for old in
      {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/scalping/reversal_code_handoff.py'] for value in pair}
      | {"da2546b0a8d923f7943c9da30c06f93443567baad3c597de20e451d15c4b6d0f", "b1fdf211b0318caaddeda2ccfdb63710c839c61edb89030633143bdf730396b7", "852a607466a82086ba79609aa2878c54a2105587d6b56518e8895f0fbfc9f49e"}}
)

# Exact reviewed monitor receipt/denominator separation and native guard custody.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/monitoring/submission_bottleneck_monitor.py', set()).update(
    {(old, '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/monitoring/submission_bottleneck_monitor.py'] for value in pair} | {'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd'}}
)

# Frozen quantity/member proof and stopped native-intake recovery pairs.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/initial_quantity_policy.py', set()).update(
    {(old, 'a60fc47c9467e0da033f8371ebdb66627e632d6b1bcd00b9a915b333fc11fd2f') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/scalping/initial_quantity_policy.py'] for value in pair} | {'ab293d183811ca8740e94046dfc54f6011ccf24ebca9803d1420da29c7ef95bf'}}
)
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/initial_quantity_refresh_evaluation.py', set()).update(
    {(old, '5a143af8a348ef30c19848ccdf696659be69831dec840bb8f4233087b1ff82f8') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/scalping/initial_quantity_refresh_evaluation.py'] for value in pair} | {'cf4a6f44ae65f44fb273649845b65bdfb2ae7e1863be9d3790935ce95a9289b8'}}
)
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/automation/postclose_summary_handoff.py', set()).update(
    {(old, '176da9c6ddd6fa313539aadee65fafc7a2c5c4321c8f529d5a2b817e67455cfa') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/automation/postclose_summary_handoff.py'] for value in pair} | {'12fef0e06265f23c6f60f2f6de2a0c67cf75922d2c54e00af49bfda7e23fc8f3'}}
)
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/automation/ordered_intraday_deploy.py', set()).update(
    {(old, '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/automation/ordered_intraday_deploy.py'] for value in pair} | {'47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8'}}
)


# Native PREOPEN and intraday stopped origins keep their distinct owners.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/scalping/reversal_code_handoff.py', set()).update(
    {(old, '945d695b08b5f8a6bb06ef723f5a9dc8226469e49c66e03eb79dca3a70e429f4') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/scalping/reversal_code_handoff.py'] for value in pair}}
)


# Prepared handoff evidence never claims successor PID consumption.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/automation/runtime_policy_bootstrap.py', set()).update(
    {(old, 'ab3e75ecf03a69bdb4787b358c06026e32963e945cf2e867aa70193bc5f32de0') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/automation/runtime_policy_bootstrap.py'] for value in pair}}
)
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/automation/postclose_summary_handoff.py', set()).update(
    {(old, 'aeb5c0e1c259425c17de08af1dab323f2101d8147e1c7cd3c53731bcf78f024d') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/automation/postclose_summary_handoff.py'] for value in pair}}
)


REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/runtime_approval_summary.py', set()).update(
    {(old, '8de2430637152fbc72c60d7f246273492754bcb922109e0f3d1afa88165e7d3a') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/runtime_approval_summary.py'] for value in pair} | {'ba8e192796659314dc1ea5d371fe72413135937f55655fd270b2bcb8b2266075'}}
)


# Exact reviewed source fixture capability transition; preserve prior readers.
REVIEWED_PREPARATION_HISTORY.setdefault('src/engine/monitoring/policy_generation_code_handoff.py', set()).update(
    {(old, '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111') for old in
     {value for pair in REVIEWED_PREPARATION_HISTORY['src/engine/monitoring/policy_generation_code_handoff.py'] for value in pair} | {'02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04'}}
)


# Independently reviewed submit/probe successor pairs. Full native request,
# origin, source-generation and isolation checks remain mandatory.
REVIEWED_SUBMIT_PROBE_SOURCES = {'src/engine/scalping/zero_base_probe.py': '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'src/engine/sniper_state_handlers.py': 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'src/engine/monitoring/entry_attempt_identity.py': '10132ab4e6d77b41a5c86408f85d8ece4350bc7a5c3e316a238fa35d291e02f4', 'src/engine/monitoring/runtime_performance.py': 'e001ea31ffe885cd3ef2d9883d1eae99cb444e3a65e53b11e9d6dd28d6bdede1', 'src/engine/automation/next_preopen_readiness.py': 'b21095ca45f5844d1b2f6cf0cf0f312f44736e42cdf1a519eb65e7d39c0821f2'}
REVIEWED_SUBMIT_PROBE_ORIGINS = {'src/engine/scalping/zero_base_probe.py': '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', 'src/engine/sniper_state_handlers.py': 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d', 'src/engine/monitoring/entry_attempt_identity.py': 'feaeb62d8bb34e911e8681618bf445dea4edf4046404948483234d037c529dd2', 'src/engine/monitoring/runtime_performance.py': 'f52beca702c647cb538054a18cb664ccff152e796b516499c6ba649936df8d47', 'src/engine/automation/next_preopen_readiness.py': 'a391fd0e9c500cb7ca222f9e6bfd2984a3891b242033f9f9edc99095246b1eff'}
for _name, _sha in REVIEWED_SUBMIT_PROBE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {value for pair in _history for value in pair}
    _prior.add(REVIEWED_SUBMIT_PROBE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Reviewed snapshot streaming and current capability/owner binding. Preserve
# prior exact readers; missing/mixed generations still fail closed.
REVIEWED_HEALTH_SNAPSHOT_SOURCES = {'src/engine/error_detectors/artifact_freshness.py': '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', 'src/engine/monitoring/policy_generation_code_handoff.py': '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', 'src/engine/log_archive_service.py': '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'src/engine/sniper_trade_review_report.py': '188e761ec9373f0bf4f8890b620b6f7071b7ec925bf7455dcc4eeb8b11aee4ac', 'src/engine/sniper_performance_tuning_report.py': 'c6a00cba271c0b4af88f6bf6973e73b110dd7eba12ac9ddbf534ea1a3c5129af'}
REVIEWED_HEALTH_SNAPSHOT_ORIGINS = {'src/engine/error_detectors/artifact_freshness.py': '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'src/engine/monitoring/policy_generation_code_handoff.py': '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', 'src/engine/log_archive_service.py': '08b7c8d890bd5d2857a428776195d1168fa4cba5dff7ee7d587e7466527114c3', 'src/engine/sniper_trade_review_report.py': '612d19f9108f6355a43188e1209b82078e3a6da7ce97323f18854d486065d53f', 'src/engine/sniper_performance_tuning_report.py': '64d66e04f7cae07a6c80ad48e7348ab77262be6f3ec8ad8ec3df1b2018dc0dd1'}
for _name, _sha in REVIEWED_HEALTH_SNAPSHOT_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {value for pair in _history for value in pair}
    _prior.add(REVIEWED_HEALTH_SNAPSHOT_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Reviewed direct FIRST_PRICE_HOLD floor recording, including cumulative roots.
# Preserve all previously reviewed predecessors; unknown generations fail closed.
REVIEWED_CUMULATIVE_HOLD_SOURCES = {'src/engine/monitoring/runtime_performance.py': 'c23788f10acaaf0e554a42f187042ea3f37ea74d9b1d969ac95f7fdd4c9ca104'}
for _name, _sha in REVIEWED_CUMULATIVE_HOLD_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {value for pair in _history for value in pair}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior | {'e001ea31ffe885cd3ef2d9883d1eae99cb444e3a65e53b11e9d6dd28d6bdede1'})


# Reviewed normal postclose loader classification, with exact historical custody.
# Prior source pairs remain valid; unknown or mixed generations stay rejected.
REVIEWED_CLOSED_LOADER_SOURCES = {'src/engine/error_detectors/artifact_freshness.py': 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3'}
for _name, _sha in REVIEWED_CLOSED_LOADER_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {value for pair in _history for value in pair}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Isolated indexed-source validation preserves native coverage and exact input
# generations. The ordinary index consumer and database prohibition stay intact.
REVIEWED_STOP_INDEX_SOURCES = {'src/engine/automation/main_trailing_source_assembler.py': '26fa3a2f2658f7d5081bb0d16d0d8ef27c19e8ab54da9f0e14074c82c3c096d5'}
for _name, _sha in REVIEWED_STOP_INDEX_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {value for pair in _history for value in pair} | {'943d15e004967ac5e084d8e49bebf53c05cf524e6f229cc8b1a3312ece1968af'}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Restore the unchanged production assembler; indexed I/O belongs exclusively
# to the authenticated isolated validation process. Retain the issued successor.
_RESTORED_ASSEMBLER = "src/engine/automation/main_trailing_source_assembler.py"
_assembler_history = REVIEWED_PREPARATION_HISTORY[_RESTORED_ASSEMBLER]
_assembler_history.update((old, "943d15e004967ac5e084d8e49bebf53c05cf524e6f229cc8b1a3312ece1968af") for old in
                          {v for pair in _assembler_history for v in pair})


# Completed-prefix report absence changes recovery custody only; every native
# policy, source and fresh terminal detector predicate remains unchanged.
REVIEWED_SUFFIX_REPORT_SOURCES = {"src/engine/automation/postclose_finalization_generation.py": "0d70b7d26a768416c20b7345f47ac45155feda44469d3241930e48fa2f0e4c41"}
for _name, _sha in REVIEWED_SUFFIX_REPORT_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {"7f5cc8274e2ba7eba200102c34dbd29635e2dad158a380024fa8d8ed70153c72"}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Reviewed daily historical diagnostic custody. Old IDs, null economics and
# exact original proofs remain immutable; new/current source validation stays.
REVIEWED_QUANTITY_HISTORY_SOURCES = {"src/engine/scalping/initial_quantity_monitor_projection.py": "e12b1702ab35598ff77113c3b42e0ae4e9d3aad623cda4a9161b34277e1ff350"}
for _name, _sha in REVIEWED_QUANTITY_HISTORY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {"32724869c09d6495aa0ab4ec8113a49081f640f15b0bcb1fea5429d467ea354a"}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Lossless closed collector custody does not grant research admission. Exact
# preselection failure recovery preserves the original selector and all proofs.
REVIEWED_DRAIN_CLOSURE_SOURCES = {"src/engine/automation/ordered_intraday_deploy.py": "f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e"}
for _name, _sha in REVIEWED_DRAIN_CLOSURE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {"7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5"}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)

# Lossless closed collector custody does not grant research admission. Exact
# preselection failure recovery preserves the original selector and all proofs.
REVIEWED_DRAIN_POINTER_SOURCES = {"src/engine/automation/ordered_intraday_deploy.py": "c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1"}
for _name, _sha in REVIEWED_DRAIN_POINTER_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {"7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5"}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Exact reviewed holding quote/custody consumer repair; policies and guards unchanged.
REVIEWED_HOLDING_QUOTE_SOURCES = {'src/engine/kiwoom_sniper_v2.py': 'f9ac6408c2ead8f699728eaf01a6170729dea6b59bb01b327bc22ff295412293', 'src/engine/sniper_state_handlers.py': 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'src/engine/kiwoom_websocket.py': '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', 'src/trading/market/aftermarket_eligibility.py': '34cce97a46d2d16af19f900012026cd78dc47f32e03594329c2e4068909f1d53'}
REVIEWED_HOLDING_QUOTE_ORIGINS = {'src/engine/kiwoom_sniper_v2.py': '870985eb69dc70bb23271e883a9170ab48f5288c506a6b0195745f54849ab827', 'src/engine/sniper_state_handlers.py': 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'src/engine/kiwoom_websocket.py': 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'src/trading/market/aftermarket_eligibility.py': 'daa1fa457c208aeb2c98a12abca0a8d748d2a9f4e7a63c384c9e911fb0cf05b1'}
for _name, _sha in REVIEWED_HOLDING_QUOTE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_HOLDING_QUOTE_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Final detector admission shares the existing finalization wall deadline.
REVIEWED_FINALIZATION_ADMISSION_SOURCES = {'deploy/run_postclose_finalization.sh': '3c8e94c94f259dc0717a649ff31bb51d56f2f00a59561ecff783b75875cd0267', 'deploy/run_error_detection.sh': '6a950c2e19d4848edb4f92d949c38d053d41f50f5701bb6d40257fba009d0c42'}
REVIEWED_FINALIZATION_ADMISSION_ORIGINS = {'deploy/run_postclose_finalization.sh': 'f0256308c44cad1f30d3f1f2bea43192f797c72aa93c3970d9ec65ef8c712fe9', 'deploy/run_error_detection.sh': 'b73d9508340b90ed47578dff314576cc1e68070071c674bb2316eb317577a5b8'}
for _name, _sha in REVIEWED_FINALIZATION_ADMISSION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_FINALIZATION_ADMISSION_ORIGINS[_name]}
    _history.update((old, _sha) for old in _prior)


# Exact reviewed holding-source capability reader; retain original generations.
REVIEWED_HOLDING_CAPABILITY_SOURCES = {'src/engine/monitoring/policy_generation_code_handoff.py': '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529'}
REVIEWED_HOLDING_CAPABILITY_ORIGINS = {'src/engine/monitoring/policy_generation_code_handoff.py': '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120'}
for _name, _sha in REVIEWED_HOLDING_CAPABILITY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_HOLDING_CAPABILITY_ORIGINS[_name]}
    _history.update((_old, _sha) for _old in _prior)

# Exact source-only latency/report successor; retain original preparation pairs.
REVIEWED_ENTRY_LATENCY_SOURCES = {'src/engine/scalping/mechanistic_entry_runtime_policy.py': 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', 'src/engine/buy_funnel_sentinel.py': '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'src/engine/monitoring/sentinel_summary_contract.py': 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'}
REVIEWED_ENTRY_LATENCY_ORIGINS = {'src/engine/scalping/mechanistic_entry_runtime_policy.py': '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'src/engine/scalping/continuous_reversal_policy_v6.py': '0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', 'src/engine/buy_funnel_sentinel.py': 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'src/engine/monitoring/sentinel_summary_contract.py': '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e'}
for _name, _sha in REVIEWED_ENTRY_LATENCY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_ENTRY_LATENCY_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Exact auxiliary capability reader successor; preserve prior preparation custody.
REVIEWED_ENTRY_CAPABILITY_SOURCES = {'src/engine/monitoring/policy_generation_code_handoff.py': 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d'}
REVIEWED_ENTRY_CAPABILITY_ORIGINS = {'src/engine/monitoring/policy_generation_code_handoff.py': '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529'}
for _name, _sha in REVIEWED_ENTRY_CAPABILITY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_ENTRY_CAPABILITY_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Reviewed identifier/source-isolation successor; original preparation stays sealed.
REVIEWED_NONFIXED_IDENTITY_SOURCES = {
    "src/engine/kiwoom_orders.py": "75df3ff7d8adfedd9e14ca0fb0d57675dd1279f12d52ff1d9b6c931746cee5a7",
    "src/engine/kiwoom_sniper_v2.py": "66b57f8ca7d37af5be3f6d5897a20e3a4ee5b7f32b5e2b511954d713d9e4006a",
    "src/engine/kiwoom_websocket.py": "d5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784",
    "src/engine/monitoring/market_opportunity_census.py": "7256a4f0d2448107219a448f1449304546048b9260b337cb21c5070867844834",
    "src/engine/monitoring/policy_generation_code_handoff.py": "9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8",
    "src/engine/scalping/continuous_reversal_source.py": "8c27036d109e04c2d4774e40cf5862004d07b60c4afb4e0d0e768c05098d87ef",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "8c96cb422e13c7d0b67df9be71caa04926fc3e26dbd4f6389ccac97a2d968b5d",
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f",
    "src/engine/scalping/zero_base_probe.py": "16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb",
    "src/engine/sniper_state_handlers.py": "51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93",
    "src/engine/sniper_trade_utils.py": "d0570ff0e17a7f164c63fd187eca593bfc92516e40c0e0c58eb019828c7ffbda",
    "src/scanners/scalping_scanner.py": "eb938c01d837d52973f7d47b59f96da1d338b2df9be8025c18d7c2f936546e16",
    "src/scanners/scanner_source_census.py": "81010bcc9ec41cc55f2a88980ccec676e174023427e4884b1eab5b56e121e6e7",
    "src/scanners/zero_base_discovery_queue.py": "d8c93e78f8944428b6cfb726a88af9e4e0c39aee724c81c97d74d721d6d89d6b",
    "src/scanners/zero_base_discovery_runtime.py": "61ebea82400e4139ed2b0dd66a2b7af5dff9e890c491af7185739b5045e36675",
    "src/scanners/zero_base_discovery_source.py": "65ce49d872b5b16ff0d43609c57e57acd7b36e20d2993bf6ce7f0ac529f1dd34",
    "src/trading/config/owner_identity.py": "db35da13c7471df8612a30e7b756f3ebe459884465eef786855a8102fbb60181",
    "src/trading/market/aftermarket_eligibility.py": "5630f3629ff8c0b5e35fa62b03aa1f56e509536efa05a6f28f9c044d485903b6",
    "src/trading/market/completed_history.py": "b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a",
    "src/trading/market/entry_ws_snapshot.py": "5254c006fd949fc564609ee108b415fbef4c187df44c5f5301f4ab760b1dd4fa",
    "src/trading/market/quote_consistency.py": "7417443e80cd7d7f53d4aaceddf1763bdd4fee97aa8176932632144fbee59cac",
    "src/trading/order/entry_liquidity_guard.py": "414f2675313da1c00558c889608e6fa597b6191bc8dceba93807ca87e1e3f1b2",
    "src/trading/order/owner_custody_registry.py": "7c860d60608b18de35dad340202966711dce7ecc172881dae02e573fef498710",
    "src/utils/kiwoom_utils.py": "1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a",
}
REVIEWED_NONFIXED_IDENTITY_ORIGINS = {
    "src/engine/kiwoom_orders.py": "c90c10ad6793869d779a4c62331c094fe5c1657d449196ff03251631c4dfd020",
    "src/engine/kiwoom_sniper_v2.py": "f9ac6408c2ead8f699728eaf01a6170729dea6b59bb01b327bc22ff295412293",
    "src/engine/kiwoom_websocket.py": "6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471",
    "src/engine/monitoring/market_opportunity_census.py": "1eaa245687d78c47885f97dab361ed18a786b7aa154a52f6e3d7a48b558712db",
    "src/engine/monitoring/policy_generation_code_handoff.py": "d6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d",
    "src/engine/scalping/continuous_reversal_source.py": "e1997f5b759f9567d4c7ec1598f6847ce5936d93986853c51a4eb6b1942229bd",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "359404e97523b868ee88cafd78591e19796b0a87b3a273d8b5e9ba9ad60135c9",
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464",
    "src/engine/scalping/zero_base_probe.py": "7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae",
    "src/engine/sniper_state_handlers.py": "c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3",
    "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
    "src/scanners/scalping_scanner.py": "ea7c459ce063c83d1df1a2b29b05baa5a0c228e3393c3abc2cfcde5eb9e8a5be",
    "src/scanners/scanner_source_census.py": "005139e3a0b3be3f666a9e56a012057b253e996c949464d5c7074caf5688f4fe",
    "src/scanners/zero_base_discovery_queue.py": "43727efd4ab06ae7f4f920759a915328d3a5051877c3a70c2332d90ba4946508",
    "src/scanners/zero_base_discovery_runtime.py": "60f3c2ac08f88273df7f945f9a8f06a270041dbecf57921d9544416ae8fe770a",
    "src/scanners/zero_base_discovery_source.py": "5a4b5832dec647a0911484014afe8472c194bf4b1fe6165cc978aca3657ec9e4",
    "src/trading/config/owner_identity.py": "36f8983b4da46ed6f8958af429d1e4847430d55287be9a0502c123d7ae659e58",
    "src/trading/market/aftermarket_eligibility.py": "34cce97a46d2d16af19f900012026cd78dc47f32e03594329c2e4068909f1d53",
    "src/trading/market/completed_history.py": "b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20",
    "src/trading/market/entry_ws_snapshot.py": "7d8ef5bd84dbf21e379cad71abc0d6d258d0311850ecc95a995db42495732e38",
    "src/trading/market/quote_consistency.py": "9614e97cbd33130e2d66ff66a5f879ae32e690ae4864d6640f9e5e6297a45dc9",
    "src/trading/order/entry_liquidity_guard.py": "dc71e13e38c2f4464fd8d5a0840958b44546743e7766f5b092ff2ebea3824a56",
    "src/trading/order/owner_custody_registry.py": "a5b40329f5d46eff8ac11696b809d520fa48620a1a7104fb8adf6faa94c59c3c",
    "src/utils/kiwoom_utils.py": "5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641",
}
for _name, _sha in REVIEWED_NONFIXED_IDENTITY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {
        REVIEWED_NONFIXED_IDENTITY_ORIGINS[_name]
    }
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Reviewed gate/transport diagnostics and local-deadline attribution only.
# Evidence: main-machine-pattern-dual-track-research-review-2026-10-21.md,
# preclaim-guard-and-exact-lease-causal-follow-up---2026-10-27.
REVIEWED_PRECLAIM_DIAGNOSTIC_SOURCES = {'src/engine/ai_engine_openai.py': '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', 'src/engine/kiwoom_websocket.py': 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'src/engine/monitoring/runtime_performance.py': '90d6d73bcbc758a880d631a5862f0f2b0ea6b6764255d4fa5a73e4ff47596d82', 'src/engine/sniper_state_handlers.py': '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', 'src/engine/monitoring/policy_generation_code_handoff.py': '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee'}
REVIEWED_PRECLAIM_DIAGNOSTIC_ORIGINS = {'src/engine/ai_engine_openai.py': 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'src/engine/kiwoom_websocket.py': '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', 'src/engine/monitoring/runtime_performance.py': 'c23788f10acaaf0e554a42f187042ea3f37ea74d9b1d969ac95f7fdd4c9ca104', 'src/engine/sniper_state_handlers.py': 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'src/engine/monitoring/policy_generation_code_handoff.py': 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d'}
for _name, _sha in REVIEWED_PRECLAIM_DIAGNOSTIC_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_PRECLAIM_DIAGNOSTIC_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Exact combined generation; standalone candidate source histories stay readable.
REVIEWED_NONFIXED_PRECLAIM_SOURCES = {
    "src/engine/ai_engine_openai.py": "4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429",
    "src/engine/kiwoom_orders.py": "75df3ff7d8adfedd9e14ca0fb0d57675dd1279f12d52ff1d9b6c931746cee5a7",
    "src/engine/kiwoom_sniper_v2.py": "66b57f8ca7d37af5be3f6d5897a20e3a4ee5b7f32b5e2b511954d713d9e4006a",
    "src/engine/kiwoom_websocket.py": "a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd",
    "src/engine/monitoring/market_opportunity_census.py": "7256a4f0d2448107219a448f1449304546048b9260b337cb21c5070867844834",
    "src/engine/monitoring/policy_generation_code_handoff.py": "aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226",
    "src/engine/monitoring/runtime_performance.py": "90d6d73bcbc758a880d631a5862f0f2b0ea6b6764255d4fa5a73e4ff47596d82",
    "src/engine/scalping/continuous_reversal_source.py": "8c27036d109e04c2d4774e40cf5862004d07b60c4afb4e0d0e768c05098d87ef",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "8c96cb422e13c7d0b67df9be71caa04926fc3e26dbd4f6389ccac97a2d968b5d",
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f",
    "src/engine/scalping/zero_base_probe.py": "16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb",
    "src/engine/sniper_state_handlers.py": "49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322",
    "src/engine/sniper_trade_utils.py": "d0570ff0e17a7f164c63fd187eca593bfc92516e40c0e0c58eb019828c7ffbda",
    "src/scanners/scalping_scanner.py": "eb938c01d837d52973f7d47b59f96da1d338b2df9be8025c18d7c2f936546e16",
    "src/scanners/scanner_source_census.py": "81010bcc9ec41cc55f2a88980ccec676e174023427e4884b1eab5b56e121e6e7",
    "src/scanners/zero_base_discovery_queue.py": "d8c93e78f8944428b6cfb726a88af9e4e0c39aee724c81c97d74d721d6d89d6b",
    "src/scanners/zero_base_discovery_runtime.py": "61ebea82400e4139ed2b0dd66a2b7af5dff9e890c491af7185739b5045e36675",
    "src/scanners/zero_base_discovery_source.py": "65ce49d872b5b16ff0d43609c57e57acd7b36e20d2993bf6ce7f0ac529f1dd34",
    "src/trading/config/owner_identity.py": "db35da13c7471df8612a30e7b756f3ebe459884465eef786855a8102fbb60181",
    "src/trading/market/aftermarket_eligibility.py": "5630f3629ff8c0b5e35fa62b03aa1f56e509536efa05a6f28f9c044d485903b6",
    "src/trading/market/completed_history.py": "b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a",
    "src/trading/market/entry_ws_snapshot.py": "5254c006fd949fc564609ee108b415fbef4c187df44c5f5301f4ab760b1dd4fa",
    "src/trading/market/quote_consistency.py": "7417443e80cd7d7f53d4aaceddf1763bdd4fee97aa8176932632144fbee59cac",
    "src/trading/order/entry_liquidity_guard.py": "414f2675313da1c00558c889608e6fa597b6191bc8dceba93807ca87e1e3f1b2",
    "src/trading/order/owner_custody_registry.py": "7c860d60608b18de35dad340202966711dce7ecc172881dae02e573fef498710",
    "src/utils/kiwoom_utils.py": "1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a"
}
REVIEWED_NONFIXED_PRECLAIM_ORIGINS = {
    "src/engine/ai_engine_openai.py": "cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e",
    "src/engine/kiwoom_orders.py": "c90c10ad6793869d779a4c62331c094fe5c1657d449196ff03251631c4dfd020",
    "src/engine/kiwoom_sniper_v2.py": "f9ac6408c2ead8f699728eaf01a6170729dea6b59bb01b327bc22ff295412293",
    "src/engine/kiwoom_websocket.py": "6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471",
    "src/engine/monitoring/market_opportunity_census.py": "1eaa245687d78c47885f97dab361ed18a786b7aa154a52f6e3d7a48b558712db",
    "src/engine/monitoring/policy_generation_code_handoff.py": "d6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d",
    "src/engine/monitoring/runtime_performance.py": "c23788f10acaaf0e554a42f187042ea3f37ea74d9b1d969ac95f7fdd4c9ca104",
    "src/engine/scalping/continuous_reversal_source.py": "e1997f5b759f9567d4c7ec1598f6847ce5936d93986853c51a4eb6b1942229bd",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "359404e97523b868ee88cafd78591e19796b0a87b3a273d8b5e9ba9ad60135c9",
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464",
    "src/engine/scalping/zero_base_probe.py": "7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae",
    "src/engine/sniper_state_handlers.py": "c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3",
    "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
    "src/scanners/scalping_scanner.py": "ea7c459ce063c83d1df1a2b29b05baa5a0c228e3393c3abc2cfcde5eb9e8a5be",
    "src/scanners/scanner_source_census.py": "005139e3a0b3be3f666a9e56a012057b253e996c949464d5c7074caf5688f4fe",
    "src/scanners/zero_base_discovery_queue.py": "43727efd4ab06ae7f4f920759a915328d3a5051877c3a70c2332d90ba4946508",
    "src/scanners/zero_base_discovery_runtime.py": "60f3c2ac08f88273df7f945f9a8f06a270041dbecf57921d9544416ae8fe770a",
    "src/scanners/zero_base_discovery_source.py": "5a4b5832dec647a0911484014afe8472c194bf4b1fe6165cc978aca3657ec9e4",
    "src/trading/config/owner_identity.py": "36f8983b4da46ed6f8958af429d1e4847430d55287be9a0502c123d7ae659e58",
    "src/trading/market/aftermarket_eligibility.py": "34cce97a46d2d16af19f900012026cd78dc47f32e03594329c2e4068909f1d53",
    "src/trading/market/completed_history.py": "b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20",
    "src/trading/market/entry_ws_snapshot.py": "7d8ef5bd84dbf21e379cad71abc0d6d258d0311850ecc95a995db42495732e38",
    "src/trading/market/quote_consistency.py": "9614e97cbd33130e2d66ff66a5f879ae32e690ae4864d6640f9e5e6297a45dc9",
    "src/trading/order/entry_liquidity_guard.py": "dc71e13e38c2f4464fd8d5a0840958b44546743e7766f5b092ff2ebea3824a56",
    "src/trading/order/owner_custody_registry.py": "a5b40329f5d46eff8ac11696b809d520fa48620a1a7104fb8adf6faa94c59c3c",
    "src/utils/kiwoom_utils.py": "5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641"
}
for _name, _sha in REVIEWED_NONFIXED_PRECLAIM_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_NONFIXED_PRECLAIM_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Exact reviewed diagnostics successor; no trading or source-quality waiver.
REVIEWED_INVALIDATION_CADENCE_SOURCES = {'src/engine/scalping/reversal_extended_state.py': '0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', 'src/engine/scalping/reversal_source_diagnostics.py': '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'src/engine/monitoring/submission_bottleneck_monitor.py': '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', 'src/engine/kiwoom_websocket.py': 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'src/engine/monitoring/ws_receive_expectation.py': '2098bfda2c73f367f0bda84a5023063e5e37da92fe94608b0b7db3b2cd38dbc8', 'src/engine/scalping/pre_submit_delay_tuning.py': 'df3b0eefc8d05046ffbbb9be36c0929c843f5c1a71f9e6c72acc956bcea9407e', 'src/engine/sniper_state_handlers.py': '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', 'src/engine/monitoring/policy_generation_code_handoff.py': '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', 'src/engine/log_archive_service.py': 'fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543', 'src/engine/sniper_trade_review_report.py': 'abefe48bfe066d9b234c4dc726d0cb91247a61c4ab1f68747f4c2279ca686da3', 'src/engine/infrastructure/runtime_release_router.py': '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', 'src/engine/compress_db_backfilled_files.py': '31e5e754441887eac1e8124515b8b4a69825be5e045feff7659aae54d80f7b80', 'deploy/install_stage2_ops_cron.sh': 'c9ae93267d1822d090c2bc5978b236429ea74784b5e73f54e44fa1c00781205e'}
REVIEWED_INVALIDATION_CADENCE_ORIGINS = {'src/engine/scalping/reversal_extended_state.py': 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3', 'src/engine/scalping/reversal_source_diagnostics.py': '3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', 'src/engine/monitoring/submission_bottleneck_monitor.py': '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', 'src/engine/kiwoom_websocket.py': '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', 'src/engine/monitoring/ws_receive_expectation.py': 'e59e190be836c8a061e3d59f59607a8174d43636d6b76af6ea03e980bd306578', 'src/engine/scalping/pre_submit_delay_tuning.py': '59a4da7cce73f59fe3c3f563e8546e12a332735e2db60fbfa9c6658a230a2024', 'src/engine/sniper_state_handlers.py': 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'src/engine/monitoring/policy_generation_code_handoff.py': 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'src/engine/log_archive_service.py': '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'src/engine/sniper_trade_review_report.py': '188e761ec9373f0bf4f8890b620b6f7071b7ec925bf7455dcc4eeb8b11aee4ac', 'src/engine/infrastructure/runtime_release_router.py': 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'src/engine/compress_db_backfilled_files.py': '3ad3176fafec6b16ce9555cb87a45b3004a49f278e3a8e23520eec30ba1f9462', 'deploy/install_stage2_ops_cron.sh': '59f572c59d1c5ba459b67adecd7b8211dc70bd58fc27b5acf8bc908abd7feb9d'}
REVIEWED_INVALIDATION_CADENCE_PROJECTED_ORIGINS = {'src/engine/scalping/reversal_extended_state.py': '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', 'src/engine/scalping/reversal_source_diagnostics.py': 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee', 'src/engine/monitoring/submission_bottleneck_monitor.py': '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', 'src/engine/kiwoom_websocket.py': '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', 'src/engine/monitoring/ws_receive_expectation.py': '604dede3290548ebcf523888226bfc75df2f4070ae9039f2e0f87b66ccb0834a', 'src/engine/scalping/pre_submit_delay_tuning.py': '6d2335731199417edce383e773b5737b110f4401297fefce75fc578dd7ce6fd2', 'src/engine/sniper_state_handlers.py': 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'src/engine/monitoring/policy_generation_code_handoff.py': 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'src/engine/log_archive_service.py': '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'src/engine/sniper_trade_review_report.py': '188e761ec9373f0bf4f8890b620b6f7071b7ec925bf7455dcc4eeb8b11aee4ac', 'src/engine/infrastructure/runtime_release_router.py': 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'src/engine/compress_db_backfilled_files.py': '501159d87c7901b2a9edb6e7cd8a04d99ef6c15aae12577f9344078cf76ace3f', 'deploy/install_stage2_ops_cron.sh': '59f572c59d1c5ba459b67adecd7b8211dc70bd58fc27b5acf8bc908abd7feb9d'}
for _name, _sha in REVIEWED_INVALIDATION_CADENCE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_INVALIDATION_CADENCE_ORIGINS[_name], REVIEWED_INVALIDATION_CADENCE_PROJECTED_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Exact integration of the reviewed preclaim and current cadence owners.
# No original-source, policy, deadline or hard-guard waiver.
REVIEWED_PRECLAIM_CADENCE_SOURCES = {'src/engine/ai_engine_openai.py': '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', 'src/engine/kiwoom_websocket.py': '1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', 'src/engine/monitoring/runtime_performance.py': '90d6d73bcbc758a880d631a5862f0f2b0ea6b6764255d4fa5a73e4ff47596d82', 'src/engine/sniper_state_handlers.py': '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', 'src/engine/monitoring/policy_generation_code_handoff.py': '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50'}
REVIEWED_PRECLAIM_CADENCE_ORIGINS = {'src/engine/ai_engine_openai.py': 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'src/engine/kiwoom_websocket.py': 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'src/engine/monitoring/runtime_performance.py': 'c23788f10acaaf0e554a42f187042ea3f37ea74d9b1d969ac95f7fdd4c9ca104', 'src/engine/sniper_state_handlers.py': '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', 'src/engine/monitoring/policy_generation_code_handoff.py': '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9'}
for _name, _sha in REVIEWED_PRECLAIM_CADENCE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_PRECLAIM_CADENCE_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((old, _sha) for old in _prior)


# Exact combined generation; standalone candidate source histories stay readable.
REVIEWED_NONFIXED_CURRENT_SOURCES = {
    "deploy/install_stage2_ops_cron.sh": "c9ae93267d1822d090c2bc5978b236429ea74784b5e73f54e44fa1c00781205e",
    "src/engine/ai_engine_openai.py": "4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429",
    "src/engine/compress_db_backfilled_files.py": "31e5e754441887eac1e8124515b8b4a69825be5e045feff7659aae54d80f7b80",
    "src/engine/infrastructure/runtime_release_router.py": "49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601",
    "src/engine/kiwoom_orders.py": "75df3ff7d8adfedd9e14ca0fb0d57675dd1279f12d52ff1d9b6c931746cee5a7",
    "src/engine/kiwoom_sniper_v2.py": "66b57f8ca7d37af5be3f6d5897a20e3a4ee5b7f32b5e2b511954d713d9e4006a",
    "src/engine/kiwoom_websocket.py": "701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474",
    "src/engine/log_archive_service.py": "fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543",
    "src/engine/monitoring/market_opportunity_census.py": "7256a4f0d2448107219a448f1449304546048b9260b337cb21c5070867844834",
    "src/engine/monitoring/policy_generation_code_handoff.py": "1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365",
    "src/engine/monitoring/runtime_performance.py": "90d6d73bcbc758a880d631a5862f0f2b0ea6b6764255d4fa5a73e4ff47596d82",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2",
    "src/engine/monitoring/ws_receive_expectation.py": "2098bfda2c73f367f0bda84a5023063e5e37da92fe94608b0b7db3b2cd38dbc8",
    "src/engine/scalping/continuous_reversal_source.py": "8c27036d109e04c2d4774e40cf5862004d07b60c4afb4e0d0e768c05098d87ef",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "8c96cb422e13c7d0b67df9be71caa04926fc3e26dbd4f6389ccac97a2d968b5d",
    "src/engine/scalping/pre_submit_delay_tuning.py": "df3b0eefc8d05046ffbbb9be36c0929c843f5c1a71f9e6c72acc956bcea9407e",
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f",
    "src/engine/scalping/reversal_extended_state.py": "0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1",
    "src/engine/scalping/reversal_source_diagnostics.py": "997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865",
    "src/engine/scalping/zero_base_probe.py": "16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb",
    "src/engine/sniper_state_handlers.py": "193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d",
    "src/engine/sniper_trade_review_report.py": "abefe48bfe066d9b234c4dc726d0cb91247a61c4ab1f68747f4c2279ca686da3",
    "src/engine/sniper_trade_utils.py": "d0570ff0e17a7f164c63fd187eca593bfc92516e40c0e0c58eb019828c7ffbda",
    "src/scanners/scalping_scanner.py": "eb938c01d837d52973f7d47b59f96da1d338b2df9be8025c18d7c2f936546e16",
    "src/scanners/scanner_source_census.py": "81010bcc9ec41cc55f2a88980ccec676e174023427e4884b1eab5b56e121e6e7",
    "src/scanners/zero_base_discovery_queue.py": "d8c93e78f8944428b6cfb726a88af9e4e0c39aee724c81c97d74d721d6d89d6b",
    "src/scanners/zero_base_discovery_runtime.py": "61ebea82400e4139ed2b0dd66a2b7af5dff9e890c491af7185739b5045e36675",
    "src/scanners/zero_base_discovery_source.py": "65ce49d872b5b16ff0d43609c57e57acd7b36e20d2993bf6ce7f0ac529f1dd34",
    "src/trading/config/owner_identity.py": "db35da13c7471df8612a30e7b756f3ebe459884465eef786855a8102fbb60181",
    "src/trading/market/aftermarket_eligibility.py": "5630f3629ff8c0b5e35fa62b03aa1f56e509536efa05a6f28f9c044d485903b6",
    "src/trading/market/completed_history.py": "b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a",
    "src/trading/market/entry_ws_snapshot.py": "5254c006fd949fc564609ee108b415fbef4c187df44c5f5301f4ab760b1dd4fa",
    "src/trading/market/quote_consistency.py": "7417443e80cd7d7f53d4aaceddf1763bdd4fee97aa8176932632144fbee59cac",
    "src/trading/order/entry_liquidity_guard.py": "414f2675313da1c00558c889608e6fa597b6191bc8dceba93807ca87e1e3f1b2",
    "src/trading/order/owner_custody_registry.py": "7c860d60608b18de35dad340202966711dce7ecc172881dae02e573fef498710",
    "src/utils/kiwoom_utils.py": "1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a"
}
REVIEWED_NONFIXED_CURRENT_ORIGINS = {
    "deploy/install_stage2_ops_cron.sh": "c9ae93267d1822d090c2bc5978b236429ea74784b5e73f54e44fa1c00781205e",
    "src/engine/ai_engine_openai.py": "cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e",
    "src/engine/compress_db_backfilled_files.py": "31e5e754441887eac1e8124515b8b4a69825be5e045feff7659aae54d80f7b80",
    "src/engine/infrastructure/runtime_release_router.py": "49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601",
    "src/engine/kiwoom_orders.py": "c90c10ad6793869d779a4c62331c094fe5c1657d449196ff03251631c4dfd020",
    "src/engine/kiwoom_sniper_v2.py": "f9ac6408c2ead8f699728eaf01a6170729dea6b59bb01b327bc22ff295412293",
    "src/engine/kiwoom_websocket.py": "ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25",
    "src/engine/log_archive_service.py": "fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543",
    "src/engine/monitoring/market_opportunity_census.py": "1eaa245687d78c47885f97dab361ed18a786b7aa154a52f6e3d7a48b558712db",
    "src/engine/monitoring/policy_generation_code_handoff.py": "5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9",
    "src/engine/monitoring/runtime_performance.py": "c23788f10acaaf0e554a42f187042ea3f37ea74d9b1d969ac95f7fdd4c9ca104",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2",
    "src/engine/monitoring/ws_receive_expectation.py": "2098bfda2c73f367f0bda84a5023063e5e37da92fe94608b0b7db3b2cd38dbc8",
    "src/engine/scalping/continuous_reversal_source.py": "e1997f5b759f9567d4c7ec1598f6847ce5936d93986853c51a4eb6b1942229bd",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "359404e97523b868ee88cafd78591e19796b0a87b3a273d8b5e9ba9ad60135c9",
    "src/engine/scalping/pre_submit_delay_tuning.py": "df3b0eefc8d05046ffbbb9be36c0929c843f5c1a71f9e6c72acc956bcea9407e",
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464",
    "src/engine/scalping/reversal_extended_state.py": "0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1",
    "src/engine/scalping/reversal_source_diagnostics.py": "997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865",
    "src/engine/scalping/zero_base_probe.py": "7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae",
    "src/engine/sniper_state_handlers.py": "21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4",
    "src/engine/sniper_trade_review_report.py": "abefe48bfe066d9b234c4dc726d0cb91247a61c4ab1f68747f4c2279ca686da3",
    "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
    "src/scanners/scalping_scanner.py": "ea7c459ce063c83d1df1a2b29b05baa5a0c228e3393c3abc2cfcde5eb9e8a5be",
    "src/scanners/scanner_source_census.py": "005139e3a0b3be3f666a9e56a012057b253e996c949464d5c7074caf5688f4fe",
    "src/scanners/zero_base_discovery_queue.py": "43727efd4ab06ae7f4f920759a915328d3a5051877c3a70c2332d90ba4946508",
    "src/scanners/zero_base_discovery_runtime.py": "60f3c2ac08f88273df7f945f9a8f06a270041dbecf57921d9544416ae8fe770a",
    "src/scanners/zero_base_discovery_source.py": "5a4b5832dec647a0911484014afe8472c194bf4b1fe6165cc978aca3657ec9e4",
    "src/trading/config/owner_identity.py": "36f8983b4da46ed6f8958af429d1e4847430d55287be9a0502c123d7ae659e58",
    "src/trading/market/aftermarket_eligibility.py": "34cce97a46d2d16af19f900012026cd78dc47f32e03594329c2e4068909f1d53",
    "src/trading/market/completed_history.py": "b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20",
    "src/trading/market/entry_ws_snapshot.py": "7d8ef5bd84dbf21e379cad71abc0d6d258d0311850ecc95a995db42495732e38",
    "src/trading/market/quote_consistency.py": "9614e97cbd33130e2d66ff66a5f879ae32e690ae4864d6640f9e5e6297a45dc9",
    "src/trading/order/entry_liquidity_guard.py": "dc71e13e38c2f4464fd8d5a0840958b44546743e7766f5b092ff2ebea3824a56",
    "src/trading/order/owner_custody_registry.py": "a5b40329f5d46eff8ac11696b809d520fa48620a1a7104fb8adf6faa94c59c3c",
    "src/utils/kiwoom_utils.py": "5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641"
}
for _name, _sha in REVIEWED_NONFIXED_CURRENT_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_NONFIXED_CURRENT_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Final integration preserves both issued generations and one exact current set.
REVIEWED_NONFIXED_FINAL_SOURCES = {
    **REVIEWED_NONFIXED_CURRENT_SOURCES,
    "src/engine/monitoring/policy_generation_code_handoff.py": "52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4",
}
for _name, _sha in REVIEWED_NONFIXED_FINAL_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Diagnostic receipt syntax follows the existing lossless identifier owner.
REVIEWED_NONFIXED_OBSERVER_SOURCES = {
    **REVIEWED_NONFIXED_FINAL_SOURCES,
    "src/engine/monitoring/submission_bottleneck_monitor.py": "9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a",
}
for _name, _sha in REVIEWED_NONFIXED_OBSERVER_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Exact collection and payload-context successor; independent preparation reader.
REVIEWED_DELAY_COLLECTION_SOURCES = {
    "src/engine/kiwoom_websocket.py": "5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352",
    "src/engine/monitoring/ws_receive_expectation.py": "b1f73780582e4411d184fe25aacb8cafd27382099db33aa32595d495e8c3a233",
    "src/engine/sniper_state_handlers.py": "16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb",
    "src/engine/monitoring/policy_generation_code_handoff.py": "bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d"
}
REVIEWED_DELAY_COLLECTION_ORIGINS = {
    "src/engine/kiwoom_websocket.py": "701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474",
    "src/engine/monitoring/ws_receive_expectation.py": "2098bfda2c73f367f0bda84a5023063e5e37da92fe94608b0b7db3b2cd38dbc8",
    "src/engine/sniper_state_handlers.py": "193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d",
    "src/engine/monitoring/policy_generation_code_handoff.py": "52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4"
}
for _name, _sha in REVIEWED_DELAY_COLLECTION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {REVIEWED_DELAY_COLLECTION_ORIGINS[_name]}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Exact current submit-local repair; independent child verifies both endpoints.
REVIEWED_SUBMIT_FRESH_ORIGINS = {
    "src/engine/kiwoom_sniper_v2.py": "66b57f8ca7d37af5be3f6d5897a20e3a4ee5b7f32b5e2b511954d713d9e4006a",
    "src/engine/monitoring/policy_generation_code_handoff.py": "bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d",
    "src/engine/scalping/scanner_async_eval.py": "6daadef71a1e62c814986fdf9dd806a5a26b7d3aac1814900e24505f0d2256ca",
    "src/engine/sniper_state_handlers.py": "16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb",
    "src/scanners/zero_base_discovery_queue.py": "d8c93e78f8944428b6cfb726a88af9e4e0c39aee724c81c97d74d721d6d89d6b",
    "src/scanners/zero_base_discovery_runtime.py": "61ebea82400e4139ed2b0dd66a2b7af5dff9e890c491af7185739b5045e36675",
    "src/trading/entry/physical_send_guard.py": "83506e38c29ef132b05732320ac8d41f53d571bcf950cb4c0b17ed0ffbd1d41f",
}
REVIEWED_SUBMIT_FRESH_SOURCES = {
    "src/engine/kiwoom_sniper_v2.py": "35393c7ffa067328fc6e2a2df931a5e352adc65ca15730513ef74da3274d0881",
    "src/engine/monitoring/policy_generation_code_handoff.py": "2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d",
    "src/engine/scalping/scanner_async_eval.py": "376aef38820f7e2f2a6869b65822e1072eb0abe426836644c3ee9d7357b8bac7",
    "src/engine/sniper_state_handlers.py": "8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672",
    "src/scanners/zero_base_discovery_queue.py": "47da6fad4d1f301e99da12f38505a193ce6b2f9bbfc122cb338503bf4b177d3e",
    "src/scanners/zero_base_discovery_runtime.py": "441f47be2b070d26f1210b81088a7e879c87060335e9f4bef6b2dc55851fafd4",
    "src/trading/entry/physical_send_guard.py": "182543858c29babbb6875ec4511aa93c09fa230f016ec758c389c5f4511f9c20",
}
REVIEWED_SUBMIT_FRESH_PROJECTED_ORIGINS = {
    "src/engine/kiwoom_sniper_v2.py": "66b57f8ca7d37af5be3f6d5897a20e3a4ee5b7f32b5e2b511954d713d9e4006a",
    "src/engine/monitoring/policy_generation_code_handoff.py": "bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d",
    "src/engine/scalping/scanner_async_eval.py": "9fb2ac9ff75f620f008fb38a6611e5f08c6984d552c475e3314fa6ad6f3fefdf",
    "src/engine/sniper_state_handlers.py": "16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb",
    "src/scanners/zero_base_discovery_queue.py": "d8c93e78f8944428b6cfb726a88af9e4e0c39aee724c81c97d74d721d6d89d6b",
    "src/scanners/zero_base_discovery_runtime.py": "61ebea82400e4139ed2b0dd66a2b7af5dff9e890c491af7185739b5045e36675",
    "src/trading/entry/physical_send_guard.py": "1d5d6f7feb0fba4062d770db52dc74d0a8fca8dbdd10b48e0485c9ec80865c27",
    "src/engine/infrastructure/startup_validation_code_context.py": "9261405f04df1337774293dc47a2a6703c229f3ee9b0ed93d30c93ea42d67c6e",
}
for _name, _sha in REVIEWED_SUBMIT_FRESH_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _prior = {v for pair in _history for v in pair} | {
        REVIEWED_SUBMIT_FRESH_ORIGINS[_name],
        REVIEWED_SUBMIT_FRESH_PROJECTED_ORIGINS[_name],
    }
    if _name in REVIEWED_PREPARATION_SOURCES:
        _prior.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _prior)


# Preserved original scoped-scoring preparation generation.
REVIEWED_SCOPED_SCORING_INITIAL_SOURCES = {
    "src/engine/scalping/continuous_reversal_policy_v6.py": "8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da",
    "src/engine/scalping/reversal_cumulative_registration.py": "f5a35312f6a0fff8c27aa6eef87513cb5ed8ba49b56f06323311b64fdc48dea4",
    "src/engine/scalping/reversal_cumulative_postclose.py": "3943d7a42a662dcf1117d78aae433000effe08c75ca4355013afaeb96c8be3ed",
}
REVIEWED_SCOPED_SCORING_INITIAL_ORIGINS = {
    "src/engine/scalping/continuous_reversal_policy_v6.py": "9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4",
    "src/engine/scalping/reversal_cumulative_registration.py": "fd49ff4d01289a23891f3bb85ee5695134a73f95c55c1f6a00e6cfc2fe4d0624",
    "src/engine/scalping/reversal_cumulative_postclose.py": "f24f1cd9dba38de51a7e3193b506cb8b0e02a8b53fbc94348bf432140782e1f9",
}
for _name, _sha in REVIEWED_SCOPED_SCORING_INITIAL_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_SCOPED_SCORING_INITIAL_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Source-first scoped scoring, integrated over the consumed submit-fresh generation.
REVIEWED_SCOPED_SCORING_SOURCES = {'src/engine/scalping/continuous_reversal_policy_v6.py': '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', 'src/engine/scalping/reversal_cumulative_registration.py': '55a35b7182abef7cb4d863d5befd9a5523169569d6bd7cd8a017195e07db43e5', 'src/engine/scalping/reversal_cumulative_postclose.py': '6bfcbdb2569a318942f227e63850a3bec9a4b0827a34202cc7f474c4aba1f511', 'src/engine/automation/postclose_summary_handoff.py': '14d18b30d6f435f55949f1e4afca9d2b00952bc7e44c82054eb49ed67f2e98b2', 'deploy/run_threshold_cycle_postclose.sh': 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'}
REVIEWED_SCOPED_SCORING_ORIGINS = {'src/engine/scalping/continuous_reversal_policy_v6.py': '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', 'src/engine/scalping/reversal_cumulative_registration.py': 'fd49ff4d01289a23891f3bb85ee5695134a73f95c55c1f6a00e6cfc2fe4d0624', 'src/engine/scalping/reversal_cumulative_postclose.py': 'f24f1cd9dba38de51a7e3193b506cb8b0e02a8b53fbc94348bf432140782e1f9', 'src/engine/automation/postclose_summary_handoff.py': 'aeb5c0e1c259425c17de08af1dab323f2101d8147e1c7cd3c53731bcf78f024d', 'deploy/run_threshold_cycle_postclose.sh': 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac'}
for _name, _sha in REVIEWED_SCOPED_SCORING_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_SCOPED_SCORING_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Reviewed report-capability census and source-review publisher. Trading
# policy sources retain their original authority and complete dependency checks.
REVIEWED_REPORT_CENSUS_SOURCES = {'src/engine/automation/ordered_intraday_deploy.py': 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'src/engine/automation/policy_generation_fixture_validation.py': '29da6c2abd0c52620fa9ae84d376ac12cac758df10a8afec5c85af2a9d03ca25', 'src/engine/error_detectors/artifact_freshness.py': '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', 'src/engine/monitoring/policy_generation_code_handoff.py': '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', 'src/engine/monitoring/policy_generation_contract.py': '820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', 'src/engine/monitoring/policy_generation_validation.py': '83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c'}
REVIEWED_REPORT_CENSUS_ORIGINS = {'src/engine/automation/ordered_intraday_deploy.py': 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'src/engine/automation/policy_generation_fixture_validation.py': '3b3a796df23267330f4d3a0705cb356f7011d62a80407d34c1c587fd64794b2f', 'src/engine/error_detectors/artifact_freshness.py': 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'src/engine/monitoring/policy_generation_code_handoff.py': '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', 'src/engine/monitoring/policy_generation_contract.py': 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'src/engine/monitoring/policy_generation_validation.py': 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a'}
for _name, _sha in REVIEWED_REPORT_CENSUS_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_REPORT_CENSUS_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Native machine comparison path repair; no calculation or policy change.
REVIEWED_MACHINE_PATH_SOURCES = {'src/engine/automation/postclose_summary_handoff.py': '42d67773f5e574e15d7e82988682428b8111e6b48ec6a466cef4b9826a98234f'}
REVIEWED_MACHINE_PATH_ORIGINS = {'src/engine/automation/postclose_summary_handoff.py': '14d18b30d6f435f55949f1e4afca9d2b00952bc7e44c82054eb49ed67f2e98b2'}
for _name, _sha in REVIEWED_MACHINE_PATH_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_MACHINE_PATH_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact reviewed cost-producer and logical-storage consumer succession.
REVIEWED_NATIVE_COST_INTAKE_SOURCES = {'deploy/run_threshold_cycle_postclose.sh': '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'src/engine/scalping/ai_action_outcome_calibration.py': '84555ccb7672fd19e7fd36498fe2c9d481b3022ea641b8e8d6efe6ce13ec2ef2', 'src/engine/sniper_trade_review_report.py': 'dbf7a672f967bb449c22725221d21dbf5c5fa53e256fa64f7c1ad4822cec29cd', 'src/engine/compress_db_backfilled_files.py': '0760d1db83cd7d8456cac14e206056d56ddb72000e1f87bc61885b72e32f5dce'}
REVIEWED_NATIVE_COST_INTAKE_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e', 'src/engine/scalping/ai_action_outcome_calibration.py': 'c570880da2ac0a96fdab41a07aea9ddc8bdf9740d9ba542d364e8b5a4e469486', 'src/engine/sniper_trade_review_report.py': 'abefe48bfe066d9b234c4dc726d0cb91247a61c4ab1f68747f4c2279ca686da3', 'src/engine/compress_db_backfilled_files.py': '31e5e754441887eac1e8124515b8b4a69825be5e045feff7659aae54d80f7b80'}
for _name, _sha in REVIEWED_NATIVE_COST_INTAKE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_NATIVE_COST_INTAKE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# First report intake of independently verified original BUY observations.
REVIEWED_PRIOR_EXECUTION_SOURCES = {'src/engine/sniper_trade_review_report.py': '07bef13f9464ed388974228ffad5936a65096a2ff88b34a2c854d0cf0191cfb8', 'src/engine/lifecycle/broker_cost_allocation.py': '6c6b5e7f29de4e9941b4eea1f83292e3b4c6ca0425c1740fa3dda903add829a1', 'src/engine/log_archive_service.py': '56dc9e53626d3d64d2a57beeb0bfb6c8db346767aeb6c9bbc70b94b27d0b15c1'}
REVIEWED_PRIOR_EXECUTION_ORIGINS = {'src/engine/sniper_trade_review_report.py': 'dbf7a672f967bb449c22725221d21dbf5c5fa53e256fa64f7c1ad4822cec29cd', 'src/engine/lifecycle/broker_cost_allocation.py': '41c070efb7491eb2b7057b8ba64f03c6870a2fa513a062a0c81060a8d42258d3', 'src/engine/log_archive_service.py': 'fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543'}
for _name, _sha in REVIEWED_PRIOR_EXECUTION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_PRIOR_EXECUTION_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact consumed completion dependencies; later holding output is not an input.
REVIEWED_QUANTITY_SOURCE_SOURCES = {'src/engine/scalping/initial_quantity_monitor_projection.py': '8ddea89000551cec2b35972f0f0752861cfd4c4f512474cb469929b0dbe5ede8'}
REVIEWED_QUANTITY_SOURCE_ORIGINS = {'src/engine/scalping/initial_quantity_monitor_projection.py': 'e12b1702ab35598ff77113c3b42e0ae4e9d3aad623cda4a9161b34277e1ff350'}
for _name, _sha in REVIEWED_QUANTITY_SOURCE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_QUANTITY_SOURCE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Native stopped-source preparation dispatch; original source roles stay bound.
REVIEWED_STOPPED_PREPARATION_SOURCES = {'src/engine/automation/next_preopen_readiness.py': '626f7849ae5fa39bf41f667b6c1cfae6b0ca765714e357fce049c523c0eaeeb9', 'src/engine/automation/main_startup_validation.py': '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481'}
REVIEWED_STOPPED_PREPARATION_ORIGINS = {'src/engine/automation/next_preopen_readiness.py': 'b21095ca45f5844d1b2f6cf0cf0f312f44736e42cdf1a519eb65e7d39c0821f2', 'src/engine/automation/main_startup_validation.py': 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604'}
for _name, _sha in REVIEWED_STOPPED_PREPARATION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_STOPPED_PREPARATION_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact native policy code belongs to the execution workflow, not the selector.
REVIEWED_EXECUTION_EXACT_SOURCES = {'src/engine/automation/main_startup_validation.py': 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'}
REVIEWED_EXECUTION_EXACT_ORIGINS = {'src/engine/automation/main_startup_validation.py': '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481'}
for _name, _sha in REVIEWED_EXECUTION_EXACT_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_EXECUTION_EXACT_ORIGINS[_name])
    _history.update((_old, _sha) for _old in _origins)


# Coordination observations are distinct from immutable native policy inputs.
REVIEWED_HANDOFF_COORDINATION_SOURCES = {'src/engine/scalping/reversal_code_handoff.py': 'd79a22aecbd2e425fe00b40bdf19d8391ae63425d1cceff97657f3ae3581475f'}
REVIEWED_HANDOFF_COORDINATION_ORIGINS = {'src/engine/scalping/reversal_code_handoff.py': '945d695b08b5f8a6bb06ef723f5a9dc8226469e49c66e03eb79dca3a70e429f4'}
for _name, _sha in REVIEWED_HANDOFF_COORDINATION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_HANDOFF_COORDINATION_ORIGINS[_name])
    _history.update((_old, _sha) for _old in _origins)


# Native closed-parent custody and original future-issuer preparation reading.
REVIEWED_CLOSED_PARENT_SOURCES = {'src/engine/scalping/reversal_code_handoff.py': '2be83fd30237b4e83506462a4a5cc78dc8f4ad4ae85e23e8909864a41d9a7825'}
REVIEWED_CLOSED_PARENT_ORIGINS = {'src/engine/scalping/reversal_code_handoff.py': 'd79a22aecbd2e425fe00b40bdf19d8391ae63425d1cceff97657f3ae3581475f'}
for _name, _sha in REVIEWED_CLOSED_PARENT_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_CLOSED_PARENT_ORIGINS[_name])
    _history.update((_old, _sha) for _old in _origins)


# Transfer original native byte custody without changing semantic validation.
REVIEWED_ISSUER_BYTES_SOURCES = {'src/engine/scalping/reversal_code_handoff.py': '21760885de2a28bd7d5c5a021af3eb88c0fd0f31c890855b94be0e81f8b7b93c'}
REVIEWED_ISSUER_BYTES_ORIGINS = {'src/engine/scalping/reversal_code_handoff.py': '2be83fd30237b4e83506462a4a5cc78dc8f4ad4ae85e23e8909864a41d9a7825'}
for _name, _sha in REVIEWED_ISSUER_BYTES_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_ISSUER_BYTES_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact partial BUY research recovery and authenticated cost-only history rollover.
REVIEWED_QUANTITY_COST_SOURCES = {'src/engine/lifecycle/broker_cost_allocation.py': '98d7b7d529eb5e850b61da3a316c794dfd45dad939bbe18d344f83bfe4d3ebf2', 'src/engine/scalping/initial_quantity_policy.py': 'bf06e3259526962b0314ce570fdb656eba2a4797d90cf7afc95eedb7d023295d', 'src/engine/scalping/initial_quantity_monitor_projection.py': '10431b20d021e3e6088f09d2e8c9fd2b5bae09708423cfffc40036f4da1ee650'}
REVIEWED_QUANTITY_COST_ORIGINS = {'src/engine/lifecycle/broker_cost_allocation.py': '6c6b5e7f29de4e9941b4eea1f83292e3b4c6ca0425c1740fa3dda903add829a1', 'src/engine/scalping/initial_quantity_policy.py': 'a60fc47c9467e0da033f8371ebdb66627e632d6b1bcd00b9a915b333fc11fd2f', 'src/engine/scalping/initial_quantity_monitor_projection.py': '8ddea89000551cec2b35972f0f0752861cfd4c4f512474cb469929b0dbe5ede8'}
for _name, _sha in REVIEWED_QUANTITY_COST_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_QUANTITY_COST_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact cancel inventory and late-response ownership repair; no policy change.
REVIEWED_SELL_CANCEL_SOURCES = {'src/engine/sniper_state_handlers.py': '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', 'src/engine/sniper_execution_receipts.py': '7fc306ee8c5be3812ba8ccf02b45cd948c62600a654b7ddf331e19f685d54cee', 'src/engine/sniper_sync.py': 'a8788beb561139657e18c4342abfbf4273d7ca6317eea8985b57c34962bc3c69', 'src/engine/automation/ordered_intraday_deploy.py': '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac'}
REVIEWED_SELL_CANCEL_ORIGINS = {'src/engine/sniper_state_handlers.py': '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', 'src/engine/sniper_execution_receipts.py': 'c16009021a52faa9486d76f4b820c42b8574ebf2775c77192e60f87e1e7dcf90', 'src/engine/sniper_sync.py': 'da6289ec42399a5b7eea141defe6e061d6f78bcf06db3fd5e9d04e137695f1a2', 'src/engine/automation/ordered_intraday_deploy.py': 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a'}
for _name, _sha in REVIEWED_SELL_CANCEL_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_SELL_CANCEL_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact initial context, native quote/GAP and bounded normalized-copy successor.
REVIEWED_HOLDING_SOURCE_SOURCES = {'src/engine/sniper_state_handlers.py': '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', 'src/engine/scalping/trailing_entry_research_source.py': '44b82ff0440a95ed186b49dcbf340099b807850dbe76c15162e501553f07c705', 'src/engine/scalping/universal_trailing_replay.py': '26d175fc0ea9e17122214ce39fcdfd8fb48e6b11d7d26ac6bb97ef1bc9a3d66b', 'src/engine/automation/main_trailing_research_diagnostics.py': 'ed6483510949b113e675532881a3c40ceed40f2103698bfbd40f736bc6b872e5', 'src/engine/automation/main_trailing_source_reuse.py': '04e8748ad7e027b2152d36c90e49b4c300c96e4b546ded76d8537ab1b2701780'}
REVIEWED_HOLDING_SOURCE_ORIGINS = {'src/engine/sniper_state_handlers.py': '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', 'src/engine/scalping/trailing_entry_research_source.py': '661977bb6561e0a5fbaba8e69d7aea5cebb519c1ebebc19bbafee1cffca03ff0', 'src/engine/scalping/universal_trailing_replay.py': 'e3ae3ca14fab06562c90e28f17cc7565b4fba667e241fecfae18aa6b690923d7', 'src/engine/automation/main_trailing_research_diagnostics.py': '3e89be5cc9f924225ebbd3fc8164c9e3d22f82f2303493c96fbd4df1c4583feb', 'src/engine/automation/main_trailing_source_reuse.py': '1ca065ee8e90c19da97fa49273cefbd36b13ab644ca816c4bffbc733ad449755'}
for _name, _sha in REVIEWED_HOLDING_SOURCE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_HOLDING_SOURCE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact family-scoped capability reader; whole immutable inventories remain checked.
REVIEWED_CAPABILITY_SCOPE_SOURCES = {'src/engine/monitoring/policy_generation_code_handoff.py': '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892'}
REVIEWED_CAPABILITY_SCOPE_ORIGINS = {'src/engine/monitoring/policy_generation_code_handoff.py': '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40'}
for _name, _sha in REVIEWED_CAPABILITY_SCOPE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_CAPABILITY_SCOPE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Read-only native PREOPEN closure after an explicitly held collector shutdown.
REVIEWED_CLOSED_NATIVE_PREPARATION_SOURCES = {'src/engine/automation/next_preopen_readiness.py': 'bb2cd92fe684f55f292509b2fd7609c683e3d8d78746899b218e4da6ca11f8e1'}
REVIEWED_CLOSED_NATIVE_PREPARATION_ORIGINS = {'src/engine/automation/next_preopen_readiness.py': '626f7849ae5fa39bf41f667b6c1cfae6b0ca765714e357fce049c523c0eaeeb9'}
for _name, _sha in REVIEWED_CLOSED_NATIVE_PREPARATION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_CLOSED_NATIVE_PREPARATION_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact submit-call reference lifetime; original signal deadline and guards are unchanged.
REVIEWED_FINAL_SIGNAL_REFERENCE_SOURCES = {'src/engine/sniper_entry_latency.py': 'a86968300bd117acf5f8cf8168eb735264357b7dfa2385f607ba8dd5919b9e9d', 'src/engine/sniper_state_handlers.py': '0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', 'src/engine/scalping/reversal_evaluation_context.py': 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'src/engine/scalping/scanner_async_eval.py': '5830d0e031cb649d3a37b40aff61ea6e7d7548f16519f3d2e13d71acf71b3a95'}
REVIEWED_FINAL_SIGNAL_REFERENCE_ORIGINS = {'src/engine/sniper_entry_latency.py': '343ce1cb5a84b4b30d039942da42d4618cea4bc6f8350d0c7c22966552eda289', 'src/engine/sniper_state_handlers.py': '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', 'src/engine/scalping/reversal_evaluation_context.py': '5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', 'src/engine/scalping/scanner_async_eval.py': '376aef38820f7e2f2a6869b65822e1072eb0abe426836644c3ee9d7357b8bac7'}
for _name, _sha in REVIEWED_FINAL_SIGNAL_REFERENCE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_FINAL_SIGNAL_REFERENCE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)

# Exact carried SELL phase recovery; preserve original position and broker guards.
REVIEWED_CARRIED_OWNER_SOURCES = {'src/engine/sniper_sync.py': '990cc54f499be60b66571742cabbb94bf752f19e1e509b19c0404951a4dff33e'}
REVIEWED_CARRIED_OWNER_ORIGINS = {'src/engine/sniper_sync.py': 'a8788beb561139657e18c4342abfbf4273d7ca6317eea8985b57c34962bc3c69'}
for _name, _sha in REVIEWED_CARRIED_OWNER_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_CARRIED_OWNER_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)

# Exact carried SELL phase recovery; preserve original position and broker guards.
REVIEWED_REPORT_ORIGIN_SOURCES = {'src/engine/automation/policy_generation_fixture_validation.py': 'f3d751c05804013292e6a7dce04fc2a9b9bc9eb8b9dba073550ab2156461b7fa'}
REVIEWED_REPORT_ORIGIN_ORIGINS = {'src/engine/automation/policy_generation_fixture_validation.py': '29da6c2abd0c52620fa9ae84d376ac12cac758df10a8afec5c85af2a9d03ca25'}
for _name, _sha in REVIEWED_REPORT_ORIGIN_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_REPORT_ORIGIN_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)

# PRE physical-release wake and opt-in offline allocation comparison. The
# independent reader admits these exact source generations only; no policy
# membership, residence, retry deadline or provider authority is changed.
REVIEWED_PRE_DELIVERY_SOURCES = {
    "src/scanners/scalping_scanner.py": "84452ea2809ba2f2df523866e166dadf4b8d82bc66cbebc8270c126de8267150",
    "src/scanners/zero_base_discovery_queue.py": "164533023032985e914eb25aa71aea97a9736072efdb82450c42c1f36affe95e",
}
REVIEWED_PRE_DELIVERY_ORIGINS = {
    "src/scanners/scalping_scanner.py": "eb938c01d837d52973f7d47b59f96da1d338b2df9be8025c18d7c2f936546e16",
    "src/scanners/zero_base_discovery_queue.py": "47da6fad4d1f301e99da12f38505a193ce6b2f9bbfc122cb338503bf4b177d3e",
}
for _name, _sha in REVIEWED_PRE_DELIVERY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_PRE_DELIVERY_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Completion reporting is separate from existing startup admission. These exact
# reviewed sources retain the original execution and policy authority boundaries.
REVIEWED_POSTCLOSE_COMPLETION_SOURCES = {'deploy/run_postclose_finalization.sh': 'ea3f3bc7fb5cb50c6601de99ec3a92f100a3bdfe64a0d6f3a2afff8864ef44db', 'src/engine/automation/postclose_finalization_generation.py': 'a2a29adac3c9777bd6ffc26ae480b80e49a40cd19fc40ce8b0e5479a21f9e9d2', 'src/engine/error_detector.py': '8cafbf31719fa8cb4a52d887bf0d79a6506bf7c2c701535d771b798d3579b426', 'src/engine/runtime_approval_summary.py': '66440188ca5a2a0b1140f133dd106d75c629629d10ab22b5f83c6f8dc3f1cc16'}
REVIEWED_POSTCLOSE_COMPLETION_ORIGINS = {'deploy/run_postclose_finalization.sh': '3c8e94c94f259dc0717a649ff31bb51d56f2f00a59561ecff783b75875cd0267', 'src/engine/automation/postclose_finalization_generation.py': '0d70b7d26a768416c20b7345f47ac45155feda44469d3241930e48fa2f0e4c41', 'src/engine/error_detector.py': '42cd31da7a2c8267b584b2f0aa4fbe11d32e762ab08b283587a11ceb7157882e', 'src/engine/runtime_approval_summary.py': '8de2430637152fbc72c60d7f246273492754bcb922109e0f3d1afa88165e7d3a'}
for _name, _sha in REVIEWED_POSTCLOSE_COMPLETION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_POSTCLOSE_COMPLETION_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Partial SELL recovery restores original BUY identity only after an exact
# native journal match; current held quantity and all admission guards remain.
REVIEWED_BUY_LINEAGE_SOURCES = {'src/engine/kiwoom_sniper_v2.py': '05fd9d811b5d433f0e7fd86c8634dcb97fba480ac1fe8963053a0a25cd59c377'}
REVIEWED_BUY_LINEAGE_ORIGINS = {'src/engine/kiwoom_sniper_v2.py': '35393c7ffa067328fc6e2a2df931a5e352adc65ca15730513ef74da3274d0881'}
for _name, _sha in REVIEWED_BUY_LINEAGE_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_BUY_LINEAGE_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Partial-exit diagnostic identity only; original source gaps and guards remain.
REVIEWED_PARTIAL_GAP_SOURCES = {'src/engine/scalping/holding_profit_exit_semantics.py': '34e654bf8cfc979783b3966b96b952f900cdd67fc21a98ae107c87b2f91b0542'}
REVIEWED_PARTIAL_GAP_ORIGINS = {'src/engine/scalping/holding_profit_exit_semantics.py': '9c6fb04e8cfe5a776b245a2957deaaa764991bf0da1313b6eaae381b65998bd7'}
for _name, _sha in REVIEWED_PARTIAL_GAP_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_PARTIAL_GAP_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Entry expiry classification and bounded preclaim rank evidence only.
# Exact producer/trace/reader bytes require independent preparation intake.
REVIEWED_ENTRY_EXPIRY_SOURCES = {'src/engine/ai_engine_openai.py': '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', 'src/engine/scalping/ai_decision_trace.py': 'f1a072179283cba22d64cba81b435dee1becb4ed875666ec1911945ff5e7517a', 'src/scanners/zero_base_discovery_runtime.py': '06eb8c05864ab691c86e15b320ae99a19fb782a78899ac70ea79191c64040c9d'}
REVIEWED_ENTRY_EXPIRY_ORIGINS = {'src/engine/ai_engine_openai.py': '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', 'src/engine/scalping/ai_decision_trace.py': 'b6e45faa04e0ae78a3ffe81a1b0a4d180f103401c9c8e1fadc5d8e76200fdd80', 'src/scanners/zero_base_discovery_runtime.py': '441f47be2b070d26f1210b81088a7e879c87060335e9f4bef6b2dc55851fafd4'}
for _name, _sha in REVIEWED_ENTRY_EXPIRY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_ENTRY_EXPIRY_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact actual-completion projection and terminal BUY field delivery.
REVIEWED_HOLDING_PROJECTION_SOURCES = {'src/engine/holding_exit_observation_report.py': 'b7ec8cf43e586de98f0e18dbce3cf3eb439a706bab495c79ac759df6d32bab09', 'src/engine/holding_exit_sentinel.py': '39bc9d11bbc66fc4dd59325ef4c7a3e30f467ab9b855d5ef46dc1522f8488d23', 'src/engine/lifecycle/research_json_stream.py': '6b2d6827fe5b614328088b1bd7311737eb59194b0c706b071d223e063310f65e'}
REVIEWED_HOLDING_PROJECTION_ORIGINS = {'src/engine/holding_exit_observation_report.py': 'ed270681ec734cef04732baade2344d5b0f7e997b323eff621b031f4f273421e', 'src/engine/holding_exit_sentinel.py': '8122426c54a67bd3270519d11dc1faf980d3e8dedb11a7e02044f59801ee6f3d', 'src/engine/lifecycle/research_json_stream.py': '8010dd6b2fdc2b513edeaeff5866710e5b5706cfb7d51f4d1b24b964451edb72'}
for _name, _sha in REVIEWED_HOLDING_PROJECTION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_HOLDING_PROJECTION_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Observer hash reuse has invocation-only authority. Historical code endpoints
# below were already reviewed by the native family readers; unknowns still fail.
REVIEWED_OBSERVER_INVOCATION_SOURCES = {'src/engine/error_detectors/artifact_freshness.py': 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'src/engine/infrastructure/validation_digest_session.py': 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff'}
REVIEWED_OBSERVER_INVOCATION_ORIGINS = {'src/engine/error_detectors/artifact_freshness.py': '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', 'src/engine/infrastructure/validation_digest_session.py': '085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a'}
REVIEWED_HOLDING_EXPIRY_HISTORY = {'src/engine/holding_exit_observation_report.py': ('108fcdffa626abec4e90b263c12780e78c7f77e222b950e2407b0b00d462fa4f', '2ec0a7be672eb04044a9094b7ee445af66cef17720df83efe24e6148110ded03', '538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255', '6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9', '8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db', 'b7ec8cf43e586de98f0e18dbce3cf3eb439a706bab495c79ac759df6d32bab09', 'bd366b341b5515a0d7dcc2b4da47cf71320a0d703b617057037044d52b8c06e3', 'bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a', 'd9310a1136cc2086e83037c020d5d44a9d3b3f57d1207697bcd8eac8f6cf73fe', 'da364a9f0a6933158e95046f82e7669f0609244c51cd8f35e119949cc0bc0969', 'ed270681ec734cef04732baade2344d5b0f7e997b323eff621b031f4f273421e', 'fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5'), 'src/engine/holding_exit_sentinel.py': ('39bc9d11bbc66fc4dd59325ef4c7a3e30f467ab9b855d5ef46dc1522f8488d23', '5bc00325005b6d4346dc896c21741cec0e61fcd9904c6c947ae7774ce5e031e4', '7ae845b51d16bf425337e4758d1f83047f1f4e1c3479d39875523f0e2748012a', '8122426c54a67bd3270519d11dc1faf980d3e8dedb11a7e02044f59801ee6f3d', 'a02066a6f6538f7b4f855c5cc93ed3b5b4e661f4516c6191cd4859542cc5afdb'), 'src/engine/lifecycle/research_json_stream.py': ('1ea671f8ba5b5397257c2d1da513dee653b05379133073d1412ee4edf7a07a11', '53bd6a0cec6435ff0cfb399ad75fc9edd0b479463c06dea77bc5cae5e59db4b6', '6b2d6827fe5b614328088b1bd7311737eb59194b0c706b071d223e063310f65e', '8010dd6b2fdc2b513edeaeff5866710e5b5706cfb7d51f4d1b24b964451edb72', '8fd211dc5409ee6a5bdd619bef772255c07687e921b075d473f50f70303a6201', 'cfaf531c495730a6ae2f159601153749f8dc53ab297576250e03de61decf796b', 'f886a7510dbabda0db35cf264a9ea61aa7e50ddeb0a5cac407a2b479d7c4c944', 'fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0', 'ff07214148fce486e68e1db048469dd7a657553894cb3472960fea59c7ee09dc'), 'src/engine/error_detectors/artifact_freshness.py': ('09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'), 'src/engine/infrastructure/validation_digest_session.py': ('085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9')}
for _name, _sha in {**REVIEWED_HOLDING_PROJECTION_SOURCES, **REVIEWED_OBSERVER_INVOCATION_SOURCES}.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.update(REVIEWED_HOLDING_EXPIRY_HISTORY[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# P5 consumes the full DigestSession diagnostic schema across a process boundary.
REVIEWED_P5_DIAGNOSTIC_SOURCES = {'src/engine/automation/main_startup_validation.py': 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929'}
REVIEWED_P5_DIAGNOSTIC_ORIGINS = {'src/engine/automation/main_startup_validation.py': 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'}
for _name, _sha in REVIEWED_P5_DIAGNOSTIC_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_P5_DIAGNOSTIC_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# BUY preclaim semantics only: market veto stays active, source failures remain
# hard blocks. Exact shared-handler/diagnostic bytes need independent intake.
REVIEWED_PRECLAIM_MARKET_SOURCES = {'src/engine/sniper_state_handlers.py': '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'src/engine/monitoring/runtime_performance.py': 'a38222e79f79e06e06331dc6057059e88191f4e1688b5fe0cf82e59cd2148cbd', 'src/engine/ai_engine_openai.py': '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', 'src/engine/scalping/ai_decision_trace.py': 'f1a072179283cba22d64cba81b435dee1becb4ed875666ec1911945ff5e7517a', 'src/engine/scalping/ai_market_snapshot.py': '577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', 'src/scanners/zero_base_discovery_runtime.py': 'b93ba0f45617fe7d95887f81b9adb6941b9b61f40d3191047addbdc5a287e393'}
REVIEWED_PRECLAIM_MARKET_ORIGINS = {'src/engine/sniper_state_handlers.py': '0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', 'src/engine/monitoring/runtime_performance.py': '90d6d73bcbc758a880d631a5862f0f2b0ea6b6764255d4fa5a73e4ff47596d82', 'src/engine/ai_engine_openai.py': '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', 'src/engine/scalping/ai_decision_trace.py': 'b6e45faa04e0ae78a3ffe81a1b0a4d180f103401c9c8e1fadc5d8e76200fdd80', 'src/engine/scalping/ai_market_snapshot.py': '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', 'src/scanners/zero_base_discovery_runtime.py': '441f47be2b070d26f1210b81088a7e879c87060335e9f4bef6b2dc55851fafd4'}
for _name, _sha in REVIEWED_PRECLAIM_MARKET_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_PRECLAIM_MARKET_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Complete integration of reviewed delivery with the issued holding/P5 repair.
# Exact predecessor pairs retain custody; no policy or timing guard changes.
REVIEWED_DELIVERY_INTEGRATED_SOURCES = {'src/engine/sniper_state_handlers.py': '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'src/engine/monitoring/runtime_performance.py': 'a38222e79f79e06e06331dc6057059e88191f4e1688b5fe0cf82e59cd2148cbd', 'src/engine/ai_engine_openai.py': '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', 'src/engine/scalping/ai_decision_trace.py': 'f1a072179283cba22d64cba81b435dee1becb4ed875666ec1911945ff5e7517a', 'src/engine/scalping/ai_market_snapshot.py': '577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', 'src/scanners/zero_base_discovery_runtime.py': '15a4f7266f329fb12fe8fc600bc639e0592c11efcae90c3df9c87902dcb7133d'}
REVIEWED_DELIVERY_INTEGRATED_ORIGINS = {'src/engine/sniper_state_handlers.py': '0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', 'src/engine/monitoring/runtime_performance.py': '90d6d73bcbc758a880d631a5862f0f2b0ea6b6764255d4fa5a73e4ff47596d82', 'src/engine/ai_engine_openai.py': '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', 'src/engine/scalping/ai_decision_trace.py': 'f1a072179283cba22d64cba81b435dee1becb4ed875666ec1911945ff5e7517a', 'src/engine/scalping/ai_market_snapshot.py': '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', 'src/scanners/zero_base_discovery_runtime.py': '06eb8c05864ab691c86e15b320ae99a19fb782a78899ac70ea79191c64040c9d'}
for _name, _sha in REVIEWED_DELIVERY_INTEGRATED_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_DELIVERY_INTEGRATED_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact lifetime/response/delivery source successor. Original profiles remain addressable.
REVIEWED_ENTRY_LIFETIME_SOURCES = {'src/engine/ai_engine_openai.py': '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', 'src/engine/monitoring/runtime_performance.py': '397c11bf4cc06f74b2d904afe187d765284e543c17d27ed1cf92f8bd5b86640a', 'src/engine/scalping/continuous_reversal_policy_v6.py': 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'src/engine/scalping/entry_deadline.py': 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'src/engine/scalping/entry_machine_source_recovery.py': 'f363242b4979cfc076b166a991d02ef7b8f54fa2d92672e48fd47ca72bdc714f', 'src/engine/scalping/reversal_auxiliary_intraday.py': 'be51fd48fe976e61f6ebeefa76f81ff480c8401470e0efdfe2360307fcbe85cc', 'src/engine/scalping/reversal_auxiliary_tuning.py': '620b24ab335edd62d0d21cd0d7523ee6fa386ea9bb97da48e0dc12a507ca2911', 'src/engine/scalping/reversal_cumulative_postclose.py': '8753cb068c06998dd1d54c382bd86527b85eea8284713503376c0d0be3b8a5b1', 'src/engine/scalping/reversal_evaluation_context.py': '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'src/engine/scalping/reversal_extended_registration.py': '639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'src/engine/scalping/reversal_extended_runtime.py': 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'src/engine/scalping/reversal_extended_state.py': 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'src/engine/scalping/reversal_joint_registration.py': '53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', 'src/engine/scalping/reversal_path_runtime.py': 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'src/engine/scalping/reversal_registered_runtime.py': 'a6ed5c230affa6f6fb0637a36c60f1629429466fa62fc198b7a7c38ed60d15b5', 'src/engine/scalping/reversal_source_diagnostics.py': '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', 'src/engine/scalping/zero_base_probe.py': '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'}
REVIEWED_ENTRY_LIFETIME_ORIGINS = {'src/engine/ai_engine_openai.py': '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', 'src/engine/monitoring/runtime_performance.py': 'a38222e79f79e06e06331dc6057059e88191f4e1688b5fe0cf82e59cd2148cbd', 'src/engine/scalping/continuous_reversal_policy_v6.py': '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', 'src/engine/scalping/entry_deadline.py': '624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'src/engine/scalping/entry_machine_source_recovery.py': '5d28bf1ea8644cdb88d5e725d1002ede4f32b1a3542994e22a77d4013adbc406', 'src/engine/scalping/reversal_auxiliary_intraday.py': '7349250cfd4d60228c9225bc92e1d7db785136b2b2f3d95d6784668a70d752f3', 'src/engine/scalping/reversal_auxiliary_tuning.py': '265a06e3b26c59f616e2819a58dbd27935a4190a7eeea95aaaba6e3e2b1c7992', 'src/engine/scalping/reversal_cumulative_postclose.py': '6bfcbdb2569a318942f227e63850a3bec9a4b0827a34202cc7f474c4aba1f511', 'src/engine/scalping/reversal_evaluation_context.py': 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'src/engine/scalping/reversal_extended_registration.py': 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'src/engine/scalping/reversal_extended_runtime.py': '6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', 'src/engine/scalping/reversal_extended_state.py': '0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', 'src/engine/scalping/reversal_joint_registration.py': '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', 'src/engine/scalping/reversal_path_runtime.py': 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'src/engine/scalping/reversal_registered_runtime.py': '69fee6b7519fa7335320e11ac668315266c317c286e5bfada04360d2db064b1c', 'src/engine/scalping/reversal_source_diagnostics.py': '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'src/engine/scalping/zero_base_probe.py': '16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb'}
for _name, _sha in REVIEWED_ENTRY_LIFETIME_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_ENTRY_LIFETIME_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# The reviewed smart SELL successor carries a literal held-position fact.
# The native preparation reader admits both changed consumers together, while
# every issued predecessor and all policy/custody/source checks remain intact.
REVIEWED_HELD_SELL_SOURCES = {'src/engine/kiwoom_orders.py': '1e957677478847e69931f903b91058836c56b3604eba2bdcd6dccc966a226188', 'src/engine/sniper_state_handlers.py': 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226'}
REVIEWED_HELD_SELL_ORIGINS = {'src/engine/kiwoom_orders.py': '75df3ff7d8adfedd9e14ca0fb0d57675dd1279f12d52ff1d9b6c931746cee5a7', 'src/engine/sniper_state_handlers.py': '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483'}
for _name, _sha in REVIEWED_HELD_SELL_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_HELD_SELL_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Exact reviewed postclose integration. Source, report and pending-policy
# consumers travel together; predecessor generations remain independently bound.
REVIEWED_POSTCLOSE_INTEGRATED_SOURCES = {'src/engine/automation/ordered_intraday_deploy.py': '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', 'src/engine/infrastructure/market_eligibility_source.py': '83351b83534d3f6626b8fb4bc697cda22dd830e0a1863424d4a2619d37cfefdb', 'src/engine/kiwoom_orders.py': '1e957677478847e69931f903b91058836c56b3604eba2bdcd6dccc966a226188', 'src/engine/scalping/reversal_cumulative_registration.py': 'e6954b00e960cd03cb63d9193e5471017cc8394cf1d02a195eb1dcbf4c2db201', 'src/engine/sniper_state_handlers.py': 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'src/engine/sniper_trade_review_report.py': 'a13e1b73e76120a4ceb87a5c65b2a714bdc6845d9b38c81f3d1d37ce7be12b08', 'src/utils/kiwoom_utils.py': '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', 'src/utils/update_kospi.py': '11863bd21a626b0212d53670acdcd7293de8334fc45aa8e0cb3474bd82d2e09c', 'src/engine/infrastructure/runtime_release_router.py': 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'}
REVIEWED_POSTCLOSE_INTEGRATED_ORIGINS = {'src/engine/automation/ordered_intraday_deploy.py': '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'src/engine/infrastructure/market_eligibility_source.py': '6cf5edc490d49411307e2ed5b4ac151722b7b92009039e905efecc7bbd7f348a', 'src/engine/kiwoom_orders.py': '75df3ff7d8adfedd9e14ca0fb0d57675dd1279f12d52ff1d9b6c931746cee5a7', 'src/engine/scalping/reversal_cumulative_registration.py': '55a35b7182abef7cb4d863d5befd9a5523169569d6bd7cd8a017195e07db43e5', 'src/engine/sniper_state_handlers.py': '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'src/engine/sniper_trade_review_report.py': '07bef13f9464ed388974228ffad5936a65096a2ff88b34a2c854d0cf0191cfb8', 'src/utils/kiwoom_utils.py': '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', 'src/utils/update_kospi.py': 'e40a8c08a2c43f91d119893f3b2387a379a0de187f192df31999610cc04db98a', 'src/engine/infrastructure/runtime_release_router.py': '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601'}
for _name, _sha in REVIEWED_POSTCLOSE_INTEGRATED_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_POSTCLOSE_INTEGRATED_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Complete reviewed orchestration/source-custody successor, independently
# pinned here as well as in the operational handoff. Mixed generations fail.
REVIEWED_PREOPEN_VALIDATION_SOURCES = {
    "src/engine/automation/main_stop_postclose.py": "866997e7d0a376f6cb2b8cdcba0d8324ce9ffd5af19eafa080335364f9ecbf0d",
    "src/engine/automation/next_preopen_readiness.py": "c89c5869690c7a17c2f3b631a5a6cb2ca0319b11e4a04b426b09e4a5bd128895",
    "src/engine/automation/ordered_intraday_deploy.py": "76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85",
    "src/engine/automation/postclose_done_controller.py": "58df8d4a53c042b20bce02fe0408ca40a0429ee350389f1c9507f0c3947fef18",
    "src/engine/scalping/continuous_reversal_policy_v6.py": "78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b",
    "src/engine/verify_threshold_cycle_postclose_chain.py": "1a03cda3865c6c9fc3ed43a28827da848c480c0d47bd23d2677fcde1ce54aab2",
    "src/run_bot.sh": "0c1f6378db03d3cc71bd65f9d8c884ee02479ef1af0326d2b061bde3c1c381a6",
}
REVIEWED_PREOPEN_VALIDATION_ORIGINS = {
    "src/engine/automation/main_stop_postclose.py": "a2ea988c1bc93962f021d3f23dab2adbc67521e5fa0bfe41dc6fd1a5e9c5946e",
    "src/engine/automation/next_preopen_readiness.py": "ba72842e94099ffbf36fe7b04f41ffb823bf6690d047a6364858d5ac7a308bcc",
    "src/engine/automation/ordered_intraday_deploy.py": "779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9",
    "src/engine/automation/postclose_done_controller.py": "659a031cb296e8e23c614f4fb1f496a25500ff2fc05aacf74c9348885be059d1",
    "src/engine/scalping/continuous_reversal_policy_v6.py": "dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499",
    "src/engine/verify_threshold_cycle_postclose_chain.py": "da729cdbbd5cc34c7ce48910055788c6886c77dc37ee15d4e6aa3b1323f78c1f",
    "src/run_bot.sh": "e32584ab0ceea9b0a7a08428204d437f5abd022014c091d1771e6ee3f6d63d5e",
}
REVIEWED_PREOPEN_VALIDATION_PROFILE = {
    **REVIEWED_POSTCLOSE_INTEGRATED_SOURCES,
    **REVIEWED_PREOPEN_VALIDATION_SOURCES,
}
for _name, _sha in REVIEWED_PREOPEN_VALIDATION_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_PREOPEN_VALIDATION_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


# Complete reviewed source/diagnostic integration, including independent preparation readers.
REVIEWED_HOLDING_HISTORY_SOURCES = {'src/engine/ai/holding_exit_vote.py': 'f0b1aac8e07417748caeac0098086f24c95901a2471bab6c3bdece5bf78f7770', 'src/engine/ai_engine_openai.py': 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20', 'src/engine/holding_exit_sentinel.py': 'e2bb53a00436e5574ec9117d2514deba798baf675d500b44e7a31eafa2d4dd93', 'src/engine/scalping/holding_decision_context.py': '620f1f2b9792c377597fbb50905fbc131ca85cc45951480a827b58484aa6c6fb', 'src/engine/scalping/holding_profit_exit_semantics.py': '64e8d0b7099b0db70f990e48ddab0c2f622116c1273921e6d12034759ce1146b', 'src/engine/scalping/main_stop_replay.py': '0ab852c1320e43df4662e51072836b71eba4088c03aee75e303cbf2899748632', 'src/engine/scalping/reversal_auxiliary_compatibility.py': 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf', 'src/engine/scalping/reversal_auxiliary_intraday.py': '02ec66f262e98123de56165890cb11c1a0464d44e4cff227845637be6e130ff9', 'src/engine/scalping/reversal_auxiliary_production_input.py': '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'src/engine/scalping/reversal_auxiliary_registry.py': '05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', 'src/engine/scalping/reversal_auxiliary_research_population.py': 'b3e3ee8c30c15a98d88839c5f167ce79930d2b295856919a08e0b728cbbe25b0', 'src/engine/scalping/reversal_auxiliary_tuning.py': '973032158d823ca2a2a96f413f4fd44acd88876c5485b366f7ec61a7e2a10211', 'src/engine/sniper_state_handlers.py': 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'src/trading/market/completed_history.py': '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb'}
REVIEWED_HOLDING_HISTORY_ORIGINS = {'src/engine/ai/holding_exit_vote.py': '71a10ceba6d02af93c8295aec826566d3730990f7c44ca5b9c8fcae1a4e51b73', 'src/engine/ai_engine_openai.py': '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', 'src/engine/holding_exit_sentinel.py': '39bc9d11bbc66fc4dd59325ef4c7a3e30f467ab9b855d5ef46dc1522f8488d23', 'src/engine/scalping/holding_decision_context.py': '879cf1d27bfa993e30edbf9bcce97510869d547f54ec673ee1535b5524bd63c2', 'src/engine/scalping/holding_profit_exit_semantics.py': '34e654bf8cfc979783b3966b96b952f900cdd67fc21a98ae107c87b2f91b0542', 'src/engine/scalping/main_stop_replay.py': '6f8764a3b6485ce4eb66b6d47c600620d74405e246e52a78de2f3311a90ea594', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', 'src/engine/scalping/reversal_auxiliary_intraday.py': 'be51fd48fe976e61f6ebeefa76f81ff480c8401470e0efdfe2360307fcbe85cc', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', 'src/engine/scalping/reversal_auxiliary_registry.py': 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77', 'src/engine/scalping/reversal_auxiliary_research_population.py': '9baabb21fe9099fa963776b38a00f124b79d371aec8bab254ae17afd65bef690', 'src/engine/scalping/reversal_auxiliary_tuning.py': '620b24ab335edd62d0d21cd0d7523ee6fa386ea9bb97da48e0dc12a507ca2911', 'src/engine/sniper_state_handlers.py': 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'src/trading/market/completed_history.py': 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a'}
REVIEWED_HOLDING_HISTORY_PROFILE = {
    **REVIEWED_PREOPEN_VALIDATION_PROFILE, **REVIEWED_HOLDING_HISTORY_SOURCES,
}
# Native selected reader has revalidated this issued predecessor for stop,
# holding and delay; preserve its exact bytes through the reviewed successor.
REVIEWED_HOLDING_HISTORY_ISSUED_ORIGINS = {'src/engine/ai/holding_exit_vote.py': 'd8c9de0ae5270c0e40f8494941def50c69d52fbab887b5c38c6b1fd73129514c', 'src/engine/ai_engine_openai.py': '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', 'src/engine/holding_exit_sentinel.py': 'a02066a6f6538f7b4f855c5cc93ed3b5b4e661f4516c6191cd4859542cc5afdb', 'src/engine/scalping/holding_decision_context.py': '5d7577896850988b6419996a76db24344f7a612c59ecac339331ca2e841607d2', 'src/engine/scalping/holding_profit_exit_semantics.py': 'c3c2d58e97c99f24e37001622874ec294b4e8424e3dc22052495f35ec564b93a', 'src/engine/scalping/main_stop_replay.py': '4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'src/engine/scalping/reversal_auxiliary_intraday.py': 'f4e59f492decd157b4e81df67ff485d3ed949c243278d16b49dad73b78918e97', 'src/engine/scalping/reversal_auxiliary_production_input.py': 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a', 'src/engine/scalping/reversal_auxiliary_registry.py': '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', 'src/engine/scalping/reversal_auxiliary_research_population.py': '79953b70d771de44252d0cacd4ef1ddab7a19d9f2a45512e9fb47574c898c0c6', 'src/engine/scalping/reversal_auxiliary_tuning.py': 'a8ac3de954b2d6e89e3a46bb49501edc0d35df47621900a1d22b6d8492672412', 'src/engine/sniper_state_handlers.py': 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'src/trading/market/completed_history.py': 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7'}
for _name, _sha in REVIEWED_HOLDING_HISTORY_SOURCES.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_HOLDING_HISTORY_ORIGINS[_name])
    _origins.add(REVIEWED_HOLDING_HISTORY_ISSUED_ORIGINS[_name])
    if _name == "src/engine/holding_exit_sentinel.py":
        _origins.add("c1d1868fee331a01bf8562965e3ada03c7ed20b61df4149f99308629b52a8b96")
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((_old, _sha) for _old in _origins)


REVIEWED_TIMEOUT_TERMINAL_HANDLER = "ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372"
REVIEWED_TIMEOUT_TERMINAL_PATH = "src/engine/sniper_state_handlers.py"
REVIEWED_TIMEOUT_PROBE_PATH = "src/engine/scalping/zero_base_probe.py"
REVIEWED_TIMEOUT_PROBE = "3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3"
REVIEWED_TIMEOUT_CHANGED = {
    REVIEWED_TIMEOUT_TERMINAL_PATH: REVIEWED_TIMEOUT_TERMINAL_HANDLER,
    REVIEWED_TIMEOUT_PROBE_PATH: REVIEWED_TIMEOUT_PROBE,
}
REVIEWED_TIMEOUT_TERMINAL_SOURCES = {
    **REVIEWED_HOLDING_HISTORY_SOURCES,
    **REVIEWED_TIMEOUT_CHANGED,
}
REVIEWED_TIMEOUT_TERMINAL_PROFILE = {
    **REVIEWED_HOLDING_HISTORY_PROFILE,
    **REVIEWED_TIMEOUT_CHANGED,
}
# Carry every previously reviewed origin into this one exact successor; no
# unreviewed current hash or partial predecessor generation is accepted.
for _name, _current in REVIEWED_TIMEOUT_CHANGED.items():
    _timeout_origins = {
        value for pair in REVIEWED_PREPARATION_HISTORY.get(_name, ()) for value in pair
    }
    if _name in REVIEWED_HOLDING_HISTORY_SOURCES:
        _timeout_origins.add(REVIEWED_HOLDING_HISTORY_SOURCES[_name])
    if _name == REVIEWED_TIMEOUT_PROBE_PATH:
        _timeout_origins.add("834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3")
    REVIEWED_PREPARATION_HISTORY.setdefault(_name, set()).update(
        (origin, _current) for origin in _timeout_origins
    )


# Exact probe provenance and ADD-only scope integration. Issued profiles remain
# immutable; missing, dirty or mixed complete generations are never successors.
REVIEWED_PROBE_AVG_CHANGED = {
    "src/engine/ai_engine_openai.py": "19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b",
    "src/engine/scalping/ai_market_snapshot.py": "91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4",
    "src/engine/scalping/entry_setup_live_policy.py": "d1fecf59bd0a0d6f358f40908aaf694f0d01e50f26ed4825aa28ca2d852fa2af",
    "src/engine/scalping/avg_down_rebound.py": "aed10b239f4ddfe069f70db5c3f69cd4114380fab85e85da7a39f477c6adf112",
    "src/engine/scalping/holding_path_vote_policy.py": "bd6c7b6dc00c90d80b9b66a146e76c4bf1110ec4b7267abcb9fe0b9b723b7432",
    "src/engine/sniper_state_handlers.py": "cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8",
    "src/engine/error_detectors/artifact_freshness.py": "33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1"
}
REVIEWED_PROBE_AVG_PROFILE = {
    **REVIEWED_TIMEOUT_TERMINAL_PROFILE, **REVIEWED_PROBE_AVG_CHANGED,
}
for _name, _current in REVIEWED_PROBE_AVG_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    if _name in REVIEWED_TIMEOUT_TERMINAL_PROFILE:
        _origins.add(REVIEWED_TIMEOUT_TERMINAL_PROFILE[_name])
    _history.update((origin, _current) for origin in _origins)


# Reviewed startup byte-custody, completed-bar and stop-only integration.
# Preserve prior complete profiles and authenticate each original issuer separately.
REVIEWED_STARTUP_STORAGE_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', 'src/engine/automation/ordered_intraday_deploy.py': '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_STARTUP_STORAGE_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/error_detectors/cron_completion.py': ['87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/entry_policy_deep_research.py': ['cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_STARTUP_STORAGE_PROFILE = {
    **REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_STARTUP_STORAGE_CHANGED,
}
for _name, _current in REVIEWED_STARTUP_STORAGE_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_STARTUP_STORAGE_ORIGINS[_name]
                    if origin != _current)


REVIEWED_SCOPED_ENTRY_CHANGED = {
    "src/engine/ai_engine_openai.py": "630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb",
    "src/engine/scalping/continuous_reversal_policy_v6.py": "9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1",
    "src/engine/scalping/entry_deadline.py": "d976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819",
    "src/engine/scalping/reversal_extended_intraday.py": "11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb",
    "src/engine/scalping/reversal_extended_registration.py": "f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b",
    "src/engine/scalping/reversal_joint_registration.py": "90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4",
    "src/engine/scalping/reversal_extended_runtime.py": "d71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47",
    "src/engine/scalping/reversal_extended_state.py": "6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b",
    "src/engine/scalping/reversal_path_runtime.py": "5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae",
}
REVIEWED_SCOPED_ENTRY_ORIGINS = {
    "src/engine/ai_engine_openai.py": "19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b",
    "src/engine/scalping/continuous_reversal_policy_v6.py": "78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b",
    "src/engine/scalping/entry_deadline.py": "af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c",
    "src/engine/scalping/reversal_extended_intraday.py": "710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3",
    "src/engine/scalping/reversal_extended_registration.py": "639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab",
    "src/engine/scalping/reversal_joint_registration.py": "53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4",
    "src/engine/scalping/reversal_extended_runtime.py": "e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7",
    "src/engine/scalping/reversal_extended_state.py": "a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e",
    "src/engine/scalping/reversal_path_runtime.py": "a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340",
}
REVIEWED_SCOPED_ENTRY_PROFILE = {
    **REVIEWED_PROBE_AVG_PROFILE,
    **REVIEWED_SCOPED_ENTRY_CHANGED,
}
for _name, _current in REVIEWED_SCOPED_ENTRY_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _origins = {value for pair in _history for value in pair}
    _origins.add(REVIEWED_SCOPED_ENTRY_ORIGINS[_name])
    if _name in REVIEWED_PREPARATION_SOURCES:
        _origins.update(REVIEWED_PREPARATION_SOURCES[_name])
    _history.update((origin, _current) for origin in _origins)


# Complete reviewed integration: startup/storage and scoped signal lifetime.
# Neither standalone predecessor authenticates a partial mixture of this generation.
REVIEWED_STARTUP_SCOPED_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', 'src/engine/ai_engine_openai.py': '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', 'src/engine/automation/ordered_intraday_deploy.py': '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_extended_intraday.py': '11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_STARTUP_SCOPED_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_STARTUP_SCOPED_PROFILE = {
    **REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_STARTUP_SCOPED_CHANGED,
}
for _name, _current in REVIEWED_STARTUP_SCOPED_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_STARTUP_SCOPED_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_STARTUP_SCOPED_AUX_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/ordered_intraday_deploy.py': '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', 'src/engine/scalping/continuous_reversal_policy_v6.py': '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_STARTUP_SCOPED_AUX_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_STARTUP_SCOPED_AUX_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_STARTUP_SCOPED_AUX_CHANGED}
for _name, _current in REVIEWED_STARTUP_SCOPED_AUX_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_STARTUP_SCOPED_AUX_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_LIFETIME_SOURCE_PHASE_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/ordered_intraday_deploy.py': '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_LIFETIME_SOURCE_PHASE_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_LIFETIME_SOURCE_PHASE_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_LIFETIME_SOURCE_PHASE_CHANGED}
for _name, _current in REVIEWED_LIFETIME_SOURCE_PHASE_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_LIFETIME_SOURCE_PHASE_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_DATED_REPORT_PARENT_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/ordered_intraday_deploy.py': '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_DATED_REPORT_PARENT_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_DATED_REPORT_PARENT_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_DATED_REPORT_PARENT_CHANGED}
for _name, _current in REVIEWED_DATED_REPORT_PARENT_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_DATED_REPORT_PARENT_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_ACTIVE_REPORT_CLOSURE_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_ACTIVE_REPORT_CLOSURE_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_ACTIVE_REPORT_CLOSURE_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_ACTIVE_REPORT_CLOSURE_CHANGED}
for _name, _current in REVIEWED_ACTIVE_REPORT_CLOSURE_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_ACTIVE_REPORT_CLOSURE_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_STARTUP_SUBMISSION_SOURCE_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_STARTUP_SUBMISSION_SOURCE_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_STARTUP_SUBMISSION_SOURCE_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_STARTUP_SUBMISSION_SOURCE_CHANGED}
for _name, _current in REVIEWED_STARTUP_SUBMISSION_SOURCE_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_STARTUP_SUBMISSION_SOURCE_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_POSTCLOSE_SELECTED_STOP_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_POSTCLOSE_SELECTED_STOP_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_POSTCLOSE_SELECTED_STOP_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_POSTCLOSE_SELECTED_STOP_CHANGED}
for _name, _current in REVIEWED_POSTCLOSE_SELECTED_STOP_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_POSTCLOSE_SELECTED_STOP_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_CANCEL_STATE_STORAGE_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/entry_cancel_wait_tuning.py': '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'src/engine/monitoring/policy_generation_contract.py': '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'src/engine/monitoring/policy_generation_validation.py': '734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_CANCEL_STATE_STORAGE_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/entry_cancel_wait_tuning.py': ['38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa', '49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4', '7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5', '860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe', 'bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e', 'd557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa', 'e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', '404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/policy_generation_validation.py': ['83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c', 'bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238', 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a', 'd925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0', 'f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_CANCEL_STATE_STORAGE_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_CANCEL_STATE_STORAGE_CHANGED}
for _name, _current in REVIEWED_CANCEL_STATE_STORAGE_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_CANCEL_STATE_STORAGE_ORIGINS[_name]
                    if origin != _current)


# Reviewed aftermarket source-evidence successor over the full integrated inventory.
REVIEWED_CANCEL_STORAGE_REVIEW_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/entry_cancel_wait_tuning.py': '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': '0c614b9cea8cd071b8dbeeaf820c5597b99e23242b295389b59349e18cb45b3e', 'src/engine/monitoring/policy_generation_contract.py': '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'src/engine/monitoring/policy_generation_validation.py': '734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_CANCEL_STORAGE_REVIEW_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/entry_cancel_wait_tuning.py': ['38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa', '49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4', '7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5', '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', '860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe', 'bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e', 'd557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa', 'e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', '404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/policy_generation_validation.py': ['734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', '83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c', 'bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238', 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a', 'd925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0', 'f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_CANCEL_STORAGE_REVIEW_PROFILE = {**REVIEWED_PROBE_AVG_PROFILE, **REVIEWED_CANCEL_STORAGE_REVIEW_CHANGED}
for _name, _current in REVIEWED_CANCEL_STORAGE_REVIEW_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_CANCEL_STORAGE_REVIEW_ORIGINS[_name]
                    if origin != _current)


# Complete causal-item successor; issued cancellation storage profiles stay immutable.
REVIEWED_CAUSAL_ITEM_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/entry_cancel_wait_tuning.py': '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'src/engine/monitoring/policy_generation_contract.py': 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'src/engine/monitoring/policy_generation_validation.py': '734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_CAUSAL_ITEM_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/entry_cancel_wait_tuning.py': ['38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa', '49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4', '7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5', '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', '860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe', 'bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e', 'd557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa', 'e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', '404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '0c614b9cea8cd071b8dbeeaf820c5597b99e23242b295389b59349e18cb45b3e', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/policy_generation_validation.py': ['734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', '83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c', 'bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238', 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a', 'd925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0', 'f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_CAUSAL_ITEM_PROFILE = {**REVIEWED_CANCEL_STORAGE_REVIEW_PROFILE, **REVIEWED_CAUSAL_ITEM_CHANGED}
for _name, _current in REVIEWED_CAUSAL_ITEM_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_CAUSAL_ITEM_ORIGINS[_name]
                    if origin != _current)


# Complete prefix-cost-context successor; issued cancellation storage profiles stay immutable.
REVIEWED_PREFIX_COST_CONTEXT_CHANGED = {'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/entry_cancel_wait_tuning.py': '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/log_archive_service.py': '1ee4737a38be9737a5d48411b836266c8a97d34e9328008aa8c50106b8b56b41', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'src/engine/monitoring/policy_generation_contract.py': 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'src/engine/monitoring/policy_generation_validation.py': '734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_PREFIX_COST_CONTEXT_ORIGINS = {'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/entry_cancel_wait_tuning.py': ['38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa', '49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4', '7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5', '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', '860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe', 'bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e', 'd557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa', 'e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', '404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/log_archive_service.py': ['08b7c8d890bd5d2857a428776195d1168fa4cba5dff7ee7d587e7466527114c3', '18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af', '1a3f94cc9e50ab7768cd7b7fb2953a3c0787a15f5b99e7a9f40231a41f8b81f2', '56dc9e53626d3d64d2a57beeb0bfb6c8db346767aeb6c9bbc70b94b27d0b15c1', '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '0c614b9cea8cd071b8dbeeaf820c5597b99e23242b295389b59349e18cb45b3e', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/policy_generation_validation.py': ['734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', '83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c', 'bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238', 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a', 'd925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0', 'f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_PREFIX_COST_CONTEXT_PRODUCER_ORIGINS = {'src/engine/log_archive_service.py': '56dc9e53626d3d64d2a57beeb0bfb6c8db346767aeb6c9bbc70b94b27d0b15c1'}
REVIEWED_PREFIX_COST_CONTEXT_PROFILE = {**REVIEWED_CAUSAL_ITEM_PROFILE, **REVIEWED_PREFIX_COST_CONTEXT_CHANGED}
for _name, _current in REVIEWED_PREFIX_COST_CONTEXT_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_PREFIX_COST_CONTEXT_ORIGINS[_name]
                    if origin != _current)


# Complete prefix-cost-context successor; issued cancellation storage profiles stay immutable.
REVIEWED_PREFIX_COST_HANDOFF_CHANGED = {'deploy/run_monitor_snapshot_safe.sh': '169653c4d4ba6223a080e9c76a9787676a97960ebf1aa731b563cd5290aab853', 'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/entry_cancel_wait_tuning.py': '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': '281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/log_archive_service.py': 'a978bf1417db9daedf6b3e3e0c487200532f8eef82c98c479f513c5b1f5ebb12', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'src/engine/monitoring/policy_generation_contract.py': 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'src/engine/monitoring/policy_generation_validation.py': '734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_PREFIX_COST_HANDOFF_ORIGINS = {'deploy/run_monitor_snapshot_safe.sh': ['0592007e50f20784981f7fe47a5424ed9b986399ea77a30fe2ad780f1150637f'], 'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/entry_cancel_wait_tuning.py': ['38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa', '49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4', '7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5', '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', '860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe', 'bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e', 'd557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa', 'e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', '404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/log_archive_service.py': ['08b7c8d890bd5d2857a428776195d1168fa4cba5dff7ee7d587e7466527114c3', '18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af', '1a3f94cc9e50ab7768cd7b7fb2953a3c0787a15f5b99e7a9f40231a41f8b81f2', '1ee4737a38be9737a5d48411b836266c8a97d34e9328008aa8c50106b8b56b41', '56dc9e53626d3d64d2a57beeb0bfb6c8db346767aeb6c9bbc70b94b27d0b15c1', '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '0c614b9cea8cd071b8dbeeaf820c5597b99e23242b295389b59349e18cb45b3e', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/policy_generation_validation.py': ['734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', '83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c', 'bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238', 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a', 'd925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0', 'f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_PREFIX_COST_HANDOFF_PRODUCER_ORIGINS = {'src/engine/log_archive_service.py': '56dc9e53626d3d64d2a57beeb0bfb6c8db346767aeb6c9bbc70b94b27d0b15c1'}
REVIEWED_PREFIX_COST_HANDOFF_PROFILE = {**REVIEWED_PREFIX_COST_CONTEXT_PROFILE, **REVIEWED_PREFIX_COST_HANDOFF_CHANGED}
for _name, _current in REVIEWED_PREFIX_COST_HANDOFF_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_PREFIX_COST_HANDOFF_ORIGINS[_name]
                    if origin != _current)


# Complete permanent scheduling and as-of custody successor; issued profiles stay immutable.
REVIEWED_CRON_PHASE_BINDING_CHANGED = {'deploy/install_postclose_done_controller_cron.sh': 'b33242679122cc072caa7ff57072ccd72fc4d3e73fbda4661953bfb7aac8110e', 'deploy/install_threshold_cycle_cron.sh': 'afa27cb228ccf3e46a636399888cf9c20023341e8f4ce7780dd60c1010101ebe', 'deploy/install_tuning_monitoring_postclose_cron.sh': 'cabda94f2b5f3db3947d141782c54706d13e665f89c9bfb2b4dfd67756f1a326', 'deploy/run_monitor_snapshot_safe.sh': '169653c4d4ba6223a080e9c76a9787676a97960ebf1aa731b563cd5290aab853', 'deploy/run_threshold_cycle_postclose.sh': '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', 'src/bot_main.py': '09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', 'src/engine/ai_engine_openai.py': '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', 'src/engine/automation/entry_cancel_wait_tuning.py': '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', 'src/engine/automation/main_startup_validation.py': '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'src/engine/automation/ordered_intraday_deploy.py': '223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', 'src/engine/build_next_stage2_checklist.py': 'e9259373ad57094012e643967a685607b10289a711c3734ebabd22ae329fa958', 'src/engine/buy_funnel_sentinel.py': '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', 'src/engine/error_detectors/artifact_freshness.py': '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', 'src/engine/error_detectors/cron_completion.py': 'bd4a22e4c1972746b8e2659c72090b2de7ca8afb23e57d366a696e0fec024802', 'src/engine/infrastructure/log_retention.py': '24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', 'src/engine/infrastructure/runtime_release_router.py': '19eb9c710a338a3dc407572f305f614f17e9df8496e9ebe7a3b15b953e85b075', 'src/engine/infrastructure/validation_digest_session.py': 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee', 'src/engine/kiwoom_websocket.py': 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'src/engine/log_archive_service.py': 'a978bf1417db9daedf6b3e3e0c487200532f8eef82c98c479f513c5b1f5ebb12', 'src/engine/monitoring/intraday_entry_flow_report.py': '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30', 'src/engine/monitoring/main_fixed_watch_policy_research.py': 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032', 'src/engine/monitoring/policy_generation_code_handoff.py': 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'src/engine/monitoring/policy_generation_contract.py': 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'src/engine/monitoring/policy_generation_validation.py': '734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', 'src/engine/monitoring/sentinel_summary_contract.py': '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', 'src/engine/monitoring/submission_bottleneck_monitor.py': '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', 'src/engine/scalping/ai_market_snapshot.py': 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261', 'src/engine/scalping/continuous_reversal_policy.py': 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1', 'src/engine/scalping/continuous_reversal_policy_v6.py': '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'src/engine/scalping/entry_deadline.py': 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819', 'src/engine/scalping/entry_policy_deep_research.py': '2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'src/engine/scalping/entry_policy_hypothesis_research.py': 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', 'src/engine/scalping/reversal_auxiliary_compatibility.py': '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', 'src/engine/scalping/reversal_auxiliary_production_input.py': '0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', 'src/engine/scalping/reversal_auxiliary_registry.py': 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'src/engine/scalping/reversal_evaluation_context.py': '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', 'src/engine/scalping/reversal_extended_intraday.py': '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', 'src/engine/scalping/reversal_extended_registration.py': 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b', 'src/engine/scalping/reversal_extended_runtime.py': 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'src/engine/scalping/reversal_extended_state.py': '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'src/engine/scalping/reversal_joint_registration.py': '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4', 'src/engine/scalping/reversal_path_runtime.py': '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'src/engine/scalping/reversal_source_diagnostics.py': '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36', 'src/engine/scalping/zero_base_probe.py': '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', 'src/engine/sniper_state_handlers.py': '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', 'src/trading/market/completed_history.py': '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'src/utils/kiwoom_utils.py': '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a'}
REVIEWED_CRON_PHASE_BINDING_ORIGINS = {'deploy/install_postclose_done_controller_cron.sh': ['1c7a59cea5856a6b5fe1fc5da84536fa1be7e82daf3389ec52884480767cc76a'], 'deploy/install_threshold_cycle_cron.sh': ['53ba1b065f412abfcaacecf450f7228846b259206ea79fb67c954a8a649a99e0'], 'deploy/install_tuning_monitoring_postclose_cron.sh': ['bcd7e1f3293461e5df79d98ae1cf81848a84fc4eea7143d0813d6a6c8df19c05'], 'deploy/run_monitor_snapshot_safe.sh': ['0592007e50f20784981f7fe47a5424ed9b986399ea77a30fe2ad780f1150637f', '169653c4d4ba6223a080e9c76a9787676a97960ebf1aa731b563cd5290aab853'], 'deploy/run_threshold_cycle_postclose.sh': ['00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c', '18bac5fbc4aae04338a61ea618bc811395e0a4d58de334fbca28d49ab1c614b6', '21df7914eb2f21733dee4fe6d57378cdb0a66b00793d30599e1193dcb740e63d', 'c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470', 'ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac', 'dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067', 'f6040a75cbba42f6c9c4ebfb90cf4d664e696c38c71fc22b29d76ed41ed1ec7e'], 'src/bot_main.py': ['09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8', '162c15efe5caf925274186071db64eda1b0b726e68f5f408b86741145fc888ea', '6ee76f8cd712f79eccacc69a4df5911499bf15db15754c93a13d9ecd64dbac5d'], 'src/engine/ai_engine_openai.py': ['194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584', '19b8e360293f3e8a3542333775b8c7b342f1ec30b6b0f8dfcbe0b8f7f17f994b', '278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2', '3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7', '376b3ce6f8ae75a5f629904c7d0a8b08670d69514b37fc4fb7db19a7e43d21de', '3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3', '424a6ae8e6c904430b9fbb601a6fdf9d9eec6aa3ab8b2c68be2f4c6919291940', '4534fc7e63f3c9df0be4c82bc8c75af2bb4d02cc4f3673a31d64f54a79765429', '4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162', '5482e28106659d646d29b9abcf3428ea7dfe989f07a1f36f59e4a4aaf8f6d2f4', '630a5519af15150d74b751bd549422d1134c7abf9a4901e0ff9646fa76972dfb', '703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07', '808000bc7fd3782583a00ecce63e0a5e5704f6e6694e7c3311537aae72579b25', '9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56', 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185', 'cc30c12c7bc806a793016a731a4b0ca58dadab250d79aff76cfbcf470373c06e', 'e6ffee39c0b99d73cf3ef3203f43a4d5946d88e6674258d2de58f5ef1e423f20'], 'src/engine/automation/entry_cancel_wait_tuning.py': ['38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa', '49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4', '7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5', '7f1c301aceae983a7d532470a82462db78ba7028022dc165cb7137d9ea27c332', '860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe', 'bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e', 'd557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa', 'e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582'], 'src/engine/automation/main_startup_validation.py': ['14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7', '680d244ea1d468af3fee125fa1b18b558e584bc79bb8aeb29073c4572b13e481', '992438432d3a6fd99a33f569380c1c9a18c5ef9289db700fbfbc5fbc9080985d', 'b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54', 'bfc7e9a9c425f7a0a13ede4f5333046e73f02589ab4f03a5e95065185561f929', 'e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604', 'e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64', 'fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c', 'ffc3433a9b8ef4a79f46562cecb4de59ed8a8b2a09ace5bb50027bb99f545c8f'], 'src/engine/automation/ordered_intraday_deploy.py': ['223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc', '404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6', '4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756', '43f5856b6d8963b627c21981911e4f944dbca98b8ef706436b053bc96209f003', '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', '64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21', '76097fa94f4eb66f6efc7f7ba3b5fc6b697672a072fb21919d80af9ee7b08a85', '779332fbb54665bef40ab39b993c8fcdb3aeb2850ac043b4fd3f668e162162f9', '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', '7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026', '92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab', '9cc092cb1f592b6399ee73a049e07e05cfe613525350fcfdfbb37546a6eabaac', 'a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed', 'afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab', 'c208f4ed8c369522c9554e87c4c03d57145f8ffac5f9a7175b05088b4c829bf1', 'd14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b', 'd56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af', 'd67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90', 'ddf0b36a3ed279c7ab89ad60e39f29d5d171c8137215e67c5b6eecc9d04baf2a', 'e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae', 'f20868ee64e670985aeefbb8ae05d674aff8fd28744e0dfc41dee087a8db56fb', 'f4c46ebf3cfb0112a06da6a03e195b119b5a18376a6386e0fbb2efecdeed5e2e', 'fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423'], 'src/engine/build_next_stage2_checklist.py': ['bc7bd6d121cdbda066eb6e696ad88a606397703c73766f3c0fa8413a503a3aff'], 'src/engine/buy_funnel_sentinel.py': ['40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a', '4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1', '680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510', '6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993', '72ed2bf11dcab9ce6b3527ca1f5b8502452ec9af8bdd3c9ac4ce5b3d5bdf1455', 'a02d6c28e6ecf32ac67f99a60188d2c61bcb6cfc22f037022fa669be0ca46dd2', 'b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7'], 'src/engine/error_detectors/artifact_freshness.py': ['09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9', '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', '2b3302868f445aece1a0e853cae2e248c30a9c4aa76ddfbc2bd86022a0d1386a', '33949dda5fef2ff04d931bd94b61c812c5383c4adb5439c377ca05f36bbcb5e1', '3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc', '47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4', '5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6', '5fb82e262bf670d0469dde7f82eacacf29c9c52bce78a9433d2c02617d6e0a79', '6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9', '6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa', '756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2', '7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376', '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27', 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a', 'defb7bb396c703cbb47acb83eb85bc9ac1d7ea57eca16c49c57a9a27485cfc67', 'edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6', 'f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf', 'f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e'], 'src/engine/error_detectors/cron_completion.py': ['281acdf8a5afa76e66e7c16c5ae53469c9a399a177b273fc790720b6c3548f9c', '87416fe29bff97db7afc637294a4352c48209e0a034934b9e4fc30e83db98410'], 'src/engine/infrastructure/log_retention.py': ['24774b9c5e6328203fc56f918ec6b58e5efacf261d5f3f723b222a4302201a9f', '4d27d4f11b3054d7604387201e9428a91cce5797ffb75d2a5c3d1ec755d10443'], 'src/engine/infrastructure/runtime_release_router.py': ['02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63', '49533a69b9cdd178ee6f580dd23085b97802391b9a8c2de1111fb17a2b710054', '49ae9494fd501e182b4b360256dd4bab5542d7db2b25bb1d1e2186717f661601', '58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308', 'a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d', 'ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962', 'dde5a9007bd25d918233642574ceb567de672b4ebe3a59a4363e24c3e2742f29'], 'src/engine/infrastructure/validation_digest_session.py': ['085b09f49408d7b544250cbf297e82052c1d6cab9df554c07d812e67ace7b74a', '40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056', '5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86', '655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1', '87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da', '8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3', 'bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9', 'd99dd1bb98a950f8ca05fc87275f883f7965eb63e34a7dd6bee061c2e87d04ff', 'ef61f71629f277d128faf7160c6c474258fb38767ccee8e6b6d7d5aa976000ee'], 'src/engine/kiwoom_websocket.py': ['1ce0eb18925736a6378ba6899d2700bc80e7563983da380b6cfa4558958bcfdb', '215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3', '5b22cec0dfd6871ccfc26d15b308845ec24f792556b87399d1561d770aa3a4e5', '5f8a0027e517f385a34fe9683aa34a6d7626b2f09efce7ab697889be363e3352', '6a794b5feb6e53990231e75404f1110b4b0cc91467b175345fdd4b0aef4be471', '701fe3127352e8c29300d43134ab4e3bdb59f6486491ae7a91a4ff574c3ca474', 'a0e9ab1108ec22d4dfb914d8eef7992234418b51a0bc5062ff4a39dd4d1cdfcd', 'a8ac34a024da459f64c4c17bc2b6e5a4d3f8c14616eb69e5003fde9ed76fdea1', 'ae6186d59bde4795d8c105e98d362328c23e594e55cf741f6c7972bd96308e25', 'cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637', 'd338a30b18f7fce6e79325865dcd3f40900533a8457a93f972f3f87262822c0c', 'd5f4dc2cb836a3789acc2a5066fcefba1880dadd88bb3f33588a4f9cdb5c8784', 'ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730', 'ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377'], 'src/engine/log_archive_service.py': ['08b7c8d890bd5d2857a428776195d1168fa4cba5dff7ee7d587e7466527114c3', '18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af', '1a3f94cc9e50ab7768cd7b7fb2953a3c0787a15f5b99e7a9f40231a41f8b81f2', '1ee4737a38be9737a5d48411b836266c8a97d34e9328008aa8c50106b8b56b41', '56dc9e53626d3d64d2a57beeb0bfb6c8db346767aeb6c9bbc70b94b27d0b15c1', '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'a978bf1417db9daedf6b3e3e0c487200532f8eef82c98c479f513c5b1f5ebb12', 'fbede30bebadb696a80bdcb765e584d18fa830c18e3655b849bf51c8b4099543'], 'src/engine/monitoring/intraday_entry_flow_report.py': ['2a8beb347d7fa5bf8b81b6b47ef4c5e5e39c55d3a769c1c0e0897b5fb6ca36f0', '546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30'], 'src/engine/monitoring/main_fixed_watch_policy_research.py': ['73c8e1a9082708ed81945cba3fd70739bf4d08e33ced2546e99fa67844afc96b', 'ebcde8b6bc1fb368482b1bb4129fecbc15f3c1a8087c46e86d6b2eb71dbb6032'], 'src/engine/monitoring/policy_generation_code_handoff.py': ['02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04', '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', '056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2', '0c614b9cea8cd071b8dbeeaf820c5597b99e23242b295389b59349e18cb45b3e', '1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc', '1cf34076b36be91af885c82ec15f6ff0aa5b01338b30d2b22aa5e77089d24365', '1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e', '2205cfa0be617994a148557397ae4bc1a13c1c9052d9b045cbc4ac0c1475223d', '28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411', '396b5dab90462247ba59f9c0fe2d7b57e46148f6934ca679febf0269cb691a40', '3a41e689b7c59de0a35bc2b76bd43effca721399d4936e9f747392e4a0951892', '41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef', '47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f', '4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b', '4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62', '52830e315e7f9be90d774b080ca31e79aca76bf7f6fdaf9f0dc29da38fa434a4', '5390fba948c04da7692d0d640316621dea3e0496ee67a8ae1b17a022647782a9', '58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e', '62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25', '64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc', '7108296fed9882a4b2e2aac016de457e493698f06d33bdc7405e6adde72707ee', '7f557af576c9bf36a8311b713cd6bbde2de40ad7c626b983c75952526d672529', '858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a', '93c77c8978f67592c4df75278cebb4dd1cda0cbc1a5a14d6110c232d0158ad50', '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', '9e1cd4b6934a31061d42b7801dd2a693f9beed65e6cfb84bd9d1b4520e35d4c8', 'aaf846749468811ae09e2a3d7d1bd99021a849f495a7edc8e0fbce4ec0f81226', 'af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc', 'b106d3748ba4dcd040248281046d9b8fbebd91a6f9aff6efc18861d278d84250', 'b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444', 'b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d', 'b57047a6fa64616c3027079d40db3eeb522b691e2499c8b4f90453425436a22d', 'b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841', 'b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e', 'bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f', 'bdf9c47cb05206eea269ba3ead0ba0083ff79a51da390cb3862d96d7782db40d', 'ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee', 'd54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b', 'd6cc6f4180ff14d6ea965a174f3db15f62527d1349d375170ca14b1e1b42ae9d', 'e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb'], 'src/engine/monitoring/policy_generation_contract.py': ['820fa372a844a7e605a82b840e0ad7af4a5d889507e312f1f4dff3a2ec65c0a9', '9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9', '9d1790d4ec77b7ffa420725b0b3cd349b8b22eac0f296bcde528a71bbddb9cfe', 'afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4', 'b6b9a97d455b25b9d95296d1831421c7132bcafee479aa4b258d963700676d98', 'e72472f82c1fc81c6103b618b9b1a3230c47a332a012654b1b50366ce2137489', 'fb55201d74668f25fcc8927eb6862beeb2a00f6ee4b6f361bf0492b7cbf446fa', 'ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028'], 'src/engine/monitoring/policy_generation_validation.py': ['734325be72615d8be8466934660d41f39d5f06a0dbd113564175b397b0edd878', '83dd37ff2381801acb287a0060c61dd2afda3c89af5c1f76e504e5cf52de6e6c', 'bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238', 'caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a', 'd925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0', 'f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc'], 'src/engine/monitoring/sentinel_summary_contract.py': ['06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80', '15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c', '182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb', '28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565', '44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd', '7f71509a725c4851b24e4db09020af5c0aba7325ac3a2372461f332e96a8066e', 'c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117', 'eab146de69c72b73f7d7f52e3ee5cc079a9f2dafd9d2360806520b798da4ae8f'], 'src/engine/monitoring/submission_bottleneck_monitor.py': ['00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae', '038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda', '0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e', '0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e', '499c3b8a66d39b6eaa85da36a4ef0aa46a0201c4e2d18184f07ec02c7c071cf8', '6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085', '7ac3ba09372b54efe9f20d3bdfb4c9428832e8039a091625fdbb834d1b650cf2', '808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57', '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c', '9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1', '9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb', '9f38385273e4a89085f3f974d962b1bb31b40348a87ff2e7944bc26f3c8fde6a', 'a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8', 'c1e3a4fe731fbc8909ff132de0d7929b162534e0b960d8e514950e587b60fcfd', 'f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902'], 'src/engine/scalping/ai_market_snapshot.py': ['577d610ae0ace22261e994f41217c8ed8cfe5162e296eca0231d426480c08db8', '7afe284ac20ac0a8f91df336bafdffac91494150d3248db83adc95619c07864a', '91840590d93b9ac2a3fdfb97e5cedfb1ae5cd5e84875f18dbe6727a74ede8ee4', 'c888a01a83040b32087fcc0bca32e11adf8b9f1596b031c6f138b18ba286c261'], 'src/engine/scalping/continuous_reversal_policy.py': ['2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd', '4a0eacb434de9af173b9807606f4333b7a414519ad5daf4d5b137693963d378e', '7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744', '82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b', 'baeb94c6a27bca23027fc4e52b460ac9a886500bc0b17420a282132906d9e3b1'], 'src/engine/scalping/continuous_reversal_policy_v6.py': ['0412a2b239cea96136f3d93347e399aea1fa9f7a782f8d679a57ffec5329390b', '17b3e2c673334dc7ddb24b41de698f40d3e16602cb3231258082cf02c4250ea4', '78c2e8a00ab0b87df3a42a0f35318598a3960e441bdbac0e090a0cb2e59a1b8b', '8c0a0a8effebd618029a9414c88ec0abee585e9fda24ed8b25327ee5fe6228da', '9342dec3beb2683d68f6851d58e8e6614f5481630abb4590d809024e8e3e5da4', '9685e84a08faa6ebe65aa9e91dec5ccd22264c598bb333390e57169023350ca1', '9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e', 'b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2', 'b357d2491d064cf331e8951124fba237043798caacf8da11ed130fb394230d79', 'dba3674350cb2a0b3b563236da605c79076d1fc0f3679ce1d9792144d4eb7499', 'eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460'], 'src/engine/scalping/entry_deadline.py': ['624fa132d48afb2ea9bd54978ff0e1b47665ce88d957ea28c88c545bc6e71916', 'af15f4b414bf0536002e9541fa67935e13de805bd97b4a01369f21a296e19a7c', 'd976f683b52d6235b6fa8739f4123c7f667ae12bcb1a2c54d8bb2b6c606ec819'], 'src/engine/scalping/entry_policy_deep_research.py': ['2ad114c4be7bf217545b8ce9bc36cc66394ea6f9e880816bd38ba1b63f3070e6', 'cf4b349b4776c29937184570e174e3a32bed85b75a1468ec55161c833b5e912e'], 'src/engine/scalping/entry_policy_hypothesis_research.py': ['474148295179e11d9465d4be93649af32a92fd82c9728446ec6b8423fff0db79', 'd172f54324899b7acf77a848d2e90f4884b8137aab24f194ec4b55b154f1a494'], 'src/engine/scalping/mechanistic_entry_runtime_policy.py': ['0fa74a8a2d245ea28a098073a215419095bde1d9d34cd974beff5fa488ae621a', '215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867', '2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08', '439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951', '45011f040639b3b241c4380f2aa60b615d332e6142c4dfbbf46689b3170e93af', '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'b3f63db7ba451860bb397c4a5c7838747ab53173509697df30b5a750dadc6537'], 'src/engine/scalping/reversal_auxiliary_compatibility.py': ['05d728265ca85e27fac5af90a1676f2675631af0d2be63406b5c2ac619558cef', '3ed7f888244a28c1f5d668cf17bc7ea9688a1a9b4441ae113d5ab9db931e44c6', '459d74a5314fdab6a3adb5ce89e445429ca4c9377739e1941755c7e2ad1f932a', '77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34', '9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce', 'df74d438bcdcf7472d7c856ced01d551f00ad951a1aaeb31e17bf89aae63d5bf'], 'src/engine/scalping/reversal_auxiliary_production_input.py': ['0620ff56cb6074efc2e1c2fca4443d7f731b1d4f6f4e0b6d4a799d1951c270b7', '0e576decb06aa17fff3548cdf15f4f23a2a87db57596b67095b7f8313d2f920f', '29bcf083d4849d0c8ca883c75a4397caba47448aa2c4951671e669eeeb638003', '324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464', '642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb', 'ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a'], 'src/engine/scalping/reversal_auxiliary_registry.py': ['05d8a9d276bba9d76aec24c869427a422b2c56378a6d22bacc01c06338cd94b7', '7421c595f810d155ad7b6f1ce264107adca8c3f14a23961aeeffbc6427cf7719', '80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0', '8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651', 'bec428d90463f855189272f20c258d05686a3fbfc6195fa6ce47ea5463b2fadb', 'e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77'], 'src/engine/scalping/reversal_evaluation_context.py': ['5eabeecc8cc043b42e9e7df0a4fe51733736cfe2d8c3e94267ad95f765856a63', '7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458', '942849d9dc2111f98bb4002d9f69ed446e0ed40960b44ca81fc99477de726760', '97ea26a45aa2484d25234eca0c83432fd6365afb3fb1adb26dcb5f3e89a69533', 'b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72', 'c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43', 'e394bbf86455185ac7081d3b419f041141766b4f8566791dcd3309b75a2bf4c9', 'fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654', 'fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2'], 'src/engine/scalping/reversal_extended_intraday.py': ['11ab9a7f08b2d595a40ef8efbb72bbda11b54178fa2c74b843589a431039f9fb', '4d378ecf2f8385fb0b74f8dcbf50842712503b884ea44440e9b3a4bfd1d7df48', '710661a7957111db81a61daca914d41dd5a1eb6b830d019efa365cb8e809ddb3'], 'src/engine/scalping/reversal_extended_registration.py': ['639643acfa06a46ddd5602ccfae056fe84bf812f0a4a35fc070acec6c96911ab', 'cd23cb34d20a15ae2d96a1c69bbcf2d33fb0b393d1d32f6a6ca04e0211a50144', 'f74666d09ffaf31120f250e10abbd1a5a1f6af090b0f7eea3162c792f7fc651b'], 'src/engine/scalping/reversal_extended_runtime.py': ['6b07229c7df2169ce18c1772d7459c59675266eca0c750cc16f52edc43c81c0e', '718b0669d34bf232674c0c2948802c73d2b2bf2a1bdfd2c29c0363a235f19ffc', 'd71057c5dec014f5a3dfac40313bcc774d0dc10487f1237b05829767747aba47', 'e80703262e2013f7164ffbb728d554e437476d2c83be0e6a919868e2934d40d7', 'f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b'], 'src/engine/scalping/reversal_extended_state.py': ['0e0d28be1cbb78e30f3e092e57f8f1adb3274379286a7a5d254a7e446eba34a1', '59b4b781c0185067bf307d5bc261cdc058d7cfcd4b70f39da8cb2bd1aadb5e66', '6f9402d54333b03a89dba81f257a6eec9dc6b52d6b6ace6d8e823400b524650b', 'a99704651c9c54cdc7f9131ed07b957fa10f8bf3d9625e408114559cc24ec21e', 'fb34756ccaf4224f5ae171dc36e69332e13184e2eef5279dca1782b4373488a3'], 'src/engine/scalping/reversal_joint_registration.py': ['53665208e48d459ad3a5e16d8492b7a01ffe0dd2fedd4994ad64452543d7ccb4', '6794108ea423f4073fdaadee2fb12f6e4a697a36fb9bb807846e76ec55b2907c', '90858229b4e80407d698fefeb291c0cd7813d4d8a33bd168a7c9f31a63c7bec4'], 'src/engine/scalping/reversal_path_runtime.py': ['476641e53d6c49a0c0c143f11e5a66a59c49d31ab49ee0c4eca7876a65760ced', '5d1ae6236aeb94cec7f1e9c9728f0deb74539d0308164ca1aebf4bd29c1df4ae', 'a1ea25c96870f2d478f12f3e5de81bcab64f4eaeb3c02cedcc977e16b697b340', 'a9b85e85869199ce01b32881591f3f8a89ca59bcc3ad2b996defdf0350a0ba67', 'ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36'], 'src/engine/scalping/reversal_source_diagnostics.py': ['3072a3bb0f67af8ee96cf3063d6940ef3fb0ff92c0bd5592c717d4b184f72ceb', '53391b706f363982b56ac4039d9770ff75efc01026ef96257148c8fd9ea52e33', '78c8ef6e40993a2d72dd20e0f5e3994defe74530a4de14e7bfac517739a4dc84', '997523f01e1583f1522328f2e16a15b8f25d7994bfe8e52f74fd14039fb44865', 'bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee'], 'src/engine/scalping/samsung_fixed_watch_evaluation_research.py': ['85c7331abac4df49b0650ecdf9c17e90b0ea4adb1820f71a95441c81727cf622', 'c4caa832c252cdb8e8088d5234beb4193180619e1ebc569c4f0c036603f0bc36'], 'src/engine/scalping/zero_base_probe.py': ['16f5e06e86943ef735fd2a20ca850a7215939e17adc734cd215762f117dacfbb', '2e5ee61aafe016389214d61e4affc11ac3a236c51e6744c97bead74fd1e6dbdd', '3410d2d2cf61c15e2b8c32c873249f8931f8313f27e8f4d0cb5c5dbf2535fed3', '3be910f21c565bfabac9ae68072a4174adf30afeac99fdf9b3ce49a6fa7d65be', '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', '834e020db2e2a14e6daa08153b688867d77d9de07814d5c07189beaa78be2af3'], 'src/engine/sniper_state_handlers.py': ['0bb6cc87e8acead7c0161bfe3d4c3ed24aa92a440a9647fbb61b69ba33bf02dd', '0c8c1874583f1ff23993b23e3187289d205c155bc257b3cb89e4f839a26a4d2c', '0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541', '16fc3202f724a2fb78d0da7e01989966560d39c7fa7439473b692a160308a2eb', '193cfb02eed0f45b553f26b3777fb921f1ecc2fa1be46c5dbdd7b2a50831b13d', '21a8ab598c4b334a4795a99236f1d49453e4da17b0feca18423ff3c91c3171d4', '2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9', '2eb4ed4fe413266422d0d2460bf30572979b4696ba217dadb32b02e0caf80aa8', '49901457d397a02b37e257d8e5a5a58df7c8cacbc3e0d82b1b3a3c21975fa322', '51856ec3f5ec75d1242a7013ebe10140a4e402cd180de1e0f5f38339675faf93', '56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20', '6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66', '6e05b0846d01ed54059021c6e44599a0668a8c7302dbfe69c7948131afb67fb3', '739fa0bfc847af66436d59ce1ff15be2959dd5f9f4c69152bbd55b33600ae0ab', '73a3790ee1a36435f84e3eaaaa5cc73c6e58e810d4043d9d8b1e4bd2e5aa6fbd', '82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6', '8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9', '8e070b77c3cd1a53454862bc18c7a7ddee09da158d862f4e93fdd56226287672', '95aa2214c1fe308dc8ebb57f028ac868d314a7df5934b18e338e0a9f0aa73483', 'b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d', 'b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9', 'bc0e823b2f358509d07dd39bc0051a5e0a3f823c687d1a0580b279242ed66e54', 'bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686', 'c7b1330cc82731b2362816c54ffd3c9df50536ef51878ee7a42b344e94d17dc3', 'cf559fca33ee59963675d9d068b353b8521999bec34f5872e634c146697b7cec', 'dd51075488ae00e544358905b7140710bbd046e42ea7bf8a236e79142adf98ff', 'e25983d9d6175fb628cc3d483ae8f522a4f336f8ce31f107d6a3cf757bd52847', 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'e8284be9145b83822d35585b19154fbc723f22cdf4c1a4050b92dc04c2e02226', 'ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86', 'eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa', 'ecd17595735b6bfe3d5262a256d5fc1d637254a1cf4fecf662bed059932ff372', 'edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419', 'f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d'], 'src/trading/market/completed_history.py': ['381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5', '4c300481759830843a9a3077f0690fcb6264a4e4d5ef9ce6c0eb35e7ef05dfbb', '55a5c60b2b07c616dd2a3361a3b731de69fcfda50d4523a52d045ec01bb6caaa', 'b027394b5ff8b650e972d939d2dd480be17bd15ca9f4a148e594340de8a05c20', 'b5ed23ac54b9dbaf5e74ddde92716c479447a49bc5595871c7141e6628bafc1a', 'dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7', 'e1a55df448d146ac26e2c526ab060b297b3afeff1baef0ee7628624d7f0abbb0'], 'src/utils/kiwoom_utils.py': ['00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f', '1a1c885edfd0a38921b2c8661c36787ee315d45a299491b63c1452c28545167a', '498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323', '57f948fc300aa86aff52b698c7863c1b85ad2afe5d015545df9f6264b93513eb', '5c4b21121fab7a7d7fe436b6a17e376a7a9e0b79bb8b9e987612b5332840e641', '84cb769fd56cb2273973d22260ded580147bf3c284e2c31b93fc53533205444a', 'a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f', 'ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95']}
REVIEWED_CRON_PHASE_BINDING_PROFILE = {**REVIEWED_PREFIX_COST_HANDOFF_PROFILE, **REVIEWED_CRON_PHASE_BINDING_CHANGED}
for _name, _current in REVIEWED_CRON_PHASE_BINDING_CHANGED.items():
    _history = REVIEWED_PREPARATION_HISTORY.setdefault(_name, set())
    _history.update((origin, _current) for origin in REVIEWED_CRON_PHASE_BINDING_ORIGINS[_name]
                    if origin != _current)

# The P5 recheck transfers only native byte identities; semantic validation is
# still performed in its own child. The full preceding profile remains required.
_P5_RECHECK_OWNER = "src/engine/automation/main_startup_validation.py"
_P5_RECHECK_CURRENT = "3874cb131182242f74184dd65ea25629c7ecfb8eeebdecf25eb51fb5e12f5dde"
REVIEWED_P5_RECHECK_PROFILE = {
    **REVIEWED_CRON_PHASE_BINDING_PROFILE,
    _P5_RECHECK_OWNER: _P5_RECHECK_CURRENT,
}
_p5_history = REVIEWED_PREPARATION_HISTORY.setdefault(_P5_RECHECK_OWNER, set())
_p5_origins = {value for pair in _p5_history for value in pair}
_p5_origins.add(REVIEWED_CRON_PHASE_BINDING_PROFILE[_P5_RECHECK_OWNER])
_p5_history.update((origin, _P5_RECHECK_CURRENT) for origin in _p5_origins
                   if origin != _P5_RECHECK_CURRENT)


REVIEWED_SCHEDULED_SUFFIX_DEPENDENCIES = {
    "src/engine/automation/postclose_finalization_generation.py":
        "3a34c0eaa23718ca6f090747eeb99129f0ae4b49186633ed07a3dc944b30dba8",
    "src/utils/market_day.py":
        "ebef1d35c9405b772484d34459eabf8ca26e59fec0bfd92aebe1b7d17781a511",
}
_suffix_owner = "src/engine/automation/postclose_finalization_generation.py"
_suffix_current = REVIEWED_SCHEDULED_SUFFIX_DEPENDENCIES[_suffix_owner]
_suffix_history = REVIEWED_PREPARATION_HISTORY.setdefault(_suffix_owner, set())
_suffix_origins = {"a2a29adac3c9777bd6ffc26ae480b80e49a40cd19fc40ce8b0e5479a21f9e9d2"}
_suffix_origins.update(value for pair in _suffix_history for value in pair)
_suffix_history.update((origin, _suffix_current) for origin in _suffix_origins
                       if origin != _suffix_current)


# One registration is consumed by both the independent preparation reader and
# the ordered handoff reader. Historical profiles retain their original bytes.
REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e",
        "6ecdd207980ff3f41b20b873791867f9b14ec84de80731b73e905c1fe4fbb18e",
    ),
}
REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE = {
    **REVIEWED_P5_RECHECK_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION.items()},
}
REVIEWED_SUBMISSION_MONITOR_TRANSITION = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "0a527ad29a96caf0f408db3467e8d407dccb8e552330f8f55e3e09a40dfc198e",
        "f3a09a8c7890b3946a3c28fa3465056ae41dfd0bd2e149be77e7ae3bdf33eaae",
    ),
    "src/engine/scalping/continuous_reversal_policy_v6.py": (
        "9f468cb97f07087ed2b714d2deda695f6b6985718ec2fb9eb2fcbe9fce57128e",
        "1f2812919d27c23bc48e106a6f37ed2db74c9995992f4a98d5d063f51b0043e9",
    ),
    "src/engine/ai_engine_openai.py": (
        "3ef25fb633af75b36f72c2721291c4425dc873bb50255d200928c05fc20598a3",
        "c6b60363676f804ecab1ef2dbaba119bb090a181fe6e4ddf7136fcda0716a920",
    ),
    "src/engine/scalping/ai_decision_trace.py": (
        "f1a072179283cba22d64cba81b435dee1becb4ed875666ec1911945ff5e7517a",
        "c79ada77b9e4566df6c55a58b5cfe039380ac452b814aab3e716276f9b547c53",
    ),
    "src/bot_main.py": (
        "09fa411c3a9fbbca5cec46b968a7ff6ac2fdac266acf02402f4684a1e3104eb8",
        "e682ed91042d98bd21f3a3f2d8537fcc05eae399f389935f3fee20789343a06b",
    ),
}
REVIEWED_SUBMISSION_MONITOR_PROFILE = {
    **REVIEWED_P5_RECHECK_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_SUBMISSION_MONITOR_TRANSITION.items()},
}

# One source registration shared by the native handoff and this independent
# preparation reader. The offline workload is report-only and is deliberately
# excluded from the startup-required profile below.
REVIEWED_STOP_INCIDENT_TRANSITION = {
    "src/engine/automation/main_stop_runtime_workload.py": (
        "4835d5168d8a87a1844f144d76da3a03a3023b8ff5f6a1c2974e14d81be00817",
        "f9ebd03ad6b55ba971b679e710db05d1a7eae21196efe5c16cce827d3aa85e28",
    ),
    "src/engine/scalping/main_stop_quantity_source.py": (
        "161ad67649004fdef873b238a5face5923079d3ee91cb0d85bc4e0cca52e2f26",
        "9885041f7c83ba5c91b632f23e371d9e32b59af71ce246cfb4cca4c7a97793bf",
    ),
    "src/engine/scalping/main_stop_runtime_source.py": (
        "6e69839e7bda72f6b7d2791c91d0c364ca51feb03bb4412176fdec364d17e1c0",
        "9ffc9b4032f41f94e23a60e8f5f2d480b60ce1e53f3b462b9a037a8e16231508",
    ),
    "src/engine/sniper_state_handlers.py": (
        "82fa6b5c762e99e644e889ca343cb565caf0f52d62da0b0ca728fca8309414f6",
        "965812f61a97ce966771c29a0430f780536907a568d25ea63de1bd1de1477efd",
    ),
    "src/engine/sniper_trade_review_report.py": (
        "a13e1b73e76120a4ceb87a5c65b2a714bdc6845d9b38c81f3d1d37ce7be12b08",
        "caf9f74641080abe610ba62ffef04fb000529de423d56d4f208c296d33078459",
    ),
    "src/engine/sniper_trade_utils.py": (
        "d0570ff0e17a7f164c63fd187eca593bfc92516e40c0e0c58eb019828c7ffbda",
        "ce50a80ee5c0dcd6ba81a37158ffbc75f023a1188e31968422b7cdd7bdd3c14e",
    ),
}
_STOP_INCIDENT_OFFLINE_OWNER = "src/engine/automation/main_stop_runtime_workload.py"
REVIEWED_STOP_INCIDENT_PROFILE = {
    **REVIEWED_SUBMISSION_MONITOR_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_STOP_INCIDENT_TRANSITION.items()
       if name != _STOP_INCIDENT_OFFLINE_OWNER},
}

# Preserve the complete issued stop/monitor generation while admitting only
# the reviewed mixed-registry common-support publisher successor.
REVIEWED_COMMON_SUPPORT_TRANSITION = {
    "src/engine/scalping/reversal_auxiliary_intraday.py": (
        "02ec66f262e98123de56165890cb11c1a0464d44e4cff227845637be6e130ff9",
        "4269e0bbb543fbf042f364f4f57bc9bf3b4c607f46a6431ba00241920877ed1f",
    ),
}
REVIEWED_COMMON_SUPPORT_PROFILE = {
    **REVIEWED_STOP_INCIDENT_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_COMMON_SUPPORT_TRANSITION.items()},
}

# Complete common-support generation with the reviewed interrupted custody
# transition owner. Historical roots retain their own original full profile.
REVIEWED_INTERRUPTED_CUSTODY_TRANSITION = {
    "src/engine/automation/ordered_intraday_deploy.py": (
        "223c7f3346eb847fa6e1ea17895429a1d680fe5e4e56fd6b7c17d2249e6fd5dc",
        "914d5a48c783b3afdd6537a796cd5e8ca120aea03ea60c705cffff76f3148374",
    )
}
REVIEWED_INTERRUPTED_CUSTODY_PROFILE = {
    **REVIEWED_COMMON_SUPPORT_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_INTERRUPTED_CUSTODY_TRANSITION.items()},
}
# The P5 consumer union changes only the selected validation orchestrator.
# The complete independent preparation profile remains mandatory for all
# overlapping callers; a changed P5 byte is a generation, not a blanket
# compatibility exception for the rest of the release.
REVIEWED_P5_CONSUMER_UNION_TRANSITION = {
    "src/engine/automation/main_startup_validation.py": (
        "3874cb131182242f74184dd65ea25629c7ecfb8eeebdecf25eb51fb5e12f5dde",
        "44cf695431f70748bdef561d3476c95c1a30c0672b3a32dcecd38f95ece6b168",
    )
}
REVIEWED_P5_CONSUMER_UNION_PROFILE = {
    **REVIEWED_INTERRUPTED_CUSTODY_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_P5_CONSUMER_UNION_TRANSITION.items()},
}
# One change-scoped registration for both independent preparation and ordered
# handoff.  Include transitive archive readers even where the previous profile
# did not enumerate them. Issued predecessor profiles remain unchanged.
REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION = {
    "src/engine/automation/ordered_intraday_deploy.py": ("914d5a48c783b3afdd6537a796cd5e8ca120aea03ea60c705cffff76f3148374", "310acd9437e826f8e105d1f74bbe7b6d1ba3dea9197798e36edc11e6b342ec1b"),
    "src/engine/monitoring/submission_bottleneck_monitor.py": ("f3a09a8c7890b3946a3c28fa3465056ae41dfd0bd2e149be77e7ae3bdf33eaae", "858db84b920533dc4fa39430a5ea70468dae92c0552924582624e20154b2f240"),
    "src/engine/buy_funnel_sentinel.py": ("680ba5cce5ecff77d573457141e604051fb6bdc2216f9f649353693e4ccaf510", "117360cda23c8afab8a0ed4a606fd74d879b312ed2a8a26e0cdaf82ae7cda014"),
    "src/engine/holding_exit_sentinel.py": ("e2bb53a00436e5574ec9117d2514deba798baf675d500b44e7a31eafa2d4dd93", "0c618b5c5852e294765a3c42aa1f82adb379e7b6994384b2f8d634dacc42dab1"),
    "src/engine/monitoring/intraday_entry_flow_report.py": ("546a76bf36773b055fab4e13939ea7701af1890fd01141dd5851a9bb8ba05a30", "f0f053a55691529517a43b5ae744633296c74dfec34981939089831805d9829a"),
    "src/engine/monitoring/sentinel_compact_store.py": ("70de438ae92ed50e3ab63666f3f49aee906f7394333acdea48a0ac8234d64320", "a2bcf7fb53929a9f40f3acd567ec3f0d40a285a8c5e8d5d6ede187bd63c36383"),
    "src/engine/monitoring/sentinel_source_window.py": ("012d290ace2bd5e6cd16a4e0f8564f8082e03dc55851959a67a0418f010c5737", "14d3cf303f8c3aa9b36c1b72d9bd03b37fa1e2382d6613cb6e4a8d1258f0a174"),
    "src/engine/monitoring/sentinel_summary_contract.py": ("44a81aea08b43a5be7a1b33aea70a231fd8b4e445d3cee6e0f8b930cb1fe41fd", "73160cbc1239ce787e23e53cc797dc88b8a3717114ace5376ffcd0b307b81beb"),
    "src/engine/sentinel_event_cache.py": ("2a9adf8c6936718163c9a57af112d7f0fe5edefec65248e58a76a9487caef70b", "92c4eacc2bfa5be319ea0c72bedba22a079afa9fd296b9eb3e553366de6cdc69"),
}
REVIEWED_STORAGE_INTEGRATION_PRIOR_PROFILE = {
    **REVIEWED_P5_CONSUMER_UNION_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION.items()},
}
REVIEWED_STORAGE_INTEGRATION_TRANSITION = {
    **REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION,
    "src/engine/automation/ordered_intraday_deploy.py": (
        "310acd9437e826f8e105d1f74bbe7b6d1ba3dea9197798e36edc11e6b342ec1b",
        "7b2be5f79240ddcaded0a9627d08be13d907f8babc9481275dc3d08f77eccce5"),
    "src/engine/scalping/reversal_code_handoff.py": (
        "21760885de2a28bd7d5c5a021af3eb88c0fd0f31c890855b94be0e81f8b7b93c",
        "df41ee6d93f1842bcd689940c8920d58aec021530e97fff252e4ceb9bb794ff3"),
}
REVIEWED_STORAGE_INTEGRATION_PROFILE = {
    **REVIEWED_STORAGE_INTEGRATION_PRIOR_PROFILE,
    **{name: pair[1] for name, pair in REVIEWED_STORAGE_INTEGRATION_TRANSITION.items()},
}


def reviewed_predecessor_origins(endpoint, edges):
    """Follow only connected, explicitly registered predecessor edges."""
    origins = {endpoint}
    while True:
        predecessors = {old for old, current in edges if current in origins}
        if predecessors <= origins:
            return frozenset(origins)
        origins.update(predecessors)


def reviewed_storage_origins(relative, *, prior=False):
    """Compose only registered predecessor edges for this exact successor."""
    transition = (REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION if prior else
                  REVIEWED_STORAGE_INTEGRATION_TRANSITION).get(relative)
    if transition is None:
        return frozenset()
    edges = set(REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    for registry in (REVIEWED_PREPARATION_SOURCES,
                     REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION,
                     REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION,
                     REVIEWED_SUBMISSION_MONITOR_TRANSITION,
                     REVIEWED_COMMON_SUPPORT_TRANSITION,
                     REVIEWED_INTERRUPTED_CUSTODY_TRANSITION,
                     REVIEWED_P5_CONSUMER_UNION_TRANSITION):
        if relative in registry:
            edges.add(registry[relative])
    return reviewed_predecessor_origins(transition[0], edges)


REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE = {
    **REVIEWED_COMMON_SUPPORT_PROFILE,
    "src/engine/automation/ordered_intraday_deploy.py":
        "d048ed30b231a1076abaaaa79d85f4b655044307c201760ac067cb3e747375b6",
}


def reviewed_preparation_pair(relative, old, current, *, root=None):
    # A predecessor comparison uses its selected origin; candidate comparisons
    # keep the execution root. A reviewed pair never changes that phase.
    comparison_root = ROOT if root is None else Path(root)
    if not comparison_root.is_absolute() or comparison_root.resolve() != comparison_root:
        return False
    storage_latest = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for name, pair in REVIEWED_STORAGE_INTEGRATION_TRANSITION.items()
        if pair[1] != REVIEWED_STORAGE_INTEGRATION_PRIOR_PROFILE.get(name)
    )
    storage_prior = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for name, pair in REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION.items()
    )
    storage_generation = storage_latest or storage_prior
    storage_profile = (REVIEWED_STORAGE_INTEGRATION_PROFILE if storage_latest
                       else REVIEWED_STORAGE_INTEGRATION_PRIOR_PROFILE)
    if storage_generation:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in storage_profile.items()
        ):
            return False
        transition = (REVIEWED_STORAGE_INTEGRATION_TRANSITION if storage_latest
                      else REVIEWED_STORAGE_INTEGRATION_PRIOR_TRANSITION).get(relative)
        if transition is not None:
            return current == transition[1] and old in reviewed_storage_origins(relative, prior=not storage_latest)
    union_generation = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for name, pair in REVIEWED_P5_CONSUMER_UNION_TRANSITION.items()
    )
    if union_generation:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in (storage_profile if storage_generation
                                   else REVIEWED_P5_CONSUMER_UNION_PROFILE).items()
        ):
            return False
        transition = REVIEWED_P5_CONSUMER_UNION_TRANSITION.get(relative)
        if transition is not None:
            return current == transition[1] and old == transition[0]
    interrupted_profile = (storage_profile if storage_generation
                           else REVIEWED_P5_CONSUMER_UNION_PROFILE if union_generation
                           else REVIEWED_INTERRUPTED_CUSTODY_PROFILE)
    prior_owner = "src/engine/automation/ordered_intraday_deploy.py"
    interrupted_prior = (
        (comparison_root / prior_owner).is_file()
        and not (comparison_root / prior_owner).is_symlink()
        and _sha(comparison_root / prior_owner) == REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE[prior_owner]
    )
    interrupted_generation = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for name, pair in REVIEWED_INTERRUPTED_CUSTODY_TRANSITION.items()
    )
    if interrupted_prior:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE.items()
        ):
            return False
        if relative == prior_owner:
            return current == REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE[prior_owner] and old in {
                REVIEWED_INTERRUPTED_CUSTODY_TRANSITION[prior_owner][0], current
            }
    if interrupted_generation:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in interrupted_profile.items()
        ):
            return False
        if relative in REVIEWED_INTERRUPTED_CUSTODY_TRANSITION:
            previous, expected = REVIEWED_INTERRUPTED_CUSTODY_TRANSITION[relative]
            return current == expected and old in {
                previous, "d048ed30b231a1076abaaaa79d85f4b655044307c201760ac067cb3e747375b6"
            }
    support_generation = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for name, pair in REVIEWED_COMMON_SUPPORT_TRANSITION.items()
    )
    if support_generation:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in (storage_profile if storage_generation
                                   else interrupted_profile if interrupted_generation
                                   else REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE if interrupted_prior
                                   else REVIEWED_COMMON_SUPPORT_PROFILE).items()
        ):
            return False
        if relative in REVIEWED_COMMON_SUPPORT_TRANSITION:
            return (old, current) == REVIEWED_COMMON_SUPPORT_TRANSITION[relative]
    stop_generation = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for name, pair in REVIEWED_STOP_INCIDENT_TRANSITION.items()
        if name != _STOP_INCIDENT_OFFLINE_OWNER
    )
    if stop_generation:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in (
                storage_profile if storage_generation
                else interrupted_profile if interrupted_generation
                else REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE if interrupted_prior
                else REVIEWED_COMMON_SUPPORT_PROFILE if support_generation
                else REVIEWED_STOP_INCIDENT_PROFILE
            ).items()
        ):
            return False
        transition = REVIEWED_STOP_INCIDENT_TRANSITION.get(relative)
        if transition is not None and relative != _STOP_INCIDENT_OFFLINE_OWNER:
            return current == transition[1] and old == transition[0]
    if (relative == _suffix_owner and current == _suffix_current
            and any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
                    or _sha(comparison_root / name) != expected
                    for name, expected in REVIEWED_SCHEDULED_SUFFIX_DEPENDENCIES.items())):
        return False
    monitor_generation = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == pair[1]
        for transitions in (REVIEWED_SUBMISSION_MONITOR_TRANSITION,
                            REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION)
        for name, pair in transitions.items()
    )
    monitor_profile = None
    if monitor_generation:
        # Authenticate a complete issued generation before interpreting a pair.
        # The current reader may compare a genuine earlier selected generation;
        # an overlapping source trigger cannot turn it into the latest profile.
        for profile in (REVIEWED_STORAGE_INTEGRATION_PROFILE, REVIEWED_P5_CONSUMER_UNION_PROFILE, REVIEWED_INTERRUPTED_CUSTODY_PROFILE, REVIEWED_INTERRUPTED_CUSTODY_PRIOR_PROFILE, REVIEWED_COMMON_SUPPORT_PROFILE,
                        REVIEWED_STOP_INCIDENT_PROFILE,
                        REVIEWED_SUBMISSION_MONITOR_PROFILE,
                        REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE):
            if all(not (comparison_root / name).is_symlink()
                   and (comparison_root / name).is_file()
                   and _sha(comparison_root / name) == expected
                   for name, expected in profile.items()):
                monitor_profile = profile
                break
        if monitor_profile is None:
            return False
        endpoint = comparison_root / relative
        if (
            (relative not in REVIEWED_PREPARATION_SOURCES
             and relative not in REVIEWED_PREPARATION_HISTORY
             and relative not in REVIEWED_SUBMISSION_MONITOR_TRANSITION)
            or endpoint.is_symlink()
            or not endpoint.is_file()
            or _sha(endpoint) != current
        ):
            return False
        transitions = [values[relative] for values in (
            REVIEWED_SUBMISSION_MONITOR_TRANSITION,
            REVIEWED_SUBMISSION_MONITOR_PRIOR_TRANSITION,
        ) if relative in values and values[relative][1] == current]
        if transitions:
            origins = {pair[0] for pair in transitions}
            if (monitor_profile is not REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE
                    and relative in REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE):
                origins.add(REVIEWED_SUBMISSION_MONITOR_PRIOR_PROFILE[relative])
            from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
            origin = reviewed_formatting_predecessor(relative, old)
            return any(
                old == predecessor or origin == reviewed_formatting_predecessor(relative, predecessor)
                or (origin, reviewed_formatting_predecessor(relative, predecessor))
                in REVIEWED_PREPARATION_HISTORY.get(relative, ())
                for predecessor in origins
            )
        # Other members retain their original endpoint and reviewed-formatting
        # predicates in the shared cron-profile branch below.
    # The report/recovery owner remains outside the startup-required profile.
    # Its new comparison endpoint requires its actual native calendar reader.
    p5_path = comparison_root / _P5_RECHECK_OWNER
    p5_recheck = (p5_path.is_file() and not p5_path.is_symlink()
                  and _sha(p5_path) == _P5_RECHECK_CURRENT)
    if p5_recheck:
        if (relative not in REVIEWED_PREPARATION_SOURCES
                and relative not in REVIEWED_PREPARATION_HISTORY
                or any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
                       or _sha(comparison_root / name) != expected
                       for name, expected in (
                           monitor_profile if monitor_generation
                           else REVIEWED_P5_RECHECK_PROFILE
                       ).items())):
            return False
        endpoint = comparison_root / relative
        if endpoint.is_symlink() or not endpoint.is_file() or _sha(endpoint) != current:
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    cron_phase_binding = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_CRON_PHASE_BINDING_CHANGED.items()
        if expected != REVIEWED_PREFIX_COST_HANDOFF_PROFILE.get(name)
    )
    if cron_phase_binding:
        if (relative not in REVIEWED_PREPARATION_SOURCES
                and relative not in REVIEWED_PREPARATION_HISTORY):
            return False
        endpoint = comparison_root / relative
        if (endpoint.is_symlink() or not endpoint.is_file()
                or _sha(endpoint) != current):
            return False
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in (
                   monitor_profile if monitor_generation
                   else REVIEWED_CRON_PHASE_BINDING_PROFILE
               ).items()):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    if all((comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
           and _sha(comparison_root / name) == expected
           for name, expected in REVIEWED_PREFIX_COST_HANDOFF_PROFILE.items()):
        return (current == REVIEWED_PREFIX_COST_HANDOFF_PROFILE.get(relative)
                and (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                     or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())))
    prefix_cost_handoff = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_PREFIX_COST_HANDOFF_CHANGED.items()
        if expected != REVIEWED_PREFIX_COST_CONTEXT_PROFILE.get(name)
    )
    if prefix_cost_handoff:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_PREFIX_COST_HANDOFF_PROFILE.items()):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    # Resolve complete historical generations before ambiguous partial triggers.
    # A historical root authenticates only its own physical consumer endpoint.
    for profile in (
        REVIEWED_PREFIX_COST_CONTEXT_PROFILE,
        REVIEWED_CAUSAL_ITEM_PROFILE,
        REVIEWED_CANCEL_STORAGE_REVIEW_PROFILE,
        REVIEWED_CANCEL_STATE_STORAGE_PROFILE,
        REVIEWED_POSTCLOSE_SELECTED_STOP_PROFILE,
        REVIEWED_STARTUP_SUBMISSION_SOURCE_PROFILE,
        REVIEWED_ACTIVE_REPORT_CLOSURE_PROFILE,
        REVIEWED_DATED_REPORT_PARENT_PROFILE,
        REVIEWED_LIFETIME_SOURCE_PHASE_PROFILE,
        REVIEWED_STARTUP_SCOPED_AUX_PROFILE,
        REVIEWED_STARTUP_SCOPED_PROFILE,
    ):
        if all((comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
               and _sha(comparison_root / name) == expected for name, expected in profile.items()):
            return (current == profile.get(relative)
                    and (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                         or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())))
    causal_item = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_CAUSAL_ITEM_CHANGED.items()
        if expected != REVIEWED_CANCEL_STORAGE_REVIEW_PROFILE.get(name)
    )
    if causal_item:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_CAUSAL_ITEM_PROFILE.items()):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    prefix_cost_context = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_PREFIX_COST_CONTEXT_CHANGED.items()
        if expected != REVIEWED_CAUSAL_ITEM_PROFILE.get(name)
    )
    if prefix_cost_context:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_PREFIX_COST_CONTEXT_PROFILE.items()):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_CANCEL_STORAGE_REVIEW_CHANGED.items()
        if expected != REVIEWED_CANCEL_STATE_STORAGE_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_CANCEL_STORAGE_REVIEW_PROFILE.items()):
            return False
        # Exact reviewed historical endpoints remain valid after complete current-generation checks.
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_CANCEL_STATE_STORAGE_CHANGED.items()
        if expected != REVIEWED_POSTCLOSE_SELECTED_STOP_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_CANCEL_STATE_STORAGE_PROFILE.items()):
            return False
        # Retain exact reviewed predecessor endpoint pairs after complete profile verification.
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_POSTCLOSE_SELECTED_STOP_CHANGED.items()
        if expected != REVIEWED_STARTUP_SUBMISSION_SOURCE_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_POSTCLOSE_SELECTED_STOP_PROFILE.items()):
            return False
        # Preserve exact reviewed historical endpoint authority after full profile checks.
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_STARTUP_SUBMISSION_SOURCE_CHANGED.items()
        if expected != REVIEWED_ACTIVE_REPORT_CLOSURE_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_STARTUP_SUBMISSION_SOURCE_PROFILE.items()):
            return False
        # Preserve reviewed historical endpoints after complete generation validation.
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_ACTIVE_REPORT_CLOSURE_CHANGED.items()
        if expected != REVIEWED_DATED_REPORT_PARENT_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_ACTIVE_REPORT_CLOSURE_PROFILE.items()):
            return False
        # This helper reviews an exact source pair, including an immutable
        # historical reader. Its caller separately authenticates each endpoint.
        # A complete current profile must not erase already reviewed history
        # or unchanged consumers absent from the changed-member inventory.
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_DATED_REPORT_PARENT_CHANGED.items()
        if expected != REVIEWED_LIFETIME_SOURCE_PHASE_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_DATED_REPORT_PARENT_PROFILE.items()):
            return False
        if current != REVIEWED_DATED_REPORT_PARENT_PROFILE.get(relative):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_LIFETIME_SOURCE_PHASE_CHANGED.items()
        if expected != REVIEWED_STARTUP_SCOPED_AUX_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_LIFETIME_SOURCE_PHASE_PROFILE.items()):
            return False
        if current != REVIEWED_LIFETIME_SOURCE_PHASE_PROFILE.get(relative):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    aftermarket = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_STARTUP_SCOPED_AUX_CHANGED.items()
        if expected != REVIEWED_STARTUP_SCOPED_PROFILE.get(name)
    )
    if aftermarket:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_STARTUP_SCOPED_AUX_PROFILE.items()):
            return False
        if current != REVIEWED_STARTUP_SCOPED_AUX_PROFILE.get(relative):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    integrated = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_STARTUP_SCOPED_CHANGED.items()
        if expected not in {REVIEWED_SCOPED_ENTRY_PROFILE.get(name),
                            REVIEWED_STARTUP_STORAGE_PROFILE.get(name)}
    ) or (
        any((comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
            and _sha(comparison_root / name) == expected
            for name, expected in REVIEWED_STARTUP_STORAGE_CHANGED.items()
            if expected != REVIEWED_PROBE_AVG_PROFILE.get(name))
        and any((comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
                and _sha(comparison_root / name) == expected
                for name, expected in REVIEWED_SCOPED_ENTRY_CHANGED.items()
                if expected != REVIEWED_PROBE_AVG_PROFILE.get(name))
    )
    if integrated:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_STARTUP_SCOPED_PROFILE.items()):
            return False
        if current != REVIEWED_STARTUP_SCOPED_PROFILE.get(relative):
            return False
        if (REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current)
                or (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ())):
            return True
        from src.engine.automation.intraday_release_handoff import reviewed_formatting_predecessor
        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        return (predecessor != current and origin == predecessor
                or REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor)
                or (origin, predecessor) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    scoped_entry = any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_SCOPED_ENTRY_CHANGED.items()
    )
    if scoped_entry:
        if any(
            (comparison_root / name).is_symlink()
            or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in REVIEWED_SCOPED_ENTRY_PROFILE.items()
        ):
            return False
        if (
            relative in REVIEWED_SCOPED_ENTRY_PROFILE
            and current != REVIEWED_SCOPED_ENTRY_PROFILE[relative]
        ):
            return False
        if REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current) or (
            old,
            current,
        ) in REVIEWED_PREPARATION_HISTORY.get(relative, ()):
            return True
        from src.engine.automation.intraday_release_handoff import (
            reviewed_formatting_predecessor,
        )

        predecessor = reviewed_formatting_predecessor(relative, current)
        origin = reviewed_formatting_predecessor(relative, old)
        if predecessor != current and origin == predecessor:
            return True
        return REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor) or (
            origin,
            predecessor,
        ) in REVIEWED_PREPARATION_HISTORY.get(relative, ())
    startup_storage = any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_STARTUP_STORAGE_CHANGED.items()
        if expected != REVIEWED_PROBE_AVG_PROFILE.get(name)
    )
    if startup_storage:
        if any((comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
               or _sha(comparison_root / name) != expected
               for name, expected in REVIEWED_STARTUP_STORAGE_PROFILE.items()):
            return False
        return (current == REVIEWED_STARTUP_STORAGE_PROFILE.get(relative)
                and (old, current) in REVIEWED_PREPARATION_HISTORY.get(relative, ()))
    probe_avg = current == REVIEWED_PROBE_AVG_PROFILE.get(relative) and any(
        (comparison_root / name).is_file()
        and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_PROBE_AVG_CHANGED.items()
    )
    if probe_avg and any(
        (comparison_root / name).is_symlink()
        or not (comparison_root / name).is_file()
        or _sha(comparison_root / name) != expected
        for name, expected in REVIEWED_PROBE_AVG_PROFILE.items()
    ):
        return False

    timeout_terminal = (
        not probe_avg
        and current == REVIEWED_TIMEOUT_TERMINAL_PROFILE.get(relative)
        and any(
            (comparison_root / name).is_file()
            and not (comparison_root / name).is_symlink()
            and _sha(comparison_root / name) == expected
            for name, expected in REVIEWED_TIMEOUT_CHANGED.items()
        )
    )
    if (
        relative in REVIEWED_TIMEOUT_CHANGED
        and current == REVIEWED_TIMEOUT_CHANGED[relative]
        and not (timeout_terminal or probe_avg)
    ):
        return False
    if timeout_terminal and any(
        (comparison_root / name).is_symlink()
        or not (comparison_root / name).is_file()
        or _sha(comparison_root / name) != expected
        for name, expected in REVIEWED_TIMEOUT_TERMINAL_PROFILE.items()
    ):
        return False
    holding_history = current == REVIEWED_HOLDING_HISTORY_PROFILE.get(relative) and any(
        (comparison_root / name).is_file() and not (comparison_root / name).is_symlink()
        and _sha(comparison_root / name) == expected
        for name, expected in REVIEWED_HOLDING_HISTORY_SOURCES.items()
    )
    if probe_avg or timeout_terminal:
        pass
    elif holding_history:
        if any(
            (comparison_root / name).is_symlink() or not (comparison_root / name).is_file()
            or _sha(comparison_root / name) != expected
            for name, expected in REVIEWED_HOLDING_HISTORY_PROFILE.items()
        ):
            return False

    elif current == REVIEWED_PREOPEN_VALIDATION_PROFILE.get(relative) and (
        current != REVIEWED_POSTCLOSE_INTEGRATED_SOURCES.get(relative)
        or any(
            (comparison_root / name).is_file()
            and not (comparison_root / name).is_symlink()
            and _sha(comparison_root / name) == expected
            for name, expected in REVIEWED_PREOPEN_VALIDATION_SOURCES.items()
            if expected != REVIEWED_POSTCLOSE_INTEGRATED_SOURCES.get(name)
        )
    ):
        for name, expected in REVIEWED_PREOPEN_VALIDATION_PROFILE.items():
            path = comparison_root / name
            if path.is_symlink() or not path.is_file() or _sha(path) != expected:
                return False
    elif current == REVIEWED_POSTCLOSE_INTEGRATED_SOURCES.get(relative) and (
        current != REVIEWED_HELD_SELL_SOURCES.get(relative)
        or any(
            (comparison_root / name).is_file()
            and not (comparison_root / name).is_symlink()
            and _sha(comparison_root / name) == expected
            for name, expected in REVIEWED_POSTCLOSE_INTEGRATED_SOURCES.items()
            if expected != REVIEWED_HELD_SELL_SOURCES.get(name)
        )
    ):
        for name, expected in REVIEWED_POSTCLOSE_INTEGRATED_SOURCES.items():
            path = comparison_root / name
            if path.is_symlink() or not path.is_file() or _sha(path) != expected:
                return False
    if not (holding_history or timeout_terminal or probe_avg) and current == REVIEWED_HELD_SELL_SOURCES.get(relative):
        for name, expected in REVIEWED_HELD_SELL_SOURCES.items():
            path = comparison_root / name
            if path.is_symlink() or not path.is_file() or _sha(path) != expected:
                return False
    # An already reviewed physical pair keeps its original authority; a
    # formatting projection must not replace either endpoint before this check.
    if REVIEWED_PREPARATION_SOURCES.get(relative) == (old, current) or (
        old,
        current,
    ) in REVIEWED_PREPARATION_HISTORY.get(relative, ()):
        return True
    from src.engine.automation.intraday_release_handoff import (
        reviewed_formatting_predecessor,
    )

    predecessor = reviewed_formatting_predecessor(relative, current)
    origin = reviewed_formatting_predecessor(relative, old)
    if predecessor != current and origin == predecessor:
        return True
    return REVIEWED_PREPARATION_SOURCES.get(relative) == (origin, predecessor) or (
        origin,
        predecessor,
    ) in REVIEWED_PREPARATION_HISTORY.get(relative, ())


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _hex(value, length=64):
    return (
        isinstance(value, str)
        and re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is not None
    )


def _read(path, *, maximum=_MAX_JSON):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError("startup_code_context_source_not_regular_bounded")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("startup_code_context_source_unbounded")
    return raw


def _json(path):
    value = json.loads(_read(path))
    if not isinstance(value, dict):
        raise ValueError("startup_code_context_object_required")
    return value


def _sha(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("startup_code_context_source_not_regular")

    def identity(value):
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    with path.open("rb") as stream:
        before = identity(os.fstat(stream.fileno()))
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
        if (
            before != identity(os.fstat(stream.fileno()))
            or path.is_symlink()
            or before != identity(path.stat())
        ):
            raise ValueError("startup_code_context_source_changed_during_read")
    return digest.hexdigest()


def _check_sources(sources, *, absent_allowed=False):
    if not isinstance(sources, dict) or not sources:
        raise ValueError("startup_code_context_sources_required")
    for name, expected in sources.items():
        if not isinstance(name, str) or not Path(name).is_absolute():
            raise ValueError("startup_code_context_source_path_invalid")
        if expected is None and absent_allowed:
            if Path(name).exists() or Path(name).is_symlink():
                raise ValueError("startup_code_context_absent_source_changed")
        elif not _hex(expected) or _sha(name) != expected:
            raise ValueError("startup_code_context_source_changed")


def _bound_source(sources, path):
    path = Path(path)
    values = {
        sources[name]
        for name in (str(path), str(path.resolve(strict=True)))
        if name in sources
    }
    if len(values) != 1 or _sha(path) not in values:
        raise ValueError("startup_code_context_source_not_bound")


def _git_head(root):
    """Read Git identity without spawning Git under seccomp."""
    root = Path(root)
    metadata = root / ".git"
    if metadata.is_file():
        line = _read(metadata, maximum=4096).decode().strip()
        if not line.startswith("gitdir: "):
            raise ValueError("startup_code_context_gitdir_invalid")
        directory = (root / line[8:]).resolve(strict=True)
    elif metadata.is_dir() and not metadata.is_symlink():
        directory = metadata
    else:
        raise ValueError("startup_code_context_gitdir_missing")
    head = _read(directory / "HEAD", maximum=4096).decode().strip()
    if _hex(head, 40):
        return head
    if not head.startswith("ref: "):
        raise ValueError("startup_code_context_git_head_invalid")
    ref = head[5:]
    if (
        not ref.startswith("refs/")
        or ".." in Path(ref).parts
        or not re.fullmatch("[A-Za-z0-9._/-]+", ref)
    ):
        raise ValueError("startup_code_context_git_ref_invalid")
    common = directory
    if (directory / "commondir").is_file():
        common = (
            directory / _read(directory / "commondir", maximum=4096).decode().strip()
        ).resolve(strict=True)
    for parent in (directory, common):
        if (parent / ref).is_file():
            commit = _read(parent / ref, maximum=4096).decode().strip()
            if _hex(commit, 40):
                return commit
            raise ValueError("startup_code_context_git_ref_invalid")
    packed = common / "packed-refs"
    if packed.is_file():
        for line in _read(packed).decode().splitlines():
            if line.startswith(("#", "^")):
                continue
            fields = line.split()
            if len(fields) == 2 and fields[1] == ref and _hex(fields[0], 40):
                return fields[0]
    raise ValueError("startup_code_context_git_ref_missing")


def _contract(root, paths, sources):
    if not isinstance(paths, dict) or not paths:
        raise ValueError("startup_code_context_contract_paths_invalid")
    values = {}
    for key, relative in paths.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
        ):
            raise ValueError("startup_code_context_contract_path_invalid")
        path = Path(root) / relative
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError("startup_code_context_contract_path_escape")
        _bound_source(sources, path)
        values[key] = _sha(path)
    return _digest(values)


def _origin(proof, request):
    origin = proof.get("origin")
    if not isinstance(origin, dict):
        raise ValueError("startup_code_context_origin_required")
    sources = origin.get("sources")
    _check_sources(sources)
    if any(proof["source_hashes"].get(name) != sha for name, sha in sources.items()):
        raise ValueError("startup_code_context_origin_not_bound")
    selected = Path(origin.get("selected_release_root") or "")
    commit = origin.get("selected_release_commit")
    if (
        not selected.is_absolute()
        or str(selected.resolve(strict=True)) != str(selected)
        or not _hex(commit, 40)
        or _git_head(selected) != commit
        or not _hex(origin.get("origin_commit"), 40)
        or origin.get("original_code_sha256") != proof["original_code_sha256"]
    ):
        raise ValueError("startup_code_context_origin_identity_invalid")
    selector = Path(request["data_root"]) / "runtime/runtime_release_selection.json"
    _bound_source(sources, selector)
    selection = _json(selector)
    if (
        selection.get("schema") != "runtime_release_selection_v1"
        or selection.get("release_root") != str(selected)
        or selection.get("git_commit") != commit
    ):
        raise ValueError("startup_code_context_selected_identity_changed")
    if origin.get("basis") == "execution_exact_code_contract":
        if (
            origin["origin_commit"] != request["execution_release_commit"]
            or proof["runtime_code_contract_sha256"] != proof["original_code_sha256"]
            or proof.get("changed_consumer_paths") != []
        ):
            raise ValueError("startup_code_context_execution_exact_origin_invalid")
        return
    selected_paths = origin.get("selected_paths", proof["paths"])
    if (
        not isinstance(selected_paths, dict)
        or not selected_paths
        or any(proof["paths"].get(key) != name for key, name in selected_paths.items())
    ):
        raise ValueError("startup_code_context_selected_inventory_invalid")
    selected_code = _contract(selected, selected_paths, sources)
    if selected_code != origin.get("selected_runtime_code_sha256"):
        raise ValueError("startup_code_context_selected_contract_changed")
    basis = origin.get("basis")
    if basis == "selected_exact_code_contract":
        if (
            selected_code != proof["original_code_sha256"]
            or origin["origin_commit"] != commit
        ):
            raise ValueError("startup_code_context_exact_origin_invalid")
    elif basis == "verified_selected_prepared_code_handoff":
        path = Path(origin.get("code_handoff_receipt_path") or "")
        _bound_source(sources, path)
        receipt = _json(path)
        if (
            _sha(path) != origin.get("code_handoff_receipt_sha256")
            or receipt.get("schema") != "prepared_policy_code_handoff_v1"
            or receipt.get("authority")
            != "APPROVED_PREPARED_POLICY_PRESERVING_CODE_HANDOFF"
            or receipt.get("receipt_sha256")
            != _digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
            or receipt.get("family") != proof["family"]
            or receipt.get("target_date") != proof["target_date"]
            or receipt.get("policy_sha256") != proof["policy_sha256"]
            or receipt.get("original_code_sha256") != proof["original_code_sha256"]
            or receipt.get("runtime_code_sha256") != selected_code
            or receipt.get("paths") != selected_paths
            or receipt.get("release_root") != str(selected)
            or receipt.get("release_commit") != commit
            or receipt.get("origin_commit") != origin["origin_commit"]
            or receipt.get("policy_effect") != "unchanged"
            or any(
                receipt.get(k) is not False
                for k in (
                    "actual_pid_consumed",
                    "policy_published",
                    "provider_called",
                    "broker_called",
                )
            )
        ):
            raise ValueError("startup_code_context_native_handoff_invalid")
        native_sources = receipt.get("sources")
        _check_sources(native_sources)
        if any(sources.get(name) != sha for name, sha in native_sources.items()):
            raise ValueError("startup_code_context_native_handoff_sources_not_bound")
    elif basis in {
        "verified_selected_intraday_code_handoff",
        "verified_closed_intraday_code_handoff",
    }:
        if basis == "verified_closed_intraday_code_handoff":
            closed = origin.get("closed_observation") or {}
            if (
                closed.get("schema") != "intraday_closed_consumption_observation_v1"
                or closed.get("target_date") != proof["target_date"]
                or closed.get("release_commit") != commit
                or closed.get("pid_identity") != origin.get("pid_identity")
                or any(
                    closed.get(key) is not False
                    for key in (
                        "runtime_effect",
                        "current_observation_verified",
                        "new_pid_consumption_claimed",
                    )
                )
                or not closed.get("source_hashes")
                or any(
                    sources.get(name) != sha
                    for name, sha in closed["source_hashes"].items()
                )
            ):
                raise ValueError("startup_code_context_closed_origin_invalid")
        handoff_path = Path(origin.get("intraday_handoff_path") or "")
        consumed_path = Path(origin.get("intraday_consumed_path") or "")
        expected = (
            Path(request["data_root"])
            / "runtime/policy_bootstrap/intraday_handoff"
            / proof["target_date"]
        )
        if handoff_path != expected / (
            commit + ".json"
        ) or consumed_path != expected / (commit + ".consumed.json"):
            raise ValueError("startup_code_context_intraday_path_invalid")
        for path, key in (
            (handoff_path, "intraday_handoff_sha256"),
            (consumed_path, "intraday_consumed_sha256"),
        ):
            _bound_source(sources, path)
            if _sha(path) != origin.get(key):
                raise ValueError("startup_code_context_intraday_source_changed")
        handoff, consumed = _json(handoff_path), _json(consumed_path)
        manifest_path = (
            Path(request["data_root"])
            / "runtime/policy_bootstrap"
            / ("runtime_policy_bootstrap_" + proof["target_date"] + ".json")
        )
        _bound_source(sources, manifest_path)
        live_manifest, prepared_manifest = _json(manifest_path), request["manifest"]
        field, _ = _FAMILIES[proof["family"]]
        # Prepared and consumed manifests keep distinct generation metadata.
        # Bind both seals and the exact policy/env values this consumer loads.
        if (
            any(
                value.get("manifest_sha256")
                != _digest({k: v for k, v in value.items() if k != "manifest_sha256"})
                for value in (live_manifest, prepared_manifest)
            )
            or live_manifest.get("target_date") != proof["target_date"]
            or live_manifest.get(field) != prepared_manifest.get(field)
            or live_manifest.get("env_overrides")
            != prepared_manifest.get("env_overrides")
            or live_manifest.get("selected_release_sha")
            != prepared_manifest.get("selected_release_sha")
        ):
            raise ValueError("startup_code_context_intraday_manifest_changed")
        identity = origin.get("pid_identity") or {}
        if (
            handoff.get("schema") != "intraday_policy_preserving_release_handoff_v1"
            or handoff.get("authority")
            != "APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF"
            or handoff.get("status") != "prepared_verified"
            or handoff.get("actual_pid_consumed") is not False
            or handoff.get("policy_effect") != "unchanged"
            or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
            or consumed.get("status") != "pass"
            or consumed.get("actual_pid_consumed") is not True
            or consumed.get("handoff_sha256") != origin["intraday_handoff_sha256"]
            or consumed.get("pid_identity") != identity
            or not identity.get("start_ticks")
            or identity.get("cwd") != str(selected / "src")
            or any(
                row.get("target_date") != proof["target_date"]
                or row.get("selected_release_commit") != commit
                or row.get("release_root") != str(selected)
                for row in (handoff, consumed)
            )
            or any(
                sources.get(name) != sha
                for name, sha in handoff.get("frozen_files", {}).items()
            )
            or not isinstance(handoff.get("frozen_files"), dict)
            or not handoff["frozen_files"]
            or handoff["frozen_files"].get(str(manifest_path))
            != sources[str(manifest_path)]
            or handoff.get("manifest_sha256") != live_manifest["manifest_sha256"]
            or not isinstance(identity.get("pid"), int)
            or identity["pid"] <= 0
            or consumed.get("manifest_sha256") != live_manifest["manifest_sha256"]
            or request["manifest"].get("selected_release_sha")
            != origin["origin_commit"]
        ):
            raise ValueError("startup_code_context_intraday_handoff_invalid")
    else:
        raise ValueError("startup_code_context_origin_basis_invalid")


def _proof(proof, family, request):
    if (
        family not in _FAMILIES
        or not isinstance(proof, dict)
        or proof.get("schema") != PROOF_SCHEMA
        or proof.get("status") != "verified"
        or proof.get("target_date") != request["target_date"]
        or proof.get("family") != family
        or proof.get("execution_release_root") != request["execution_release_root"]
        or proof.get("execution_release_commit") != request["execution_release_commit"]
        or proof.get("policy_effect") != "unchanged"
        or any(
            proof.get(key, False) is not False
            for key in (
                "runtime_effect",
                "actual_pid_consumed",
                "execution_authority",
                "allowed_runtime_apply",
            )
        )
        or not all(
            _hex(proof.get(key))
            for key in (
                "policy_sha256",
                "original_code_sha256",
                "runtime_code_contract_sha256",
            )
        )
    ):
        raise ValueError("startup_code_context_handoff_invalid")
    field, key = _FAMILIES[family]
    bound = (request.get("manifest") or {}).get(field) or {}
    if (
        bound.get("target_date") != request["target_date"]
        or bound.get(key) != proof["policy_sha256"]
    ):
        raise ValueError("startup_code_context_policy_binding_invalid")
    sources = proof.get("source_hashes")
    _check_sources(sources)
    if any(request["source_hashes"].get(name) != sha for name, sha in sources.items()):
        raise ValueError("startup_code_context_handoff_sources_not_bound")
    if (
        _contract(ROOT, proof.get("paths"), sources)
        != proof["runtime_code_contract_sha256"]
    ):
        raise ValueError("startup_code_context_runtime_contract_changed")
    _origin(proof, request)


def _isolation(request):
    from src.engine.infrastructure.startup_validation_isolation import (
        assert_no_forbidden_attempts,
    )

    checked = assert_no_forbidden_attempts()
    capabilities = checked.get("capabilities") or {}
    run = Path(request.get("run_directory") or "")
    if (
        checked.get("passed") is not True
        or checked.get("forbidden_attempt_count") != 0
        or not run.is_absolute()
        or str(run.resolve(strict=True)) != str(run)
        or capabilities.get("schema") != "main_startup_validation_isolation_v1"
        or capabilities.get("filesystem_write_root") != str(run)
        or capabilities.get("process_group") != os.getpid()
        or capabilities.get("session_id") != os.getpid()
        or os.getpgrp() != os.getpid()
        or os.getsid(0) != os.getpid()
        or capabilities.get("landlock_abi", 0) < 3
        or capabilities.get("no_new_privileges") is not True
        or any(
            capabilities.get(key) is not False
            for key in (
                "network_access",
                "process_creation",
                "metadata_changes",
                "operational_file_locks",
            )
        )
    ):
        raise ValueError("startup_code_context_real_isolation_required")
    return run


def install_validation_code_context(request: dict) -> None:
    """Install once, only after the actual mandatory OS boundary is active."""
    global _CONTEXT
    from src.engine.infrastructure.startup_validation_isolation import (
        assert_no_forbidden_attempts,
    )

    assert_no_forbidden_attempts()  # Outside isolation leaves the live lookup untouched.
    if _CONTEXT is not None:
        _CONTEXT = {"valid": False}
        raise ValueError("startup_code_context_already_installed")
    _CONTEXT = {"valid": False}
    run = _isolation(request)
    request = json.loads(json.dumps(request, allow_nan=False))
    if (
        request.get("schema") != REQUEST_SCHEMA
        or not _hex(request.get("run_id"), 32)
        or run.name != request["run_id"]
        or request.get("execution_release_root") != str(ROOT)
        or not _hex(request.get("execution_release_commit"), 40)
        or _git_head(ROOT) != request["execution_release_commit"]
        or date.fromisoformat(request["target_date"]).isoformat()
        != request["target_date"]
        or request.get("request_sha256")
        != _digest({k: v for k, v in request.items() if k != "request_sha256"})
        or any(
            request.get(key, False) is not False
            for key in (
                "runtime_effect",
                "actual_pid_consumed",
                "allowed_runtime_apply",
            )
        )
    ):
        raise ValueError("startup_code_context_request_invalid")
    request_path = run / "request.json"
    if _json(request_path) != request:
        raise ValueError("startup_code_context_request_file_changed")
    sources = request.get("source_hashes")
    _check_sources(sources, absent_allowed=True)
    _bound_source(sources, Path(__file__))
    proofs = request.get("candidate_code_handoffs")
    if not isinstance(proofs, dict) or not proofs:
        raise ValueError("startup_code_context_handoffs_required")
    for family, proof in proofs.items():
        _proof(proof, family, request)
    if request.get("main_preparation_code_handoff") is not None:
        _main_proof(request["main_preparation_code_handoff"], request)
    _isolation(request)
    _CONTEXT = dict(
        valid=True,
        pid=os.getpid(),
        start_ticks=_read("/proc/self/stat", maximum=65536)
        .decode()
        .rsplit(")", 1)[1]
        .split()[19],
        request=request,
        request_path=str(request_path),
        request_sha256=_sha(request_path),
    )
    _CONTEXT["request_identity"] = _request_identity(request_path)
    if request.get("main_preparation_code_handoff") is not None:
        proof = request["main_preparation_code_handoff"]
        mounts = _sha("/proc/self/mountinfo")
        _CONTEXT["main_anchor_identities"] = {
            path: _request_identity(path) for path in proof["source_hashes"]
        }
        if _sha("/proc/self/mountinfo") != mounts:
            _CONTEXT = {"valid": False}
            raise ValueError("startup_main_mount_generation_changed")
        _CONTEXT["main_mountinfo_sha256"] = mounts
        _CONTEXT["delegation"] = dict(
            digest_reused_reads=0, digest_reused_bytes=0, auxiliary_manifests=[]
        )
        from src.engine.infrastructure.validation_digest_session import ACTIVE

        if ACTIVE.get() is not None:
            _CONTEXT = {"valid": False}
            raise ValueError("startup_code_context_digest_owner_already_active")
        ACTIVE.set(_PreparationDigests())
        # The native assembler imports this reader at call time. Install the
        # I/O adapter only in this OS-isolated child after its Main proof is
        # authenticated. Live producers and their code fingerprints stay intact.
        from src.engine.automation import main_trailing_source_store as indexed

        indexed.generation = validation_indexed_source_generation


def verify_validation_consumer_code(
    day, *, family, policy_sha, expected, paths, actual
):
    """Return None outside this context; never soften the ordinary live guard."""
    global _CONTEXT
    if _CONTEXT is None:
        return None
    context = _CONTEXT
    try:
        if context.get("valid") is not True:
            raise ValueError("startup_code_context_invalid")
        request = context["request"]
        _isolation(request)
        if (
            os.getpid() != context["pid"]
            or _git_head(ROOT) != request["execution_release_commit"]
            or _read("/proc/self/stat", maximum=65536)
            .decode()
            .rsplit(")", 1)[1]
            .split()[19]
            != context["start_ticks"]
            or _sha(context["request_path"]) != context["request_sha256"]
            or _json(context["request_path"]) != request
        ):
            raise ValueError("startup_code_context_execution_changed")
        proof = request["candidate_code_handoffs"].get(family)
        if (
            not isinstance(proof, dict)
            or day != request["target_date"]
            or policy_sha != proof["policy_sha256"]
            or expected != proof["original_code_sha256"]
            or actual != proof["runtime_code_contract_sha256"]
            or paths != proof["paths"]
        ):
            raise ValueError("startup_code_context_consumer_binding_invalid")
        _check_sources(request["source_hashes"], absent_allowed=True)
        _proof(proof, family, request)
        return dict(
            status="verified_intraday_consumer_repair",
            verification_basis=SCHEMA,
            basis=SCHEMA,
            target_date=day,
            policy_sha256=policy_sha,
            code_contract_sha256=expected,
            runtime_code_contract_sha256=actual,
            origin_commit=proof["origin"]["origin_commit"],
            policy_effect="unchanged",
            actual_pid_consumed=False,
            execution_authority=False,
        )
    except (OSError, ValueError, TypeError, KeyError):
        _CONTEXT = {"valid": False}
        raise


def _main_inventories(bundle):
    result = []
    seen = set()
    while bundle:
        family = bundle.get("continuous_reversal") or {}
        ident = bundle.get("bundle_sha256")
        if ident in seen or len(result) >= 4 or not _hex(ident):
            raise ValueError("startup_main_inventory_cycle_or_identity")
        seen.add(ident)
        expected = family.get("contract_file_sha256")
        if (
            family.get("schema")
            not in {
                "continuous_reversal_policy_v4",
                "continuous_reversal_policy_v5",
                "continuous_reversal_policy_v6",
            }
            or not isinstance(expected, dict)
            or not expected
            or not all(
                isinstance(k, str) and Path(k).name == k and _hex(v)
                for k, v in expected.items()
            )
        ):
            raise ValueError("startup_main_inventory_invalid")
        result.append(
            dict(
                bundle_sha256=ident,
                target_date=bundle["target_date"],
                family_sha256=family["family_sha256"],
                schema=family["schema"],
                expected=expected,
                origin_commit=family["release_commit"],
            )
        )
        bundle = family.get("native_parent_bundle")
    return result


def _active_entry_code_extension(data_root, day, selected, root, commit, inventories):
    """Bind a new runtime member absent from an already issued policy inventory.

    The old policy's membership stays immutable.  Only the exact reviewed
    entry-deadline addition, issued in the active-policy code handoff for this
    candidate, may supplement the isolated preparation reader's code closure.
    """
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_code_handoff as H

    if not inventories or inventories[0]["schema"] != V.SCHEMA:
        return None
    old_names = set(inventories[0]["expected"])
    # Only a full issued V6 inventory can carry the active-policy extension.
    # Historical partial fixture inventories retain their original reader.
    if not {"continuous_reversal_policy_v6.py", "reversal_code_handoff.py"}.issubset(old_names):
        return None
    current_names = {Path(m.__file__).name for m in V.contract_modules()}
    extra = current_names - old_names
    if not extra:
        return None
    if extra != {"entry_deadline.py"} or old_names - current_names:
        raise ValueError("startup_main_native_membership_extension_unreviewed")
    relative = _code_path("entry_deadline.py")
    selected = Path(selected)
    root = Path(root)
    current = _sha(Path(root) / relative)
    pointer = Path(data_root) / "runtime/mechanistic_entry_policy/current.json"
    active = _json(pointer)
    active_sha = active.get("bundle_sha256")
    if not _hex(active_sha):
        raise ValueError("startup_main_native_membership_extension_unbound")
    pointer_sha = _sha(pointer)
    receipt_path = H.path(data_root, day, commit, active_sha)
    receipt = H.validate_receipt(
        _json(receipt_path), day=day, commit=commit, root=Path(root),
        bundle_sha=active_sha, pointer_sha=pointer_sha,
    )
    origin = Path(str(receipt.get("origin_root", "")))
    if (
        not origin.is_absolute()
        or origin.resolve(strict=True) != origin
        or origin not in {selected, root} and selected != root
    ):
        raise ValueError("startup_main_native_membership_extension_unbound")
    original = _sha(selected / relative)
    origin_sha = _sha(origin / relative)
    # After the first reviewed member addition, later releases carry the same
    # reviewed bytes. Their issued handoff names that actual selected origin,
    # not the pre-addition source. Preserve both phases without minting another
    # compatibility pair or accepting arbitrary identical, unreviewed bytes.
    reviewed_change = (
        origin_sha == REVIEWED_ENTRY_LIFETIME_ORIGINS.get(relative)
        and reviewed_preparation_pair(relative, origin_sha, current)
    )
    reviewed_carry = origin_sha == current == REVIEWED_ENTRY_LIFETIME_SOURCES.get(relative)
    if (
        receipt.get("origin_commit") != _git_head(origin)
        or current != REVIEWED_ENTRY_LIFETIME_SOURCES.get(relative)
        or not (reviewed_change or reviewed_carry)
        or original != (current if selected == root else origin_sha)
        or receipt.get("code_hashes") != H.code_hashes()
        or receipt.get("code_hashes", {}).get(str(Path(root) / relative)) != current
        or receipt.get("actual_pid_consumed") is not False
        or receipt.get("policy_reselected") is not False
        or receipt.get("source_semantics_repair") is not True
        or _sha(pointer) != pointer_sha
    ):
        raise ValueError("startup_main_native_membership_extension_unbound")
    return dict(
        relative=relative, original_sha256=original, runtime_sha256=current,
        receipt_path=str(receipt_path), receipt_sha256=_sha(receipt_path),
        pointer_path=str(pointer), pointer_sha256=pointer_sha,
    )


def _code_path(name):
    if name == "session_contract.py":
        return "src/trading/market/" + name
    if name == "ai_engine_openai.py":
        return "src/engine/" + name
    if not isinstance(name, str) or Path(name).name != name or not name.endswith(".py"):
        raise ValueError("startup_main_code_name_invalid")
    return "src/engine/scalping/" + name


def _pairs(expected, actual):
    if not isinstance(expected, dict) or not expected or set(expected) != set(actual):
        raise ValueError("startup_main_code_inventory_changed")
    for relative, old in expected.items():
        current = actual[relative]
        if not _hex(old) or not _hex(current):
            raise ValueError("startup_main_code_digest_invalid")
        if old != current and not reviewed_preparation_pair(relative, old, current):
            raise ValueError("startup_main_code_pair_unreviewed:" + relative)


def _historical_code_refs(manifest):
    root = Path(manifest["frozen_validator_root"])
    refs = {}
    for name, expected in manifest["semantic_code_hashes"].items():
        relative = _code_path(name)
        path = root / relative
        if path.resolve(strict=True) != path or _sha(path) != expected:
            raise ValueError("startup_main_historical_code_changed")
        refs[relative] = dict(path=str(path), sha256=expected)
    return refs


_DELAY_CONTRACT_OWNER = "src/engine/scalping/pre_submit_delay_initial_policy.py"


def _delay_contract_paths(raw):
    """Read the immutable origin declaration without importing its module."""
    declarations = [
        node.value
        for node in ast.parse(raw).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "CONTRACT_PATHS"
            for target in node.targets
        )
    ]
    if len(declarations) != 1 or not isinstance(declarations[0], ast.Tuple):
        raise ValueError("startup_delay_native_contract_declaration_invalid")
    paths = ast.literal_eval(declarations[0])
    if (
        not 1 <= len(paths) <= 128
        or any(
            not isinstance(path, str)
            or not path.startswith("src/")
            or not path.endswith(".py")
            or str(Path(path)) != path
            or ".." in Path(path).parts
            for path in paths
        )
        or len(set(paths)) != len(paths)
        or _DELAY_CONTRACT_OWNER not in paths
    ):
        raise ValueError("startup_delay_native_contract_declaration_invalid")
    return list(paths)


def _native_verifier_code(proof):
    """Keep actual native verifier code distinct from consumed policy origin."""
    native = proof["native_verification"]
    root = native.get("verification_code_root", proof["selected_release_root"])
    commit = native.get("verification_code_commit", proof["selected_release_commit"])
    allowed = {
        (proof["selected_release_root"], proof["selected_release_commit"]),
        (proof["execution_release_root"], proof["execution_release_commit"]),
    }
    if (root, commit) not in allowed or Path(root).resolve(strict=True) != Path(root):
        raise ValueError("startup_native_verifier_code_identity_invalid")
    return Path(root), commit


def _main_inventory_origin(item, proof):
    """Resolve policy code origin independently of the verification workflow."""
    native = proof["native_verification"]
    observation = native.get("stopped_postclose_observation")
    if not observation or item["bundle_sha256"] != proof["policy_sha256"]:
        return item["origin_commit"]
    root, commit = _native_verifier_code(proof)
    if str(root) == proof["selected_release_root"]:
        return item["origin_commit"]
    records = proof["closure"].get("preserved_generations") or {}
    if len(records) != 1:
        raise ValueError("startup_main_workflow_preparation_required")
    sha, record = next(iter(records.items()))
    path = Path(record["prepared_receipt_path"])
    receipt = _json(path)
    workflow = receipt.get("verification_workflow") or {}
    if (
        _sha(path) != sha
        or native.get("validation_scope") != "current_full_contract"
        or receipt.get("selected_release_commit") != proof["selected_release_commit"]
        or item["origin_commit"] != proof["selected_release_commit"]
        or receipt.get("target_date") != proof["target_date"]
        or receipt.get("source_date") != native.get("source_date")
        or observation.get("source_date") != native.get("source_date")
        or observation.get("prepared_target_date") != proof["target_date"]
        or observation.get("release_commit") != proof["selected_release_commit"]
        or workflow.get("code_root") != str(root)
        or workflow.get("code_commit") != commit
        or workflow.get("native_cold_review_sha256") != _digest(observation)
        or any(
            workflow.get(k) is not False
            for k in ("runtime_effect", "actual_pid_consumed")
        )
        or any(
            observation.get(k) is not False
            for k in ("runtime_effect", "actual_pid_consumed", "allowed_runtime_apply")
        )
        or not observation.get("source_hashes")
    ):
        raise ValueError("startup_main_workflow_origin_unbound")
    _check_sources(observation["source_hashes"])
    # A reviewed workflow may only read the original issuer's family. Keep
    # that declared code origin when every pinned module still matches the
    # selected tree; the parent separately attests these bytes in Git. A
    # family actually computed with workflow code retains that other origin.
    selected = Path(proof["selected_release_root"])
    if all(
        _sha(selected / _code_path(name)) == expected
        for name, expected in item["expected"].items()
    ):
        return item["origin_commit"]
    return commit


def _attest_delay_inventory(selected, commit, records, sources):
    """Parent-only exact Git origin; the child consumes no Git subprocess."""
    import subprocess

    if not records:
        return None
    selected = Path(selected)
    if (
        selected.resolve(strict=True) != selected
        or not _hex(commit, 40)
        or _git_head(selected) != commit
    ):
        raise ValueError("startup_delay_native_inventory_origin_changed")
    raw = subprocess.check_output(
        ["git", "-C", str(selected), "show", commit + ":" + _DELAY_CONTRACT_OWNER]
    )
    paths = _delay_contract_paths(raw)
    inventory = {}
    for relative in paths:
        path = selected / relative
        original = (
            raw
            if relative == _DELAY_CONTRACT_OWNER
            else subprocess.check_output(
                ["git", "-C", str(selected), "show", commit + ":" + relative]
            )
        )
        expected = hashlib.sha256(original).hexdigest()
        if path.resolve(strict=True) != path or _sha(path) != expected:
            raise ValueError("startup_delay_native_code_git_changed")
        if sources.setdefault(str(path), expected) != expected:
            raise ValueError("startup_delay_native_source_conflict")
        inventory[relative] = expected
    if any(item.get("native_code_inventory") != inventory for item in records.values()):
        raise ValueError("startup_delay_native_code_inventory_invalid")
    return dict(
        schema="startup_delay_native_inventory_git_v1",
        origin_commit=commit,
        selected_release_root=str(selected),
        declaration_path=str(selected / _DELAY_CONTRACT_OWNER),
        declaration_sha256=inventory[_DELAY_CONTRACT_OWNER],
        contract_paths=paths,
        code_hashes=inventory,
    )


def _native_main_basis(native):
    """Keep PREOPEN custody scope distinct from this invocation's Main closure."""
    if native.get("status") != "pass" or native.get("findings"):
        return None
    if native.get("validation_scope") == "current_full_contract":
        return "same_invocation_selected_native_full_verification"
    consumed = native.get("native_predecessor_consumption") or {}
    closed = consumed.get("closed_observation") or {}
    if (
        native.get("validation_scope") == "intraday_preserved_historical_generation"
        and native.get("handoff_basis") == "native_closed_preopen_preserved_generation"
        and consumed.get("schema") == "intraday_pid_consumption_verification_v1"
        and consumed.get("status") == "pass" and not consumed.get("findings")
        and consumed.get("basis") == "native_preopen"
        and consumed.get("actual_pid_consumed") is False
        and consumed.get("historical_consumption_verified") is True
        and consumed.get("runtime_effect") is False
        and consumed.get("target_date") == native.get("target_date")
        and consumed.get("selected_release_commit") == native.get("preserved_preopen_commit")
        and _hex(consumed.get("manifest_sha256"))
        and closed.get("schema") == "intraday_closed_consumption_observation_v1"
        and closed.get("basis") == "native_preopen_closed"
        and closed.get("target_date") == native.get("target_date")
        and closed.get("release_commit") == consumed.get("selected_release_commit")
        and closed.get("pid_identity") == consumed.get("pid_identity")
        and closed.get("manifest_sha256") == consumed.get("manifest_sha256")
        and closed.get("historical_consumption_verified") is True
        and closed.get("current_observation_verified") is False
        and closed.get("new_pid_consumption_claimed") is False
        and closed.get("runtime_effect") is False
        and closed.get("source_hashes")
        and (closed.get("collector_shutdown") or {}).get("status") == "verified"
    ):
        return "same_invocation_selected_closed_preopen_native_validation"
    if (
        native.get("validation_scope") == "intraday_preserved_historical_generation"
        and native.get("handoff_basis")
        == "native_consumed_preopen_preserved_generation"
        and consumed.get("schema") == "intraday_pid_consumption_verification_v1"
        and consumed.get("status") == "pass"
        and consumed.get("findings") == []
        and consumed.get("basis") == "native_preopen"
        and consumed.get("actual_pid_consumed") is True
        and consumed.get("target_date") == native.get("target_date")
        and consumed.get("selected_release_commit")
        == native.get("preserved_preopen_commit")
        and _hex(consumed.get("manifest_sha256"))
    ):
        return "same_invocation_selected_consumed_preopen_native_validation"
    if (
        native.get("validation_scope") == "intraday_preserved_historical_generation"
        and native.get("handoff_basis")
        in {
            "intraday_preserved_preopen_generation",
            "intraday_preserved_preopen_generation_current_postclose_resealed",
        }
        and _hex(native.get("preserved_preopen_commit"), 40)
    ):
        return (
            "same_invocation_selected_prepared_intraday_native_validation"
            if native.get("prepared_intraday_handoff")
            else "same_invocation_selected_intraday_native_validation"
        )
    return None


def _preserved_native_sources(proof):
    """Same-invocation full bootstrap with prepared or consumed source custody.

    Intraday Main can preserve a prepared policy without publishing an auxiliary
    transition manifest. That path must supply its own nonempty native closure;
    an empty auxiliary manifest set alone never authorizes delegation.
    """
    native = proof["native_verification"]
    closure = proof["closure"]
    records = closure.get("preserved_generations")
    if not records:
        return {}
    native_consumed = (
        _native_main_basis(native)
        == "same_invocation_selected_consumed_preopen_native_validation"
    )
    native_closed = (
        _native_main_basis(native) == "same_invocation_selected_closed_preopen_native_validation"
    )
    native_prepared = (
        _native_main_basis(native)
        == "same_invocation_selected_prepared_intraday_native_validation"
    )
    prepared_commit = (
        native.get("preserved_preopen_commit")
        if native_prepared
        else proof["selected_release_commit"]
    )
    if (
        native.get("validation_scope") == "current_full_contract"
        or native_consumed
        or native_closed
        or native_prepared
    ):
        if not isinstance(records, dict) or len(records) != 1:
            raise ValueError("startup_prepared_native_scope_invalid")
        data = Path(proof["policy_path"]).parents[3]
        day = proof["target_date"]
        index = data / "runtime/policy_bootstrap/prepared" / day / "latest.json"
        view = _json(index)
        prepared = Path(view["receipt_path"])
        sha = _sha(prepared)
        record = records.get(sha)
        value = _json(prepared)
        if (
            prepared.resolve().parent.parent != index.parent.resolve()
            or view.get("schema") != "next_preopen_readiness_index_v1"
            or view.get("target_date") != day
            or view.get("receipt_sha256") != sha
            or not isinstance(record, dict)
            or record.get("schema") != "startup_native_prepared_preopen_closure_v1"
            or record.get("prepared_receipt_path") != str(prepared)
            or record.get("target_date") != day
            or value.get("target_date") != day
            or value.get("schema") != "next_preopen_readiness_v1"
            or value.get("status") != "prepared_verified"
            or value.get("runtime_effect") is not False
            or value.get("actual_pid_consumed") is not False
            or value.get("source_date") != native.get("source_date")
            or value.get("selected_release_commit") != prepared_commit
            or record.get("selected_release_commit") != prepared_commit
            or (value.get("activation_candidate") or {}).get("bundle_sha256")
            != proof["policy_sha256"]
        ):
            raise ValueError("startup_prepared_native_identity_invalid")
        refs = {str(prepared): sha}
        for name, digest in (
            ("manifest_path", "manifest_file_sha256"),
            ("env_path", "env_sha256"),
            ("verification_path", "verification_sha256"),
            ("controller_path", "controller_sha256"),
            ("summary_path", "summary_sha256"),
        ):
            refs[value[name]] = value[digest]
        for source in value.get("policy_receipts", []):
            refs[source["path"]] = source["sha256"]
        if refs != record.get("sources"):
            raise ValueError("startup_prepared_native_source_set_changed")
        _check_sources(refs)
        full = record.get("full_bootstrap") or {}
        checked = full.get("result") or {}
        manifest = _json(Path(value["manifest_path"]))
        if (
            full.get("path") != value["manifest_path"]
            or full.get("sha256") != value["manifest_file_sha256"]
            or full.get("write") is not False
            or full.get("full_native_verification") is not True
            or checked.get("status") != "pass"
            or checked.get("findings")
            or checked.get("target_date") != day
            or not _hex(value.get("manifest_content_sha256"))
            or checked.get("manifest_sha256") != value["manifest_content_sha256"]
            or record.get("prepared_manifest_sha256")
            != value["manifest_content_sha256"]
            or manifest.get("manifest_sha256") != value["manifest_content_sha256"]
            or manifest.get("target_date") != day
            or manifest.get("selected_release_sha") != prepared_commit
        ):
            raise ValueError("startup_prepared_full_bootstrap_unbound")
        refs[str(index)] = _sha(index)
        if native_prepared:
            binding = native["prepared_intraday_handoff"]
            observation = native.get("stopped_preparation_observation")
            if observation is not None:
                if (
                    observation.get("target_date") != day
                    or observation.get("release_commit")
                    != proof["selected_release_commit"]
                    or any(
                        observation.get(k) is not False
                        for k in (
                            "runtime_effect",
                            "actual_pid_consumed",
                            "allowed_runtime_apply",
                        )
                    )
                    or not observation.get("source_hashes")
                    or any(
                        binding["sources"].get(name) != sha
                        for name, sha in observation["source_hashes"].items()
                    )
                ):
                    raise ValueError("startup_stopped_preparation_observation_invalid")
                _check_sources(observation["source_hashes"])

            path = (
                data
                / "runtime/policy_bootstrap/intraday_handoff"
                / day
                / (proof["selected_release_commit"] + ".json")
            )
            handoff = _json(path)
            expected_sources = {
                **handoff.get("frozen_files", {}),
                str(path): _sha(path),
                **((observation or {}).get("source_hashes") or {}),
            }
            if observation is not None and observation.get(
                "original_first_launch_before"
            ) != handoff.get("first_launch_before"):
                raise ValueError("startup_stopped_preparation_expiry_changed")
            selected = _json(data / "runtime/runtime_release_selection.json")
            active = (
                data
                / "runtime/policy_bootstrap"
                / ("runtime_policy_bootstrap_" + day + ".json")
            )
            active_body = _json(active)
            if (
                binding.get("path") != str(path)
                or binding.get("sha256") != _sha(path)
                or binding.get("sources") != expected_sources
                or binding.get("full_native_validation") is not True
                or native.get("actual_pid_consumed") is not False
                or handoff.get("schema")
                != "intraday_policy_preserving_release_handoff_v1"
                or handoff.get("authority")
                != "APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF"
                or handoff.get("status") != "prepared_verified"
                or handoff.get("target_date") != day
                or handoff.get("selected_release_commit")
                != proof["selected_release_commit"]
                or handoff.get("release_root") != proof["selected_release_root"]
                or handoff.get("actual_pid_consumed") is not False
                or handoff.get("policy_effect") != "unchanged"
                or handoff.get("prepared_receipt_path") != str(prepared)
                or handoff.get("prepared_receipt_sha256") != sha
                or handoff.get("manifest_sha256") != active_body.get("manifest_sha256")
                or active_body.get("target_date") != day
                or expected_sources.get(str(active)) != _sha(active)
                or selected.get("git_commit") != proof["selected_release_commit"]
                or selected.get("release_root") != proof["selected_release_root"]
                or selected.get("actual_pid_consumed") is not False
            ):
                raise ValueError("startup_prepared_intraday_handoff_invalid")
            _check_sources(expected_sources)
            refs.update(expected_sources)
            refs[str(data / "runtime/runtime_release_selection.json")] = _sha(
                data / "runtime/runtime_release_selection.json"
            )
        if native_consumed or native_closed:
            consumed = native["native_predecessor_consumption"]
            selection = data / "runtime/runtime_release_selection.json"
            selected = _json(selection)
            actor = selected.get("actual_pid_receipt") or {}
            identity = dict(
                pid=actor.get("pid"),
                start_ticks=str(actor.get("start_ticks")),
                cwd=actor.get("process_cwd"),
            )
            if (
                selected.get("schema") != "runtime_release_selection_v1"
                or selected.get("actual_pid_consumed") is not True
                or selected.get("release_root") != proof["selected_release_root"]
                or selected.get("git_commit") != proof["selected_release_commit"]
                or consumed.get("release_root") != proof["selected_release_root"]
                or consumed.get("pid_identity") != identity
                or type(identity["pid"]) is not int
                or identity["pid"] <= 0
                or identity["cwd"] != str(Path(proof["selected_release_root"]) / "src")
            ):
                raise ValueError("startup_native_consumption_identity_invalid")
            active = (
                data
                / "runtime/policy_bootstrap"
                / ("runtime_policy_bootstrap_" + day + ".json")
            )
            env = active.with_suffix(".env")
            if _json(active).get("manifest_sha256") != consumed["manifest_sha256"]:
                raise ValueError("startup_native_consumption_bootstrap_changed")
            refs.update({str(p): _sha(p) for p in (selection, active, env)})
            if native_closed:
                closed_sources = consumed["closed_observation"]["source_hashes"]
                if any(closed_sources.get(str(p)) != refs[str(p)] for p in (selection, active, env)):
                    raise ValueError("startup_closed_native_source_binding_invalid")
                _check_sources(closed_sources)
                refs.update(closed_sources)
        return refs
    if (
        native.get("validation_scope") != "intraday_preserved_historical_generation"
        or _native_main_basis(native)
        != "same_invocation_selected_intraday_native_validation"
        or not isinstance(records, dict)
        or len(records) not in {1, 2}
    ):
        raise ValueError("startup_preserved_native_scope_invalid")
    data = Path(proof["policy_path"]).parents[3]
    day = proof["target_date"]
    commit = proof["selected_release_commit"]
    selected = proof["selected_release_root"]
    base = data / "runtime/policy_bootstrap/intraday_handoff" / day
    path = base / (commit + ".json")
    consumed = base / (commit + ".consumed.json")
    sha = _sha(path)
    record = records.get(sha)
    if (
        not isinstance(record, dict)
        or record.get("schema") != "startup_native_preserved_preopen_closure_v1"
        or record.get("target_date") != day
        or record.get("selected_release_commit") != commit
        or record.get("handoff_path") != str(path)
        or record.get("consumed_path") != str(consumed)
    ):
        raise ValueError("startup_preserved_native_identity_invalid")
    handoff = _json(path)
    receipt = _json(consumed)
    manifest_sha = record.get("manifest_sha256")
    if (
        handoff.get("schema") != "intraday_policy_preserving_release_handoff_v1"
        or handoff.get("status") != "prepared_verified"
        or handoff.get("target_date") != day
        or handoff.get("selected_release_commit") != commit
        or handoff.get("release_root") != selected
        or handoff.get("actual_pid_consumed") is not False
        or handoff.get("manifest_sha256") != manifest_sha
        or receipt.get("schema") != "intraday_policy_preserving_consumption_v1"
        or receipt.get("status") != "pass"
        or receipt.get("actual_pid_consumed") is not True
        or receipt.get("handoff_sha256") != sha
        or receipt.get("manifest_sha256") != manifest_sha
        or receipt.get("target_date") != day
        or receipt.get("selected_release_commit") != commit
        or receipt.get("release_root") != selected
        or not receipt.get("pid_identity")
    ):
        raise ValueError("startup_preserved_native_consumption_invalid")
    refs = {**handoff["frozen_files"], str(path): sha, str(consumed): _sha(consumed)}
    if refs != record.get("sources"):
        raise ValueError("startup_preserved_native_source_set_changed")
    _check_sources(refs)
    prepared = Path(handoff["prepared_receipt_path"])
    value = _json(prepared)
    full = record.get("full_bootstrap") or {}
    checked = full.get("result") or {}
    bootstrap = prepared.parent / ("runtime_policy_bootstrap_" + day + ".json")
    if (
        refs.get(str(prepared)) != handoff.get("prepared_receipt_sha256")
        or value.get("source_date") != native.get("source_date")
        or value.get("target_date") != day
        or value.get("status") != "prepared_verified"
        or (value.get("activation_candidate") or {}).get("bundle_sha256")
        != proof["policy_sha256"]
        or full.get("path") != str(bootstrap)
        or _sha(bootstrap) != full.get("sha256")
        or full.get("write") is not False
        or full.get("full_native_verification") is not True
        or checked.get("status") != "pass"
        or checked.get("findings")
        or checked.get("target_date") != day
        or record.get("prepared_manifest_sha256")
        != value.get("manifest_content_sha256")
        or not _hex(value.get("manifest_content_sha256"))
        or checked.get("manifest_sha256") != value["manifest_content_sha256"]
        or _json(bootstrap).get("manifest_sha256") != value["manifest_content_sha256"]
    ):
        raise ValueError("startup_preserved_full_bootstrap_unbound")
    refs[str(bootstrap)] = full["sha256"]
    if len(records) == 2:
        # A full native handoff can also visit its original prepared generation.
        # Admit only that exact ancestor and recheck its complete native contract.
        prepared_sha = handoff["prepared_receipt_sha256"]
        ancestor = records.get(prepared_sha)
        if (
            set(records) != {sha, prepared_sha}
            or not isinstance(ancestor, dict)
            or ancestor.get("prepared_receipt_path") != str(prepared)
            or ancestor.get("full_bootstrap") != full
        ):
            raise ValueError("startup_preserved_native_ancestry_invalid")
        ancestor_refs = _preserved_native_sources(
            dict(
                proof,
                selected_release_commit=value.get("selected_release_commit"),
                native_verification=dict(
                    native, validation_scope="current_full_contract"
                ),
                closure=dict(closure, preserved_generations={prepared_sha: ancestor}),
            )
        )
        if any(
            path in refs and refs[path] != digest
            for path, digest in ancestor_refs.items()
        ):
            raise ValueError("startup_preserved_native_ancestry_source_changed")
        refs.update(ancestor_refs)
    return refs


def bind_main_preparation(root, commit, data_root, intake):
    """Parent-only Git attestation after this invocation's full native verify."""
    import subprocess

    root = Path(root).resolve(strict=True)
    data_root = Path(data_root).resolve(strict=True)
    selected = Path(intake["selected_root"]).resolve(strict=True)
    original_commit = intake["selected_commit"]
    native = intake["native_verification"]
    closure = native.get("native_machine_closure")
    day = intake["manifest"]["target_date"]
    if (
        _native_main_basis(native)
        == "same_invocation_selected_intraday_native_validation"
        and native.get("actual_pid_consumed") is False
    ):
        from src.engine.automation import intraday_release_handoff as H

        path, consumed = H._paths(day, original_commit)
        if not consumed.exists():
            observation = native.get("stopped_preparation_observation")
            if observation is not None:
                with H.stopped_preparation_review(day) as current:
                    if current != observation:
                        raise ValueError("startup_stopped_preparation_proof_changed")
                    checked = H._verify_handoff(day, original_commit)
            else:
                checked = H._verify_handoff(day, original_commit)
            if checked.get("status") != "pass":
                raise ValueError("startup_prepared_intraday_native_validation_failed")
            handoff = checked["handoff"]
            native = dict(
                native,
                prepared_intraday_handoff=dict(
                    path=str(path),
                    sha256=_sha(path),
                    sources={
                        **handoff["frozen_files"],
                        str(path): _sha(path),
                        **(
                            (native.get("stopped_preparation_observation") or {}).get(
                                "source_hashes"
                            )
                            or {}
                        ),
                    },
                    full_native_validation=True,
                ),
            )
    if (
        native.get("status") != "pass"
        or native.get("findings")
        or _native_main_basis(native) is None
        or native.get("target_date") != day
        or native.get("selected_release_commit") != original_commit
        or (
            native.get("validation_scope") == "intraday_preserved_historical_generation"
            and native.get("preserved_preopen_commit")
            != intake["manifest"].get("selected_release_sha")
        )
        or not isinstance(closure, dict)
    ):
        raise ValueError("startup_main_native_full_validation_required")
    policy = (
        data_root
        / "runtime/mechanistic_entry_policy/candidates"
        / ("policy_" + day + ".json")
    )
    bundle = _json(policy)
    if bundle.get("bundle_sha256") != intake["receipt"]["activation_candidate"][
        "bundle_sha256"
    ] or bundle["bundle_sha256"] not in closure.get("bundles", {}):
        raise ValueError("startup_main_native_bundle_unobserved")
    inventories = _main_inventories(bundle)
    extension = _active_entry_code_extension(
        data_root, day, selected, root, commit, inventories
    )
    native_proof = dict(
        policy_path=str(policy),
        policy_sha256=bundle["bundle_sha256"],
        target_date=day,
        selected_release_commit=original_commit,
        selected_release_root=str(selected),
        execution_release_root=str(root),
        execution_release_commit=commit,
        native_verification=native,
        closure=closure,
    )
    preserved_sources = _preserved_native_sources(native_proof)
    native_root, native_commit = _native_verifier_code(native_proof)
    expected = {}
    inventory_attestations = {}
    for item in inventories:
        if not _hex(item["origin_commit"], 40):
            raise ValueError("startup_main_inventory_origin_invalid")
        inventory_origin = _main_inventory_origin(item, native_proof)
        verified = {}
        for name, value in item["expected"].items():
            relative = _code_path(name)
            original = hashlib.sha256(
                subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(selected),
                        "show",
                        inventory_origin + ":" + relative,
                    ]
                )
            ).hexdigest()
            if original != value:
                raise ValueError("startup_main_inventory_git_origin_changed")
            verified[relative] = original
            expected[relative] = _sha(selected / relative)
        inventory_attestations[item["bundle_sha256"]] = dict(
            origin_commit=inventory_origin, code_hashes=verified
        )
    manifests = closure.get("manifests")
    if (
        not isinstance(manifests, dict)
        or len(manifests) > 16
        or not (manifests or preserved_sources)
    ):
        raise ValueError("startup_main_manifest_closure_required")
    sources = {
        str(policy): _sha(policy),
        str(data_root / "runtime/runtime_release_selection.json"): _sha(
            data_root / "runtime/runtime_release_selection.json"
        ),
    }
    sources.update(preserved_sources)
    if extension is not None:
        for key in ("receipt", "pointer"):
            path, sha = extension[key + "_path"], extension[key + "_sha256"]
            if sources.setdefault(path, sha) != sha:
                raise ValueError("startup_main_native_membership_extension_conflict")
    # Cold predecessor raw sources remain under their full native observation
    # and digest closure. Generic request sources are bounded metadata/code.
    # _main_inventory_origin rechecks the observation; never flatten its raw
    # history into the independent small-source reader's authority.
    histories, native_readers = {}, {}
    for ident, observed in manifests.items():
        manifest = _json(observed["path"])
        if (
            manifest.get("artifact_content_sha256") != ident
            or _sha(observed["path"]) != observed["sha256"]
            or observed["bundle_sha256"] != bundle["bundle_sha256"]
            or observed["target_date"] != day
        ):
            raise ValueError("startup_main_manifest_closure_changed")
        sources[observed["path"]] = observed["sha256"]
        declared = {ref["path"] for ref in manifest["sources"]}
        declared.update(manifest["ledger_pack_paths"])
        declared.update(manifest["baseline_dependency_paths"])
        dependencies = observed.get("dependencies")
        if not isinstance(dependencies, list) or len(dependencies) > 8192:
            raise ValueError("startup_main_manifest_dependency_set_changed")
        for dependency, _ in dependencies:
            path = Path(dependency)
            if dependency in declared:
                continue
            if (
                not path.is_relative_to(native_root / "src")
                or path.resolve(strict=True) != path
                or path.suffix != ".py"
            ):
                raise ValueError("startup_main_native_reader_path_invalid")
            relative = str(path.relative_to(native_root))
            digest = hashlib.sha256(
                subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(native_root),
                        "show",
                        native_commit + ":" + relative,
                    ]
                )
            ).hexdigest()
            if (
                _sha(path) != digest
                or len(native_readers) >= 128
                and relative not in native_readers
            ):
                raise ValueError("startup_main_native_reader_git_changed")
            native_readers[relative] = digest
            sources[str(path)] = digest
        histories[ident] = _historical_code_refs(manifest)
        for relative, ref in histories[ident].items():
            sources[ref["path"]] = ref["sha256"]
            selected_hash = _sha(selected / relative)
            if expected.setdefault(relative, selected_hash) != selected_hash:
                raise ValueError("startup_main_origin_inventory_conflict")
        for field in ("next_session_code_hashes", "reader_code_hashes"):
            for name, value in manifest[field].items():
                relative = _code_path(name)
                selected_hash = _sha(selected / relative)
                if (
                    value != selected_hash
                    and not reviewed_preparation_pair(relative, value, selected_hash, root=selected)
                    or expected.setdefault(relative, selected_hash) != selected_hash
                ):
                    raise ValueError(
                        "startup_main_origin_inventory_conflict:" + relative
                    )
    # These entry/configuration owners are not all in the historical inventory.
    # Bind their exact original/current bytes without adding retroactive keys.
    for relative in REVIEWED_PREPARATION_SOURCES:
        old = hashlib.sha256(
            subprocess.check_output(
                ["git", "-C", str(selected), "show", original_commit + ":" + relative]
            )
        ).hexdigest()
        if expected.setdefault(relative, old) != old:
            raise ValueError("startup_main_origin_inventory_conflict")
    if extension is not None:
        relative = extension["relative"]
        if expected.setdefault(relative, extension["original_sha256"]) != extension[
            "original_sha256"
        ]:
            raise ValueError("startup_main_origin_inventory_conflict")
    actual = {}
    for relative, old in expected.items():
        for checkout, revision, digest in (
            (selected, original_commit, old),
            (root, commit, None),
        ):
            path = checkout / relative
            if path.resolve(strict=True) != path or path.is_symlink():
                raise ValueError("startup_main_source_alias")
            value = _sha(path)
            git_value = hashlib.sha256(
                subprocess.check_output(
                    ["git", "-C", str(checkout), "show", revision + ":" + relative]
                )
            ).hexdigest()
            if value != git_value or (digest is not None and value != digest):
                raise ValueError("startup_main_source_git_or_origin_changed")
            sources[str(path)] = value
            if checkout == root:
                actual[relative] = value
    _pairs(expected, actual)
    for item in inventories:
        values = {_code_path(name): value for name, value in item["expected"].items()}
        _pairs(values, {name: actual[name] for name in values})
    for refs in histories.values():
        _pairs(
            {name: ref["sha256"] for name, ref in refs.items()},
            {name: actual[name] for name in refs},
        )
    # A delay rebuild is observed in this same native verification process.
    # Bind its actual immutable documents and selected implementation bytes to
    # the request/source CAS; this grants no standalone selection authority.
    for item in closure.get("delay_selections", {}).values():
        for ref in item["artifacts"].values():
            if sources.setdefault(ref["path"], ref["sha256"]) != ref["sha256"]:
                raise ValueError("startup_delay_native_source_conflict")
    delay_inventory = _attest_delay_inventory(
        native_root, native_commit, closure.get("delay_selections", {}), sources
    )
    proof = dict(
        schema=MAIN_PROOF_SCHEMA,
        target_date=day,
        policy_path=str(policy),
        policy_sha256=bundle["bundle_sha256"],
        policy_file_sha256=_sha(policy),
        execution_release_root=str(root),
        execution_release_commit=commit,
        selected_release_root=str(selected),
        selected_release_commit=original_commit,
        original_code_hashes=expected,
        runtime_code_hashes=actual,
        inventories=inventories,
        active_entry_code_extension=extension,
        inventory_git_attestations=inventory_attestations,
        delay_inventory_git_attestation=delay_inventory,
        historical_semantic_code_sources=histories,
        native_reader_code_sources=native_readers,
        source_hashes=sources,
        closure=closure,
        native_verification={
            k: v for k, v in native.items() if k != "native_machine_closure"
        },
        delegation_basis=_native_main_basis(native),
        policy_effect="unchanged",
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_pid_consumed=False,
    )
    proof["stop_indexed_sources"] = _bind_stop_indexed_sources(
        data_root, intake["manifest"].get("main_stop_confirmation_receipt"), sources
    )
    _check_native_closure(proof)
    return proof


def _stop_index_inventory(data_root, receipt):
    """Read the exact native report named by preparation, never a latest file."""
    if not receipt:
        return {}, {}
    day, target = receipt.get("source_date"), receipt.get("target_date")
    if (
        date.fromisoformat(day).isoformat() != day
        or date.fromisoformat(target).isoformat() != target
        or not day < target
        or not _hex(receipt.get("generation"))
    ):
        raise ValueError("startup_stop_index_scope_invalid")
    directory = (
        Path(data_root)
        / "threshold_cycle/main_stop_confirmation/generations"
        / receipt["generation"]
    )
    path = directory / "report.json"
    report, bundle = _json(path), _json(directory / "policy.json")
    if (
        report.get("report_sha256") != receipt.get("report_sha256")
        or report.get("report_sha256")
        != _digest({k: v for k, v in report.items() if k != "report_sha256"})
        or report.get("source_date") != day
        or report.get("target_date") != target
        or report.get("policy_sha256") != receipt.get("policy_sha256")
        or bundle.get("policy_sha256") != receipt.get("policy_sha256")
        or bundle.get("research_sha256") != report.get("research_sha256")
    ):
        raise ValueError("startup_stop_index_report_changed")
    from src.engine.automation.main_trailing_source_store import SCHEMA

    inventory = {
        name: value
        for name, value in report.get("vote_source_inventory", {}).items()
        if value.get("schema") == SCHEMA + ":generation"
    }
    return inventory, {str(p): _sha(p) for p in (path, directory / "policy.json")}


def _stop_index_identities(data_root, path):
    from src.engine.automation import main_trailing_source_store as S
    from src.engine.infrastructure.validation_digest_session import identity

    logical, _, database = S._location(data_root, path)
    # Include absence: a new WAL or a raw-to-archive transition invalidates the
    # parent observation too. SHM is a lock/index cache, not database content.
    paths = (
        logical,
        Path(str(logical) + ".gz"),
        Path(str(logical) + ".gz.archive_receipt.json"),
        database,
        Path(str(database) + "-wal"),
    )
    return {
        str(p): identity(p) if p.exists() or p.is_symlink() else None for p in paths
    }


def _bind_stop_indexed_sources(data_root, receipt, sources):
    """Parent-only native O(1) index reads, sealed for this isolated invocation."""
    from src.engine.automation import main_trailing_source_store as S
    from src.engine.automation.main_trailing_source_assembler import (
        source_generation_matches,
    )

    inventory, refs = _stop_index_inventory(data_root, receipt)
    entries = {}
    for path, expected in inventory.items():
        # SQLite may create an empty WAL on its first readonly connection.
        # Establish that native reader before sealing physical identities;
        # subsequent source/index/WAL changes retain the strict failure path.
        S.generation(data_root, path)
        before = _stop_index_identities(data_root, path)
        current = S.generation(data_root, path)
        if (
            not source_generation_matches(
                data_root, receipt["source_date"], path, expected
            )
            or _stop_index_identities(data_root, path) != before
        ):
            raise ValueError("startup_stop_index_generation_changed")
        entries[path] = dict(generation=current, identities=before)
    for path, sha in refs.items():
        if sources.setdefault(path, sha) != sha:
            raise ValueError("startup_stop_index_source_conflict")
    return dict(receipt=receipt, entries=entries, source_hashes=refs)


def _verify_stop_indexed_sources(proof, *, verify_native=False):
    from src.engine.automation import main_trailing_source_store as S

    closure = proof.get("stop_indexed_sources")
    if closure is None:
        return {}  # Historical proofs without this consumer retain their scope.
    data_root = Path(proof["policy_path"]).parents[3]
    inventory, refs = _stop_index_inventory(data_root, closure.get("receipt"))
    entries = closure.get("entries")
    if (
        not isinstance(entries, dict)
        or set(entries) != set(inventory)
        or refs != closure.get("source_hashes")
        or any(proof["source_hashes"].get(p) != sha for p, sha in refs.items())
    ):
        raise ValueError("startup_stop_index_closure_unbound")
    for path, entry in entries.items():
        logical, _, _ = S._location(data_root, path)
        before = _stop_index_identities(data_root, path)
        current, expected = entry["generation"], inventory[path]
        if (
            before != entry.get("identities")
            or any(
                value.get("sha256")
                != hashlib.sha256(
                    S.encode({k: v for k, v in value.items() if k != "sha256"})
                ).hexdigest()
                for value in (current, expected)
            )
            # Archived source_signature itself reads SQLite. Its native parent
            # proof is instead pinned by the exact archive/receipt/DB/WAL set.
            or logical.is_file()
            and current.get("source_stat") != S.signature(logical.stat())
            or (
                current != expected
                and (
                    logical.exists()
                    or not Path(str(logical) + ".gz").is_file()
                    or {
                        k: v
                        for k, v in current.items()
                        if k not in {"source_stat", "sha256"}
                    }
                    != {
                        k: v
                        for k, v in expected.items()
                        if k not in {"source_stat", "sha256"}
                    }
                )
            )
            or verify_native
            and S.generation(data_root, path) != current
            or _stop_index_identities(data_root, path) != before
        ):
            raise ValueError("startup_stop_index_generation_changed")
    return entries


def _check_native_closure(proof):
    """Check generations, not a cached verdict, for delegated process-only work."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.validation_digest_session import identity

    closure = proof["closure"]
    native = proof["native_verification"]
    binding = closure.get("digest_binding") or {}
    data_root = Path(proof["policy_path"]).parents[3]
    io = native.get("native_validation_io") or {}
    if (
        closure.get("schema") != "startup_native_machine_closure_v1"
        or not _hex(closure.get("run_id"), 32)
        or native.get("status") != "pass"
        or native.get("findings")
        or _native_main_basis(native) is None
        or native.get("target_date") != proof["target_date"]
        or native.get("selected_release_commit") != proof["selected_release_commit"]
        or binding.get("role") != "postclose"
        or binding.get("day") != native.get("source_date")
        or binding.get("lexical_root") != str(data_root)
        or binding.get("resolved_root") != str(data_root.resolve(strict=True))
        or binding.get("pid") != (io.get("stats") or {}).get("pid")
        or io.get("remaining_entries") != 0
        or binding.get("boot_id")
        != _read("/proc/sys/kernel/random/boot_id", maximum=128).decode().strip()
    ):
        raise ValueError("startup_main_native_closure_invalid")
    bundles = closure.get("bundles")
    bundle = _json(proof["policy_path"])
    if (
        not isinstance(bundles, dict)
        or not 1 <= len(bundles) <= 16
        or bundles.get(proof["policy_sha256"])
        != dict(
            target_date=proof["target_date"],
            family_sha256=bundle["continuous_reversal"]["family_sha256"],
        )
    ):
        raise ValueError("startup_main_native_bundle_unobserved")
    current = closure.get("report_parent_current")
    if current is not None:
        pointer = data_root / "runtime/mechanistic_entry_policy/current.json"
        observed = _json(pointer)
        if (not isinstance(current, dict)
                or current.get("pointer_path") != str(pointer)
                or current.get("pointer_sha256") != _sha(pointer)
                or current.get("target_date") != proof["target_date"]
                or observed.get("effective_date") != proof["target_date"]
                or observed.get("bundle_sha256") != current.get("bundle_sha256")
                or current.get("parent_bundle_sha256") != proof["policy_sha256"]
                or current.get("bundle_sha256") not in bundles):
            raise ValueError("startup_report_parent_current_unbound")
    _delay_selection_records(proof)
    entries = closure.get("digest_entries")
    if (
        not isinstance(entries, dict)
        or len(entries) > 4096
        or len(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode())
        > 512 * 1024
    ):
        raise ValueError("startup_main_digest_closure_unbounded")
    for path, entry in entries.items():
        if (
            not isinstance(entry, dict)
            or set(entry)
            not in (
                {"identity", "digest", "created"},
                {"identity", "digest", "created", "native_generation_proof"},
            )
            or "native_generation_proof" in entry
            and not _hex(entry["native_generation_proof"])
            or not _hex(entry.get("digest"))
            or identity(path) != entry.get("identity")
            or entry["identity"][4] < 1024 * 1024
            or entry["identity"][2] != Path(binding["resolved_root"]).stat().st_dev
            or entry["identity"][8] != os.getuid()
            or type(entry["created"]) not in (int, float)
            or not 0 <= time.time() - entry["created"] <= 600
            or not Path(path).resolve().is_relative_to(binding["resolved_root"])
        ):
            raise ValueError("startup_main_digest_generation_changed")
    sessions = closure.get("digest_sessions")
    if sessions is not None:
        if not isinstance(sessions, dict) or not 1 <= len(sessions) <= 8:
            raise ValueError("startup_main_digest_session_set_invalid")
        for key, observed in sessions.items():
            owner = observed.get("binding") or {}
            stats = observed.get("stats") or {}
            if (
                key
                != hashlib.sha256(
                    json.dumps(owner, sort_keys=True).encode()
                ).hexdigest()
                or owner.get("role") != "postclose"
                or owner.get("pid") != binding["pid"]
                or owner.get("boot_id") != binding["boot_id"]
                or owner.get("resolved_root") != binding["resolved_root"]
                or owner.get("lexical_root") != binding["lexical_root"]
                or owner.get("day") not in {native["source_date"], proof["target_date"]}
                or stats.get("pid") != binding["pid"]
            ):
                raise ValueError("startup_main_digest_session_owner_changed")
    manifests = closure.get("manifests")
    preserved = _preserved_native_sources(proof)
    if (
        not isinstance(manifests, dict)
        or len(manifests) > 16
        or not (manifests or preserved)
    ):
        raise ValueError("startup_main_manifest_closure_invalid")
    for ident, observed in manifests.items():
        manifest = _json(observed["path"])
        if (
            _sha(observed["path"]) != observed["sha256"]
            or manifest.get("artifact_content_sha256") != ident
            or ident
            != _digest(
                {k: v for k, v in manifest.items() if k != "artifact_content_sha256"}
            )
            or observed.get("bundle_sha256") != proof["policy_sha256"]
            or manifest.get("base_bundle_sha256") != proof["policy_sha256"]
            or observed.get("target_date") != proof["target_date"]
        ):
            raise ValueError("startup_main_manifest_binding_invalid")
        paths = {ref["path"] for ref in manifest["sources"]}
        paths.update(manifest["ledger_pack_paths"])
        paths.update(manifest["baseline_dependency_paths"])
        readers = proof.get("native_reader_code_sources", {})
        if not isinstance(readers, dict) or len(readers) > 128:
            raise ValueError("startup_main_native_reader_sources_invalid")
        selected, _ = _native_verifier_code(proof)
        for relative, digest in readers.items():
            path = selected / relative
            if (
                not relative.startswith("src/")
                or ".." in Path(relative).parts
                or path.resolve(strict=True) != path
                or path.suffix != ".py"
                or proof["source_hashes"].get(str(path)) != digest
                or _sha(path) != digest
            ):
                raise ValueError("startup_main_native_reader_source_changed")
            paths.add(str(path))
        dependencies = observed.get("dependencies")
        if (
            not isinstance(dependencies, list)
            or len(dependencies) > 8192
            or len(dependencies) != len(paths)
            or {v[0] for v in dependencies} != paths
        ):
            raise ValueError("startup_main_manifest_dependency_set_changed")
        for path, signature in dependencies:
            if json.loads(json.dumps(N._signature(path))) != signature:
                raise ValueError("startup_main_manifest_dependency_changed")
        frozen_root = manifest["frozen_validator_root"]
        from src.engine.scalping import reversal_auxiliary_next_session as A

        inventory = closure.get("frozen_inventories", {}).get(frozen_root)
        frozen = closure.get("frozen_validations", {}).get(
            manifest["source_manifest"]["path"]
        )
        if (
            inventory != manifest["frozen_inventory"]
            or not inventory
            or _git_head(frozen_root) != manifest["frozen_validator_commit"]
            or not isinstance(frozen, dict)
            or frozen.get("root") != frozen_root
            or frozen.get("bundle_path") != manifest["source_bundle"]["path"]
            or frozen.get("result") != manifest["frozen_validation"]
            or frozen.get("invocation")
            != dict(
                executable=str(Path(frozen_root) / ".venv/bin/python"),
                arguments=["-B", "-c"],
                script_sha256=hashlib.sha256(A._FROZEN_SCRIPT.encode()).hexdigest(),
                cwd=frozen_root,
                source_manifest=manifest["source_manifest"]["path"],
                source_bundle=manifest["source_bundle"]["path"],
                environment=dict(PYTHONPATH=frozen_root, PYTHONDONTWRITEBYTECODE="1"),
                parent_environment="sanitized_p5_native_verification",
            )
        ):
            raise ValueError("startup_main_frozen_native_validation_unbound")
        # Original frozen source bytes are in native dependency signatures and
        # are also rehashed by the native prepare validator below.
        if not set(inventory).issubset(paths):
            raise ValueError("startup_main_frozen_inventory_incomplete")
        if (
            json.loads(json.dumps(A._database_signature(manifest)))
            != observed["database"]
        ):
            raise ValueError("startup_main_manifest_database_changed")
    _native_logical_sources(proof)


def _native_logical_sources(proof, *, verify_ledger=False):
    """Finite selected-ledger evidence, never a byte hash of its global DB."""
    from src.engine.infrastructure.validation_digest_session import identity
    from src.engine.scalping import reversal_auxiliary_next_session as A
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.ai import offline_comparison_store as S

    _verify_stop_indexed_sources(proof, verify_native=verify_ledger)
    native = proof["native_verification"]
    if (
        native.get("status") != "pass"
        or native.get("findings")
        or _native_main_basis(native) is None
        or proof.get("delegation_basis") != _native_main_basis(native)
    ):
        raise ValueError("startup_logical_native_validation_required")
    result = {}
    observed_manifests = proof["closure"]["manifests"]
    if (
        not isinstance(observed_manifests, dict)
        or len(observed_manifests) > 16
        or not (observed_manifests or _preserved_native_sources(proof))
    ):
        raise ValueError("startup_logical_manifest_set_invalid")
    for ident, observed in observed_manifests.items():
        manifest = _json(observed["path"])
        if (
            _sha(observed["path"]) != observed["sha256"]
            or manifest.get("artifact_content_sha256") != ident
            or ident
            != _digest(
                {k: v for k, v in manifest.items() if k != "artifact_content_sha256"}
            )
            or manifest["base_bundle_sha256"] != proof["policy_sha256"]
            or observed["target_date"] != proof["target_date"]
        ):
            raise ValueError("startup_logical_manifest_changed")
        database = json.loads(json.dumps(A._database_signature(manifest)))
        if database != observed["database"]:
            raise ValueError("startup_logical_database_changed")
        identities = observed.get("database_source_identities") or {}
        if set(identities) != {v[0] for v in (database or ()) if v is not None}:
            raise ValueError("startup_logical_database_identity_set_changed")
        if database and verify_ledger:
            with S.Store(manifest["ledger_data_root"], readonly=True) as store:
                store.db.execute("BEGIN")
                actual = J._ledger_fingerprint(store, manifest["ledger_metadata"])
            if (
                actual != manifest["ledger_metadata"]["fingerprint_sha256"]
                or json.loads(json.dumps(A._database_signature(manifest))) != database
            ):
                raise ValueError("startup_logical_ledger_changed")
        if database and manifest.get("policy_data_root") != str(
            Path(proof["policy_path"]).parents[3]
        ):
            raise ValueError("startup_logical_data_root_changed")
        for index, signature in enumerate(database or ()):
            if signature is None:
                continue
            path = signature[0]
            if identity(path) != identities[path]:
                raise ValueError("startup_logical_database_identity_changed")
            row = result.setdefault(
                path,
                dict(
                    schema="startup_native_logical_source_v1",
                    path=path,
                    source_kind=(
                        "sqlite_ledger_container" if index == 0 else "sqlite_ledger_wal"
                    ),
                    identity=identities[path],
                    native_signature=signature,
                    manifest_proofs={},
                    policy_data_root=manifest["policy_data_root"],
                    source_run_id=proof["closure"]["run_id"],
                    target_date=proof["target_date"],
                    policy_sha256=proof["policy_sha256"],
                    runtime_effect=False,
                    allowed_runtime_apply=False,
                ),
            )
            if (
                row["identity"] != identities[path]
                or row["native_signature"] != signature
            ):
                raise ValueError("startup_logical_database_conflict")
            row["manifest_proofs"][ident] = dict(
                path=observed["path"],
                sha256=observed["sha256"],
                ledger_data_root=manifest["ledger_data_root"],
                ledger_metadata_sha256=_digest(manifest["ledger_metadata"]),
                ledger_fingerprint_sha256=manifest["ledger_metadata"][
                    "fingerprint_sha256"
                ],
            )
    return {
        path: {**row, "receipt_sha256": _digest(row)} for path, row in result.items()
    }


def preparation_logical_sources():
    """P5-only typed sources; ordinary/native runtime callers keep full reads."""
    proof = _main_context()
    return {} if proof is None else _native_logical_sources(proof)


def verify_preparation_logical_sources(proof, receipts):
    """Parent/P6 exact-set check after request binding; recheck finite native rows.

    Callers retain their original request, release, selector and source CAS.
    No old digest TTL or cached verification verdict is reused here.
    """
    expected = _native_logical_sources(proof, verify_ledger=True)
    if not isinstance(receipts, dict) or receipts != expected:
        raise ValueError("startup_logical_source_set_changed")
    return expected


def _main_proof(proof, request):
    if (
        not isinstance(proof, dict)
        or proof.get("schema") != MAIN_PROOF_SCHEMA
        or proof.get("target_date") != request["target_date"]
        or proof.get("execution_release_root") != request["execution_release_root"]
        or proof.get("execution_release_commit") != request["execution_release_commit"]
        or proof.get("closure", {}).get("run_id") != request["run_id"]
        or proof.get("policy_effect") != "unchanged"
        or proof.get("delegation_basis")
        != _native_main_basis(proof.get("native_verification") or {})
        or _native_main_basis(proof.get("native_verification") or {}) is None
        or (
            proof.get("native_verification", {}).get("validation_scope")
            == "intraday_preserved_historical_generation"
            and proof["native_verification"].get("preserved_preopen_commit")
            != request["manifest"].get("selected_release_sha")
        )
        or any(
            proof.get(k) is not False
            for k in ("runtime_effect", "allowed_runtime_apply", "actual_pid_consumed")
        )
        or any(
            (request.get("expected_policy_hashes") or {}).get(k)
            != proof.get("policy_sha256")
            for k in ("main_machine", "main_auxiliary")
        )
    ):
        raise ValueError("startup_main_preparation_proof_invalid")
    stop = request["manifest"].get("main_stop_confirmation_receipt")
    closure = proof.get("stop_indexed_sources")
    if stop and (not isinstance(closure, dict) or closure.get("receipt") != stop):
        raise ValueError("startup_stop_index_preparation_unbound")
    sources = proof.get("source_hashes")
    _check_sources(sources)
    if any(
        request["source_hashes"].get(path) != value for path, value in sources.items()
    ):
        raise ValueError("startup_main_preparation_sources_unbound")
    data = Path(request["data_root"])
    path = (
        data
        / "runtime/mechanistic_entry_policy/candidates"
        / ("policy_" + request["target_date"] + ".json")
    )
    if proof.get("policy_path") != str(path) or _sha(path) != proof.get(
        "policy_file_sha256"
    ):
        raise ValueError("startup_main_preparation_policy_changed")
    bundle = _json(path)
    if bundle.get("bundle_sha256") != proof["policy_sha256"] or _main_inventories(
        bundle
    ) != proof.get("inventories"):
        raise ValueError("startup_main_preparation_inventory_changed")
    selected = Path(proof["selected_release_root"])
    if _git_head(selected) != proof["selected_release_commit"]:
        raise ValueError("startup_main_preparation_selected_changed")
    selector = _json(data / "runtime/runtime_release_selection.json")
    if (
        selector.get("release_root") != str(selected)
        or selector.get("git_commit") != proof["selected_release_commit"]
    ):
        raise ValueError("startup_main_preparation_selector_changed")
    expected, actual = proof["original_code_hashes"], proof["runtime_code_hashes"]
    required = {}
    inventory_attestations = {}
    for item in proof["inventories"]:
        if not _hex(item["origin_commit"], 40):
            raise ValueError("startup_main_inventory_origin_invalid")
        values = {_code_path(name): value for name, value in item["expected"].items()}
        inventory_attestations[item["bundle_sha256"]] = dict(
            origin_commit=_main_inventory_origin(item, proof), code_hashes=values
        )
        for name, value in item["expected"].items():
            relative = _code_path(name)
            required[relative] = _sha(selected / relative)
        _pairs(values, {name: actual[name] for name in values})
    if inventory_attestations != proof.get("inventory_git_attestations"):
        raise ValueError("startup_main_inventory_git_attestation_changed")
    histories = {}
    for ident, observed in proof["closure"]["manifests"].items():
        manifest = _json(observed["path"])
        histories[ident] = _historical_code_refs(manifest)
        for relative, ref in histories[ident].items():
            if sources.get(ref["path"]) != ref["sha256"]:
                raise ValueError("startup_main_historical_code_unbound")
            value = _sha(selected / relative)
            if required.setdefault(relative, value) != value:
                raise ValueError("startup_main_origin_inventory_conflict")
        for field in ("next_session_code_hashes", "reader_code_hashes"):
            for name, value in manifest[field].items():
                relative = _code_path(name)
                selected_hash = _sha(selected / relative)
                if (
                    value != selected_hash
                    and not reviewed_preparation_pair(relative, value, selected_hash, root=selected)
                    or required.setdefault(relative, selected_hash) != selected_hash
                ):
                    raise ValueError(
                        "startup_main_origin_inventory_conflict:" + relative
                    )
    for relative in REVIEWED_PREPARATION_SOURCES:
        old = _sha(selected / relative)
        if required.setdefault(relative, old) != old:
            raise ValueError("startup_main_origin_inventory_conflict")
    extension = _active_entry_code_extension(
        data, request["target_date"], selected, ROOT,
        request["execution_release_commit"], proof["inventories"],
    )
    if extension != proof.get("active_entry_code_extension"):
        raise ValueError("startup_main_native_membership_extension_changed")
    if extension is not None:
        relative = extension["relative"]
        if (
            required.setdefault(relative, extension["original_sha256"])
            != extension["original_sha256"]
            or sources.get(extension["receipt_path"])
            != extension["receipt_sha256"]
            or sources.get(extension["pointer_path"])
            != extension["pointer_sha256"]
            or actual.get(relative) != extension["runtime_sha256"]
        ):
            raise ValueError("startup_main_native_membership_extension_unbound")
    if required != expected or histories != proof.get(
        "historical_semantic_code_sources"
    ):
        raise ValueError("startup_main_exact_code_closure_required")
    _pairs(expected, actual)
    for refs in histories.values():
        _pairs(
            {name: ref["sha256"] for name, ref in refs.items()},
            {name: actual[name] for name in refs},
        )
    for relative, old in expected.items():
        if (
            _sha(selected / relative) != old
            or _sha(ROOT / relative) != actual[relative]
            or sources.get(str(selected / relative)) != old
            or sources.get(str(ROOT / relative)) != actual[relative]
        ):
            raise ValueError("startup_main_preparation_code_changed")
    _check_native_closure(proof)


def _request_identity(path):
    from src.engine.infrastructure.validation_digest_session import identity

    return identity(path)


def _anchor_identities_unchanged(anchors):
    """Compare all files while checking shared lexical parents once per pass."""
    parents = {}

    def parent_row(name):
        value = os.lstat(name)
        row = [name, value.st_dev, value.st_ino, value.st_mode, value.st_uid]
        if stat.S_ISLNK(value.st_mode):
            row += [value.st_ctime_ns, os.readlink(name)]
        return row

    for name, before in anchors.items():
        if name != before[0]:
            return False
        if before[0] != before[1]:
            if _request_identity(name) != before:
                return False
            continue
        value = os.lstat(name)
        if [
            value.st_dev,
            value.st_ino,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
            value.st_mode,
            value.st_uid,
        ] != before[2:9]:
            return False
        for row in before[9]:
            if row[0] not in parents:
                parents[row[0]] = parent_row(row[0])
            if parents[row[0]] != row:
                return False
    return all(parent_row(name) == row for name, row in parents.items())


def _main_context(*, digest_only=False):
    global _CONTEXT
    if _CONTEXT is None:
        return None
    try:
        c = _CONTEXT
        if c.get("valid") is not True:
            raise ValueError("startup_code_context_invalid")
        _isolation(c["request"])
        if (
            os.getpid() != c["pid"]
            or _request_identity(c["request_path"]) != c["request_identity"]
            or (
                not digest_only
                and (
                    _git_head(ROOT) != c["request"]["execution_release_commit"]
                    or _sha(c["request_path"]) != c["request_sha256"]
                )
            )
        ):
            raise ValueError("startup_code_context_execution_changed")
        proof = c["request"].get("main_preparation_code_handoff")
        if not isinstance(proof, dict):
            raise ValueError("startup_main_preparation_proof_required")
        if (
            _git_head(proof["selected_release_root"])
            != proof["selected_release_commit"]
            or _git_head(ROOT) != c["request"]["execution_release_commit"]
            or _sha("/proc/self/mountinfo") != c["main_mountinfo_sha256"]
            or not _anchor_identities_unchanged(c["main_anchor_identities"])
            or _sha("/proc/self/mountinfo") != c["main_mountinfo_sha256"]
        ):
            raise ValueError("startup_main_preparation_anchor_changed")
        return proof
    except (OSError, ValueError, KeyError, TypeError):
        _CONTEXT = {"valid": False}
        raise


def validation_indexed_source_generation(data_root, path):
    """Use exact native index evidence only inside the isolated P5 invocation.

    The parent runs the native reader before and after the child. The child
    rechecks raw/archive and DB/WAL identities; it never opens SQLite or scans
    an unbounded raw stream. Ordinary consumers retain the native index reader.
    """
    if _CONTEXT is None:
        return None
    proof = _main_context()
    request = _CONTEXT["request"]
    if str(Path(data_root).resolve()) != request["data_root"]:
        raise ValueError("startup_stop_index_data_root_changed")
    entries = _verify_stop_indexed_sources(proof)
    from src.engine.automation import main_trailing_source_store as S

    logical, _, _ = S._location(data_root, path)
    matching = [value for name, value in entries.items()
                if S._location(data_root, name)[0] == logical]
    if len(matching) != 1:
        raise ValueError("startup_stop_index_source_unbound")
    entry = matching[0]
    return json.loads(json.dumps(entry["generation"]))


def validation_raw_vote_sources(data_root, source_date):
    """Keep isolated native vote validation on its bounded raw JSONL reader.

    Ordinary runtime/research retains the indexed reader. This selects I/O,
    never a semantic verdict or an exception to the original raw guards.
    """
    if _CONTEXT is None:
        return False
    proof = _main_context()
    request = _CONTEXT["request"]
    if (
        str(Path(data_root).resolve()) != request["data_root"]
        or date.fromisoformat(source_date).isoformat() != source_date
        or source_date > proof["native_verification"]["source_date"]
        or not source_date < request["target_date"]
    ):
        raise ValueError("startup_raw_vote_source_scope_invalid")
    return True


def validation_future_vote_snapshot(data_root, source_date):
    """Permit only a native future-tail snapshot inside the isolated child."""
    if _CONTEXT is None:
        return False
    _main_context()
    request = _CONTEXT["request"]
    proof = request["candidate_code_handoffs"].get("main_stop")
    if not isinstance(proof, dict):
        raise ValueError("startup_stop_snapshot_policy_required")
    _proof(proof, "main_stop", request)
    receipt = request["manifest"]["main_stop_confirmation_receipt"]
    if (
        str(Path(data_root).resolve()) != request["data_root"]
        or receipt.get("source_date") != source_date
        or not source_date < request["target_date"]
    ):
        raise ValueError("startup_stop_snapshot_scope_invalid")
    return True


def _delay_selection_records(proof):
    from src.engine.infrastructure.validation_digest_session import identity

    records = proof["closure"].get("delay_selections", {})
    if not isinstance(records, dict) or len(records) > 16:
        raise ValueError("startup_delay_selection_closure_invalid")
    origin = proof.get("delay_inventory_git_attestation")
    if records:
        selected, native_commit = _native_verifier_code(proof)
        declaration = selected / _DELAY_CONTRACT_OWNER
        if (
            not isinstance(origin, dict)
            or origin.get("schema") != "startup_delay_native_inventory_git_v1"
            or origin.get("origin_commit") != native_commit
            or origin.get("selected_release_root") != str(selected)
            or selected.resolve(strict=True) != selected
            or _git_head(selected) != native_commit
            or origin.get("declaration_path") != str(declaration)
            or declaration.resolve(strict=True) != declaration
            or _sha(declaration) != origin.get("declaration_sha256")
            or proof["source_hashes"].get(str(declaration))
            != origin.get("declaration_sha256")
            or origin.get("contract_paths") != _delay_contract_paths(_read(declaration))
            or not isinstance(origin.get("code_hashes"), dict)
            or set(origin["code_hashes"]) != set(origin["contract_paths"])
        ):
            raise ValueError("startup_delay_native_inventory_attestation_invalid")
    for key, item in records.items():
        if (
            not isinstance(item, dict)
            or item.get("schema") != "startup_native_delay_selection_v1"
            or item.get("run_id") != proof["closure"]["run_id"]
            or item.get("parent_full_selection_recomputed") is not True
            or item.get("child_recomputed") is not False
            or item.get("target_date") not in (None, proof["target_date"])
            or key != _digest([item.get("policy_sha256"), item.get("target_date")])
            or set(item.get("artifacts", {})) != {"policy", "report"}
        ):
            raise ValueError("startup_delay_selection_closure_invalid")
        root = Path(item["evidence_root"])
        if root.resolve(strict=True) != root or root.is_symlink():
            raise ValueError("startup_delay_evidence_alias")
        values = {}
        for name, ref in item["artifacts"].items():
            path = root / (name + ".json")
            if (
                ref.get("path") != str(path)
                or identity(path) != ref.get("identity")
                or proof["source_hashes"].get(str(path)) != ref.get("sha256")
                or _sha(path) != ref.get("sha256")
            ):
                raise ValueError("startup_delay_artifact_generation_changed")
            values[name] = _json(path)
        policy, report = values["policy"], values["report"]
        data_root = Path(proof["policy_path"]).parents[3]
        expected_root = (
            data_root
            / "threshold_cycle/pre_submit_delay_policy/generations"
            / _digest([report, policy])
        )
        if root != expected_root:
            raise ValueError("startup_delay_policy_generation_unbound")
        if (
            item.get("documents_sha256") != _digest([policy, report])
            or item.get("report_sha256") != _digest(report)
            or item.get("policy_sha256") != policy.get("policy_sha256")
            or item.get("source_sha256") != policy.get("source_sha256")
            or item.get("code_contract_sha256") != policy.get("code_contract_sha256")
            or item.get("effective_from") != policy.get("effective_from")
            or item.get("expires_on") != policy.get("expires_on")
            or not item["effective_from"] <= proof["target_date"] <= item["expires_on"]
            or item.get("tree_refs")
            != {
                key: report.get(key)
                for key in ("qualified_projection_ref", "partitions_ref", "cells_ref")
            }
        ):
            raise ValueError("startup_delay_selection_binding_invalid")
        inventory = item.get("native_code_inventory")
        if (
            not isinstance(inventory, dict)
            or inventory != origin["code_hashes"]
            or _digest(inventory) != item.get("native_code_sha256")
        ):
            raise ValueError("startup_delay_native_code_inventory_invalid")
        for relative, expected in inventory.items():
            path = selected / relative
            if (
                path.resolve(strict=True) != path
                or not _hex(expected)
                or proof["source_hashes"].get(str(path)) != expected
                or _sha(path) != expected
            ):
                raise ValueError("startup_delay_native_code_changed")
    return records


def validate_preparation_delay_selection(policy, report, *, target_date=None):
    """Recheck source trees; delegate only the parent's observed SQL rebuild.

    The same invocation's native full verification executed that rebuild
    before isolation. Ordinary consumers retain the complete native algorithm.
    """
    proof = _main_context(digest_only=True)
    if proof is None:
        return False
    request = _CONTEXT["request"]
    contract = request["candidate_code_handoffs"].get("pre_submit_delay") or {}
    bound = request["manifest"].get("pre_submit_delay_handoff") or {}
    if (
        contract.get("policy_sha256") != policy.get("policy_sha256")
        or bound.get("policy_path")
        != str(getattr(policy, "evidence_root", "") / Path("policy.json"))
        or target_date not in (None, request["target_date"])
    ):
        raise ValueError("startup_delay_request_binding_invalid")
    records = _delay_selection_records(proof)
    matched = [
        v for v in records.values() if v["policy_sha256"] == policy.get("policy_sha256")
    ]
    root = getattr(report, "evidence_root", None)
    if (
        not matched
        or root is None
        or getattr(policy, "evidence_root", None) != root
        or any(
            v["evidence_root"] != str(root)
            or v["documents_sha256"] != _digest([policy, report])
            for v in matched
        )
    ):
        raise ValueError("startup_delay_selection_unobserved_or_changed")
    sources = _delay_tree_sources(root, report)
    delegated = _CONTEXT["delegation"].setdefault("delay_selections", {})
    delegated[policy["policy_sha256"]] = dict(
        parent_full_selection_recomputed=True,
        child_recomputed=False,
        child_headers_and_physical_logical_trees_reverified=True,
        documents_sha256=_digest([policy, report]),
        evidence_root=str(root),
        source_hashes=sources,
    )
    return True


def _delay_tree_sources(root, report):
    """Reverify the native trees, including every nested membership leaf."""
    from src.engine.lifecycle import research_storage as storage
    from src.engine.lifecycle.research_input_budget import Claim
    from src.engine.infrastructure.validation_digest_session import identity

    sources = {}

    def physical(ref, depth=0):
        if depth > 16:
            raise ValueError("research_tree_depth_invalid")
        if ref.get("kind") == "inline":
            return
        if type(ref.get("size")) is not int or not 0 <= ref["size"] <= 4 * 1024 * 1024:
            raise ValueError("research_shard_generation_changed")
        path = storage.safe_path(root, ref["path"])
        before = identity(path)
        with Claim(ref["size"] * 8):
            raw = _read(path, maximum=ref["size"])
            if (
                len(raw) != ref["size"]
                or hashlib.sha256(raw).hexdigest() != ref["sha256"]
                or identity(path) != before
            ):
                raise ValueError("startup_delay_shard_generation_changed")
            if sources.setdefault(str(path), ref["sha256"]) != ref["sha256"]:
                raise ValueError("startup_delay_shard_reference_conflict")
            body = json.loads(raw)
            for child in body.get("children", []):
                physical(child, depth + 1)

    for key in ("qualified_projection_ref", "partitions_ref", "cells_ref"):
        for row in storage.iter_tree(root, report[key]):
            if key == "partitions_ref":
                for _ in storage.iter_tree(root, row["membership"]):
                    pass
                physical(row["membership"])
        physical(report[key])
    return sources


def preparation_delay_source_hashes():
    if _main_context(digest_only=True) is None:
        return {}
    sources = {}
    for item in _CONTEXT["delegation"].get("delay_selections", {}).values():
        for path, sha in item["source_hashes"].items():
            if sources.setdefault(path, sha) != sha:
                raise ValueError("startup_delay_child_source_conflict")
    return sources


def verify_preparation_delay_delegation(proof, delegation, request, consumer):
    """Parent mandatory exact-set check; also reusable for fresh source CAS."""
    records = _delay_selection_records(proof)
    bound = request["manifest"].get("pre_submit_delay_handoff") or {}
    ident = bound.get("policy_sha256")
    matched = [v for v in records.values() if v["policy_sha256"] == ident]
    actual = delegation.get("delay_selections", {})
    if not matched:
        configured = _json(bound["policy_path"]) if bound.get("policy_path") else {}
        if (
            actual
            or configured.get("storage_schema")
            == "pre_submit_delay_sharded_evidence_v3"
        ):
            raise ValueError("startup_delay_child_selection_unobserved")
        return
    if set(actual) != {ident} or consumer.get("status") != "loaded":
        raise ValueError("startup_delay_child_selection_missing")
    item = matched[0]
    if item["artifacts"]["policy"]["path"] != bound.get("policy_path"):
        raise ValueError("startup_delay_child_policy_unbound")
    report = _json(item["artifacts"]["report"]["path"])
    sources = _delay_tree_sources(Path(item["evidence_root"]), report)
    expected = dict(
        parent_full_selection_recomputed=True,
        child_recomputed=False,
        child_headers_and_physical_logical_trees_reverified=True,
        documents_sha256=item["documents_sha256"],
        evidence_root=item["evidence_root"],
        source_hashes=sources,
    )
    if actual[ident] != expected or any(
        consumer.get("source_hashes", {}).get(p) != s for p, s in sources.items()
    ):
        raise ValueError("startup_delay_child_selection_changed")


def verify_validation_main_code(bundle, paths, actual):
    proof = _main_context()
    if proof is None:
        return False
    item = next(
        (
            v
            for v in proof["inventories"]
            if v["bundle_sha256"] == bundle.get("bundle_sha256")
        ),
        None,
    )
    family = bundle.get("continuous_reversal") or {}
    expected = family.get("contract_file_sha256")
    extension = proof.get("active_entry_code_extension")
    extra = (
        {Path(extension["relative"]).name}
        if isinstance(extension, dict) and item is not None
        and item["schema"] == "continuous_reversal_policy_v6"
        else set()
    )
    if (
        item is None
        or item["expected"] != expected
        or item["schema"] != family.get("schema")
        or item["target_date"] != bundle.get("target_date")
        or set(paths) != set(expected) | extra
        or set(actual) != set(expected) | extra
    ):
        raise ValueError("startup_main_native_inventory_unbound")
    if extra:
        relative = extension["relative"]
        name = Path(relative).name
        if (
            name != "entry_deadline.py"
            or proof["original_code_hashes"].get(relative)
            != extension["original_sha256"]
            or proof["runtime_code_hashes"].get(relative)
            != extension["runtime_sha256"]
            or actual.get(name) != extension["runtime_sha256"]
            or str(Path(paths[name]).resolve(strict=True)) != str(ROOT / relative)
            or _sha(paths[name]) != actual[name]
        ):
            raise ValueError("startup_main_native_membership_extension_unbound")
    for name, old in expected.items():
        relative = _code_path(name)
        if (
            str(Path(paths[name]).resolve(strict=True)) != str(ROOT / relative)
            or proof["runtime_code_hashes"].get(relative) != actual[name]
            or _sha(paths[name]) != actual[name]
        ):
            raise ValueError("startup_main_native_code_unbound")
    _pairs(
        {_code_path(name): old for name, old in expected.items()},
        {_code_path(name): actual[name] for name in expected},
    )
    return True


def validation_auxiliary_preparation(manifest, bundle, data_root):
    proof = _main_context()
    if proof is None:
        return None
    item = proof["closure"]["manifests"].get(manifest.get("artifact_content_sha256"))
    if (
        not isinstance(item, dict)
        or bundle.get("bundle_sha256") != proof["policy_sha256"]
        or bundle.get("target_date") != proof["target_date"]
        or str(Path(data_root).resolve()) != _CONTEXT["request"]["data_root"]
        or _json(item["path"]) != manifest
        or _sha(item["path"]) != item["sha256"]
    ):
        raise ValueError("startup_main_auxiliary_preparation_unbound")
    _check_native_closure(proof)
    ident = manifest["artifact_content_sha256"]
    if ident not in _CONTEXT["delegation"]["auxiliary_manifests"]:
        _CONTEXT["delegation"]["auxiliary_manifests"].append(ident)
    historical = proof["historical_semantic_code_sources"][ident]
    original = {
        **proof["original_code_hashes"],
        **{name: ref["sha256"] for name, ref in historical.items()},
    }
    for field in ("next_session_code_hashes", "reader_code_hashes"):
        for name, digest in manifest[field].items():
            relative = _code_path(name)
            if relative not in historical:
                original[relative] = digest
    return dict(
        manifest=manifest,
        frozen_inventory=manifest["frozen_inventory"],
        frozen_validation=manifest["frozen_validation"],
        original_code_hashes=original,
        runtime_code_hashes=proof["runtime_code_hashes"],
        delegation_basis=proof["delegation_basis"],
    )


class _PreparationDigests:
    """Read-only, process-bound reuse of bytes hashed by the same P5 intake."""

    @property
    def binding(self):
        if _main_context() is None:
            raise ValueError("startup_code_context_required")
        # This adapter must never enroll source generations as a postclose
        # producer; native readers still execute against the parent byte proof.
        return {"role": "startup_validation"}

    def digest(self, path):
        if _CONTEXT is None:
            return None
        if _CONTEXT.get("valid") is not True:
            raise ValueError("startup_code_context_invalid")
        item = _CONTEXT["request"].get("main_preparation_code_handoff")
        if not isinstance(item, dict):
            return None
        entry = item["closure"]["digest_entries"].get(str(Path(path).absolute()))
        if entry is None:
            return None
        proof = _main_context(digest_only=True)
        if proof is None:
            return None
        from src.engine.infrastructure.validation_digest_session import identity

        if (
            identity(path) != entry["identity"]
            or not 0 <= time.time() - entry["created"] <= 600
        ):
            raise ValueError("startup_main_digest_generation_changed")
        _CONTEXT["delegation"]["digest_reused_reads"] += 1
        _CONTEXT["delegation"]["digest_reused_bytes"] += entry["identity"][4]
        return entry["digest"]


def preparation_source_digest(path):
    """Only the P5 parent attestation; ordinary digest sessions do not opt in."""
    return _PreparationDigests().digest(path)


def validation_delegation_receipt():
    proof = _main_context()
    if proof is None:
        return None
    return dict(
        schema="startup_native_validation_delegation_v1",
        basis=proof["delegation_basis"],
        source_native_pid=proof["closure"]["digest_binding"]["pid"],
        target_date=proof["target_date"],
        policy_sha256=proof["policy_sha256"],
        run_id=proof["closure"]["run_id"],
        request_sha256=_CONTEXT["request"]["request_sha256"],
        parent_validation_scope=proof["native_verification"]["validation_scope"],
        child_semantic_validation="native_validators_executed",
        **_CONTEXT["delegation"],
        runtime_effect=False,
        actual_pid_consumed=False,
        allowed_runtime_apply=False,
    )
