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
import text_manipulators



############################################################################################

class KanripoText:
    

    def __init__(self, kanripo_code: str, prompt_engine = None):

        self.kanripo_code = kanripo_code

        self.chinese_title, self.properties, self.page_labels, self.segments = \
                                                    fetch_from_kanripo(self.kanripo_code)
        self.prompt_engine = PromptEngine() if prompt_engine is None else prompt_engine
        
        self.translated_title = "Untranslated Title"
        
        self.translation_glossary = {}
        self.punctuated_segments = []
        self.mended_segments = []
        self.segment_breaches = []
        self.verse_lists = []
        self.versified_segments = []
        self.segment_glossaries = []
        self.translated_segments = []
        self.cross_examined_segments = []
        self.finalized_segments = []
        self.number_of_completed_segments = 0

        # save the initialized instance
        self.save_as_pickle(f"{self.kanripo_code} {self.chinese_title}.pkl")
        

    def resume_translation(self):

        if self.translated_title == "Untranslated Title":
            self.translate_title()
        
        for i in range(self.number_of_completed_segments, len(self.segments)):

            print(f"\n{self.page_labels[i]}\n")

            # punctuate the first three segments (if not punctuated already):
            for j in (0, 1, 2):     # After first iteration, only j = 2 will run.
                if  len(self.punctuated_segments) == i+j and len(self.segments) > i+j:
                    self.punctuated_segments.append(self.prompt_engine.punctuate(i+j, self))

            # restore broken sentence on segments' borders:
            if i == 0 and len(self.punctuated_segments)>=2: # first segment
                a, b, c = text_manipulators.mend_last_sentence(self.punctuated_segments[i],
                                                               self.punctuated_segments[i+1])
                self.mended_segments.append(a)
                self.mended_segments.append(b)
                self.segment_breaches.append(c)
            elif i ==0 and len(self.punctuated_segments)==1:
                self.mended_segments.append(self.punctuated_segments[i])

            if i < len(self.punctuated_segments)-2:
                a, b, c = text_manipulators.mend_last_sentence(self.mended_segments[i+1],
                                                               self.punctuated_segments[i+2])
                self.mended_segments[i+1] = a
                self.mended_segments.append(b)
                self.segment_breaches.append(c)
                    
            if i == len(self.segments)-1:   # last segment
                self.segment_breaches.append(None)
                
            # create lists of verses (a.k.a. numbered sentences):
            for j in (0, 1):     # After first iteration, only j = 1 will run.
                if  len(self.verse_lists) == i+j and len(self.mended_segments) > i+j:
                    self.verse_lists.append(text_manipulators.break_to_verses(self.mended_segments[i+j]))
                    # then put the verses together in a versified segment:
                    self.versified_segments.append(text_manipulators.glue_verses(self.verse_lists[i+j]))
                    
            # create_glossaries:
        
            segment_glossary = {}

            pre_segment =self.mended_segments[i-1] if i > 0 else None
            fol_segment =self.mended_segments[i+1] if i < len(self.punctuated_segments)-1 \
                                                    else None

            selection_text = self.prompt_engine.select_glossary(self.mended_segments[i],
                                                    preceding_section = pre_segment,
                                                    following_section = fol_segment)

            for term in selection_text.splitlines():
                    if term in self.prompt_engine.glossary:
                           segment_glossary[term] = self.prompt_engine.glossary[term]
                
            self.segment_glossaries.append(segment_glossary)
            
            # translate:
        
            self.translated_segments.append(self.prompt_engine.translate(i, self))

            # cross examine:
            
            if i ==0:
                self.cross_examined_segments.append(None)
            else:
                self.cross_examined_segments.append(self.prompt_engine.cross_examine(i,self))

            # finalize translation:
            
            if self.cross_examined_segments[i] is None:
                self.finalized_segments.append(self.translated_segments[i])
            else:
                self.finalized_segments.append(self.cross_examined_segments[i])
            
            # extract_glossary:
        
            extracted_glossary = self.prompt_engine.extract_glossary(i, self)
            update_glossary(self.prompt_engine.glossary, extracted_glossary)
            update_glossary(self.translation_glossary, extracted_glossary)

            # save progress:
            self.number_of_completed_segments +=1
            self.save_as_pickle(f"{self.full_title()} - Translation.pkl")


    def translate_title(self):
        

        selection_text = self.prompt_engine.select_glossary(self.chinese_title)
        
        title_glossary = {}
        for term in selection_text.splitlines():
                if term in self.prompt_engine.glossary:
                       title_glossary[term] = self.prompt_engine.glossary[term]

        self.translated_title = self.prompt_engine.translate_title(title_glossary,
                                                                  self.chinese_title)

        glossary_additions = self.prompt_engine.extract_glossary_from_title(self)
        update_glossary(self.prompt_engine.glossary, glossary_additions)
        update_glossary(self.translation_glossary, glossary_additions)
                                    

    def full_title(self):
        fulltitle = \
            f"{self.kanripo_code} {self.chinese_title} - {self.prompt_engine.title_extension}"
        return fulltitle

    
    def save_as_pickle(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self, f)

            
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

