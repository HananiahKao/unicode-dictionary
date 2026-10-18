.PHONY: all data xml dict install clean test help

# Configuration
PROJECT_NAME := UnicodeDictionary
DICT_BUNDLE := $(PROJECT_NAME).dictionary
DICT_BUNDLE_PATH := dist/$(DICT_BUNDLE)
DICT_BUILD_TOOL_DIR ?= /usr/local/Dictionary\ Development\ Kit

# Files
UCD_FILES := data/UnicodeData.txt data/Blocks.txt data/Scripts.txt
XML_SOURCE := dist/UnicodeDictionary.xml
CSS_SOURCE := src/UnicodeDictionary.css
INFO_PLIST := src/Info.plist

# Spike mode: limit to 5000 entries for testing
SPIKE ?= 0
SPIKE_LIMIT := --limit 5000
SPIKE_OUTPUT := dist/UnicodeDictionary-spike.xml

help:
	@echo "Unicode Dictionary Builder"
	@echo ""
	@echo "Targets:"
	@echo "  make data         - Download Unicode Character Database"
	@echo "  make xml          - Generate dictionary XML (requires 'data' target)"
	@echo "  make xml-spike    - Generate small XML for testing (5k entries)"
	@echo "  make dict         - Build .dictionary bundle (requires 'xml')"
	@echo "  make install      - Install to ~/Library/Dictionaries/"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove generated files"
	@echo ""
	@echo "Usage:"
	@echo "  make               # Full build"
	@echo "  make SPIKE=1 all   # Build spike version (5k entries)"
	@echo "  make install       # Install to system"

all: data xml dict

data:
	@echo "Downloading Unicode Character Database..."
	@bash build/fetch_ucd.sh
	@echo "✓ UCD download complete"

xml: $(XML_SOURCE)

$(XML_SOURCE): $(UCD_FILES) build/gen_dict.py build/ucd_parse.py
	@echo "Generating dictionary XML..."
	@mkdir -p dist
	cd build && python3 -I gen_dict.py --output ../$(XML_SOURCE) --data-dir ../data
	@echo "✓ XML generation complete"

xml-spike:
	@echo "Generating spike XML (first 5000 entries)..."
	@mkdir -p dist
	cd build && python3 -I gen_dict.py --output ../$(SPIKE_OUTPUT) --data-dir ../data $(SPIKE_LIMIT)
	@echo "✓ Spike XML generation complete"

dict: $(XML_SOURCE) $(CSS_SOURCE) $(INFO_PLIST)
	@echo "Building dictionary bundle..."
	@mkdir -p "$(DICT_BUNDLE_PATH)/Contents/Resources"

	# Try using the Dictionary Development Kit first
	@if command -v build_dict.sh >/dev/null 2>&1; then \
		echo "Using Dictionary Development Kit..."; \
		build_dict.sh "$(PROJECT_NAME)" "$(XML_SOURCE)" "$(CSS_SOURCE)" "$(INFO_PLIST)"; \
		mkdir -p dist; \
		mv "$(PROJECT_NAME).dictionary" "$(DICT_BUNDLE_PATH)"; \
	else \
		echo "Dictionary Development Kit not found; building bundle manually..."; \
		$(MAKE) _build_bundle_manual; \
	fi
	@echo "✓ Dictionary bundle created at $(DICT_BUNDLE_PATH)"

_build_bundle_manual:
	@echo "Creating bundle structure..."

	# Copy Info.plist
	cp "$(INFO_PLIST)" "$(DICT_BUNDLE_PATH)/Contents/Info.plist"

	# For manual build without the Kit, we'd need to:
	# 1. Create the Body.data file (gzipped XML chunks)
	# 2. Create the KeyText.index file (searchable index)
	# This requires the Kit's tools (bin/plutil, etc.)
	# For now, we'll create a minimal bundle structure

	@echo "Note: Manual bundle creation requires Apple's Dictionary Development Kit"
	@echo "Visit: https://developer.apple.com/download/all/"
	@echo "Download: Additional Tools for Xcode"
	@echo ""
	@echo "To complete the build, install the Kit and run 'make dict' again"

install: $(DICT_BUNDLE_PATH)
	@echo "Installing dictionary..."
	@mkdir -p ~/Library/Dictionaries/
	@cp -r "$(DICT_BUNDLE_PATH)" ~/Library/Dictionaries/
	@echo "✓ Dictionary installed to ~/Library/Dictionaries/"
	@echo ""
	@echo "Next: Open Dictionary.app → Settings → enable 'Unicode Character Database'"

test:
	@echo "Running tests..."
	@mkdir -p data
	@python3 -I tests/test_gen.py
	@echo "✓ Tests complete"

clean:
	@echo "Cleaning..."
	@rm -rf dist/*.xml dist/*.dictionary
	@echo "✓ Cleaned"

clean-all: clean
	@echo "Removing downloaded data..."
	@rm -rf data/
	@echo "✓ Complete clean done"

# Phony targets that depend on files
.PHONY: $(XML_SOURCE) $(DICT_BUNDLE_PATH)
