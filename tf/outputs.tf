output "backend_asg_name" {
  description = "Name of the backend Auto Scaling Group"
  value       = aws_autoscaling_group.backend.name
}

output "frontend_asg_name" {
  description = "Name of the frontend Auto Scaling Group"
  value       = aws_autoscaling_group.frontend.name
}

output "backend_launch_template_id" {
  description = "ID of the backend Launch Template"
  value       = aws_launch_template.backend.id
}

output "frontend_launch_template_id" {
  description = "ID of the frontend Launch Template"
  value       = aws_launch_template.frontend.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 artifacts bucket"
  value       = data.aws_s3_bucket.artifacts.arn
}

output "iam_instance_profile_name" {
  description = "Name of the IAM instance profile attached to EC2 instances"
  value       = aws_iam_instance_profile.ec2_profile.name
}

output "backend_security_group_id" {
  description = "ID of the backend security group (port ${var.backend_port})"
  value       = aws_security_group.backend.id
}

output "frontend_security_group_id" {
  description = "ID of the frontend security group (port ${var.frontend_port})"
  value       = aws_security_group.frontend.id
}
