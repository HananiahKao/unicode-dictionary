# Developer Notes for Unicode Dictionary Project

## Quick Reference

**Project:** Unicode Character Database → macOS Look Up Dictionary  
**Status:** Implementation complete, awaiting Dictionary Development Kit  
**Key Files:**  
- `build/gen_dict.py` – Main XML generator (47.1 MB output)
- `build/ucd_parse.py` – UCD file parser
- `dist/UnicodeDictionary.xml` – Generated dictionary XML
- `src/Info.plist` – Dictionary metadata
- `Makefile` – Build automation

## Architecture Overview

The project converts text-based Unicode data into an Apple Dictionary:

1. **Data fetch** (`make data`) – curl downloads UCD from Unicode.org
2. **Parse** (`ucd_parse.py`) – Read 12+ text files, build character property objects
3. **Generate** (`gen_dict.py`) – Create Apple Dictionary XML with 40,575 entries
4. **Bundle** (`bundle_dict.py`) – Create `.dictionary` structure (fallback without Kit)
5. **Compile** (Kit's `build_dict.sh`) – Generate binary Body.data and KeyText.index

## Implementation Checklist

- [x] Download UCD files from Unicode.org
- [x] Parse UnicodeData.txt (40,575 assigned characters)
- [x] Parse Blocks.txt, Scripts.txt, DerivedAge.txt, etc. (12 files)
- [x] Generate Apple Dictionary XML with proper namespaces
- [x] Create d:entry elements with d:index for lookup
- [x] Format HTML content with property tables
- [x] Handle XML-unsafe characters (controls, surrogates, etc.)
- [x] Implement light/dark mode CSS
- [x] Create Info.plist with correct keys
- [x] Build bundle structure (fallback without Kit)
- [x] Write comprehensive documentation
- [x] Create test suite for validation
- [x] Set up Makefile for automation
- [x] Commit to git with proper history

## Known Limitations & TODOs

### v1.0 Limitations
1. **Dictionary Development Kit required** – XML ready but needs Kit for compilation
2. **Unihan properties partial** – Downloaded but not yet integrated (optional)
3. **Emoji ZWJ sequences** – Not fully supported; Look Up uses first code point
4. **No per-character pronunciation** – Would require external data source
5. **Hangul syllables (~11,172) and large CJK ideograph ranges are missing entries** –
   `UnicodeData.txt` uses `<..., First>`/`<..., Last>` range markers for these blocks
   instead of per-codepoint lines, and `ucd_parse.py` does not yet implement Unicode's
   algorithmic naming (e.g. the Hangul Syllable Name algorithm) to expand them. Also
   observed: `漢` (U+6F22) resolves via `DCSCopyTextDefinition` to the wrong,
   compatibility-duplicate codepoint (U+FA47) — a glyph-collision bug to fix alongside this.

### Known Apple/macOS Dictionary.app bug (confirmed, not a bug in this project)
**Symptom:** with only ONE dictionary enabled in Dictionary.app → Settings → Dictionaries,
clicking a search result in the main browsing window shows a completely blank content
pane (sidebar list populates fine; no error, no WebKit navigation/log activity at all —
confirmed via `log stream` with zero load/navigation events on click). Enabling a SECOND
dictionary (any dictionary, built-in or custom) alongside it makes the exact same content
render correctly immediately.

**Root cause: confirmed external to this project.** Reproduced identically, byte-for-byte,
using Apple's own completely unmodified sample dictionary built straight from their
Dictionary Development Kit (`project_templates/MyDictionary.xml` + `MyInfo.plist`, zero
changes) — it also shows blank with only itself enabled, and also starts working the
moment a second dictionary is enabled. This is a macOS Dictionary.app bug, not something
in `gen_dict.py`, `Info.plist`, or `UnicodeDictionary.css`.

A related, separately-confirmed Apple bug (developer.apple.com/forums/thread/842956):
when an entry's content expands/reflows after initial load, Dictionary.app's native
scroll view doesn't update to the new content size, making long/expanded entries look
truncated or "collapsed" — also an OS-side bug with no app-side CSS/HTML fix.

**Workaround (permanent, required for normal use):** always keep at least one other
dictionary enabled alongside "Unicode Character Database" in Settings → Dictionaries.
Do not spend further debugging time chasing "blank main window" as if it were a bug in
this project's XML/CSS/Info.plist — it was investigated exhaustively (control characters,
index count limits, bundle ID caching, WebKit process caches, CSS background opacity) and
none of those were the cause; the single-vs-multiple active dictionary count is.

