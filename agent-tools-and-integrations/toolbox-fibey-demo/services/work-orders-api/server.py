import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).parent / "data" / "work_orders.json"

WorkOrderStatus = Literal["open", "in_progress", "completed", "cancelled"]
WorkOrderPriority = Literal["low", "medium", "high", "critical"]


class PartNeeded(BaseModel):
    part_id: str = Field(..., pattern=r"^FIB-\d{3}$")
    quantity: int = Field(..., ge=1)


class WorkOrder(BaseModel):
    id: str = Field(..., pattern=r"^WO-\d{3}$")
    title: str
    description: str
    status: WorkOrderStatus
    priority: WorkOrderPriority
    assigned_technician: str
    location: str
    parts_needed: list[PartNeeded] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    due_date: datetime


class WorkOrderCreate(BaseModel):
    title: str
    description: str
    status: WorkOrderStatus = "open"
    priority: WorkOrderPriority
    assigned_technician: str
    location: str
    parts_needed: list[PartNeeded] = Field(default_factory=list)
    due_date: datetime

    model_config = {"extra": "forbid"}


class WorkOrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: WorkOrderStatus | None = None
    priority: WorkOrderPriority | None = None
    assigned_technician: str | None = None
    location: str | None = None
    parts_needed: list[PartNeeded] | None = None
    due_date: datetime | None = None

    model_config = {"extra": "forbid"}


def load_work_orders() -> list[WorkOrder]:
    raw_orders = json.loads(DATA_PATH.read_text())
    return [WorkOrder.model_validate(order) for order in raw_orders]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.work_orders = load_work_orders()
    yield


app = FastAPI(title="Work Orders API", version="0.1.0", lifespan=lifespan)


def get_work_orders() -> list[WorkOrder]:
    return app.state.work_orders


def find_work_order(work_order_id: str) -> tuple[int, WorkOrder]:
    for index, work_order in enumerate(get_work_orders()):
        if work_order.id == work_order_id:
            return index, work_order
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")


def next_work_order_id() -> str:
    current_ids = [int(work_order.id.split("-")[1]) for work_order in get_work_orders()]
    next_id = max(current_ids, default=0) + 1
    return f"WO-{next_id:03d}"


@app.get("/health")
def health_check() -> dict[str, str | int]:
    return {"status": "ok", "work_order_count": len(get_work_orders())}


@app.get("/work-orders", response_model=list[WorkOrder])
def list_work_orders(
    status_filter: WorkOrderStatus | None = Query(default=None, alias="status"),
    priority: WorkOrderPriority | None = None,
    assigned_technician: str | None = None,
) -> list[WorkOrder]:
    work_orders = get_work_orders()

    if status_filter is not None:
        work_orders = [work_order for work_order in work_orders if work_order.status == status_filter]
    if priority is not None:
        work_orders = [work_order for work_order in work_orders if work_order.priority == priority]
    if assigned_technician is not None:
        work_orders = [
            work_order
            for work_order in work_orders
            if work_order.assigned_technician == assigned_technician
        ]

    return work_orders


@app.get("/work-orders/{work_order_id}", response_model=WorkOrder)
def get_work_order(work_order_id: str) -> WorkOrder:
    _, work_order = find_work_order(work_order_id)
    return work_order


@app.post("/work-orders", response_model=WorkOrder, status_code=status.HTTP_201_CREATED)
def create_work_order(payload: WorkOrderCreate) -> WorkOrder:
    now = datetime.now(UTC)
    work_order = WorkOrder(
        id=next_work_order_id(),
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    get_work_orders().append(work_order)
    return work_order


@app.patch("/work-orders/{work_order_id}", response_model=WorkOrder)
def update_work_order(work_order_id: str, payload: WorkOrderUpdate) -> WorkOrder:
    index, existing_work_order = find_work_order(work_order_id)
    updated_work_order = existing_work_order.model_copy(
        update={
            **payload.model_dump(exclude_unset=True),
            "updated_at": datetime.now(UTC),
        }
    )
    get_work_orders()[index] = updated_work_order
    return updated_work_order


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
