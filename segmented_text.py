############################################################################################
############################################################################################
############################################################################################
### THE SEGMENTED TEXT CLASS
############################################################################################
############################################################################################
############################################################################################


############################################################################################


class SegmentedText:
    
    def __init__(self, segments = None, original_title = None, translated_title = None):

        self.segments = [] if segments is None else segments
        self.original_title = original_title if original_title else None
        self.translated_title = translated_title if translated_title else None
        self.properties = []
        
        self.page_labels = []
        self.translation_glossary = {}
        self.punctuated_segments = []
        self.translated_segments = []
        self.segment_glossaries = []

        self.is_punctuated = False
        self.working_segment = [0, ""]
        
        self.model_settings = ""
        
                                    
    def full_title(self):
        fulltitle = (self.original_title if self.original_title else "Untitled")\
                  + (f"- {self.translated_title}" if self.translated_title else "")
        return fulltitle

                
    def translation_to_docx(self):
        # Check if the KanripoText instance is eady to be printed:
        if len(self.translated_segments) > 0:
            scribe_translation_to_word_document(self)
        else:
            print(f"Error: There are no translated segments.")


############################################################################################
