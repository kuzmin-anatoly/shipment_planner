from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    channel: str = "web"
    history: list[ChatMessage] = Field(default_factory=list)


class AgentResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    intent: str
    agent: str
    sources: list[str] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    llm: dict
    agents: list[str]


class KnowledgeDocument(BaseModel):
    title: str
    content: str
    metadata: dict = Field(default_factory=dict)


class IngestRequest(BaseModel):
    source: str = "manual"
    documents: list[KnowledgeDocument]


class IngestResponse(BaseModel):
    indexed: int


class BoxItem(BaseModel):
    name: str
    contractor: str = ""
    direction_code: str = ""
    amount: float = 0
    volume: float = 0
    length: float = 0
    width: float = 0
    height: float = 0
    weight: float = 0
    direction: str = "UNKNOWN"


class PlannedBoxItem(BoxItem):
    segment: str = ""
    cost_segment: str = ""
    weight_segment: str = ""
    volume_segment: str = ""
    sort_score: float = 0


class VehicleSpec(BaseModel):
    name: str = Field(min_length=1)
    direction: str = ""
    max_length: float = Field(gt=0)
    max_width: float = Field(gt=0)
    max_height: float = Field(gt=0)
    max_volume: float = Field(gt=0)
    max_weight: float = Field(gt=0)


class ShipmentPlanningRequest(BaseModel):
    vehicles: list[VehicleSpec] = Field(min_length=1)
    min_total_amount: float = Field(default=0, ge=0)
    min_fill_percent: float = Field(default=75, ge=0, le=100)
    max_fill_percent: float = Field(default=95, ge=0, le=100)
    distribution_mode: Literal["balanced", "free", "all"] = "balanced"
    sort_by_amount: bool = True
    sort_by_volume: bool = True
    sort_by_weight: bool = True
    boxes: list[BoxItem] | None = None


class ShipmentPlanningMetrics(BaseModel):
    total_boxes: int
    total_amount: float
    total_volume: float
    total_weight: float
    fill_percent: float
    weight_percent: float
    direction_count: int


class ContainerPlan(BaseModel):
    container_no: int
    vehicle: VehicleSpec
    success: bool
    metrics: ShipmentPlanningMetrics
    selected_boxes: list[PlannedBoxItem] = Field(default_factory=list)
    direction_summary: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ShipmentPlanningResponse(BaseModel):
    success: bool
    source: str
    metrics: ShipmentPlanningMetrics | None = None
    distribution_mode: Literal["balanced", "free", "all"] = "balanced"
    total_containers: int = 0
    used_containers: int = 0
    container_plans: list[ContainerPlan] = Field(default_factory=list)
    selected_boxes: list[PlannedBoxItem] = Field(default_factory=list)
    excluded_boxes: list[PlannedBoxItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    direction_summary: dict[str, int] = Field(default_factory=dict)


class CsvBoxesUploadRequest(BaseModel):
    filename: str = Field(min_length=1)
    content: str = Field(min_length=1)
