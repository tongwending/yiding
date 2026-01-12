############################################################################################
############################################################################################
############################################################################################
### INSTRUCTIONS PROFILE CLASS
############################################################################################
############################################################################################
############################################################################################


from openai import OpenAI

from glossary_dictate import *
import text_manipulators
import model_attributes


############################################################################################


class PromptEngine:


    def __init__(self, glossary = None, language = None):

        from sk import my_sk            # Imports the personal OpenAI API Key to access GPT.

        self.client = OpenAI(api_key=my_sk)  # Reads the OpenAI API Key.

        if language:
            self.language = language
        else:
            self.language = model_attributes.LANGUAGE

        self.PUNCTUATION_INSTRUCTIONS = model_attributes.instruct_punctuation()
        self.PUNCTUATION_MODEL = model_attributes.PUNCTUATION_MODEL
        self.PUNCTUATION_REASONING = model_attributes.PUNCTUATION_REASONING
        self.PUNCTUATION_VERBOSITY = model_attributes.PUNCTUATION_VERBOSITY
        self.PUNCTUATION_TEMPERATURE = model_attributes.PUNCTUATION_TEMPERATURE

        self.GLOSSARY_SELECTION_INSTRUCTIONS = model_attributes.instruct_glossary_selection(language = self.language)
        self.GLOSSARY_SELECTION_MODEL = model_attributes.GLOSSARY_SELECTION_MODEL
        self.GLOSSARY_SELECTION_REASONING = model_attributes.GLOSSARY_SELECTION_REASONING
        self.GLOSSARY_SELECTION_VERBOSITY = model_attributes.GLOSSARY_SELECTION_VERBOSITY
        self.GLOSSARY_SELECTION_TEMPERATURE = model_attributes.GLOSSARY_SELECTION_TEMPERATURE

        self.TRANSLATION_INSTRUCTIONS = model_attributes.instruct_translation(language = self.language)
        self.TRANSLATION_MODEL = model_attributes.TRANSLATION_MODEL
        self.TRANSLATION_REASONING = model_attributes.TRANSLATION_REASONING
        self.TRANSLATION_VERBOSITY = model_attributes.TRANSLATION_VERBOSITY
        self.TRANSLATION_TEMPERATURE = model_attributes.TRANSLATION_TEMPERATURE

        self.TITLE_TRANSLATION_INSTRUCTIONS = model_attributes.instruct_title_translation(language = self.language)
        self.TITLE_TRANSLATION_MODEL = model_attributes.TITLE_TRANSLATION_MODEL
        self.TITLE_TRANSLATION_REASONING = model_attributes.TITLE_TRANSLATION_REASONING
        self.TITLE_TRANSLATION_VERBOSITY = model_attributes.TITLE_TRANSLATION_VERBOSITY
        self.TITLE_TRANSLATION_TEMPERATURE = model_attributes.TITLE_TRANSLATION_TEMPERATURE

        self.CROSS_EXAMINATION_INSTRUCTIONS = model_attributes.instruct_cross_examination(language = self.language)
        self.CROSS_EXAMINATION_MODEL = model_attributes.CROSS_EXAMINATION_MODEL
        self.CROSS_EXAMINATION_REASONING = model_attributes.CROSS_EXAMINATION_REASONING
        self.CROSS_EXAMINATION_VERBOSITY = model_attributes.CROSS_EXAMINATION_VERBOSITY
        self.CROSS_EXAMINATION_TEMPERATURE = model_attributes.CROSS_EXAMINATION_TEMPERATURE

        self.GLOSSARY_EXTRACTION_INSTRUCTIONS = model_attributes.instruct_glossary_extraction(language = self.language)
        self.GLOSSARY_EXTRACTION_MODEL = model_attributes.GLOSSARY_EXTRACTION_MODEL
        self.GLOSSARY_EXTRACTION_REASONING = model_attributes.GLOSSARY_EXTRACTION_REASONING
        self.GLOSSARY_EXTRACTION_VERBOSITY = model_attributes.GLOSSARY_EXTRACTION_VERBOSITY
        self.GLOSSARY_EXTRACTION_TEMPERATURE = model_attributes.GLOSSARY_EXTRACTION_TEMPERATURE
        

        if glossary:
            self.glossary = load_glossary(glossary)
        else:
            self.glossary = {}

        self.title_extension = f" - PUN{self.PUNCTUATION_REASONING}" + \
                               f" - GLSEL{self.GLOSSARY_SELECTION_REASONING}" + \
                               f" - TRANS{self.TRANSLATION_REASONING}" + \
                               f" - GLEXT{self.GLOSSARY_EXTRACTION_REASONING}"

            
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
# PROMPTORS
############################################################################################


    def punctuate(self, i, text):

        preceding_section = text.segments[i-1] if i > 0 else None
        preceding_punctuated = text.punctuated_segments[i-1] if i > 0 else None
        following_section = text.segments[i+1] if i < len(text.segments)-1 else None
      
        conversation_history = ""
        if preceding_section:
            conversation_history = (conversation_history +
                                    "Preceding segment:\n" +
                                    preceding_section +
                                    "\n\nPreceding segment punctuated:\n" +
                                    preceding_punctuated)
            
        conversation_history += f"\n\n\nCurrent segment:\n{text.segments[i]}"

        if following_section:
            conversation_history = (conversation_history + "\n\n\n" +
                                    "Following segment:\n" +
                                    following_section)
        
        print(text.segments[i])
        
        
        attempts = 0
        response_is_uncorrupted = False
        
        while response_is_uncorrupted == False and attempts < 3:
            response = self.client.responses.create(
                    model = self.PUNCTUATION_MODEL,
                    input=[
                        {
                            "role": "developer",
                            "content": self.PUNCTUATION_INSTRUCTIONS
                        },
                        {
                            "role": "user", 
                            "content": conversation_history
                        }],
                    reasoning={"effort": self.PUNCTUATION_REASONING},
                    text={"verbosity": self.PUNCTUATION_VERBOSITY},
                    temperature = self.PUNCTUATION_TEMPERATURE
                    )         

            punctuated_text = response.output_text

            print(punctuated_text + "\n")

            attempts += 1

            # Ensure no original Chinese character was corrupted:
            if text_manipulators.strip_punctuation(text.segments[i]) == text_manipulators.strip_punctuation(punctuated_text):
                response_is_uncorrupted = True

        if response_is_uncorrupted == False:
            raise ValueError("GPT's response corrupted the original text.")
        
        
        return punctuated_text
    

