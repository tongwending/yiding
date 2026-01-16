############################################################################################
############################################################################################
############################################################################################
# INSTRUCTION PROMPTS
############################################################################################
############################################################################################
############################################################################################


# reasoning options: "none" | "low" | "medium" | "high"
# verbosity option: "low" | "medium" | "high"

LANGUAGE = "English"

PUNCTUATION_MODEL = "gpt-5.1"
PUNCTUATION_REASONING = "none"
PUNCTUATION_VERBOSITY = "low"
PUNCTUATION_TEMPERATURE = 0

GLOSSARY_SELECTION_MODEL = "gpt-5.1"
GLOSSARY_SELECTION_REASONING = "none"
GLOSSARY_SELECTION_VERBOSITY = "high"
GLOSSARY_SELECTION_TEMPERATURE = 0

TRANSLATION_MODEL = "gpt-5.1"
TRANSLATION_REASONING = "none"
TRANSLATION_VERBOSITY = "medium"
TRANSLATION_TEMPERATURE = 0

TITLE_TRANSLATION_MODEL = "gpt-5.1"
TITLE_TRANSLATION_REASONING = "none"
TITLE_TRANSLATION_VERBOSITY = "low"
TITLE_TRANSLATION_TEMPERATURE = 0

CROSS_EXAMINATION_MODEL = "gpt-5.1"
CROSS_EXAMINATION_REASONING = "none"
CROSS_EXAMINATION_VERBOSITY = "low"
CROSS_EXAMINATION_TEMPERATURE = 0

CROSS_CORRECTION_MODEL = "gpt-5.1"
CROSS_CORRECTION_REASONING = "none"
CROSS_CORRECTION_VERBOSITY = "low"
CROSS_CORRECTION_TEMPERATURE = 0

GLOSSARY_EXTRACTION_MODEL = "gpt-5.1"
GLOSSARY_EXTRACTION_REASONING = "none"
GLOSSARY_EXTRACTION_VERBOSITY = "medium"
GLOSSARY_EXTRACTION_TEMPERATURE = 0


def instruct_punctuation():
    return """The user will give you a section of Chinese text to punctuate.
For context and continuation, the punctuated preceding segment and the yet to be punctuated following segment will be provided. Punctuate only the "Current segment".
Keep the parentheses in their places, but punctuate inside them if needed.
Add a double asterisk (**) before and after main title, headers, and tail titles (but not quoted titles), using the following format: **TITLE**
Do not change any Chinese characters.
Do not add anything else in the response; give only the punctuated text.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• If the text is clearly in verses (for example, as in a poem or song) keep the structure.
• Be mindful of new lines. Do not follow the new lines of the original text unless they are purposefully lined that way. Change line only if it makes sense in the structure of the text.
• Keep referenced titles of scripture intact (do not punctuate inside them).
• Use 《》(or〈〉) for quoted titles of other scripture.
• Use 「」(or『』) when something is quoted or character speaks. When appropriate, use ： for the quotes' introduction.
• Always use ；(分號 fēnhào) to separate parallel units that are related but already internally complex, except if the clauses are too short or too long.
• Keep honorific chains intact.
"""


def instruct_glossary_selection (language = LANGUAGE):
    return f"""The user will give you a segment of Chinese text and you will select the Chinese terms needed for the translation of the text into {language}.
For context and continuation, the punctuated preceding segment and the yet to be punctuated following segment will be provided. Select terms only from the "Current segment".
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
    return f"""Translate to {language} the given segment of Chinese text.
For context and continuation, the preceding segment, its translation, and the yet to be translated following section will be provided. Translate only the "Current segment".
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
"""• The translation should be elegant.
• If the text is clearly in verses (for example, as in a poem or song) keep the structure.
• Keep the parataxis of the Chinese text using the equivalent of  ；(分號 fēnhào).
• If titles of other scriptures are referenced use ‘ ’.
• If the text is quoting something, use “ ”.
• If there is title, header or tail title, make sure an empty line precedes it and add a double asterisk (**) before and after the title, using the following format: **Title**
• Use appropriate capitalization in titles or headers
• Do not add empty lines between paragraphs except if there is a clear strong distinction in the text's structure, such as the introduction of a new header or a lengthy quote.
• Start paragraphs with indentation, except in the case of introducing structured texts (such as verses of a song) or continuing directly from the preceding segment.
"""


def instruct_title_translation (language = LANGUAGE):
    return f"""The user will give you a Chinese title to translate into {language}.
Do not use any character or symbol that cannot be in the name of a computer file.
Do not add anything else in the response; give only the translation.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• The translation style should be academic but without compromising the poetics of the title.
• Use capitalization appropriate to a title of a book or text.
• Do not use a period at the end.
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
• grammatical number of the same term rendered differently.
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
For context and continuation, the preceding and following segments will be provided. Select terms only from the "Current segment" (including terms that might be separated from the segment divide).

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


        
    
