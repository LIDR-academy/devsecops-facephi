data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND
# ─────────────────────────────────────────────────────────────────────────────

locals {
  backend_user_data = base64encode(templatefile("${path.module}/user_data_backend.sh", {
    bucket       = var.s3_bucket_name
    backend_port = var.backend_port
    region       = var.aws_region
  }))

  frontend_user_data = base64encode(templatefile("${path.module}/user_data_frontend.sh", {
    bucket        = var.s3_bucket_name
    frontend_port = var.frontend_port
    region        = var.aws_region
  }))
}

resource "aws_launch_template" "backend" {
  name_prefix   = "${var.project_name}-backend-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.backend.id]
  }

  key_name  = var.key_name != "" ? var.key_name : null
  user_data = local.backend_user_data

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "${var.project_name}-backend"
      Project = var.project_name
      Role    = "backend"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "backend" {
  name                = "${var.project_name}-backend-asg"
  min_size            = var.asg_min_size
  desired_capacity    = var.asg_desired_size
  max_size            = var.asg_max_size
  vpc_zone_identifier = data.aws_subnets.default.ids

  launch_template {
    id      = aws_launch_template.backend.id
    version = "$Latest"
  }

  # Ensure at least one instance is always healthy during a rolling deployment
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 100
    }
  }

  health_check_type         = "EC2"
  health_check_grace_period = 120

  tag {
    key                 = "Name"
    value               = "${var.project_name}-backend"
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = var.project_name
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# FRONTEND
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_launch_template" "frontend" {
  name_prefix   = "${var.project_name}-frontend-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.frontend.id]
  }

  key_name  = var.key_name != "" ? var.key_name : null
  user_data = local.frontend_user_data

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "${var.project_name}-frontend"
      Project = var.project_name
      Role    = "frontend"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "frontend" {
  name                = "${var.project_name}-frontend-asg"
  min_size            = var.asg_min_size
  desired_capacity    = var.asg_desired_size
  max_size            = var.asg_max_size
  vpc_zone_identifier = data.aws_subnets.default.ids

  launch_template {
    id      = aws_launch_template.frontend.id
    version = "$Latest"
  }

  # Ensure at least one instance is always healthy during a rolling deployment
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 100
    }
  }

  health_check_type         = "EC2"
  health_check_grace_period = 120

  tag {
    key                 = "Name"
    value               = "${var.project_name}-frontend"
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = var.project_name
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}
