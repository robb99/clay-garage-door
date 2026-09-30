#!/usr/bin/env python3
"""
clay-garage-door - Garage Door Controller CLI for Home Assistant

Control garage doors via Home Assistant API.
Supports: status, open, close, toggle, and listing all garage doors.

Usage:
    python3 clay_garage_door.py list          # List all garage doors
    python3 clay_garage_door.py status        # Show status of all garage doors
    python3 clay_garage_door.py status main   # Status of specific door
    python3 clay_garage_door.py open         # Open garage door (prompts for entity)
    python3 clay_garage_door.py open main    # Open specific door
    python3 clay_garage_door.py close        # Close garage door
    python3 clay_garage_door.py toggle       # Toggle garage door
    python3 clay_garage_door.py --json ...   # JSON output

Environment:
    HA_TOKEN - Home Assistant Long-Lived Access Token
    HA_URL   - Home Assistant URL (default: http://192.168.1.135:8123)
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, List, Dict, Any

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


def get_ha_config() -> Dict[str, str]:
    """Get Home Assistant configuration from environment or secrets."""
    token = os.environ.get('HA_TOKEN')
    if not token:
        # Try to read from .secrets/ha-token
        secrets_path = os.path.expanduser('~/.clay/.secrets/ha-token')
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                token = f.read().strip()
    
    if not token:
        print(f"{RED}Error: HA_TOKEN not found. Set HA_TOKEN environment variable or create ~/.clay/.secrets/ha-token{RESET}")
        sys.exit(1)
    
    url = os.environ.get('HA_URL', 'http://192.168.1.135:8123')
    return {'token': token, 'url': url}


def ha_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
    """Make request to Home Assistant API."""
    config = get_ha_config()
    headers = {
        'Authorization': f'Bearer {config["token"]}',
        'Content-Type': 'application/json'
    }
    url = f'{config["url"]}/api/{endpoint}'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else None
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error connecting to Home Assistant: {e}{RESET}")
        sys.exit(1)


def get_cover_entities() -> List[Dict]:
    """Get all cover entities (garage doors) from Home Assistant."""
    states = ha_request('GET', 'states')
    # Filter for cover domain (includes garage doors)
    covers = [s for s in states if s.get('entity_id', '').startswith('cover.')]
    return covers


def find_garage_doors() -> List[Dict]:
    """Find garage door entities specifically."""
    covers = get_cover_entities()
    # Look for entities with 'garage' in the name or entity_id
    garage_doors = [
        c for c in covers 
        if 'garage' in c.get('entity_id', '').lower() 
        or 'garage' in c.get('attributes', {}).get('friendly_name', '').lower()
    ]
    # If no explicit garage doors found, return all covers as they might be garage doors
    return garage_doors if garage_doors else covers


def get_garage_door(entity_id: str) -> Optional[Dict]:
    """Get a specific garage door entity."""
    try:
        return ha_request('GET', f'states/{entity_id}')
    except:
        return None


def control_garage_door(entity_id: str, action: str) -> bool:
    """Control a garage door (open, close, toggle)."""
    # Map action to HA service
    service_map = {
        'open': 'cover.open_cover',
        'close': 'cover.close_cover', 
        'toggle': 'cover.toggle'
    }
    
    if action not in service_map:
        print(f"{RED}Unknown action: {action}{RESET}")
        return False
    
    service = service_map[action]
    domain, action_name = service.split('.')
    
    try:
        ha_request('POST', f'services/{domain}/{action_name}', {'entity_id': entity_id})
        return True
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return False


def format_status(door: Dict, include_json: bool = False) -> Dict:
    """Format garage door status."""
    entity_id = door.get('entity_id', '')
    state = door.get('state', 'unknown')
    friendly_name = door.get('attributes', {}).get('friendly_name', entity_id)
    
    # Determine status icon and color
    if state == 'open':
        icon = '🔓'
        color = GREEN
    elif state == 'closed':
        icon = '🔒'
        color = GREEN
    elif state == 'opening':
        icon = '⬆️'
        color = YELLOW
    elif state == 'closing':
        icon = '⬇️'
        color = YELLOW
    else:
        icon = '❓'
        color = YELLOW
    
    result = {
        'entity_id': entity_id,
        'name': friendly_name,
        'state': state,
        'icon': icon
    }
    
    if include_json:
        return result
    
    # Print formatted output
    print(f"{color}{icon} {BOLD}{friendly_name}{RESET}")
    print(f"   Entity: {entity_id}")
    print(f"   State: {color}{state.upper()}{RESET}")
    print()
    
    return result


def cmd_list(args):
    """List all garage doors."""
    doors = find_garage_doors()
    
    if not doors:
        print(f"{YELLOW}No garage door entities found in Home Assistant.{RESET}")
        return
    
    if args.json:
        output = [format_status(d, include_json=True) for d in doors]
        print(json.dumps(output, indent=2))
    else:
        print(f"{BOLD}Garage Doors ({len(doors)} found):{RESET}\n")
        for door in doors:
            format_status(door)


def cmd_status(args):
    """Show status of garage doors."""
    if args.entity:
        # Specific entity
        door = get_garage_door(args.entity)
        if not door:
            print(f"{RED}Garage door '{args.entity}' not found{RESET}")
            sys.exit(1)
        if args.json:
            print(json.dumps(format_status(door, include_json=True), indent=2))
        else:
            format_status(door)
    else:
        # All doors
        doors = find_garage_doors()
        if not doors:
            print(f"{YELLOW}No garage door entities found.{RESET}")
            return
        
        if args.json:
            output = [format_status(d, include_json=True) for d in doors]
            print(json.dumps(output, indent=2))
        else:
            print(f"{BOLD}Garage Door Status:{RESET}\n")
            for door in doors:
                format_status(door)


def cmd_control(args):
    """Control garage door (open, close, toggle)."""
    # Determine entity
    entity_id = args.entity
    
    if not entity_id:
        # No entity specified, show list and prompt
        doors = find_garage_doors()
        if not doors:
            print(f"{YELLOW}No garage doors found.{RESET}")
            sys.exit(1)
        
        if len(doors) == 1:
            entity_id = doors[0]['entity_id']
        else:
            print(f"{BOLD}Multiple garage doors found. Please specify:{RESET}\n")
            for i, door in enumerate(doors, 1):
                print(f"  {i}. {door.get('attributes', {}).get('friendly_name', door['entity_id'])} ({door['entity_id']})")
            print()
            # Try to use first one as default
            entity_id = doors[0]['entity_id']
            print(f"{CYAN}Using: {entity_id}{RESET}\n")
    
    # Validate entity exists
    door = get_garage_door(entity_id)
    if not door:
        print(f"{RED}Garage door '{entity_id}' not found{RESET}")
        sys.exit(1)
    
    # Show current state
    current_state = door.get('state', 'unknown')
    action = args.command
    
    if args.json:
        result = control_garage_door(entity_id, action)
        print(json.dumps({
            'entity_id': entity_id,
            'action': action,
            'success': result
        }, indent=2))
        return
    
    # Perform action
    action_verbs = {
        'open': 'Opening',
        'close': 'Closing', 
        'toggle': 'Toggling'
    }
    
    print(f"{CYAN}{action_verbs[action]} {door.get('attributes', {}).get('friendly_name', entity_id)}...{RESET}")
    
    if control_garage_door(entity_id, action):
        print(f"{GREEN}✓ Done!{RESET}")
    else:
        print(f"{RED}✗ Failed{RESET}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Control garage doors via Home Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                  List all garage doors
  %(prog)s status                Show status of all garage doors
  %(prog)s status garage_door    Show status of specific door
  %(prog)s open                  Open garage door (prompts if multiple)
  %(prog)s open garage_door      Open specific door
  %(prog)s close                 Close garage door
  %(prog)s toggle                Toggle garage door state

Environment:
  HA_TOKEN    Home Assistant Long-Lived Access Token
  HA_URL      Home Assistant URL (default: http://192.168.1.135:8123)
        """
    )
    
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    parser_list = subparsers.add_parser('list', help='List all garage doors')
    
    # status command
    parser_status = subparsers.add_parser('status', help='Show garage door status')
    parser_status.add_argument('entity', nargs='?', help='Specific entity ID')
    
    # open command
    parser_open = subparsers.add_parser('open', help='Open garage door')
    parser_open.add_argument('entity', nargs='?', help='Specific entity ID')
    
    # close command
    parser_close = subparsers.add_parser('close', help='Close garage door')
    parser_close.add_argument('entity', nargs='?', help='Specific entity ID')
    
    # toggle command
    parser_toggle = subparsers.add_parser('toggle', help='Toggle garage door')
    parser_toggle.add_argument('entity', nargs='?', help='Specific entity ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command in ('open', 'close', 'toggle'):
        cmd_control(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
