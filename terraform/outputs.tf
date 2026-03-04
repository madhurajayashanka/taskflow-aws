output "ec2_public_ip" {
  description = "Elastic IP of the EC2 instance"
  value       = aws_eip.app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of EC2 instance"
  value       = aws_instance.app.public_dns
}

output "s3_bucket_name" {
  description = "S3 bucket name for file uploads"
  value       = aws_s3_bucket.uploads.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.uploads.arn
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${var.private_key_path} ubuntu@${aws_eip.app.public_ip}"
  sensitive   = true
}

output "app_url" {
  description = "Application URL"
  value       = "https://${aws_eip.app.public_ip}"
}

output "iam_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "deployment_summary" {
  description = "Deployment summary with all connection details"
  sensitive   = true
  value       = <<-EOT

╔══════════════════════════════════════════════════════════╗
║              TaskFlow — Deployment Complete              ║
╠══════════════════════════════════════════════════════════╣
║  App URL   : https://${aws_eip.app.public_ip}  (self-signed cert)
║  SSH       : ssh -i ${var.private_key_path} ubuntu@${aws_eip.app.public_ip}
║  S3 Bucket : ${aws_s3_bucket.uploads.bucket}
║  IAM Role  : ${aws_iam_role.ec2_role.name}
╚══════════════════════════════════════════════════════════╝

  EOT
}
