"""
Data models for Haikara system
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class WorkloadPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkloadStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ComputeWorkload(BaseModel):
    """Represents a compute workload that needs to be scheduled"""
    job_id: str
    name: str
    energy_usage_kw: float
    duration_hours: float
    priority: WorkloadPriority
    sla_deadline: datetime
    earliest_start: datetime
    status: WorkloadStatus = WorkloadStatus.PENDING
    metadata: Dict[str, Any] = {}


class EnergySignal(BaseModel):
    """Energy grid signals for a specific time window"""
    timestamp: datetime
    price_per_kwh: float
    carbon_intensity_g_per_kwh: float
    grid_availability: float  # 0-1 scale
    p415_event_active: bool = False
    p415_revenue_per_kwh: float = 0.0


class ScheduleDecision(BaseModel):
    """Decision made by the optimization engine"""
    job_id: str
    scheduled_start: datetime
    scheduled_end: datetime
    expected_cost: float
    expected_carbon: float
    expected_p415_revenue: float
    optimization_score: float


class BecknSearchRequest(BaseModel):
    """Beckn search/discover request"""
    context: Dict[str, Any]
    message: Dict[str, Any]


class BecknSearchResponse(BaseModel):
    """Beckn on_search response"""
    context: Dict[str, Any]
    message: Dict[str, Any]
    catalog: Optional[Dict[str, Any]] = None


class AuditLog(BaseModel):
    """Audit trail entry"""
    timestamp: datetime
    event_type: str
    job_id: Optional[str]
    beckn_transaction_id: Optional[str]
    data: Dict[str, Any]
    signature: Optional[str] = None
