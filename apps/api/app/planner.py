from datetime import datetime, timezone
from uuid import uuid4

from .models import DeploymentRequest, InfrastructurePlan
from .policy import evaluate_policy


def create_plan(request: DeploymentRequest) -> InfrastructurePlan:
    resources = [
        "container-workload",
        "load-balancer",
        "networking",
        "iam-role",
        "logging",
    ]

    if request.environment == "prod":
        resources.extend(
            [
                "high-availability",
                "autoscaling",
                "enhanced-monitoring",
            ]
        )

    policy = evaluate_policy(request)

    return InfrastructurePlan(
        plan_id=str(uuid4()),
        created_at=datetime.now(timezone.utc),
        application=request.name,
        provider=request.provider,
        region=request.region,
        environment=request.environment,
        replicas=request.replicas,
        resources=resources,
        status="validated" if policy.allowed else "denied",
        policy=policy,
    )
