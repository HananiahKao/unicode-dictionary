# Unicode 18.0.0 `/Public/18.0.0/` Tree — Reference

A complete map of everything reachable from
`https://www.unicode.org/Public/18.0.0/`, compiled by reading each file's own
header comments (not guessed). Written for future development sessions on
the **unicode-dictionary** project (macOS Look Up dictionary built from the
UCD). For each file: one-line content summary, field/column layout when the
file is structured text, and a relevance tag:

- **(a) USED** — already consumed by `build/fetch_ucd.sh` / `build/ucd_parse.py` / `build/gen_dict.py`
- **(b) USEFUL, NOT USED** — plausibly worth ingesting; reason given
- **(c) NOT RELEVANT** — out of scope for a character-property Look Up dictionary

Compiled against the live directory listing and file headers on 2026-10-22.
Note the server's file headers show `© 2026 Unicode®, Inc.` even though this
is "Unicode 18.0.0" — that's the copyright year on the files themselves, not
a typo in this doc.

> Scope note: `MAPPINGS/`, `charts/CodeCharts.pdf`-adjacent legacy encoding
> tables, etc. that live directly under `/Public/` (unversioned) are **not**
> under `/Public/18.0.0/` and are out of scope for this document — the task
> was to document the 18.0.0-versioned tree specifically. (Checked: MAPPINGS
> lives only at `/Public/MAPPINGS/`, not duplicated per-version.)

---

## Top-level layout

```
/Public/18.0.0/
├── ReadMe.txt
├── charts/            — per-block PDF code charts + chart indexes (~421 PDFs)
├── emoji/              — UTS #51 emoji sequence data (sequences, ZWJ, test file)
├── idna/               — UTS #46 IDNA mapping/property data + conformance tests
├── linkification/      — UTS #58 URL/email link-detection property data (NEW area)
├── security/           — UTS #39 confusables & identifier security data
├── uca/                — UTS #10 Unicode Collation Algorithm data (DUCET)
├── ucd/                — the Unicode Character Database itself (what this project parses)
│   ├── auxiliary/      — text-segmentation (grapheme/word/sentence/line break) property + test files
│   ├── emoji/           — UTS #51 files that are normative *UCD* properties (Emoji, EVS)
│   └── extracted/       — same data as other UCD files, pre-filtered to single-property listings
└── ucdxml/             — the whole UCD re-expressed as 6 XML variants (flat/grouped × 3 Unihan modes)
```

`ReadMe.txt` (top level): one paragraph pointing to
`https://www.unicode.org/versions/Unicode18.0.0/` for documentation; says
each subdirectory has its own ReadMe. **(c)** — pure pointer, no data.

This project's `build/fetch_ucd.sh` currently pulls files only from `ucd/`
(12 named files) plus `ucd/emoji/emoji-data.txt` and `ucd/Unihan.zip`. Every
other top-level directory (`charts/`, `emoji/`, `idna/`, `linkification/`,
`security/`, `uca/`, `ucdxml/`) and most of `ucd/` itself has never been
looked at by the pipeline.

---

## `ucd/` — Unicode Character Database

The directory this project already draws from. Below, files already in
`fetch_ucd.sh` are marked **(a) USED**; everything else in `ucd/` is new
territory.

### Root data files

**`UnicodeData.txt`** — 2.1 MB. **(a) USED** — the core per-character record
file; no `#`-comment header (by long-standing convention), so format is
documented in UAX #44, not in-file. Semicolon-delimited, 15 fields per line,
one line per code point (or a `First>`/`<..., Last>` pair bracketing a large
uniform range such as Hangul syllables or CJK ideograph blocks — this is the
documented gap in `CLAUDE.md` about the ~11,172 Hangul syllables and large
Han ranges never being expanded into entries):

| # | Field | Example |
|---|---|---|
| 0 | Code point (hex) | `0041` |
| 1 | Name (or `<control>`/`<CJK Ideograph, First>` etc. for ranges) | `LATIN CAPITAL LETTER A` |
| 2 | General_Category | `Lu` |
| 3 | Canonical_Combining_Class | `0` |
| 4 | Bidi_Class | `L` |
| 5 | Decomposition_Type and Mapping | `<compat> 0041` |
| 6 | Numeric Value — decimal digit | `9` |
| 7 | Numeric Value — digit | `9` |
| 8 | Numeric Value — numeric | `1/4` |
| 9 | Bidi_Mirrored (Y/N) | `N` |
| 10 | Unicode_1_Name (obsolete, Unicode 1.0 name) | |
| 11 | ISO_Comment (obsolete, always empty since Unicode 5.2) | |
| 12 | Simple_Uppercase_Mapping | |
| 13 | Simple_Lowercase_Mapping | |
| 14 | Simple_Titlecase_Mapping | |

