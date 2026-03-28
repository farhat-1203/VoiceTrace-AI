# Quick Fix for Docker Build Error

## The Error You're Seeing

```
parent snapshot sha256:... does not exist: not found
```

This is a Docker build cache corruption issue, common on EC2 instances.

---

## Quick Fix (Copy & Paste)

Run these commands on your EC2 instance:

```bash
# Stop containers
docker compose down

# Clean Docker system completely
docker system prune -af --volumes

# Remove VoiceTrace images
docker rmi voicetrace-ai-backend voicetrace-ai-streamlit 2>/dev/null || true

# Clear buildx cache
docker buildx prune -af

# Rebuild without cache
DOCKER_BUILDKIT=1 docker compose build --no-cache --pull

# Start services
docker compose up -d

# Check status
docker compose ps
```

---

## Or Use the Fix Script

```bash
# Make script executable
chmod +x fix-docker-build.sh

# Run it
./fix-docker-build.sh
```

---

## Verify It's Working

```bash
# Check containers are running
docker compose ps

# Check backend health
curl http://localhost:8000/health

# View logs
docker compose logs -f
```

---

## If Still Having Issues

Check disk space:
```bash
df -h
```

If disk is full (>90%), clean up:
```bash
# Remove old logs
sudo journalctl --vacuum-time=3d

# Remove unused packages
sudo apt autoremove -y

# Check again
df -h
```

---

## Expected Output

After successful deployment:

```
NAME                    IMAGE                          STATUS
voicetrace-backend      voicetrace-ai-backend:latest   Up
voicetrace-streamlit    voicetrace-ai-streamlit:latest Up
```

Health check should return:
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

---

## Access Your Application

- **Backend API:** http://YOUR_EC2_IP:8000
- **Frontend:** http://YOUR_EC2_IP:8501
- **Health Check:** http://YOUR_EC2_IP:8000/health
- **API Docs:** http://YOUR_EC2_IP:8000/docs

---

**Note:** Make sure ports 8000 and 8501 are open in your EC2 Security Group!
