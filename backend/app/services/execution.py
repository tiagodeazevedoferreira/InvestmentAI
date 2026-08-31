from .settings import get_settings, TradingMode
from .firebase import FirebaseRepository

settings = get_settings()

def build_firebase() -> FirebaseRepository:
    return FirebaseRepository(settings.firebase_database_url, settings.firebase_service_account)

def can_execute_live() -> tuple[bool, str]:
    if settings.trading_mode != TradingMode.LIVE:
        return False, "Trading mode is not live"
    if not settings.live_trading_enabled:
        return False, "Live trading is disabled"
    if not settings.model_approved:
        return False, "Model is not approved"
    if not settings.risk_gate_enabled:
        return False, "Risk gate is disabled"
    return True, "Live execution gate passed"
