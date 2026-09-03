from fastapi import APIRouter, HTTPException
import pandas as pd

from ..models import (
    PaperAccountResponse, PaperAutomationRequest, PaperAutomationResponse,
    PaperMarkRequest, PaperOrderRequest, PaperResetRequest,
)
from ..services.paper_execution import PaperExecutionError
from ..services.paper_store import PaperAccountStore
from ..services.paper_automation import evaluate_paper_signal
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


@router.post("/automate", response_model=PaperAutomationResponse)
def paper_automate(req: PaperAutomationRequest):
    """Evaluate the current technical signal and optionally execute it in PAPER."""
    try:
        account = paper_store.get()
        frame = pd.DataFrame(req.bars)
        result = evaluate_paper_signal(
            account,
            req.symbol,
            frame,
            max_order_notional=settings.paper_max_order_notional,
            target_allocation=req.target_allocation,
            execute=req.execute,
        )
        if result.get("executed"):
            paper_store.save()
        return result
    except (ValueError, PaperExecutionError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
