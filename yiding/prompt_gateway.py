# ------------------------------------------------------------------------------------------
# prompt_gateway
# ------------------------------------------------------------------------------------------

# imports inside code:
# from openai import OpenAI
# from google.genai import Client
# from .gpt_invoker import GPT_Invoker
# from .gemini_invoker import Gemini_Invoker

from . import instructors

# ------------------------------------------------------------------------------------------

GPT_MODELS = ("o1", "o1-mini", "o1-pro",
              "o3", "o3-deep-research", "o4-mini-deep-research",
              "o4-mini")

GEMINI_MODELS = ()

NO_API_KEY_ERROR = "Error: No API key in file."

# ------------------------------------------------------------------------------------------

class PromptGateway:

    def __init__(self, settings):

        self.settings = settings

        self.openai_client = None
        self.google_client = None
        
        self.invokers = []

        if self.settings["punctuation"]["enabled"]:
        
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

        if self.settings["translation"]["enabled"]:
            
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

        self.log = ""
        for inv in self.invokers:
            self._update_log(f"------------\n{inv.instructions}")
    
    def _update_log(self, text):
        text = f"\n{text}\n"
        self.log += text

    def create_invoker(self, x, instructions, boolean_response = False):
        if x["model"] in GPT_MODELS or x["model"].startswith("gpt"):
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

        elif x["model"] in GEMINI_MODELS or x["model"].startswith("gemini"):
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
        
        if model in GPT_MODELS or model.startswith("gpt"):
            if self.openai_client is None:
                if self.settings["api_serial_keys"]["openai"].lower().endswith(".txt"):
                    with open(self.settings["api_serial_keys"]["openai"],"r",encoding="utf-8") as f:
                        api_key = f.read().strip()
                        if not api_key:
                            raise ValueError(NO_API_KEY_ERROR)
                else:
                    api_key = self.settings["api_serial_keys"]["openai"]
                from openai import OpenAI
                self.openai_client = OpenAI(api_key = api_key)
            client = self.openai_client

        elif model in GEMINI_MODELS or model.startswith("gemini"):
            if self.google_client is None:
                if self.settings["api_serial_keys"]["google"].lower().endswith(".txt"):
                    with open(self.settings["api_serial_keys"]["google"],"r",encoding="utf-8") as f:
                        api_key = f.read().strip()
                        if not api_key:
                            raise ValueError(NO_API_KEY_ERROR)
                else:
                    api_key = self.settings["api_serial_keys"]["google"]
                from google.genai import Client
                self.google_client = Client(api_key = api_key)
            client = self.google_client

        else:
            raise ValueError(f"Unknown model in settings: {model}")

        return client

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
        for inv in self.invokers:
            inv.bind_client(self.create_client(inv.model))

# ------------------------------------------------------------------------------------------
