# 🗒️ TaskFlow

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Free_Tier-FF9900?logo=amazonaws&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

> A production-ready full-stack task management app deployed on AWS — built as a
> technical assessment demonstrating cloud infrastructure, containerization, IaC,
> and security best practices.

**Live Demo:** `http://<ec2-ip>` (see deployment section)

---

## ⚡ Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/taskflow
cd taskflow

# 2. Set up environment
cp .env.example .env
# Edit .env with your values

# 3. Start everything
make up

# 4. Open browser
open http://localhost

# Tear down
make down
```

All commands: `make help`

---

## 📐 Architecture

```
Internet
    │
    ▼ :80 / :443
┌─────────────────────────────────────────────────────────┐
│                    AWS Cloud (us-east-1)                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              EC2 t2.micro (Free Tier)            │   │
│  │                                                 │   │
│  │  ┌──────────────┐                               │   │
│  │  │    Nginx      │  :80 → redirect to :443      │   │
│  │  │  :80 / :443   │  /api/* → backend:8000       │   │
│  │  └──────┬───────┘  /* → frontend:80             │   │
│  │         │                                       │   │
│  │  ┌──────┴──────┐  ┌──────────────┐             │   │
│  │  │   Backend   │  │   Frontend   │             │   │
│  │  │ Django:8000 │  │  React/Nginx │             │   │
│  │  └──────┬──────┘  └──────────────┘             │   │
│  │         │                                       │   │
│  │  ┌──────┴──────┐                               │   │
│  │  │ PostgreSQL  │  NOT exposed publicly          │   │
│  │  │   :5432     │  internal Docker network only  │   │
│  │  └─────────────┘                               │   │
│  └─────────────────────────────────────────────────┘   │
│                         │ IAM Role (no static keys)     │
│  ┌──────────────────┐   │                               │
│  │    S3 Bucket     │◄──┘                               │
│  │  Block all public│  AES256 encrypted                 │
│  │  Versioning ON   │  30-day lifecycle policy          │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

**Key design decisions:**

- All traffic enters through Nginx on ports 80/443 only
- Database is on an internal Docker network, never publicly exposed
- S3 accessed via EC2 IAM Role — no long-term credentials on the server
- All infrastructure is defined in Terraform — reproducible with one command

---

## 🐳 Local Development

### Prerequisites

- Docker + Docker Compose
- Make

### Setup

```bash
cp .env.example .env
# Fill in POSTGRES_PASSWORD and SECRET_KEY at minimum
make up          # Start all services
make migrate     # Run DB migrations (first time)
make logs        # Watch logs
```

### Useful Commands

```bash
make shell-backend   # Django shell / bash
make shell-db        # PostgreSQL psql
make test            # Run test suite
make down            # Stop everything
```

---

## ☁️ AWS Deployment

### Prerequisites

- AWS account (free tier)
- Terraform >= 1.5 installed
- EC2 key pair created in AWS Console
- AWS CLI configured (`aws configure`)
- A GitHub repository URL for your code (public or accessible via deploy key)

### One-Command Deployment

The entire stack is deployed with a single `make deploy`. Terraform provisions
the EC2 instance, S3 bucket, IAM role, and security groups, then **cloud-init
automatically** installs Docker, clones the repo, generates a self-signed SSL
certificate, writes the `.env`, and starts the application.

```bash
# 1. Configure Terraform variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit: set key_pair_name, allowed_ssh_cidr, and repo_url

# 2. Deploy everything (init + apply)
make deploy

# 3. Get outputs
make output
# → EC2 Public IP, S3 Bucket Name, SSH command
```

After ~3-5 minutes, the app is live at `https://<ec2-ip>` (self-signed cert —
browser will show a warning, which is expected for an IP-based deployment).

### Optional: Real SSL Certificate

```bash
# SSH into EC2
ssh -i ~/.ssh/your-key.pem ubuntu@$(cd terraform && terraform output -raw ec2_public_ip)

# If you've pointed a domain to the EC2 IP:
sudo certbot certonly --webroot -w /var/www/certbot -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/ssl/taskflow/fullchain.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/ssl/taskflow/privkey.pem
cd /opt/taskflow && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Verify Deployment

```bash
# Health check
curl -sk https://<ec2-ip>/api/health/
# → {"status":"ok","db":"connected"}

# SSH into EC2 and check logs
ssh -i ~/.ssh/your-key.pem ubuntu@<ec2-ip>
cat /var/log/taskflow-bootstrap.log
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs
```

### Teardown (Important — avoids charges)

```bash
make destroy   # destroys ALL AWS resources
```

---

## 🔒 IAM Configuration

### Principle of Least Privilege

The EC2 instance uses an **IAM Role** (not static access keys). The role is attached
as an Instance Profile — the app gets temporary rotating credentials automatically.

**Permissions granted:**

| Service | Action         | Resource              | Justification  |
| ------- | -------------- | --------------------- | -------------- |
| S3      | `PutObject`    | `taskflow-uploads-*/` | Upload files   |
| S3      | `GetObject`    | `taskflow-uploads-*/` | Serve files    |
| S3      | `DeleteObject` | `taskflow-uploads-*/` | Remove files   |
| S3      | `ListBucket`   | `taskflow-uploads-*`  | Browse uploads |

**Explicitly NOT granted:**

- `s3:CreateBucket` / `s3:DeleteBucket`
- `ec2:*` / `iam:*` / `rds:*`
- Access to any other AWS service
- Access to any other S3 bucket

---

## 🛡️ Security Group Rules

| Direction | Port | Protocol | Source         | Purpose                             |
| --------- | ---- | -------- | -------------- | ----------------------------------- |
| Inbound   | 80   | TCP      | 0.0.0.0/0      | HTTP (redirects to HTTPS)           |
| Inbound   | 443  | TCP      | 0.0.0.0/0      | HTTPS application traffic           |
| Inbound   | 22   | TCP      | `<your-ip>/32` | SSH — **restricted to deployer IP** |
| Outbound  | All  | All      | 0.0.0.0/0      | Outbound (updates, S3, etc.)        |

**Ports NOT exposed:** 5432 (PostgreSQL), 8000 (Django), 5173 (Vite dev)

---

## 💸 AWS Free Tier Compliance

| Service           | Free Tier          | Usage      | Status  |
| ----------------- | ------------------ | ---------- | ------- |
| EC2 t2.micro      | 750 hrs/month      | 1 instance | ✅ Safe |
| EBS Storage       | 30 GB              | 20 GB      | ✅ Safe |
| S3 Storage        | 5 GB               | < 1 GB     | ✅ Safe |
| S3 GET Requests   | 20,000/month       | Minimal    | ✅ Safe |
| S3 PUT Requests   | 2,000/month        | Minimal    | ✅ Safe |
| Data Transfer Out | 15 GB/month        | Minimal    | ✅ Safe |
| Elastic IP        | Free when attached | 1 EIP      | ✅ Safe |

> Run `make destroy` after the assessment demo to avoid any charges.

---

## 🚀 Scaling Strategy

**Current Architecture** (this assessment):

```
Internet → EC2 (Nginx + Docker Compose) → PostgreSQL container
```

**Phase 2 — Horizontal Scale:**

```
Internet → ALB → Auto Scaling Group (EC2)
                         ↓
               Amazon RDS PostgreSQL (Multi-AZ)
               ElastiCache Redis (sessions)
