





############################################################################################
############################################################################################
############################################################################################
### GPT ENGINES
############################################################################################
############################################################################################
############################################################################################


from glossary_dictate import stylize_glossary, destylize_glossary


############################################################################################


def GPT_Punctuator(i, text):

    preceding_section = text.segments[i-1] if i > 0 else None
    preceding_punctuated = text.punctuated_segments[i-1] if i > 0 else None
    following_section = text.segments[i+1] if i < len(text.segments)-1 else None
  
    conversation_history = ""
    if preceding_section:
        conversation_history = (conversation_history +
                                "Preceding original text:\n" +
                                preceding_section +
                                "\n\nPreceding punctuated text:\n" +
                                preceding_punctuated)
    if preceding_section and following_section:
        conversation_history = conversation_history + "\n\n"
    if following_section:
        conversation_history = (conversation_history +
                                "Following original text:\n" +
                                following_section)
    
    print(text.segments[i])
    

    response = text.instructions.client.responses.create(
            model = text.instructions.punctuation_GPT_model,
            input=[
                {
                    "role": "developer",
                    "content": text.instructions.punctuation_instructions
                },
                {
                    "role": "assistant",            
                    "content": conversation_history
                },
                {
                    "role": "user", 
                    "content": text.segments[i]
                }],
            reasoning={"effort": text.instructions.punctuation_GPT_reasoning},
            text={"verbosity": text.instructions.punctuation_GPT_verbosity}
            )         

    punctuated_text = response.output_text


    print(punctuated_text + "\n")
    
    
    return punctuated_text


############################################################################################


def GPT_Glossary_Selector(instructions_profile,
                   current_section, preceding_section = None, following_section = None):

    comb_instructions = (instructions_profile.glossary_selection_instructions)
   
    conversation_history = ""
    if preceding_section:
        conversation_history = (conversation_history +
                                "Preceding text:\n" +
                                preceding_section)
    if preceding_section and following_section:
        conversation_history = conversation_history + "\n\n"
    if following_section:
        conversation_history = (conversation_history +
                                "Following text:\n" +
                                following_section)

    print(current_section + "\n")
    

    response = instructions_profile.client.responses.create(
            model = instructions_profile.glossary_selection_GPT_model,
            input=[
                {
                    "role": "developer",
                    "content": comb_instructions
                },
                {
                    "role": "assistant",            
                    "content": conversation_history
                },
                {
                    "role": "user", 
                    "content": current_section
                }],
            reasoning={"effort": instructions_profile.glossary_selection_GPT_reasoning},
            text={"verbosity": instructions_profile.glossary_selection_GPT_verbosity}
            )         

    selection_of_terms = response.output_text


    print(selection_of_terms + "\n")
    
    
    return selection_of_terms


############################################################################################


def GPT_Translator(i, text):

    preceding_section = text.punctuated_segments[i-1] if i>0 else None
    preceding_translation = text.translated_segments[i-1] if i>0 else None
    following_section = text.punctuated_segments[i+1] if i<len(text.punctuated_segments)-1\
                                                        else None
                                                        

    stylized_glossary = stylize_glossary(text.segment_glossaries[i])
    
    comb_instructions = (text.instructions.translation_instructions +
                         "\n\nUse the glossary below (if applicable):\n" +
                         stylized_glossary)
    
    
    conversation_history = \
            f"Title: {text.Chinese_title}\nTranslation: {text.translated_title}\n\n"
    if preceding_section:
        conversation_history = (conversation_history +
                                "Preceding Chinese text:\n" +
                                preceding_section)
        if preceding_section or following_section:
            conversation_history = conversation_history + "\n\n"
    if preceding_translation:
        conversation_history = (conversation_history +
                                "Preceding English translation:\n" +
                                preceding_translation)
        if following_section:
            conversation_history = conversation_history + "\n\n\n"
    if following_section:
        conversation_history = (conversation_history +
                                "Following Chinese text:\n" +
                                following_section)
        
        
    print(stylized_glossary + "\n\n" + text.punctuated_segments[i] + "\n")
    

    response = text.instructions.client.responses.create(
            model = text.instructions.translation_GPT_model,
            input=[
                {
                    "role": "developer",
                    "content": comb_instructions
                },
                {
                    "role": "assistant",            
                    "content": conversation_history
                },
                {
                    "role": "user", 
                    "content": text.punctuated_segments[i]
                }],
            reasoning={"effort": text.instructions.translation_GPT_reasoning},
            text={"verbosity": text.instructions.translation_GPT_verbosity}
            )         

    translation = response.output_text

          
    print(translation + "\n")

    return translation


