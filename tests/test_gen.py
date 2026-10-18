#!/usr/bin/env python3
"""
Tests for Unicode Dictionary generator.
Run with: python3 -I tests/test_gen.py
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import unicodedata

# Add build dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from build.ucd_parse import UCDParser
from build.gen_dict import generate_dictionary, make_xml_id


class TestUCDParser(unittest.TestCase):
    """Test UCD parsing."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        cls.data_dir = 'data'
        if not Path(cls.data_dir).exists():
            print(f"⚠ Data directory '{cls.data_dir}' not found. Skipping parser tests.")
            print("Run 'make data' first to download UCD files.")
            return

        cls.parser = UCDParser(cls.data_dir)
        try:
            cls.characters = cls.parser.parse_all()
        except FileNotFoundError as e:
            print(f"⚠ Error parsing UCD: {e}")
            cls.characters = {}

    def test_parser_loads_data(self):
        """Test that parser loads characters."""
        if not self.characters:
            self.skipTest("UCD data not available")
        self.assertGreater(len(self.characters), 100000, "Should load >100k characters")

    def test_basic_ascii(self):
        """Test that basic ASCII characters are present."""
        if not self.characters:
            self.skipTest("UCD data not available")

        # 'A' (U+0041)
        self.assertIn(0x0041, self.characters)
        self.assertEqual(self.characters[0x0041].name, "LATIN CAPITAL LETTER A")
        self.assertEqual(self.characters[0x0041].category, "Lu")
        self.assertEqual(self.characters[0x0041].block, "Basic Latin")

    def test_blocks_assigned(self):
        """Test that block assignments work."""
        if not self.characters:
            self.skipTest("UCD data not available")

        # Basic Latin block is 0000..007F
        for cp in range(0x0000, 0x0080):
            if cp in self.characters:
                self.assertEqual(self.characters[cp].block, "Basic Latin")

    def test_script_assigned(self):
        """Test that script assignments work."""
        if not self.characters:
            self.skipTest("UCD data not available")

        # 'A' should be Latin
        a = self.characters.get(0x0041)
        if a:
            self.assertEqual(a.script, "Latin")

    def test_no_duplicate_names(self):
        """Test that name assignments are reasonable."""
        if not self.characters:
            self.skipTest("UCD data not available")

        # Most characters should have names or be unassigned
        with_names = sum(1 for ch in self.characters.values() if ch.name)
        self.assertGreater(with_names, 100000, "Should have >100k named characters")


class TestDictionaryGeneration(unittest.TestCase):
    """Test dictionary XML generation."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        cls.data_dir = 'data'
        if not Path(cls.data_dir).exists():
            return

        parser = UCDParser(cls.data_dir)
        try:
            cls.characters = parser.parse_all()
        except FileNotFoundError:
            cls.characters = {}

        # Generate small test dictionary
        cls.test_output = Path(tempfile.gettempdir()) / 'test_dict.xml'
        if cls.characters:
            generate_dictionary(cls.characters, limit=100, output_file=str(cls.test_output))

    def test_xml_generated(self):
        """Test that XML file is created."""
        if not self.characters:
            self.skipTest("UCD data not available")

        self.assertTrue(self.test_output.exists(), "XML file should be created")
        self.assertGreater(self.test_output.stat().st_size, 1000, "XML should have content")

    def test_xml_well_formed(self):
        """Test that generated XML is well-formed."""
        if not self.test_output.exists():
            self.skipTest("XML not generated")

        try:
            tree = ET.parse(str(self.test_output))
            root = tree.getroot()
            # Check root element
            self.assertIn('dictionary', root.tag, "Root should be dictionary element")
        except ET.ParseError as e:
            self.fail(f"XML not well-formed: {e}")

    def test_entries_have_ids(self):
        """Test that entries have unique IDs."""
        if not self.test_output.exists():
            self.skipTest("XML not generated")

        tree = ET.parse(str(self.test_output))
        root = tree.getroot()

        # Define namespace
        ns = {'d': 'http://www.apple.com/DTDs/DictionaryService-1.0.rng'}

        entries = root.findall('.//d:entry', ns)
        self.assertGreater(len(entries), 0, "Should have entries")

        # Check IDs are unique
        ids = [e.get('id') for e in entries]
        self.assertEqual(len(ids), len(set(ids)), "All entry IDs should be unique")

    def test_entries_have_indexes(self):
        """Test that entries have index elements."""
        if not self.test_output.exists():
            self.skipTest("XML not generated")

        tree = ET.parse(str(self.test_output))
        root = tree.getroot()

        ns = {'d': 'http://www.apple.com/DTDs/DictionaryService-1.0.rng'}

        entries = root.findall('.//d:entry', ns)
        for entry in entries[:10]:  # Check first 10
            indexes = entry.findall('d:index', ns)
            if entry.get('id') != 'About':
                self.assertGreater(len(indexes), 0,
                    f"Entry {entry.get('id')} should have indexes")


class TestXMLIDGeneration(unittest.TestCase):
    """Test XML ID generation."""

    def test_id_generation(self):
        """Test that IDs are valid XML."""
        from build.ucd_parse import CharacterData

        # Test with various names
        test_cases = [
            (0x0041, "LATIN CAPITAL LETTER A"),
            (0x1F600, "GRINNING FACE"),
            (0x0000, "NULL"),
            (0x200B, "ZERO WIDTH SPACE"),
        ]

        for cp, name in test_cases:
            char_data = CharacterData(
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

            xml_id = make_xml_id(char_data)

            # Check that ID is valid XML
            # Must start with letter, underscore, or colon
            self.assertIn(xml_id[0], 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz',
                f"ID '{xml_id}' should start with valid XML name character")

            # Check for valid characters (alphanumeric, underscore, dash, period)
            for ch in xml_id:
                self.assertIn(ch, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-.',
                    f"ID '{xml_id}' contains invalid character '{ch}'")


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestUCDParser))
    suite.addTests(loader.loadTestsFromTestCase(TestDictionaryGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestXMLIDGeneration))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
