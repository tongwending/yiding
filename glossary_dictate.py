# ------------------------------------------------------------------------------------------
# glossary_dictate
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
        if len(words) > 2:
            glossary[words[0]] = [words[1], {w for w in words[2:] if w.strip() != ""} ]

    return glossary

# ------------------------------------------------------------------------------------------

def update_glossary(glossary, addition):

    for term in addition:
        if term not in glossary:
                glossary[term] = addition[term]
        if term in glossary:
                glossary[term][1].update(addition[term][1])

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

            translations = term_and_translations[1].split(',')
            translations = [t.strip() for t in translations]
            set_of_translations = set(translations)

            pinyin_and_set_of_translations = [pinyin, set_of_translations]

            glossary_proper[chinese] = pinyin_and_set_of_translations

    # The product is a dictionary whose values are lists of a str and a set:
    # glossary_proper = {chinese:[pinyin, {set_of_translations}]}
    return glossary_proper

# ------------------------------------------------------------------------------------------

def glossary_to_csv(glossary, filename): #  not used now but might be handy later
    with open(filename, "w", encoding="utf-8") as file:
        for key, value in glossary.items():
            file.write(f"{key},{value[0]}")
            for translation in value[1]:
                file.write(f",{translation}")
            file.write("\n")

# ------------------------------------------------------------------------------------------
