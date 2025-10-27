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
MCP_HTTP_PORT=${MCP_PORT:-8100}
MCP_HTTP_HOST=${MCP_HOST:-0.0.0.0}

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

# Start MCP HTTP Server
echo -e "${YELLOW}🌐 Starting MCP HTTP Server on ${MCP_HTTP_HOST}:${MCP_HTTP_PORT}...${NC}"
python3 /app/mcp_server_http.py > /app/logs/mcp_http.log 2>&1 &
MCP_HTTP_PID=$!
echo "MCP HTTP Server PID: $MCP_HTTP_PID"

# Give MCP HTTP a moment to start
sleep 2

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ All Services Started Successfully${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Services Status:${NC}"
echo -e "  📡 Flask API:        http://localhost:${FLASK_PORT} (PID: ${FLASK_PID})"
echo -e "  🌐 MCP HTTP Server:  http://${MCP_HTTP_HOST}:${MCP_HTTP_PORT} (PID: ${MCP_HTTP_PID})"
echo -e "  📨 MCP SSE Endpoint: http://${MCP_HTTP_HOST}:${MCP_HTTP_PORT}/sse"
echo -e "  💬 MCP Messages:     http://${MCP_HTTP_HOST}:${MCP_HTTP_PORT}/messages"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "  Flask API:     /app/logs/flask.log"
echo -e "  MCP HTTP:      /app/logs/mcp_http.log"
echo -e "  MCP Stdio:     stdout (below)"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ All Services Running${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Note: MCP Stdio server not started (requires stdin/stdout).${NC}"
echo -e "${YELLOW}      Use MCP HTTP server on port ${MCP_HTTP_PORT} for external access.${NC}"
echo ""
echo -e "${GREEN}Container will remain running. Press Ctrl+C to stop.${NC}"
echo ""

# Keep container alive by tailing logs
tail -f /app/logs/flask.log /app/logs/mcp_http.log
