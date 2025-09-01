#!/usr/bin/env python3
"""
PostScript Converter for printer data.
Extracts text from PostScript (.bin) files by looking for text between parentheses
and other common PostScript text patterns.
"""
import re
from pathlib import Path

def convert_postscript(input_path):
    """
    Convert PostScript binary data to readable text.
    
    Args:
        input_path (str): Path to the input .bin file
        
    Returns:
        str: Extracted text content
    """
    try:
        # Read the binary file with Latin-1 encoding to preserve all byte values
        with open(input_path, 'rb') as f:
            content = f.read().decode('latin-1')
        
        # Extract text between parentheses (common in PostScript)
        text_pieces = re.findall(r'\((?:\\.|[^\\()])*\)', content)
        
        # Clean up the extracted text
        cleaned_text = []
        for text in text_pieces:
            # Remove surrounding parentheses and unescape characters
            text = text[1:-1]  # Remove parentheses
            text = text.replace('\\', '')  # Remove escape characters
            if text.strip():  # Only add non-empty strings
                cleaned_text.append(text)
        
        # Also look for common PostScript text commands
        ps_text = re.findall(r'\bT[adf]?\s*[\(]([^)]+)[\)]', content)
        cleaned_text.extend(ps_text)
        
        # Join all text pieces with newlines
        return '\n'.join(cleaned_text) if cleaned_text else "No text content found in PostScript data."
        
    except Exception as e:
        return f"Error processing PostScript data: {str(e)}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python postscript_converter.py <input_file.bin>")
        sys.exit(1)
    
    result = convert_postscript(sys.argv[1])
    print(result)
