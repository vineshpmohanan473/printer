#!/usr/bin/env python3
"""
ESC/POS format converter for thermal printer data.
Handles binary data with ESC/POS control codes and extracts printable text.
"""

def convert_escpos(bin_data):
    """
    Convert ESC/POS binary data to readable text.
    
    Args:
        bin_data (bytes): Binary data from .bin file
        
    Returns:
        str: Extracted text with control codes removed
    """
    try:
        # Common ESC/POS control codes to remove or handle
        control_codes = {
            # Cursor and line control
            b'\x0A': '\n',  # Line Feed
            b'\x0D': '',     # Carriage Return
            b'\x1B\x64': '\n',  # Print and feed line
            
            # Text formatting
            b'\x1B\x21\x00': '',  # Normal text
            b'\x1B\x21\x01': '',  # Bold on
            b'\x1B\x21\x10': '',  # Double height
            b'\x1B\x21\x20': '',  # Double width
            
            # Alignment
            b'\x1B\x61\x00': '',  # Left align
            b'\x1B\x61\x01': '',  # Center align
            b'\x1B\x61\x02': '',  # Right align
            
            # Cutter commands
            b'\x1D\x56\x41\x00': '\n--- CUT ---\n',  # Full cut
            b'\x1D\x56\x42\x00': '\n--- CUT ---\n',  # Partial cut
        }
        
        # Initialize result
        text = bin_data.decode('latin-1', errors='replace')
        
        # Replace control codes
        for code, replacement in control_codes.items():
            text = text.replace(code.decode('latin-1', errors='ignore'), replacement)
            
        # Remove other control characters (0x00-0x1F, 0x7F-0x9F) except newlines and tabs
        cleaned = []
        for char in text:
            code = ord(char)
            if (32 <= code <= 126) or (code in (9, 10, 13)):
                cleaned.append(char)
            elif code > 127:
                # Try to handle extended ASCII
                cleaned.append(char if 160 <= code <= 255 else '?')
                
        return ''.join(cleaned)
        
    except Exception as e:
        return f"[ERROR] ESC/POS conversion failed: {str(e)}"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 escpos_converter.py <input_file.bin>")
        sys.exit(1)
        
    try:
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
            
        print(convert_escpos(data))
        
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)
