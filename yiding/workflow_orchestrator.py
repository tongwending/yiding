# ------------------------------------------------------------------------------------------
# workflow_orchestrator
# ------------------------------------------------------------------------------------------

from uuid import uuid4

from .segmented_text import SegmentedText
from .prompt_gateway import PromptGateway
from .glossary_dictate import *
from . import text_manipulators as tm
from .yiding_file_io import autosave_project, create_run, finish_run


# ------------------------------------------------------------------------------------------

CORRUPTION_ERROR = "Error: Response corrupted original text."
CHARACTER_CAP = 120

class TransformCancelled(Exception):
    pass

# ------------------------------------------------------------------------------------------

class WorkflowOrchestrator:

    def __init__(self, text: SegmentedText, settings, progress_callback=None):

        self.text = text
        
        self.gate = None
        self.settings = settings
        
        self.progress_callback = progress_callback
        self.cancel_check = None
        self.checkpoint_callback = None
        
        self.project_file = None
        self.runs = list(getattr(self.text, "yiding_runs", []))
        self.provenance = getattr(
            self.text,
            "yiding_provenance",
            {"punctuated_segment_run_ids": [None for _ in self.text.punctuated_segments],
             "translated_segment_run_ids": [None for _ in self.text.translated_segments],})
        self.active_runs = {run["operation"]: run["id"] for run in self.runs
                            if run["status"] == "in_progress"}

# ------------------------------------------------------------------------------------------

    def _start_run(self, operation):
        
        if operation in self.active_runs:
            return self.active_runs[operation]
        
        run_id = f"{operation}-{uuid4().hex}"
        run = create_run(operation, self.settings, run_id)
        self.runs.append(run)
        self.active_runs[operation] = run_id
        
        return run_id

    def _emit_progress(self, phase, current, total, segment=None):

        if self.progress_callback is None:
            return

        data = {"phase": phase, "current": current, "total": total}

        if segment is not None:
            data["segment"] = segment

        self.progress_callback(data)
        
    def _check_for_cancellation(self):

        if self.cancel_check is not None and self.cancel_check():
            raise TransformCancelled()
    
    def _finish_run(self, operation):

        run_id = self.active_runs.get(operation)

        if not run_id:
            return

        for run in reversed(self.runs):
            if run["id"] == run_id:
                finish_run(run)
                break

        del self.active_runs[operation]

    def save_as_yiding(self, filename=None, operation=None, status="in_progress",):

        self._check_for_cancellation()

        if filename:
            self.project_file = tm.strip_invalid_characters(filename)
        elif not self.project_file:
            self.project_file = tm.strip_invalid_characters(
                f"{self.text.full_title()[:CHARACTER_CAP]}.yiding")

        active_run_id = (self.active_runs.get(operation) if operation else None)

        workflow = {
            "status": status,
            "operation": operation,
            "active_run_id": active_run_id,
            "working_i": self.text.working_i,
            "working_text": self.text.working_text,
            "working_labels": self.text.working_labels,
            "translation_i": self.text.translation_i,
            "term_extraction_i": self.text.term_extraction_i,
            "glossary_extraction_i": self.text.glossary_extraction_i,
        }

        saved_path = autosave_project(
            self.project_file,
            self.text,
            self.settings,
            workflow=workflow,
            runs=self.runs,
            provenance=self.provenance,
            glossary_source_path=(self.settings["translation"]["glossary"]),
        )

        self.project_file = str(saved_path)
        
        if self.checkpoint_callback is not None:
            self.checkpoint_callback()

        return saved_path

# ------------------------------------------------------------------------------------------

    def _update_log(self, text):
        self.text._update_log(text)

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
               f"{self.settings['translation']['language']} translation:\n{translation}")
        self._update_log(f"Extracted glossary:\n{extracted_glossary_text}")
        # update glossaries
        extracted_glossary = destylize_glossary(extracted_glossary_text)
        update_glossary(self.text.new_glossary,
                        differentiate_glossaries(extracted_glossary, self.glossary))
        update_glossary(self.glossary, extracted_glossary)
        update_glossary(self.text.translation_glossary, extracted_glossary)

