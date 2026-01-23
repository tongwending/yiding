############################################################################################
############################################################################################
############################################################################################
# INSTRUCTION PROMPTS
############################################################################################
############################################################################################
############################################################################################


# reasoning options: "none" | "low" | "medium" | "high"
# verbosity option: "low" | "medium" | "high"

PUNCTUATION_SPAN = 3 # number of previous punctuated segments in prompts 
TRANSLATION_SPAN = 2 # number of previous punctuated-translated segment pairs in prompts
MAX_UNSEGMENTED_SPAN = 680 # maximum characters allowed without segment break

LANGUAGE = "English"

PUNCTUATION_MODEL = "gpt-5.2"
PUNCTUATION_REASONING = "low"
PUNCTUATION_VERBOSITY = "low"
PUNCTUATION_TEMPERATURE = 1

GLOSSARY_SELECTION_MODEL = "gpt-5.2"
GLOSSARY_SELECTION_REASONING = "none"
GLOSSARY_SELECTION_VERBOSITY = "high"
GLOSSARY_SELECTION_TEMPERATURE = 1

TRANSLATION_MODEL = "gpt-5.2"
TRANSLATION_REASONING = "low"
TRANSLATION_VERBOSITY = "medium"
TRANSLATION_TEMPERATURE = 1

TITLE_TRANSLATION_MODEL = "gpt-5.2"
TITLE_TRANSLATION_REASONING = "low"
TITLE_TRANSLATION_VERBOSITY = "low"
TITLE_TRANSLATION_TEMPERATURE = 1

CROSS_EXAMINATION_MODEL = "gpt-5.2"
CROSS_EXAMINATION_REASONING = "none"
CROSS_EXAMINATION_VERBOSITY = "low"
CROSS_EXAMINATION_TEMPERATURE = 1

CROSS_CORRECTION_MODEL = "gpt-5.2"
CROSS_CORRECTION_REASONING = "none"
CROSS_CORRECTION_VERBOSITY = "low"
CROSS_CORRECTION_TEMPERATURE = 1

GLOSSARY_EXTRACTION_MODEL = "gpt-5.2"
GLOSSARY_EXTRACTION_REASONING = "none"
GLOSSARY_EXTRACTION_VERBOSITY = "medium"
GLOSSARY_EXTRACTION_TEMPERATURE = 1


def instruct_punctuation():
    return """The user will give you a segment of Chinese text to punctuate and break into sections reflecting paragraphs, stanzas or distinct text blocks using the following signifier: <break>
Break only when making sense as a paragraph or the text changes indentation structure or inserts a block of text as a quote or poem.
Keep lists as lists using newlists.
If the text is structured in verses, every verse should be in each own line and break after each stanza.
For context and continuation, the already punctuated preceding text will be provided. Punctuate only the "Current segment".
Keep in mind that the text might be abruptetely ended, which means that the last paragraph or section might be halfway only.
Do not change any Chinese characters.
Do not add anything else in the response; give only the punctuated text.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Guidelines for Punctuation:
- Keep the parentheses in their places, but punctuate inside them if needed.
- Add a double asterisk (**) before and after main title, headers, and tail titles (but not quoted titles), using the following format: **TITLE**
• If the text is clearly in verses (for example, as in a poem or song) keep the structure.
• Be mindful of new lines. Do not follow the new lines of the original text unless they are purposefully lined that way. Change line only if it makes sense in the structure of the text.
• Keep referenced titles of scripture intact (do not punctuate inside them).
• Use 《》(or〈〉) for quoted titles of other scripture.
• Use 「」(or『』) when something is quoted or character speaks. When appropriate, use： for the quotes' introduction.
• Always use ；(分號 fēnhào) to separate parallel units that are related but already internally complex, except if the clauses are too short or too long.
• Always use 、(顿号 dùnhào) to separate lists.
• Keep honorific chains intact.
"""


def instruct_glossary_selection (language = LANGUAGE):
    return f"""The user will give you a segment of Chinese text and you will select the Chinese terms needed for the translation of the text into {language}.
Write the selected terms as a list (each on its own line without any punctuation):

term 1
term 2
term 3
etc

Do not add anything else in the response; give only the list.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• Do not select whole phrases, except in the case of idiomatic expressions, in which case give both the phrase and the terms it is comprised of.
• If there is a title, select the title as a whole as well as each of its terms individually.
• Do not include 《,》,〈,〉,「 ,」,『 or 』.
"""


def instruct_translation (language = LANGUAGE):
    return f"""Translate the given segment of Chinese text to {language}.
For context and continuation, the preceding segment and its translation. Translate only the "Current segment".
Make sure to continue from where previous section's translation ended (don't change paragraph if the paragraph doesn't change in the Chinese text).
Keep parentheses and other elements, but do not keep new lines if they don't meaningfully contribute to the structure of the text.
Do not include your own explanations or comments; only the translation.
Do not italicize or bold.
Do not include parentheses of your own; only the ones that already exist.
Do not keep the Chinese version of terms in translation; just translate.
Do not add anything else in the response; give only the translation.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
{TRANSLATION_GUIDELINES}
"""

