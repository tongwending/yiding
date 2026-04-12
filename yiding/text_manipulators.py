# ------------------------------------------------------------------------------------------
# text_manipulators
# ------------------------------------------------------------------------------------------

import string
import re

# ------------------------------------------------------------------------------------------

SEGMENTOR = "<break>"

ENDERS = "。？！.!?)*" # ** is coded for titles and headers.
CLOSERS = '"”’」』】）》）〉》〕］｝」』｣)}›»*'
punctuation = re.compile(rf"[{re.escape(ENDERS)}][{re.escape(CLOSERS)}]*") # [..]* is regex.
punctuation_end = re.compile(rf"[{re.escape(ENDERS)}][{re.escape(CLOSERS)}]*$")

INVALID_CHARACTERS = r'[<>:"/\\|?*\x00-\x1F]'

_PARENTHESIS = re.compile(r"\(([^()]*)\)", flags = re.S) # last part is for multiple lines

CHARACTER_PLACEHOLDERS = {'⬤', '■', '◆', '▲'} # plalceholders of unknonw characters

non_characters = set()
# ASCII punctuation and space
non_characters.update(string.punctuation)    # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
non_characters.add(' ')                      # normal space
non_characters.update(string.digits)         # numbers
non_characters.update(string.ascii_letters)  # Latin letters (A–Z, a–z)
# Common special spaces
non_characters.add('\u00A0')  # NO-BREAK SPACE
non_characters.add('\u3000')  # IDEOGRAPHIC SPACE (full-width space)
# Newlines and tabs:
non_characters.add('\n')
non_characters.add('\r')     # Windows-style line endings
non_characters.add('\t')     # tabs
# General Punctuation block
non_characters.update(chr(cp) for cp in range(0x2000, 0x206F + 1))
# CJK Symbols and Punctuation block: U+3000–U+303F
non_characters.update(chr(cp) for cp in range(0x3000, 0x303F + 1))
# Halfwidth and Fullwidth Forms: U+FF01–U+FF5E (fullwidth ASCII & punctuation)
non_characters.update(chr(cp) for cp in range(0xFF01, 0xFF5E + 1))
# Geometric shapes (icludes bulletpoints)
non_characters.update(chr(cp) for cp in range(0x25A0, 0x25FF + 1))
# Misc. symbols and arrows
non_characters.update(chr(cp) for cp in range(0x2B00, 0x2BFF + 1))
# Combine to table 
_NON_CHARACTERS_SET = set(non_characters)

# Remove character placeholders
non_characters.difference_update(CHARACTER_PLACEHOLDERS)
# Remove the character parenthesis
non_characters.difference_update({'(', ')'})
# Combine in a table for stipping punctuation
_STRIP_TABLE = str.maketrans('', '', ''.join(non_characters))

# ------------------------------------------------------------------------------------------

def strip_punctuation(text: str) -> str:

    return text.translate(_STRIP_TABLE)

# ------------------------------------------------------------------------------------------

def strip_invalid_characters(text):

    return re.sub(INVALID_CHARACTERS, '', text)

# ------------------------------------------------------------------------------------------

def segmentate(text):

    punctuated_segments = []
    leftover = ""

    no_segmentor_left = False    
    while no_segmentor_left == False:
        
        next_segmentor = re.search(SEGMENTOR, text)

        if not next_segmentor:
            no_segmentor_left = True
        else:
            punctuated_segments.append(text[:next_segmentor.start()])
            text = text[next_segmentor.end():]

    if text.strip():
        leftover = text
    elif len(punctuated_segments) > 0:
        leftover = punctuated_segments.pop()

    return punctuated_segments, leftover
        
# ------------------------------------------------------------------------------------------

def chop_from_working_segment(chop, working_segment, labels):

    # labels[n] = [page: str, first_line: int, last_line: int]

    LABEL_ERROR = "Error: Page'n'lines labels misaligned."

    while working_segment.startswith('\n'):
        if not labels:
            raise ValueError(LABEL_ERROR)
        else:         
            working_segment = working_segment[1:]
            labels[0][1] += 1
            if labels[0][1] > labels[0][2]:
                labels.pop(0)

    if not labels:
        raise ValueError(LABEL_ERROR)
    
    label_start = [labels[0][0], labels[0][1]]
    label_finish = ["", 0]
    end = 0
    chop = strip_punctuation(chop)
    
    if not chop:
        return None, working_segment, None, labels
        
    for x in chop:
        if x not in working_segment[end:]:
            raise ValueError(f"Error: Missing character: {x}")
        for i in range(end, len(working_segment)):
            if working_segment[i] == x:
                end = i+1
                break

    razorcut = False
    if end < len(working_segment):
        if working_segment[end] == "\n":
            end += 1
            razorcut = True

    lines_chopped = working_segment[:end].count("\n") + (0 if razorcut else 1)
    
    while lines_chopped > 0:
        if not labels:
            raise ValueError(LABEL_ERROR)
        else:
            if lines_chopped <= labels[0][2]-labels[0][1]+1:
                label_finish = [labels[0][0], labels[0][1]+lines_chopped-1]
                labels[0][1] += lines_chopped if razorcut else (lines_chopped-1)
                if labels[0][1] > labels[0][2]:
                    labels.pop(0)
                lines_chopped = 0
            else:
                lines_chopped -= labels[0][2]-labels[0][1]+1
                labels.pop(0)
    
    label = (f"{label_start[0]}.{label_start[1]}"
             + ("–" if label_start != label_finish else "")
             + (f"{label_finish[0]}." if label_finish[0] != label_start[0] else "")
             + (f"{label_finish[1]}" if label_start != label_finish else ""))
    
    return working_segment[:end], working_segment[end:], label, labels

# ------------------------------------------------------------------------------------------

def clean(text):
    if not text:
        return text
    text = text.replace("/", "")
    text = text.replace(")\n(", "\n")
    text = text.replace(")\n　(", "\n")
    return text

# ------------------------------------------------------------------------------------------

def pop_glosses(segment, marker = ""):

    glosses = []

    def _insert_marker(m: re.Match):
        glosses.append(m.group(1)) # content without parentheses        
        return marker

    stripped_segment = _PARENTHESIS.sub(_insert_marker, segment)

    return stripped_segment, glosses

# ------------------------------------------------------------------------------------------

def find_possible_terms(segment):
    
    list_of_terms = []

    def parse_phrase(phrase: str):
        for span in range(0, len(phrase)):
            for i in range(0, len(phrase)-span):
                list_of_terms.append(phrase[i:i+1+span])

    start = 0
    for i in range(0, len(segment)):
        if segment[i] in _NON_CHARACTERS_SET:
            parse_phrase(segment[start:i])
            start = i+1
    parse_phrase(segment[start:])

    return list_of_terms

# ------------------------------------------------------------------------------------------
