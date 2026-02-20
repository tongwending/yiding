# ------------------------------------------------------------------------------------------
# workflow_orchestrator
# ------------------------------------------------------------------------------------------

import pickle

from .segmented_text import SegmentedText
from .prompt_gateway import PromptGateway
from .glossary_dictate import *
from . import text_manipulators as tm

# ------------------------------------------------------------------------------------------

CORRUPTION_ERROR = "Error: Response corrupted original text."
CHARACTER_CAP = 120

# ------------------------------------------------------------------------------------------

class WorkflowOrchestrator:

    def __init__(self, text: SegmentedText, gate: PromptGateway):

        self.text = text
        self.gate = gate
        self.text.settings = self.gate.settings
        self.glossary = (load_glossary(self.gate.settings["translation"]["glossary"])
                         if self.gate.settings["translation"]["glossary"]
                         else {})
        self.log = ""

        self._update_log(f"Settings:\n{self.gate.settings}")
        self._update_log(f"Text log:\n{self.text.log}")
        
    def save_as_pickle(self, filename = None):
        filename = filename if filename else f"{self.text.full_title()[:CHARACTER_CAP]}.pkl"
        filename = tm.strip_invalid_characters(filename)
        with open(filename, "wb") as f:
            pickle.dump(self, f)
            
    def _update_log(self, text):
        self.log += f"{text}\n"; print(text)

    def select_glossary(self, segment):
        selected_glossary = {}

        if self.gate.glossary_selector:
            selection_of_terms = self.gate.glossary_selector.invoke(
                                f"Chinese segment:\n{segment}")
            possible_terms = selection_of_terms.splitlines()
            self._update_log(f"Terms selected:\n{selection_of_terms}")
        else:
            possible_terms = tm.find_possible_terms(segment)
            
        for term in possible_terms:
            if term in self.glossary:
                selected_glossary[term] = self.glossary[term]
        stylized_glossary = stylize_glossary(selected_glossary)
        self._update_log(f"Segment glossary:\n{stylized_glossary}\n")

        return stylized_glossary

    def extract_glossary(self, original, translation):
        # extract_glossary:
        extracted_glossary_text = self.gate.glossary_extractor.invoke(
               f"Chinese segment:\n{original}\n\n"
               f"{self.gate.settings['translation']['language']} translation:\n{translation}")
        self._update_log(f"Extracted glossary:\n{extracted_glossary_text}")
        # update glossaries
        extracted_glossary = destylize_glossary(extracted_glossary_text)
        update_glossary(self.glossary, extracted_glossary)
        update_glossary(self.text.translation_glossary, extracted_glossary)