# ------------------------------------------------------------------------------------------

    def resume_punctuation(self):
        
        punctuation_run_id = self._start_run("punctuation")
        self._emit_progress("punctuation", self.text.working_i, len(self.text.segments))

        self.text.settings["punctuation"] = self.settings["punctuation"]
        self._update_log(f"Settings:\n{self.text.settings['punctuation']}")

        self.gate = PromptGateway(self.settings, "punctuation")
        self._update_log(f"Prompt Gateway:\n{self.gate.log}")

        def add_to_working_text(i):
            self.text.working_text += self.text.segments[i]
            self.text.working_text = tm.clean(self.text.working_text)
            self.text.working_labels.append(
                        [self.text.page_labels[i], 1, self.text.page_lines[i]])
            self.text.working_i += 1
            self._emit_progress("punctuation", self.text.working_i, len(self.text.segments))
            self._update_log(f"Facsimile {self.text.page_labels[i]} added to working text.")

        if self.text.working_i == 0 and len(self.text.segments) > 1:
            add_to_working_text(0)
            
        for i in range(self.text.working_i,
                       len(self.text.segments),
                       self.settings["punctuation"]["facsimile_span"]):
                
            for j in range(0, self.settings["punctuation"]["facsimile_span"]):
                if i+j < len(self.text.segments):
                    add_to_working_text(i+j)

            self._update_log(f"Working text:\n{self.text.working_text}")

            if len(self.text.working_text) > self.settings["punctuation"]["max_unsegmented_span"]:
                raise ValueError("Reached maximum unsegmented text span.")
            
            # put together previous puncuated segmets
            first_pun = (
                (len(self.text.punctuated_segments) - self.settings["punctuation"]["punctuation_span"])
                if self.settings["punctuation"]["punctuation_span"] < len(self.text.punctuated_segments)
                else 0
                         )
            punctuated_text = ""
            for x in self.text.punctuated_segments[first_pun:]:
                punctuated_text += f"{x.rstrip()}\n<break>\n"

            attempts = 0
            response_is_uncorrupted = False
            while not response_is_uncorrupted and attempts < self.settings["punctuation"]["max_punctuation_attempts"]:
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

                    if self.settings["punctuation"]["cross_check"]["enabled"]:
                        
                        # Progress bar emition:
                        cross_total = len(self.text.punctuated_segments)
                        cross_segment = (cross_total + 1)
                        self._emit_progress("punctuation_cross_check", 0, cross_total,
                                            segment = cross_segment)

                        for j in range(0, len(self.text.punctuated_segments)):

                            self._check_for_cancellation()
                            
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
                                
                                while not response_is_uncorrupted and attempts < self.settings["punctuation"]["max_punctuation_attempts"]:

                                    self._check_for_cancellation()
                                    
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

                            # Progress bar emition:
                            self._emit_progress("punctuation_cross_check", j + 1, cross_total,
                                                segment = cross_segment)
                            
                    self.text.punctuated_segments.append(x.strip())
                    self.provenance["punctuated_segment_run_ids"].append(punctuation_run_id)
            
            for x in punctuated_segments:
                if x:
                    chop_cross_check_and_append(x)
            
            if self.text.working_i >= len(self.text.segments):
                if leftover.rstrip():
                    chop_cross_check_and_append(leftover)
                self.text.is_structured = True
                self.text.is_punctuated = True

            # save progress:
            if self.text.is_punctuated:
                self._finish_run("punctuation")
                self.save_as_yiding(operation="punctuation", status="completed",)
            else:
                self.save_as_yiding(operation="punctuation", status="in_progress",)

