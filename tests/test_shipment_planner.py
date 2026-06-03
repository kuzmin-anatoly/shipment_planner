from app.schemas import BoxItem, VehicleSpec
from app.services.shipment_planner import shipment_planner_service


def make_vehicle(name: str = "Truck", volume: float = 25, weight: float = 500, direction: str = "") -> VehicleSpec:
    return VehicleSpec(
        name=name,
        direction=direction,
        max_length=3,
        max_width=3,
        max_height=3,
        max_volume=volume,
        max_weight=weight,
    )


def test_free_mode_keeps_single_direction_when_mixing_disabled() -> None:
    boxes = [
        BoxItem(name="A1", amount=1000, volume=10, length=1, width=1, height=1, weight=100, direction="KZ"),
        BoxItem(name="A2", amount=900, volume=10, length=1, width=1, height=1, weight=100, direction="KZ"),
        BoxItem(name="B1", amount=1500, volume=8, length=1, width=1, height=1, weight=80, direction="UZ"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle()],
        min_total_amount=1800,
        min_fill_percent=60,
        allow_mixed_directions=False,
        distribution_mode="free",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert result.success is True
    assert {box.direction for box in result.selected_boxes} == {"KZ"}


def test_free_mode_splits_across_multiple_containers() -> None:
    boxes = [
        BoxItem(name="A", amount=1000, volume=8, length=1, width=1, height=1, weight=100, direction="SEA"),
        BoxItem(name="B", amount=1000, volume=8, length=1, width=1, height=1, weight=100, direction="SEA"),
        BoxItem(name="C", amount=1000, volume=8, length=1, width=1, height=1, weight=100, direction="SEA"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle("C1", 10, 500), make_vehicle("C2", 10, 500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="free",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert result.used_containers == 2
    assert len(result.selected_boxes) == 2
    assert len(result.excluded_boxes) == 1


def test_free_mode_without_mixing_distributes_different_directions_between_containers() -> None:
    boxes = [
        BoxItem(name="KZ-1", amount=1200, volume=8, length=1, width=1, height=1, weight=100, direction="KZ"),
        BoxItem(name="KZ-2", amount=1100, volume=8, length=1, width=1, height=1, weight=100, direction="KZ"),
        BoxItem(name="UZ-1", amount=900, volume=8, length=1, width=1, height=1, weight=100, direction="UZ"),
        BoxItem(name="UZ-2", amount=850, volume=8, length=1, width=1, height=1, weight=100, direction="UZ"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle("C1", 10, 500), make_vehicle("C2", 10, 500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=False,
        distribution_mode="free",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    non_empty_plans = [plan for plan in result.container_plans if plan.metrics.total_boxes > 0]
    assert len(non_empty_plans) == 2
    assert {next(iter(plan.direction_summary)) for plan in non_empty_plans} == {"KZ", "UZ"}


def test_balanced_mode_distributes_evenly_between_containers() -> None:
    boxes = [
        BoxItem(name="A", amount=1000, volume=4, length=1, width=1, height=1, weight=40, direction="SEA"),
        BoxItem(name="B", amount=950, volume=4, length=1, width=1, height=1, weight=40, direction="SEA"),
        BoxItem(name="C", amount=900, volume=4, length=1, width=1, height=1, weight=40, direction="SEA"),
        BoxItem(name="D", amount=850, volume=4, length=1, width=1, height=1, weight=40, direction="SEA"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle("C1", 12, 500), make_vehicle("C2", 12, 500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="balanced",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    counts = [plan.metrics.total_boxes for plan in result.container_plans]
    assert counts == [2, 2]
    assert result.used_containers == 2


def test_balanced_mode_without_mixing_spreads_directions_across_containers() -> None:
    boxes = [
        BoxItem(name="KZ-1", amount=1200, volume=4, length=1, width=1, height=1, weight=40, direction="KZ"),
        BoxItem(name="KZ-2", amount=1100, volume=4, length=1, width=1, height=1, weight=40, direction="KZ"),
        BoxItem(name="UZ-1", amount=900, volume=4, length=1, width=1, height=1, weight=40, direction="UZ"),
        BoxItem(name="UZ-2", amount=850, volume=4, length=1, width=1, height=1, weight=40, direction="UZ"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle("C1", 12, 500), make_vehicle("C2", 12, 500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=False,
        distribution_mode="balanced",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    non_empty_plans = [plan for plan in result.container_plans if plan.metrics.total_boxes > 0]
    assert len(non_empty_plans) == 2
    assert {next(iter(plan.direction_summary)) for plan in non_empty_plans} == {"KZ", "UZ"}


def test_vehicle_direction_filters_assignments() -> None:
    boxes = [
        BoxItem(name="KZ-1", amount=1200, volume=4, length=1, width=1, height=1, weight=40, direction="KZ"),
        BoxItem(name="KZ-2", amount=1100, volume=4, length=1, width=1, height=1, weight=40, direction="KZ"),
        BoxItem(name="UZ-1", amount=900, volume=4, length=1, width=1, height=1, weight=40, direction="UZ"),
        BoxItem(name="UZ-2", amount=850, volume=4, length=1, width=1, height=1, weight=40, direction="UZ"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle("KZ container", 12, 500, "KZ"), make_vehicle("UZ container", 12, 500, "UZ")],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="free",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert [plan.vehicle.direction for plan in result.container_plans] == ["KZ", "UZ"]
    assert {box.direction for box in result.container_plans[0].selected_boxes} == {"KZ"}
    assert {box.direction for box in result.container_plans[1].selected_boxes} == {"UZ"}


def test_balanced_mode_respects_centimeter_box_dimensions() -> None:
    boxes = [
        BoxItem(name="CM-BOX", amount=1000, volume=1, length=160, width=14, height=130, weight=23, direction="SEA"),
    ]
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

    assert result.success is True
    assert len(result.selected_boxes) == 1


def test_container_threshold_warning_is_reported() -> None:
    boxes = [
        BoxItem(name="OnlyBox", amount=800, volume=10, length=1, width=1, height=1, weight=100, direction="RU"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle(volume=20, weight=500)],
        min_total_amount=1000,
        min_fill_percent=60,
        allow_mixed_directions=True,
        distribution_mode="free",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert result.success is False
    assert any("стоимости" in warning or "загрузки" in warning for warning in result.warnings)


def test_sort_score_respects_disabled_sort_dimensions() -> None:
    boxes = [
        BoxItem(name="A", amount=1000, volume=3, length=1, width=1, height=1, weight=50, direction="SEA"),
        BoxItem(name="B", amount=400, volume=6, length=1, width=1, height=1, weight=90, direction="SEA"),
        BoxItem(name="C", amount=700, volume=2, length=1, width=1, height=1, weight=30, direction="SEA"),
    ]

    full = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle(volume=20, weight=500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="balanced",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )
    amount_disabled = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle(volume=20, weight=500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="balanced",
        sort_by_amount=False,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    full_scores = {box.name: box.sort_score for box in full.selected_boxes}
    disabled_scores = {box.name: box.sort_score for box in amount_disabled.selected_boxes}

    assert full_scores != disabled_scores
    assert any(box.cost_segment == "Off" for box in amount_disabled.selected_boxes)


def test_free_mode_selection_order_follows_active_sort_score() -> None:
    boxes = [
        BoxItem(name="AmountFirst", amount=1000, volume=1, length=1, width=1, height=1, weight=10, direction="SEA"),
        BoxItem(name="VolumeWeightFirst", amount=100, volume=10, length=1, width=1, height=1, weight=100, direction="SEA"),
    ]

    by_all = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle(volume=50, weight=500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="free",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )
    without_amount = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle(volume=50, weight=500)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="free",
        sort_by_amount=False,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert by_all.selected_boxes[0].name == "AmountFirst"
    assert without_amount.selected_boxes[0].name == "VolumeWeightFirst"


def test_container_metrics_include_weight_percent() -> None:
    boxes = [
        BoxItem(name="A", amount=500, volume=4, length=1, width=1, height=1, weight=100, direction="SEA"),
        BoxItem(name="B", amount=500, volume=4, length=1, width=1, height=1, weight=50, direction="SEA"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle(volume=20, weight=200)],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=True,
        distribution_mode="balanced",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert result.container_plans[0].metrics.total_weight == 150
    assert result.container_plans[0].metrics.weight_percent == 75


def test_all_mode_returns_sorted_boxes_without_container_split() -> None:
    boxes = [
        BoxItem(name="Low", amount=100, volume=1, length=1, width=1, height=1, weight=10, direction="SEA"),
        BoxItem(name="High", amount=1000, volume=1, length=1, width=1, height=1, weight=10, direction="SEA"),
        BoxItem(name="Mid", amount=500, volume=1, length=1, width=1, height=1, weight=10, direction="SEA"),
    ]

    result = shipment_planner_service.build_plan(
        boxes=boxes,
        vehicles=[make_vehicle("ALL", 1, 1, "")],
        min_total_amount=0,
        min_fill_percent=0,
        allow_mixed_directions=False,
        distribution_mode="all",
        sort_by_amount=True,
        sort_by_volume=True,
        sort_by_weight=True,
        source="test",
    )

    assert result.distribution_mode == "all"
    assert result.container_plans == []
    assert [box.name for box in result.selected_boxes] == ["High", "Mid", "Low"]
