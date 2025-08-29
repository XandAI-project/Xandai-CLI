#!/usr/bin/env python3
"""
Test script for path duplication fixes
"""

import sys
sys.path.insert(0, '.')

from xandai.shell_executor import ShellExecutor
from pathlib import Path

def test_current_directory_cleaning():
    """Test that get_current_directory applies deduplication"""
    print("🧪 Testing current directory cleaning...")
    
    shell = ShellExecutor()
    
    # Manually set a duplicated path to test cleaning
    duplicated_path = Path("C:/Users/keyce/XandNet Project/XandAI-CLI/examples/XandAI-CLI/examples/public")
    shell.current_dir = duplicated_path
    
    print(f"Before: {duplicated_path}")
    
    # Get current directory - should apply cleaning
    clean_current = shell.get_current_directory()
    
    print(f"After:  {clean_current}")
    print(f"Cleaned: {duplicated_path != Path(clean_current)}")

def test_path_resolution():
    """Test path resolution with cleaning"""
    print("\n🧪 Testing path resolution...")
    
    # Simulate the CLI path resolution
    from xandai.cli import XandAICLI
    
    cli = XandAICLI()
    
    # Test with a problematic current directory
    current_dir = Path("C:/Users/keyce/XandNet Project/XandAI-CLI/examples/examples")
    
    # Resolve a file path
    filename = "app.js"
    resolved = cli._resolve_file_path(filename, current_dir)
    
    print(f"Current dir: {current_dir}")
    print(f"Filename:    {filename}")
    print(f"Resolved:    {resolved}")
    
    # Check if the path contains duplications
    path_parts = str(resolved).replace('\\', '/').split('/')
    has_consecutive_duplicates = any(path_parts[i] == path_parts[i+1] for i in range(len(path_parts)-1) if path_parts[i])
    
    print(f"Has duplicates: {has_consecutive_duplicates}")

if __name__ == "__main__":
    test_current_directory_cleaning()
    test_path_resolution()
    print("\n🎉 Path cleaning tests completed!")
