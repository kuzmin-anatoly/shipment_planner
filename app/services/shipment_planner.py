from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.schemas import (
    BoxItem,
    ContainerPlan,
    PlannedBoxItem,
    ShipmentPlanningMetrics,
    ShipmentPlanningResponse,
    VehicleSpec,
)


@dataclass
class ScoredBox:
    box: BoxItem
    planned: PlannedBoxItem


@dataclass
class PlanningCandidate:
    selected: list[ScoredBox]
    excluded: list[ScoredBox]
    warnings: list[str]
    vehicle: VehicleSpec

    def metrics(self) -> ShipmentPlanningMetrics:
        return ShipmentPlannerService.metrics_for_boxes(
            [item.planned for item in self.selected],
            self.vehicle.max_volume,
            self.vehicle.max_weight,
        )


@dataclass
class ContainerState:
    container_no: int
    vehicle: VehicleSpec
    selected_boxes: list[ScoredBox] = field(default_factory=list)
    assigned_direction: str | None = None

    @property
    def total_volume(self) -> float:
        return sum(item.box.volume for item in self.selected_boxes)

    @property
    def total_weight(self) -> float:
        return sum(item.box.weight for item in self.selected_boxes)

    @property
    def total_amount(self) -> float:
        return sum(item.box.amount for item in self.selected_boxes)


