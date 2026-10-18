#!/usr/bin/env python3
"""
Wrapper script to build dictionary from project root.
Handles imports and working directory properly.
"""

import sys
import os

# Get the build directory
build_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(build_dir)

# Add build directory to path
sys.path.insert(0, build_dir)

# Change to project directory
os.chdir(project_dir)

# Import after path setup
from gen_dict import main

if __name__ == '__main__':
    main()
