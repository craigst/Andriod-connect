#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Android-Connect Docker Container${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
FLASK_PORT=5020
FLASK_HOST="localhost"

# Start Flask API
echo -e "${YELLOW}📡 Starting Flask API on port ${FLASK_PORT}...${NC}"
python3 /app/server.py > /app/logs/flask.log 2>&1 &
FLASK_PID=$!
echo "Flask API PID: $FLASK_PID"

# Wait for Flask to be ready
echo -e "${YELLOW}⏳ Waiting for Flask API to be ready...${NC}"
MAX_WAIT=30
COUNT=0
while [ $COUNT -lt $MAX_WAIT ]; do
    if curl -s "http://${FLASK_HOST}:${FLASK_PORT}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Flask API is ready${NC}"
        break
    fi
    COUNT=$((COUNT + 1))
    if [ $COUNT -eq $MAX_WAIT ]; then
        echo -e "${RED}❌ Flask API failed to start within ${MAX_WAIT} seconds${NC}"
        echo "Check /app/logs/flask.log for details"
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Flask API Started Successfully${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Service Status:${NC}"
echo -e "  📡 Flask API:  http://localhost:${FLASK_PORT} (PID: ${FLASK_PID})"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "  Flask API:  /app/logs/flask.log"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Service Running${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Note: MCP server is now a separate project.${NC}"
echo -e "${YELLOW}      See mcp-server/ directory for standalone MCP server.${NC}"
echo ""
echo -e "${GREEN}Container will remain running. Press Ctrl+C to stop.${NC}"
echo ""

# Keep container alive by tailing logs
tail -f /app/logs/flask.log
