# clay-garage-door 🚗

Garage Door Controller CLI for Home Assistant. Control your garage doors from the command line!

## Features

- 🚪 **List** all garage door entities in Home Assistant
- 📊 **Status** check - see if doors are open or closed
- 🔓 **Open** garage doors remotely
- 🔒 **Close** garage doors remotely
- 🔄 **Toggle** garage door state
- 📄 **JSON output** for scripting and automation

## Installation

```bash
# Clone or copy to your tools directory
cp clay_garage_door.py ~/clay/tools/clay_garage_door.py
chmod +x ~/clay/tools/clay_garage_door.py

# Or use directly
python3 clay_garage_door.py --help
```

## Configuration

### Home Assistant Token

Set your Home Assistant Long-Lived Access Token:

```bash
# Option 1: Environment variable
export HA_TOKEN="your_long_lived_access_token"

# Option 2: Create a secrets file
mkdir -p ~/.clay/.secrets
echo "your_long_lived_access_token" > ~/.clay/.secrets/ha-token
```

To create a token:
1. Go to your Home Assistant UI
2. Click your profile icon (bottom left)
3. Scroll down to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Give it a name (e.g., "clay-garage-door")

### Home Assistant URL (optional)

```bash
# Default: http://192.168.1.135:8123
export HA_URL="http://192.168.1.135:8123"
```

## Usage

```bash
# List all garage doors
python3 clay_garage_door.py list

# Show status of all garage doors
python3 clay_garage_door.py status

# Show status of specific door
python3 clay_garage_door.py status cover.garage_door

# Open garage door (prompts if multiple)
python3 clay_garage_door.py open

# Open specific door
python3 clay_garage_door.py open cover.garage_door

# Close garage door
python3 clay_garage_door.py close
python3 clay_garage_door.py close cover.garage_door

# Toggle garage door
python3 clay_garage_door.py toggle
python3 clay_garage_door.py toggle cover.garage_door

# JSON output for scripting
python3 clay_garage_door.py status --json
python3 clay_garage_door.py open cover.garage_door --json
```

## Examples

### Check if garage door is open

```bash
$ python3 clay_garage_door.py status

Garage Door Status:

🔒 Main Garage Door
   Entity: cover.garage_door
   State: CLOSED
```

### Open garage door

```bash
$ python3 clay_garage_door.py open

Opening Main Garage Door...
✓ Done!
```

### Scripting: Check if any door is open

```bash
#!/bin/bash
STATUS=$(python3 clay_garage_door.py status --json)
IS_OPEN=$(echo $STATUS | jq '.[] | select(.state == "open")')

if [ -n "$IS_OPEN" ]; then
    echo "WARNING: Garage door is open!"
    # Send alert
fi
```

## Requirements

- Python 3.7+
- requests

```bash
pip install requests
```

## Use Cases

- **Peace of mind**: "Did I leave the garage door open?"
- **Remote control**: Open garage door for delivery while away
- **Automation**: Add to morning/evening routines
- **Voice control**: Integrate with clay-voice for voice commands

## Integration Ideas

### With clay-voice (voice announcements)

```bash
# Announce garage door status
python3 clay_garage_door.py status
# Then use clay_voice to speak the result
```

### Morning/Evening Routines

Add to your morning briefing:
```bash
# Check garage door status as part of morning routine
python3 clay_garage_door.py status
```

### Cron Job - Reminder

```bash
# Remind if garage door is left open at night
0 22 * * * python3 /path/to/clay_garage_door.py status
```

## Troubleshooting

### "HA_TOKEN not found"

Make sure you've set the HA_TOKEN environment variable or created the secrets file:
```bash
export HA_TOKEN="your_token_here"
```

### "No garage door entities found"

Your garage door might be named differently in Home Assistant. Try:
```bash
# List all cover entities
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  http://192.168.1.135:8123/api/states | \
  python3 -c "import sys,json; [print(s['entity_id']) for s in json.load(sys.stdin) if s['entity_id'].startswith('cover.')]"
```

## License

MIT License - Feel free to use and modify!
