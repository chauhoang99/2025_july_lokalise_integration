# Lokalise Translation Pipeline

This project implements an automated translation pipeline that integrates Lokalise with AI-powered translations.

## Prerequisites

- Docker and Docker Compose
- A Lokalise account with API key and project ID
- An OpenRouter account with API key

## Quick Start Guide

1. **Clone the Repository**
```bash
git clone https://github.com/chauhoang99/2025_july_lokalise_integration.git
cd 2025_july_lokalise_integration
```

2. **Set Up Environment Variables**

Environment Variables are hard-coded in docker-compose file
Yes it is not a good practice but should be fine for a POC
The API keys can be disable at any time so should not be a big problem

LOKALISE_API_KEY=your_lokalise_api_key
LOKALISE_PROJECT_ID=your_lokalise_project_id
OPEN_ROUTER_API_KEY=your_openrouter_api_key
SECRET_KEY=django_secret_key
DEBUG=True
NUXT_PUBLIC_API_BASE=http://web:8000/api

3. **Build and Run with Docker**
```bash
# Build and start all services
docker-compose up -d --build
```

4. **Access the Application**
- Frontend UI: http://localhost:3000
- Backend API: http://localhost:8000/api

## Troubleshooting Docker Issues

If you encounter any issues:

1. **Check if ports are available**
```bash
# On Windows:
netstat -ano | findstr "3000"
netstat -ano | findstr "8000"

# On macOS/Linux:
lsof -i :3000
lsof -i :8000
```

2. **Clean up Docker resources**
```bash
# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Clean up Docker cache
docker system prune -a

# Rebuild from scratch
docker-compose up --build
```

3. **View logs**
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs frontend
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f
```

4. **Common Issues**

- **Error: "port is already allocated"**
  - Stop any services using ports 3000 or 8000
  - Or modify the ports in `docker-compose.yml`

- **Error: "connection refused"**
  - Wait a few moments for services to fully start
  - Check if all containers are running: `docker-compose ps`

- **Container exits immediately**
  - Check logs: `docker-compose logs`
  - Verify environment variables are set correctly

## Stopping the Application

```bash
# Stop all services but keep containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers and volumes
docker-compose down -v
``` 
