terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  # ── Remote State (uncomment for team usage) ──────────────────
  # backend "s3" {
  #   bucket         = "taskflow-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TaskFlow"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ── Secret Generation ──────────────────────────────────────────
# Terraform generates ALL production secrets — no manual .env needed

resource "random_password" "db_password" {
  length  = 32
  special = false # safe for DATABASE_URL embedding
}

resource "random_password" "django_secret_key" {
  length  = 64
  special = true
}

# ── Wait for App to Be Live ────────────────────────────────────
# SSH into EC2 and wait for bootstrap to complete + health check

resource "null_resource" "wait_for_app" {
  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.private_key_path)
      host        = aws_eip.app.public_ip
      timeout     = "15m"
    }
    inline = [
      "echo 'Waiting for TaskFlow bootstrap to complete...'",
      "timeout 600 bash -c 'until grep -q \"Bootstrap Complete\" /var/log/taskflow-bootstrap.log 2>/dev/null; do sleep 10; echo \"Still waiting...\"; done'",
      "echo 'Bootstrap log shows complete. Checking health endpoint...'",
      "timeout 60 bash -c 'until curl -sf http://localhost/api/health/ > /dev/null 2>&1; do sleep 5; done'",
      "echo '✓ TaskFlow is live and healthy!'",
    ]
  }

  depends_on = [aws_eip_association.app]
}
