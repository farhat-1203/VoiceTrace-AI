#!/bin/bash

# Quick fix for Docker build cache corruption on EC2
# Run this when you get "parent snapshot does not exist" error

set -e

echo "🔧 Fixing Docker build cache corruption..."
echo ""

# Stop all containers
echo "1️⃣  Stopping containers..."
docker compose down 2>/dev/null || true

# Remove dangling images and build cache
echo "2️⃣  Cleaning Docker system..."
docker system prune -af --volumes

# Remove specific images
echo "3️⃣  Removing VoiceTrace images..."
docker rmi $(docker images -q voicetrace-ai-backend) 2>/dev/null || true
docker rmi $(docker images -q voicetrace-ai-streamlit) 2>/dev/null || true

# Clear buildx cache
echo "4️⃣  Clearing buildx cache..."
docker buildx prune -af

# Rebuild from scratch
echo "5️⃣  Building images (no cache)..."
DOCKER_BUILDKIT=1 docker compose build --no-cache --pull

# Start services
echo "6️⃣  Starting services..."
docker compose up -d

echo ""
echo "✅ Done! Check status with: docker compose ps"
echo "📋 View logs with: docker compose logs -f"
