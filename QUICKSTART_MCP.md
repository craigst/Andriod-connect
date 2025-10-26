# MCP Server - Quick Start Guide

Get your AI-powered paperwork automation running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] VS Code with Cline extension installed
- [ ] Your Flask API running or ready to start

## Step 1: Install Dependencies (1 minute)

```bash
cd /home/craigst/Nextcloud/Documents/projects/Andriod-connect
pip install mcp httpx
```

## Step 2: Run Setup Script (1 minute)

```bash
./start_mcp.sh
```

This will:
1. Check if Flask API is running
2. Start it if needed
3. Display your MCP configuration

## Step 3: Configure Cline (2 minutes)

1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type "Cline: Open MCP Settings"
4. Copy the configuration from the script output
5. Save and restart Cline

The configuration should look like:

```json
{
  "mcpServers": {
    "android-paperwork": {
      "command": "python3",
      "args": [
        "/home/craigst/Nextcloud/Documents/projects/Andriod-connect/mcp_server.py"
      ],
      "env": {
        "FLASK_API_URL": "http://localhost:5020"
      }
    }
  }
}
```

## Step 4: Test It! (1 minute)

Open Cline in VS Code and try:

```
Check device status
```

If you see device information, **it's working!** 🎉

## First Tasks to Try

### Pull Latest Data

```
Pull latest data from my phone
```

### View Today's Loads

```
What loads do I have today?
```

### Generate Paperwork

```
Generate paperwork for all loads this week
```

## Troubleshooting

### "API request failed"
- Flask API isn't running
- Run: `python server.py`

### "Failed to connect to MCP server"
- Check the path in MCP settings is correct
- Verify: `python3 mcp_server.py` runs without errors

### "Database not found"
- Pull data first: `Pull latest data from device`

## What's Next?

Check out:
- `MCP_EXAMPLE_PROMPTS.md` - Tons of example prompts
- `README_MCP.md` - Complete documentation
- Start automating your paperwork! 🚀

## Daily Workflow

1. **Morning:**
   ```
   Pull latest data, then show me today's loads
   ```

2. **Generate Paperwork:**
   ```
   Generate all loadsheets for today
   ```

3. **End of Week:**
   ```
   Help me create my timesheet for this week
   ```

That's it! You're ready to let AI handle your paperwork.

---

**Need Help?** See `README_MCP.md` for detailed documentation.
