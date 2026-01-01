############################################################################################
############################################################################################
############################################################################################
### INSTRUCTIONS PROFILE CLASS
############################################################################################
############################################################################################
############################################################################################


from openai import OpenAI

from glossary_dictate import *

from text_manipulators import *

from instruction_prompts import *


############################################################################################


class PromptEngine:


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
        self.punctuation_GPT_temperature = 0
                
        self.glossary_selection_instructions = glossary_selection_instructions
        self.glossary_selection_GPT_model = "gpt-5.1"
        self.glossary_selection_GPT_reasoning = "none"
        self.glossary_selection_GPT_verbosity = "high"
        self.glossary_selecion_GPT_temperature = 0
        
        self.translation_instructions = translation_instructions
        self.translation_GPT_model = "gpt-5.1"
        self.translation_GPT_reasoning = "none"
        self.translation_GPT_verbosity = "low"
        self.translation_GPT_temperature = 0
        
        self.title_translation_instructions = title_translation_instructions
        self.title_translation_GPT_model = "gpt-5.1"
        self.title_translation_GPT_reasoning = self.translation_GPT_reasoning
        self.title_translation_GPT_verbosity = "low"
        self.title_translation_GPT_temperature = 0

        self.glossary_extraction_instructions = glossary_extraction_instructions
        self.glossary_extraction_GPT_model = "gpt-5.1"
        self.glossary_extraction_GPT_reasoning = "none"
        self.glossary_extraction_GPT_verbosity = "high"
        self.glossary_extraction_GPT_temperature = 0
        

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
                    model = self.punctuation_GPT_model,
                    input=[
                        {
                            "role": "developer",
                            "content": self.punctuation_instructions
                        },
                        {
                            "role": "user", 
                            "content": conversation_history
                        }],
                    reasoning={"effort": self.punctuation_GPT_reasoning},
                    text={"verbosity": self.punctuation_GPT_verbosity},
                    temperature = self.punctuation_GPT_temperature
                    )         

            punctuated_text = response.output_text

            print(punctuated_text + "\n")

            attempts += 1

            # Ensure no original Chinese character was corrupted:
            if strip_punctuation(text.segments[i]) == strip_punctuation(punctuated_text):
                response_is_uncorrupted = True

        if response_is_uncorrupted == False:
            raise ValueError("GPT's response corrupted the original text.")
        
        
        return punctuated_text
    


############################################################################################


    def select_glossary(self,
                    current_section, preceding_section = None, following_section = None):

        comb_instructions = (self.glossary_selection_instructions)
       
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
                model = self.glossary_selection_GPT_model,
                input=[
                    {
                        "role": "developer",
                        "content": comb_instructions
                    },
                    {
                        "role": "user", 
                        "content": conversation_history
                    }],
                reasoning={"effort": self.glossary_selection_GPT_reasoning},
                text={"verbosity": self.glossary_selection_GPT_verbosity},
                temperature = self.glossary_selecion_GPT_temperature
                )         

        selection_of_terms = response.output_text


        print(selection_of_terms + "\n")
        
        
        return selection_of_terms


############################################################################################


    def translate(self, i, text):

        preceding_section = text.punctuated_segments[i-1] if i>0 else None
        preceding_translation = text.translated_segments[i-1] if i>0 else None
        following_section = text.punctuated_segments[i+1] \
                                        if i<len(text.punctuated_segments)-1 else None
                                                            

        stylized_glossary = stylize_glossary(text.segment_glossaries[i])
        
        comb_instructions = (self.translation_instructions +
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

        conversation_history += f"\n\n\nCurrent segment:\n{text.punctuated_segments[i]}"
        
        if following_section:
            conversation_history = (conversation_history + "\n\n\n" +
                                    "Following segment:\n" +
                                    following_section)
            
            
        print(stylized_glossary + "\n\n" + text.punctuated_segments[i] + "\n")
        

        response = self.client.responses.create(
                model = self.translation_GPT_model,
                input=[
                    {
                        "role": "developer",
                        "content": comb_instructions
                    },
                    {
                        "role": "user", 
                        "content": conversation_history
                    }],
                reasoning={"effort": self.translation_GPT_reasoning},
                text={"verbosity": self.translation_GPT_verbosity},
                temperature = self.translation_GPT_temperature
                )         

        translation = response.output_text

              
        print(translation + "\n")

        return translation


############################################################################################


    def extract_glossary(self, i, text):

        preceding_section = text.punctuated_segments[i-1] if i>0 else None
        preceding_translation = text.translated_segments[i-1] if i>0 else None
        following_section = text.punctuated_segments[i+1] \
                                    if i<len(text.punctuated_segments)-1 else None

        
        text_and_translation = ("Current segment:\n" + text.punctuated_segments[i] + "\n\n" +
                                "Current segment translation:\n" + text.translated_segments[i])


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
                model = self.glossary_extraction_GPT_model,
                input=[
                    {
                        "role": "developer",
                        "content": self.glossary_extraction_instructions
                    },
                    {
                        "role": "user", 
                        "content": conversation_history
                    }],
                reasoning={"effort": self.glossary_extraction_GPT_reasoning},
                text={"verbosity": self.glossary_extraction_GPT_verbosity},
                temperature = self.glossary_extraction_GPT_temperature
                )         

        glossary_text = response.output_text

        
        print(glossary_text + "\n")


        return destylize_glossary(glossary_text)


############################################################################################


    def translate_title(self, temp_glossary, title):
            
        stylized_glossary = stylize_glossary(temp_glossary)
        
        comb_instructions = (self.title_translation_instructions +
                             "\n\nUse the glossary below (if applicable):\n" +
                             stylized_glossary)


        print(stylized_glossary + "\n\n" + title + "\n")
        

        response = self.client.responses.create(
                model = self.title_translation_GPT_model,
                input=[
                    {
                        "role": "developer",
                        "content": comb_instructions
                    },
                    {
                        "role": "user", 
                        "content": title
                    }],
                reasoning={"effort": self.title_translation_GPT_reasoning},
                text={"verbosity": self.title_translation_GPT_verbosity},
                temperature = self.title_translation_GPT_temperature
                )         

        translated_title = response.output_text

        
        print(translated_title + "\n\n" + title + "\n")

        return translated_title

        


    def extract_glossary_from_title(self, text):
        
        text_and_translation = ("Chinese original:\n" + text.chinese_title + "\n\n" +
                                "English translation:\n" + text.translated_title)
        
        response = self.client.responses.create(
                model = self.glossary_extraction_GPT_model,
                input=[
                    {
                        "role": "developer",
                        "content": self.glossary_extraction_instructions
                    },
                    {
                        "role": "user", 
                        "content": text_and_translation
                    }],
                reasoning={"effort": self.glossary_extraction_GPT_reasoning},
                text={"verbosity": self.glossary_extraction_GPT_verbosity},
                temperature = self.glossary_extraction_GPT_temperature
                )         

        glossary_text = response.output_text
        
        print(glossary_text + "\n")

        return destylize_glossary(glossary_text)
    

############################################################################################

