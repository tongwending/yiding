############################################################################################
############################################################################################
############################################################################################
# INSTRUCTION PROMPTS
############################################################################################
############################################################################################
############################################################################################


punctuation_instructions = (
"""The user will give you a section of Chinese text to punctuate.
For context and continuation, the punctuated preceding segment and the yet to be punctuated following segment will be provided. Punctuate only the "Current segment".
Keep the parentheses in their places, but punctuate inside them if needed.
Do not change any Chinese characters.
Do not add anything else in the response; give only the punctuated text.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• If the text is clearly in verses (for example, as in a poem or song) keep the structure.
• Be mindful of new lines. Do not follow the new lines of the original text unless they are purposefully lined that way. Change line only if it makes sense in the structure of the text.
• Use 《》(or〈〉) for quoted titles of other scripture.
• Use 「」(or『』) when something is quoted or character speaks. When appropriate, use ： for the quotes' introduction.
• Always use ；(分号 fēnhào) to separates parallel units that are related but already internally complex, except if the clauses are too short or too long.
• Keeps honorific chains intact.""")

glossary_extraction_instructions = (
"""The user will give you a segment of Chinese text to create a list of the key terms of the Chinese text and how they are translated by provided translation.
For context and continuation, the preceding and following segments will be provided. Select terms only from the "Current segment" (including terms that might be separated from the segment divide).

In your answer you should include only the list following the excact format below:
Chinese term (accented Pinyin) = English translation

Do not add your own translation of the term (use only what is found in the corresponding English translation).
If the text translates multiple instances of a Chinese term differently, add English translations using commas to separate them.
Always separate multiple meanings with comma (not slash).
Do not give translation variants. Only what is in the corresponding text.
Do not add anything else in the response; give only the list.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidlines:
• Except if a term is inherently plural, use English singular form even if in the translation it is in plural.
• Do not select whole phrases, except in the case of idiomatic expresions, in which case give both the phrase and the terms it is comprised of.
• If there is a title, select the title as a whole as well as each of its terms individually.
• Make sure you separate the pinyin parts (but not the Chinese).
• Don't forget the umlauts.
• Do not include 《,》,〈,〉,「 ,」,『 or 』.
• Do not include phrases, except if they are part of a term or a compound.
• Capitalize only proper names.""")

translation_instructions = (
"""Translate to English the given segment of Chinese text.
For context and continuation, the preceding segment, its translation, and the yet to be translated following section will be provided. Translate only the "Current segment".
Make sure to continue from the previous section's translation, expecially if left in the middle of a sentence.
Keep parenthesises and other elements, but do not keep new lines if they don't meaningfully contribute to the structure of the text.
Do not include your own explainations or comments; only the translation.
Do not include parentheses of your own; only the ones that allready exist.
Do not keep the Chinese version of terms in translation; just translate.
Do not add anything else in the response; give only the translation.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• The translation should be elegant.
• If the text is clearly in verses (for example, as in a poem or song) keep the structure.
• Do not italicize or bolden.
• If titles of other scriptures are referenced use ‘ ’.
• If the text is quoting something, use “ ”.
• If a part is clearly the title or header of a section, make sure that an empty line precedes, that you use appropriate capitalization for title or header, and that the title or header has the follow form: - Title of Section -
• Do not add empty lines between paragraphs except if there is a clear strong distinction in the text's structure, such as the intruduction of a new header or a lengthy quote.
• Start paragraphs with indentation, except in the case of introducing structured texts (such as verses of a song) or continueing directly from the preceding segment.
• Do not end with … if the text continues to the next segment.""")

title_translation_instructions = (
"""The user will give you a Chinese title to translate into English.
Do not use any character or symbol that cannot be in the name of a computer file.
Do not add anything else in the response; give only the translation.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidlines:
• The translation style should be academic but without compromising the poetics of the title.
• Use capitalization appropriate to a title of a book or text.
• Do not use a period at the end.""")

glossary_selection_instructions = (
"""The user will give you a segment of Chinese text and you will select the Chinese terms needed for the translation of the text into English.
For context and continuation, the assistant will provide the punctuated preceding segment and yet to be punctuated following segment. Select terms only from the "Current segment".
Write the selected terms as a list (each on its own line without any panctuation):

term 1
term 2
term 3
etc

Do not add anything else in the response; give only the list.
If the user only gives an empty text or a single underscore character, respond back with a single underscore character.

Stylistic Guidelines:
• Do not select whole phrases, except in the case of idiomatic expresions, in which case give both the phrase and the terms it is comprised of.
• If there is a title, select the title as a whole as well as each of its terms individually.""")


############################################################################################


        
    
