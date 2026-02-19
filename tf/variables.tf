variable "aws_region" {
  description = "AWS region where all resources will be deployed"
  type        = string
  default     = "eu-west-1"
}

variable "ami_id" {
  description = "AMI ID to use for the EC2 instances (Amazon Linux 2023 in eu-west-1 by default)"
  type        = string
  default     = "ami-0df368112825f8d8f"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "s3_bucket_name" {
  description = "Name of the existing S3 bucket that contains frontend.zip and backend.zip"
  type        = string
}

variable "key_name" {
  description = "Name of the existing EC2 key pair for SSH access (leave empty to disable SSH)"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Prefix used to name all created resources"
  type        = string
  default     = "facephi"
}

variable "backend_port" {
  description = "Port on which the backend application listens"
  type        = number
  default     = 8080
}

variable "frontend_port" {
  description = "Port on which the frontend application listens"
  type        = number
  default     = 3000
}

variable "asg_min_size" {
  description = "Minimum number of instances in each Auto Scaling Group"
  type        = number
  default     = 1
}

variable "asg_desired_size" {
  description = "Desired number of instances in each Auto Scaling Group"
  type        = number
  default     = 1
}

variable "asg_max_size" {
  description = "Maximum number of instances in each Auto Scaling Group"
  type        = number
  default     = 2
}
