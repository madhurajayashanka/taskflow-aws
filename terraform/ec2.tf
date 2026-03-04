data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical official

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-*-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── Elastic IP (created BEFORE EC2) ────────────────────────────
# EIP must exist first so its IP can be injected into user_data
# for ALLOWED_HOSTS, CORS, etc.

resource "aws_eip" "app" {
  domain = "vpc"
  tags   = { Name = "taskflow-eip" }
}

# ── EC2 Instance ───────────────────────────────────────────────

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data.sh", {
    repo_url      = var.repo_url
    db_name       = var.db_name
    db_user       = var.db_user
    db_password   = random_password.db_password.result
    secret_key    = random_password.django_secret_key.result
    s3_bucket     = aws_s3_bucket.uploads.bucket
    aws_region    = var.aws_region
    ec2_public_ip = aws_eip.app.public_ip
  })

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
    tags        = { Name = "taskflow-root-volume" }
  }

  tags = { Name = "taskflow-app-server" }

  lifecycle {
    create_before_destroy = true
  }
}

# ── EIP Association (after both EIP and EC2 exist) ─────────────

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}
