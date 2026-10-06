from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    aws = "aws"


class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class CostRisk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DeploymentRequest(BaseModel):
    name: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9-]+$")
    provider: CloudProvider = CloudProvider.aws
    region: str = "us-east-1"
    environment: Environment = Environment.dev
    replicas: int = Field(default=1, ge=1, le=10)


class PolicyEvaluation(BaseModel):
    allowed: bool
    violations: list[str]
    warnings: list[str]
    cost_risk: CostRisk


class InfrastructurePlan(BaseModel):
    plan_id: str
    created_at: datetime
    application: str
    provider: CloudProvider
    region: str
    environment: Environment
    replicas: int
    resources: list[str]
    status: str
    policy: PolicyEvaluation


class RuntimeStatus(BaseModel):
    mode: str
    kubernetes_detected: bool
    namespace: str | None = None
    pod_name: str | None = None
    node_name: str | None = None
