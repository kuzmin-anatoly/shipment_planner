from pathlib import Path

from app.schemas import VehicleSpec
from app.services.csv_boxes import parse_boxes_csv
from app.services.shipment_planner import shipment_planner_service


def test_uploaded_csv_example_has_fitting_boxes_for_40ft_container() -> None:
    csv_path = Path(r"C:\Users\a.kuzmin\Downloads\BOX.csv")
    boxes = parse_boxes_csv(csv_path.read_bytes())
    vehicle = VehicleSpec(
        name="40 ft",
        max_length=12.03,
        max_width=2.35,
        max_height=2.39,
        max_volume=67.7,
        max_weight=26500,
    )

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[vehicle],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="balanced",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert len(result.selected_boxes) > 0
    assert boxes[0].contractor
    assert boxes[0].direction_code
