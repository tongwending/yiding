# ------------------------------------------------------------------------------------------
# workflow_orchestrator
# ------------------------------------------------------------------------------------------

import pickle

from .segmented_text import SegmentedText
from .prompt_gateway import PromptGateway
from .glossary_dictate import *
from . import text_manipulators

# ------------------------------------------------------------------------------------------

CORRUPTION_ERROR = "Error: Response corrupted original text."

# ------------------------------------------------------------------------------------------

class WorkflowOrchestrator:

    def __init__(self, text: SegmentedText, gate: PromptGateway):

        self.text = text
        self.gate = gate
        self.text.settings = self.gate.settings
        self.glossary = (load_glossary(self.gate.settings.GLOSSARY_FILE)
                         if self.gate.settings.GLOSSARY_FILE
                         else {})
        
    def save_as_pickle(self, filename = None):
        filename = filename if filename else f"{self.text.full_title()}.pkl"
        filename = text_manipulators.strip_invalid_characters(filename)
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    def select_glossary(self, segment):
        selected_glossary = {}

        if self.gate.glossary_selector:
            selection_of_terms = self.gate.glossary_selector.invoke(
                                f"Chinese segment:\n{segment}")
            print(selection_of_terms + "\n")
            possible_terms = selection_of_terms.splitlines()
        else:
            possible_terms = text_manipulators.find_possible_terms(segment)
            
        for term in possible_terms:
            if term in self.glossary:
                selected_glossary[term] = self.glossary[term]
        stylized_glossary = stylize_glossary(selected_glossary)
        print(stylized_glossary)

        return stylized_glossary

    def extract_glossary(self, original, translation):
        # extract_glossary:
        extracted_glossary_text = self.gate.glossary_extractor.invoke(
               f"Chinese segment:\n{original}\n\n"
               f"{self.gate.settings.LANGUAGE} translation:\n{translation}")
        print(extracted_glossary_text + "\n")
        extracted_glossary = destylize_glossary(extracted_glossary_text)
        # update glossaries
        update_glossary(self.glossary, extracted_glossary)
        update_glossary(self.text.translation_glossary, extracted_glossary)

# ------------------------------------------------------------------------------------------

    def resume_punctuation(self):

        if self.text.working_i == 0 and len(self.text.segments) > 1:
            self.text.working_text = self.text.segments[0]
            self.text.working_labels.append(
                        [self.text.page_labels[0], 1, self.text.page_lines[0]])
            self.text.working_i += 1
            

        for i in range(self.text.working_i,
                       len(self.text.segments),
                       self.gate.settings.FACSIMILE_SPAN):
                
            for j in range(0, self.gate.settings.FACSIMILE_SPAN):
                if i+j < len(self.text.segments):
                    self.text.working_text += self.text.segments[i+j]
                    self.text.working_text = text_manipulators.clean(self.text.working_text)
                    self.text.working_labels.append(
                                [self.text.page_labels[i+j], 1,self.text.page_lines[i+j]])
                    print(f"\n{self.text.page_labels[i+j]}\n")

            if len(self.text.working_text) > self.gate.settings.MAX_UNSEGMENTED_SPAN:
                raise ValueError("Reached maximum unsegmented text span.")
            
            # put together previous puncuated segmets
            first_pun = (
                (len(self.text.punctuated_segments) - self.gate.settings.PUNCTUATION_SPAN)
                if self.gate.settings.PUNCTUATION_SPAN < len(self.text.punctuated_segments)
                else 0
                         )
            punctuated_text = ""
            for x in self.text.punctuated_segments[first_pun:]:
                punctuated_text += f"{x.rstrip()}\n<break>\n"
                                       
            print(self.text.working_text)

            attempts = 0
            response_is_uncorrupted = False
            while not response_is_uncorrupted and attempts < self.gate.settings.MAX_PUNCTUATION_ATTEMPTS:
                segmented_text = self.gate.punctuator.invoke(
                    (f"Preceding punctuated text:\n{punctuated_text}"
                        if len(self.text.punctuated_segments) > 0 else "")
                    +f"\n\n\nText to be punctuated:\n{self.text.working_text}")
                print(f"Attempt {attempts+1}:\n{segmented_text}")
                attempts += 1
                # Ensure original Chinese characters are not corrupted:
                if text_manipulators.strip_punctuation(self.text.working_text) == text_manipulators.strip_punctuation(segmented_text):
                    response_is_uncorrupted = True

            if response_is_uncorrupted == False:
                raise ValueError(CORRUPTION_ERROR)
            
            punctuated_segments, leftover = text_manipulators.segmentate(segmented_text)

            def chop_cross_check_and_append(x):
                a, b, c, d =  text_manipulators.chop_from_working_segment(x,
                                                        self.text.working_text,
                                                        self.text.working_labels)
                self.text.working_text = b
                self.text.working_labels = d
                
                if a and c:
                    self.text.unpunctuated_segments.append(a)
                    self.text.segment_labels.append(c)

                    if self.gate.settings.PUNCTUATION_CROSS_CHECK:
                        for j in range(0, len(self.text.punctuated_segments)):
                            prompt = (
                                "Unpunctuated segment A:\n"
                                f"{self.text.unpunctuated_segments[j]}\n\n"
                                "Punctuated segment A:\n"
                                f"{self.text.punctuated_segments[j]}\n\n\n"
                                "Unpunctuated segment B:\n"
                                f"{self.text.unpunctuated_segments[-1]}\n"
                                "\nPunctuated segment B:\n"
                                f"{x}"
                                      )
                            inconsistencies_exist = self.gate.punctuation_examinator.invoke(prompt)

                            if inconsistencies_exist == True:
                                print(f"Inconsistencies detected with segment {j}.")
                                attempts = 0
                                response_is_uncorrupted = False
                                while not response_is_uncorrupted and attempts < self.gate.settings.MAX_PUNCTUATION_ATTEMPTS:
                                    corrected_segment = self.gate.punctuation_corrector.invoke(prompt)
                                    print(f"Correction attempt {attempts+1}:\n{corrected_segment}")
                                    attempts += 1
                                    # Ensure original Chinese characters are not corrupted:
                                    if text_manipulators.strip_punctuation(self.text.unpunctuated_segments[-1]) == text_manipulators.strip_punctuation(corrected_segment):
                                        response_is_uncorrupted = True
                                if response_is_uncorrupted == False:
                                    raise ValueError(CORRUPTION_ERROR)
                                x = corrected_segment
                            else:
                                print(f"No inconsistencies with segment {j}.")
                            
                    self.text.punctuated_segments.append(x.strip())
            
            for x in punctuated_segments:
                if x:
                    chop_cross_check_and_append(x)
            
            self.text.working_i += self.gate.settings.FACSIMILE_SPAN

            if self.text.working_i >= len(self.text.segments):
                if leftover.rstrip():
                    chop_cross_check_and_append(leftover)
                self.text.is_punctuated = True

            # save progress:
            self.save_as_pickle()

