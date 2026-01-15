############################################################################################
############################################################################################
############################################################################################
### THE WORKFLOW ORCHESTRATOR CLASS
############################################################################################
############################################################################################
############################################################################################

import pickle

from SegmentedText import SegmentedText
from PromptGateway import PromptGateway
from glossary_dictate import *
import text_manipulators



############################################################################################


class WorkflowOrchestrator:
    

    def __init__(self, text: SegmentedText, gate: PromptGateway, glossary = None):

        self.text = text
        self.gate = gate
        self.glossary = {} if glossary is None else glossary
            
        # save the initialized instance
        self.save_as_pickle(f"{self.text.full_title()}.pkl")
        

    def resume_translation(self):

        if self.text.translated_title == "Untranslated Title":
            self.translate_title()
        
        for i in range(self.text.number_of_completed_segments, len(self.text.segments)):

            print(f"\n{self.text.page_labels[i]}\n")

            # punctuate (first run punctuates the first three segments):
            
            for j in (0, 1, 2):     # After first iteration, only j = 2 will run.
                
                if  len(self.text.punctuated_segments)==i+j and len(self.text.segments)>i+j:

                    prompt = self.build_punctuation_prompt(i+j)

                    print(self.text.segments[i+j])
                    
                    attempts = 0
                    response_is_uncorrupted = False
                    while response_is_uncorrupted == False and attempts < 3:
                        
                        punctuated_text = self.gate.punctuator.invoke(prompt)

                        print(punctuated_text + "\n")

                        attempts += 1

                        # Ensure no original Chinese character was corrupted:
                        if text_manipulators.strip_punctuation(self.text.segments[i+j])\
                                    == text_manipulators.strip_punctuation(punctuated_text):
                            response_is_uncorrupted = True

                    if response_is_uncorrupted == False:
                        raise ValueError("GPT's response corrupted the original text.")
                    else:
                        self.text.punctuated_segments.append(punctuated_text)

            # restore broken sentence on segments' borders:
            
            if i == 0 and len(self.text.punctuated_segments)>=2: # first segment
                a , b , c = text_manipulators.mend_last_sentence(
                                                        self.text.punctuated_segments[i],
                                                        self.text.punctuated_segments[i+1])
                self.text.mended_segments.append(a)
                self.text.mended_segments.append(b)
                self.text.segment_breaches.append(c)
            elif i ==0 and len(self.text.punctuated_segments)==1:
                self.text.mended_segments.append(self.text.punctuated_segments[i])

            if i < len(self.text.punctuated_segments)-2:
                a, b, c = text_manipulators.mend_last_sentence(
                                                        self.text.mended_segments[i+1],
                                                        self.text.punctuated_segments[i+2])
                self.text.mended_segments[i+1] = a
                self.text.mended_segments.append(b)
                self.text.segment_breaches.append(c)
                    
            if i == len(self.text.segments)-1:   # last segment
                self.text.segment_breaches.append(None)
                
            # create lists of verses (a.k.a. numbered sentences):
        
            for j in (0, 1):     # After first iteration, only j = 1 will run.
                if  len(self.text.verse_lists) == i+j and len(self.text.mended_segments) > i+j:
                    self.text.verse_lists.append(text_manipulators.break_to_verses(self.text.mended_segments[i+j]))
                    # then put the verses together in a versified segment:
                    self.text.versified_segments.append(text_manipulators.glue_verses(self.text.verse_lists[i+j]))
                    
            # build segment glossary:
        
            selected_glossary = {}

            pre_segment = self.text.mended_segments[i-1] if i > 0 else None
            fol_segment = self.text.mended_segments[i+1] \
                    if i < len(self.text.mended_segments)-1 else None

            prompt = self.build_glossary_selection_prompt(self.text.mended_segments[i],
                                                          preceding_section = pre_segment,
                                                          following_section = fol_segment)

            selection_of_terms = self.gate.glossary_selector.invoke(prompt)
            print(selection_of_terms + "\n")

            for term in selection_of_terms.splitlines():
                if term in self.glossary:
                    selected_glossary[term] = self.glossary[term]
                            
            # translate:
            
            prompt = self.build_translation_prompt(i)
            comb_instructions = self.build_translation_instructions(selected_glossary)

            print(self.text.mended_segments[i])
            translation = self.gate.translator.invoke(prompt,
                                                      instructions = comb_instructions)
            print(translation + "\n")

            self.text.translated_segments.append(translation)

            # cross examine:
            
            for j in range(0, len(self.text.translated_segments)-1):

                prompt = self.build_cross_examination_prompt(i, j)

                corrected_segment = self.gate.cross_examinator.invoke(prompt)
        
                if corrected_segment.strip() != "N/A":
                    self.text.translated_segments[i] = corrected_segment
                    print(f"\nCorrected segment:\n{self.text.translated_segments[i]}")
                        
            # extract_glossary:
        
            prompt = self.build_glossary_extraction_prompt(i)

            extracted_glossary_text = self.gate.glossary_extractor.invoke(prompt)
            print(extracted_glossary_text + "\n")

            extracted_glossary = destylize_glossary(extracted_glossary_text)

            self.text.segment_glossaries.append(extracted_glossary)
            update_glossary(self.glossary, extracted_glossary)
            update_glossary(self.text.translation_glossary, extracted_glossary)

            # save progress:
            
            self.text.number_of_completed_segments += 1
            self.save_as_pickle(f"{self.text.full_title()} - Translation.pkl")


    def save_as_pickle(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self, f)


    def translate_title(self):
        
        # select glossary:

        prompt = self.build_glossary_selection_prompt(self.text.original_title)
        selection_text = self.gate.glossary_selector.invoke(prompt)

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
        
        self.text.translated_title = self.gate.title_translator.invoke(
                                                            self.text.original_title,
                                                            instructions = instructions)
        print(self.text.translated_title + "\n\n")


        # extract glossary:
        prompt = ("Chinese original:\n"\
                  + self.text.original_title\
                  + "\n\nEnglish translation:\n"\
                  + self.text.translated_title)
        
        glossary_text = self.gate.glossary_extractor.invoke(prompt)
        
        print(glossary_text + "\n")

        glossary_additions = destylize_glossary(glossary_text)

        # update glossaries:
        update_glossary(self.glossary, glossary_additions)
        update_glossary(self.text.translation_glossary, glossary_additions)

                            
