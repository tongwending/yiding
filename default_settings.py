# ------------------------------------------------------------------------------------------
# default_settings
# ------------------------------------------------------------------------------------------

OPEN_AI_API_KEY = "openai_sk.txt"    # actual key or the TXT file containing it
GOOGLE_API_KEY = "google_sk.txt"     # actual key or the TXT file containing it

# ------------------------------------------------------------------------------------------

LANGUAGE = "English"

# ------------------------------------------------------------------------------------------

GLOSSARY_FILE = "my_glossary.csv"

# ------------------------------------------------------------------------------------------

PUNCTUATION_GUIDELINES = """
- Keep referenced scripture titles intact; do not punctuate inside them.
- Use 《》 (or 〈〉) for quoted titles of other scripture.
- Use 「」 (or 『』) for direct speech/quotations; when appropriate, introduce the quote with ：.
- Use ； (分號 fēnhào) to separate parallel units that are related but already internally complex, except when clauses are too short or too long for a semicolon to read well.
- Use 、 (顿号 dùnhào) to separate list items.
- Keep honorific chains intact; do not split them with punctuation.
- If there is a list of terms, titles or headers, use bullet points ● (○ for sublists) and group them together as a unit.
"""

TRANSLATION_GUIDELINES = """
- The translation should be academic without compromising the poetics of the original Chinese text.
- Favor translating nouns in the singular unless context clearly requires plural.
- Preserve Chinese parataxis using the equivalent of ； (分號 fēnhào), i.e., semicolons where appropriate.
- When referencing the title of a scripture book, use single quotation marks: ‘ ’.
- When quoting speech or a passage, use double quotation marks: “ ”.
- Do not start paragraphs with indentation.
- If the text is in verses (e.g., poem/song), keep the verse structure; each verse should be on its own line.
"""

TITLE_TRANSLATION_GUIDELINES = """
- The translation style should be academic without compromising the poetics of the original Chinese.
- Use capitalization appropriate for a book/text title in the target language.
"""

# ------------------------------------------------------------------------------------------

PUNCTUATION_CROSS_CHECK = True # If true, cost is subject to O(n^2) growth.
TRANSLATION_CROSS_CHECK = True # If true, cost is subject to O(n^2) growth.
FASCIMILE_SPAN = 1
PUNCTUATION_SPAN = 3 # number of previous punctuated segments in prompts
TRANSLATION_SPAN = 2 # number of previous punctuated-translated segment pairs in prompts
MAX_UNSEGMENTED_SPAN = 1000 # maximum characters allowed without segment break
MAX_PUNCTUATION_ATTEMPTS = 7

# ------------------------------------------------------------------------------------------

# GPT reasoning options: "none" | "low" | "medium" | "high"
# Gemini reasoning (aka thinking) options: "minimal" | "low" | "medium" | "high"
# GPT verbosity option: "low" | "medium" | "high"

PUNCTUATION_MODEL = "gpt-5.2"
PUNCTUATION_REASONING = "none"
PUNCTUATION_VERBOSITY = "low"
PUNCTUATION_TEMPERATURE = 1

PUNCTUATION_EXAMINATION_MODEL = "gpt-5.2"
PUNCTUATION_EXAMINATION_REASONING = "none"
PUNCTUATION_EXAMINATION_VERBOSITY = "low"
PUNCTUATION_EXAMINATION_TEMPERATURE = 1

PUNCTUATION_CORRECTION_MODEL = "gpt-5.2"
PUNCTUATION_CORRECTION_REASONING = "low"
PUNCTUATION_CORRECTION_VERBOSITY = "low"
PUNCTUATION_CORRECTION_TEMPERATURE = 1

GLOSSARY_SELECTION_MODEL = "gpt-5.2"
GLOSSARY_SELECTION_REASONING = "none"
GLOSSARY_SELECTION_VERBOSITY = "high"
GLOSSARY_SELECTION_TEMPERATURE = 1

TRANSLATION_MODEL = "gpt-5.2"
TRANSLATION_REASONING = "none"
TRANSLATION_VERBOSITY = "medium"
TRANSLATION_TEMPERATURE = 1

TITLE_TRANSLATION_MODEL = "gpt-5.2"
TITLE_TRANSLATION_REASONING = "none"
TITLE_TRANSLATION_VERBOSITY = "low"
TITLE_TRANSLATION_TEMPERATURE = 1

TRANSLATION_EXAMINATION_MODEL = "gpt-5.2"
TRANSLATION_EXAMINATION_REASONING = "none"
TRANSLATION_EXAMINATION_VERBOSITY = "low"
TRANSLATION_EXAMINATION_TEMPERATURE = 1

TRANSLATION_CORRECTION_MODEL = "gpt-5.2"
TRANSLATION_CORRECTION_REASONING = "low"
TRANSLATION_CORRECTION_VERBOSITY = "low"
TRANSLATION_CORRECTION_TEMPERATURE = 1

GLOSSARY_EXTRACTION_MODEL = "gpt-5.2"
GLOSSARY_EXTRACTION_REASONING = "none"
GLOSSARY_EXTRACTION_VERBOSITY = "medium"
GLOSSARY_EXTRACTION_TEMPERATURE = 1

# ------------------------------------------------------------------------------------------
