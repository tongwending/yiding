############################################################################################
############################################################################################
############################################################################################
### THE KANRIPO TEXT CLASS
############################################################################################
############################################################################################
############################################################################################

# Standard libraries:
import pickle

# Cauldron modules:
from kanripo_fetch import fetch_from_kanripo
from glossary_dictate import *
from PromptEngine import PromptEngine



############################################################################################

class KanripoText:
    

    def __init__(self, kanripo_code: str, prompt_engine = None):

        self.kanripo_code = kanripo_code

        self.chinese_title, self.properties, self.page_labels, self.segments = \
                                                    fetch_from_kanripo(self.kanripo_code)
        self.prompt_engine = PromptEngine() if prompt_engine is None else prompt_engine
        
        self.translated_title = "Untranslated Title"
        

        # Inquisition attributes:
        self.cites = []
        for i in range(0, len(self.page_labels)):
            self.cites.append(f"{self.kanripo_code} {self.page_labels[i]}")
        self.citelogs = []

        
        # Translation attributes:
        self.translation_glossary = {}
        self.punctuated_segments = []
        self.segment_glossaries = []
        self.translated_segments = []
        self.number_of_completed_segments = 0
        

        save_as_pickle(f"{self.kanripo_code} {self.chinese_title}.pkl")
        

    def resume_translation(self):

        if self.translated_title == "Untranslated Title":
            self.translate_title()
        
        for i in range(self.number_of_completed_segments, len(self.segments)):

            print(f"\n{self.page_labels[i]}\n")

            #punctuate (if not already punctuated):
            if i == 0 and len(self.punctuated_segments) == 0:
                self.punctuated_segments.append(self.prompt_engine.punctuate(i, self))
            if i < len(self.segments)-1 and len(self.punctuated_segments) == i+1:
                self.punctuated_segments.append(self.prompt_engine.punctuate(i+1, self))                           
            
            #create_glossaries:
        
            segment_glossary = {}

            pre_segment =self.punctuated_segments[i-1] if i > 0 else None
            fol_segment =self.punctuated_segments[i+1] if i < len(self.segments)-1 else None


            selection_text = self.prompt_engine.select_glossary(self.punctuated_segments[i],
                                                    preceding_section = pre_segment,
                                                    following_section = fol_segment)

            for term in selection_text.splitlines():
                    if term in self.prompt_engine.glossary:
                           segment_glossary[term] = self.prompt_engine.glossary[term]
                
            self.segment_glossaries.append(segment_glossary)
            
            # translate:
        
            self.translated_segments.append(self.prompt_engine.translate(i, self))

            # extract_glossary:
        
            extracted_glossary = self.prompt_engine.extract_glossary(i, self)
            update_glossary(self.prompt_engine.glossary, extracted_glossary)
            update_glossary(self.translation_glossary, extracted_glossary)

            # save progress:
            self.number_of_completed_segments +=1
            save_as_pickle(f"{self.full_title()} - Translation.pkl")


    def translate_title(self):
        

        selection_text = self.prompt_engine.select_glossary(self.chinese_title)
        
        title_glossary = {}
        for term in selection_text.splitlines():
                if term in self.prompt_engine.glossary:
                       title_glossary[term] = self.prompt_engine.glossary[term]

        self.translated_title = self.prompt_engine.translate_title(title_glossary,
                                                                  self.chinese_title)

        glossary_additions = self.prompt_engine.extract_glossary_from_title(self, self.translated_title)
        update_glossary(self.prompt_engine.glossary, glossary_additions)
        update_glossary(self.translation_glossary, glossary_additions)
                                    

    def full_title(self):
        fulltitle = \
            f"{self.kanripo_code} {self.chinese_title} - {self.prompt_engine.title_extension}"
        return fulltitle

    
    def save_as_pickle(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(obj, f)

            
    def translation_to_docx(self):
        # Check if the KanripoText instance is eady to be printed:
        if self.number_of_completed_segments > 0:
            scribe_translation_to_word_document(self)
        else:
            print(f"Error: There are no translated segments.")


    def glossary_to_csv(self): # This function is not used now but might be handy later.
        glossaryfile = self.full_title() + " - Glossary.csv"
        with open(glossaryfile, "w", encoding="utf-8") as file:
            for key, value in self.translation_glossary.items():
                file.write(f"{key},{value[0]}")
                for translation in value[1]:
                    file.write(f",{translation}")
                file.write("\n")

