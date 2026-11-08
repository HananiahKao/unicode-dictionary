# Developer Notes for Unicode Dictionary Project

## Quick Reference

**Project:** Unicode Character Database → macOS Look Up Dictionary  
**Status:** Built with the real Dictionary Development Kit, installed, and working  
**Key Files:**  
- `build/gen_dict.py` – Main XML generator (249 MB output, 172,873 entries)
- `build/ucd_parse.py` – UCD file parser
- `dist/UnicodeDictionary.xml` – Generated dictionary XML (not tracked in git — regenerate with `make xml`)
- `src/Info.plist` – Dictionary metadata
- `Makefile` – Build automation

**Note:** `data/` (downloaded UCD source) and `dist/` (generated XML/dictionary output) are
gitignored as of 2026-11-08 — they're large, fully reproducible from `make data`/`make xml`/
`make dict`, and don't belong in version control. An earlier version of this doc said they
were intentionally committed "for reference/reproducibility"; that was reversed once the
repo size made it clear reproducibility is better served by the build scripts than by
committing their output.

## Architecture Overview

The project converts text-based Unicode data into an Apple Dictionary:

1. **Data fetch** (`make data`) – curl downloads UCD from Unicode.org
2. **Parse** (`ucd_parse.py`) – Read 12+ text files, build character property objects
3. **Generate** (`gen_dict.py`) – Create Apple Dictionary XML with 172,873 entries
4. **Bundle** (`bundle_dict.py`) – Create `.dictionary` structure (fallback without Kit)
5. **Compile** (Kit's `build_dict.sh`) – Generate binary Body.data and KeyText.index

## Implementation Checklist

- [x] Download UCD files from Unicode.org
- [x] Parse UnicodeData.txt (172,873 assigned characters, Unicode 18.0)
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
3. **Multi-codepoint grapheme clusters (emoji ZWJ sequences, regional-indicator flag
   pairs, skin-tone modifier sequences, IME-composed Hangul jamo clusters) are not
   matched at all** – confirmed empirically (2026-10-22): selecting a composed glyph
   like 👍🏻 and invoking Look Up passes the whole multi-codepoint grapheme cluster to
   Dictionary Services as one exact-match search term. No `d:index` in this dictionary
   is keyed on a multi-codepoint string (every index is single-codepoint or a name/
   alias string; see `generate_entry_xml()` in `gen_dict.py`), so the lookup fails
   outright with "no entries found." There is **no automatic fallback to the base/
   first code point** — that was an earlier, disproven assumption; correct it if you
   see it elsewhere. Each component code point (e.g. the base 👍 and the Fitzpatrick
   modifier 🏻) does have its own entry, reachable by searching its name or U+code
   individually, just not by searching the rendered composed glyph.
4. **No per-character pronunciation** – Would require external data source
5. ~~Hangul syllables and large CJK ideograph ranges are missing entries~~ – **Fixed**
   (commit `bd62a46`): `ucd_parse.py` now expands `<..., First>`/`<..., Last>` ranges
   for CJK ideographs, Hangul syllables, and Tangut ideographs using Python's
   `unicodedata.name()`, which computes names via the same algorithm the Unicode
   Standard specifies. Surrogates and private-use ranges remain unexpanded
   (intentional — they have no inherent name). Still open: `漢` (U+6F22) resolves via
   `DCSCopyTextDefinition` to the wrong, compatibility-duplicate codepoint (U+FA47) —
   a glyph-collision bug, unrelated to the range-expansion fix.
6. ~~New in Unicode 18.0: Jurchen Character and Seal Character ranges not expanded~~
   – **Fixed** (2026-10-22): Python 3.15's `unicodedata` module reports
   `unidata_version == "17.0.0"`, so it can't name Unicode-18.0-only code points
   and `unicodedata.name()` raised `ValueError` for all of them, silently skipped
   by `_parse_unicode_data()`'s existing exception handling. Rather than wait on a
   future Python release, `ucd_parse.py` now hardcodes the two stems directly
   (`_MANUAL_NAME_STEMS`), bypassing `unicodedata.name()` for just these ranges.
   The stems were verified against the Unicode 18.0 Core Specification, Chapter 4,
   Table 4-8 "Name Derivation Rule Prefix Strings"
   (https://www.unicode.org/versions/Unicode18.0.0/core-spec/chapter-4/, fetched
   and grepped as raw HTML, not taken from an AI-summarized fetch, after that
   summarized version turned out to omit a real nuance -- see below):
   - `18E00..19191` (914 chars) → `JURCHEN CHARACTER-XXXX`
   - `3D000..3FC3F` (11,328 chars, the "Small Seal" script) → `SMALL SEAL CHARACTER-XXXX`

   Correction (2026-10-22, caught a factual error from the first version of this
   note): U+191A0-U+191D2 ("Jurchen Radicals", 51 code points) are NOT inside
   the Jurchen Character range and are NOT NamesList.txt chart-annotation-only
   labels as previously claimed here -- 0x191A0 > 0x19191 (compare hex digit by
   digit: the earlier claim mixed this up). They're a separate, adjacent block
   immediately after it, with their own genuine individual UnicodeData.txt
   lines (e.g. `191A0;JURCHEN RADICAL-01;Lo;...`), matching Chapter 4's own
   stated convention that ideographic scripts other than Han and Tangut get
   explicit per-character lines even where NR2-derivable. The existing,
   unmodified single-line parsing path has always picked these up correctly
   with their true official names -- confirmed by checking the dictionary XML
   already committed in 22ba83f, before any radical-specific code existed at
   all. A later attempt in this session to "fix" this with a hardcoded
   `_JURCHEN_RADICAL_ALIASES` table was based on this same mistaken premise and
   has been reverted; it changed no output (confirmed: regenerated XML is
   byte-identical to what was already committed). Nothing was broken and
   nothing needed fixing here.

   172,870 total entries (confirmed unchanged by the correction above), up from
   160,628 before this fix -- exactly 914 + 11,328 = 12,242 more, confirming
   the Python/unicodedata fix covers precisely the two ranges intended and nothing
   else shifted.
7. ~~C0/C1 control codes show the literal "<control>" placeholder as their
   title~~ – **Fixed** (2026-10-22): `UnicodeData.txt` genuinely has no Name
   property for these 65 code points (not an omission -- "<control>" is
   UnicodeData.txt's own placeholder convention for code points with no Name).
   `NameAliases.txt` exists specifically to stand in for this: `_parse_name_
   aliases()` now promotes the first "control"-type alias (or "figment" for
   the 3 never-standardized C1 codes that only have that type) to `.name`,
   same precedence pattern already used for "correction" type. Checked all 65:
   zero still show "<control>" after the fix. Where a code point has more than
   one same-type alias (e.g. U+0009 has both "CHARACTER TABULATION" and
   "HORIZONTAL TABULATION"), the first in file order becomes the title and the
   rest remain as searchable aliases -- NameAliases.txt doesn't document an
   explicit tie-break rule for this, so file order is a pragmatic default, not
   a claimed normative one.
8. ~~Algorithmic names depend on Python's `unicodedata` (version-lagging) and a
   hand-maintained `_MANUAL_NAME_STEMS` table~~ – **Replaced** (2026-10-22):
   switched to `ucd/extracted/DerivedName.txt`, Unicode's own complete,
   pre-computed Name property for every code point -- individual names and
   algorithmic-range patterns alike -- published specifically "so that
   implementations do not have to properly code that derivation" (its own
   header). `_parse_derived_name()` (previously a dead stub that incorrectly
   claimed the file didn't exist -- it does, just under `ucd/extracted/`, not
   `ucd/` directly) now parses it and is the sole authoritative source for
   `.name`; `_parse_unicode_data()`'s range-expansion loop no longer computes
   names at all, just placeholder-fills entries for category/bidi/etc. so
   `_parse_derived_name()` has something to overwrite. `unicodedata` import
   removed entirely -- no more Python-version dependency for naming, and a
   future Unicode version's new algorithmic ranges need no code changes here,
   just a fresh `DerivedName.txt` download.

   Verified via full diff of every entry's name before/after the refactor
   (172,870 entries before -> 172,873 after): zero renames -- everything
   already in the dictionary (including the hand-verified Jurchen/Seal stems
   and the control-character alias fix) matched DerivedName.txt exactly, so
   none of that earlier manual work was wrong. Found exactly 3 new entries
   (18D1F, 18D20 in Tangut Ideograph Supplement; 2B81E in CJK Ideograph
   Extension D) -- all three are code points Unicode 18.0 added to the *tail*
   of ranges that already existed in 17.0, silently dropped by the old
   `unicodedata.name()` + `except ValueError: continue` path because it only
   failed at the newly-extended boundary, not across the whole range, making
   it easy to miss without this kind of exhaustive diff. This is exactly the
   class of gap this refactor eliminates project-wide, not just for Jurchen
   and Seal specifically.

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

**A third, distinct bug (confirmed 2026-10-23, fixed in this project's own markup):**
in the Ctrl+Cmd+D Look Up popover specifically (reproduced in both the isolated single-
dictionary view and the "All dictionaries" aggregate view), an entry whose first child
element is `.glyph` (`font-size: 5.14em`, per `UnicodeDictionary.css`) renders a
completely empty body below the dictionary's section header — title, codepoint table,
case mappings, aliases, everything gone, with no error. The main Dictionary.app browsing
window is unaffected; this is specific to the Look Up popover's content rendering.

Root cause isolated by binary search on Apple's own unmodified sample dictionary
(`project_templates/MyDictionary.xml`), not assumed: built a minimal entry with the exact
production glyph markup (`<div class="glyph" role="img" aria-label="NULL">␀</div>`,
first child) — reproduced the empty-popover symptom with zero other project markup
present, ruling out every other hypothesis tested earlier in this investigation (tables,
`d:priority`, multi-dictionary collisions, CSS bleed between co-displayed dictionaries,
and dictionary scale were all tested and individually ruled out as the cause — see git
history / session notes for those intermediate experiments). Moving the identical
`.glyph` div to *after* `<h1>` in that same test entry fixed it immediately; moving it
back before `<h1>` reproduced the failure again — repeatable both directions. Likely
mechanism (not independently verified against WebKit/Dictionary Services source): the
Look Up popover computes its initial content height from the first child before the
oversized glyph font is applied, then clips/fails to lay out everything after it —
consistent in spirit with the already-documented Apple reflow/scroll-view bug above,
but a distinct trigger (element order, not post-load reflow) and, unlike that one, a
mitigation exists on our side.

**Fix applied:** `generate_entry_html()` in `gen_dict.py` now emits `<h1>` before
`.glyph` (previously `.glyph` was first). Regenerated the full 172,873-entry dictionary
and rebuilt/reinstalled with the Kit after this change. If this element order ever
regresses (e.g. during a refactor of `generate_entry_html()`), this exact bug will
return project-wide in the Look Up popover — keep `<h1>` first among visible children.

### Potential Improvements
- [ ] **Unihan integration** – Add kDefinition, kTotalStrokes, etc. for CJK
- [ ] **Multi-codepoint grapheme cluster search** (ZWJ sequences, flag pairs, skin-tone
  modifiers) – currently unsearchable as a composed glyph (see limitation #3 above).
  Parked design question for a future session: how to index a cluster like 👍🏻 so
  Look Up can match it — candidate directions include emitting a `d:index` keyed on
  the literal multi-codepoint grapheme string per combination actually in use (from
  Unicode's `emoji-sequences.txt`/`emoji-zwj-sequences.txt`, not yet ingested into
  `data/`), or some other mechanism; not yet scoped.
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

- **Dictionary generation:** several seconds for 160k+ entries (XML writing is I/O bound);
  grew substantially once Hangul/CJK/Tangut range expansion and word-level indexing
  were added -- the "~1.5 seconds for 40k+ entries" figure predates both and is stale
- **XML source size:** 249 MB
- **Installed bundle size:** 206 MB (Kit-compiled; not gzip-compressed like the
  no-Kit fallback bundle_dict.py path, so the old "2.2 MB compressed" figure doesn't
  apply to a real Kit build)

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
- **Space:** O(characters) = ~160k CharacterData objects in memory

### Generator
- **Time:** O(characters × indexes) -- now larger than the original O(40k × 5) estimate:
  160k+ characters, and word-level indexing adds a variable number of indexes per
  entry on top of the original fixed ~5
- **Space:** O(characters) for generated entry strings before write
- **I/O:** 249 MB XML write to disk

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

Current version: Unicode 18.0 (September 2026)

---

**Last Updated:** 2026-10-23  
**Maintained By:** Unicode Dictionary Project Contributors
