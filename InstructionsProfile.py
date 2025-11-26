





############################################################################################
############################################################################################
############################################################################################
### INSTRUCTIONS PROFILE CLASS
############################################################################################
############################################################################################
############################################################################################


from glossary_dictate import load_glossary


############################################################################################


class InstructionsProfile:


    def __init__(self, glossary = None):

        from sk import my_sk            # Imports the personal OpenAI API Key to access GPT.

        client = OpenAI(api_key=my_sk)  # Reads the OpenAI API Key.
        self.client = client
        
        # reasoning options: "none" | "low" | "medium" | "high"
        # verbosity option: "low" | "medium" | "high"

        self.punctuation_instructions = punctuation_instructions
        self.punctuation_GPT_model = "gpt-5.1"
        self.punctuation_GPT_reasoning = "none"
        self.punctuation_GPT_verbosity = "low"
                
        self.glossary_selection_instructions = glossary_selection_instructions
        self.glossary_selection_GPT_model = "gpt-5.1"
        self.glossary_selection_GPT_reasoning = "none"
        self.glossary_selection_GPT_verbosity = "high"
        
        self.translation_instructions = translation_instructions
        self.translation_GPT_model = "gpt-5.1"
        self.translation_GPT_reasoning = "none"
        self.translation_GPT_verbosity = "low"
        
        self.title_translation_instructions = title_translation_instructions
        self.title_translation_GPT_model = "gpt-5.1"
        self.title_translation_GPT_reasoning = self.translation_GPT_reasoning
        self.title_translation_GPT_verbosity = "low"

        self.glossary_extraction_instructions = glossary_extraction_instructions
        self.glossary_extraction_GPT_model = "gpt-5.1"
        self.glossary_extraction_GPT_reasoning = "none"
        self.glossary_extraction_GPT_verbosity = "high"
        

        if glossary:
            self.glossary = load_glossary(glossary)
        else:
            self.glossary = {}

        self.title_extension = f" - PUN{self.punctuation_GPT_reasoning}" + \
                               f" - GLSEL{self.glossary_selection_GPT_reasoning}" + \
                               f" - TRANS{self.translation_GPT_reasoning}" + \
                               f" - GLEXT{self.glossary_extraction_GPT_reasoning}"

            
    def dictate(self, file_or_text):
        self.glossary = load_glossary(file_or_text)


    def __getstate__(self):
        """Return picklable state (drop the OpenAI client)."""
        state = self.__dict__.copy()
        # client is not picklable
        state['client'] = None
        return state


    def __setstate__(self, state):
        """Restore state and recreate the OpenAI client."""
        self.__dict__.update(state)
        from sk import my_sk
        self.client = OpenAI(api_key=my_sk)
        

############################################################################################
# INSTRUCTIONS PROMPTS
############################################################################################


punctuation_instructions = (
"""The user will give you a section of Chinese text to punctuate.
For context and continuation, the assistant will provide the punctuated preceding text and yet to be punctuated following text.
If the text is clearly in verses (for example, as in a poem or song) keep the structure.
Be mindful of new lines. Do not follow the new lines of the original text unless they are purposefully lined that way. Change line only if it makes sense in the structure of the text.
Use 《》(or〈〉) for titles of works.
Use 「」(or『』) when something is quoted or character speaks. When appropriate, use ： for the quotes' introduction.
Avoid ；, except if it is absolutely necessary.
Keeps honorific chains intact.
Do not change any Chinese characters.
Keep the parentheses in their places, but punctuate inside them if needed.
Do not add anything else in the response; give only the punctuated text.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.""")

glossary_extraction_instructions = (
"""The user will give you a section of Chinese text.
For context and continuation, the assistant will provide the preceding and following texts.

Create a list of the key terms of the Chinese text and how they are translated by provided translation.
In your answer you should include only the list following the excct format below: 

Chinese term (accented Pinyin) = English translation

- Do not add your own translation of the term (use only what is found in the corresponding English translation).
- If the text translates multiple instances of a Chinese term differently, add English translations using commas to separate them.
- Except if a term is inherently plural, use English singular form even if in the translation it is in plural.
- Do not select whole phrases, except in the case of idiomatic expresions, in which case give both the phrase and the terms it is comprised of.
- If there is a title, select the title as a whole as well as each of its terms individually.
- Make sure you separate the pinyin parts (but not the Chinese).
- Don't forget the umlauts.
- Do not include 《,》,〈,〉,「 ,」,『 or 』.
- Do not include phrases, except if they are part of a term or a compound.
- Do not give translation variants. Only what is in the corresponding text.
- Always separate multiple meanings with comma (not slash).
- Capitalize only proper names.
- Do not add anything else in the response; give only the list.
- If the user only gives an empty text or a single underscore character, respond back with a single underscore character.""")

translation_instructions = (
"""Translate to English the given section of Chinese text.
The translation should be elegant.
If the text is clearly in verses (for example, as in a poem or song) keep the structure.
Keep parenthesises and other elements, but do not keep new lines if they don't meaningfully contribute to the structure of the text.
Do not italicize or bolden.
If titles of other scriptures are referenced use ‘ ’.
If the text is quoting something, use “ ”.
If a part is clearly the title or header of a section, make sure that an empty line precedes, that you use appropriate capitalization for title or header, and that the title or header has the follow form:
- Title of Section -
Do not add empty lines between paragraphs except if there is a clear strong distinction in the text's structure, such as the intruduction of a new header or a lengthy quote.
Start paragraphs with indentation, except in the case of introducing structured texts (such as verses of a song).
For context and continuation, the assistant will provide the preceding section and its translation as well as the yet to be translated following section. Make sure to continue from the previous section's translation, expecially if left in the middle of a sentence.
Do not end with … if the text continue to the next segment.
Do not include your own explainations or comments; only the translation.
Do not include parentheses of your own; only the ones that allready exist.
Do not keep the Chinese version of terms in translation; just translate.
Do not add anything else in the response; give only the translation.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.""")

title_translation_instructions = (
"""The user will give you a Chinese title to translate into English.
The translation style should be academic but without compromising the poetics of the title.
Use capitalization appropriate to a title of a book or text.
Do not use a period at the end.
Do not use any character or symbol that cannot be in the name of a computer file.
Do not add anything else in the response; give only the translation.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.""")

glossary_selection_instructions = (
"""The user will give you a Chinese text and you will select the Chinese terms needed for the translation of the text into English.
Do not select whole phrases, except in the case of idiomatic expresions, in which case give both the phrase and the terms it is comprised of.
If there is a title, select the title as a whole as well as each of its terms individually.
For context and continuation, the assistant will provide the punctuated preceding text and yet to be punctuated following text.
Write the selected terms as a list (each on its own line without any panctuation):

term 1
term 2
term 3
etc

Do not add anything else in the response; give only the list.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.""")


############################################################################################

