# ------------------------------------------------------------------------------------------
# prompt_gateway
# ------------------------------------------------------------------------------------------

# imports inside code:
# from openai import OpenAI
# from google.genai import Client
# from .gpt_invoker import GPT_Invoker
# from .gemini_invoker import Gemini_Invoker

import keyring

from .llm_lists import is_open_ai, is_google
from . import instructors

# ------------------------------------------------------------------------------------------

class PromptGateway:

    def __init__(self, settings, job):

        self.settings = settings
        self.job = job

        self.openai_client = None
        self.google_client = None
        
        self.invokers = []
        
        self.punctuator = None
        self.punctuation_examinator = None
        self.punctuation_corrector = None

        self.glossary_selector = None
        self.translator = None
        self.translation_examinator = None
        self.translation_corrector = None
        self.glossary_extractor = None

        self.mono_glossary_selector = None
        
        self.mono_glossary_extractor = None


        if self.job == "punctuation":
        
            self.punctuator = self.create_invoker(
                self.settings["punctuation"]["punctuation"],
                instructors.instruct_punctuation(self.settings))
            self.invokers.append(self.punctuator)
            
            if not self.settings["punctuation"]["cross_check"]["enabled"]:
                self.punctuation_examinator = None
                self.punctuation_corrector = None
            else:
                self.punctuation_examinator = self.create_invoker(
                    self.settings["punctuation"]["cross_examination"],
                    instructors.instruct_punctuation_examination(),
                    boolean_response = True)
                self.invokers.append(self.punctuation_examinator)
                
                self.punctuation_corrector = self.create_invoker(
                    self.settings["punctuation"]["cross_correction"],
                    instructors.instruct_punctuation_correction(self.settings))
                self.invokers.append(self.punctuation_corrector)

        if self.job == "translation":
            
            if not self.settings["translation"]["llm_glossary_selection"]["enabled"]:
                self.glossary_selector = None
            else:
                self.glossary_selector = self.create_invoker(
                    self.settings["translation"]["glossary_selection"],
                    instructors.instruct_glossary_selection(self.settings))
                self.invokers.append(self.glossary_selector)

            self.translator = self.create_invoker(
                    self.settings["translation"]["translation"],
                    instructors.instruct_translation(self.settings))
            self.invokers.append(self.translator)

            if not self.settings["translation"]["cross_check"]["enabled"]:
                self.translation_examinator = None
                self.translation_corrector = None
            else:
                self.translation_examinator = self.create_invoker(
                    self.settings["translation"]["cross_examination"],
                    instructors.instruct_translation_examination(self.settings),
                    boolean_response = True)
                self.invokers.append(self.translation_examinator)

                self.translation_corrector = self.create_invoker(
                    self.settings["translation"]["cross_correction"],
                    instructors.instruct_translation_correction(self.settings))
                self.invokers.append(self.translation_corrector)

            self.glossary_extractor = self.create_invoker(
                    self.settings["translation"]["glossary_extraction"],
                    instructors.instruct_glossary_extraction(self.settings))
            self.invokers.append(self.glossary_extractor)

        if self.job == "term_extraction":
            
            self.mono_glossary_selector = self.create_invoker(
                self.settings["term_extraction"]["extraction"],
                instructors.instruct_mono_glossary_selection(self.settings))
            self.invokers.append(self.mono_glossary_selector)
            
        if self.job == "glossary_extraction":
            
            self.mono_glossary_extractor = self.create_invoker(
                self.settings["glossary_extraction"]["extraction"],
                instructors.instruct_mono_glossary_extraction(self.settings))
            self.invokers.append(self.mono_glossary_extractor)

        self.log = ""
        for inv in self.invokers:
            self._update_log(f"------------\n{inv.instructions}")
    
    def _update_log(self, text):
        text = f"\n{text}\n"
        self.log += text

    def create_invoker(self, x, instructions, boolean_response = False):
        if is_open_ai(x["model"]):
            from .gpt_invoker import GPT_Invoker
            return GPT_Invoker(
                        self.create_client(x["model"]),
                        instructions,
                        x["model"],
                        (x["reasoning"] if x["reasoning"] is not False else None),
                        (x["verbosity"] if x["verbosity"] is not False else None),
                        (x["temperature"] if x["temperature"] is not False else None),
                        (x["top_p"] if x["top_p"] is not False else None),
                        boolean_response)

        elif is_google(x["model"]):
            from .gemini_invoker import Gemini_Invoker
            return Gemini_Invoker(
                        self.create_client(x["model"]),
                        instructions,
                        x["model"],
                        (x["reasoning"] if x["reasoning"] is not False else None),
                        (x["verbosity"] if x["verbosity"] is not False else None),
                        (x["temperature"] if x["temperature"] is not False else None),
                        (x["top_p"] if x["top_p"] is not False else None),
                        boolean_response)
        else:
            raise ValueError("Error: Unknown LLM model.")

                             
    def create_client(self, model):

        if is_open_ai(model):

            if self.openai_client is None:
                api_key = keyring.get_password("Yiding", "OpenAI")

                if not api_key:
                    raise ValueError("No OpenAI API key is saved in Yiding.")

                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)

            client = self.openai_client

        elif is_google(model):

            if self.google_client is None:

                api_key = keyring.get_password("Yiding", "Google")

                if not api_key:
                    raise ValueError("No Google API key is saved in Yiding.")

                from google.genai import Client
                self.google_client = Client(api_key=api_key)

            client = self.google_client

        else:

            raise ValueError(f"Unknown model in settings: {model}")

        return client

# ------------------------------------------------------------------------------------------
