#!/usr/bin/env python3
"""
Generate Apple Dictionary XML from Unicode Character Database.
Usage: python3 -I gen_dict.py [--limit N] [--output FILE]
  --limit N: output only first N entries (for testing)
  --output FILE: write to FILE instead of dist/UnicodeDictionary.xml
"""

import sys
import re
import html
from pathlib import Path
from typing import List, Optional
import unicodedata

# Run with -I flag to use unbundled standard library only
from build.ucd_parse import UCDParser, CharacterData


# Unicode code points that cannot appear literally in XML
XML_UNSAFE_CHARS = {
    # C0 controls (0x00-0x1F) except tab, LF, CR
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,  # no tab (0x09)
    0x0B, 0x0C,  # no LF (0x0A), no CR (0x0D)
    0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F,
    # C1 controls (0x7F-0x9F)
    0x7F,
    0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F,
    0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F,
    # Surrogates and other XML-illegal
    0xFFFE, 0xFFFF,
}


def char_to_display(cp: int) -> str:
    """Convert a code point to displayable form, handling XML-unsafe characters."""
    if cp in XML_UNSAFE_CHARS or 0xD800 <= cp <= 0xDFFF or 0xFDD0 <= cp <= 0xFDEF or cp > 0x10FFFF:
        # Use Control Pictures for C0/C1 controls if available
        if 0x00 <= cp <= 0x1F:
            control_pic = cp + 0x2400
            if control_pic <= 0x243F:
                try:
                    return chr(control_pic)
                except:
                    pass
        elif 0x7F <= cp <= 0x9F:
            # Use symbol representations for DEL and C1
            if cp == 0x7F:
                return "␡"  # DELETE symbol
            control_pic = cp - 0x80 + 0x2440
            try:
                return chr(control_pic)
            except:
                pass
        # Fallback: show as hex code
        return f"&lt;U+{cp:04X}&gt;"

    try:
        return chr(cp)
    except:
        return f"&lt;U+{cp:04X}&gt;"


def safe_xml_char(cp: int) -> str:
    """Convert code point to XML-safe representation."""
    if cp in XML_UNSAFE_CHARS or 0xD800 <= cp <= 0xDFFF or 0xFDD0 <= cp <= 0xFDEF or cp > 0x10FFFF:
        return f"&#{cp};"
    try:
        ch = chr(cp)
        # XML special chars
        ch = ch.replace('&', '&amp;')
        ch = ch.replace('<', '&lt;')
        ch = ch.replace('>', '&gt;')
        ch = ch.replace('"', '&quot;')
        return ch
    except:
        return f"&#{cp};"


def make_xml_id(char_data: CharacterData) -> str:
    """Create a unique, valid XML ID for a character."""
    # ID format: U_XXXX_NAME (with special chars removed)
    if char_data.name:
        safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', char_data.name.lower())
        safe_name = re.sub(r'_+', '_', safe_name)[:20]  # limit length
        return f"U_{char_data.codepoint:04X}_{safe_name}"
    return f"U_{char_data.codepoint:04X}"


def format_category(cat: str) -> str:
    """Format General Category with description."""
    categories = {
        'Lu': 'Letter, Uppercase',
        'Ll': 'Letter, Lowercase',
        'Lt': 'Letter, Titlecase',
        'Lm': 'Letter, Modifier',
        'Lo': 'Letter, Other',
        'Mn': 'Mark, Nonspacing',
        'Mc': 'Mark, Spacing Combining',
        'Me': 'Mark, Enclosing',
        'Nd': 'Number, Decimal Digit',
        'Nl': 'Number, Letter',
        'No': 'Number, Other',
        'Pc': 'Punctuation, Connector',
        'Pd': 'Punctuation, Dash',
        'Ps': 'Punctuation, Open',
        'Pe': 'Punctuation, Close',
        'Pi': 'Punctuation, Initial Quote',
        'Pf': 'Punctuation, Final Quote',
        'Po': 'Punctuation, Other',
        'Sm': 'Symbol, Math',
        'Sc': 'Symbol, Currency',
        'Sk': 'Symbol, Modifier',
        'So': 'Symbol, Other',
        'Zs': 'Separator, Space',
        'Zl': 'Separator, Line',
        'Zp': 'Separator, Paragraph',
        'Cc': 'Other, Control',
        'Cf': 'Other, Format',
        'Cs': 'Other, Surrogate',
        'Co': 'Other, Private Use',
        'Cn': 'Other, Not Assigned',
    }
    return categories.get(cat, cat)


