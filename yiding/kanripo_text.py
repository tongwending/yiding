# ------------------------------------------------------------------------------------------
# kanripo_text
# ------------------------------------------------------------------------------------------

import kanripo

from .segmented_text import SegmentedText
from . import text_manipulators

# ------------------------------------------------------------------------------------------

PARSING_ERROR_MESSAGE = "nonexistent or unknown Kanripo documentation"
KANRIPO_ERROR = "404: Not Found"

# ------------------------------------------------------------------------------------------

class KanripoText(SegmentedText):
    
    def __init__(self, kanripo_code: str, glosses_on = True):

        super().__init__()

        self.kanripo_code = kanripo_code
        self.glosses_on = glosses_on

        self.fetch_and_parse() # fills title, properties, segments, page_labels

        for x in self.segments:
            self.page_lines.append(x.count("\n"))

        if not self.glosses_on:
            for i in range(0, len(self.segments)):
                segment, glosslist = text_manipulators.pop_glosses(self.segments[i])
                self.segments[i] = segment
                self.glosses.append(glosslist)
                                    
    def full_title(self): # needs reworkings
        fulltitle = (f"{self.kanripo_code} - {self.original_title}"\
                     + (f" - {self.translated_title}" if self.translated_title else ""))
        return fulltitle

    def fetch_and_parse(self):

        raw_juan = self.fetch_segments()

        if not raw_juan:
            raise ValueError(f"Error: Code {self.kanripo_code} is {PARSING_ERROR_MESSAGE}.")

        else:
            self.original_title = detect_title(raw_juan[0])
            self.properties = detect_properties(raw_juan[0])

            for i in range(0, len(raw_juan)):
                sectioned_juan, page = slice_into_sections(raw_juan[i])
                if sectioned_juan and page:
                    for j in range(0, len(sectioned_juan)):
                        self.segments.append(sectioned_juan[j])
                        self.page_labels.append(page[j])

    def fetch_segments(self):

        list_of_juan = []
        self._update_log(f"Kanripo code: {self.kanripo_code}\n")

        i = 0
        misfetches = 0
        while True:
            
            kanripo_juan_code = f"{self.kanripo_code}_{i:03d}"
            self._update_log(f"\nFetching {kanripo_juan_code}\n")
            
            fetched_juan = kanripo.get_result_file(kanripo_juan_code)
            if not isinstance(fetched_juan, str):    # must be string
                raise ValueError(f"Error: Something wrong, {PARSING_ERROR_MESSAGE}.")

            self._update_log(f"{fetched_juan}\n")

            # Should loop end when there are no more valid fetches.
            if fetched_juan == KANRIPO_ERROR:
                break
            
            if "<pb:" in fetched_juan:
                list_of_juan.append(fetched_juan)
                misfetches = 0
            else:
                misfetches += 1
                # Maybe 2 fetches could be empty because of content fetches (but 3 is too much).
                if misfetches == 3:
                    raise ValueError(f"Error: Something is {PARSING_ERROR_MESSAGE}.")
            i += 1
                
        for i in range(0,len(list_of_juan)):
            list_of_juan[i] = list_of_juan[i].replace("¶", "")
            
        return list_of_juan

# ------------------------------------------------------------------------------------------
# parsers
# ------------------------------------------------------------------------------------------

def slice_into_sections(text):

    sections = [] # This is going to be the end product: a list of Chinese sections.
    current_section = []
    real_text = False

    # This loop goes through the text line by line
    # searching for brackets to define the divisions.
    for line in text.splitlines(True):
        if line.startswith('<pb:'):
            real_text = True
            # Saves the previous section if it exists.
            if current_section:
                sections.append(''.join(current_section))
                current_section = []
        if real_text == True:
            current_section.append(line)
        
    # Adds the last section if the file didn't end with a new section.
    if current_section:
        sections.append(''.join(current_section))

    page_labels = []
    for i in range(0, len(sections)):
        first_line, new_line, rest_of_text = sections[i].partition("\n")
        page_labels.append(detect_page(first_line))
        sections[i] = rest_of_text
                
    return sections, page_labels

# ------------------------------------------------------------------------------------------

def detect_title(text):

    title = "Unknown Title"

    for line in text.splitlines():
        if line.startswith("#+TITLE: "):
            title = line[len("#+TITLE: "):]
            break

    return title

# ------------------------------------------------------------------------------------------

def detect_properties(text):

    properties = []

    for line in text.splitlines():
        if line.startswith("#+PROPERTY: "):
            properties.append(line[len("#+PROPERTY: "):].strip())

    return properties

# ------------------------------------------------------------------------------------------

def detect_page(line):

    final_form = line

    if len(line)>24:

        try:
            segment = int(line[17:20])  # won't work with unknow Kanripo documentation
            segment_format = f"{segment}." if segment > 0 else ""
            page = int(line[21:24])     # won't work with unknow Kanripo documentation
            side = line[24]
        except (ValueError, IndexError):
            raise ValueError(f"Error: Label is {PARSING_ERROR_MESSAGE}.")

        final_form = f"{segment_format}{page}{side}"

    return final_form

# ------------------------------------------------------------------------------------------
