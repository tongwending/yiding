############################################################################################
############################################################################################
############################################################################################
### THE WORKFLOW ORCHESTRATOR CLASS
############################################################################################
############################################################################################
############################################################################################

import pickle

from segmented_text import SegmentedText
from prompt_gateway import PromptGateway
from glossary_dictate import *
import text_manipulators



############################################################################################


class WorkflowOrchestrator:
    

    def __init__(self, text: SegmentedText, gate: PromptGateway, glossary = None):

        self.text = text
        self.gate = gate
        self.glossary = {} if glossary is None else glossary
            
        # save the initialized instance
        self.save_as_pickle()


    def save_as_pickle(self, filename = None):
        filename = filename if filename else f"{self.text.full_title()}.pkl"
        with open(filename, "wb") as f:
            pickle.dump(self, f)


    def resume_punctuation(self):

        for i in range(self.text.working_segment[0], len(self.text.segments)):
            
            self.text.working_segment[1] += f"\n{self.text.segments[i].rstrip()}"
            if len(self.text.working_segment[1]) > self.gate.max_unsegmented_span:
                raise ValueError("Reached maximum unsegmented text span.")
            
            # put together previous puncuated segmets
            first_pun = ((len(self.text.punctuated_segments) - self.gate.punctuation_span)
                         if self.gate.punctuation_span < len(self.text.punctuated_segments)
                         else 0)
            punctuated_text = ""
            for x in self.text.punctuated_segments[first_pun:]:
                punctuated_text += f"\n{x.rstrip()}\n<break>"

            print(f"\n{self.text.page_labels[i]}\n")                                       
            print(self.text.working_segment[1])

            attempts = 0
            response_is_uncorrupted = False
            while response_is_uncorrupted == False and attempts < 3:
                segmented_text = self.gate.punctuator.invoke(
                            (f"Preceding punctuated text:\n{punctuated_text}"
                                 if len(self.text.punctuated_segments) > 0 else "")
                            +f"\n\n\nCurrent segment:\n{self.text.working_segment[1]}")
                print(segmented_text)
                attempts += 1
                # Ensure original Chinese characters are not corrupted:
                if text_manipulators.strip_punctuation(self.text.working_segment[1])\
                            == text_manipulators.strip_punctuation(segmented_text):
                    response_is_uncorrupted = True

            if response_is_uncorrupted == False:
                raise ValueError("GPT's response corrupted the original text.")
            
            punctuated_segments, leftover = text_manipulators.segmentate(segmented_text)
                
            for x in punctuated_segments:
                if x:
                    self.text.punctuated_segments.append(x)

            if i == len(self.text.segments)-1 and leftover:
                self.text.punctuated_segments.append(leftover)
            else:
                self.text.working_segment[1] =  text_manipulators.chop_from_working_segment(
                                                            punctuated_segments,
                                                            self.text.working_segment[1])
            
            # save progress:
            self.text.working_segment[0] += 1
            self.save_as_pickle()

        if self.text.working_segment[0] >= len(self.text.segments):
            self.text.is_punctuated = True


    def resume_translation(self):

        if not self.text.translated_title:
            self.translate_title()

        if not self.text.is_punctuated:
            self.resume_punctuation()
        
        for i in range(len(self.text.segment_glossaries),len(self.text.punctuated_segments)):
                    
            # build segment glossary:
            selected_glossary = {}
            selection_of_terms = self.gate.glossary_selector.invoke(
                                f"Chinese segment:\n{self.text.punctuated_segments[i]}")
            print(selection_of_terms + "\n")

            for term in selection_of_terms.splitlines():
                if term in self.glossary:
                    selected_glossary[term] = self.glossary[term]
                            
            # translate:
            prompt = (((f"Title: {self.text.original_title}\n"
                     + f"Translated title: {self.text.translated_title}\n\n")
                        if self.text.original_title and self.text.translated_title else "")
                   + ((f"Preceding text:\n{self.text.punctuated_segments[i-1]}"
                    + f"\n\nPreceding translation:\n{self.text.translated_segments[i-1]}")
                        if i > 0 else "")
                   + f"\n\n\nText to be translated:\n{self.text.punctuated_segments[i]}")
            print(self.text.punctuated_segments[i])
            
            s = self.text.punctuated_segments[i].strip()
            if s.startswith("**") and s.endswith("**") and "**" not in s[2:-2]:
                instructions = (f"{self.gate.title_translator.instructions}\n\n"
                              +  "Use the glossary below (if applicable):\n"
                              + f"{stylize_glossary(selected_glossary)}")
                translation = self.gate.title_translator.invoke(prompt,
                                                          instructions = instructions)
            else:
                instructions = (f"{self.gate.translator.instructions}\n\n"
                              +  "Use the glossary below (if applicable):\n"
                              + f"{stylize_glossary(selected_glossary)}")
                translation = self.gate.translator.invoke(prompt,
                                                          instructions = instructions)
            print(translation + "\n")
            self.text.translated_segments.append(translation)

            # cross examine:
            for j in range(0, len(self.text.translated_segments)-1):
                prompt = (
                         f"Segment A:\n{self.text.punctuated_segments[j]}\n\n"
                       + f"Segment A translation:\n{self.text.translated_segments[j]}\n\n\n"
                       + f"Segment B:\n{self.text.punctuated_segments[i]}\n\n"
                       + f"Segment B translation:\n{self.text.translated_segments[i]}")                
                inconsistencies_exist = self.gate.cross_examinator.invoke(prompt)
                if inconsistencies_exist == True:
                    self.text.translated_segments[i] = \
                                                    self.gate.cross_corrector.invoke(prompt)
                    print(f"\nCorrected segment:\n{self.text.translated_segments[i]}")
                else:
                    print(f"No inconsistencies with segment {j}.")
                        
            # extract_glossary:
            extracted_glossary_text = self.gate.glossary_extractor.invoke(
                   f"Chinese segment:\n{self.text.punctuated_segments[i]}\n\n"
                 + f"{self.gate.language} translation:\n{self.text.translated_segments[i]}")
            print(extracted_glossary_text + "\n")
            extracted_glossary = destylize_glossary(extracted_glossary_text)
            update_glossary(self.glossary, extracted_glossary)
            update_glossary(self.text.translation_glossary, extracted_glossary)
            self.text.segment_glossaries.append(extracted_glossary)

            # save progress:
            self.save_as_pickle()


    def translate_title(self):
        
        # select glossary:
        selection_text = self.gate.glossary_selector.invoke(f"{self.text.original_title}")

        # prepare glossary:
        title_glossary = {}
        for term in selection_text.splitlines():
            if term in self.glossary:
                title_glossary[term] = self.glossary[term]
        stylized_glossary = stylize_glossary(title_glossary)

        # prepare translation  instructions:
        instructions = (self.gate.title_translator.instructions\
                        + "\n\nUse the glossary below (if applicable):\n"\
                        + stylized_glossary)

        # translate title:
        print(stylized_glossary + "\n\n" + self.text.original_title + "\n")
        title = self.gate.title_translator.invoke(
                                f"**{self.text.original_title}**",
                                instructions = instructions)
        self.text.translated_title = title.strip().strip("*")
        print(self.text.translated_title + "\n\n")

        # extract glossary:
        prompt = (f"Chinese original:\n{self.text.original_title}"
                + f"\n\nEnglish translation:\n{self.text.translated_title}")
        glossary_text = self.gate.glossary_extractor.invoke(prompt)
        print(glossary_text + "\n")
        glossary_additions = destylize_glossary(glossary_text)

        # update glossaries:
        update_glossary(self.glossary, glossary_additions)
        update_glossary(self.text.translation_glossary, glossary_additions)

        # save progress:
        self.save_as_pickle()


############################################################################################

