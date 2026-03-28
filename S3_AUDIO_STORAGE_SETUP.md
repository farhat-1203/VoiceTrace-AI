# S3 Audio Storage Configuration

## Overview

All audio files are stored in AWS S3 (NOT Supabase Storage). Presigned URLs are stored in the database for faster referencing.

---

## Storage Architecture

```
User uploads audio (3-min recording)
    ↓
Audio saved temporarily to backend/uploads/
    ↓
LangGraph pipeline processes audio
    ↓
Audio uploaded to S3
    ├─ Bucket: AWS_S3_BUCKET (from .env)
    ├─ Path: user_id/session_id.ext
    └─ Metadata: user_id, session_id
    ↓
Generate S3 presigned URL (expires in 7 days)
    ↓
Store in database:
    ├─ transcriptions.audio_url (presigned URL)
    ├─ transcriptions.audio_storage_path (S3 key)
    ├─ ledger_entries.audio_url (presigned URL)
    ├─ ledger_entries.audio_storage_path (S3 key)
    └─ audio_segments.audio_url (presigned URL)
    ↓
Delete temporary file from backend/uploads/
```

---

## Database Schema

### transcriptions table
```sql
ALTER TABLE public.transcriptions 
ADD COLUMN audio_url TEXT,              -- S3 presigned URL (expires after 7 days)
ADD COLUMN audio_storage_path TEXT;     -- S3 key for regenerating URLs
```

### ledger_entries table
```sql
ALTER TABLE public.ledger_entries 
ADD COLUMN audio_url TEXT,              -- S3 presigned URL (expires after 7 days)
ADD COLUMN audio_storage_path TEXT;     -- S3 key for regenerating URLs
```

### audio_segments table
```sql
-- Already has audio_url column
-- Stores presigned URL for full audio
```

---

## Environment Variables

```bash
# AWS S3 Configuration (REQUIRED)
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=voicetrace-audio

# Storage backend is hardcoded to S3
# AUDIO_STORAGE_BACKEND is no longer used
```

---

## S3 Bucket Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://voicetrace-audio --region us-east-1
```

### 2. Configure Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBackendAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/voicetrace-backend"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::voicetrace-audio/*"
    }
  ]
}
```

### 3. Enable CORS (if needed for direct browser access)

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

### 4. Configure Lifecycle Policy (Optional)

Delete old audio files after 30 days:

```json
{
  "Rules": [
    {
      "Id": "DeleteOldAudio",
      "Status": "Enabled",
      "Prefix": "",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

---

## IAM User Setup

### 1. Create IAM User

```bash
aws iam create-user --user-name voicetrace-backend
```

### 2. Create Access Key

```bash
aws iam create-access-key --user-name voicetrace-backend
```

Save the output:
- `AccessKeyId` → `AWS_ACCESS_KEY_ID`
- `SecretAccessKey` → `AWS_SECRET_ACCESS_KEY`

### 3. Attach Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::voicetrace-audio",
        "arn:aws:s3:::voicetrace-audio/*"
      ]
    }
  ]
}
```

```bash
aws iam put-user-policy \
  --user-name voicetrace-backend \
  --policy-name S3AudioAccess \
  --policy-document file://s3-policy.json
```

---

## Storage Path Format

### S3 Key Structure
```
user_id/session_id.ext

Example:
550e8400-e29b-41d4-a716-446655440000/7c9e6679-7425-40de-944b-e07fc1f90ae7.mp3
```

### Presigned URL Example
```
https://voicetrace-audio.s3.us-east-1.amazonaws.com/550e8400-e29b-41d4-a716-446655440000/7c9e6679-7425-40de-944b-e07fc1f90ae7.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Date=...&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=...
```

---

## Presigned URL Expiration

### Default Expiration
- **7 days (604800 seconds)** for transcriptions and ledger entries
- URLs expire and need to be regenerated

### Regenerating Presigned URLs

```python
from services.audio_storage_service import audio_storage_service

# Get storage path from database
storage_path = "user_id/session_id.mp3"

# Generate new presigned URL
new_url = audio_storage_service.get_presigned_url(
    storage_path=storage_path,
    expires_in=604800  # 7 days
)

# Update database
supabase_service._client.table("transcriptions").update({
    "audio_url": new_url
}).eq("audio_storage_path", storage_path).execute()
```

---

## Code Flow

### 1. Upload Audio (main.py)

```python
# Upload to S3 BEFORE storing transcription
audio_storage_path = audio_storage_service.upload_audio(
    file_path=file_path,
    user_id=user_id,
    session_id=session_id,
)

# Generate presigned URL
audio_url = audio_storage_service.get_presigned_url(
    storage_path=audio_storage_path,
    expires_in=604800,  # 7 days
)

# Store transcription with audio URLs
transcription_id = supabase_service.store_transcription(
    user_id=user_id,
    transcript=transcript,
    audio_url=audio_url,
    audio_storage_path=audio_storage_path,
    # ... other fields
)
```

### 2. Create Ledger Entry (ledger_service.py)