**`NameAliases.txt`** — 16 KB. **(a) USED** (added recently per git log: "Use
official NameAliases.txt aliases for control character titles"). Format:
`code; alias; type`, where type is one of `correction`, `control`,
`alternate`, `figment`, `abbreviation`.

**`Blocks.txt`** — 12 KB. **(a) USED**. Format: `Start..End; Block Name`.
Unlisted ranges default to `No_Block`.

**`Scripts.txt`** — 191 KB. **(a) USED**. Format:
`code-or-range ; Script_value # GC_abbrev [count] Name..Name`. Unlisted
defaults to `Unknown`.

**`ScriptExtensions.txt`** — 21 KB. **(a) USED**. Format: `code-or-range ;
space-separated list of Script abbreviations # comment`. Only lists
code points that are used in more than one script; defaults to the plain
Script value otherwise.

**`DerivedAge.txt`** — 139 KB. **(a) USED**. Format: `code-or-range ;
Age-value # comment`, Age being a Unicode version number (e.g. `6.0`) —
the version in which the code point was first assigned.

**`PropList.txt`** — 146 KB. **(a) USED**. Format: `code-or-range ;
Binary_Property_Name # GC [count] Name`, organized as one block per
property (e.g. `White_Space`, `Bidi_Control`, `Join_Control`, `Dash`,
`Deprecated`, etc.), each ending with a `# Total code points: N` comment.

**`DerivedCoreProperties.txt`** — 1.1 MB. **(a) USED**. Same `code-or-range ;
Property_Name # comment` format as PropList.txt, but for *derived* properties
computed from combinations of other properties (`Math`, `Alphabetic`,
`ID_Start`, `ID_Continue`, `Lowercase`, `Uppercase`, `Cased`,
`Grapheme_Extend`, etc.) — each section states what it's "Generated from".

**`EastAsianWidth.txt`** — 200 KB. **(a) USED**. Format: `code-or-range ;
EAW-value` where value ∈ {A, F, H, N, Na, W}. Important defaulting rules
in the header: unassigned code points in CJK Ext-A/URO/CJK-Compat-Ideographs
blocks default to W; unassigned code points in all of Plane 2/3 default to W.

**`LineBreak.txt`** — 260 KB. **(a) USED**. Format: `code-or-range ;
LB-class` (two-letter classes like `AL`, `ID`, `NU`...). Elaborate
defaulting rules for unassigned code points in CJK/Plane 1-emoji/currency
ranges (defaults to `ID`, `ID`, or `PR` respectively) — documented in-header,
worth checking against if the dictionary ever needs line-break display.

**`DerivedNormalizationProps.txt`** — 1.3 MB. **(a) USED**. Multiple
sections, one per derived normalization property (`FC_NFKC`,
`Full_Composition_Exclusion`, `NFD_QC`, `NFC_QC`, `NFKD_QC`, `NFKC_QC`,
`Expands_On_NFC/D/KC/KD` (deprecated), `NFKC_Casefold`,
`Changes_When_NFKC_Casefolded`, etc.). Each section's format is `code(s) ;
Property[=value] ; data # comment` and is explained right above that
section rather than once at the top.

**`BidiMirroring.txt`** — 27 KB. **(a) USED**. Format: `code ; mirror-code`
— two hex code points per line, optionally commented `# BEST FIT` when the
mirroring is only approximate. Characters with no mirror partner are listed
as trailing comments.

**`ArabicShaping.txt`** — 41 KB. **(b) USEFUL, NOT USED** — defines
Joining_Type/Joining_Group for Arabic, Syriac, N'Ko, Mandaic, Manichaean,
Mongolian, Phags-pa, and several more scripts, for positional-shaping
rendering. Format: `code; short-name; Joining_Type; Joining_Group` (4
semicolon fields). Not needed for a definitional lookup dictionary unless
shaping behavior is ever described per-character; `DerivedJoiningType.txt`/
`DerivedJoiningGroup.txt` (in `extracted/`) supersede it per its own header.

**`BidiBrackets.txt`** — 8.8 KB. **(b) USEFUL, NOT USED** — defines
Bidi_Paired_Bracket / Bidi_Paired_Bracket_Type for the Unicode Bidi
Algorithm. Format: `code; paired-code; type(o|c) # Name`. Could enrich
bracket-character entries (e.g. showing the bidi pairing partner) but is a
niche enhancement, not a gap called out in CLAUDE.md.

**`BidiCharacterTest.txt`** (6.6 MB) / **`BidiTest.txt`** (7.6 MB) — **(c)
NOT RELEVANT** — these are UBA conformance *test suites* (input sequences +
expected resolved levels/reordering), not character property data. Formats
documented in-header (5 fields for BidiCharacterTest: codepoints; paragraph
direction; resolved level; per-char levels; visual order indices — 4 fields
for BidiTest using symbolic bidi-class tokens rather than codepoints). No use
to a dictionary generator.

**`CJKRadicals.txt`** — 5.4 KB. **(c) borderline NOT RELEVANT** —
maps CJK radical numbers (as used in `kRSUnicode`) to the radical character
and an equivalent CJK unified ideograph. Format: `radical-number; radical-char;
unified-ideograph-char` (3 semicolon fields). Only useful if the dictionary
ever displays radical/stroke indices for Han characters — currently it
doesn't, so not relevant unless that's pursued.

**`CaseFolding.txt`** — 87 KB. **(c) NOT RELEVANT for current scope** — full
+ simple case-folding mappings (format: `code; status(C/F/S/T); mapping(s) #
comment`, where C=common, F=full, S=simple, T=Turkic). Used for
case-insensitive matching/search, not for displaying character properties;
not needed unless the dictionary adds search-folding behavior.

**`CompositionExclusions.txt`** — 8.8 KB. **(c) NOT RELEVANT** — lists code
points excluded from the NFC composition table (format: `code # comment`,
single field + comment). A normalization-algorithm input, not display data.
(Superseded for programmatic use by `Full_Composition_Exclusion` in
`DerivedNormalizationProps.txt`, already fetched.)

**`DoNotEmit.txt`** — 51 KB. **(b) marginally USEFUL, NOT USED** — lists
discouraged/deprecated character *sequences* that authoring tools should
avoid generating, with a suggested alternative sequence. Could in principle
feed a "discouraged — use X instead" annotation on relevant entries, but is
a narrow, low-priority enhancement not mentioned in CLAUDE.md's gap list.

**`EmojiSources.txt`** — 13 KB. **(c) NOT RELEVANT** — historical mapping
table from Unicode emoji to Japanese carrier (DoCoMo/KDDI/SoftBank)
Shift-JIS codes. Format: 4 semicolon fields (codepoint-or-sequence; DoCoMo
code; KDDI code; SoftBank code). Legacy round-trip data, no modern display
value.

**`EquivalentUnifiedIdeograph.txt`** — 18 KB. **(b) USEFUL for the known
glyph-collision bug** — maps CJK radicals/strokes to a visually-identical
CJK unified ideograph. Format: `code-or-range; unified-ideograph-code`.
This is adjacent to, but not the same bug as, the CLAUDE.md-documented
U+6F22 ↔ U+FA47 compatibility-duplicate issue (that's a *compatibility
ideograph* canonical-decomposition collision, not a *radical* mapping) — so
this file alone won't fix it, but is worth knowing about when debugging
Han glyph-identity issues generally.

**`HangulSyllableType.txt`** — 50 KB. **(b) USEFUL — directly closes a
documented gap**. Defines Hangul_Syllable_Type (`L`/`V`/`T`/`LV`/`LVT`) for
each conjoining jamo and syllable block. Format: `code-or-range ;
type-abbrev # GC [count] Name..Name`. Combined with `Jamo.txt` (below), this
is exactly the data needed to **implement the Hangul Syllable Name algorithm**
and expand the ~11,172 missing Hangul syllable entries that CLAUDE.md flags
as a known limitation.

**`Index.txt`** — 166 KB. **(b) USEFUL, NOT USED** — a human-curated
"inverted" name index (format: `Natural-language sort key\tcodepoint`, tab
separated, no header comments at all) used to build the printed charts'
back-of-book index (e.g. "A WITH ACUTE, LATIN CAPITAL LETTER" rather than
"LATIN CAPITAL LETTER A WITH ACUTE"). Could be used to add alternate
natural-order search terms to `d:index` entries, but isn't a gap currently
flagged.

**`IndicPositionalCategory.txt`** — 51 KB / **`IndicSyllabicCategory.txt`**
— 85 KB. **(c) NOT RELEVANT for current dictionary scope** — detailed Indic
script segmentation/shaping properties (where a combining mark sits
relative to a consonant, syllable-structure role). Format: `code-or-range ;
category-value # GC Name`. Useful only for Indic rendering engines, not for
a definitional lookup entry.

**`Jamo.txt`** — 3.3 KB. **(b) USEFUL — directly closes a documented gap**.
Defines `Jamo_Short_Name` (e.g. `1100;G`, the "G" in Hangul syllable names
like "HANGUL SYLLABLE GA"). Format: `code; short-name # Name`. Required,
together with `HangulSyllableType.txt`, to implement the algorithmic Hangul
Syllable Name generation that `ucd_parse.py` is noted as not yet doing.

**`JurchenSources.txt`** — 77 KB / **`TangutSources.txt`** — 387 KB /
**`NushuSources.txt`** — 23 KB / **`Unikemet.txt`** (Egyptian Hieroglyphs) —
1.4 MB / **`SealSources.txt`** (Small Seal script) — 1.8 MB. **(c) NOT
RELEVANT** (optional enrichment at most) — all five are tagged, Unihan-style
data files (`U+code<TAB>tag<TAB>value`, one tag per line) giving
script-specific scholarly source/reference/reading/radical data for small
historic scripts newly or recently encoded (Jurchen, Tangut, Nüshu, Egyptian
Hieroglyphs, Chinese seal script). Each has its own tag vocabulary
documented in its header (e.g. `kTGT_MergedSrc`, `kEH_Desc`, `kSEAL_MCJK`).
Low general value for a Look Up dictionary; would only matter for
specialist entries on those scripts.

**`NamedSequences.txt`** — 20 KB / **`NamedSequencesProv.txt`** (provisional)
— 2.0 KB. **(b) USEFUL, NOT USED** — defines official multi-codepoint Named
Character Sequences (e.g. keycap digits, some flag-like sequences) that have
a name but no single code point. Format: `Name;code code code...`
(semicolon between name and the space-delimited codepoint list). This is
UCD's native (small, curated) analog to the much larger emoji-sequence
files, and the most directly relevant data for the CLAUDE.md-flagged gap of
"multi-codepoint grapheme clusters... aren't currently searchable" — though
it won't cover emoji ZWJ sequences (those live in the separate top-level
`emoji/` directory, see below).

