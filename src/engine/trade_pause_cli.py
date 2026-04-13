from __future__ import annotations

import argparse
import json

from src.engine.trade_pause_control import get_pause_state_label, is_buy_side_paused, set_buy_side_pause


def _main() -> int:
    parser = argparse.ArgumentParser(description="Buy-side pause CLI helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pause_parser = subparsers.add_parser("pause", help="Pause new buy-side orders")
    pause_parser.add_argument("--source", default="codex_prompt")
    pause_parser.add_argument("--reason", default="")

    resume_parser = subparsers.add_parser("resume", help="Resume new buy-side orders")
    resume_parser.add_argument("--source", default="codex_prompt")
    resume_parser.add_argument("--reason", default="")

    subparsers.add_parser("status", help="Show pause status")

    args = parser.parse_args()
    if args.command == "pause":
        paused = set_buy_side_pause(True, source=args.source, reason=args.reason or None)
        print(
            json.dumps(
                {
                    "ok": True,
                    "command": "pause",
                    "paused": paused,
                    "label": get_pause_state_label(),
                    "source": args.source,
                    "reason": args.reason,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "resume":
        paused = set_buy_side_pause(False, source=args.source, reason=args.reason or None)
        print(
            json.dumps(
                {
                    "ok": True,
                    "command": "resume",
                    "paused": paused,
                    "label": get_pause_state_label(),
                    "source": args.source,
                    "reason": args.reason,
                },
                ensure_ascii=False,
            )
        )
        return 0

    print(
        json.dumps(
            {
                "ok": True,
                "command": "status",
                "paused": is_buy_side_paused(),
                "label": get_pause_state_label(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
