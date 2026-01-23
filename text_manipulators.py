############################################################################################
############################################################################################
############################################################################################
# TEXT MANIPULATORS
############################################################################################
############################################################################################
############################################################################################


import string

import re


############################################################################################

SEGMENTOR = "<break>"

ENDERS = "。？！.!?)*" # ** is coded for titles and headers.

CLOSERS = '"”’」』】）》）〉》〕］｝」』｣)}›»*'

punctuation = re.compile(rf"[{re.escape(ENDERS)}][{re.escape(CLOSERS)}]*") # [..]* is regex.

punctuation_end = re.compile(rf"[{re.escape(ENDERS)}][{re.escape(CLOSERS)}]*$")

non_characters = set()
# ASCII punctuation and space
non_characters.update(string.punctuation)    # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
non_characters.add(' ')                      # normal space
non_characters.update(string.digits)         # numbers
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
# All Latin letters (ASCII) a-zA-Z
non_characters.update(string.ascii_letters)
# Combine in a table:
_STRIP_TABLE = str.maketrans('', '', ''.join(non_characters))


############################################################################################


def strip_punctuation(text: str) -> str:

    return text.translate(_STRIP_TABLE)


############################################################################################


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
        

############################################################################################


def chop_from_working_segment(punctuated_segments, working_segment):

    chop = ""

    for x in punctuated_segments:
        chop += x

    chop = strip_punctuation(chop)
    
    start = 0
    
    for x in chop:
        for i in range(start, len(working_segment)):
            if working_segment[i] == x:
                start = i+1
                break

    return working_segment[start:]


############################################################################################
