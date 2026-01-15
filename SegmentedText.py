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
        self.original_title = original_title if original_title else "Untitled"
        self.translated_title = translated_title if translated_title\
                                                    else "Untranslated Title"
        self.properties = []
        
        self.page_labels = []
        self.translation_glossary = {}
        self.punctuated_segments = []
        self.mended_segments = []
        self.segment_breaches = []
        self.verse_lists = []
        self.versified_segments = []
        self.translated_segments = []
        self.segment_glossaries = []

        self.number_of_completed_segments = 0
        
        self.model_settings = ""
        
                                    
    def full_title(self):
        fulltitle = \
            f"{self.original_title} - {self.translated_title}"
        return fulltitle

                
    def translation_to_docx(self):
        # Check if the KanripoText instance is eady to be printed:
        if self.number_of_completed_segments > 0:
            scribe_translation_to_word_document(self)
        else:
            print(f"Error: There are no translated segments.")


############################################################################################