############################################################################################


    def select_glossary(self,
                    current_section, preceding_section = None, following_section = None):

        comb_instructions = (self.GLOSSARY_SELECTION_INSTRUCTIONS)
       
        conversation_history = ""
        if preceding_section:
            conversation_history = (conversation_history +
                                    "Preceding segment:\n" +
                                    preceding_section)

        conversation_history += f"\n\n\nCurrent segment:\n{current_section}"


        if following_section:
            conversation_history = (conversation_history + "\n\n\n" +
                                    "Following segment:\n" +
                                    following_section)

        print(current_section + "\n")
        

        response = self.client.responses.create(
                model = self.GLOSSARY_SELECTION_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": comb_instructions
                    },
                    {
                        "role": "user", 
                        "content": conversation_history
                    }],
                reasoning={"effort": self.GLOSSARY_SELECTION_REASONING},
                text={"verbosity": self.GLOSSARY_SELECTION_VERBOSITY},
                temperature = self.GLOSSARY_SELECTION_TEMPERATURE
                )         

        selection_of_terms = response.output_text


        print(selection_of_terms + "\n")
        
        
        return selection_of_terms


############################################################################################


    def translate(self, i, text):

        preceding_section = text.versified_segments[i-1] if i > 0 else None
        preceding_translation = text.translated_segments[i-1] if i > 0 else None
        following_section = text.versified_segments[i+1] \
                                        if i < len(text.versified_segments)-1 else None
                                                            

        stylized_glossary = stylize_glossary(text.segment_glossaries[i])
        
        comb_instructions = (self.TRANSLATION_INSTRUCTIONS +
                             "\n\nUse the glossary below (if applicable):\n" +
                             stylized_glossary)
        
        if text.chinese_title and text.translated_title:
            conversation_history = \
                    f"Title: {text.chinese_title}\nTranslation: {text.translated_title}\n\n"
        else:
            conversation_history = ""
            
        if preceding_section:
            conversation_history = (conversation_history +
                                    "Preceding segment:\n" +
                                    preceding_section)
        if preceding_translation:
            conversation_history = (conversation_history + "\n\n" +
                                    "Preceding segment translation:\n" +
                                    preceding_translation)

        conversation_history += f"\n\n\nCurrent segment:\n{text.versified_segments[i]}"
        
        if following_section:
            conversation_history = (conversation_history + "\n\n\n" +
                                    "Following segment:\n" +
                                    following_section)
            
            
        print(stylized_glossary + "\n\n" + text.versified_segments[i] + "\n")
        

        response = self.client.responses.create(
                model = self.TRANSLATION_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": comb_instructions
                    },
                    {
                        "role": "user", 
                        "content": conversation_history
                    }],
                reasoning={"effort": self.TRANSLATION_REASONING},
                text={"verbosity": self.TRANSLATION_VERBOSITY},
                temperature = self.TRANSLATION_TEMPERATURE
                )         

        translation = response.output_text

              
        print(translation + "\n")

        return translation


