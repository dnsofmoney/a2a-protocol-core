from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.fednow import FedNowAdapter
from app.adapters.internal_ledger import InternalLedgerAdapter
from app.adapters.xrpl import XRPLAdapter
from app.api.routes import router
from app.db.database import init_db
from app.services.payments import PaymentOrchestrator
from app.services.receipts import ReceiptStore
from app.services.registry import AgentRegistry
from app.services.reputation import ReputationService
from app.services.resolver import FASResolver


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    init_db()

    # Shared in-memory instances
    app.state.registry = AgentRegistry()
    app.state.resolver = FASResolver()  # seeds 3 aliases on init
    app.state.receipt_store = ReceiptStore()
    app.state.reputation_service = ReputationService()
    app.state.payment_results: dict = {}

    # Payment adapters
    adapters = {
        "XRPL": XRPLAdapter(),
        "FEDNOW": FedNowAdapter(),
        "INTERNAL_LEDGER": InternalLedgerAdapter(),
    }
    app.state.orchestrator = PaymentOrchestrator(
        resolver=app.state.resolver,
        adapters=adapters,
    )

    yield


app = FastAPI(
    title="A2A Protocol Core",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
