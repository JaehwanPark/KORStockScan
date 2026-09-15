import sys
import types


def _install_telebot_stub(monkeypatch):
    telebot_module = types.ModuleType("telebot")

    class DummyTeleBot:
        def __init__(self, token):
            self.token = token

        def message_handler(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def reply_to(self, *args, **kwargs):
            return None

        def send_message(self, *args, **kwargs):
            return None

        def __getattr__(self, name):
            if name.endswith("_handler"):

                def registrar(*args, **kwargs):
                    def decorator(func):
                        return func

                    return decorator

                return registrar
            raise AttributeError(name)

    telebot_module.TeleBot = DummyTeleBot
    telebot_module.logger = types.SimpleNamespace(setLevel=lambda *args, **kwargs: None)
    telebot_module.types = types.SimpleNamespace(
        ReplyKeyboardMarkup=lambda *args, **kwargs: types.SimpleNamespace(
            add=lambda *a, **k: None
        ),
        ChatMemberUpdated=object,
    )

    apihelper_module = types.ModuleType("telebot.apihelper")
    apihelper_module.ApiTelegramException = Exception

    db_manager_module = types.ModuleType("src.database.db_manager")

    class DummyDBManager:
        def __init__(self, *args, **kwargs):
            pass

    db_manager_module.DBManager = DummyDBManager

    market_regime_module = types.ModuleType("src.market_regime")
    market_regime_module.MarketRegimeService = object
    market_regime_module.summarize_market_regime_snapshot = lambda *args, **kwargs: {}

    kiwoom_utils_module = types.ModuleType("src.utils.kiwoom_utils")

    monkeypatch.setitem(sys.modules, "telebot", telebot_module)
    monkeypatch.setitem(sys.modules, "telebot.apihelper", apihelper_module)
    monkeypatch.setitem(sys.modules, "src.database.db_manager", db_manager_module)
    monkeypatch.setitem(sys.modules, "src.market_regime", market_regime_module)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", kiwoom_utils_module)


def test_main_keyboard_omits_donation_button(monkeypatch):
    _install_telebot_stub(monkeypatch)
    import src.notify.telegram_manager as telegram_manager

    rows = []
    monkeypatch.setattr(
        telegram_manager.types,
        "ReplyKeyboardMarkup",
        lambda *args, **kwargs: types.SimpleNamespace(
            add=lambda *buttons, **ignored: rows.append(buttons)
        ),
    )

    telegram_manager.get_main_keyboard(chat_id="not-admin")

    buttons = [button for row in rows for button in row]
    assert "☕ 서버 운영 후원하기" not in buttons
    assert "🤖 AI 확신지수란?" in buttons


def test_start_intro_uses_html_and_survives_database_error(monkeypatch):
    _install_telebot_stub(monkeypatch)
    import src.notify.telegram_manager as telegram_manager

    sent = []
    monkeypatch.setattr(
        telegram_manager.db_manager,
        "add_new_user",
        lambda chat_id: (_ for _ in ()).throw(RuntimeError("database unavailable")),
        raising=False,
    )
    monkeypatch.setattr(
        telegram_manager.bot,
        "send_message",
        lambda *args, **kwargs: sent.append((args, kwargs)),
    )
    monkeypatch.setattr(
        telegram_manager, "get_main_keyboard", lambda chat_id=None: "keyboard"
    )
    monkeypatch.setattr(telegram_manager, "log_error", lambda *args, **kwargs: None)

    class Chat:
        id = "not-admin"

    class Message:
        chat = Chat()

    telegram_manager.handle_start(Message())

    assert len(sent) == 1
    assert sent[0][1]["parse_mode"] == "HTML"
    assert sent[0][1]["reply_markup"] == "keyboard"


def test_ai_info_uses_current_auxiliary_role_and_html(monkeypatch):
    _install_telebot_stub(monkeypatch)
    import src.notify.telegram_manager as telegram_manager

    replies = []
    monkeypatch.setattr(
        telegram_manager.bot,
        "reply_to",
        lambda *args, **kwargs: replies.append((args, kwargs)),
    )

    telegram_manager.handle_ai_confidence_info(object())

    assert len(replies) == 1
    assert replies[0][1]["parse_mode"] == "HTML"
    assert "독자적으로 발급하지 않습니다" in replies[0][0][1]


def test_admin_buy_pause_confirm_invokes_guard(monkeypatch):
    _install_telebot_stub(monkeypatch)
    import src.notify.telegram_manager as telegram_manager

    replies = []
    broadcasts = []
    monkeypatch.setattr(
        telegram_manager.bot,
        "reply_to",
        lambda *args, **kwargs: replies.append((args, kwargs)),
    )
    monkeypatch.setattr(
        telegram_manager.event_bus,
        "publish",
        lambda *args, **kwargs: broadcasts.append((args, kwargs)),
    )
    monkeypatch.setattr(
        telegram_manager, "get_main_keyboard", lambda chat_id=None: None
    )
    monkeypatch.setattr(
        telegram_manager,
        "confirm_buy_pause_guard",
        lambda guard_id, event_bus=None: {
            "ok": True,
            "message": f"confirmed {guard_id}",
        },
    )

    class Chat:
        id = telegram_manager.ADMIN_ID

    class Message:
        chat = Chat()
        text = "/buy_pause_confirm BPG-20260409-1000-01"

    telegram_manager.cmd_buy_pause_confirm(Message())

    assert replies
    assert "confirmed BPG-20260409-1000-01" in replies[0][0][1]
    assert broadcasts


def test_non_admin_buy_pause_reject_is_rejected(monkeypatch):
    _install_telebot_stub(monkeypatch)
    import src.notify.telegram_manager as telegram_manager

    replies = []
    monkeypatch.setattr(
        telegram_manager.bot,
        "reply_to",
        lambda *args, **kwargs: replies.append((args, kwargs)),
    )
    monkeypatch.setattr(
        telegram_manager,
        "reject_buy_pause_guard",
        lambda guard_id: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    class Chat:
        id = "not-admin"

    class Message:
        chat = Chat()
        text = "/buy_pause_reject BPG-20260409-1000-01"

    telegram_manager.cmd_buy_pause_reject(Message())

    assert replies
    assert "권한이 없습니다." in replies[0][0][1]
