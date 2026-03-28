#!/bin/bash

# VoiceTrace AI - Clean Deployment Script
# Fixes Docker build cache corruption issues

set -e  # Exit on error

echo "🚀 VoiceTrace AI - Clean Deployment"
echo "===================================="
echo ""

# Step 1: Stop and remove all containers
echo "📦 Step 1: Stopping containers..."
docker compose down 2>/dev/null || true
echo "✅ Containers stopped"
echo ""

# Step 2: Clean Docker build cache
echo "🧹 Step 2: Cleaning Docker build cache..."
docker builder prune -af --filter "until=1h"
echo "✅ Build cache cleaned"
echo ""

# Step 3: Remove old images
echo "🗑️  Step 3: Removing old images..."
docker rmi voicetrace-ai-backend:latest 2>/dev/null || true
docker rmi voicetrace-ai-streamlit:latest 2>/dev/null || true
echo "✅ Old images removed"
echo ""

# Step 4: Build with no cache
echo "🔨 Step 4: Building images (no cache)..."
docker compose build --no-cache --progress=plain
echo "✅ Images built successfully"
echo ""

# Step 5: Start services
echo "🚀 Step 5: Starting services..."
docker compose up -d
echo "✅ Services started"
echo ""

# Step 6: Wait for services to be ready
echo "⏳ Step 6: Waiting for services to be ready..."
sleep 5

# Check backend health
echo "🔍 Checking backend health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend health check timeout (this is normal on first start)"
    fi
    sleep 2
done
echo ""

# Step 7: Show logs
echo "📋 Step 7: Service status"
echo "========================"
docker compose ps
echo ""

echo "✅ Deployment complete!"
echo ""
echo "📍 Services:"
echo "   - Backend:  http://localhost:8000"
echo "   - Frontend: http://localhost:8501"
echo "   - Health:   http://localhost:8000/health"
echo ""
echo "📝 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