**`NormalizationCorrections.txt`** — 2.2 KB. **(c) NOT RELEVANT** — tiny (6
entries) historical record of decomposition-mapping typos corrected under
Unicode Corrigenda #3/#4, kept only for exact-reconstruction of old data.
Format: `code;old-decomp;new-decomp;version # Corrigendum N`.

**`PropertyAliases.txt`** — 9.7 KB. **(b) marginally USEFUL, NOT USED** —
maps every UCD property's short/abbreviated name to its long/formal name
(and any other aliases). Format: `short; long; (more aliases...)`. Could be
used to show full property names instead of abbreviations in the generated
HTML (e.g. show "General_Category" instead of raw "Lu") — a possible
"Better styling" polish item, not currently fetched.

**`PropertyValueAliases.txt`** — 82 KB. **(b) marginally USEFUL, NOT USED**
— same idea, but for property *values* (e.g. `gc ; Lu ; Uppercase_Letter`).
Format: `property; short-value; long-value` (4 fields for
Canonical_Combining_Class, which also carries a numeric value field). Same
potential use as PropertyAliases.txt — expanding abbreviations for display.

**`SpecialCasing.txt`** — 17 KB. **(c) NOT RELEVANT for current scope** —
full (context/locale-dependent) case mappings beyond the simple 1:1 mappings
in UnicodeData.txt fields 12–14 (e.g. Turkish dotless i, German ß→SS).
Format: `code; lower; title; upper; (conditions;)? # comment`. Only matters
if the dictionary ever shows full case-mapping behavior per character.