```python
# Create ledger entry with audio URLs
ledger_entry_id = ledger_service.create_entry_from_transcription(
    user_id=user_id,
    transcription_id=transcription_id,
    extracted_data=extracted_data,
    audio_url=audio_url,
    audio_storage_path=audio_storage_path,
)
```

### 3. Store Audio Segments (audio_storage_service.py)

```python
# Store segment metadata with audio URL
audio_storage_service.store_audio_segments(
    transcription_id=transcription_id,
    segments=segments,
    audio_url=audio_url,
)
```

---

## Database Queries

### Get Transcription with Audio

```sql
SELECT 
    id,
    transcript,
    audio_url,
    audio_storage_path,
    created_at
FROM transcriptions
WHERE user_id = 'user-uuid'
ORDER BY created_at DESC;
```

### Get Ledger Entry with Audio

```sql
SELECT 
    le.id,
    le.entry_date,
    le.audio_url,
    le.audio_storage_path,
    t.transcript
FROM ledger_entries le
LEFT JOIN transcriptions t ON le.transcription_id = t.id
WHERE le.user_id = 'user-uuid'
ORDER BY le.entry_date DESC;
```

### Get Audio Segments

```sql
SELECT 
    segment_index,
    start_time,
    end_time,
    text,
    audio_url
FROM audio_segments
WHERE transcription_id = 'transcription-uuid'
ORDER BY segment_index;
```

---

## Testing

### 1. Test S3 Upload

```bash
# Upload test file
curl -X POST http://localhost:8000/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test-audio.mp3"
```

### 2. Verify S3 Storage

```bash
# List files in bucket
aws s3 ls s3://voicetrace-audio/ --recursive

# Check file exists
aws s3 ls s3://voicetrace-audio/user-id/session-id.mp3
```

### 3. Test Presigned URL

```bash
# Get presigned URL from database
psql -h your-supabase-host -d postgres -c \
  "SELECT audio_url FROM transcriptions WHERE id = 'transcription-uuid';"

# Test URL (should download audio)
curl -I "PRESIGNED_URL"
```

---

## Troubleshooting

### Issue: Audio not uploading to S3

**Check:**
1. AWS credentials are correct in `.env`
2. IAM user has S3 permissions
3. Bucket exists and is accessible
4. boto3 is installed: `pip install boto3`

**Debug:**
```python
# Test S3 connection
import boto3
s3 = boto3.client('s3',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET',
    region_name='us-east-1'
)
s3.list_buckets()
```

### Issue: Presigned URLs not working

**Check:**
1. URL hasn't expired (7 days)
2. S3 bucket policy allows GetObject
3. CORS is configured if accessing from browser

**Regenerate URL:**
```python
from services.audio_storage_service import audio_storage_service
new_url = audio_storage_service.get_presigned_url(
    storage_path="user_id/session_id.mp3",
    expires_in=604800
)
```

### Issue: Database columns missing

**Run migration:**
```sql
-- Run migrations/004_add_audio_url_fields.sql
ALTER TABLE public.transcriptions 
ADD COLUMN IF NOT EXISTS audio_url TEXT,
ADD COLUMN IF NOT EXISTS audio_storage_path TEXT;

ALTER TABLE public.ledger_entries 
ADD COLUMN IF NOT EXISTS audio_url TEXT,
ADD COLUMN IF NOT EXISTS audio_storage_path TEXT;
```

---

## Cost Estimation

### S3 Storage Costs (us-east-1)

**Assumptions:**
- 100 users
- 1 audio file per day per user (3 minutes)
- Audio file size: ~3 MB (MP3, 128kbps)
- Retention: 30 days

**Monthly Storage:**
- Files: 100 users × 30 days = 3,000 files
- Size: 3,000 × 3 MB = 9 GB
- Cost: 9 GB × $0.023/GB = **$0.21/month**

**Monthly Requests:**
- PUT: 3,000 uploads × $0.005/1000 = **$0.015**
- GET: 10,000 downloads × $0.0004/1000 = **$0.004**

**Total: ~$0.23/month** for 100 users

---

## Security Best Practices

1. **Use IAM roles** instead of access keys when running on EC2
2. **Enable S3 bucket encryption** at rest
3. **Use VPC endpoints** for S3 access from EC2
4. **Rotate access keys** regularly
5. **Monitor S3 access logs** for suspicious activity
6. **Set bucket versioning** for accidental deletion protection
7. **Use presigned URLs** with short expiration times for sensitive audio

---

## Summary

✅ All audio files stored in AWS S3 (NOT Supabase Storage)  
✅ Presigned URLs stored in database for faster referencing  
✅ URLs expire after 7 days and can be regenerated  
✅ Storage path format: `user_id/session_id.ext`  
✅ Database tables updated with audio_url and audio_storage_path columns  
✅ Migration script provided: `migrations/004_add_audio_url_fields.sql`  

---

**Status:** ✅ COMPLETE  
**Last Updated:** March 29, 2026  
**Version:** 1.0