class ShipmentPlannerService:
    def build_plan(
        self,
        boxes: list[BoxItem],
        vehicles: list[VehicleSpec],
        min_total_amount: float,
        min_fill_percent: float,
        allow_mixed_directions: bool,
        distribution_mode: str,
        sort_by_amount: bool,
        sort_by_volume: bool,
        sort_by_weight: bool,
        source: str,
    ) -> ShipmentPlanningResponse:
        if not boxes:
            return ShipmentPlanningResponse(
                success=False,
                source=source,
                distribution_mode=distribution_mode,
                total_containers=len(vehicles),
                warnings=["Не найдено коробок для планирования партии."],
            )
        if not vehicles:
            return ShipmentPlanningResponse(
                success=False,
                source=source,
                distribution_mode=distribution_mode,
                total_containers=0,
                warnings=["Не добавлено ни одного контейнера."],
            )

        vehicles = self._resolve_vehicle_directions(boxes, vehicles)

        scored_boxes = self._score_boxes(
            boxes,
            sort_by_amount=sort_by_amount,
            sort_by_volume=sort_by_volume,
            sort_by_weight=sort_by_weight,
        )
        if distribution_mode == "all":
            return self._build_all_plan(
                scored_boxes=scored_boxes,
                vehicles=vehicles,
                min_total_amount=min_total_amount,
                min_fill_percent=min_fill_percent,
                source=source,
            )
        if distribution_mode == "balanced":
            return self._build_balanced_plan(
                scored_boxes=scored_boxes,
                vehicles=vehicles,
                min_total_amount=min_total_amount,
                min_fill_percent=min_fill_percent,
                allow_mixed_directions=allow_mixed_directions,
                source=source,
            )
        return self._build_free_plan(
            scored_boxes=scored_boxes,
            vehicles=vehicles,
            min_total_amount=min_total_amount,
            min_fill_percent=min_fill_percent,
            allow_mixed_directions=allow_mixed_directions,
            source=source,
        )

    def _build_all_plan(
        self,
        scored_boxes: list[ScoredBox],
        vehicles: list[VehicleSpec],
        min_total_amount: float,
        min_fill_percent: float,
        source: str,
    ) -> ShipmentPlanningResponse:
        selected_boxes = [item.planned for item in sorted(scored_boxes, key=self._sort_priority, reverse=True)]
        metrics = self.metrics_for_boxes(selected_boxes, max_volume=0, max_weight=0)
        warnings: list[str] = []
        if metrics.total_amount < min_total_amount:
            warnings.append("Режим ALL не достиг минимальной стоимости.")
        if min_fill_percent > 0:
            warnings.append("Режим ALL не использует контейнерную загрузку, поэтому процент заполнения не рассчитывается.")
        success = metrics.total_amount >= min_total_amount
        return ShipmentPlanningResponse(
            success=success,
            source=source,
            metrics=metrics,
            distribution_mode="all",
            total_containers=0,
            used_containers=0,
            container_plans=[],
            selected_boxes=selected_boxes,
            excluded_boxes=[],
            warnings=warnings,
            direction_summary=dict(Counter(item.direction for item in selected_boxes)),
        )

    def _resolve_vehicle_directions(self, boxes: list[BoxItem], vehicles: list[VehicleSpec]) -> list[VehicleSpec]:
        available_directions: list[str] = []
        seen: set[str] = set()
        for box in boxes:
            direction = self._normalized_direction(box.direction)
            if direction and direction not in seen:
                seen.add(direction)
                available_directions.append(direction)

        if not available_directions:
            return vehicles

        resolved: list[VehicleSpec] = []
        direction_index = 0
        for vehicle in vehicles:
            vehicle_direction = self._normalized_direction(vehicle.direction)
            if not vehicle_direction:
                vehicle_direction = available_directions[direction_index % len(available_directions)]
                direction_index += 1
            resolved.append(vehicle.model_copy(update={"direction": vehicle_direction}))
        return resolved

    def _score_boxes(
        self,
        boxes: list[BoxItem],
        sort_by_amount: bool,
        sort_by_volume: bool,
        sort_by_weight: bool,
    ) -> list[ScoredBox]:
        amounts = [box.amount for box in boxes]
        weights = [box.weight for box in boxes]
        volumes = [box.volume for box in boxes]
        amount_low, amount_high = self._thresholds(amounts)
        weight_low, weight_high = self._thresholds(weights)
        volume_low, volume_high = self._thresholds(volumes)

        scored: list[ScoredBox] = []
        for box in boxes:
            cost_segment, cost_score = self._segment_value(box.amount, amount_low, amount_high)
            weight_segment, weight_score = self._segment_value(box.weight, weight_low, weight_high)
            volume_segment, volume_score = self._segment_value(box.volume, volume_low, volume_high)
            segment_parts = [
                f"C:{cost_segment if sort_by_amount else 'Off'}",
                f"W:{weight_segment if sort_by_weight else 'Off'}",
                f"V:{volume_segment if sort_by_volume else 'Off'}",
            ]
            sort_score = round(
                (cost_score * 100 if sort_by_amount else 0)
                + (weight_score * 10 if sort_by_weight else 0)
                + (volume_score if sort_by_volume else 0),
                3,
            )
            planned = PlannedBoxItem(
                **box.model_dump(),
                segment=" / ".join(segment_parts),
                cost_segment=cost_segment if sort_by_amount else "Off",
                weight_segment=weight_segment if sort_by_weight else "Off",
                volume_segment=volume_segment if sort_by_volume else "Off",
                sort_score=sort_score,
            )
            scored.append(ScoredBox(box=box, planned=planned))
        return scored

    def _thresholds(self, values: list[float]) -> tuple[float, float]:
        ordered = sorted(values)
        if not ordered:
            return 0, 0
        low = ordered[len(ordered) // 3]
        high = ordered[(len(ordered) * 2) // 3]
        return low, high

    def _segment_value(self, value: float, low: float, high: float) -> tuple[str, int]:
        if value >= high:
            return "High", 3
        if value >= low:
            return "Mid", 2
        return "Low", 1

    def _build_balanced_plan(
        self,
        scored_boxes: list[ScoredBox],
        vehicles: list[VehicleSpec],
        min_total_amount: float,
        min_fill_percent: float,
        allow_mixed_directions: bool,
        source: str,
    ) -> ShipmentPlanningResponse:
        states = [
            ContainerState(
                container_no=index + 1,
                vehicle=vehicle,
                assigned_direction=self._normalized_direction(vehicle.direction) or None,
            )
            for index, vehicle in enumerate(vehicles)
        ]
        oversized: list[ScoredBox] = []
        distributable: list[ScoredBox] = []
        for item in scored_boxes:
            if any(self._vehicle_accepts_box(state.vehicle, item.box) for state in states):
                distributable.append(item)
            else:
                oversized.append(item)

        ordered_boxes = sorted(distributable, key=self._sort_priority, reverse=True)
        unassigned: list[ScoredBox] = []
        for item in ordered_boxes:
            candidates = [state for state in states if self._can_place_box(state, item)]
            if not candidates:
                unassigned.append(item)
                continue
            best_state = min(candidates, key=lambda state: self._balanced_container_rank(state))
            best_state.selected_boxes.append(item)
            if best_state.assigned_direction is None:
                best_state.assigned_direction = item.box.direction

        return self._response_from_states(
            states=states,
            oversized=oversized,
            leftover=unassigned,
            min_total_amount=min_total_amount,
            min_fill_percent=min_fill_percent,
            distribution_mode="balanced",
            source=source,
        )

    def _build_free_plan(
        self,
        scored_boxes: list[ScoredBox],
        vehicles: list[VehicleSpec],
        min_total_amount: float,
        min_fill_percent: float,
        allow_mixed_directions: bool,
        source: str,
    ) -> ShipmentPlanningResponse:
        remaining = list(scored_boxes)
        oversized_global: list[ScoredBox] = []
        states: list[ContainerState] = []
        used_directions: set[str] = set()

        for index, vehicle in enumerate(vehicles, start=1):
            fitting = [item for item in remaining if self._vehicle_accepts_box(vehicle, item.box)]
            if fitting:
                candidate = self._build_best_candidate(
                    fitting_boxes=fitting,
                    vehicle=vehicle,
                    min_total_amount=min_total_amount,
                    min_fill_percent=min_fill_percent,
                    allow_mixed_directions=allow_mixed_directions,
                )
                if candidate.selected:
                    used_directions.add(candidate.selected[0].box.direction)
            else:
                candidate = PlanningCandidate(selected=[], excluded=[], warnings=[], vehicle=vehicle)
            states.append(
                ContainerState(
                    container_no=index,
                    vehicle=vehicle,
                    selected_boxes=candidate.selected,
                    assigned_direction=self._normalized_direction(vehicle.direction)
                    or (candidate.selected[0].box.direction if candidate.selected else None),
                )
            )
            selected_ids = {id(item.box) for item in candidate.selected}
            remaining = [item for item in remaining if id(item.box) not in selected_ids]

        oversized_global = [item for item in remaining if not any(self._vehicle_accepts_box(vehicle, item.box) for vehicle in vehicles)]
        leftover = [item for item in remaining if item not in oversized_global]

        return self._response_from_states(
            states=states,
            oversized=oversized_global,
            leftover=leftover,
            min_total_amount=min_total_amount,
            min_fill_percent=min_fill_percent,
            distribution_mode="free",
            source=source,
        )

    def _response_from_states(
        self,
        states: list[ContainerState],
        oversized: list[ScoredBox],
        leftover: list[ScoredBox],
        min_total_amount: float,
        min_fill_percent: float,
        distribution_mode: str,
        source: str,
    ) -> ShipmentPlanningResponse:
        plans: list[ContainerPlan] = []
        warnings = self._base_warnings(oversized)
        used_states = [state for state in states if state.selected_boxes]

        for state in states:
            metrics = self.metrics_for_boxes(
                [item.planned for item in state.selected_boxes],
                state.vehicle.max_volume,
                state.vehicle.max_weight,
            )
            success = (
                metrics.total_boxes > 0
                and metrics.total_amount >= min_total_amount
                and metrics.fill_percent >= min_fill_percent
            )
            plan_warnings: list[str] = []
            if metrics.total_boxes == 0:
                plan_warnings.append("Контейнер остался пустым.")
            if metrics.total_boxes > 0 and metrics.total_amount < min_total_amount:
                plan_warnings.append("Контейнер не достиг минимальной стоимости.")
            if metrics.total_boxes > 0 and metrics.fill_percent < min_fill_percent:
                plan_warnings.append("Контейнер не достиг минимальной загрузки.")
            plans.append(
                ContainerPlan(
                    container_no=state.container_no,
                    vehicle=state.vehicle,
                    success=success,
                    metrics=metrics,
                    selected_boxes=[item.planned for item in state.selected_boxes],
                    direction_summary=dict(Counter(item.box.direction for item in state.selected_boxes)),
                    warnings=plan_warnings,
                )
            )

        selected_boxes = [item.planned for state in used_states for item in state.selected_boxes]
        total_volume_capacity = sum(state.vehicle.max_volume for state in used_states) or sum(state.vehicle.max_volume for state in states)
        total_weight_capacity = sum(state.vehicle.max_weight for state in used_states) or sum(state.vehicle.max_weight for state in states)
        overall_metrics = self.metrics_for_boxes(selected_boxes, total_volume_capacity, total_weight_capacity) if states else None
        if leftover:
            warnings.append(f"После распределения осталось вне плана коробок: {len(leftover)}.")
        for plan in plans:
            for warning in plan.warnings:
                if warning not in warnings:
                    warnings.append(warning)

        success = bool(used_states) and all(plan.success for plan in plans if plan.metrics.total_boxes > 0)
        return ShipmentPlanningResponse(
            success=success,
            source=source,
            metrics=overall_metrics,
            distribution_mode=distribution_mode,
            total_containers=len(states),
            used_containers=len(used_states),
            container_plans=plans,
            selected_boxes=selected_boxes,
            excluded_boxes=[item.planned for item in oversized + leftover],
            warnings=warnings,
            direction_summary=dict(Counter(item.direction for item in selected_boxes)),
        )

    def _build_best_candidate(
        self,
        fitting_boxes: list[ScoredBox],
        vehicle: VehicleSpec,
        min_total_amount: float,
        min_fill_percent: float,
        allow_mixed_directions: bool,
    ) -> PlanningCandidate:
        return self._build_candidate(fitting_boxes, vehicle, min_total_amount, min_fill_percent, [])

    def _build_best_direction_candidate(
        self,
        fitting_boxes: list[ScoredBox],
        vehicle: VehicleSpec,
        min_total_amount: float,
        min_fill_percent: float,
        used_directions: set[str],
    ) -> PlanningCandidate:
        ranked_candidates: list[tuple[tuple[int, int, float, float, float], PlanningCandidate]] = []
        for direction in self._direction_priority(fitting_boxes):
            same_direction = [item for item in fitting_boxes if item.box.direction == direction]
            other = [item for item in fitting_boxes if item.box.direction != direction]
            candidate = self._build_candidate(
                same_direction,
                vehicle,
                min_total_amount,
                min_fill_percent,
                [],
                other,
            )
            metrics = candidate.metrics()
            fresh_direction_bonus = int(direction not in used_directions)
            viable_bonus = int(metrics.total_boxes > 0)
            rank = (fresh_direction_bonus, viable_bonus, metrics.total_amount, metrics.fill_percent, -metrics.total_weight)
            ranked_candidates.append((rank, candidate))
        return max(ranked_candidates, key=lambda item: item[0])[1] if ranked_candidates else PlanningCandidate(selected=[], excluded=[], warnings=[], vehicle=vehicle)

    def _build_candidate(
        self,
        boxes: list[ScoredBox],
        vehicle: VehicleSpec,
        min_total_amount: float,
        min_fill_percent: float,
        warnings: list[str],
        excluded_seed: list[ScoredBox] | None = None,
    ) -> PlanningCandidate:
        ordered = sorted(boxes, key=self._sort_priority, reverse=True)
        selected, excluded = self._greedy_pick(ordered, vehicle)
        improved = self._fill_remaining_capacity(selected, boxes, vehicle)
        improved_rank = self._selection_rank(improved, vehicle, min_total_amount, min_fill_percent)
        selected_rank = self._selection_rank(selected, vehicle, min_total_amount, min_fill_percent)
        if improved_rank > selected_rank:
            selected = improved
            excluded = [item for item in boxes if item not in improved]
        return PlanningCandidate(selected=selected, excluded=list(excluded_seed or []) + excluded, warnings=warnings, vehicle=vehicle)

    def _greedy_pick(self, boxes: list[ScoredBox], vehicle: VehicleSpec) -> tuple[list[ScoredBox], list[ScoredBox]]:
        selected: list[ScoredBox] = []
        excluded: list[ScoredBox] = []
        total_volume = 0.0
        total_weight = 0.0
        for item in boxes:
            if total_volume + item.box.volume <= vehicle.max_volume and total_weight + item.box.weight <= vehicle.max_weight:
                selected.append(item)
                total_volume += item.box.volume
                total_weight += item.box.weight
            else:
                excluded.append(item)
        return selected, excluded

    def _fill_remaining_capacity(self, selected: list[ScoredBox], boxes: list[ScoredBox], vehicle: VehicleSpec) -> list[ScoredBox]:
        selected_ids = {id(item.box) for item in selected}
        total_volume = sum(item.box.volume for item in selected)
        total_weight = sum(item.box.weight for item in selected)
        improved = list(selected)
        remainder = sorted(
            [item for item in boxes if id(item.box) not in selected_ids],
            key=self._sort_priority,
            reverse=True,
        )
        for item in remainder:
            if total_volume + item.box.volume <= vehicle.max_volume and total_weight + item.box.weight <= vehicle.max_weight:
                improved.append(item)
                total_volume += item.box.volume
                total_weight += item.box.weight
        return improved

    def _round_robin_by_direction(self, boxes: list[ScoredBox]) -> list[ScoredBox]:
        direction_groups: dict[str, list[ScoredBox]] = {}
        for direction in self._direction_priority(boxes):
            direction_groups[direction] = sorted(
                [item for item in boxes if item.box.direction == direction],
                key=self._sort_priority,
                reverse=True,
            )

        ordered: list[ScoredBox] = []
        while any(direction_groups.values()):
            for direction in list(direction_groups.keys()):
                group = direction_groups[direction]
                if group:
                    ordered.append(group.pop(0))
        return ordered

    def _direction_priority(self, boxes: list[ScoredBox]) -> list[str]:
        totals: dict[str, tuple[float, float, float, float]] = {}
        for item in boxes:
            score, amount, volume, weight = totals.get(item.box.direction, (0.0, 0.0, 0.0, 0.0))
            totals[item.box.direction] = (
                score + item.planned.sort_score,
                amount + item.box.amount,
                volume + item.box.volume,
                weight + item.box.weight,
            )
        return sorted(
            totals.keys(),
            key=lambda direction: totals[direction],
            reverse=True,
        )

    def _normalized_direction(self, direction: str | None) -> str:
        return (direction or "").strip()

    def _sort_priority(self, item: ScoredBox) -> tuple[float, float, float, float, str]:
        amount = item.box.amount if item.planned.cost_segment != "Off" else 0.0
        volume = item.box.volume if item.planned.volume_segment != "Off" else 0.0
        weight = item.box.weight if item.planned.weight_segment != "Off" else 0.0
        return item.planned.sort_score, amount, volume, weight, item.box.name

    def _fits_vehicle(self, box: BoxItem, vehicle: VehicleSpec) -> bool:
        box_length, box_width, box_height = self._dimensions_to_meters(box.length, box.width, box.height)
        vehicle_length, vehicle_width, vehicle_height = self._dimensions_to_meters(vehicle.max_length, vehicle.max_width, vehicle.max_height)
        return box_length <= vehicle_length and box_width <= vehicle_width and box_height <= vehicle_height

    def _vehicle_accepts_box(self, vehicle: VehicleSpec, box: BoxItem) -> bool:
        if not self._fits_vehicle(box, vehicle):
            return False
        vehicle_direction = self._normalized_direction(vehicle.direction)
        if not vehicle_direction:
            return True
        return vehicle_direction == self._normalized_direction(box.direction)

    def _can_place_box(self, state: ContainerState, item: ScoredBox) -> bool:
        if not self._vehicle_accepts_box(state.vehicle, item.box):
            return False
        if state.total_volume + item.box.volume > state.vehicle.max_volume:
            return False
        if state.total_weight + item.box.weight > state.vehicle.max_weight:
            return False
        return state.assigned_direction in (None, item.box.direction)

    def _balanced_container_rank(self, state: ContainerState) -> tuple[float, float, float, int]:
        volume_ratio = state.total_volume / state.vehicle.max_volume if state.vehicle.max_volume else 0
        weight_ratio = state.total_weight / state.vehicle.max_weight if state.vehicle.max_weight else 0
        return volume_ratio + weight_ratio, state.total_amount, len(state.selected_boxes), state.container_no

    def _selection_rank(self, selected: list[ScoredBox], vehicle: VehicleSpec, min_total_amount: float, min_fill_percent: float) -> tuple[int, float, float, float]:
        metrics = self.metrics_for_boxes([item.planned for item in selected], vehicle.max_volume, vehicle.max_weight)
        valid = int(metrics.total_boxes > 0 and metrics.total_amount >= min_total_amount and metrics.fill_percent >= min_fill_percent)
        return valid, metrics.total_amount, metrics.fill_percent, -metrics.total_weight

    def _candidate_rank(self, candidate: PlanningCandidate, min_total_amount: float, min_fill_percent: float) -> tuple[int, float, float, float]:
        return self._selection_rank(candidate.selected, candidate.vehicle, min_total_amount, min_fill_percent)

    def _base_warnings(self, oversized_boxes: list[ScoredBox]) -> list[str]:
        if not oversized_boxes:
            return []
        return [f"Исключено по габаритам ТС: {len(oversized_boxes)} коробок."]

    def _safe_ratio(self, numerator: float, denominator: float) -> float:
        return numerator / denominator if denominator else numerator

    def _dimensions_to_meters(self, length: float, width: float, height: float) -> tuple[float, float, float]:
        values = (length, width, height)
        if max(values) > 20:
            return tuple(value / 100 if value > 0 else value for value in values)
        return values

    @staticmethod
    def metrics_for_boxes(selected: list[PlannedBoxItem], max_volume: float, max_weight: float) -> ShipmentPlanningMetrics:
        total_amount = sum(box.amount for box in selected)
        total_volume = sum(box.volume for box in selected)
        total_weight = sum(box.weight for box in selected)
        directions = {box.direction for box in selected}
        fill_percent = (total_volume / max_volume * 100) if max_volume else 0
        weight_percent = (total_weight / max_weight * 100) if max_weight else 0
        return ShipmentPlanningMetrics(
            total_boxes=len(selected),
            total_amount=round(total_amount, 2),
            total_volume=round(total_volume, 3),
            total_weight=round(total_weight, 3),
            fill_percent=round(fill_percent, 2),
            weight_percent=round(weight_percent, 2),
            direction_count=len(directions),
        )


shipment_planner_service = ShipmentPlannerService()