**A related, narrower variant of the same bug** (confirmed 2026-10-20): when 2+ active
dictionaries each have a matching entry for the exact same search query, the content-
aggregation views (main window, Ctrl+Cmd+D Look Up popover, AND the search-box's live
autocomplete dropdown) can render one dictionary's section with only an empty header —
content omitted, not just hidden. Does not require d:priority or any markup of ours;
reproduces with Apple's own unmodified Kit sample too. Research turned up a 2010 Mac
Forums report of the identical symptom between two of Apple's *own* built-in dictionaries,
on macOS 10.6 — this has been unfixed and apparently unacknowledged by Apple for 14+
years, with no newer official build toolchain, no Info.plist/version key workaround
(`IDXDictionaryVersion` is hardcoded to 1 by the public Kit regardless of source content —
confirmed identical even on Apple's own unmodified sample bundle), and no known mitigation
beyond disabling the colliding dictionary. Real shipping commercial dictionaries (e.g.
Apple's bundled "Traditional Chinese - English") exhibit the same behavior, so this is a
platform-wide limitation, not a blocker specific to this project. Do not re-investigate;
document as a known limitation.

### Potential Improvements
- [ ] **Unihan integration** – Add kDefinition, kTotalStrokes, etc. for CJK
- [ ] **Emoji better handling** – Handle ZWJ sequences, skin tone modifiers
- [ ] **Cross-references** – d:anchor links to related characters (decomposition targets, case pairs)
- [ ] **Pronunciation** – Add CLDR data for phonetic lookups (if available)
- [ ] **Codepoint ranges** – Dedicated entries for unassigned/private-use ranges
- [ ] **Performance tuning** – Consider breaking into multiple smaller dictionaries
- [ ] **Better styling** – Collapsible sections, tabs, better typography
- [ ] **Script-specific pages** – Introduction to each script (Latin, Greek, Arabic, Han, etc.)
- [ ] **Variant charts** – Display character variants, regional differences
- [ ] **Compatibility notes** – Show compatibility decompositions vs. canonical

## How to Work on This Project

### Setup
```bash
cd /Users/hananiah/Developer/unicode-dictionary
# Already initialized with git, make available
```

### Common Tasks

**Generate dictionary:**
```bash
make data          # Download UCD (done once)
make xml           # Generate full XML
make xml-spike     # Quick test with 5k entries
```

**Build and install:**
```bash
make dict          # Create bundle (fallback if no Kit)
make install       # Copy to ~/Library/Dictionaries/
```

**Validate:**
```bash
make test          # Run Python tests
xmllint --noout dist/UnicodeDictionary.xml  # Validate XML
```

**Quick iteration:**
```bash
make clean
make xml-spike
make test
```

### Testing Workflow

1. **Unit tests** – `python3 -I tests/test_gen.py`
   - Parser validates character counts
   - Generator validates XML structure
   - XML ID generation validates spec compliance

2. **Integration test** – Build spike, validate XML
   ```bash
   make xml-spike
   xmllint --noout dist/UnicodeDictionary-spike.xml
   grep -c "d:entry" dist/UnicodeDictionary-spike.xml
   ```

3. **Manual test** (requires Kit)
   - After Kit installed: `make dict && make install`
   - Open Dictionary.app, enable Unicode dictionary
   - Select character and Look Up (Ctrl+Cmd+D)

## Code Organization

### `ucd_parse.py` – Character Property Parser
- **Class `UCDParser`** – Main parser, manages file reading and data merging
- **Class `CharacterData`** – Dataclass holding all properties for one character
- **Methods:**
  - `parse_all()` – Main entry point, orchestrates all parsing
  - `_parse_unicode_data()` – Main character data (names, categories, mappings)
  - `_parse_blocks()` – Block assignments (Latin, Han, etc.)
  - `_parse_scripts()` – Script assignments (Latin, Arabic, etc.)
  - `_parse_*_properties()` – Boolean properties (Alphabetic, Emoji, Math, etc.)
  - `_assign_blocks()` – Map block names to characters

**Key Properties in CharacterData:**
- `codepoint: int` – U+XXXX as integer
- `name: str` – Official character name
- `category: str` – General category (Lu, Ll, Nd, etc.)
- `script: str` – Writing system (Latin, Han, etc.)
- `block: str` – Unicode block
- `decomposition: (str, [int])` – (type, list of codepoints)
- `props: Set[str]` – Boolean properties

### `gen_dict.py` – Dictionary XML Generator
- **Function `generate_dictionary()`** – Main entry point
- **Function `generate_entry_xml()`** – Create one `<d:entry>` element
- **Function `generate_entry_html()`** – Create HTML content for entry
- **Function `safe_xml_char()`** – Escape XML-unsafe characters
- **Function `make_xml_id()`** – Create valid XML ID from character name
- **Constants:**
  - `XML_UNSAFE_CHARS` – Set of code points that can't appear literally in XML

**Key XML Structure:**
```xml
<d:entry id="U_0041_..." d:title="LATIN CAPITAL LETTER A">
  <d:index d:value="A" d:title="..."/>
  <d:index d:value="U+0041" d:title="..."/>
  ...
  <div><!-- XHTML content --></div>
</d:entry>
```

### `bundle_dict.py` – Bundle Creator (Fallback)
- **Function `create_bundle()`** – Create `.dictionary` directory structure
- Creates:
  - `Contents/Info.plist` – Dictionary metadata
  - `Contents/Resources/Dictionary.css` – Styling
  - `Contents/Resources/Dictionary.xml.gz` – Compressed source XML
  - `Contents/Resources/README.txt` – Instructions for Kit

### `Makefile` – Build Automation
- **Targets:**
  - `data` – Fetch UCD files
  - `xml` – Generate full dictionary XML
  - `xml-spike` – Generate test version (5k entries)
  - `dict` – Build bundle (detect Kit, fallback if missing)
  - `install` – Copy to ~/Library/Dictionaries/
  - `test` – Run validation tests
  - `clean` – Remove generated files
  - `clean-all` – Remove data + generated files

## Performance Notes

- **Data parsing:** ~400-500ms for all 12 UCD files
- **Dictionary generation:** ~1.5 seconds for 40k+ entries (XML writing is I/O bound)
- **Total build:** ~2 seconds + download time
- **Bundle size:** 47.1 MB (XML source) → 2.2 MB (compressed)

### Potential Optimizations
1. **Parallel parsing** – Use ThreadPoolExecutor for independent files
2. **Incremental generation** – Cache parsed data, regenerate only changed entries
3. **Streaming XML write** – Use iterative XML generation instead of list concat
4. **Split dictionaries** – Separate Han (100k entries) into own dictionary

## Git Workflow

Current history:
1. Initial project structure with generator (commit 1)
2. Fix imports and generate spike (commit 2)
3. Generate complete XML (commit 3)
4. Add bundle creator and finalize build (commit 4)

For future work:
```bash
# Before making changes
git status
git log --oneline | head -5

# Work on a feature
git checkout -b feature/name
# ...make changes...
git add -A
git commit -m "Description

Detailed explanation

Co-Authored-By: [Your name] <email>"

# Merge back
git checkout main
git merge --no-ff feature/name
```

## Dictionary Development Kit Integration

When Kit is available (`build_dict.sh` in PATH):
1. Makefile detects it with `command -v`
2. Calls: `build_dict.sh PROJECT_NAME XML CSS INFO_PLIST`
3. Kit produces: `PROJECT_NAME.dictionary/Contents/Resources/Body.data`
4. Kit produces: `PROJECT_NAME.dictionary/Contents/Resources/KeyText.index`

The fallback (no Kit):
1. Python script creates directory structure
2. Copies XML source as reference (compressed)
3. Explains to user that Kit is needed for real use

**Next step when Kit available:**
1. Download from developer.apple.com
2. Install (usually `/usr/local/Dictionary\ Development\ Kit/`)
3. Run: `make dict` (will auto-detect and use it)

## Testing Strategy

### Unit Tests (`tests/test_gen.py`)
- `TestUCDParser` – Validates parsing (char counts, names, categories)
- `TestDictionaryGeneration` – Validates XML output (structure, IDs, indexes)
- `TestXMLIDGeneration` – Validates XML ID spec compliance

### Integration Tests
- Spike test: `make xml-spike && xmllint --noout`
- Full test: same with full dictionary
- Manual test: requires Kit installation and Dictionary.app

### Validation Commands
```bash
# Check parsing correctness
grep "^0041;" data/UnicodeData.txt  # Should show "LATIN CAPITAL LETTER A"
grep "U_0041" dist/UnicodeDictionary.xml  # Should find entry

# Check index coverage
grep '<d:index' dist/UnicodeDictionary.xml | wc -l  # Should be 40k+

# Check XML well-formedness
xmllint --noout dist/UnicodeDictionary.xml

# Check specific entry
grep -A 20 'id="U_0041' dist/UnicodeDictionary.xml
```

## Memory & Computational Complexity

### Parser
- **Time:** O(n) where n = total lines in all UCD files (~2M lines)
- **Space:** O(characters) = ~40k CharacterData objects in memory (~100MB estimated)

### Generator
- **Time:** O(characters × indexes) = O(40k × 5) = O(200k) HTML generations
- **Space:** O(characters) for generated entry strings before write
- **I/O:** 47.1 MB XML write to disk

### Potential bottlenecks
1. String concatenation in generation (mitigated by list/join)
2. File I/O for large XML (mitigated by buffering)
3. Memory for complete CharacterData objects (could stream if needed)

## Resources

- **Unicode Standard:** https://www.unicode.org/standard/
- **UCD Documentation:** https://www.unicode.org/reports/tr44/
- **Apple Dictionary Guide:** https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/DictionaryServicesProgGuide/
- **RELAX NG Schema:** http://www.apple.com/DTDs/DictionaryService-1.0.rng

## Future Maintainence

When Unicode Standard updates:
1. New version available on Unicode.org/Public/
2. Download new UCD files: `make clean-all && make data`
3. Update version in `src/Info.plist`: `<string>X.Y</string>`
4. Regenerate: `make xml && make dict`
5. Test: `make test`
6. Commit: `git add -A && git commit -m "Update to Unicode X.Y"`

Current version: Unicode 17.0 (October 2024)

---

**Last Updated:** 2026-10-18  
**Maintained By:** Unicode Dictionary Project Contributors
