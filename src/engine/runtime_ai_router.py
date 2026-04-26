import os
import socket
from typing import Any

from src.utils.logger import log_info


def resolve_runtime_role() -> str:
    """Return runtime role: main (default) or remote."""
    host = socket.gethostname().strip().lower()
    remote_host_hints = ("remote", "windy", "songstockscan", "korstock-test-server")
    host_looks_remote = any(token in host for token in remote_host_hints)

    # Safety-first default for known remote hosts unless explicitly forced.
    force_main_on_remote = str(os.getenv("KORSTOCKSCAN_FORCE_MAIN_ON_REMOTE", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    explicit = str(os.getenv("KORSTOCKSCAN_RUNTIME_ROLE", "") or "").strip().lower()
    if explicit in {"main", "remote"}:
        if explicit == "main" and host_looks_remote and not force_main_on_remote:
            log_info("[AI_ROUTER] override main->remote on known remote host")
            return "remote"
        return explicit

    latency_profile = str(os.getenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "") or "").strip().lower()
    if "remote" in latency_profile:
        return "remote"

    if host_looks_remote:
        return "remote"
    return "main"


def resolve_scalping_ai_route() -> str:
    """Return live scalping AI route: gemini (main default), deepseek (remote default), or openai."""
    explicit = str(os.getenv("KORSTOCKSCAN_SCALPING_AI_ROUTE", "") or "").strip().lower()
    if explicit in {"gemini", "openai", "deepseek"}:
        return explicit

    if resolve_runtime_role() == "remote":
        return "deepseek"
    return "gemini"


class RuntimeAIEngineRouter:
    """
    Runtime router:
    - openai route + main role: scalping analyze_target -> OpenAI engine
    - deepseek route + remote role: scalping analyze_target -> DeepSeek engine
    - fallback route: Gemini engine when the preferred engine is unavailable
    """

    def __init__(
        self,
        *,
        gemini_engine: Any = None,
        openai_scalping_engine: Any = None,
        deepseek_scalping_engine: Any = None,
        runtime_role: str = "main",
        scalping_ai_route: str = "gemini",
    ):
        self.gemini_engine = gemini_engine
        self.openai_scalping_engine = openai_scalping_engine
        self.deepseek_scalping_engine = deepseek_scalping_engine
        self.runtime_role = str(runtime_role or "main").strip().lower()
        self.scalping_ai_route = str(scalping_ai_route or "gemini").strip().lower()

        openai_enabled = (
            self.scalping_ai_route == "openai"
            and self.runtime_role == "main"
            and self.openai_scalping_engine is not None
        )
        deepseek_enabled = (
            self.scalping_ai_route == "deepseek"
            and self.runtime_role == "remote"
            and self.deepseek_scalping_engine is not None
        )
        log_info(
            f"[AI_ROUTER] role={self.runtime_role} "
            f"scalping_route={self.scalping_ai_route} "
            f"scalping_openai={'on' if openai_enabled else 'off'} "
            f"scalping_deepseek={'on' if deepseek_enabled else 'off'}"
        )

    def _is_scalping_strategy(self, strategy: Any) -> bool:
        return str(strategy or "SCALPING").strip().upper() in {"SCALPING", "SCALP"}

    def _should_use_openai_scalping(self, *, strategy: Any) -> bool:
        return (
            self.scalping_ai_route == "openai"
            and self.runtime_role == "main"
            and self.openai_scalping_engine is not None
            and self._is_scalping_strategy(strategy)
        )

    def _should_use_deepseek_scalping(self, *, strategy: Any) -> bool:
        return (
            self.scalping_ai_route == "deepseek"
            and self.runtime_role == "remote"
            and self.deepseek_scalping_engine is not None
            and self._is_scalping_strategy(strategy)
        )

    def _fallback_scalping_engine(self):
        for engine in (self.gemini_engine, self.deepseek_scalping_engine, self.openai_scalping_engine):
            if engine is not None:
                return engine
        raise RuntimeError("No AI engine available for live scalping route")

    def _selected_scalping_engine(self, strategy: Any):
        if self._should_use_deepseek_scalping(strategy=strategy):
            return self.deepseek_scalping_engine
        if self._should_use_openai_scalping(strategy=strategy):
            return self.openai_scalping_engine
        return self._fallback_scalping_engine()

    def analyze_target(
        self,
        target_name,
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        program_net_qty=0,
        cache_profile="default",
        prompt_profile="shared",
    ):
        engine = self._selected_scalping_engine(strategy=strategy)
        return engine.analyze_target(
            target_name,
            ws_data,
            recent_ticks,
            recent_candles,
            strategy=strategy,
            program_net_qty=program_net_qty,
            cache_profile=cache_profile,
            prompt_profile=prompt_profile,
        )

    def generate_realtime_report(self, *args, **kwargs):
        return self._selected_scalping_engine(strategy="SCALPING").generate_realtime_report(*args, **kwargs)

    def analyze_target_shadow_prompt(self, *args, **kwargs):
        engine = self._selected_scalping_engine(strategy="SCALPING")
        if hasattr(engine, "analyze_target_shadow_prompt"):
            return engine.analyze_target_shadow_prompt(*args, **kwargs)
        if hasattr(self.gemini_engine, "analyze_target_shadow_prompt"):
            return self.gemini_engine.analyze_target_shadow_prompt(*args, **kwargs)
        return {"action": "WAIT", "score": 50, "reason": "shadow unsupported"}

    def _extract_scalping_features(self, *args, **kwargs):
        engine = self._selected_scalping_engine(strategy="SCALPING")
        if hasattr(engine, "_extract_scalping_features"):
            return engine._extract_scalping_features(*args, **kwargs)
        return {}

    def __getattr__(self, name: str):
        selected = self._selected_scalping_engine(strategy="SCALPING")
        if hasattr(selected, name):
            return getattr(selected, name)
        if hasattr(self.gemini_engine, name):
            return getattr(self.gemini_engine, name)
        if self.deepseek_scalping_engine is not None and hasattr(self.deepseek_scalping_engine, name):
            return getattr(self.deepseek_scalping_engine, name)
        if self.openai_scalping_engine is not None and hasattr(self.openai_scalping_engine, name):
            return getattr(self.openai_scalping_engine, name)
        raise AttributeError(name)