# ------------------------------------------------------------------------------------------

    def resume_punctuation(self):

        def add_to_working_text(i):
            self.text.working_text += self.text.segments[i]
            self.text.working_text = tm.clean(self.text.working_text)
            self.text.working_labels.append(
                        [self.text.page_labels[i], 1, self.text.page_lines[i]])
            self.text.working_i += 1
            self._update_log(f"Facsimile {self.text.page_labels[i]} added to working text.")

        if self.text.working_i == 0 and len(self.text.segments) > 1:
            add_to_working_text(0)
            
        for i in range(self.text.working_i,
                       len(self.text.segments),
                       self.gate.settings["punctuation"]["facsimile_span"]):
                
            for j in range(0, self.gate.settings["punctuation"]["facsimile_span"]):
                if i+j < len(self.text.segments):
                    add_to_working_text(i+j)

            self._update_log(f"Working text:\n{self.text.working_text}")

            if len(self.text.working_text) > self.gate.settings["punctuation"]["max_unsegmented_span"]:
                raise ValueError("Reached maximum unsegmented text span.")
            
            # put together previous puncuated segmets
            first_pun = (
                (len(self.text.punctuated_segments) - self.gate.settings["punctuation"]["punctuation_span"])
                if self.gate.settings["punctuation"]["punctuation_span"] < len(self.text.punctuated_segments)
                else 0
                         )
            punctuated_text = ""
            for x in self.text.punctuated_segments[first_pun:]:
                punctuated_text += f"{x.rstrip()}\n<break>\n"

            attempts = 0
            response_is_uncorrupted = False
            while not response_is_uncorrupted and attempts < self.gate.settings["punctuation"]["max_punctuation_attempts"]:
                segmented_text = self.gate.punctuator.invoke(
                    (f"Preceding punctuated text:\n{punctuated_text}"
                        if len(self.text.punctuated_segments) > 0 else "")
                    +f"\n\n\nText to be punctuated:\n{self.text.working_text}")
                self._update_log(f"Punctuation attempt {attempts+1}:\n{segmented_text}")
                attempts += 1
                # Ensure original Chinese characters are not corrupted:
                if tm.strip_punctuation(self.text.working_text) == tm.strip_punctuation(segmented_text):
                    response_is_uncorrupted = True

            if response_is_uncorrupted == False:
                raise ValueError(CORRUPTION_ERROR)
            
            punctuated_segments, leftover = tm.segmentate(segmented_text)

            def chop_cross_check_and_append(x):
                a, b, c, d =  tm.chop_from_working_segment(x,
                                                        self.text.working_text,
                                                        self.text.working_labels)
                self.text.working_text = b
                self.text.working_labels = d
                
                if a and c:
                    self.text.unpunctuated_segments.append(a)
                    self.text.segment_labels.append(c)

                    if self.gate.settings["punctuation"]["cross_check"]["enabled"]:

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
                                self._update_log(f"Segment {self.text.segment_labels[-1]} inconsistent with segment {self.text.segment_labels[j]}.")
                                attempts = 0
                                response_is_uncorrupted = False
                                while not response_is_uncorrupted and attempts < self.gate.settings["punctuation"]["max_punctuation_attempts"]:
                                    corrected_segment = self.gate.punctuation_corrector.invoke(prompt)
                                    self._update_log(f"Punctuation correction attempt {attempts+1}:\n{corrected_segment}")
                                    attempts += 1
                                    # Ensure original Chinese characters are not corrupted:
                                    if tm.strip_punctuation(self.text.unpunctuated_segments[-1]) == tm.strip_punctuation(corrected_segment):
                                        response_is_uncorrupted = True
                                if response_is_uncorrupted == False:
                                    raise ValueError(CORRUPTION_ERROR)
                                x = corrected_segment
                            else:
                                self._update_log(f"Segment {self.text.segment_labels[-1]} consistent with segment {self.text.segment_labels[j]}.")
                            
                    self.text.punctuated_segments.append(x.strip())
            
            for x in punctuated_segments:
                if x:
                    chop_cross_check_and_append(x)
            
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
            span = (self.gate.settings["translation"]["translation_span"]
                    if self.gate.settings["translation"]["translation_span"] < i
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
            instructions = (self.gate.translator.instructions
                         + (selected_glossary if selected_glossary else "No glossary provided."))
            translation = self.gate.translator.invoke(prompt, instructions = instructions)
            self.text.translated_segments.append(translation.strip())
            self._update_log(f"Punctuated segment {self.text.segment_labels[i]}:\n"
                             f"{self.text.punctuated_segments[i]}\n\n"
                             f"Translated segment {self.text.segment_labels[i]}:\n"
                             f"{self.text.translated_segments[i]}")

            # cross examine:
            if self.gate.settings["translation"]["cross_check"]["enabled"]:
                for j in range(0, len(self.text.translated_segments)-1):
                    prompt = (
                        (f"Scripture title: {self.text.original_title}\n"
                         f"Translated scripture title: {self.text.translated_title}\n\n"
                         if self.text.original_title and self.text.translated_title else "")
                        +(f"Segment A:\n{self.text.punctuated_segments[j]}\n\n"
                          f"Segment A translation:\n{self.text.translated_segments[j]}\n\n\n"
                          f"Segment B:\n{self.text.punctuated_segments[i]}\n\n"
                          f"Segment B translation:\n{self.text.translated_segments[i]}")
                                )                
                    inconsistencies_exist = self.gate.translation_examinator.invoke(prompt)
                    if inconsistencies_exist == True:
                        self._update_log(f"{self.text.segment_labels[i]} is inconsistent with segment {self.text.segment_labels[j]}.")
                        corrected_segment = self.gate.translation_corrector.invoke(prompt)
                        self.text.translated_segments[i] = corrected_segment.strip()
                        self._update_log(f"Corrected segment:\n{self.text.translated_segments[i]}")
                    else:
                        self._update_log(f"{self.text.segment_labels[i]} is consistent with segment {self.text.segment_labels[j]}.")
                        
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
                     + (selected_glossary if selected_glossary else "No glossary provided."))

        # translate title:
        self._update_log(f"Original title:\n{self.text.original_title}")
        title = self.gate.translator.invoke(f"{self.text.original_title}",
                                                  instructions = instructions)
        self.text.translated_title = title.strip()
        self._update_log(f"{self.gate.settings['translation']['language']} title:\n{self.text.translated_title}")

        # extract glossary from title and update global glossaries:
        self.extract_glossary(self.text.original_title, self.text.translated_title)
        
        # save progress:
        self.save_as_pickle()

# ------------------------------------------------------------------------------------------
