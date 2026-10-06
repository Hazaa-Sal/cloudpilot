from .models import CostRisk, DeploymentRequest, PolicyEvaluation


def evaluate_policy(request: DeploymentRequest) -> PolicyEvaluation:
    violations: list[str] = []
    warnings: list[str] = []
    cost_risk = CostRisk.low

    if request.environment == "prod" and request.replicas < 2:
        violations.append("Production deployments require at least 2 replicas.")

    if request.environment == "prod":
        warnings.append(
            "Production plans include high-availability and monitoring resources "
            "that may incur cloud charges if applied."
        )
        cost_risk = CostRisk.medium

    if request.environment == "staging" and request.replicas == 1:
        warnings.append("Staging with 1 replica has no workload redundancy.")

    if request.replicas >= 5:
        warnings.append(
            "High replica count detected. Review capacity before provisioning paid infrastructure."
        )
        cost_risk = CostRisk.high
    elif request.replicas >= 3 and cost_risk == CostRisk.low:
        cost_risk = CostRisk.medium

    if request.region != "us-east-1":
        warnings.append(
            "The current Terraform dev environment defaults to us-east-1; "
            "align the Terraform variables before any future apply."
        )
        if cost_risk == CostRisk.low:
            cost_risk = CostRisk.medium

    return PolicyEvaluation(
        allowed=not violations,
        violations=violations,
        warnings=warnings,
        cost_risk=cost_risk,
    )
