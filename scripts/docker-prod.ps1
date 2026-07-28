# Helper script to build and run the production frontend Docker container on Windows

Write-Host "▶ Building frontend production Docker image..." -ForegroundColor Cyan
docker build -f docker/Dockerfile.frontend.prod -t asterion-frontend-prod .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host "▶ Stopping existing container if running..." -ForegroundColor Yellow
    docker rm -f asterion-frontend-prod-run 2>$null | Out-Null
    
    Write-Host "▶ Starting production container on port 3000..." -ForegroundColor Yellow
    docker run -d -p 3000:3000 --name asterion-frontend-prod-run asterion-frontend-prod
    
    Write-Host "🎉 Frontend production build running at http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
