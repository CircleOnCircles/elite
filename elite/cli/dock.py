#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys

from ruamel.yaml import YAML

from ..libraries import dock


# Configure YAML parsing to be safe by default
yaml = YAML(typ='safe')
yaml.default_flow_style = False
yaml.explicit_start = True

# Colours
BOLD = '\033[1m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    # Create the parser for the build sub-command
    build_parser = subparsers.add_parser(
        'build', help='build the dock plist using the config provided'
    )
    build_parser.add_argument('config_path', help='the file path of the config to use')

    # Create the parser for the extract sub-command
    extract_parser = subparsers.add_parser(
        'extract', help='extract the dock plist into a config file'
    )
    extract_parser.add_argument(
        '-f', '--format', choices=['json', 'yaml'], default='yaml',
        help='the format to extract your config to'
    )
    extract_parser.add_argument('config_path', help='the file path to extract the config to')

    # Create the parser for the compare sub-command
    compare_parser = subparsers.add_parser(
        'compare', help='compare the dock plist with the config'
    )
    compare_parser.add_argument('config_path', help='the file path of the config to compare')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.error('please specify an action to perform')

    print()
    print(f'{BOLD}Dock Builder{ENDC}')
    print()

    # Determine the location of the Dock plist file
    dock_plist_path = dock.get_dock_plist_path()

    print(f'{BLUE}Using Dock plist {dock_plist_path}{ENDC}')

    # Build
    if args.command == 'build':
        with open(args.config_path) as fp:
            config = yaml.load(fp)

        print(f'{BLUE}Rebuilding the Dock plist{ENDC}')
        dock.build(
            config.get('app_layout', []), config.get('other_layout', []), dock_plist_path
        )

        # Restart the Dock so that the new plist file can be utilised
        print(f'{BLUE}Restarting the Dock to apply the new plist{ENDC}')
        subprocess.call(['/usr/bin/killall', 'Dock'])

        print(
            f'{GREEN}Successfully build the Dock layout defined in {args.config_path}{ENDC}'
        )

    # Extract
    elif args.command == 'extract':
        app_layout, other_layout = dock.extract(dock_plist_path)

        layout = {
            'app_layout': app_layout,
            'other_layout': other_layout
        }

        with open(args.config_path, 'w') as fp:
            if args.format == 'yaml':
                yaml.dump(layout, fp)
            else:
                json.dump(layout, fp, indent=2)

        print(f'{GREEN}Successfully wrote Dock config to {args.config_path}{ENDC}')

    # Compare
    elif args.command == 'compare':
        with open(args.config_path) as fp:
            config = yaml.load(fp)

        app_layout_existing, other_layout_existing = dock.extract(dock_plist_path)

        layout_existing = {
            'app_layout': app_layout_existing,
            'other_layout': other_layout_existing
        }

        app_layout_normalised, other_layout_normalised = dock.normalise(
            config.get('app_layout', []), config.get('other_layout', [])
        )
        layout_config = {
            'app_layout': app_layout_normalised,
            'other_layout': other_layout_normalised
        }

        if layout_config == layout_existing:
            print(f'{GREEN}The configuration provided is identical to the current layout{ENDC}')
        else:
            print(f'{RED}The configuration provided is different to the current layout{ENDC}')
            print()
            sys.exit(1)

    print()


if __name__ == '__main__':
    main()
