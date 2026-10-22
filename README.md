# Unicode Character Database → Apple Look Up Dictionary

A custom macOS Dictionary that brings the complete Unicode Character Database to your fingertips. Select any character and use Look Up (Ctrl+Cmd+D) to instantly see its official name, code point, properties, and more.

## Features

- **Complete Unicode 18.0 database** – 172,873 assigned characters
- **Instant lookup** – Use standard macOS Look Up/dictionary features
- **Rich properties** – Character name, code point, category, script, block, combining class, bidi properties, decomposition, case mappings, numeric values, East Asian width, line break properties, and boolean properties (Alphabetic, Emoji, Math, White_Space, ID_Start, etc.)
- **Smart indexing** – Look up by character, `U+XXXX` format, or full Unicode name
- **Compact pop-over** – Most important data visible by default; additional properties collapsible
- **Light/dark mode** – Automatic theme support

## Quick Start

### Prerequisites

- macOS 10.11+ (Dictionary Services)
- Xcode Command Line Tools: `xcode-select --install`
- Python 3.6+

### Build Instructions

```bash
cd unicode-dictionary

# Step 1: Download Unicode Character Database
make data

# Step 2: Generate dictionary XML
make xml

# Step 3: Build dictionary bundle
make dict

# Step 4: Install to system
make install
```

### Enable in Dictionary.app

1. Open **Dictionary.app** (Applications → Utilities)
2. Go to **Settings** (or **Preferences** on older macOS)
3. Find **"Unicode Character Database"** in the list
4. Check the box to enable it
5. Close Settings

Done! You can now Look Up any character.

## Usage

Select any character in any app, then:

- **macOS keyboard:** Ctrl+Cmd+D
- **Trackpad:** Three-finger tap  
- **Mouse:** Right-click → Look Up

Try these examples:
- `A` → Latin Capital Letter A, properties
- `é` → Latin Small Letter E with Acute
- `€` → Euro Sign (with decomposition, category, etc.)
- `😀` → Grinning Face (emoji properties)
- `한` → Hangul Syllable Han
- `漢` → CJK Ideograph
- `U+1F600` → Search by code point (Grinning Face)

## Advanced Usage

### Build a Spike (Test Edition)

To test with just the first 5,000 entries:

```bash
make xml-spike
make dict
make install
```

### Development

#### Project Structure

```
unicode-dictionary/
├── build/
│   ├── fetch_ucd.sh           # Download Unicode files
│   ├── ucd_parse.py           # Parse UCD files into Python objects
│   └── gen_dict.py            # Generate Apple Dictionary XML
├── src/
│   ├── Info.plist             # Dictionary bundle metadata
│   └── UnicodeDictionary.css  # Styling for pop-over
├── data/                      # Unicode files (after `make data`)
├── dist/                      # Build output
├── tests/
│   └── test_gen.py            # Validation tests
├── Makefile
└── README.md
```

#### Run Tests

```bash
python3 -I tests/test_gen.py
```

Tests validate:
- UCD parsing (character counts, names, categories)
- XML generation (well-formed, unique IDs, proper indexes)
- XML IDs conform to XML spec

#### Regenerate from Source

```bash
make clean
make all
make install
```

#### Check Installation

```bash
ls -la ~/Library/Dictionaries/UnicodeDictionary.dictionary/
```

## Uninstall

```bash
rm -rf ~/Library/Dictionaries/UnicodeDictionary.dictionary/
```

## Data Source

All character data comes from the **Unicode Character Database (UCD) 18.0**:

- **UnicodeData.txt** – Character names, categories, case mappings, decompositions
- **DerivedName.txt** – Algorithmic names for Hangul, CJK, Tangut, etc.
- **NameAliases.txt** – Alternate names (e.g., "NEWLINE" for U+000A)
- **Blocks.txt** – Unicode block assignments
- **Scripts.txt** – Writing system assignments
- **ScriptExtensions.txt** – Characters used in multiple scripts
- **DerivedAge.txt** – Unicode version when character was introduced
- **PropList.txt & DerivedCoreProperties.txt** – Boolean properties
- **EastAsianWidth.txt** – Display width properties
- **LineBreak.txt** – Line breaking properties
- **BidiMirroring.txt** – Bidirectional text mirroring pairs
- **Unihan.zip** – CJK Ideograph definitions (optional)

Download: https://www.unicode.org/Public/18.0.0/ucd/

**License:** Unicode License Agreement – https://www.unicode.org/license.html

## Dictionary Development Kit

The build process attempts to use Apple's **Dictionary Development Kit** to create a proper `.dictionary` bundle. If the Kit is not found, the script falls back to manual bundle assembly.

### Install Dictionary Development Kit

1. Visit https://developer.apple.com/download/all/
2. Search for "Additional Tools for Xcode"
3. Download the latest version for your macOS
4. Open the `.dmg` and install
5. The Kit includes `build_dict.sh` and related tools

**Note:** The Kit is only necessary to build the final `.dictionary` bundle. The generator itself (XML creation) requires only Python 3.

## Known Limitations

### v1.0

- **Multi-character clusters** (emoji ZWJ sequences, flag pairs, skin-tone modifiers, base + combining marks): selecting the composed glyph and invoking Look Up reports "no entries found" — there is no fallback to the base/first code point. Each component code point has its own entry, searchable individually by its name or U+code.
- **Unihan data** (CJK extended properties): Optional download. Basic properties included.
- **Font rendering**: If no installed font covers a character's actual glyph, the `.glyph` display falls back to Apple's "LastResort" system font, which draws a labeled block/range placeholder instead of a blank box. The code point and name are always shown regardless.

### Single-Character Indexing

The dictionary is indexed for:
- The literal character (e.g., `A`)
- Code point formats: `U+0041`, `0041`, `u+0041`
- Full Unicode name: `LATIN CAPITAL LETTER A`
- Name variants (lowercase): `latin capital letter a`
- Aliases (if any)

For emoji, Han, and other multi-code-point sequences, macOS Look Up sends the first character; the dictionary will display its entry and cross-reference related characters.

## Troubleshooting

### Dictionary not showing in settings

Ensure the `.dictionary` bundle is installed:

```bash
ls -la ~/Library/Dictionaries/UnicodeDictionary.dictionary/
```

If missing, run `make install`. Then restart Dictionary.app.

### Look Up not working

1. Check that the dictionary is enabled in Dictionary settings
2. Some apps (e.g., terminal emulators) may not support Look Up — test in a standard app like Mail or Notes
3. Restart the app or macOS

### XML generation is slow

The full dictionary with ~140k entries takes a few minutes. Use `make xml-spike` for a test build with 5k entries.

### "Dictionary Development Kit not found"

The script will attempt manual bundle assembly, but will require the Kit for final compilation. Download and install it as described above.

## Contributing

This is a personal/educational project. The data is generated entirely from the official Unicode Character Database; no custom entries are included.

To report issues or suggest improvements:
- File an issue with the UCD data source version
- Suggest additional properties to display

## License

- **Dictionary builder code:** MIT (or equivalent)
- **Unicode data:** Unicode License Agreement (see UCD at unicode.org)

This dictionary is not endorsed by Apple Inc. or The Unicode Consortium.

---

**Version:** 1.0 (Unicode 18.0)  
**Last updated:** 2026-10-17
