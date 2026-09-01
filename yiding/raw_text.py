# ------------------------------------------------------------------------------------------
# raw_text
# ------------------------------------------------------------------------------------------

from .segmented_text import SegmentedText

# ------------------------------------------------------------------------------------------


class RawText(SegmentedText):
    
    def __init__(self, text: str,
                 divider: str, keep_divider = False, divider_is_whole_line = False,
                 original_title = None, translated_title = None,
                 structured = False, punctuated = False):

        super().__init__()

        if original_title:
            self.original_title = original_title
        if translated_title:
            self.translated_title = translated_title

        self.segments = slice_into_segments(text,
                                            divider,
                                            keep_divider,
                                            divider_is_whole_line)
        
        if structured:
            self.is_structured = True
            self.unpunctuated_segments = self.segments
        if punctuated:
            self.is_punctuated = True
            self.punctuated_segments = self.segments
        
# ------------------------------------------------------------------------------------------

def slice_into_segments(text: str,
                        divider: str,
                        keep_divider = False,
                        divider_is_whole_line = False):

    sections = [] # This is going to be the end product: a list of Chinese sections.
    current_section = []

    # This loop goes through the text line by line
    # searching for brackets to define the divisions.
    for line in text.splitlines(True):
        if divider in line:

            if divider_is_whole_line:
                
                # Saves the previous section if it exists.
                if current_section:
                    sections.append(''.join(current_section))
                    current_section = []
                if keep_divider:
                    current_section.append(line)
            else:
                left, div, right = line.partition(divider)
                if left:
                    current_section.append(left)
                if current_section:
                    sections.append(''.join(current_section))
                current_section = []
                
                if keep_divider:
                    right = div + right
                if right:
                    current_section.append(right)                    
                
        else:
            current_section.append(line)
        
    # Adds the last section if the file didn't end with a new section.
    if current_section:
        sections.append(''.join(current_section))
                
    return sections

# ------------------------------------------------------------------------------------------