# ------------------------------------------------------------------------------------------

    def resume_translation(self):

        if not self.text.is_punctuated:
            self.resume_punctuation()
            
        self.text.settings["translation"] = self.settings["translation"]
        self._update_log(f"Settings:\n{self.text.settings['translation']}")

        self.gate = PromptGateway(self.settings, "translation")
        self._update_log(f"Prompt Gateway:\n{self.gate.log}")
        
        self.glossary = (load_glossary(self.settings["translation"]["glossary"])
                         if self.settings["translation"]["glossary"]
                         else {})
                         
        if self.text.translation_glossary:
            update_glossary(self.glossary, self.text.translation_glossary)

        translation_run_id = self._start_run("translation")

        if self.text.original_title and not self.text.translated_title:
            self.translate_title()

        # Progress bar emition:
        self._emit_progress("translation", self.text.translation_i,
                            len(self.text.punctuated_segments))
        
        for i in range(self.text.translation_i, len(self.text.punctuated_segments)):
                    
            # select glossary
            selected_glossary = self.select_glossary(self.text.punctuated_segments[i])
                            
            # translate:
            span = (self.settings["translation"]["translation_span"]
                    if self.settings["translation"]["translation_span"] < i
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
            self.provenance["translated_segment_run_ids"].append(translation_run_id)
            
            self._update_log(f"Punctuated segment {self.text.segment_labels[i]}:\n"
                             f"{self.text.punctuated_segments[i]}\n\n"
                             f"Translated segment {self.text.segment_labels[i]}:\n"
                             f"{self.text.translated_segments[i]}")

            # cross examine:
            if self.settings["translation"]["cross_check"]["enabled"]:

                cross_total = len(self.text.translated_segments) - 1
                self._emit_progress("translation_cross_check", 0, cross_total,
                                    segment = i+1)
                
                for j in range(0, len(self.text.translated_segments)-1):

                    self._check_for_cancellation()

                    prompt = (
                        (f"Text title: {self.text.original_title}\n"
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

                    # Progress bar emition:
                    self._emit_progress("translation_cross_check", j + 1, cross_total,
                                        segment = i+1)
                    
            # extract glossary from segment and update the global glossaries
            self.extract_glossary(self.text.punctuated_segments[i],
                                  self.text.translated_segments[i])

            # save progress:
            self.text.translation_i += 1
            
            # Progress bar emition:
            self._emit_progress("translation", self.text.translation_i,
                                len(self.text.punctuated_segments))
            
            if (self.text.translation_i >= len(self.text.punctuated_segments)):
                self.text.is_translated = True
                self.text.translation_language = (self.settings["translation"]["language"])
                self._finish_run("translation")
                self.save_as_yiding(operation="translation", status="completed",)
            else:
                self.save_as_yiding(operation="translation", status="in_progress",)

# ------------------------------------------------------------------------------------------

    def translate_title(self):

        # Progress bar emition:
        self._check_for_cancellation()
        self._emit_progress("translation_title", 0, 0)

        # select glossary and insert it to instructions:
        selected_glossary = self.select_glossary(self.text.original_title)
        instructions = (self.gate.translator.instructions
                     + (selected_glossary if selected_glossary else "No glossary provided."))

        # translate title:
        self._update_log(f"Original title:\n{self.text.original_title}")
        title = self.gate.translator.invoke(f"{self.text.original_title}",
                                                  instructions = instructions)
        self.text.translated_title = title.strip()
        self._update_log(f"{self.settings['translation']['language']} title:\n{self.text.translated_title}")

        # extract glossary from title and update global glossaries:
        self.extract_glossary(self.text.original_title, self.text.translated_title)
        
        # save progress:
        self.save_as_yiding(operation="translation", status="in_progress",)

# ------------------------------------------------------------------------------------------

    def resume_term_extraction(self):

        self._start_run("term_extraction")

        self.text.settings["term_extraction"] = self.settings["term_extraction"]
        self._update_log(f"Settings:\n{self.text.settings['term_extraction']}")

        self.gate = PromptGateway(self.settings, "term_extraction")
        self._update_log(f"Prompt Gateway:\n{self.gate.log}")

        self._emit_progress("term_extraction", self.text.term_extraction_i,
                            len(self.text.punctuated_segments))

        for i in range(self.text.term_extraction_i,
                       len(self.text.punctuated_segments),
                       self.settings["term_extraction"]["span"]
            ):

            self._check_for_cancellation()

            span = (self.settings["term_extraction"]["span"]
                    if self.settings["term_extraction"]["span"]+i < len(self.text.punctuated_segments)
                    else len(self.text.punctuated_segments)-i)
                    
            segments = '\n'.join(self.text.punctuated_segments[i:i+span])
            
            selection_of_terms = self.gate.mono_glossary_selector.invoke(
                f"Chinese text:\n{segments}")

            selected_terms = destylize_terms(selection_of_terms)
            update_glossary(self.text.extracted_terms, selected_terms)

            self._update_log(f"Terms selected:\n{selected_terms}")

            self.text.term_extraction_i += span

            # Progress bar emition:
            self._emit_progress("term_extraction", self.text.term_extraction_i,
                                len(self.text.punctuated_segments))

            if (self.text.term_extraction_i >= len(self.text.punctuated_segments)):
                self.text.is_term_extracted = True
                self._finish_run("term_extraction")
                self.save_as_yiding(operation="term_extraction", status="completed",)
            else:
                self.save_as_yiding(operation="term_extraction", status="in_progress",)

# ------------------------------------------------------------------------------------------

    def resume_glossary_extraction(self):

        self._start_run("glossary_extraction")

        self.text.settings["glossary_extraction"] = self.settings["glossary_extraction"]
        self._update_log(f"Settings:\n{self.text.settings['glossary_extraction']}")


        self.gate = PromptGateway(self.settings, "glossary_extraction")
        self._update_log(f"Prompt Gateway:\n{self.gate.log}")

        self._emit_progress("glossary_extraction", self.text.glossary_extraction_i,
                            len(self.text.translated_segments))

        for i in range(self.text.glossary_extraction_i,
                       len(self.text.translated_segments),
                       self.settings["glossary_extraction"]["span"]
            ):

            self._check_for_cancellation()
            
            if self.text.translation_language:
                translation_header = f"{self.text.translation_language} translation"
            else:
                translation_header = "Translation"

            span = (self.settings["glossary_extraction"]["span"]
                    if self.settings["glossary_extraction"]["span"]+i < len(self.text.translated_segments)
                    else len(self.text.translated_segments)-i)
                    
            punctuated_segments = '\n'.join(self.text.punctuated_segments[i:i+span])
            translated_segments = '\n'.join(self.text.translated_segments[i:i+span])

            extracted_glossary_text = self.gate.mono_glossary_extractor.invoke(
                   f"Chinese text:\n{punctuated_segments}\n\n"
                   f"{translation_header}:\n{translated_segments}")
            self._update_log(f"Extracted glossary:\n{extracted_glossary_text}")
            # update glossaries
            extracted_glossary = destylize_glossary(extracted_glossary_text)
            update_glossary(self.text.extracted_glossary, extracted_glossary)

            self.text.glossary_extraction_i += span

            # Progress bar emition:
            self._emit_progress("glossary_extraction", self.text.glossary_extraction_i,
                                len(self.text.translated_segments))

            if (self.text.glossary_extraction_i >= len(self.text.translated_segments)):
                self.text.is_glossary_extracted = True
                self._finish_run("glossary_extraction")
                self.save_as_yiding(operation="glossary_extraction", status="completed",)
            else:
                self.save_as_yiding(operation="glossary_extraction", status="in_progress",)
        
# ------------------------------------------------------------------------------------------

