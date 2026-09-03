from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import paper_routes
from backend.app.services.paper_execution import PaperAccount


class MemoryPaperStore:
    def __init__(self):
        self.account = PaperAccount(initial_cash=100_000, fee_bps=0, slippage_bps=0)

    def get(self):
        return self.account

    def save(self):
        return self.account.snapshot()

    def reset(self, initial_cash):
        self.account = PaperAccount(initial_cash=initial_cash, fee_bps=0, slippage_bps=0)
        return self.account.snapshot()


def test_paper_api_end_to_end(monkeypatch):
    store = MemoryPaperStore()
    monkeypatch.setattr(paper_routes, "paper_store", store)
    client = TestClient(app)

    account = client.get("/api/paper/account")
    assert account.status_code == 200
    assert account.json()["cash"] == 100_000

    order = client.post(
        "/api/paper/order",
        json={"symbol": "PETR4", "side": "BUY", "quantity": 10, "reference_price": 40},
    )
    assert order.status_code == 200
    assert order.json()["status"] == "filled"

    mark = client.post("/api/paper/mark", json={"prices": {"PETR4": 45}})
    assert mark.status_code == 200
    assert mark.json()["equity"] == 100_050
    assert mark.json()["positions"]["PETR4"]["unrealized_pnl"] == 50

    sell = client.post(
        "/api/paper/order",
        json={"symbol": "PETR4", "side": "SELL", "quantity": 10, "reference_price": 45},
    )
    assert sell.status_code == 200
    assert client.get("/api/paper/account").json()["realized_pnl"] == 50


def test_paper_api_enforces_order_notional(monkeypatch):
    monkeypatch.setattr(paper_routes, "paper_store", MemoryPaperStore())
    client = TestClient(app)
    response = client.post(
        "/api/paper/order",
        json={"symbol": "PETR4", "side": "BUY", "quantity": 1000, "reference_price": 20},
    )
    assert response.status_code == 422