############################################################################################


def GPT_Glossator(i, text):

    preceding_section = text.punctuated_segments[i-1] if i>0 else None
    preceding_translation = text.translated_segments[i-1] if i>0 else None
    following_section = text.punctuated_segments[i+1] if i<len(text.punctuated_segments)-1\
                                                        else None

    
    text_and_translation = ("Chinese original:\n" + text.punctuated_segments[i] + "\n\n" +
                            "English translation:\n" + text.translated_segments[i])


    conversation_history = ""
    if preceding_section:
        conversation_history = ("Preceding Chinese text:\n" + preceding_section)
        if preceding_section or following_section:
            conversation_history = conversation_history + "\n\n"
    if preceding_translation:
        conversation_history = (conversation_history +
                                "Preceding translation:\n" +
                                preceding_translation)
        if following_section:
            conversation_history = conversation_history + "\n\n\n"
    if following_section:
        conversation_history = (conversation_history +
                                "Following Chinese text:\n" +
                                following_section)

    response = text.instructions.client.responses.create(
            model = text.instructions.glossary_extraction_GPT_model,
            input=[
                {
                    "role": "developer",
                    "content": text.instructions.glossary_extraction_instructions
                },
                {
                    "role": "assistant",            
                    "content": conversation_history
                },
                {
                    "role": "user", 
                    "content": text_and_translation
                }],
            reasoning={"effort": text.instructions.glossary_extraction_GPT_reasoning},
            text={"verbosity": text.instructions.glossary_extraction_GPT_verbosity}
            )         

    glossary_text = response.output_text

    
    print(glossary_text + "\n")


    return destylize_glossary(glossary_text)


############################################################################################


def GPT_Title_Translator(instructions_profile, temp_glossary, title):
        
    stylized_glossary = stylize_glossary(temp_glossary)
    
    comb_instructions = (instructions_profile.title_translation_instructions +
                         "\n\nUse the glossary below (if applicable):\n" +
                         stylized_glossary)


    conversation_history = ""

    print(stylized_glossary + "\n\n" + title + "\n")
    

    response = instructions_profile.client.responses.create(
            model = instructions_profile.title_translation_GPT_model,
            input=[
                {
                    "role": "developer",
                    "content": comb_instructions
                },
                {
                    "role": "assistant",            
                    "content": conversation_history
                },
                {
                    "role": "user", 
                    "content": title
                }],
            reasoning={"effort": instructions_profile.title_translation_GPT_reasoning},
            text={"verbosity": instructions_profile.title_translation_GPT_verbosity}
            )         

    translated_title = response.output_text

    
    print(translated_title + "\n\n" + title + "\n")

    return translated_title

    


def GPT_Title_Glossator(text, title):
    
    text_and_translation = ("Chinese original:\n" + text.Chinese_title + "\n\n" +
                            "English translation:\n" + title)

    conversation_history = ""

    
    response = text.instructions.client.responses.create(
            model = text.instructions.glossary_extraction_GPT_model,
            input=[
                {
                    "role": "developer",
                    "content": text.instructions.glossary_extraction_instructions
                },
                {
                    "role": "assistant",            
                    "content": conversation_history
                },
                {
                    "role": "user", 
                    "content": text_and_translation
                }],
            reasoning={"effort": text.instructions.glossary_extraction_GPT_reasoning},
            text={"verbosity": text.instructions.glossary_extraction_GPT_verbosity}
            )         

    glossary_text = response.output_text
    
    print(glossary_text + "\n")

    return destylize_glossary(glossary_text)
    

############################################################################################
