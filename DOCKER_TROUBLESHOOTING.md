# Docker Troubleshooting Guide

## Common Issues and Solutions

---

## Issue 1: "parent snapshot does not exist: not found"

### Symptoms
```
failed to prepare extraction snapshot: parent snapshot does not exist: not found
```

### Cause
Docker build cache corruption, common on EC2 instances with limited disk space or after interrupted builds.

### Solution

**Option A: Quick Fix (Recommended)**
```bash
# Make script executable
chmod +x fix-docker-build.sh

# Run the fix script
./fix-docker-build.sh
```

**Option B: Manual Fix**
```bash
# 1. Stop containers
docker compose down

# 2. Clean everything
docker system prune -af --volumes

# 3. Remove VoiceTrace images
docker rmi $(docker images -q voicetrace-ai-backend) 2>/dev/null || true
docker rmi $(docker images -q voicetrace-ai-streamlit) 2>/dev/null || true

# 4. Clear buildx cache
docker buildx prune -af

# 5. Rebuild without cache
DOCKER_BUILDKIT=1 docker compose build --no-cache --pull

# 6. Start services
docker compose up -d
```

---

## Issue 2: "version is obsolete" Warning

### Symptoms
```
WARN[0000] the attribute `version` is obsolete
```

### Cause
Docker Compose v2 doesn't require version field.

### Solution
Already fixed in `docker-compose.yml`. The warning is harmless but has been removed.

---

## Issue 3: Out of Disk Space

### Symptoms
```
no space left on device
```

### Check Disk Space
```bash
df -h
docker system df
```

### Solution
```bash
# Remove unused Docker data
docker system prune -af --volumes

# Remove old logs
sudo journalctl --vacuum-time=3d

# Check again
df -h
```

---

## Issue 4: Port Already in Use

### Symptoms
```
bind: address already in use
```

### Check Ports
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Check what's using port 8501
sudo lsof -i :8501
```

### Solution
```bash
# Kill process using the port
sudo kill -9 $(sudo lsof -t -i:8000)
sudo kill -9 $(sudo lsof -t -i:8501)

# Or change ports in docker-compose.yml
# Change "8000:8000" to "8080:8000"
```

---

## Issue 5: Container Keeps Restarting

### Check Logs
```bash
# View all logs
docker compose logs

# View specific service
docker compose logs backend
docker compose logs streamlit

# Follow logs in real-time
docker compose logs -f backend
```

### Common Causes

**Missing Environment Variables**
```bash
# Check .env file exists
ls -la .env

# Verify required variables
cat .env | grep -E "GROQ_API_KEY|SUPABASE_URL|AWS_ACCESS_KEY_ID"
```

**Database Connection Issues**
```bash
# Test Supabase connection
curl -H "apikey: YOUR_SUPABASE_ANON_KEY" \
  "YOUR_SUPABASE_URL/rest/v1/"
```

**S3 Connection Issues**
```bash
# Test AWS credentials
docker compose exec backend python -c "
import boto3
s3 = boto3.client('s3')
print(s3.list_buckets())
"
```

---

## Issue 6: Backend Not Responding

### Check Backend Health
```bash
# Health check
curl http://localhost:8000/health

# Check if container is running
docker compose ps

# Check backend logs
docker compose logs backend --tail=50
```

### Solution
```bash
# Restart backend
docker compose restart backend

# Or rebuild
docker compose up -d --build backend
```

---

## Issue 7: Frontend Can't Connect to Backend

### Symptoms
- Frontend loads but shows connection errors
- API calls fail

### Check Network
```bash
# Check if backend is accessible from streamlit container
docker compose exec streamlit curl http://backend:8000/health

# Check environment variables
docker compose exec streamlit env | grep BACKEND_URL
```

### Solution
```bash
# Ensure BACKEND_URL is set correctly in docker-compose.yml
# Should be: http://backend:8000 (not localhost)

# Restart services
docker compose restart
```

---

## Issue 8: Permission Denied Errors

### Symptoms
```
permission denied while trying to connect to the Docker daemon socket
```

### Solution
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (logout/login or run)
newgrp docker

# Verify
docker ps
```

---

## Issue 9: Build Takes Too Long

### Symptoms
- Build hangs on pip install
- Timeout errors

### Solution
```bash
# Increase timeout in Dockerfile
# Change: --timeout 120
# To: --timeout 300

# Or use faster mirror
docker compose build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## Issue 10: Container Exits Immediately

### Check Exit Code
```bash
# View container status
docker compose ps -a