TRANSLATION_GUIDELINES = \
"""• The translation should be academic without compromising the poetics of the original Chinese text.
• Favor translating nouns in singular number, unless the context clearly indicates that it should be plural.
• Keep the parataxis of the Chinese text using the equivalent of  ；(分號 fēnhào).
• If a title of a scripture book is referenced in the text use ‘ ’.
• If the text is quoting something, use “ ”.
• Don't start paragraphs with indentation.
• If the text is in verses (for example, as in a poem or song) keep its structure. Each verse should be in its own line.
"""


def instruct_title_translation (language = LANGUAGE):
    return f"""Translate the given Chinese title to {language}.
For context and continuation, the preceding text might be given. Translate only the title.
Do not include your own explanations or comments; only the translation.
Do not italicize or bold.
Do not include parentheses of your own; only the ones that already exist.
Do not keep the Chinese version of terms in translation; just translate.
Do not add anything else in the response; give only the translation of the title
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• The translation style should be academic but without compromising the poetics of the original Chinese.
• Use capitalization appropriate to a title of a book or text.
• Do not use a period at the end of a title, header or tai title.
• Add a double asterisk (**) before and after the translated title, using the following format: **Title**
"""
    

def instruct_cross_examination(language = LANGUAGE):
    return f"""You will be given two different Chinese segments (segment A and segment B) and their corresponding {language} translations.
Check if translation B is inconsistent with translation A according to the definition of inconsistencies below:
{INCONSISTENCIES}

Return ONLY a valid JSON object with exactly one key: "answer".
"answer" must be a boolean (true or false). Do not include any other keys, text, markdown, or code fences.
If there are inconsistencies, respond with true.
If there are no inconsistencies, respond with false.

Further Guidelines:
Focus only on translation or rendering inconsistences, not style.
Don't bother with minor incosistencies such as an article or pronoun here and there.
Don't bother with alternative translations of the Chinese; focus
Don't compare each translation with their conresponding Chinese text; compare the two translation and how they handled same terms, idioms or phrases.
They two Chinese segments are different, so don't flag them as inconsistent for not being identical.
They is a high possibility that there are no inconsistences; don't flag as inconsistent without a reason.
"""

INCONSISTENCIES = \
"""• terms translated unjustifiably differently.
• idioms translated differently.
• phrases translated differently.
• verbatim sentences or quotes translated differently.
"""


def instruct_cross_correction(language = LANGUAGE):
    return f"""You will be given two Chinese segments and their corresponding {language} translation.
The translation of segment B has one or more inconsistences when compared to translation of segment A.
Identify them and to make minimal changes to segment B in order to smooth them out.

Inconsistences are defined as:
{INCONSISTENCIES}

Focus only on translation or rendering inconsistences, not style.
Don't bother with minor incosistencies such as an article or pronoun here and there.
Don't compare each translation with their conresponding Chinese text; compare the two translation and how they handled same terms, idioms or phrases.
Respond only with the minimally corrected translation of segment B.
Don't add anything else in the response.

When correcting, adhere to the following guidelines:
• Make minimal changes that will correct the inconsistencies. 
• Change only the inconsistencies; don't change anything else. There is high possibility that there will be a very small number of inconsistent sentences.
• Make minor changes in the rest of the text only if it is necessary for the new corrections to work.
• Keep punctuation and indentation as is.
• Do not add anything else in the response; give only the corrected translation.
• If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

The translation follows the certain stylistic guidelines. Adhere to them. They are the following:
{TRANSLATION_GUIDELINES}
"""

    
def instruct_glossary_extraction(language = LANGUAGE):
    return f"""The user will give you a segment of Chinese text to create a list of the key terms of the Chinese text and how they are translated by the provided translation.
In your answer you should include only the list following the exact format below:
Chinese term (accented Pinyin) = {language} translation

Do not add your own translation of the term (use only what is found in the corresponding {language} translation).
If the text translates multiple instances of a Chinese term differently, add {language} translations using commas to separate them.
Always separate multiple meanings with a comma (not a slash).
Do not give translation variants. Only what is in the corresponding text.
Do not add anything else in the response; give only the list.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• Except if a term is inherently plural, use {language} singular form even if in the translation it is in plural.
• Do not select whole phrases, except in the case of idiomatic expressions, in which case give both the phrase and the terms it is comprised of.
• If there is a title, select the title as a whole as well as each of its terms individually.
• Make sure you separate the pinyin syllables (but not the Chinese characters).
• Don't forget the umlauts.
• Do not include 《,》,〈,〉,「 ,」,『 or 』.
• Capitalize only proper names.
"""


############################################################################################


        
    
