#!/bin/bash
# Start MCP Server Helper Script
# Ensures Flask API is running before starting MCP server

# Configuration
FLASK_PORT=5020
FLASK_HOST="localhost"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Android-Connect MCP Server Startup${NC}"
echo "========================================"
echo ""

# Check if Flask API is running
echo -e "${YELLOW}Checking Flask API...${NC}"
if curl -s "http://${FLASK_HOST}:${FLASK_PORT}/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Flask API is running on port ${FLASK_PORT}${NC}"
else
    echo -e "${YELLOW}⚠️  Flask API is not running${NC}"
    echo -e "${YELLOW}Starting Flask API...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Start Flask in background
    python3 server.py > logs/flask.log 2>&1 &
    FLASK_PID=$!
    
    echo -e "${YELLOW}Waiting for Flask to start...${NC}"
    
    # Wait up to 10 seconds for Flask to start
    for i in {1..10}; do
        sleep 1
        if curl -s "http://${FLASK_HOST}:${FLASK_PORT}/api/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Flask API started successfully (PID: ${FLASK_PID})${NC}"
            echo "${FLASK_PID}" > /tmp/android_connect_flask.pid
            break
        fi
        
        if [ $i -eq 10 ]; then
            echo -e "${RED}❌ Flask API failed to start${NC}"
            echo "Check logs/flask.log for details"
            exit 1
        fi
    done
fi

echo ""
echo -e "${GREEN}MCP Server Configuration:${NC}"
echo "  API URL: http://${FLASK_HOST}:${FLASK_PORT}"
echo "  MCP Server: ${PROJECT_DIR}/mcp_server.py"
echo ""
echo -e "${GREEN}✅ Ready! The MCP server can now be used with Cline.${NC}"
echo ""
echo "Add this to your Cline MCP settings:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "android-paperwork": {'
echo '      "command": "python3",'
echo "      \"args\": [\"${PROJECT_DIR}/mcp_server.py\"],"
echo '      "env": {'
echo "        \"FLASK_API_URL\": \"http://${FLASK_HOST}:${FLASK_PORT}\""
echo '      }'
echo '    }'
echo '  }'
echo '}'
echo ""
echo -e "${YELLOW}Note:${NC} Flask API is running in the background."
echo "      To stop it: kill \$(cat /tmp/android_connect_flask.pid)"
echo ""