**`StandardizedVariants.txt`** — 76 KB. **(b) marginally USEFUL, NOT USED**
— defines standardized variation sequences (base + variation selector →
specific glyph meaning, e.g. text-style vs. emoji-style, or CJK unified
ideograph + VS → specific source glyph). Format: `code+VS; description;
Unicode-1-ref # comment`. Relevant to "variant charts" potential improvement
in CLAUDE.md, and to the Han-glyph-identity debugging context (it's where
CJK compatibility/variant glyph relationships beyond
`EquivalentUnifiedIdeograph.txt` are formally recorded).

**`USourceData.txt`** — 252 KB. **(c) NOT RELEVANT for current scope** —
basic status/cross-reference data for "U-source" (IRG submission) CJK
ideographs not otherwise in Unihan — which extension block they ended up
in, their radical-stroke index, etc. 10 tab-separated fields, documented
fully in-header. Niche CJK-encoding-history data.

**`USourceGlyphs.pdf`** / **`USourceRSChart.pdf`** — PDF glyph charts for
U-source ideographs / radical-stroke chart. **(c) NOT RELEVANT** — binary,
one-liner only as instructed.

**`VerticalOrientation.txt`** — 188 KB. **(c) NOT RELEVANT for current
scope** — defines whether a character should be rotated when set
vertically (CJK vertical text layout, UAX #50). Format: `code-or-range ;
U|R|Tu|Tr`. Would only matter for a vertical-text rendering feature, not a
lookup dictionary.

**`UCD.zip`** — 5.4 MB. **(c) NOT RELEVANT as a separate fetch** — a
convenience bundle containing all the plain-text UCD files above in one
archive; redundant with fetching individual files, which is what
`fetch_ucd.sh` already does.

**`Unihan.zip`** — 8.0 MB. **(a) USED** — already downloaded by
`fetch_ucd.sh`, flagged in CLAUDE.md as only partially integrated
(`kDefinition`, `kTotalStrokes` etc. not yet surfaced in generated entries —
listed as a "Potential Improvement").

**`ReadMe.txt`** (ucd/) — 729 B. **(c)** — pointer to version docs and to
UAX #38/#42/#44, UTS #51, UAX #57/#60; mentions `NamesList.html` lives here
too.

**`NamesList.html`** — 36 KB. **(c) NOT RELEVANT** — HTML rendering/index of
NamesList.txt content; superseded for parsing purposes by the `.txt` file
below.

**`NamesList.txt`** — 2.0 MB. **(b) HIGH-VALUE, NOT USED** — the file
explicitly flagged in the task background as "already consulted ad hoc this
session." Its own header is explicit that **it is semi-automated and
annotation-rich but not intended to be machine-parsed** ("this file should
not be parsed for machine-readable information"). Structure is a custom
line-tag format, not CSV/semicolon fields:
- `@@` — block header line (`@@  start-code  Block Name (alt name)  end-code`)
- plain hex code + tab + character name
- `=` lines — alias/cross-reference names
- `x` lines — cross-references ("see also")
- `~` lines — abbreviation-of/related-to glyph variant notes
- `#` and `*` lines — informative annotation/comment text explaining a
  character's usage (this is the richest content — see e.g. its header's
  note that "Alias names are those for ISO/IEC 6429:1992...").
