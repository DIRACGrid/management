#!/bin/bash

# Enable Bash strict mode
set -euo pipefail
IFS=$'\n\t'

# Determine the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Directory containing the SVG files relative to the script's location
SVG_DIR="$SCRIPT_DIR/svg"
# Output directories for PNG and PDF files
PNG_DIR="$SCRIPT_DIR/png"
PDF_DIR="$SCRIPT_DIR/pdf"

# Create output directories if they do not exist
mkdir -p "$PNG_DIR"
mkdir -p "$PDF_DIR"

# Check if there are any SVG files to process
shopt -s nullglob
svg_files=("$SVG_DIR"/*.svg)
shopt -u nullglob

if [ ${#svg_files[@]} -eq 0 ]; then
  echo "No SVG files found in $SVG_DIR"
  exit 1
fi

# Loop through each SVG file in the directory
for svg_file in "${svg_files[@]}"; do
  # Get the base name of the file (without extension)
  base_name=$(basename "$svg_file" .svg)

  # Define output file paths for default transparent background version
  png_file="$PNG_DIR/${base_name}-transparent-background.png"
  pdf_file="$PDF_DIR/${base_name}.pdf"

  # Convert SVG to PNG without background
  if inkscape "$svg_file" --export-type=png --export-filename="$png_file" --export-background-opacity=0; then
    echo "Converted $svg_file to $png_file with transparent background"
  else
    echo "Failed to convert $svg_file to PNG with transparent background" >&2
    exit 1
  fi

  # Convert SVG to PDF without background
  if inkscape "$svg_file" --export-type=pdf --export-filename="$pdf_file"; then
    echo "Converted $svg_file to $pdf_file"
  else
    echo "Failed to convert $svg_file to PDF" >&2
    exit 1
  fi

  # Define output file paths for version with white background
  png_file_white="$PNG_DIR/${base_name}-white-background.png"
  pdf_file_white="$PDF_DIR/${base_name}-white-background.pdf"

  # Convert SVG to PNG with white background
  if inkscape "$svg_file" --export-type=png --export-filename="$png_file_white" --export-background="#FFFFFF" --export-background-opacity=1; then
    echo "Converted $svg_file to $png_file_white with white background"
  else
    echo "Failed to convert $svg_file to PNG with white background" >&2
    exit 1
  fi

  # Convert SVG to PDF with white background
  if inkscape "$svg_file" --export-type=pdf --export-filename="$pdf_file_white" --export-background="#FFFFFF" --export-background-opacity=1; then
    echo "Converted $svg_file to $pdf_file_white with white background"
  else
    echo "Failed to convert $svg_file to PDF with white background" >&2
    exit 1
  fi

  # Define output file paths for high-resolution version with transparent background (300 DPI)
  png_file_high_res="$PNG_DIR/${base_name}-high-res-transparent-background.png"

  # Convert SVG to high-resolution PNG without background
  if inkscape "$svg_file" --export-type=png --export-filename="$png_file_high_res" --export-dpi=300 --export-background-opacity=0; then
    echo "Converted $svg_file to $png_file_high_res with transparent background"
  else
    echo "Failed to convert $svg_file to high-resolution PNG with transparent background" >&2
    exit 1
  fi

  # Define output file paths for high-resolution version with white background (300 DPI)
  png_file_high_res_white="$PNG_DIR/${base_name}-high-res-white-background.png"

  # Convert SVG to high-resolution PNG with white background
  if inkscape "$svg_file" --export-type=png --export-filename="$png_file_high_res_white" --export-dpi=300 --export-background="#FFFFFF" --export-background-opacity=1; then
    echo "Converted $svg_file to $png_file_high_res_white with white background"
  else
    echo "Failed to convert $svg_file to high-resolution PNG with white background" >&2
    exit 1
  fi

done

echo "Conversion process completed."

