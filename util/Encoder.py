import os
import unicodedata
import re

class Encoder:
    """Helper class to handle encoding issues."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text from problematic Unicode characters."""
        if not text:
            return ""
        
        # Method 1: Remove surrogates and invalid characters
        try:
            # Encode to UTF-8 and decode back, replacing errors
            cleaned = text.encode('utf-8', errors='replace').decode('utf-8')
            
            # Remove surrogate characters specifically
            cleaned = re.sub(r'[\uD800-\uDFFF]', '', cleaned)
            
            # Normalize Unicode (NFD = decomposed, NFC = composed)
            cleaned = unicodedata.normalize('NFC', cleaned)
            
            # Remove or replace other problematic characters
            cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
            
            return cleaned
            
        except UnicodeError:
            # Fallback: more aggressive cleaning
            return Encoder.aggressive_clean(text)
    
    @staticmethod
    def aggressive_clean(text: str) -> str:
        """More aggressive text cleaning as fallback."""
        try:
            # Keep only printable ASCII + common accented characters
            cleaned = ''.join(char for char in text if ord(char) < 65536 and char.isprintable() or char in ' \n\t')
            
            # Replace common problematic characters
            replacements = {
                ''': "'",  # Smart quotes
                ''': "'",
                '"': '"',
                '"': '"',
                '–': '-',  # En dash
                '—': '-',  # Em dash
                '…': '...',  # Ellipsis
                'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
                'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
                'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
                'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
                'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
                'ç': 'c', 'ñ': 'n'
            }
            
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            
            return cleaned
            
        except Exception:
            # Ultimate fallback: keep only ASCII
            return ''.join(char for char in text if ord(char) < 128)
    
    @staticmethod
    def safe_encode_decode(text: str) -> str:
        """Safely encode and decode text."""
        try:
            # Try different encoding strategies
            strategies = [
                ('utf-8', 'strict'),
                ('utf-8', 'replace'),
                ('latin-1', 'replace'),
                ('ascii', 'replace')
            ]
            
            for encoding, errors in strategies:
                try:
                    return text.encode(encoding, errors=errors).decode(encoding)
                except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError):
                    continue
            
            # Final fallback
            return Encoder.aggressive_clean(text)
            
        except Exception:
            return ""