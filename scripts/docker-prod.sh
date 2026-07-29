#!/bin/bash
# Helper script to build and run the production frontend Docker container

echo "▶ Building frontend production Docker image..."
docker build -f docker/Dockerfile.frontend.prod -t asterion-frontend-prod .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "▶ Stopping existing container if running..."
    docker rm -f asterion-frontend-prod-run 2>/dev/null || true
    
    echo "▶ Starting production container on port 3000..."
    docker run -d -p 3000:3000 --name asterion-frontend-prod-run asterion-frontend-prod
    
    echo "🎉 Frontend production build running at http://localhost:3000"
else
    echo "❌ Build failed!"
    exit 1
fi
