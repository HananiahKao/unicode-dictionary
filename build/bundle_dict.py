#!/usr/bin/env python3
"""
Create an Apple Dictionary bundle from XML source.

This is a fallback when Apple's Dictionary Development Kit is not available.
For production use, the official Kit should be used, which compiles the dictionary
into optimized binary format (Body.data and KeyText.index).

This script creates a basic bundle structure that can be used for testing
or as a foundation for further processing.
"""

import os
import sys
import shutil
import gzip
from pathlib import Path
from plistlib import dump as plist_dump

def create_bundle(
    bundle_name: str,
    xml_source: str,
    css_source: str,
    info_plist: str,
    output_dir: str = ".",
) -> str:
    """Create a dictionary bundle from source files."""

    # Create bundle directory structure
    bundle_path = Path(output_dir) / f"{bundle_name}.dictionary"
    contents = bundle_path / "Contents"
    resources = contents / "Resources"

    print(f"Creating bundle: {bundle_path}")

    # Remove existing bundle
    if bundle_path.exists():
        shutil.rmtree(bundle_path)
        print(f"  Removed existing bundle")

    # Create directories
    resources.mkdir(parents=True, exist_ok=True)
    print(f"  Created directory structure")

    # Copy Info.plist
    if os.path.exists(info_plist):
        shutil.copy2(info_plist, contents / "Info.plist")
        print(f"  ✓ Copied Info.plist")

    # Copy CSS
    if os.path.exists(css_source):
        shutil.copy2(css_source, resources / "Dictionary.css")
        print(f"  ✓ Copied CSS stylesheet")

    # For now, copy XML directly as a reference
    # In production, this would be compiled into Body.data and KeyText.index
    if os.path.exists(xml_source):
        # Create a gzipped copy for reference
        xml_path = Path(xml_source)
        with open(xml_path, 'rb') as f_in:
            with gzip.open(resources / "Dictionary.xml.gz", 'wb') as f_out:
                f_out.writelines(f_in)
        print(f"  ✓ Compressed and copied XML source ({xml_path.stat().st_size / (1024*1024):.1f} MB)")

    # Create a README in the bundle explaining the situation
    readme = resources / "README.txt"
    readme.write_text("""\
Unicode Dictionary Bundle (Partial)

This bundle was created without Apple's Dictionary Development Kit.

For full functionality, the dictionary source XML must be compiled using Apple's
Dictionary Development Kit, which creates optimized binary files:
- Body.data (compiled dictionary content)
- KeyText.index (full-text search index)

Without these compiled files, the dictionary will not appear in Dictionary.app.

To complete the build:
1. Download Apple's "Additional Tools for Xcode" from developer.apple.com
2. Install the Dictionary Development Kit
3. Run: build_dict.sh UnicodeDictionary dist/UnicodeDictionary.xml src/UnicodeDictionary.css src/Info.plist
4. Copy the resulting .dictionary bundle to ~/Library/Dictionaries/

The uncompiled XML source is provided as Dictionary.xml.gz for reference.
""")
    print(f"  ✓ Created README")

    print(f"\n⚠ Note: This bundle is incomplete without the Dictionary Development Kit.")
    print(f"The dictionary will not appear in Dictionary.app until compiled with the Kit's tools.")
    print(f"\nBundle location: {bundle_path}")

    return str(bundle_path)


def create_mock_bundle(
    bundle_name: str,
    info_plist: str,
    output_dir: str = ".",
) -> str:
    """Create a minimal mock bundle structure for testing."""

    bundle_path = Path(output_dir) / f"{bundle_name}.dictionary"
    contents = bundle_path / "Contents"
    resources = contents / "Resources"

    resources.mkdir(parents=True, exist_ok=True)

    # Copy Info.plist
    if os.path.exists(info_plist):
        shutil.copy2(info_plist, contents / "Info.plist")

    # Create empty/minimal required files
    # These would normally be compiled by the Kit
    (resources / "Body.data").write_bytes(b"")
    (resources / "KeyText.index").write_bytes(b"")

    return str(bundle_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Create Apple Dictionary bundle (without Kit compilation)"
    )
    parser.add_argument("bundle_name", help="Bundle name (e.g., UnicodeDictionary)")
    parser.add_argument("xml_source", help="Path to source XML file")
    parser.add_argument("css_source", help="Path to CSS stylesheet")
    parser.add_argument("info_plist", help="Path to Info.plist")
    parser.add_argument("--output", "-o", default=".", help="Output directory")

    args = parser.parse_args()

    bundle = create_bundle(
        args.bundle_name,
        args.xml_source,
        args.css_source,
        args.info_plist,
        args.output,
    )

    print(f"\n✓ Bundle created at: {bundle}")
    print(f"\nTo use this dictionary:")
    print(f"1. Install the Dictionary Development Kit from Apple")
    print(f"2. Run: build_dict.sh {args.bundle_name} {args.xml_source} {args.css_source} {args.info_plist}")
    print(f"3. Copy the result to ~/Library/Dictionaries/")


if __name__ == "__main__":
    main()