# Check logs
docker compose logs backend
```

### Common Causes

**Missing Dependencies**
```bash
# Rebuild with no cache
docker compose build --no-cache backend
```

**Configuration Errors**
```bash
# Validate .env file
cat .env | grep -v "^#" | grep -v "^$"

# Check for syntax errors
docker compose config
```

---

## Useful Commands

### Monitoring
```bash
# View all containers
docker compose ps

# View resource usage
docker stats

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
```

### Debugging
```bash
# Enter backend container
docker compose exec backend bash

# Enter streamlit container
docker compose exec streamlit bash

# Run Python in backend
docker compose exec backend python

# Test imports
docker compose exec backend python -c "import fastapi; print('OK')"
```

### Cleanup
```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# Remove all Docker data
docker system prune -af --volumes

# Remove specific image
docker rmi voicetrace-ai-backend:latest
```

### Rebuilding
```bash
# Rebuild specific service
docker compose build backend

# Rebuild without cache
docker compose build --no-cache

# Rebuild and restart
docker compose up -d --build
```

---

## EC2-Specific Issues

### Issue: Low Memory

**Check Memory**
```bash
free -h
docker stats
```

**Solution**
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: Slow Network

**Check Network**
```bash
# Test download speed
curl -o /dev/null http://speedtest.tele2.net/10MB.zip

# Check DNS
nslookup google.com
```

**Solution**
```bash
# Use faster DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Issue: Security Group Blocks Ports

**Check Ports**
```bash
# Test from outside
curl http://YOUR_EC2_IP:8000/health
```

**Solution**
- Open AWS Console → EC2 → Security Groups
- Add inbound rules:
  - Port 8000 (Backend)
  - Port 8501 (Frontend)
  - Source: 0.0.0.0/0 (or your IP)

---

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "backend": "running",
    "qdrant_cloud": "connected",
    "supabase": "connected"
  }
}
```

### Frontend Health
```bash
curl -I http://localhost:8501
```

Expected: `HTTP/1.1 200 OK`

### Database Health
```bash
# Test Supabase connection
curl -H "apikey: YOUR_ANON_KEY" \
  "YOUR_SUPABASE_URL/rest/v1/"
```

### S3 Health
```bash
# Test S3 access
docker compose exec backend python -c "
import boto3
import os
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
print('Buckets:', [b['Name'] for b in s3.list_buckets()['Buckets']])
"
```

---

## Complete Reset

If all else fails, do a complete reset:

```bash
# 1. Stop everything
docker compose down -v

# 2. Remove all Docker data
docker system prune -af --volumes

# 3. Remove VoiceTrace images
docker rmi $(docker images -q voicetrace-ai-*) 2>/dev/null || true

# 4. Clear buildx cache
docker buildx prune -af

# 5. Verify .env file
cat .env

# 6. Rebuild from scratch
DOCKER_BUILDKIT=1 docker compose build --no-cache --pull

# 7. Start services
docker compose up -d

# 8. Check logs
docker compose logs -f
```

---

## Getting Help

### Collect Debug Info
```bash
# System info
uname -a
docker --version
docker compose version

# Disk space
df -h

# Memory
free -h

# Docker info
docker info

# Container status
docker compose ps -a

# Recent logs
docker compose logs --tail=100

# Environment (sanitized)
cat .env | grep -v "KEY\|SECRET\|PASSWORD"
```

### Share Logs
```bash
# Save logs to file
docker compose logs > docker-logs.txt

# Save last 200 lines
docker compose logs --tail=200 > docker-logs-recent.txt
```

---

## Prevention

### Regular Maintenance
```bash
# Weekly cleanup
docker system prune -f

# Monthly deep clean
docker system prune -af --volumes
```

### Monitoring
```bash
# Add to crontab for daily checks
0 0 * * * docker system df >> /var/log/docker-usage.log
```

### Backups
```bash
# Backup .env file
cp .env .env.backup

# Backup database (if using local DB)
docker compose exec backend pg_dump > backup.sql
```

---

## Quick Reference

| Issue | Command |
|-------|---------|
| Build cache error | `./fix-docker-build.sh` |
| Out of space | `docker system prune -af --volumes` |
| Port in use | `sudo lsof -i :8000` |
| View logs | `docker compose logs -f` |
| Restart service | `docker compose restart backend` |
| Rebuild | `docker compose up -d --build` |
| Enter container | `docker compose exec backend bash` |
| Check health | `curl localhost:8000/health` |
| Complete reset | `docker compose down -v && docker system prune -af` |

---

**Last Updated:** March 29, 2026  
**Version:** 1.0
