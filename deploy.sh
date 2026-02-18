#!/bin/bash
set -e

echo "========================================="
echo "  Zoniq - Production Deployment Script"
echo "========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Check .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Copy .env.example to .env and fill in your production values:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo ""
echo "Building and starting all services..."
echo ""

docker compose -f docker-compose.prod.yaml up -d --build

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Services:"
docker compose -f docker-compose.prod.yaml ps
echo ""
echo "Access your application at: http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')"
echo ""
echo "Useful commands:"
echo "  View logs:     docker compose -f docker-compose.prod.yaml logs -f"
echo "  Stop:          docker compose -f docker-compose.prod.yaml down"
echo "  Restart:       docker compose -f docker-compose.prod.yaml restart"
echo "  Backend logs:  docker compose -f docker-compose.prod.yaml logs -f backend"
