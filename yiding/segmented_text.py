# ------------------------------------------------------------------------------------------
# segmented_text
# ------------------------------------------------------------------------------------------



class SegmentedText:
    
    def __init__(self):
        
        self.original_title = None
        self.translated_title = None
        self.translation_language = None
        self.properties = []
        self.settings = {}
        
        self.segments = []
        self.unpunctuated_segments = []
        self.punctuated_segments = []
        self.translated_segments = []
        
        self.page_labels = [] # Labels of the segments/facsimiles
        self.page_lines = []
        self.segment_labels = []
        
        self.glosses = []
        self.punctuated_glosses = []
        
        self.translation_glossary = {}
        self.new_glossary = {}
        self.extracted_terms = {}
        self.extracted_glossary = {}

        self.working_i = 0
        self.working_text = ""
        self.working_labels = []
        self.translation_i = 0
        self.term_extraction_i = 0
        self.glossary_extraction_i = 0
        
        self.log = ""

        self.is_structured = False # True means it is divided into meaningful sections.
        self.is_punctuated = False
        self.is_translated = False
        self.is_term_extracted = False
        self.is_glossary_extracted = False
                                    
    def full_title(self):
        fulltitle = (self.original_title if self.original_title else "Untitled")\
                  + (f" - {self.translated_title}" if self.translated_title else "")
        return fulltitle

    def empty_translation(self, empty_title = True):
        self.translation_i = 0
        self.translated_segments = []
        self.translation_glossary = {}
        self.new_glossary = {}
        self.is_translated = False
        self.translation_language = None

        self.glossary_extraction_i = 0
        self.extracted_glossary = {}
        self.is_glossary_extracted = False
        
        if empty_title:
            self.translated_title = None

    def _update_log(self, text):
        self.log += f"{text}\n"
        print(text)
            
# ------------------------------------------------------------------------------------------
