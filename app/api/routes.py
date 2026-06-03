from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas import (
    CsvBoxesUploadRequest,
    HealthResponse,
    ShipmentPlanningRequest,
    ShipmentPlanningResponse,
)
from app.services.csv_boxes import parse_boxes_csv
from app.services.shipment_planner import shipment_planner_service
from app.services.xlsx_export import build_planner_workbook

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/shipment-planner/boxes/upload")
async def shipment_planner_boxes_upload(request: CsvBoxesUploadRequest) -> dict:
    if not request.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Загрузите CSV файл.")
    if len(request.content.encode("utf-8")) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV слишком большой. Максимум 5 MB.")

    try:
        boxes = parse_boxes_csv(request.content.encode("utf-8"))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "source": "csv",
        "filename": request.filename,
        "count": len(boxes),
        "boxes": [box.model_dump() for box in boxes],
    }


def _build_plan_or_raise(request: ShipmentPlanningRequest) -> ShipmentPlanningResponse:
    if request.boxes is None:
        raise HTTPException(status_code=400, detail="Сначала загрузите CSV с коробками.")

    return shipment_planner_service.build_plan(
        boxes=request.boxes,
        vehicles=request.vehicles,
        min_total_amount=request.min_total_amount,
        min_fill_percent=request.min_fill_percent,
        max_fill_percent=request.max_fill_percent,
        allow_mixed_directions=False,
        distribution_mode=request.distribution_mode,
        sort_by_amount=request.sort_by_amount,
        sort_by_volume=request.sort_by_volume,
        sort_by_weight=request.sort_by_weight,
        source="shipment_planner",
    )


@router.post("/shipment-planner/plan", response_model=ShipmentPlanningResponse)
async def shipment_planner_plan(request: ShipmentPlanningRequest) -> ShipmentPlanningResponse:
    return _build_plan_or_raise(request)


@router.post("/shipment-planner/export")
async def shipment_planner_export(request: ShipmentPlanningRequest) -> Response:
    result = _build_plan_or_raise(request)
    workbook = build_planner_workbook(result)
    headers = {"Content-Disposition": 'attachment; filename="shipment-plan.xlsx"'}
    return Response(
        content=workbook,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
