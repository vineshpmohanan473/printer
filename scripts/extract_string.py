#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def detect_format(file_path):
    """
    Detect the format of printer data file.
    
    Args:
        file_path (str): Path to the input file
        
    Returns:
        str: Detected format ('escpos', 'postscript', or 'rawtext')
    """
    try:
        with open(file_path, 'rb') as f:
            # Read first 1024 bytes for analysis
            header = f.read(1024)
            
            # Check for PostScript (starts with %!PS)
            if header.startswith(b'%!PS') or b'%!PS' in header:
                return 'postscript'
                
            # Check for ESC/POS commands (ESC @, ESC !, etc.)
            if b'\x1b' in header:  # ESC character
                return 'escpos'
                
            # Default to raw text if no specific format detected
            return 'rawtext'
            
    except Exception as e:
        print(f"[ERROR] Format detection failed: {e}")
        return 'rawtext'  # Default to raw text on error

def convert_escpos(file_path):
    """Convert ESC/POS binary data to readable text."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('latin-1')
        
        # Common ESC/POS control codes to remove
        escpos_codes = [
            '\x1b@',    # Initialize printer
            '\x1b!',    # Select print mode
            '\x1b-',    # Underline mode
            '\x1bE',    # Bold on
            '\x1bF',    # Bold off
            '\x1bM',    # Font A
            '\x1bP',    # 10 cpi font
            '\x1b!\x00', # Normal text
        ]
        
        cleaned = content
        for code in escpos_codes:
            cleaned = cleaned.replace(code, '')
        
        # Remove other non-printable characters except newlines and tabs
        cleaned = re.sub(r'[^\x20-\x7E\n\t]', '', cleaned)
        return cleaned.strip()
        
    except Exception as e:
        return f"Error converting ESC/POS: {str(e)}"

def convert_postscript(file_path):
    """Convert PostScript data to readable text."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('latin-1', errors='replace')
        
        # Look for text in common PostScript patterns
        patterns = [
            # Text in parentheses after text operators
            (r'\bT[FJ]\s*\(([^)]+)\)', 1),
            # Text before text operators
            (r'\b\([^)]+\)\s*T[FJ]', 1),
            # Text in text blocks
            (r'\b(?:T[FJ]|BT|ET)\b.*?\(([^)]+)\)', 1),
            # Another variation of text blocks
            (r'\b(?:T[FJ]|BT|ET)\b[^()]*\(([^)]+)\)', 1),
            # Text in show operators
            (r'\b\([^)]+\)\s+show\b', 1),
            # Text in string literals
            (r'\([^\\()]*(?:\\.[^\\()]*)*\)', 0),
        ]
        
        # Also try to extract any text between parentheses as a last resort
        all_text = []
        in_text = False
        current_text = []
        
        for char in content:
            if char == '(' and not in_text:
                in_text = True
                current_text = []
            elif char == ')' and in_text:
                in_text = False
                if current_text:
                    text = ''.join(current_text).strip()
                    if len(text) > 3:  # Only keep meaningful text
                        all_text.append(text)
            elif in_text:
                current_text.append(char)
        
        # Now try the regex patterns
        for pattern, group in patterns:
            try:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        text = match[group] if group < len(match) else ''
                    else:
                        text = match
                    
                    # Clean up the text
                    text = text.strip()
                    if text and len(text) > 3:  # Only keep meaningful text
                        # Remove escape sequences
                        text = re.sub(r'\\([()\\])', r'\1', text)
                        all_text.append(text)
            except Exception as e:
                print(f"[WARN] Error processing pattern {pattern}: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_text = []
        for text in all_text:
            if text not in seen:
                seen.add(text)
                unique_text.append(text)
        
        return '\n'.join(unique_text) if unique_text else "No text content found in PostScript data."
        
    except Exception as e:
        return f"Error converting PostScript: {str(e)}"

def convert_rawtext(file_path):
    """Convert raw text data to clean text."""
    try:
        # Try UTF-8 first, fall back to Latin-1 if that fails
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Remove non-printable characters except newlines and tabs
        cleaned = re.sub(r'[^\x20-\x7E\n\t]', '', content)
        return cleaned.strip()
        
    except Exception as e:
        return f"Error converting raw text: {str(e)}"

def process_file(file_path):
    """
    Process the input file based on its detected format.
    Uses a switch-case like pattern to call the appropriate converter.
    """
    print(f"\n[INFO] Processing file: {file_path}")
    
    # Detect the file format
    file_format = detect_format(file_path)
    print(f"[INFO] Detected format: {file_format}")
    
    # Switch-case equivalent using a dictionary
    converters = {
        'escpos': convert_escpos,
        'postscript': convert_postscript,
        'rawtext': convert_rawtext
    }
    
    # Get the appropriate converter function and call it
    converter = converters.get(file_format, convert_rawtext)  # Default to rawtext if format not found
    print(f"[INFO] Using converter: {converter.__name__}")
    
    try:
        result = converter(file_path)
        print(f"[INFO] Conversion completed successfully")
        return result
    except Exception as e:
        error_msg = f"[ERROR] Conversion failed: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 extract_string.py <path_to_bin_file>")
        sys.exit(1)
        
    bin_file = sys.argv[1]
    if not Path(bin_file).exists():
        print(f"[ERROR] File does not exist: {bin_file}")
        sys.exit(1)
    
    print("=" * 60)
    print(f"[INFO] Starting conversion of: {bin_file}")
    print("=" * 60)
    
    result = process_file(bin_file)
    
    print("\n" + "=" * 60)
    print("CONVERSION RESULT:")
    print("-" * 60)
    print(result)
    print("=" * 60)
