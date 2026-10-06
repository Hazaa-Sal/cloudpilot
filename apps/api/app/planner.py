from .models import DeploymentRequest, InfrastructurePlan


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

    return InfrastructurePlan(
        application=request.name,
        provider=request.provider,
        region=request.region,
        environment=request.environment,
        replicas=request.replicas,
        resources=resources,
        status="validated",
    )
