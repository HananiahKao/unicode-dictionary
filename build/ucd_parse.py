#!/usr/bin/env python3
"""
Unicode Character Database parser.
Reads all UCD files and provides access to character properties.
Treat UCD data files as untrusted; run with python3 -I.
"""

import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class CharacterData:
    """Complete data for a single Unicode character."""
    codepoint: int
    name: str  # official name or derived name
    aliases: List[str]  # alternate names
    category: str  # L, Ll, Lm, Lo, Lu, Mn, Mc, Me, Nd, Nl, No, Pc, Pd, Ps, Pe, Pi, Pf, Po, Sm, Sc, Sk, So, Zs, Zl, Zp, Cc, Cf, Cs, Co, Cn
    combining_class: int
    bidi_class: str  # L, R, AL, EN, ES, ET, AN, CS, NSM, BN, B, S, WS, ON, LRE, LRO, RLE, RLO, PDF, etc.
    bidi_mirrored: bool
    bidi_mirror_char: Optional[int]  # code point of mirror character if mirrored
    decomposition: Tuple[str, List[int]]  # (type, [codepoints]) e.g., ("compat", [0x1234, 0x5678])
    numeric_value: Optional[Tuple[int, int]]  # (numerator, denominator) if numeric
    numeric_type: str  # "Decimal", "Digit", "Numeric", or ""
    uppercase_mapping: Optional[int]
    lowercase_mapping: Optional[int]
    titlecase_mapping: Optional[int]
    block: str  # block name
    script: str  # script name
    script_extensions: Set[str]  # additional scripts
    age: Optional[str]  # version (e.g., "1.1", "3.0", "14.0")
    east_asian_width: str  # F, H, W, Na, A, N
    line_break: str  # Open, Close, Exclamation, etc.
    props: Set[str]  # boolean properties: Alphabetic, Emoji, Math, White_Space, ID_Start, ID_Continue, etc.

    def to_xml_id(self) -> str:
        """Generate a safe XML ID for this character."""
        if self.name:
            # Sanitize name for use as ID
            safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', self.name.lower())
            return f"U_{self.codepoint:04X}_{safe_name[:30]}"
        return f"U_{self.codepoint:04X}"


