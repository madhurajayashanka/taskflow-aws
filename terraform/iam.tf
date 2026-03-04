resource "aws_iam_role" "ec2_role" {
  name        = "taskflow-ec2-role-${var.environment}"
  description = "IAM role for TaskFlow EC2 instance - S3 access only"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "s3_policy" {
  name = "taskflow-s3-least-privilege"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ObjectOperations"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.uploads.arn}/*"
      },
      {
        Sid      = "AllowS3BucketList"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.uploads.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "taskflow-ec2-profile-${var.environment}"
  role = aws_iam_role.ec2_role.name
}