This is the best available source for rich, human-written explanatory
annotations per character — exactly the kind of content a Look Up
dictionary entry benefits from beyond bare property tables — but because
Unicode itself disclaims its machine-readability, any ingestion would need
a hand-tolerant parser (treat it as semi-structured, expect exceptions) and
should probably be used to **supplement**, not replace, `UnicodeData.txt`
as the source of truth for names.

### `ucd/auxiliary/` — text segmentation properties

Implements UAX #29 (grapheme/word/sentence breaking) and UAX #14 (line
breaking, supplementing the root `LineBreak.txt`). All property files
share the same format: `code-or-range ; Break_Class # GC [count] Name`,
each `*Test.txt` a `÷`/`×`-annotated break-opportunity test string format
(documented in matching `*Test.html`, referenced but not fetched).

- **`GraphemeBreakProperty.txt`** — Grapheme_Cluster_Break property (values
  like `Prepend`, `Extend`, `ZWJ`, `Regional_Indicator`...). **(b) HIGH
  RELEVANCE, NOT USED** — this is the actual UAX #29 property needed to
  correctly segment multi-codepoint grapheme clusters (flags, ZWJ
  sequences, skin-tone modifiers) for display/lookup purposes — more
  fundamental than the emoji-sequence lists themselves for the
  CLAUDE.md-flagged "emoji ZWJ sequences... not fully supported" gap, since
  it's the general mechanism, not just an enumerated emoji list.
- **`WordBreakProperty.txt`** / **`SentenceBreakProperty.txt`** — same
  format, for word/sentence boundaries. **(c) NOT RELEVANT** to a
  per-character dictionary.
- **`GraphemeBreakTest.txt`**, **`WordBreakTest.txt`**,
  **`SentenceBreakTest.txt`**, **`LineBreakTest.txt`** (+ matching `.html`
  docs) — conformance test suites for the above. **(c) NOT RELEVANT** —
  tests, not property data.

### `ucd/emoji/` — UTS #51 files that are normative UCD properties

- **`ReadMe.txt`** — points to the sibling top-level `emoji/` directory for
  the sequence/test files, clarifying the split: *this* directory holds
  only the two files that are formal UCD binary/string properties.
- **`emoji-data.txt`** — 13 KB (fetched by current pipeline, but as a
  single-property cross-cut of `PropList.txt`/`DerivedCoreProperties.txt`,
  not `emoji-sequences.txt`). **(a) USED**. Format: `code-or-range ;
  Property # Ex.n [count] (glyph) name`, covering `Emoji`,
  `Emoji_Presentation`, `Emoji_Modifier`, `Emoji_Modifier_Base`,
  `Emoji_Component`, `Extended_Pictographic`, `Basic_Emoji` component
  listings.
- **`emoji-variation-sequences.txt`** — 13 KB. **(b) USEFUL, NOT USED** —
  defines the `FE0E`/`FE0F` (text-style/emoji-style) variation sequences.
  Format: `base FE0E|FE0F ; "text style"|"emoji style"; # (version) Name`.
  Directly useful for correctly representing/searching emoji-presentation
  variants of dual-presentation characters (e.g. `#️`, `*️`) that currently
  likely resolve only to their base codepoint.

### `ucd/extracted/` — single-property re-derivations

Twelve files, each re-publishing *one* property already present (sometimes
combined/derived from multiple fields) in another normative file, filtered
to just that property's `code-or-range ; value # comment` listing. Useful
as a simpler, already-filtered source for a property instead of parsing the
wider file, but functionally redundant with data the pipeline can already
get from `UnicodeData.txt` + friends:

| File | Source of the data (per its own header) |
|---|---|
| `DerivedBidiClass.txt` | UnicodeData.txt field 4 |
| `DerivedBinaryProperties.txt` | UnicodeData.txt field 9 (Bidi_Mirrored) |
| `DerivedCombiningClass.txt` | UnicodeData.txt field 3 |
| `DerivedDecompositionType.txt` | UnicodeData.txt field 5 |
| `DerivedEastAsianWidth.txt` | EastAsianWidth.txt field 1 |
| `DerivedGeneralCategory.txt` | UnicodeData.txt field 2 |
| `DerivedJoiningGroup.txt` | ArabicShaping.txt field 3 |
| `DerivedJoiningType.txt` | computed per ArabicShaping.txt rules |
| `DerivedLineBreak.txt` | LineBreak.txt |
| `DerivedName.txt` | UnicodeData.txt Name field + Jamo.txt + algorithmic name patterns |
| `DerivedNumericType.txt` | UnicodeData.txt fields 6–8 + Unihan numeric fields |
| `DerivedNumericValues.txt` | UnicodeData.txt field 8 + Unihan numeric fields |

