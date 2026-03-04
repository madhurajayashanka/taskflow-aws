variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (production/staging)"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type — t2.micro is free tier eligible"
  type        = string
  default     = "t2.micro"
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "private_key_path" {
  description = "Local path to the SSH private key (e.g. ~/.ssh/taskflow-key.pem) — used by null_resource to verify deployment"
  type        = string
  sensitive   = true
}

variable "repo_url" {
  description = "GitHub repository URL to clone on EC2 (e.g. https://github.com/user/taskflow)"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH — MUST be set to your IP (e.g. 1.2.3.4/32). Run: curl ifconfig.me"
  type        = string
  # No default — forces user to set their own IP for security
}

variable "app_port" {
  description = "Internal port the Django app runs on"
  type        = number
  default     = 8000
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "taskflow_db"
}

variable "db_user" {
  description = "PostgreSQL database user"
  type        = string
  default     = "taskflow_user"
}
