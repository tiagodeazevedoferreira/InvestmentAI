from fastapi import APIRouter, HTTPException

from ..models import PaperAccountResponse, PaperMarkRequest, PaperOrderRequest, PaperResetRequest
from ..services.paper_execution import PaperExecutionError
from ..services.paper_store import PaperAccountStore
from ..settings import get_settings

router = APIRouter(prefix="/paper", tags=["paper-trading"])
settings = get_settings()
paper_store = PaperAccountStore()


@router.get("/account", response_model=PaperAccountResponse)
def paper_account():
    try:
        return paper_store.get().snapshot()
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/order")
def paper_order(req: PaperOrderRequest):
    reference_notional = req.quantity * req.reference_price
    if reference_notional > settings.paper_max_order_notional:
        raise HTTPException(
            status_code=422,
            detail=f"paper order notional exceeds limit of {settings.paper_max_order_notional}",
        )
    try:
        account = paper_store.get()
        result = account.submit_order(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            reference_price=req.reference_price,
            order_type=req.order_type,
            limit_price=req.limit_price,
            reason=req.reason,
        )
        paper_store.save()
        return result
    except (ValueError, PaperExecutionError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/mark", response_model=PaperAccountResponse)
def paper_mark(req: PaperMarkRequest):
    try:
        account = paper_store.get()
        snapshot = account.mark_to_market(req.prices)
        paper_store.save()
        return snapshot
    except (ValueError, PaperExecutionError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/reset", response_model=PaperAccountResponse)
def paper_reset(req: PaperResetRequest):
    try:
        return paper_store.reset(req.initial_cash)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