def generate_entry_html(char_data: CharacterData) -> str:
    """Generate HTML content for a dictionary entry."""
    cp = char_data.codepoint
    name = html.escape(char_data.name or "[No Name]")

    # Glyph display
    glyph = char_to_display(cp)

    # Start building content
    html_parts = [
        f'<div class="entry">',
        f'  <div class="glyph" role="img" aria-label="{name}">{html.escape(glyph)}</div>',
        f'  <h1>{name}</h1>',
        f'  <div class="codepoint">U+{cp:04X}</div>',
    ]

    # Main properties table (shown by default)
    props_parts = [
        '<table class="properties">',
        '  <tr><th>Category</th><td>' + format_category(char_data.category) + f' ({char_data.category})</td></tr>',
    ]

    if char_data.script:
        props_parts.append(f'  <tr><th>Script</th><td>{html.escape(char_data.script)}</td></tr>')

    if char_data.block:
        props_parts.append(f'  <tr><th>Block</th><td>{html.escape(char_data.block)}</td></tr>')

    if char_data.age:
        props_parts.append(f'  <tr><th>Age</th><td>Unicode {html.escape(char_data.age)}</td></tr>')

    if char_data.combining_class:
        props_parts.append(f'  <tr><th>Combining Class</th><td>{char_data.combining_class}</td></tr>')

    if char_data.bidi_class:
        props_parts.append(f'  <tr><th>Bidi Class</th><td>{html.escape(char_data.bidi_class)}</td></tr>')

    if char_data.numeric_value:
        num, denom = char_data.numeric_value
        if denom == 1:
            props_parts.append(f'  <tr><th>Numeric Value</th><td>{num}</td></tr>')
        else:
            props_parts.append(f'  <tr><th>Numeric Value</th><td>{num}/{denom}</td></tr>')

    if char_data.east_asian_width and char_data.east_asian_width != 'N':
        width_names = {'F': 'Fullwidth', 'H': 'Halfwidth', 'W': 'Wide', 'Na': 'Narrow', 'A': 'Ambiguous', 'N': 'Neutral'}
        props_parts.append(f'  <tr><th>East Asian Width</th><td>{width_names.get(char_data.east_asian_width, char_data.east_asian_width)}</td></tr>')

    if char_data.line_break and char_data.line_break != 'XX':
        props_parts.append(f'  <tr><th>Line Break</th><td>{html.escape(char_data.line_break)}</td></tr>')

    props_parts.append('</table>')
    html_parts.extend(props_parts)

    # Case mappings (shown by default if present)
    if char_data.uppercase_mapping or char_data.lowercase_mapping or char_data.titlecase_mapping:
        html_parts.append('<h2>Case Mappings</h2>')
        html_parts.append('<table>')
        if char_data.uppercase_mapping:
            upper_char = char_to_display(char_data.uppercase_mapping)
            html_parts.append(f'  <tr><td>Uppercase:</td><td>{html.escape(upper_char)} (U+{char_data.uppercase_mapping:04X})</td></tr>')
        if char_data.lowercase_mapping:
            lower_char = char_to_display(char_data.lowercase_mapping)
            html_parts.append(f'  <tr><td>Lowercase:</td><td>{html.escape(lower_char)} (U+{char_data.lowercase_mapping:04X})</td></tr>')
        if char_data.titlecase_mapping:
            title_char = char_to_display(char_data.titlecase_mapping)
            html_parts.append(f'  <tr><td>Titlecase:</td><td>{html.escape(title_char)} (U+{char_data.titlecase_mapping:04X})</td></tr>')
        html_parts.append('</table>')

    # Decomposition (hidden by default with d:priority="2")
    if char_data.decomposition[1]:
        decomp_type, decomp_chars = char_data.decomposition
        html_parts.append(f'<div d:priority="2"><h3>Decomposition</h3>')
        if decomp_type:
            html_parts.append(f'<p>Type: {html.escape(decomp_type)}</p>')
        html_parts.append('<p>')
        for dcp in decomp_chars:
            dchar = char_to_display(dcp)
            dname = "[No Name]"
            try:
                dname = unicodedata.name(chr(dcp))
            except:
                pass
            html_parts.append(f'{html.escape(dchar)} (U+{dcp:04X} {html.escape(dname)})<br/>')
        html_parts.append('</p>')
        html_parts.append('</div>')

    # Additional aliases (hidden)
    if char_data.aliases:
        html_parts.append(f'<div d:priority="2"><h3>Aliases</h3>')
        html_parts.append('<ul>')
        for alias in char_data.aliases:
            html_parts.append(f'<li>{html.escape(alias)}</li>')
        html_parts.append('</ul></div>')

    # Boolean properties (hidden)
    if char_data.props:
        html_parts.append(f'<div d:priority="2"><h3>Properties</h3>')
        html_parts.append('<ul>')
        for prop in sorted(char_data.props):
            html_parts.append(f'<li>{html.escape(prop)}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


def generate_entry_xml(char_data: CharacterData) -> str:
    """Generate a complete d:entry XML element for one character."""
    cp = char_data.codepoint
    entry_id = make_xml_id(char_data)
    name = html.escape(char_data.name or f"U+{cp:04X}")

    # Build indexes
    indexes = []

    # Index 1: the character itself (if safe to display)
    if cp not in XML_UNSAFE_CHARS and not (0xD800 <= cp <= 0xDFFF):
        try:
            char = chr(cp)
            # Escape for XML
            char_escaped = char.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            indexes.append(f'    <d:index d:value="{char_escaped}" d:title="{name}"/>')
        except:
            pass

    # Index 2: U+XXXX format
    hex_index = f"U+{cp:04X}"
    indexes.append(f'    <d:index d:value="{hex_index}" d:title="{name}"/>')

    # Index 3: XXXX format (without U+)
    hex_no_prefix = f"{cp:04X}"
    indexes.append(f'    <d:index d:value="{hex_no_prefix}" d:title="{name}"/>')

    # Index 4: Full name
    if char_data.name:
        name_escaped = html.escape(char_data.name).replace('"', '&quot;')
        indexes.append(f'    <d:index d:value="{name_escaped}" d:title="{name}"/>')

        # Index 5: Lowercase name (for case-insensitive matching)
        name_lower = char_data.name.lower()
        if name_lower != char_data.name:
            name_lower_escaped = html.escape(name_lower).replace('"', '&quot;')
            indexes.append(f'    <d:index d:value="{name_lower_escaped}" d:title="{name}"/>')

    # Index 6: Aliases
    for alias in char_data.aliases[:3]:  # limit to first 3 to avoid bloat
        alias_escaped = html.escape(alias).replace('"', '&quot;')
        indexes.append(f'    <d:index d:value="{alias_escaped}" d:title="{name}"/>')

    # Generate content
    content = generate_entry_html(char_data)
    content_escaped = html.escape(content)

    entry_parts = [
        f'  <d:entry id="{entry_id}" d:title="{html.escape(name)[:100]}">',
    ]
    entry_parts.extend(indexes)
    entry_parts.append('    <div>')
    entry_parts.append(content)
    entry_parts.append('    </div>')
    entry_parts.append('  </d:entry>')

    return '\n'.join(entry_parts)


def generate_dictionary(characters: dict, limit: Optional[int] = None, output_file: str = None) -> str:
    """Generate complete dictionary XML."""

    if output_file is None:
        output_file = 'dist/UnicodeDictionary.xml'

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter assigned characters
    assigned = sorted(
        [cp for cp, ch in characters.items() if ch.name or ch.category],
        key=lambda x: x
    )

    if limit:
        assigned = assigned[:limit]

    print(f"Generating {len(assigned)} entries...")

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<d:dictionary xmlns="http://www.w3.org/1999/xhtml"',
        '  xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">',
        '',
    ]

    # Front matter / about page
    xml_lines.extend([
        '  <d:entry id="About" d:title="About Unicode Dictionary">',
        '    <d:index d:value="about" d:title="About"/>',
        '    <div>',
        '      <h1>Unicode Character Database Dictionary</h1>',
        '      <p>Comprehensive reference for all Unicode 17.0 characters.</p>',
        '      <h2>Features</h2>',
        '      <ul>',
        '        <li>Official character names</li>',
        '        <li>Code points (U+XXXX and numeric)</li>',
        '        <li>General category, script, block</li>',
        '        <li>Age (Unicode version introduced)</li>',
        '        <li>Combining class, bidi properties</li>',
        '        <li>Decomposition, case mappings</li>',
        '        <li>Numeric values, East Asian width</li>',
        '        <li>Boolean properties (Alphabetic, Emoji, Math, etc.)</li>',
        '      </ul>',
        '      <h2>Usage</h2>',
        '      <p>Select any character and use Look Up (Ctrl+Cmd+D) to search this dictionary.</p>',
        '      <h2>Property Legend</h2>',
        '      <dl>',
        '        <dt>Category</dt><dd>General character classification</dd>',
        '        <dt>Script</dt><dd>Writing system (Latin, Greek, Han, etc.)</dd>',
        '        <dt>Block</dt><dd>Unicode block assignment</dd>',
        '        <dt>Age</dt><dd>Unicode version when character was introduced</dd>',
        '        <dt>Combining Class</dt><dd>Canonical combining class (0 if not combining)</dd>',
        '        <dt>Bidi Class</dt><dd>Bidirectional text properties</dd>',
        '        <dt>Numeric Value</dt><dd>Numeric value if character represents a number</dd>',
        '        <dt>East Asian Width</dt><dd>Display width in East Asian context</dd>',
        '      </dl>',
        '      <p><small>Data from Unicode Standard 17.0. License: <a href="https://www.unicode.org/license.html">Unicode License</a></small></p>',
        '    </div>',
        '  </d:entry>',
        '',
    ])

    # Character entries
    for i, cp in enumerate(assigned):
        if (i + 1) % 10000 == 0:
            print(f"  {i + 1}/{len(assigned)}...")

        char_data = characters[cp]
        entry_xml = generate_entry_xml(char_data)
        xml_lines.append(entry_xml)
        xml_lines.append('')

    # Close dictionary
    xml_lines.extend([
        '</d:dictionary>',
    ])

    xml_content = '\n'.join(xml_lines)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f"✓ Written {output_file}")
    print(f"  Size: {output_path.stat().st_size / (1024*1024):.1f} MB")

    return str(output_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate Unicode Dictionary XML')
    parser.add_argument('--limit', type=int, help='Limit to first N entries')
    parser.add_argument('--output', default='dist/UnicodeDictionary.xml', help='Output file')
    parser.add_argument('--data-dir', default='data', help='Data directory containing UCD files')

    args = parser.parse_args()

    # Parse UCD
    parser_obj = UCDParser(args.data_dir)
    characters = parser_obj.parse_all()

    print(f"Total characters parsed: {len(characters)}")

    # Generate dictionary
    generate_dictionary(characters, limit=args.limit, output_file=args.output)


if __name__ == '__main__':
    main()
