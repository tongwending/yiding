# ------------------------------------------------------------------------------------------
# glossary_dictate
# ------------------------------------------------------------------------------------------

from copy import deepcopy

# ------------------------------------------------------------------------------------------

def load_glossary(file_or_text):
    
    glossary = {}

    if file_or_text == None:
        return glossary

    if file_or_text.lower().endswith(".txt") or file_or_text.lower().endswith(".csv"):
        with open(file_or_text, 'r', encoding='utf-8') as f:
            list_of_rows = f.readlines()
    else:
        list_of_rows = file_or_text.splitlines()

    for row in list_of_rows:
        words = [x.strip() for x in row.split(",")]
        if len(words) >= 2:
            glossary[words[0]] = [words[1], {w for w in words[2:] if w.strip() != ""} ]

    return glossary

# ------------------------------------------------------------------------------------------

def update_glossary(glossary, addition):

    for term in addition:
        if term in glossary:
            glossary[term][1].update(addition[term][1])
        else:
            glossary[term] = deepcopy(addition[term])

# ------------------------------------------------------------------------------------------

def stylize_glossary(glossary):
    
    stylized_glossary = ""
    
    if glossary:
   
        for term in glossary:
            stylized_glossary = (stylized_glossary +
                            f"\n{term} ({glossary[term][0]}) = ")
            if glossary[term][1]:
                for translation in glossary[term][1]:
                    stylized_glossary = (stylized_glossary +
                                            f"{translation}, ")
                stylized_glossary = stylized_glossary.strip(", ")


    return stylized_glossary

# ------------------------------------------------------------------------------------------

def destylize_glossary(glossary_text):
    
    glossary_lines = glossary_text.splitlines()

    glossary_proper = {}
    
    for j in glossary_lines:
        if "=" in j and "(" in j:
            term_and_translations = j.split('=')
            
            term = term_and_translations[0].strip()
            chinese_and_pinyin = term.split('(')

            chinese = chinese_and_pinyin[0].strip()
            pinyin = chinese_and_pinyin[1].strip(')')

            translations = {
                t.strip()
                for t in term_and_translations[1].split(',')
                if t.strip()
            }

            pinyin_and_set_of_translations = [pinyin, translations]

            glossary_proper[chinese] = pinyin_and_set_of_translations

    # The product is a dictionary whose values are lists of a str and a set:
    # glossary_proper = {chinese:[pinyin, {set_of_translations}]}
    return glossary_proper

# ------------------------------------------------------------------------------------------

def destylize_terms(term_text):
    
    term_lines = term_text.splitlines()

    terms_proper = {}

    for line in term_lines:

        if "(" in line:
            chinese_and_pinyin = line.split('(')
            chinese = chinese_and_pinyin[0].strip()
            pinyin = chinese_and_pinyin[1].strip()
            pinyin = pinyin.strip(')')
            empty_translations = set()
            terms_proper[chinese] = [pinyin, empty_translations]

    return terms_proper

# ------------------------------------------------------------------------------------------

def unite_glossaries(glossary_A, glossary_B):

    united_glossary = deepcopy(glossary_A)
    update_glossary(united_glossary, glossary_B)

    return united_glossary

# ------------------------------------------------------------------------------------------

def differentiate_glossaries(minuend_glossary, subtrahend_glossary):

    #The result is translation_glossary minus its intersection with base_glossary.

    differentiated_glossary = {}

    for term in minuend_glossary:
        pinyin = minuend_glossary[term][0]
        translations = minuend_glossary[term][1]
        
        if term in subtrahend_glossary:
            remaining_translations = translations - subtrahend_glossary[term][1]

            if remaining_translations or not translations:
                differentiated_glossary[term] = [pinyin, set(remaining_translations)]
                
        else:
            differentiated_glossary[term] = [pinyin, set(translations)]

    return differentiated_glossary

# ------------------------------------------------------------------------------------------

def intersect_glossaries(glossary_A, glossary_B):

    intersected_glossary = {}

    for term in glossary_A:

        if term in glossary_B:
            translations = (glossary_A[term][1] & glossary_B[term][1])
            intersected_glossary[term] = [glossary_A[term][0], set(translations)]
                
    return intersected_glossary

# ------------------------------------------------------------------------------------------