**`DerivedName.txt` — (a) USED** (as of 2026-10-22, shortly after this doc
was written). Acted on exactly the recommendation below: it's now the sole
authoritative source for `CharacterData.name` in `ucd_parse.py`
(`_parse_derived_name()`), replacing a Python-`unicodedata`-based approach
that silently dropped any code point newer than the interpreter's bundled
Unicode version. Confirmed via full before/after diff: zero renames against
everything already in the dictionary, plus 3 previously-missing code points
recovered (boundary extensions to the Tangut Ideograph Supplement and CJK
Ideograph Extension D ranges that Python's `unicodedata` didn't know yet).
See `CLAUDE.md` limitation #8 for the full writeup. (Original note, kept for
context: its header says explicitly it's "a full listing of the derived
[Name] values so that implementations do not have to properly code that
derivation," including pattern-based algorithmic names for Hangul syllables
and CJK/Tangut ranges via `*` pattern strings — exactly what made this the
right fix.)

All other `extracted/` files: **(c) NOT RELEVANT as new ingestion targets**
— the pipeline already derives equivalent information from the files it
parses directly.

---

## `emoji/` (top level) — UTS #51 sequence & test data

Distinct from `ucd/emoji/`: this directory holds the emoji data that is
*not* itself a formal UCD character property but rather sequence/grouping
data layered on top (per its ReadMe, which cross-references `ucd/emoji/`).

- **`ReadMe.txt`** — explains the split between this dir and `ucd/emoji/`.
- **`emoji-sequences.txt`** — **(b) HIGH VALUE, NOT USED** — defines
  `Basic_Emoji`, `Emoji_Keycap_Sequence`, `RGI_Emoji_Flag_Sequence`,
  `RGI_Emoji_Tag_Sequence`, `RGI_Emoji_Modifier_Sequence` (e.g. skin-tone
  modifier combinations, flag sequences from two Regional_Indicator
  codepoints). Format: `code(s) ; type_field ; CLDR short name # comments`.
  This is one of the two files CLAUDE.md names by filename as a suspected
  (unscoped) fix for "flag pairs, skin-tone modifiers... not currently
  searchable."
- **`emoji-zwj-sequences.txt`** — **(b) HIGH VALUE, NOT USED** — the other
  file CLAUDE.md names by filename. Defines `RGI_Emoji_ZWJ_Sequence`
  entries (e.g. family groupings, "couple with heart", skin-toned
  professions) joined with U+200D ZERO WIDTH JOINER. Same 3-field format as
  `emoji-sequences.txt`, organized into commented subgroups (`# ... :
  Family`, etc.).
- **`emoji-test.txt`** — **(c) NOT RELEVANT as a data source** — a
  keyboard/display *test/reference* listing in CLDR (not codepoint) order,
  tagging each sequence `component` / `fully-qualified` /
  `minimally-qualified` / `unqualified`. Useful only to cross-check
  coverage/qualification status, not as a primary content source; the RGI
  (Recommended for General Interchange) set is already fully covered by the
  two sequence files above.

