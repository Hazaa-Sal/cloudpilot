resource "aws_ecr_repository" "app" {
  #checkov:skip=CKV_AWS_136:AES256 encryption is used; customer-managed KMS keys add cost to this plan-only demo.
  name                 = "${var.project_name}-${var.environment}-app"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecs_cluster" "this" {
  #checkov:skip=CKV_AWS_65:Container Insights incurs charges; local Prometheus/Grafana provides demo observability.
  name = "${var.project_name}-${var.environment}-cluster"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_security_group" "ecs" {
  #checkov:skip=CKV2_AWS_5:Plan-only scaffold intentionally has no ECS service or ENI to attach.
  name        = "${var.project_name}-${var.environment}-ecs-sg"
  description = "Security group for CloudPilot ECS workloads"
  vpc_id      = var.vpc_id

  egress {
    description = "HTTPS only for image registries and AWS APIs"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
