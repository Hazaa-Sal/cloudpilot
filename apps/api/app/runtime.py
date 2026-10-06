import os

from .models import RuntimeStatus


def get_runtime_status() -> RuntimeStatus:
    kubernetes_detected = bool(os.getenv("KUBERNETES_SERVICE_HOST"))

    return RuntimeStatus(
        mode="kubernetes" if kubernetes_detected else "local",
        kubernetes_detected=kubernetes_detected,
        namespace=os.getenv("CLOUDPILOT_NAMESPACE"),
        pod_name=os.getenv("CLOUDPILOT_POD_NAME"),
        node_name=os.getenv("CLOUDPILOT_NODE_NAME"),
    )