############################################################################################
# PROMPT FACTORY
############################################################################################


    def build_punctuation_prompt(self, i):

        preceding_section = self.text.segments[i-1] if i > 0 else None
        preceding_punctuated = self.text.punctuated_segments[i-1] if i > 0 else None
        following_section = self.text.segments[i+1] if i < len(self.text.segments)-1\
                                                    else None
      
        prompt = ""
        if preceding_section:
            prompt += ("Preceding segment:\n"\
                       + preceding_section\
                       + "\n\nPreceding segment punctuated:\n"\
                       + preceding_punctuated)
            
        prompt += f"\n\n\nCurrent segment:\n{self.text.segments[i]}"

        if following_section:
            prompt += f"\n\n\nFollowing segment:\n{following_section}"
        
        return prompt
    

############################################################################################


    def build_glossary_selection_prompt(self,
                    current_section, preceding_section = None, following_section = None):
       
        prompt = ""
        if preceding_section:
            prompt += f"Preceding segment:\n{preceding_section}"

        prompt += f"\n\n\nCurrent segment:\n{current_section}"

        if following_section:
            prompt += f"\n\n\nFollowing segment:\n{following_section}"

        return prompt


############################################################################################


    def build_translation_prompt(self, i):

        preceding_section = self.text.versified_segments[i-1] if i > 0 else None
        preceding_translation = self.text.translated_segments[i-1] if i > 0 else None
        following_section = self.text.versified_segments[i+1] \
                                    if i < len(self.text.versified_segments)-1 else None
                                                                    
        if self.text.original_title not in (None, "Untitled")\
           and self.text.translated_title not in (None, "Untranslated Title"):
            prompt = f"Title: {self.text.original_title}\nTranslation: {self.text.translated_title}\n\n"
        else:
            prompt = ""
            
        if preceding_section:
            prompt += f"Preceding segment:\n{preceding_section}"
            
        if preceding_translation:
            prompt += f"\n\nPreceding segment translation:\n{preceding_translation}"

        prompt += f"\n\n\nCurrent segment:\n{self.text.versified_segments[i]}"
        
        if following_section:
            prompt += f"\n\n\nFollowing segment:\n{following_section}"
            
        return prompt
    

    def build_translation_instructions(self, segment_glossary):
        
        stylized_glossary = stylize_glossary(segment_glossary)
        
        comb_instructions = (self.gate.translator.instructions +
                             "\n\nUse the glossary below (if applicable):\n" +
                             stylized_glossary)
        
        return comb_instructions
            

############################################################################################


    def build_cross_examination_prompt(self, i, j):

        prompt = (
            "Segment A:\n" \
            + self.text.versified_segments[j] \
            + "\n\n" \
            + "Segment A translation:\n" \
            + self.text.translated_segments[j] \
            + "\n\n\n" \
            + "Segment B:\n" \
            + self.text.versified_segments[i] \
            + "\n\n" \
            + "Segment B translation:\n" \
            + self.text.translated_segments[i]
            )
        
        return prompt

        
############################################################################################


    def build_glossary_extraction_prompt(self, i):

        preceding_section = self.text.versified_segments[i-1] if i>0 else None
        preceding_translation = self.text.translated_segments[i-1] if i>0 else None
        following_section = self.text.versified_segments[i+1] \
                                    if i<len(self.text.versified_segments)-1 else None

        
        text_and_translation = ("Current segment:\n" \
                                + self.text.versified_segments[i] \
                                + "\n\n" \
                                + "Current segment translation:\n" \
                                + self.text.translated_segments[i])
        
        prompt = ""
        
        if preceding_section:
            prompt += f"Preceding segment:\n{preceding_section}"
        if preceding_translation:
            prompt += f"\n\nPreceding segment translation:\n{preceding_translation}"

        prompt += f"\n\n\n{text_and_translation}"
        
        if following_section:
            prompt += f"\n\n\nFollowing segment:\n{following_section}"

        return prompt


############################################################################################

