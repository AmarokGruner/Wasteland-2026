#!/bin/bash

# =====================================================
# Wasteland Deployment Script
# Tested on: Linux, macOS, Windows (Git Bash/WSL)
# =====================================================

set -e

# Configuration
IMAGE_NAME="wasteland"
CONTAINER_NAME="wasteland"
PORT=8000
DB_FILE="verbrannte_zone.db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    log_info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_warn "Docker Compose not found. Will use plain docker commands."
        USE_COMPOSE=false
    else
        USE_COMPOSE=true
    fi
    
    log_success "Docker is available"
}

# Build the Docker image
build_image() {
    log_info "Building Docker image: $IMAGE_NAME"
    
    if [ "$USE_COMPOSE" = true ]; then
        docker compose build
    else
        docker build -t $IMAGE_NAME .
    fi
    
    log_success "Image built successfully"
}

# Run the container
run_container() {
    log_info "Starting container: $CONTAINER_NAME"
    
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Container already exists. Removing old container..."
        docker rm -f $CONTAINER_NAME
    fi
    
    # Check if DB file exists
    if [ -f "$DB_FILE" ]; then
        log_info "Found existing database: $DB_FILE"
    else
        log_warn "No database file found. A new one will be created."
    fi
    
    if [ "$USE_COMPOSE" = true ]; then
        docker compose up -d
    else
        # Map volume for database persistence
        DB_VOLUME=""
        if [ -f "$DB_FILE" ]; then
            DB_VOLUME="-v $(pwd)/$DB_FILE:/app/$DB_FILE"
        fi
        
        docker run -d \
            --name $CONTAINER_NAME \
            -p $PORT:8000 \
            $DB_VOLUME \
            -e SECRET_KEY=${SECRET_KEY:-wasteland_ultra_secure_secret_2026} \
            --restart unless-stopped \
            $IMAGE_NAME
    fi
    
    log_success "Container started"
}

# Stop the container
stop_container() {
    log_info "Stopping container: $CONTAINER_NAME"
    
    if [ "$USE_COMPOSE" = true ]; then
        docker compose stop
    else
        docker stop $CONTAINER_NAME 2>/dev/null || true
    fi
    
    log_success "Container stopped"
}

# Remove the container
remove_container() {
    log_info "Removing container: $CONTAINER_NAME"
    
    if [ "$USE_COMPOSE" = true ]; then
        docker compose down
    else
        docker rm -f $CONTAINER_NAME 2>/dev/null || true
    fi
    
    log_success "Container removed"
}

# Show logs
show_logs() {
    if [ "$USE_COMPOSE" = true ]; then
        docker compose logs -f
    else
        docker logs -f $CONTAINER_NAME
    fi
}

# Show status
show_status() {
    if [ "$USE_COMPOSE" = true ]; then
        docker compose ps
    else
        docker ps --filter "name=$CONTAINER_NAME"
    fi
}

# Quick status check - is the API responding?
health_check() {
    log_info "Checking API health..."
    
    MAX_RETRIES=30
    RETRY_INTERVAL=2
    
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s http://localhost:$PORT/docs &>/dev/null; then
            log_success "API is responding on port $PORT"
            return 0
        fi
        
        if [ $i -lt $MAX_RETRIES ]; then
            log_info "Waiting for API... (attempt $i/$MAX_RETRIES)"
            sleep $RETRY_INTERVAL
        fi
    done
    
    log_error "API health check failed"
    return 1
}

# Full deployment: build + run + health check
deploy() {
    log_info "Starting full deployment..."
    
    check_docker
    build_image
    run_container
    
    if health_check; then
        log_success "Deployment completed successfully!"
        echo ""
        echo "========================================"
        echo "  Wasteland API: http://localhost:$PORT"
        echo "  Swagger UI:    http://localhost:$PORT/docs"
        echo "  Game UI:       http://localhost:$PORT/login.html"
        echo "========================================"
    else
        log_error "Deployment failed. Check logs with: ./deploy.sh logs"
        exit 1
    fi
}

# Usage information
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy      Build and start the container (default)"
    echo "  build       Build only the Docker image"
    echo "  start       Start the container (requires built image)"
    echo "  stop        Stop the container"
    echo "  restart     Restart the container"
    echo "  remove      Remove the container completely"
    echo "  logs        Show container logs (follow mode)"
    echo "  status      Show container status"
    echo "  health      Check if API is responding"
    echo ""
    echo "Examples:"
    echo "  $0 deploy          # Full deployment"
    echo "  $0 logs            # View logs"
    echo "  $0 restart         # Restart container"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    build)
        check_docker
        build_image
        ;;
    start)
        run_container
        health_check || log_warn "Health check failed"
        ;;
    stop)
        stop_container
        ;;
    restart)
        stop_container
        run_container
        health_check || log_warn "Health check failed"
        ;;
    remove)
        stop_container
        remove_container
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    health)
        health_check
        ;;
    *)
        usage
        exit 1
        ;;
esac