output "alb_dns_name" {
  description = "ALB DNS name — point your CNAME here"
  value       = aws_lb.main.dns_name
}

output "ecr_api_url" {
  description = "ECR URL for API image pushes"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_dashboard_url" {
  description = "ECR URL for dashboard image pushes"
  value       = aws_ecr_repository.dashboard.repository_url
}

output "rds_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}
