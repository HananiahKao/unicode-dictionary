#!/bin/bash
# Fetch Unicode Character Database files from Unicode.org
# Stores in data/ directory (treated as untrusted; clean before running generators)

set -e

UCD_VERSION="18.0.0"
UCD_URL="https://www.unicode.org/Public/${UCD_VERSION}/ucd"
DATA_DIR="data"

mkdir -p "$DATA_DIR"

# Files to download
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

# DerivedName.txt: Unicode's own complete, pre-computed Name property for
# every code point (individual names and algorithmic-range patterns alike),
# published specifically "so that implementations do not have to properly
# code that derivation" (its own header). Lives under ucd/extracted/, not at
# the top level of ucd/ with the other files above.
derived_name_file="${DATA_DIR}/DerivedName.txt"
if [ -f "$derived_name_file" ]; then
    echo "✓ DerivedName.txt (already exists)"
else
    echo "Downloading DerivedName.txt..."
    curl -# -f -o "$derived_name_file" "${UCD_URL}/extracted/DerivedName.txt" || { echo "✗ Failed to download DerivedName.txt"; exit 1; }
fi

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
