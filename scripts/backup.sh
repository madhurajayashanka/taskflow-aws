#!/bin/bash
set -e

TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
BACKUP_FILE="/tmp/taskflow-backup-${TIMESTAMP}.sql.gz"
S3_BUCKET=${AWS_S3_BUCKET_NAME}

echo "[$(date)] Starting database backup..."

docker compose exec -T db pg_dump \
  -U "${POSTGRES_USER}" \
  "${POSTGRES_DB}" | gzip > "${BACKUP_FILE}"

aws s3 cp "${BACKUP_FILE}" \
  "s3://${S3_BUCKET}/backups/${TIMESTAMP}.sql.gz" \
  --region "${AWS_REGION:-us-east-1}"

rm -f "${BACKUP_FILE}"
echo "[$(date)] Backup complete: s3://${S3_BUCKET}/backups/${TIMESTAMP}.sql.gz"
