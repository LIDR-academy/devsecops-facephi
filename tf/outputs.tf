output "vpc_id" {
  description = "ID of the created VPC"
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.network.private_subnet_ids
}

output "artifacts_bucket_name" {
  description = "Name of the S3 bucket for frontend/backend artifacts"
  value       = module.s3_artifacts.bucket_name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.compute.alb_dns_name
}

