#!/usr/bin/env python3
"""
Raw Text Converter for printer data.
Handles simple ASCII/UTF-8 text files by removing non-printable characters.
"""
import re
from pathlib import Path

def convert_rawtext(input_path):
    """
    Convert raw text binary data to clean, readable text.
    
    Args:
        input_path (str): Path to the input .bin file
        
    Returns:
        str: Cleaned text content
    """
    try:
        # Try UTF-8 first, fall back to Latin-1 if that fails
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Remove non-printable characters except newlines and tabs
        # This keeps standard ASCII 32-126, plus newlines and tabs
        cleaned = []
        for line in content.splitlines():
            # Remove non-printable chars from each line
            clean_line = ''.join(char for char in line if 32 <= ord(char) <= 126 or char in '\t\n\r')
            if clean_line.strip():  # Only keep non-empty lines
                cleaned.append(clean_line)
        
        return '\n'.join(cleaned) if cleaned else "No readable text content found."
        
    except Exception as e:
        return f"Error processing raw text data: {str(e)}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python rawtext_converter.py <input_file.bin>")
        sys.exit(1)
    
    result = convert_rawtext(sys.argv[1])
    print(result)