```

**Phase 3 — Containerised:**

```
Internet → CloudFront → ALB → ECS Fargate (containers)
                                    ↓
                          RDS Aurora Serverless
                          ElastiCache Redis
```

Changes needed to reach Phase 2:

1. Move PostgreSQL to RDS (change `DATABASE_URL` env var — no code changes)
2. Add ALB in front of EC2
3. Make EC2 stateless (sessions → Redis, files → S3 already done)
4. Create Auto Scaling Group with Launch Template

---

## 🤖 CI/CD Pipeline

Automated deployment via **GitHub Actions** (`.github/workflows/deploy.yml`):

```
Push to main → Run Tests → Lint Code → Deploy to EC2 via SSH
```

| Stage  | Trigger        | What it does                                 |
| ------ | -------------- | -------------------------------------------- |
| Test   | Push / PR      | Runs Django tests against PostgreSQL service |
| Lint   | Push / PR      | flake8 + hardcoded secrets scan              |
| Deploy | Push to `main` | SSH into EC2, git pull, rebuild containers   |

**Required GitHub Secrets:**

| Secret        | Description                      |
| ------------- | -------------------------------- |
| `EC2_HOST`    | Elastic IP of the EC2 instance   |
| `EC2_SSH_KEY` | Private SSH key for ubuntu user  |
| `EC2_USER`    | SSH username (default: `ubuntu`) |

---

## 💾 Backup Strategy

**Database:** Automated daily backup via cron job on EC2

```bash
# Runs at 2am daily, stores compressed SQL to S3
docker exec taskflow-db pg_dump -U $POSTGRES_USER $POSTGRES_DB \
  | gzip | aws s3 cp - s3://$BUCKET/backups/$(date +%Y-%m-%d).sql.gz
```

**S3 Files:** S3 Versioning enabled — deleted/overwritten files retained 30 days

**EC2:** AMI snapshot can be created before major changes via AWS Backup

---

## 📋 Environment Variables

| Variable                 | Required | Example                           | Description          |
| ------------------------ | -------- | --------------------------------- | -------------------- |
| `SECRET_KEY`             | ✅       | `django-insecure-...`             | Django secret key    |
| `POSTGRES_DB`            | ✅       | `taskflow_db`                     | Database name        |
| `POSTGRES_USER`          | ✅       | `taskflow_user`                   | Database user        |
| `POSTGRES_PASSWORD`      | ✅       | `strong-password`                 | Database password    |
| `DATABASE_URL`           | ✅       | `postgres://user:pass@db:5432/db` | Full DB URL          |
| `DJANGO_SETTINGS_MODULE` | ✅       | `app.settings.development`        | Settings module      |
| `ALLOWED_HOSTS`          | ✅       | `localhost,127.0.0.1`             | Django allowed hosts |
| `CORS_ALLOWED_ORIGINS`   | ✅       | `http://localhost`                | Allowed CORS origins |
| `AWS_S3_BUCKET_NAME`     | ✅       | `taskflow-uploads-abc123`         | S3 bucket            |
| `AWS_REGION`             | ✅       | `us-east-1`                       | AWS region           |
| `VITE_API_URL`           | frontend | `http://localhost`                | API base URL         |
