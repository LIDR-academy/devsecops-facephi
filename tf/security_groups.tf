data "aws_vpc" "default" {
  default = true
}

# Security Group for the backend instance (port 8080 + SSH)
resource "aws_security_group" "backend" {
  name        = "${var.project_name}-backend-sg"
  description = "Allow inbound traffic on port ${var.backend_port} and SSH"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Backend application port"
    from_port   = var.backend_port
    to_port     = var.backend_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.key_name != "" ? [1] : []
    content {
      description = "SSH access"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-backend-sg"
    Project = var.project_name
  }
}

# Security Group for the frontend instance (port 3000 + SSH)
resource "aws_security_group" "frontend" {
  name        = "${var.project_name}-frontend-sg"
  description = "Allow inbound traffic on port ${var.frontend_port} and SSH"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Frontend application port"
    from_port   = var.frontend_port
    to_port     = var.frontend_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.key_name != "" ? [1] : []
    content {
      description = "SSH access"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-frontend-sg"
    Project = var.project_name
  }
}