# ------------------------------------------------------------------------------------------

    def resume_translation(self):

        if self.text.original_title and not self.text.translated_title:
            self.translate_title()

        if not self.text.is_punctuated:
            self.resume_punctuation()
        
        for i in range(self.text.translation_i, len(self.text.punctuated_segments)):
                    
            # select glossary
            selected_glossary = self.select_glossary(self.text.punctuated_segments[i])
                            
            # translate:
            span = (self.gate.settings.TRANSLATION_SPAN
                    if self.gate.settings.TRANSLATION_SPAN < i
                    else i)
            previous_segments = '\n'.join(self.text.punctuated_segments[i-span:i])
            previous_translations = '\n'.join(self.text.translated_segments[i-span:i])
            prompt = (
                (f"Title: {self.text.original_title}\n"
                  f"Translated title: {self.text.translated_title}\n\n"
                        if self.text.original_title and self.text.translated_title else "")
                +
                (f"Preceding text:\n{previous_segments}\n\n"
                 f"Preceding translation:\n{previous_translations}\n\n\n"
                 if i > 0 else "")
                +
                f"Text to be translated:\n{self.text.punctuated_segments[i]}")
            print(self.text.punctuated_segments[i])
            
            instructions = (f"{self.gate.translator.instructions}\n\n"
                                "Use the glossary below (if applicable):\n"
                                f"{selected_glossary}")
            translation = self.gate.translator.invoke(prompt, instructions = instructions)
            print(translation + "\n")
            self.text.translated_segments.append(translation.strip())

            # cross examine:
            if self.gate.settings.TRANSLATION_CROSS_CHECK:
                for j in range(0, len(self.text.translated_segments)-1):
                    prompt = (
                             f"Segment A:\n{self.text.punctuated_segments[j]}\n\n"
                             f"Segment A translation:\n{self.text.translated_segments[j]}\n\n\n"
                             f"Segment B:\n{self.text.punctuated_segments[i]}\n\n"
                             f"Segment B translation:\n{self.text.translated_segments[i]}")                
                    inconsistencies_exist = self.gate.translation_examinator.invoke(prompt)
                    if inconsistencies_exist == True:
                        corrected_segment = self.gate.translation_corrector.invoke(prompt)
                        self.text.translated_segments[i] = corrected_segment.strip()
                        print(f"\nCorrected segment:\n{self.text.translated_segments[i]}")
                    else:
                        print(f"No inconsistencies with segment {j}.")
                        
            # extract glossary from segment and update the global glossaries
            self.extract_glossary(self.text.punctuated_segments[i],
                                  self.text.translated_segments[i])

            # save progress:
            self.text.translation_i += 1
            self.save_as_pickle()

# ------------------------------------------------------------------------------------------

    def translate_title(self):

        # select glossary and insert it to instructions:
        selected_glossary = self.select_glossary(self.text.original_title)
        instructions = (self.gate.translator.instructions
                       + "\n\nUse the glossary below (if applicable):\n"\
                       + selected_glossary)

        # translate title:
        print(selected_glossary + "\n\n" + self.text.original_title + "\n")
        title = self.gate.translator.invoke(f"{self.text.original_title}",
                                                  instructions = instructions)
        print(title + "\n\n")
        self.text.translated_title = title.strip()

        # extract glossary from title and update global glossaries:
        self.extract_glossary(self.text.original_title, self.text.translated_title)
        
        # save progress:
        self.save_as_pickle()

# ------------------------------------------------------------------------------------------
