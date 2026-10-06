output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "ecr_repository_url" {
  value = module.compute.ecr_repository_url
}

output "ecs_cluster_name" {
  value = module.compute.ecs_cluster_name
}

output "ecs_security_group_id" {
  value = module.compute.ecs_security_group_id
}
