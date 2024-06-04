#!/bin/bash

# Enable Bash strict mode
set -euo pipefail
IFS=$'\n\t'

# Determine the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# SVG files
SVG_MINIMAL="$SCRIPT_DIR/svg/diracx-logo-square-minimal.svg"
SVG_STANDARD="$SCRIPT_DIR/svg/diracx-logo-square.svg"

# Output directories for favicons
FAVICON_DIR_STANDARD="$SCRIPT_DIR/favicons/standard"
FAVICON_DIR_MINIMAL="$SCRIPT_DIR/favicons/minimal"

# Create output directories if they do not exist
mkdir -p "$FAVICON_DIR_STANDARD"
mkdir -p "$FAVICON_DIR_MINIMAL"

# Array of common favicon sizes
sizes=(16 32 48 64 96 128 256 512)

# Function to generate favicons
generate_favicons() {
  local svg_file="$1"
  local output_dir="$2"

  for size in "${sizes[@]}"; do
    output_file="$output_dir/favicon-${size}x${size}.png"
    if inkscape "$svg_file" --export-type=png --export-filename="$output_file" --export-width="$size" --export-height="$size"; then
      echo "Generated $output_file"
    else
      echo "Failed to generate $output_file" >&2
      exit 1
    fi
  done

  # Generate a single multi-resolution ICO file
  output_ico="$output_dir/favicon.ico"
  if convert "${output_dir}/favicon-16x16.png" "${output_dir}/favicon-32x32.png" "${output_dir}/favicon-48x48.png" "${output_dir}/favicon-64x64.png" "${output_dir}/favicon-128x128.png" "${output_dir}/favicon-256x256.png" "${output_ico}"; then
    echo "Generated $output_ico"
  else
    echo "Failed to generate $output_ico" >&2
    exit 1
  fi
}

# Generate favicons for standard logo
generate_favicons "$SVG_STANDARD" "$FAVICON_DIR_STANDARD"

# Generate favicons for minimal logo
generate_favicons "$SVG_MINIMAL" "$FAVICON_DIR_MINIMAL"

echo "Favicon generation process completed."

