# TaskFlow — Free Tier AWS Deployment Guide

> **From zero to live app in ~15 minutes, costing $0/month on AWS Free Tier.**

---

## Table of Contents

1. [What You'll End Up With](#1-what-youll-end-up-with)
2. [What It Will Cost](#2-what-it-will-cost)
3. [Prerequisites (Your Laptop)](#3-prerequisites-your-laptop)
4. [Step 1 — AWS Account Setup (One-Time)](#step-1--aws-account-setup-one-time-5-min)
5. [Step 2 — Install Tools on Your Mac](#step-2--install-tools-on-your-mac-3-min)
6. [Step 3 — Configure AWS CLI](#step-3--configure-aws-cli-2-min)
7. [Step 4 — Create an EC2 Key Pair](#step-4--create-an-ec2-key-pair-1-min)
8. [Step 5 — Push Code to GitHub](#step-5--push-code-to-github-2-min)
9. [Step 6 — Configure Terraform Variables](#step-6--configure-terraform-variables-2-min)
10. [Step 7 — Deploy (One Command)](#step-7--deploy-one-command)
11. [What Happens Behind the Scenes](#what-happens-behind-the-scenes)
12. [Step 8 — Verify Everything Works](#step-8--verify-everything-works)
13. [Step 9 — Destroy Everything (One Command)](#step-9--destroy-everything-one-command)
14. [Troubleshooting](#troubleshooting)
15. [Free Tier Limits to Watch](#free-tier-limits-to-watch)
16. [FAQ](#faq)

---

## 1. What You'll End Up With

```
Internet ──▶ Elastic IP ──▶ EC2 (t2.micro, Ubuntu 22.04)
                             ├── Nginx (reverse proxy)
                             ├── React Frontend (Vite)
                             ├── Django API (Gunicorn)
                             ├── PostgreSQL 15 (in Docker)
                             └── S3 Bucket (file uploads)
```

- A **live task management app** at `https://<your-elastic-ip>` (self-signed SSL)
- All infrastructure defined as code (Terraform)
- Auto-generated secrets (DB password + Django secret key)
- Daily database backups to S3
- Zero manual SSH configuration

---

## 2. What It Will Cost

| Resource      | Free Tier Allowance                         | TaskFlow Usage  | Cost         |
| ------------- | ------------------------------------------- | --------------- | ------------ |
| EC2 t2.micro  | 750 hrs/month (12 months)                   | ~730 hrs/month  | **$0**       |
| EBS gp3 20GB  | 30 GB free (12 months)                      | 20 GB           | **$0**       |
| S3            | 5 GB + 20K GET + 2K PUT                     | Minimal         | **$0**       |
| Data Transfer | 100 GB/month out                            | Minimal         | **$0**       |
| Elastic IP    | Free **while attached** to running instance | Always attached | **$0**       |
| **Total**     |                                             |                 | **$0/month** |

> **⚠️ IMPORTANT:** If you **stop** your EC2 instance but don't release the Elastic IP, AWS charges ~$3.65/month for the idle EIP. Always either keep EC2 running OR run `make destroy` to clean up everything.

> **⚠️ 12-month limit:** Free tier for EC2/EBS is only valid for 12 months after you create your AWS account. After that, t2.micro costs ~$8.50/month.

---

## 3. Prerequisites (Your Laptop)

You need these installed on your Mac before starting:

| Tool                                   | Check if installed    | Install command                                                                                   |
| -------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------- |
| **Homebrew**                           | `brew --version`      | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| **Terraform**                          | `terraform --version` | `brew install terraform`                                                                          |
| **AWS CLI**                            | `aws --version`       | `brew install awscli`                                                                             |
| **Git**                                | `git --version`       | Already on macOS (Xcode tools)                                                                    |
| **Docker** _(optional, for local dev)_ | `docker --version`    | `brew install --cask docker`                                                                      |

---

## Step 1 — AWS Account Setup (One-Time, ~5 min)

If you already have an AWS account, skip to Step 1b.

### 1a. Create AWS Account

1. Go to [https://aws.amazon.com/free](https://aws.amazon.com/free)
2. Click **"Create a Free Account"**
3. Enter email, password, account name
4. Choose **"Personal"** account type
5. Enter credit card (you **will not be charged** unless you exceed free tier)
6. Complete phone verification
7. Choose the **"Basic Support — Free"** plan

### 1b. Create an IAM User (Don't Use Root)

> **Never use your root account for daily work.** Create an IAM user instead.

1. Sign in at [https://console.aws.amazon.com](https://console.aws.amazon.com)
2. Search for **"IAM"** in the top search bar → click it
3. In the left sidebar, click **"Users"** → **"Create user"**
4. **User name:** `taskflow-deployer`
5. Check **"Provide user access to the AWS Management Console"** (optional — for console access)
6. Click **"Next"**
7. Choose **"Attach policies directly"**
8. Search and check these policies:
   - ✅ `AmazonEC2FullAccess`
   - ✅ `AmazonS3FullAccess`
   - ✅ `IAMFullAccess`
   - ✅ `AmazonVPCFullAccess`
9. Click **"Next"** → **"Create user"**

### 1c. Create Access Keys for CLI

1. Click into the `taskflow-deployer` user you just created
2. Go to **"Security credentials"** tab
3. Scroll to **"Access keys"** → **"Create access key"**
4. Choose **"Command Line Interface (CLI)"**
5. Check the confirmation box → **"Next"** → **"Create access key"**
6. **⚠️ SAVE BOTH VALUES NOW** — you won't see the secret key again:
   - `Access key ID` (looks like `AKIAIOSFODNN7EXAMPLE`)
   - `Secret access key` (looks like `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

---

## Step 2 — Install Tools on Your Mac (~3 min)

Open Terminal and run:

```bash
# Install Homebrew (skip if already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Terraform and AWS CLI
brew install terraform awscli

# Verify installations
terraform --version    # Should show >= 1.5.0
aws --version          # Should show aws-cli/2.x.x
```

---

## Step 3 — Configure AWS CLI (~2 min)

```bash
aws configure
```

It will prompt you for 4 values:

```
AWS Access Key ID [None]: PASTE_YOUR_ACCESS_KEY_HERE
AWS Secret Access Key [None]: PASTE_YOUR_SECRET_KEY_HERE
Default region name [None]: us-east-1
Default output format [None]: json
```

**Verify it works:**

```bash
aws sts get-caller-identity
```

You should see output like:

```json
{
  "UserId": "AIDACKCEVSQ6C2EXAMPLE",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/taskflow-deployer"
}
```

> If you get an error, double-check your access key and secret key.

---

## Step 4 — Create an EC2 Key Pair (~1 min)

This creates the SSH key that Terraform uses to verify deployment.

```bash
# Create the key pair in AWS and save the private key locally
aws ec2 create-key-pair \
  --key-name taskflow-key \
  --key-type rsa \
  --query 'KeyMaterial' \
  --output text \
  --region us-east-1 > ~/.ssh/taskflow-key.pem

# Lock down permissions (required by SSH)
chmod 400 ~/.ssh/taskflow-key.pem
```

**Verify it exists:**

```bash
aws ec2 describe-key-pairs --key-names taskflow-key --region us-east-1
```

> **What this does:** Creates a key pair named `taskflow-key` in AWS and downloads the private key to `~/.ssh/taskflow-key.pem`. Terraform references this to SSH into your EC2 instance for deployment verification.

---

## Step 5 — Push Code to GitHub (~2 min)

The EC2 instance needs to `git clone` your code. Push this project to a **public** GitHub repo (or a private one with a personal access token in the URL).

```bash
cd /path/to/taskflow

# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit — TaskFlow"

# Create repo on GitHub (via github.com or gh CLI), then:
git remote add origin https://github.com/YOUR_USERNAME/taskflow.git
git branch -M main
git push -u origin main
```

> **Private repo?** Use this format for `repo_url`:
> `https://YOUR_PAT_TOKEN@github.com/YOUR_USERNAME/taskflow.git`
> Generate a PAT at: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens

---

## Step 6 — Configure Terraform Variables (~2 min)

```bash
cd taskflow/terraform

# Copy the example file
cp terraform.tfvars.example terraform.tfvars
```

Now edit `terraform.tfvars`:

```bash
nano terraform.tfvars
# (or: code terraform.tfvars — if using VS Code)
```

Fill in these values:

```hcl
aws_region       = "us-east-1"
environment      = "production"
instance_type    = "t2.micro"
key_pair_name    = "taskflow-key"
private_key_path = "~/.ssh/taskflow-key.pem"
allowed_ssh_cidr = "YOUR_IP/32"
repo_url         = "https://github.com/YOUR_USERNAME/taskflow"
```

### How to find YOUR_IP:

```bash
curl ifconfig.me
```

If it returns `203.0.113.42`, then set:

```hcl
allowed_ssh_cidr = "203.0.113.42/32"
```

> **What is `/32`?** It means "only this one IP address". This locks SSH access to your machine only.

> **On dynamic IP / coffee shop wifi?** Use `0.0.0.0/0` temporarily (allows SSH from anywhere). Change it back to your IP when you're on a stable network.

---

## Step 7 — Deploy (One Command)

```bash
cd taskflow   # make sure you're in the project root (where Makefile is)
make deploy
```

**That's it.** One command. Go grab a coffee — takes about 8-12 minutes.

### What you'll see in your terminal:

```
Initializing the backend...
Initializing provider plugins...

Terraform has been successfully initialized!

Terraform will perform the following actions:

  # aws_eip.app will be created
  # aws_instance.app will be created
  # aws_s3_bucket.uploads will be created
  # aws_security_group.ec2 will be created
  # aws_iam_role.ec2_role will be created
  ... (13 resources total)

Plan: 13 to add, 0 to change, 0 to destroy.

aws_eip.app: Creating...
aws_eip.app: Creation complete [id=eipalloc-0abc123]

aws_s3_bucket.uploads: Creating...
aws_s3_bucket.uploads: Creation complete

aws_instance.app: Creating...
aws_instance.app: Still creating... [2m0s elapsed]
aws_instance.app: Creation complete

null_resource.wait_for_app: Creating...
null_resource.wait_for_app: Provisioning with 'remote-exec'...
  Waiting for TaskFlow bootstrap to complete...
  Still waiting...
  Still waiting...
  Still waiting...
  Bootstrap log shows complete. Checking health endpoint...
  ✓ TaskFlow is live and healthy!

╔══════════════════════════════════════════════════════════╗
║              TaskFlow — Deployment Complete              ║
╠══════════════════════════════════════════════════════════╣
║  App URL   : https://54.xxx.xxx.xxx  (self-signed cert)   ║
║  SSH       : ssh -i ~/.ssh/taskflow-key.pem ubuntu@54.. ║
║  S3 Bucket : taskflow-uploads-a1b2c3d4                  ║
║  IAM Role  : taskflow-ec2-role-production               ║
╚══════════════════════════════════════════════════════════╝
```

> **When you see the box at the bottom, your app is LIVE.** Open the URL in your browser.

---

## What Happens Behind the Scenes

Here's the full timeline of what `make deploy` does:

```
 0:00  terraform init — downloads AWS/null/random providers
 0:10  terraform apply starts — creates resources in this order:

       1. Elastic IP           (instant)      — reserves a static IP
       2. S3 Bucket            (2s)           — for file uploads
       3. S3 Configs           (5s)           — encryption, versioning, lifecycle
       4. IAM Role + Policy    (5s)           — EC2 can access S3 only
       5. Security Group       (3s)           — allows 80, 443, your-IP:22
       6. random_password × 2  (instant)      — generates DB pwd + Django secret
       7. EC2 Instance         (~2 min)       — launches Ubuntu 22.04

 2:00  EC2 boots and user_data.sh starts automatically:
       [1/8] System update             (apt-get update + upgrade)
       [2/8] Docker install            (curl get.docker.com)
       [3/8] Docker Compose plugin     (apt-get install)
       [4/8] AWS CLI + Certbot         (for S3 access + future SSL)
       [5/8] Git clone YOUR repo       (to /opt/taskflow)
       [6/8] Write .env file           (with Terraform-generated secrets)
       [7/8] docker compose up         (builds + starts 4 containers)
             └── Nginx ──▶ React + Django ──▶ PostgreSQL
       [8/8] Setup daily backup cron   (DB dump → S3 at 2 AM)

 8:00  null_resource SSHes in and verifies:
       — waits for "Bootstrap Complete" in /var/log/taskflow-bootstrap.log
       — hits http://localhost/api/health/ to confirm app is serving
       — prints "✓ TaskFlow is live and healthy!"

10:00  Terraform prints deployment summary box
       ✅ DONE — App is live
```

### What's running on EC2:

```
┌────────────────────────────────────────┐
│  EC2 t2.micro (1 vCPU, 1GB RAM)       │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  Docker Compose                  │  │
│  │                                  │  │
│  │  ┌──────┐  ┌─────────┐         │  │
│  │  │ Nginx│──│React SPA│         │  │
│  │  │ :80  │  │  (Vite) │         │  │
│  │  └──┬───┘  └─────────┘         │  │
│  │     │                           │  │
│  │  ┌──▼──────────┐  ┌─────────┐  │  │
│  │  │Django + DRF │──│Postgres │  │  │
│  │  │  (Gunicorn) │  │  :5432  │  │  │
│  │  └─────────────┘  └─────────┘  │  │
│  │                                  │  │
│  └──────────────────────────────────┘  │
│                                        │
│  /opt/taskflow/.env   (secrets)        │
│  /var/log/taskflow-bootstrap.log       │
└────────────────────────────────────────┘
         │
         ▼
   S3 Bucket (file uploads)
```

---

## Step 8 — Verify Everything Works

### Open the app

Copy the IP from the deployment summary and open in your browser:

````
https://54.xxx.xxx.xxx```

You should see the TaskFlow dashboard.

### Test CRUD operations

1. **Create** a task — click "New Task", fill in title/description, save
2. **Read** — see it appear in the task list
3. **Update** — click edit, change the status, save
4. **Delete** — click delete, confirm

### Check health endpoint

```bash
curl -sk https://54.xxx.xxx.xxx/api/health/
# Should return: {"status":"ok","db":"connected"}
````

### SSH into the instance (optional)

```bash
ssh -i ~/.ssh/taskflow-key.pem ubuntu@54.xxx.xxx.xxx
```

Once inside:

```bash
# Check bootstrap log
cat /var/log/taskflow-bootstrap.log

# Check running containers
cd /opt/taskflow && docker compose ps

# Check application logs
docker compose logs --tail=50

# Check the generated .env (secrets)
cat .env
```

---

## Step 9 — Destroy Everything (One Command)

When you're done (or want to stop charges), destroy everything:

```bash
make destroy
```

This will:

1. Show a **5-second warning** (press Ctrl+C to cancel)
2. Delete the EC2 instance
3. Release the Elastic IP
4. Delete the S3 bucket + all files in it
5. Delete the security group, IAM role, instance profile
6. **Total AWS resources after destroy: 0**

```
WARNING: This will permanently destroy all AWS resources
Press Ctrl+C within 5 seconds to cancel...

aws_eip_association.app: Destroying...
null_resource.wait_for_app: Destroying...
aws_instance.app: Destroying...
aws_s3_bucket.uploads: Destroying...
aws_iam_role.ec2_role: Destroying...
...
Destroy complete! Resources: 13 destroyed.

✓ All AWS resources destroyed
```

> **There is nothing left in your AWS account.** No hidden charges.

---

## Troubleshooting

### "Error: No valid credential sources found"

```
AWS CLI is not configured. Run:
  aws configure
And paste your Access Key ID + Secret Access Key.
```

### "Error: error creating EC2 Instance: UnauthorizedOperation"

Your IAM user is missing permissions. Go to IAM → Users → taskflow-deployer → Add permissions:

- `AmazonEC2FullAccess`
- `AmazonS3FullAccess`
- `IAMFullAccess`
- `AmazonVPCFullAccess`

### "Error: InvalidKeyPair.NotFound"

The key pair doesn't exist in that region. Create it:

```bash
aws ec2 create-key-pair \
  --key-name taskflow-key \
  --key-type rsa \
  --query 'KeyMaterial' \
  --output text \
  --region us-east-1 > ~/.ssh/taskflow-key.pem
chmod 400 ~/.ssh/taskflow-key.pem
```

### "null_resource.wait_for_app: timeout"

Bootstrap is taking longer than 15 minutes. SSH in and check the log:

```bash
ssh -i ~/.ssh/taskflow-key.pem ubuntu@<IP>
tail -f /var/log/taskflow-bootstrap.log
```

Common causes:

- **Slow Docker image builds** — t2.micro has only 1GB RAM. Wait longer.
- **Git clone failed** — Check that `repo_url` in terraform.tfvars is correct and the repo is public (or has PAT token).
- **Docker pull failed** — Transient network issue. Re-run `make deploy`.

### "Error: topping EIP: disassociation failed"

Sometimes EIP disassociation is slow. Wait 30 seconds and run `make destroy` again.

### App loads but shows blank page

The frontend built but the API isn't responding:

```bash
ssh -i ~/.ssh/taskflow-key.pem ubuntu@<IP>
cd /opt/taskflow
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend
```

### "Permission denied (publickey)"

```bash
# Check the key file has correct permissions
ls -la ~/.ssh/taskflow-key.pem
# Must show: -r--------  (400)

# Fix:
chmod 400 ~/.ssh/taskflow-key.pem
```

### Want to redeploy after code changes?

```bash
# Option A: SSH in and pull latest
ssh -i ~/.ssh/taskflow-key.pem ubuntu@<IP>
cd /opt/taskflow
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Option B: Destroy and recreate (clean slate)
make destroy
make deploy
```

---

## Free Tier Limits to Watch

| Resource       | Free Tier Limit         | What Happens If Exceeded     |
| -------------- | ----------------------- | ---------------------------- |
| EC2 t2.micro   | 750 hours/month         | ~$8.50/month per instance    |
| EBS            | 30 GB total             | $0.08/GB/month               |
| S3             | 5 GB storage            | $0.023/GB/month              |
| S3 Requests    | 20,000 GET / 2,000 PUT  | $0.0004 per 1000 requests    |
| Data out       | 100 GB/month            | $0.09/GB after               |
| **Elastic IP** | **Free while attached** | **~$3.65/month if detached** |

### How to monitor:

1. Go to [AWS Billing Dashboard](https://console.aws.amazon.com/billing/home)
2. Look at **"Free Tier Usage"** section
3. Set up a **Billing Alarm**:
   ```bash
   # This creates an alarm if your bill exceeds $1
   aws cloudwatch put-metric-alarm \
     --alarm-name "billing-alarm-1usd" \
     --alarm-description "Alert when bill > $1" \
     --metric-name EstimatedCharges \
     --namespace AWS/Billing \
     --statistic Maximum \
     --period 21600 \
     --threshold 1 \
     --comparison-operator GreaterThanThreshold \
     --dimensions Name=Currency,Value=USD \
     --evaluation-periods 1 \
     --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:billing-alerts \
     --region us-east-1
   ```
   _(Or just do it in the AWS Console → Billing → Billing preferences → "Receive Free Tier Usage Alerts")_

---

## FAQ

### Q: Can I use a region other than us-east-1?

Yes. Change `aws_region` in `terraform.tfvars`. Make sure your key pair is in the same region:

```bash
aws ec2 create-key-pair --key-name taskflow-key --region YOUR_REGION ...
```

### Q: Can I use t3.micro instead of t2.micro?

Yes — `t3.micro` is also free tier eligible (750 hrs/month). Change `instance_type` in `terraform.tfvars`.

### Q: What if I'm past the 12-month free tier?

You'll pay ~$8.50/month for t2.micro + ~$1.60/month for 20GB gp3 EBS. Total: ~$10/month. Destroy when not needed.

### Q: Can I add a real domain name?

1. Buy a domain (Route 53-$12/year, or Namecheap, etc.)
2. Point an A record to your Elastic IP
3. SSH in and run: `sudo certbot --nginx -d yourdomain.com`
4. Update `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` in `/opt/taskflow/.env`
5. Restart: `docker compose -f docker-compose.yml -f docker-compose.prod.yml restart`

### Q: How do I check what's running on my AWS account?

```bash
# List all EC2 instances
aws ec2 describe-instances --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress,Type:InstanceType}' --output table

# List all S3 buckets
aws s3 ls

# List all Elastic IPs
aws ec2 describe-addresses --output table

# Nuclear option — see EVERYTHING Terraform manages:
cd terraform && terraform state list
```

### Q: How do I make sure I'm not being charged?

```bash
# Check Terraform state — if it shows 0 resources, nothing is running:
cd terraform && terraform state list

# Or check directly in AWS:
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --output table
```

If both show nothing, you have $0 in charges.

### Q: I'm getting "You have reached your limit of 5 Elastic IPs"

Free tier accounts can have up to 5 EIPs. Release old ones:

```bash
# List all EIPs
aws ec2 describe-addresses --output table

# Release one by allocation ID
aws ec2 release-address --allocation-id eipalloc-0abc123
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────┐
│                  COMMANDS CHEAT SHEET                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  DEPLOY:     make deploy                             │
│  DESTROY:    make destroy                            │
│  STATUS:     cd terraform && terraform output        │
│  SSH IN:     ssh -i ~/.ssh/taskflow-key.pem \        │
│                ubuntu@<IP>                           │
│  LOGS:       ssh in → tail -f                        │
│                /var/log/taskflow-bootstrap.log        │
│  YOUR IP:    curl ifconfig.me                        │
│  HELP:       make help                               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

**Total time: ~15 minutes. Total cost: $0. Total SSH commands needed: 0.**
