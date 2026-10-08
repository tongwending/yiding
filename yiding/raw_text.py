# ------------------------------------------------------------------------------------------
# raw_text
# ------------------------------------------------------------------------------------------

from .segmented_text import SegmentedText

# ------------------------------------------------------------------------------------------


class RawText(SegmentedText):
    
    def __init__(
            self,
            unpunctuated_text = None,
            unpunctuated_divider = None,
            unpunctuated_keep_divider = False,
            unpunctuated_divider_is_whole_line = False,

            punctuated_text = None,
            punctuated_divider = None,
            punctuated_keep_divider = False,
            punctuated_divider_is_whole_line = False,

            translated_text = None,
            translation_divider = None,
            translation_keep_divider = False,
            translation_divider_is_whole_line = False,

            original_title = None,
            translated_title = None,
            translation_language = None,
            structured = False,
            ):

        super().__init__()

        # ------------------------------------------------------------------
        # titles / translation language
        # ------------------------------------------------------------------

        if original_title:
            self.original_title = original_title

        if translated_title:
            self.translated_title = translated_title

        if translation_language:
            self.translation_language = translation_language

        # ------------------------------------------------------------------
        # preserve the raw-text segmentation settings
        # ------------------------------------------------------------------

        self.unpunctuated_divider = unpunctuated_divider
        self.unpunctuated_keep_divider = unpunctuated_keep_divider
        self.unpunctuated_divider_is_whole_line = (
            unpunctuated_divider_is_whole_line
        )

        self.punctuated_divider = punctuated_divider
        self.punctuated_keep_divider = punctuated_keep_divider
        self.punctuated_divider_is_whole_line = (
            punctuated_divider_is_whole_line
        )

        self.translation_divider = translation_divider
        self.translation_keep_divider = translation_keep_divider
        self.translation_divider_is_whole_line = (
            translation_divider_is_whole_line
        )

        # ------------------------------------------------------------------
        # unpunctuated text
        # ------------------------------------------------------------------

        if unpunctuated_text is not None:

            if unpunctuated_divider is None:
                raise ValueError(
                    "Unpunctuated text requires a segment delimiter."
                )

            self.segments = slice_into_segments(
                unpunctuated_text,
                unpunctuated_divider,
                unpunctuated_keep_divider,
                unpunctuated_divider_is_whole_line,
            )

            if structured:
                self.is_structured = True
                self.unpunctuated_segments = list(
                    self.segments
                )

        # ------------------------------------------------------------------
        # punctuated text
        # ------------------------------------------------------------------

        if punctuated_text is not None:

            if punctuated_divider is None:
                raise ValueError(
                    "Punctuated text requires a segment delimiter."
                )

            self.punctuated_segments = slice_into_segments(
                punctuated_text,
                punctuated_divider,
                punctuated_keep_divider,
                punctuated_divider_is_whole_line,
            )

            self.is_punctuated = True

        # ------------------------------------------------------------------
        # translation
        # ------------------------------------------------------------------

        if translated_text is not None:

            if translation_divider is None:
                raise ValueError(
                    "Translation requires a segment delimiter."
                )

            self.translated_segments = slice_into_segments(
                translated_text,
                translation_divider,
                translation_keep_divider,
                translation_divider_is_whole_line,
            )

            self.translation_i = len(
                self.translated_segments
            )

            self.is_translated = True
    
        # ------------------------------------------------------------------
        # alignment checks
        # ------------------------------------------------------------------

        if (
            self.punctuated_segments
            and self.translated_segments
            and len(self.punctuated_segments)
            != len(self.translated_segments)
        ):
            raise ValueError(
                "Punctuated text and translation have "
                "different numbers of segments."
            )

        if self.is_structured:

            if (
                self.punctuated_segments
                and len(self.unpunctuated_segments)
                != len(self.punctuated_segments)
            ):
                raise ValueError(
                    "Unpunctuated and punctuated text have "
                    "different numbers of segments."
                )

            if (
                self.translated_segments
                and len(self.unpunctuated_segments)
                != len(self.translated_segments)
            ):
                raise ValueError(
                    "Unpunctuated text and translation have "
                    "different numbers of segments."
                )
        
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
