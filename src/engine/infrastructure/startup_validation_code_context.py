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


def reviewed_preparation_pair(relative, old, current):
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
    selector = Path(request["data_root"]) / "runtime/runtime_release_selection.json"
    _bound_source(sources, selector)
    selection = _json(selector)
    if (
        selection.get("schema") != "runtime_release_selection_v1"
        or selection.get("release_root") != str(selected)
        or selection.get("git_commit") != commit
    ):
        raise ValueError("startup_code_context_selected_identity_changed")
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
    """A cold workflow computes the new family; carried parents keep their origin."""
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
        if native_consumed:
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
                    and not reviewed_preparation_pair(relative, value, selected_hash)
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
            or Path(path).is_file()
            and current.get("source_stat") != S.signature(Path(path).stat())
            or (
                current != expected
                and (
                    Path(path).exists()
                    or not Path(str(path) + ".gz").is_file()
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
                    and not reviewed_preparation_pair(relative, value, selected_hash)
                    or required.setdefault(relative, selected_hash) != selected_hash
                ):
                    raise ValueError(
                        "startup_main_origin_inventory_conflict:" + relative
                    )
    for relative in REVIEWED_PREPARATION_SOURCES:
        old = _sha(selected / relative)
        if required.setdefault(relative, old) != old:
            raise ValueError("startup_main_origin_inventory_conflict")
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
    entry = entries.get(str(Path(path).absolute()))
    if entry is None:
        raise ValueError("startup_stop_index_source_unbound")
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
    if (
        item is None
        or item["expected"] != expected
        or item["schema"] != family.get("schema")
        or item["target_date"] != bundle.get("target_date")
        or set(paths) != set(expected)
        or set(actual) != set(expected)
    ):
        raise ValueError("startup_main_native_inventory_unbound")
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
        {_code_path(name): value for name, value in actual.items()},
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
