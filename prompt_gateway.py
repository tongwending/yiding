############################################################################################
############################################################################################
############################################################################################
### PROMPT GATEWAY CLASS
############################################################################################
############################################################################################
############################################################################################


from openai import OpenAI
from google.genai import Client

from invoker import Invoker
import model_settings


############################################################################################


class PromptGateway:


    def __init__(self, language = None):

        import openai_sk            # Imports the personal OpenAI API Key to access GPT.
        self.openai_client = OpenAI(api_key = openai_sk.my_sk)  # Reads the OpenAI API Key.
        import google_sk            # Imports the personal Gemini API Key to access Gemini.
        self.google_client = Client(api_key = google_sk.my_sk)  # Reads the Gemini API Key.

        self.language = language if language else model_settings.LANGUAGE

        self.punctuation_span = model_settings.PUNCTUATION_SPAN
        self.translation_span = model_settings.TRANSLATION_SPAN
        self.max_unsegmented_span = model_settings.MAX_UNSEGMENTED_SPAN

        client = None
        if model_settings.PUNCTUATION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.PUNCTUATION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.punctuator = Invoker(client,
                    model_settings.instruct_punctuation(),
                    model_settings.PUNCTUATION_MODEL,
                    model_settings.PUNCTUATION_REASONING,
                    model_settings.PUNCTUATION_VERBOSITY,
                    model_settings.PUNCTUATION_TEMPERATURE)

        client = None
        if model_settings.GLOSSARY_SELECTION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.GLOSSARY_SELECTION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.glossary_selector = Invoker(client,
                    model_settings.instruct_glossary_selection(language = self.language),
                    model_settings.GLOSSARY_SELECTION_MODEL,
                    model_settings.GLOSSARY_SELECTION_REASONING,
                    model_settings.GLOSSARY_SELECTION_VERBOSITY,
                    model_settings.GLOSSARY_SELECTION_TEMPERATURE)

        client = None
        if model_settings.TRANSLATION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.TRANSLATION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.translator = Invoker(client,
                    model_settings.instruct_translation(language = self.language),
                    model_settings.TRANSLATION_MODEL,
                    model_settings.TRANSLATION_REASONING,
                    model_settings.TRANSLATION_VERBOSITY,
                    model_settings.TRANSLATION_TEMPERATURE)

        client = None
        if model_settings.TITLE_TRANSLATION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.TITLE_TRANSLATION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.title_translator = Invoker(client,
                    model_settings.instruct_title_translation(language = self.language),
                    model_settings.TITLE_TRANSLATION_MODEL,
                    model_settings.TITLE_TRANSLATION_REASONING,
                    model_settings.TITLE_TRANSLATION_VERBOSITY,
                    model_settings.TITLE_TRANSLATION_TEMPERATURE)

        client = None
        if model_settings.CROSS_EXAMINATION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.CROSS_EXAMINATION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.cross_examinator = Invoker(client,
                    model_settings.instruct_cross_examination(language = self.language),
                    model_settings.CROSS_EXAMINATION_MODEL,
                    model_settings.CROSS_EXAMINATION_REASONING,
                    model_settings.CROSS_EXAMINATION_VERBOSITY,
                    model_settings.CROSS_EXAMINATION_TEMPERATURE,
                    boolean_response = True)

        client = None
        if model_settings.CROSS_CORRECTION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.CROSS_CORRECTION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.cross_corrector = Invoker(client,
                    model_settings.instruct_cross_correction(language = self.language),
                    model_settings.CROSS_CORRECTION_MODEL,
                    model_settings.CROSS_CORRECTION_REASONING,
                    model_settings.CROSS_CORRECTION_VERBOSITY,
                    model_settings.CROSS_CORRECTION_TEMPERATURE)

        client = None
        if model_settings.GLOSSARY_EXTRACTION_MODEL[0:3] == "gpt":
            client = self.openai_client
        elif model_settings.GLOSSARY_EXTRACTION_MODEL[0:6] == "gemini":
            client = self.google_client
        self.glossary_extractor = Invoker(client,
                    model_settings.instruct_glossary_extraction(language = self.language),
                    model_settings.GLOSSARY_EXTRACTION_MODEL,
                    model_settings.GLOSSARY_EXTRACTION_REASONING,
                    model_settings.GLOSSARY_EXTRACTION_VERBOSITY,
                    model_settings.GLOSSARY_EXTRACTION_TEMPERATURE)
        
        self.settings = f"punctuation:\n{self.punctuator.settings}"\
                      + f"glossary selection:\n {self.glossary_selector.settings}"\
                      + f"translation:\n {self.translator.settings}"\
                      + f"title_translation:\n {self.title_translator.settings}"\
                      + f"cross examination:\n {self.cross_examinator.settings}"\
                      + f"cross correction:\n {self.cross_corrector.settings}"\
                      + f"glossary extraction:\n {self.glossary_extractor.settings}"
                      

############################################################################################


    def __getstate__(self):
        """Return picklable state (drop the LLM clients)."""
        state = self.__dict__.copy()
        # client is not picklable
        state.pop("openai_client", None)
        state.pop("google_client", None)
        return state


    def __setstate__(self, state):
        """Restore state and recreate the LLM clients."""
        self.__dict__.update(state)
        import openai_sk
        self.openai_client = OpenAI(api_key= openai_sk.my_sk)
        import google_sk
        self.google_client = Client(api_key= google_sk.my_sk)
        # then re-bind every invoker to the client
        for inv in (
            self.punctuator,
            self.glossary_selector,
            self.translator,
            self.cross_examinator,
            self.cross_corrector,
            self.glossary_extractor,
            self.title_translator,
        ):
            if inv.model[0:3] == "gpt":
                inv.bind_client(self.openai_client)
            elif inv.model[0:6] == "gemini":
                inv.bind_client(self.google_client)


############################################################################################
