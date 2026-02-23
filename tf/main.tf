terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source = "./modules/network"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr_block = var.vpc_cidr_block
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "s3_artifacts" {
  source = "./modules/s3_artifacts"

  project_name = var.project_name
  environment  = var.environment
}

module "security" {
  source = "./modules/security"

  vpc_id = module.network.vpc_id

  project_name = var.project_name
  environment  = var.environment
}

module "compute" {
  source = "./modules/compute"

  project_name = var.project_name
  environment  = var.environment

  vpc_id             = module.network.vpc_id
  public_subnet_ids  = module.network.public_subnet_ids
  private_subnet_ids = module.network.private_subnet_ids

  frontend_instance_type = var.frontend_instance_type
  backend_instance_type  = var.backend_instance_type

  artifacts_bucket_name = module.s3_artifacts.bucket_name

  instance_profile_arn = module.security.instance_profile_arn

  frontend_sg_id = module.security.frontend_sg_id
  backend_sg_id  = module.security.backend_sg_id
  alb_sg_id      = module.security.alb_sg_id
}
