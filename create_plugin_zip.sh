#!/usr/bin/env bash
set -euo pipefail

# Set the output zip file name
ZIPFILE="${HOME}/Downloads/splashtool_result_loader.zip"

# Resolve script directory to run relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Remove existing zip file if it exists
if [[ -f "$ZIPFILE" ]]; then
  rm -f "$ZIPFILE"
fi

# Check if standard 'zip' exists in PATH
if ! command -v zip >/dev/null 2>&1; then
  echo "Error: 'zip' command not found."
  echo "Install it with: sudo apt-get install -y zip  # Debian/Ubuntu"
  echo "or: sudo dnf install -y zip                    # Fedora/RHEL"
  echo "or: sudo pacman -S zip                         # Arch"
  exit 1
fi

# Ensure plugin directory exists
if [[ ! -d "splashtool_result_loader" ]]; then
  echo "Error: Directory 'splashtool_result_loader' not found next to this script."
  exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$ZIPFILE")"

# Create the zip file including the parent directory
zip -r "$ZIPFILE" "splashtool_result_loader" >/dev/null

echo "Plugin zip file created successfully: $ZIPFILE"