**Scoping conclusion for the CLAUDE.md "hasn't been scoped" emoji-sequence
question**: yes, `emoji-sequences.txt` + `emoji-zwj-sequences.txt` are
exactly the right files, confirmed by reading their own headers. The
remaining design work is in `ucd_parse.py`/`gen_dict.py`: representing a
multi-codepoint sequence as a dictionary entry/index (likely alongside
`ucd/auxiliary/GraphemeBreakProperty.txt`-driven grapheme-cluster handling
so arbitrary ZWJ combos beyond the curated RGI set don't break lookup).

---

## `idna/` — UTS #46 Internationalized Domain Names

**(c) NOT RELEVANT** to this project as a whole — domain-name
validation/mapping rules, not character display properties.

- **`ReadMe.txt`** — scope note; also covers `Idna2008.txt`'s relation to
  RFC 5892.
- **`Idna2008.txt`** — 2 fields: `code-or-range ; IDNA2008_Category` where
  category ∈ {PVALID, CONTEXTJ, CONTEXTO, DISALLOWED, UNASSIGNED}.
- **`IdnaMappingTable.txt`** — UTS #46 preprocessing table. Format:
  `code-or-range ; status ; mapping ; (NV8|XV8 flag) # comment`, status ∈
  {valid, mapped, disallowed, deviation, ignored, disallowed_STD3_valid,
  disallowed_STD3_mapped}.
- **`IdnaTestV2.txt`** — conformance test cases (`source; toUnicode;
  toUnicodeStatus; toAsciiN; ...` — 5+ semicolon columns, documented fully
  in-header).

---

## `linkification/` — UTS #58 Link Detection and Formatting

New-ish (UTS #58) technical standard for auto-detecting/formatting URLs and
email addresses in plain text. **(c) NOT RELEVANT** to a character-property
Look Up dictionary — this is about *text scanning for links*, not per-
character metadata, though each property file is itself keyed by code
point so it's structurally similar to UCD property files.

- **`ReadMe.txt`** — scope pointer to UTS #58.
- **`LinkBracket.txt`** — `Link_Bracket` property: `code; matching-open-
  bracket-code # version (sample) Name` — which bracket characters pair for
  link-boundary trimming.
- **`LinkEmail.txt`** — `Link_Email` binary property: `code-or-range #
  version [count] (sample) Name` — which characters are valid in the local
  part of an email address for linkification purposes.
- **`LinkTerm.txt`** — `Link_Term` enumerated property: `code-or-range ;
  value # version [count] (sample) Name`, value ∈ {Include, Hard, Soft,
  Close, Open} — how a character terminates a detected link.
- **`LinkDetectionTest.txt`** — plain-text test corpus using `⸠`/`⸡`
  brackets to mark expected detected links.
- **`LinkFormattingTest.txt`** — paired source/result test lines (escaped
  vs. minimally-escaped URL display forms), with inline `𝑺`/`𝑯`/`𝑷`/`𝑸`/`𝑽`/
  `𝑭`/`𝑫` annotation characters marking URL-structure parts (schema, host,
  path, query, value, fragment, fragment-directive) in comments.

---

## `security/` — UTS #39 Unicode Security Mechanisms

Visual/identifier confusables and security classification data. **Directly
relevant to the "homoglyph-detection features" possibility** flagged in the
task background as never having been looked at.

- **`ReadMe.txt`** — scope pointer to UTS #39.
- **`confusables.txt`** — **(b) USEFUL for a potential new feature, NOT
  USED** — the core confusable-mapping table: maps a code point or sequence
  to another, visually-confusable target, each tagged with a confusable
  type. Format: `source(s) ; target(s) ; type(SL|SA|ML|MA) # ( glyph → glyph
  ) Source Name → Target Name #`, where S/M = Single/Multiple script, L/A =
  identical/similar appearance. This is the primary data source if the
  project ever wants to add "this character is visually confusable with: …"
  cross-reference content to entries — a natural fit for a dictionary whose
  core subject is characters, and not previously considered per the task
  background.
- **`confusablesSummary.txt`** — **(c) NOT RELEVANT as a separate source**
  — a grouped, human-readable re-presentation of the same confusables.txt
  data (one skeleton glyph with all its confusable variants listed
  together); redundant with confusables.txt for programmatic use.
- **`intentional.txt`** — **(b) marginally USEFUL** — lists confusable
  pairs that are considered *intentional/acceptable* in context (e.g. Latin
  A ~ Greek Alpha, Latin C ~ Cyrillic Es) rather than security problems.
  Format: `source ; target # ( glyph ~ glyph ) Source Name ~ Target Name`.
  Would matter only if building out the confusables feature with a
  severity/intentionality distinction.
- **`IdentifierStatus.txt`** — **(c) NOT RELEVANT** — classifies each code
  point `Allowed`/`Restricted` for use in programming-language/protocol
  identifiers. Format: `code-or-range ; Allowed|Restricted # version Name`.
- **`IdentifierType.txt`** — **(c) NOT RELEVANT** — finer-grained
  classification per code point into a *set* of values (`Not_Character`,
  `Deprecated`, `Default_Ignorable`, `Not_NFKC`, `Not_XID`, `Exclusion`,
  `Obsolete`, `Technical`, `Uncommon_Use`, `Limited_Use`, `Inclusion`,
  `Recommended`). Format: `code-or-range ; {set of values} # version Name`.
  Could in principle flag "Obsolete"/"Deprecated" characters in the UI, but
  overlaps with existing `Deprecated` property already available via
  `PropList.txt`.
- **`uts39-data-18.0.0.zip`** — bundle of the above as a single archive.
  **(c) NOT RELEVANT as a separate fetch** — redundant with individual
  files.

---

## `uca/` — UTS #10 Unicode Collation Algorithm

Defines sort/collation order, not display/definition content. **(c) NOT
RELEVANT** to a Look Up dictionary (which displays character information,
not sorted lists) — though it's exactly the piece needed if the project
ever wants a well-defined "sort my 40k dictionary entries in proper Unicode
default-collation order" behavior instead of raw code-point order.

- **`ReadMe.txt`** — scope pointer to UTS #10.
- **`allkeys.txt`** — the Default Unicode Collation Element Table (DUCET).
  Custom format, not semicolon-CSV: `code(s) ; [primary.secondary.tertiary]
  (variant markers) # Name`, plus `@implicitweights` directives for
  algorithmically-weighted large unassigned-script ranges (Tangut, Nüshu,
  Khitan Small Script, etc.).
- **`ctt.txt`** — a POSIX `LC_COLLATE` "Common Template Table" rendering of
  the same collation data, in ISO/IEC TR 30112 locale-definition syntax
  (`collating-symbol`, `%`-comment POSIX locale format) — for systems that
  consume POSIX locale collation data directly.
- **`decomps.txt`** — the decompositions actually used internally to derive
  DUCET (a collation-tuned variant of UnicodeData.txt's canonical
  decompositions — occasionally suppressed/adjusted for better collation
  weights). Format: `code; decomposition-tag; decomposition # comment`.
- **`CollationTest.zip`** — conformance test data for UCA implementations.
  **(c)** — zip, test data, one-liner only.

---

## `ucdxml/` — UCD re-expressed as XML (UAX #42)

**(c) NOT RELEVANT as an ingestion source** — this is the *same* UCD data
the pipeline already parses from the native `.txt` files, just re-encoded
as XML per UAX #42. Switching `ucd_parse.py` to consume this instead of the
individual `.txt` files would be a large refactor for no new data — the
`.txt` files remain authoritative per `ucdxml.readme.txt`'s own disclaimer
("there may be some errors; the UCD files are authoritative").

- **`ucdxml.readme.txt`** — explains the flat-vs-grouped ×
  no-Unihan/Unihan-only/complete axes (6 total combinations).
- **`ucd.all.flat.zip`**, **`ucd.all.grouped.zip`** — complete UCD
  (including Unihan), flat repeat-every-attribute-per-char vs.
  grouped-by-block XML structuring.
- **`ucd.nounihan.flat.zip`**, **`ucd.nounihan.grouped.zip`** — same, minus
  Unihan-sourced properties.
- **`ucd.unihan.flat.zip`**, **`ucd.unihan.grouped.zip`** — Unihan-only
  properties/characters, in each structuring style.

All six are zip archives; one-liners only per task instructions (no
extraction).

---

## `charts/` — PDF code charts (one-liner group summary)

**(c) NOT RELEVANT as ingestable data** — these are typeset, printable PDF
references of the code charts, meant for human browsing/citation, not
programmatic consumption. The directory is actually an HTML index page
(`https://www.unicode.org/Public/18.0.0/charts/`, not a plain Apache
autoindex) linking out to:

- **`PDF/U<hex>.pdf`** — **~421 files**, one PDF per Unicode block (e.g.
  `PDF/U0041.pdf` for Basic Latin — note chart filenames key off the block's
  *starting* code point, not the block name). Each is a standard
  code-chart page: grid of glyphs with hex labels, block name header, and a
  names-list excerpt. Representative examples seen: `U0400.pdf` (Cyrillic),
  `U1F00.pdf` (Greek Extended), `U10800.pdf` (Cypriot Syllabary).
- **`collation/`** — chart(s) specifically for collation-order
  presentation (cross-referenced from the UCA pages).
- **`nameslist/`** — HTML-rendered, chart-linked version of the
  `NamesList.txt` content, split per block/range for browsing.
- **`RSIndex.txt`** — radical-stroke index text file (companion to the
  `USourceRSChart.pdf` / `CJKRadicals.txt` radical-index material already
  covered above under `ucd/`).
- **`About.html`**, **`charindex.html`** — chart conventions/help page and
  a combined name index across all charts (overlaps in purpose with
  `ucd/Index.txt`).

No reason to enumerate all 421 PDFs individually — they're a single
uniform, auto-generated-per-block pattern with no per-file variation worth
documenting beyond "it's the printable chart for that block."

---

## Priority recommendations (tie-back to CLAUDE.md gaps)

1. ~~Hangul syllables / large Han ranges~~ — **Done** (2026-10-22, same day
   this doc was written): `ucd/extracted/DerivedName.txt` did give the
   already-expanded names directly, as suspected. Now the sole source for
   `CharacterData.name` project-wide. See `CLAUDE.md` limitation #8.
2. **Emoji ZWJ sequences / flag pairs / skin-tone modifiers (documented
   limitation, "hasn't been scoped")** — confirmed: `emoji/emoji-
   sequences.txt` and `emoji/emoji-zwj-sequences.txt` are the right files,
   plus `ucd/emoji/emoji-variation-sequences.txt` for text/emoji
   presentation variants, plus `ucd/auxiliary/GraphemeBreakProperty.txt` for
   the general grapheme-cluster mechanism underlying all of them.
3. **`NamesList.txt` ingestion** — richest source of human-written
   explanatory annotation per character, but explicitly self-disclaimed as
   not strictly machine-parseable; would need a tolerant custom parser, used
   to *supplement* `UnicodeData.txt`, not replace it.
4. **`NamedSequences.txt`** — the UCD-native (non-emoji) named multi-
   codepoint sequences; smaller and more strictly formatted than the emoji
   sequence files, easy additional win for the "sequences aren't
   searchable" gap.
5. **`security/confusables.txt`** (+ `intentional.txt`) — net-new feature
   opportunity (homoglyph cross-references) raised in the task background,
   not previously considered by the project.
6. **`PropertyAliases.txt` / `PropertyValueAliases.txt`** — low-effort
   display polish (expand `Lu` → `Uppercase_Letter` etc.) matching the
   CLAUDE.md "Better styling" potential improvement.
7. Lower priority / optional: `StandardizedVariants.txt` and
   `EquivalentUnifiedIdeograph.txt` for variant/cross-reference charts
   (another listed potential improvement), and general awareness that the
   CLAUDE.md-documented U+6F22/U+FA47 glyph-collision bug is a
   *compatibility-decomposition* identity issue, not something these two
   files alone resolve — `DerivedDecompositionType.txt` /
   `DerivedNormalizationProps.txt` (already fetched) are the more directly
   relevant existing sources for debugging that specific bug.
