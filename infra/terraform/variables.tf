variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "nelvra"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "api_cpu" {
  description = "ECS API task CPU units"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "ECS API task memory in MB"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Number of API ECS tasks"
  type        = number
  default     = 2
}

variable "domain_name" {
  description = "Domain name for the application (e.g. api.nelvra.io)"
  type        = string
  default     = ""
}
