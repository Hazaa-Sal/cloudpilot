from enum import Enum

from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    aws = "aws"


class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class DeploymentRequest(BaseModel):
    name: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9-]+$")
    provider: CloudProvider = CloudProvider.aws
    region: str = "us-east-1"
    environment: Environment = Environment.dev
    replicas: int = Field(default=1, ge=1, le=10)


class InfrastructurePlan(BaseModel):
    application: str
    provider: CloudProvider
    region: str
    environment: Environment
    replicas: int
    resources: list[str]
    status: str
