# Reference the existing S3 bucket (already contains frontend.zip and backend.zip)
data "aws_s3_bucket" "artifacts" {
  bucket = var.s3_bucket_name
}

# IAM role that allows EC2 instances to read from the S3 bucket
resource "aws_iam_role" "ec2_s3_access" {
  name = "${var.project_name}-ec2-s3-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_policy" "s3_read_artifacts" {
  name        = "${var.project_name}-s3-read-artifacts"
  description = "Allow EC2 instances to download deployment artifacts from the S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.artifacts.arn,
          "${data.aws_s3_bucket.artifacts.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_s3_attach" {
  role       = aws_iam_role.ec2_s3_access.name
  policy_arn = aws_iam_policy.s3_read_artifacts.arn
}

# Instance profile to attach the IAM role to EC2 / Launch Templates
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_s3_access.name

  tags = {
    Project = var.project_name
  }
}