class UCDParser:
    """Parse Unicode Character Database files."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.characters: Dict[int, CharacterData] = {}
        self.blocks: Dict[str, Tuple[int, int]] = {}
        self.scripts: Dict[str, Set[int]] = {}

    def parse_all(self) -> Dict[int, CharacterData]:
        """Parse all UCD files and return complete character database."""
        print("Parsing UnicodeData.txt...")
        self._parse_unicode_data()

        print("Parsing DerivedName.txt...")
        self._parse_derived_name()

        print("Parsing Blocks.txt...")
        self._parse_blocks()

        print("Parsing Scripts.txt...")
        self._parse_scripts()

        print("Parsing ScriptExtensions.txt...")
        self._parse_script_extensions()

        print("Parsing NameAliases.txt...")
        self._parse_name_aliases()

        print("Parsing DerivedAge.txt...")
        self._parse_derived_age()

        print("Parsing PropList.txt...")
        self._parse_prop_list()

        print("Parsing DerivedCoreProperties.txt...")
        self._parse_derived_core_properties()

        print("Parsing EastAsianWidth.txt...")
        self._parse_east_asian_width()

        print("Parsing LineBreak.txt...")
        self._parse_line_break()

        print("Parsing BidiMirroring.txt...")
        self._parse_bidi_mirroring()

        print("Assigning blocks to characters...")
        self._assign_blocks()

        return self.characters

    # <..., First>/<..., Last> range labels whose code points have real,
    # individually-meaningful names and should get one entry per code point.
    # Ranges not listed here (surrogates, private-use planes) have no inherent
    # name and are intentionally left unexpanded -- one entry per code point
    # there would be meaningless and would bloat the dictionary by ~1M entries.
    #
    # Naming itself is no longer this method's problem (2026-10-22 rewrite):
    # entries created in the expansion loop below get an empty placeholder
    # name, and _parse_derived_name() -- called right after this method, see
    # parse_all() -- fills it in authoritatively from DerivedName.txt,
    # Unicode's own complete, pre-computed Name property for every code point
    # (individual names and algorithmic-range patterns alike), published
    # specifically "so that implementations do not have to properly code that
    # derivation" (its own header). This replaces an earlier approach that
    # called Python's bundled `unicodedata.name()` and hand-maintained a
    # _MANUAL_NAME_STEMS table for ranges it didn't know yet (confirmed
    # 2026-10-22: unicodedata.unidata_version stayed at "17.0.0" well after
    # Unicode 18.0 shipped, so it couldn't name Jurchen Character or Seal
    # Character at all). Using DerivedName.txt instead means a future Unicode
    # version's new algorithmically-named ranges need no code changes here --
    # just a fresh DerivedName.txt download -- and it's also unaffected by the
    # Jurchen Radicals situation (U+191A0-U+191D2, a separate adjacent block
    # with its own real individual names, not nested inside this range at all
    # despite an earlier version of this comment claiming otherwise -- see
    # commit 7e46c31): DerivedName.txt already reconciles that correctly since
    # it's Unicode's own final computed output, not a raw range pattern we'd
    # have to reconcile against exceptions ourselves.
    _EXPANDABLE_RANGE_PREFIXES = (
        "CJK Ideograph", "Hangul Syllable", "Tangut Ideograph",
        "Jurchen Character", "Seal Character",
    )

    def _build_character(self, codepoint: int, name: str, fields: List[str]) -> CharacterData:
        """Build a CharacterData from a parsed UnicodeData.txt field list."""
        category = fields[2]
        combining_class = int(fields[3])
        bidi_class = fields[4]
        decomposition_str = fields[5]

        numeric_value = None
        numeric_type = ""
        if fields[6]:  # Decimal Digit Value
            numeric_type = "Decimal"
            numeric_value = (int(fields[6]), 1)
        elif fields[7]:  # Digit Value
            numeric_type = "Digit"
            numeric_value = (int(fields[7]), 1)
        elif fields[8]:  # Numeric Value
            numeric_type = "Numeric"
            try:
                parts = fields[8].split('/')
                if len(parts) == 2:
                    numeric_value = (int(parts[0]), int(parts[1]))
                else:
                    numeric_value = (int(parts[0]), 1)
            except:
                pass

        decomposition = ("", [])
        if decomposition_str:
            parts = decomposition_str.split()
            if parts[0].startswith('<'):
                decomp_type = parts[0][1:-1]
                decomp_chars = [int(p, 16) for p in parts[1:]]
            else:
                decomp_type = ""
                decomp_chars = [int(p, 16) for p in parts]
            decomposition = (decomp_type, decomp_chars)

        uppercase = int(fields[12], 16) if fields[12] else None
        lowercase = int(fields[13], 16) if fields[13] else None
        titlecase = int(fields[14], 16) if fields[14] else None

        return CharacterData(
            codepoint=codepoint,
            name=name,
            aliases=[],
            category=category,
            combining_class=combining_class,
            bidi_class=bidi_class,
            bidi_mirrored=fields[9] == "Y",
            bidi_mirror_char=None,
            decomposition=decomposition,
            numeric_value=numeric_value,
            numeric_type=numeric_type,
            uppercase_mapping=uppercase,
            lowercase_mapping=lowercase,
            titlecase_mapping=titlecase,
            block="",
            script="",
            script_extensions=set(),
            age=None,
            east_asian_width="N",
            line_break="XX",
            props=set(),
        )

    def _parse_unicode_data(self):
        """Parse UnicodeData.txt - main character database.

        Most lines are one code point each. Large algorithmically-named
        blocks (CJK ideographs, Hangul syllables, Tangut, ...) instead appear
        as a <Label, First>/<Label, Last> pair bracketing the whole range;
        each code point in between must be expanded individually to get its
        other properties (category, combining class, bidi class, ...), which
        are uniform across the range and taken from the <Label, First> line.
        Names are deliberately NOT computed here -- see _parse_derived_name().
        """
        path = self.data_dir / "UnicodeData.txt"
        if not path.exists():
            raise FileNotFoundError(f"UnicodeData.txt not found in {self.data_dir}")

        pending_range = None  # (first_codepoint, label, fields)

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                fields = line.split(';')
                if len(fields) < 15:
                    continue

                codepoint = int(fields[0], 16)
                raw_name = fields[1] or ""

                range_match = re.match(r'^<(.+), (First|Last)>$', raw_name)
                if range_match:
                    label, boundary = range_match.groups()
                    if boundary == "First":
                        pending_range = (codepoint, label, fields)
                        continue
                    # boundary == "Last"
                    if pending_range is None or pending_range[1] != label:
                        pending_range = None
                        continue
                    first_cp, _, first_fields = pending_range
                    pending_range = None
                    if label.startswith(self._EXPANDABLE_RANGE_PREFIXES):
                        for cp in range(first_cp, codepoint + 1):
                            # Placeholder name -- _parse_derived_name() fills
                            # in the real one right after this method returns.
                            self.characters[cp] = self._build_character(cp, "", first_fields)
                    # Non-expandable ranges (surrogates, private use): no
                    # entries, intentionally -- see _EXPANDABLE_RANGE_PREFIXES.
                    continue

                self.characters[codepoint] = self._build_character(codepoint, raw_name, fields)

    def _parse_blocks(self):
        """Parse Blocks.txt for block assignments."""
        path = self.data_dir / "Blocks.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Format: START..END; NAME
                match = re.match(r'([0-9A-F]+)\.\.([0-9A-F]+);\s*(.+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16)
                    block_name = match.group(3).strip()
                    self.blocks[block_name] = (start, end)

    def _parse_scripts(self):
        """Parse Scripts.txt for script assignments."""
        path = self.data_dir / "Scripts.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Format: START..END ; SCRIPT # comment or SINGLE ; SCRIPT # comment
                match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16) if match.group(2) else start
                    script = match.group(3)

                    if script not in self.scripts:
                        self.scripts[script] = set()

                    for cp in range(start, end + 1):
                        self.scripts[script].add(cp)
                        if cp in self.characters:
                            self.characters[cp].script = script

    def _parse_script_extensions(self):
        """Parse ScriptExtensions.txt for characters with multiple scripts."""
        path = self.data_dir / "ScriptExtensions.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Format: START..END ; SCRIPTS or SINGLE ; SCRIPTS
                match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*([\w\s]+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16) if match.group(2) else start
                    scripts = set(match.group(3).split())

                    for cp in range(start, end + 1):
                        if cp in self.characters:
                            self.characters[cp].script_extensions = scripts

    def _parse_derived_name(self):
        """Parse DerivedName.txt -- Unicode's own complete, pre-computed Name
        property for every code point, individual names and algorithmic-range
        patterns alike. Authoritative source for CharacterData.name; see the
        comment on _EXPANDABLE_RANGE_PREFIXES above for why this replaced
        calling Python's `unicodedata.name()` and hand-maintaining name stems.

        Format (from the file's own header): two fields separated by `;`.
        Field 0 is a single code point or a START..END range. Field 1 is
        either a literal name, or a pattern containing `*` as a placeholder
        for the code point in 4-to-6-digit uppercase hex (e.g.
        "CJK UNIFIED IDEOGRAPH-*" -> "CJK UNIFIED IDEOGRAPH-4E2D" for U+4E2D).

        Unconditionally overwrites .name for every code point it covers --
        it's authoritative, not a fallback -- and creates a minimal
        CharacterData for any code point not already present (shouldn't
        normally happen since DerivedName.txt's coverage is a subset of what
        _parse_unicode_data() already produces, but data files can surprise
        you, so don't assume).
        """
        path = self.data_dir / "DerivedName.txt"
        if not path.exists():
            raise FileNotFoundError(f"DerivedName.txt not found in {self.data_dir}")

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                field0, sep, field1 = line.partition(';')
                if not sep:
                    continue
                field0 = field0.strip()
                name_field = field1.strip()

                if '..' in field0:
                    start_str, end_str = field0.split('..', 1)
                    start, end = int(start_str, 16), int(end_str, 16)
                else:
                    start = end = int(field0, 16)

                is_pattern = '*' in name_field

                for cp in range(start, end + 1):
                    name = name_field.replace('*', f'{cp:04X}') if is_pattern else name_field
                    if cp in self.characters:
                        self.characters[cp].name = name
                    else:
                        self.characters[cp] = CharacterData(
                            codepoint=cp,
                            name=name,
                            aliases=[],
                            category="",
                            combining_class=0,
                            bidi_class="",
                            bidi_mirrored=False,
                            bidi_mirror_char=None,
                            decomposition=("", []),
                            numeric_value=None,
                            numeric_type="",
                            uppercase_mapping=None,
                            lowercase_mapping=None,
                            titlecase_mapping=None,
                            block="",
                            script="",
                            script_extensions=set(),
                            age=None,
                            east_asian_width="N",
                            line_break="XX",
                            props=set(),
                        )

    def _parse_name_aliases(self):
        """Parse NameAliases.txt for alternate names."""
        path = self.data_dir / "NameAliases.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Format: CODEPOINT ; ALIAS ; TYPE
                match = re.match(r'([0-9A-F]+)\s*;\s*([^;]+);\s*(\w+)', line)
                if match:
                    cp = int(match.group(1), 16)
                    alias = match.group(2).strip()
                    alias_type = match.group(3).strip()

                    if cp not in self.characters:
                        self.characters[cp] = CharacterData(
                            codepoint=cp,
                            name="",
                            aliases=[],
                            category="",
                            combining_class=0,
                            bidi_class="",
                            bidi_mirrored=False,
                            bidi_mirror_char=None,
                            decomposition=("", []),
                            numeric_value=None,
                            numeric_type="",
                            uppercase_mapping=None,
                            lowercase_mapping=None,
                            titlecase_mapping=None,
                            block="",
                            script="",
                            script_extensions=set(),
                            age=None,
                            east_asian_width="N",
                            line_break="XX",
                            props=set(),
                        )

                    # Prefer "correction" aliases, which replace a known-wrong
                    # Name outright. Also prefer "control"/"figment" aliases
                    # when the Name property is the literal "<control>"
                    # placeholder UnicodeData.txt uses for C0/C1 control codes,
                    # which have no real Name at all (not an omission on our
                    # part -- it's how the Unicode Standard itself treats them;
                    # NameAliases.txt's own header says these types exist
                    # specifically "to help avoid name collisions" by standing
                    # in for the missing Name). Checked (2026-10-22): all 65
                    # UnicodeData.txt "<control>" entries have a usable alias --
                    # 62 have at least one "control" type, the remaining 3
                    # (never-standardized C1 codes) have only "figment". Where
                    # a code point has more than one alias of the preferred
                    # type (e.g. U+0009 has both "CHARACTER TABULATION" and
                    # "HORIZONTAL TABULATION" as "control" aliases), the first
                    # one in file order wins as the display name and later ones
                    # still land in aliases -- NameAliases.txt doesn't document
                    # an explicit tie-break rule for this, so file order (i.e.
                    # Unicode's own publication order) is a reasonable default,
                    # not a claimed normative rule.
                    if alias_type == "correction" and not self.characters[cp].name:
                        self.characters[cp].name = alias
                    elif alias_type in ("control", "figment") and self.characters[cp].name == "<control>":
                        self.characters[cp].name = alias
                    else:
                        self.characters[cp].aliases.append(alias)

    def _parse_derived_age(self):
        """Parse DerivedAge.txt for character age (Unicode version introduced)."""
        path = self.data_dir / "DerivedAge.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*([\d.]+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16) if match.group(2) else start
                    age = match.group(3)

                    for cp in range(start, end + 1):
                        if cp in self.characters:
                            self.characters[cp].age = age

    def _parse_prop_list(self):
        """Parse PropList.txt for boolean properties."""
        path = self.data_dir / "PropList.txt"
        if not path.exists():
            return

        self._parse_property_file(path)

    def _parse_derived_core_properties(self):
        """Parse DerivedCoreProperties.txt for derived properties."""
        path = self.data_dir / "DerivedCoreProperties.txt"
        if not path.exists():
            return

        self._parse_property_file(path)

    def _parse_property_file(self, path: Path):
        """Generic property file parser."""
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16) if match.group(2) else start
                    prop = match.group(3)

                    for cp in range(start, end + 1):
                        if cp in self.characters:
                            self.characters[cp].props.add(prop)

    def _parse_east_asian_width(self):
        """Parse EastAsianWidth.txt."""
        path = self.data_dir / "EastAsianWidth.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16) if match.group(2) else start
                    width = match.group(3)

                    for cp in range(start, end + 1):
                        if cp in self.characters:
                            self.characters[cp].east_asian_width = width

    def _parse_line_break(self):
        """Parse LineBreak.txt."""
        path = self.data_dir / "LineBreak.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)', line)
                if match:
                    start = int(match.group(1), 16)
                    end = int(match.group(2), 16) if match.group(2) else start
                    lb = match.group(3)

                    for cp in range(start, end + 1):
                        if cp in self.characters:
                            self.characters[cp].line_break = lb

    def _parse_bidi_mirroring(self):
        """Parse BidiMirroring.txt for bidirectional mirroring pairs."""
        path = self.data_dir / "BidiMirroring.txt"
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                match = re.match(r'([0-9A-F]+)\s*;\s*([0-9A-F]+)', line)
                if match:
                    cp = int(match.group(1), 16)
                    mirror_cp = int(match.group(2), 16)

                    if cp in self.characters:
                        self.characters[cp].bidi_mirror_char = mirror_cp

    def _assign_blocks(self):
        """Assign block names to characters based on block ranges."""
        for block_name, (start, end) in self.blocks.items():
            for cp in range(start, end + 1):
                if cp in self.characters:
                    self.characters[cp].block = block_name
