############################################################################################
############################################################################################
############################################################################################
# TEXT MANIPULATORS
############################################################################################
############################################################################################
############################################################################################


import string


############################################################################################


def strip_punctuation(text: str) -> str:

    chars = set()

    # ASCII punctuation and space
    chars.update(string.punctuation)   # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    chars.add(' ')                     # normal space

    # Common special spaces
    chars.add('\u00A0')  # NO-BREAK SPACE
    chars.add('\u3000')  # IDEOGRAPHIC SPACE (full-width space)

    # Newlines and tabs:
    chars.add('\n')
    chars.add('\r')     # Windows-style line endings
    chars.add('\t')     # tabs

    # General Punctuation block
    chars.update(chr(cp) for cp in range(0x2000, 0x206F + 1))

    # CJK Symbols and Punctuation block: U+3000–U+303F
    chars.update(chr(cp) for cp in range(0x3000, 0x303F + 1))

    # Halfwidth and Fullwidth Forms: U+FF01–U+FF5E (fullwidth ASCII & punctuation)
    chars.update(chr(cp) for cp in range(0xFF01, 0xFF5E + 1))

    return text.translate(str.maketrans('', '', ''.join(chars)))
