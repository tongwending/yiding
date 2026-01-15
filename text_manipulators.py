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
_STRIP_TABLE = str.maketrans('', '', ''.join(non_characters))


############################################################################################


def strip_punctuation(text: str) -> str:

    return text.translate(_STRIP_TABLE)


############################################################################################


def mend_last_sentence(segment_a, segment_b):
    
    stripped_a = segment_a.rstrip()

    if not stripped_a or re.search(punctuation_end, stripped_a):
        return segment_a, segment_b, None
    
    first_punctuation = re.search(punctuation, segment_b)
    
    new_segment_a = stripped_a + segment_b[:first_punctuation.end()] \
                    if first_punctuation else segment_a

    new_segment_b = segment_b[first_punctuation.end():].lstrip() \
                    if first_punctuation else segment_b
    
    moved_halfverse = segment_b[:first_punctuation.end()] if first_punctuation else None
    
    return new_segment_a, new_segment_b, moved_halfverse


############################################################################################


def break_to_verses(segment):

    list_of_verses = []

    no_punctuation_left = False    
    while no_punctuation_left == False:
        
        next_punctuation = re.search(punctuation, segment)

        if not next_punctuation:
            no_punctuation_left = True

        else:
            list_of_verses.append(segment[:next_punctuation.end()])
            segment = segment[next_punctuation.end():]

    # check for leftovers
    if segment.rstrip():
        list_of_verses.append(segment)


    return list_of_verses


############################################################################################


def glue_verses(list_of_verses):

    versified_segment = ""

    for i in range(0, len(list_of_verses)):

        versified_segment = f"{versified_segment}[{i+1}]{list_of_verses[i]}"

    return versified_segment


############################################################################################
