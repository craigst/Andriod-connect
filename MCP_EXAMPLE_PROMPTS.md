# MCP Example Prompts for Cline

This document provides example prompts you can use with Cline once the MCP server is configured. These demonstrate the natural language capabilities of the system.

## Getting Started

### Check System Status

```
Check device status
```

```
Is my data up to date?
```

```
How fresh is my database?
```

## Viewing Loads

### By Date

```
What loads do I have today?
```

```
Show me all loads for this week
```

```
What work do I have tomorrow?
```

```
List loads from last week
```

```
Show me next week's loads
```

### By Location

```
Find loads going to WBAC Ashford
```

```
Show me all BCA loads
```

```
What loads are for Paddock Wood?
```

```
Find anything going to Blackbushe
```

### General Summary

```
Show me all my loads
```

```
What loads are in the database?
```

```
List all current work
```

## Generating Paperwork

### Single Loadsheet

```
Generate loadsheet for $S275052
```

```
Make a loadsheet for load $S275053
```

```
Create paperwork for $S275054
```

### Batch Generation

```
Generate paperwork for all loads this week
```

```
Create loadsheets for all of today's work
```

```
Make loadsheets for all WBAC loads
```

```
Generate all paperwork from last week
```

### Timesheet Generation

```
Generate a timesheet for last week
```

```
Create timesheet from 14th to 20th October
```

```
Make a timesheet for this week
```

## Interactive Timesheet Entry

### Starting the Process

```
Help me create my timesheet for this week
```

```
I need to fill in my hours for the week
```

Then Cline will guide you through each day:

**Example Conversation:**

```
You: Help me create my timesheet for this week

Cline: I'll help you create your timesheet. What's the week ending date? (Should be a Sunday, format YYYY-MM-DD)

You: 2025-10-20

Cline: Great! Let's start with Monday. What time did you start?

You: 06:30

Cline: And what time did you finish?

You: 16:00

Cline: [Creates entry] Monday recorded: 9.5 hours

Cline: Now Tuesday. What time did you start?

... (continues for each day)
```

### Quick Entry (All at Once)

```
Add timesheet entry for Monday 14th Oct, started 6:30, finished 16:00
```

```
Record Tuesday: 07:00 to 17:30
```

### View Existing Entries

```
Show me my timesheet entries for this week
```

```
What hours did I enter for week ending 20th October?
```

## Device Management

### Checking Status

```
Are my devices connected?
```

```
What's the status of my phones?
```

```
Check if devices are online
```

### Pulling Data

```
Pull latest data from my phone
```

```
Update the database from device
```

```
Get fresh data
```

### Connecting Devices

```
Connect to all my devices
```

```
Reconnect devices
```

## Vehicle Lookups

### Looking Up Vehicles

```
Look up vehicle registration ABC123
```

```
What's the make and model of XYZ789?
```

```
Check vehicle DEF456
```

### Saving Overrides

```
Save vehicle override for ABC123 as Ford Transit Custom
```

```
Update XYZ789 to Mercedes Sprinter
```

## Complex Workflows

### Morning Routine

```
Pull latest data, then show me today's loads
```

```
Update database and generate all loadsheets for today
```

### End of Week Workflow

```
Generate all paperwork for this week and create my timesheet
```

```
Show me this week's loads, generate all loadsheets, then help me fill in my timesheet
```

### Data Freshness Check

```
Check how old my data is. If it's more than 2 hours old, pull fresh data
```

```
Is my database current? Pull new data if needed
```

## Troubleshooting Prompts

### When Things Don't Work

```
Why can't I see any loads?
```
*Cline will check if database exists and suggest pulling data*

```
The loadsheet generation failed
```
*Cline will explain the error and suggest solutions*

```
I can't connect to my device
```
*Cline will check device status and suggest troubleshooting steps*

## Advanced Queries

### Filtering and Searching

```
Show me loads with more than 5 vehicles
```

```
Find loads from last Monday
```

```
What loads were on 15th October?
```

### Batch Operations

```
Generate loadsheets for all loads from WBAC in the last week
```

```
Create paperwork for every load going to BCA Paddock Wood
```

### Reporting

```
How many loads do I have this week?
```

```
What's my total vehicle count for today?
```

```
List all unique locations from this week
```

## Tips for Effective Prompts

### Be Specific

✅ Good: "Generate loadsheets for all loads this week"
❌ Vague: "Make some paperwork"

### Use Natural Language

✅ Good: "What loads do I have today?"
❌ Technical: "Query loads table for current date"

### Provide Context

✅ Good: "Pull latest data, then show me today's loads"
❌ Unclear: "Show loads" (might be stale data)

### Ask for Clarification

✅ Good: "I'm not sure what loads I need paperwork for. Can you show me this week's work?"
❌ Guessing: Trying random load numbers

### Chain Operations

✅ Good: "Check database freshness. If old, pull new data. Then generate all loadsheets for today"
❌ Inefficient: Asking for each step separately

## Common Question Patterns

### "What" Questions
- What loads do I have today?
- What's the status of my devices?
- What work is scheduled for tomorrow?

### "Show/List" Requests
- Show me all loads
- List today's work
- Display device status

### "Generate/Create/Make" Commands
- Generate loadsheet for $S275052
- Create my timesheet
- Make paperwork for this week

### "Check/Verify" Queries
- Check if my data is fresh
- Verify devices are connected
- Check database status

### "Pull/Update/Refresh" Actions
- Pull latest data
- Update database
- Refresh from device

## Error Recovery Prompts

### Database Issues

```
The database seems empty, what should I do?
```

```
I'm getting database errors
```

### Connection Problems

```
My devices won't connect
```

```
Flask API isn't responding
```

### Generation Failures

```
Loadsheet generation failed for $S275052
```

```
Why didn't the timesheet generate?
```

## Pro Tips

1. **Start Each Session:** "Check device status and database freshness"

2. **Daily Workflow:** "Pull latest data, show today's loads, generate all loadsheets"

3. **Weekly Routine:** "Show this week's loads, generate all paperwork, help me create my timesheet"

4. **Before Leaving:** "Generate all outstanding paperwork and verify everything is saved"

5. **Regular Maintenance:** "Check database age - pull fresh data if needed"

## Natural Conversation Flow

Remember, you can have a natural conversation with Cline:

```
You: What do I have on for tomorrow?

Cline: Let me check your loads for tomorrow.
[Shows 3 loads]

You: Can you make paperwork for all of those?

Cline: I'll generate loadsheets for all 3 loads.
[Generates paperwork]

You: Thanks! Now what about my timesheet?

Cline: I can help you create your timesheet. What week do you need?

You: This week please

Cline: Great! Let's start with Monday...
```

## Experiment!

The MCP server is designed to understand natural language, so don't be afraid to ask questions in your own words. Cline will use the available tools to help you accomplish what you need.

Try variations of these prompts and see what works best for your workflow!
