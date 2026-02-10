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
- The translation should be easy flowing, readable, and smooth.
- Favor translating nouns in the singular unless context clearly requires plural.
- Follow the Chinese text punctuation as faithfully as possible.
- When referencing the title of a scripture book, use single quotation marks: ‘ ’.
- When quoting speech or a passage, use double quotation marks: “ ”.
- Do not start paragraphs with indentation.
- If the text is in verses (e.g., poem/song), keep the verse structure; each verse should be on its own line.
- For titles and headers, use capitalization appropriate for a book/text title.
"""

# ------------------------------------------------------------------------------------------

PUNCTUATION_CROSS_CHECK = True # If true, cost is subject to O(n^2) growth.
TRANSLATION_CROSS_CHECK = True # If true, cost is subject to O(n^2) growth.
LLM_GLOSSARY_SELECTION = False # If false, the selection is mechanical.

FACSIMILE_SPAN = 1
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
PUNCTUATION_VERBOSITY = "medium"
PUNCTUATION_TEMPERATURE = None
PUNCTUATION_TOP_P = None

PUNCTUATION_EXAMINATION_MODEL = "gemini-2.5-flash"
PUNCTUATION_EXAMINATION_REASONING = None
PUNCTUATION_EXAMINATION_VERBOSITY = None
PUNCTUATION_EXAMINATION_TEMPERATURE = 0
PUNCTUATION_EXAMINATION_TOP_P = None

PUNCTUATION_CORRECTION_MODEL = "gpt-5.2"
PUNCTUATION_CORRECTION_REASONING = "low"
PUNCTUATION_CORRECTION_VERBOSITY = "medium"
PUNCTUATION_CORRECTION_TEMPERATURE = None
PUNCTUATION_CORRECTION_TOP_P = None

GLOSSARY_SELECTION_MODEL = "gpt-5.2"
GLOSSARY_SELECTION_REASONING = "none"
GLOSSARY_SELECTION_VERBOSITY = "high"
GLOSSARY_SELECTION_TEMPERATURE = None
GLOSSARY_SELECTION_TOP_P = 1

TRANSLATION_MODEL = "gpt-5.2"
TRANSLATION_REASONING = "medium"
TRANSLATION_VERBOSITY = "medium"
TRANSLATION_TEMPERATURE = None
TRANSLATION_TOP_P = None

TRANSLATION_EXAMINATION_MODEL = "gemini-2.5-flash"
TRANSLATION_EXAMINATION_REASONING = None
TRANSLATION_EXAMINATION_VERBOSITY = None
TRANSLATION_EXAMINATION_TEMPERATURE = 0
TRANSLATION_EXAMINATION_TOP_P = None

TRANSLATION_CORRECTION_MODEL = "gpt-5.2"
TRANSLATION_CORRECTION_REASONING = "medium"
TRANSLATION_CORRECTION_VERBOSITY = "medium"
TRANSLATION_CORRECTION_TEMPERATURE = None
TRANSLATION_CORRECTION_TOP_P = None

GLOSSARY_EXTRACTION_MODEL = "gpt-5.2"
GLOSSARY_EXTRACTION_REASONING = "none"
GLOSSARY_EXTRACTION_VERBOSITY = "medium"
GLOSSARY_EXTRACTION_TEMPERATURE = 0
GLOSSARY_EXTRACTION_TOP_P = None

# ------------------------------------------------------------------------------------------