############################################################################################

    def cross_examine(self, i, text):

        texts_and_translations = ("Segment A:\n" \
                                + text.versified_segments[i-1] \
                                + "\n\n" \
                                + "Segment A translation:\n" \
                                + text.translated_segments[i-1] \
                                + "\n\n\n" \
                                + "Segment B:\n" \
                                + text.versified_segments[i] \
                                + "\n\n" \
                                + "Segment B translation:\n" \
                                + text.translated_segments[i])

        print(texts_and_translations)

        response = self.client.responses.create(
                model = self.CROSS_EXAMINATION_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": self.CROSS_EXAMINATION_INSTRUCTIONS
                    },
                    {
                        "role": "user", 
                        "content": texts_and_translations
                    }],
                reasoning={"effort": self.CROSS_EXAMINATION_REASONING},
                text={"verbosity": self.CROSS_EXAMINATION_VERBOSITY},
                temperature = self.CROSS_EXAMINATION_TEMPERATURE
                )         

        corrected_segment = response.output_text

        print(corrected_segment + "\n")

        return corrected_segment if corrected_segment.strip()!= "N/A" else None

        


############################################################################################


    def extract_glossary(self, i, text):

        preceding_section = text.versified_segments[i-1] if i>0 else None
        preceding_translation = text.finalized_segments[i-1] if i>0 else None
        following_section = text.versified_segments[i+1] \
                                    if i<len(text.versified_segments)-1 else None

        
        text_and_translation = ("Current segment:\n" \
                                + text.versified_segments[i] \
                                + "\n\n" \
                                + "Current segment translation:\n" \
                                + text.finalized_segments[i])


        conversation_history = ""
        
        if preceding_section:
            conversation_history = ("Preceding segment:\n" + preceding_section)
        if preceding_translation:
            conversation_history = (conversation_history + "\n\n" +
                                    "Preceding segment translation:\n" +
                                    preceding_translation)

        conversation_history = conversation_history + "\n\n\n" + text_and_translation
        
        if following_section:
            conversation_history = (conversation_history + "\n\n\n" +
                                    "Following segment:\n" +
                                    following_section)

        response = self.client.responses.create(
                model = self.GLOSSARY_EXTRACTION_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": self.GLOSSARY_EXTRACTION_INSTRUCTIONS
                    },
                    {
                        "role": "user", 
                        "content": conversation_history
                    }],
                reasoning={"effort": self.GLOSSARY_EXTRACTION_REASONING},
                text={"verbosity": self.GLOSSARY_EXTRACTION_VERBOSITY},
                temperature = self.GLOSSARY_EXTRACTION_TEMPERATURE
                )         

        glossary_text = response.output_text

        
        print(glossary_text + "\n")


        return destylize_glossary(glossary_text)


############################################################################################


    def translate_title(self, temp_glossary, title):
            
        stylized_glossary = stylize_glossary(temp_glossary)
        
        comb_instructions = (self.TITLE_TRANSLATION_INSTRUCTIONS +
                             "\n\nUse the glossary below (if applicable):\n" +
                             stylized_glossary)


        print(stylized_glossary + "\n\n" + title + "\n")
        

        response = self.client.responses.create(
                model = self.TITLE_TRANSLATION_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": comb_instructions
                    },
                    {
                        "role": "user", 
                        "content": title
                    }],
                reasoning={"effort": self.TITLE_TRANSLATION_REASONING},
                text={"verbosity": self.TITLE_TRANSLATION_VERBOSITY},
                temperature = self.TITLE_TRANSLATION_TEMPERATURE
                )         

        translated_title = response.output_text

        
        print(translated_title + "\n\n" + title + "\n")

        return translated_title

        


    def extract_glossary_from_title(self, text):
        
        text_and_translation = ("Chinese original:\n" + text.chinese_title + "\n\n" +
                                "English translation:\n" + text.translated_title)
        
        response = self.client.responses.create(
                model = self.GLOSSARY_EXTRACTION_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": self.GLOSSARY_EXTRACTION_INSTRUCTIONS
                    },
                    {
                        "role": "user", 
                        "content": text_and_translation
                    }],
                reasoning={"effort": self.GLOSSARY_EXTRACTION_REASONING},
                text={"verbosity": self.GLOSSARY_EXTRACTION_VERBOSITY},
                temperature = self.GLOSSARY_EXTRACTION_TEMPERATURE
                )         

        glossary_text = response.output_text
        
        print(glossary_text + "\n")

        return destylize_glossary(glossary_text)
    

############################################################################################

