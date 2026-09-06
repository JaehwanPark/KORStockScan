#!/usr/bin/env bash
set -euo pipefail

TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
echo "[SCALP_SIM_OVERNIGHT] RETIRED target_date=$TARGET_DATE retirement_id=scalping_overnight_retirement_20260906"
