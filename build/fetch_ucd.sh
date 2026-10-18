#!/bin/bash
# Fetch Unicode Character Database files from Unicode.org
# Stores in data/ directory (treated as untrusted; clean before running generators)

set -e

UCD_VERSION="17.0.0"
UCD_URL="https://www.unicode.org/Public/${UCD_VERSION}/ucd"
DATA_DIR="data"

mkdir -p "$DATA_DIR"

# Files to download
# Note: DerivedName.txt doesn't exist as a separate file; algorithmic names are in UnicodeData.txt range data
FILES=(
    "UnicodeData.txt"
    "NameAliases.txt"
    "Blocks.txt"
    "Scripts.txt"
    "ScriptExtensions.txt"
    "DerivedAge.txt"
    "PropList.txt"
    "DerivedCoreProperties.txt"
    "EastAsianWidth.txt"
    "LineBreak.txt"
    "DerivedNormalizationProps.txt"
    "BidiMirroring.txt"
)

echo "Fetching Unicode Character Database v${UCD_VERSION}..."

for file in "${FILES[@]}"; do
    url="${UCD_URL}/${file}"
    dest="${DATA_DIR}/${file}"

    if [ -f "$dest" ]; then
        echo "✓ ${file} (already exists)"
    else
        echo "Downloading ${file}..."
        curl -# -f -o "$dest" "$url" || { echo "✗ Failed to download $file"; exit 1; }
    fi
done

# Download emoji data (in subdirectory)
mkdir -p "$DATA_DIR/emoji"
emoji_file="${DATA_DIR}/emoji/emoji-data.txt"
if [ ! -f "$emoji_file" ]; then
    echo "Downloading emoji-data.txt..."
    curl -# -f -o "$emoji_file" "${UCD_URL}/emoji/emoji-data.txt" || { echo "⚠ Failed to download emoji-data.txt (optional)"; }
fi

# Download Unihan (large file, optional)
unihan_dir="${DATA_DIR}/Unihan"
mkdir -p "$unihan_dir"
unihan_file="${unihan_dir}/Unihan.zip"
if [ ! -f "$unihan_file" ]; then
    echo "Downloading Unihan.zip (for CJK properties)..."
    curl -# -f -o "$unihan_file" "${UCD_URL}/Unihan.zip" || { echo "⚠ Failed to download Unihan.zip (optional)"; }
    if [ -f "$unihan_file" ]; then
        unzip -q "$unihan_file" -d "$unihan_dir" && rm "$unihan_file"
    fi
fi

echo ""
echo "✓ UCD download complete"
ls -lh "$DATA_DIR" | tail -n +2
