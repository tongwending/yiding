# ------------------------------------------------------------------------------------------
# prompt_gateway
# ------------------------------------------------------------------------------------------

# Potential imports:
# from openai import OpenAI
# from google.genai import Client

from types import SimpleNamespace

from .invoker import Invoker
from . import default_settings
from . import instructors


# ------------------------------------------------------------------------------------------

NO_API_KEY_ERROR = "Error: No API key in file."

# ------------------------------------------------------------------------------------------

class PromptGateway:

    def __init__(self, settings = None):

        self.settings = SimpleNamespace(**{
                k: v for k, v in vars(settings if settings else default_settings).items()
                if not k.startswith("_")
                                           })
        self.openai_client = None
        self.google_client = None
        
        self.punctuator = Invoker(
                    self.create_client(self.settings.PUNCTUATION_MODEL),
                    instructors.instruct_punctuation(self.settings),
                    self.settings.PUNCTUATION_MODEL,
                    self.settings.PUNCTUATION_REASONING,
                    self.settings.PUNCTUATION_VERBOSITY,
                    self.settings.PUNCTUATION_TEMPERATURE,
                    self.settings.PUNCTUATION_TOP_P)
        
        self.punctuation_examinator = Invoker(
                    self.create_client(self.settings.PUNCTUATION_EXAMINATION_MODEL),
                    instructors.instruct_punctuation_examination(),
                    self.settings.PUNCTUATION_EXAMINATION_MODEL,
                    self.settings.PUNCTUATION_EXAMINATION_REASONING,
                    self.settings.PUNCTUATION_EXAMINATION_VERBOSITY,
                    self.settings.PUNCTUATION_EXAMINATION_TEMPERATURE,
                    self.settings.PUNCTUATION_EXAMINATION_TOP_P,
                    boolean_response = True)
        
        self.punctuation_corrector = Invoker(
                    self.create_client(self.settings.PUNCTUATION_CORRECTION_MODEL),
                    instructors.instruct_punctuation_correction(self.settings),
                    self.settings.PUNCTUATION_CORRECTION_MODEL,
                    self.settings.PUNCTUATION_CORRECTION_REASONING,
                    self.settings.PUNCTUATION_CORRECTION_VERBOSITY,
                    self.settings.PUNCTUATION_CORRECTION_TEMPERATURE,
                    self.settings.PUNCTUATION_CORRECTION_TOP_P)

        if not self.settings.LLM_GLOSSARY_SELECTION:
            self.glossary_selector = None
        else:
            self.glossary_selector = Invoker(
                        self.create_client(self.settings.GLOSSARY_SELECTION_MODEL),
                        instructors.instruct_glossary_selection(self.settings),
                        self.settings.GLOSSARY_SELECTION_MODEL,
                        self.settings.GLOSSARY_SELECTION_REASONING,
                        self.settings.GLOSSARY_SELECTION_VERBOSITY,
                        self.settings.GLOSSARY_SELECTION_TEMPERATURE,
                        self.settings.GLOSSARY_SELECTION_TOP_P)

        self.translator = Invoker(
                    self.create_client(self.settings.TRANSLATION_MODEL),
                    instructors.instruct_translation(self.settings),
                    self.settings.TRANSLATION_MODEL,
                    self.settings.TRANSLATION_REASONING,
                    self.settings.TRANSLATION_VERBOSITY,
                    self.settings.TRANSLATION_TEMPERATURE,
                    self.settings.TRANSLATION_TOP_P)

        self.translation_examinator = Invoker(
                    self.create_client(self.settings.TRANSLATION_EXAMINATION_MODEL),
                    instructors.instruct_translation_examination(self.settings),
                    self.settings.TRANSLATION_EXAMINATION_MODEL,
                    self.settings.TRANSLATION_EXAMINATION_REASONING,
                    self.settings.TRANSLATION_EXAMINATION_VERBOSITY,
                    self.settings.TRANSLATION_EXAMINATION_TEMPERATURE,
                    self.settings.TRANSLATION_EXAMINATION_TOP_P,
                    boolean_response = True)

        self.translation_corrector = Invoker(
                    self.create_client(self.settings.TRANSLATION_CORRECTION_MODEL),
                    instructors.instruct_translation_correction(self.settings),
                    self.settings.TRANSLATION_CORRECTION_MODEL,
                    self.settings.TRANSLATION_CORRECTION_REASONING,
                    self.settings.TRANSLATION_CORRECTION_VERBOSITY,
                    self.settings.TRANSLATION_CORRECTION_TEMPERATURE,
                    self.settings.TRANSLATION_CORRECTION_TOP_P)

        self.glossary_extractor = Invoker(
                    self.create_client(self.settings.GLOSSARY_EXTRACTION_MODEL),
                    instructors.instruct_glossary_extraction(self.settings),
                    self.settings.GLOSSARY_EXTRACTION_MODEL,
                    self.settings.GLOSSARY_EXTRACTION_REASONING,
                    self.settings.GLOSSARY_EXTRACTION_VERBOSITY,
                    self.settings.GLOSSARY_EXTRACTION_TEMPERATURE,
                    self.settings.GLOSSARY_EXTRACTION_TOP_P)
                      
# ------------------------------------------------------------------------------------------

    def create_client(self, model):
        
        if model[0:3] == "gpt":
            if self.openai_client is None:
                if self.settings.OPEN_AI_API_KEY.lower().endswith(".txt"):
                    with open(self.settings.OPEN_AI_API_KEY,"r",encoding="utf-8") as f:
                        api_key = f.read().strip()
                        if not api_key:
                            raise ValueError(NO_API_KEY_ERROR)
                else:
                    api_key = self.settings.OPEN_AI_API_KEY
                from openai import OpenAI
                self.openai_client = OpenAI(api_key = api_key)
            client = self.openai_client

        elif model[0:6] == "gemini":
            if self.google_client is None:
                if self.settings.GOOGLE_API_KEY.lower().endswith(".txt"):
                    with open(self.settings.GOOGLE_API_KEY,"r",encoding="utf-8") as f:
                        api_key = f.read().strip()
                        if not api_key:
                            raise ValueError(NO_API_KEY_ERROR)
                else:
                    api_key = self.settings.GOOGLE_API_KEY
                from google.genai import Client
                self.google_client = Client(api_key = api_key)
            client = self.google_client

        else:
            raise ValueError(f"Unknown model in settings: {model}")

        return client

# ------------------------------------------------------------------------------------------

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
        # emtpy possible old clients:
        self.openai_client = None
        self.google_client = None
        # re-bind every invoker to the client creating new clients on the way:
        for inv in (
            self.punctuator,
            self.punctuation_examinator,
            self.punctuation_corrector,
            *((self.glossary_selector,) if self.glossary_selector else ()),
            self.translator,
            self.translation_examinator,
            self.translation_corrector,
            self.glossary_extractor,
        ):
            inv.bind_client(self.create_client(inv.model))

# ------------------------------------------------------------------------------------------
