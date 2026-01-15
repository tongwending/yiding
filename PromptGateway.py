############################################################################################
############################################################################################
############################################################################################
### PROMPT GATEWAY CLASS
############################################################################################
############################################################################################
############################################################################################


from openai import OpenAI

from GptInvoker import GptInvoker
import model_settings

############################################################################################


class PromptGateway:


    def __init__(self, language = None):

        from sk import my_sk            # Imports the personal OpenAI API Key to access GPT.

        self.client = OpenAI(api_key=my_sk)  # Reads the OpenAI API Key.

        self.language = language if language else model_settings.LANGUAGE
        

        self.punctuator = GptInvoker(self.client,
                    model_settings.instruct_punctuation(),
                    model_settings.PUNCTUATION_MODEL,
                    model_settings.PUNCTUATION_REASONING,
                    model_settings.PUNCTUATION_VERBOSITY,
                    model_settings.PUNCTUATION_TEMPERATURE)
                             
        self.glossary_selector = GptInvoker(self.client,
                    model_settings.instruct_glossary_selection(language = self.language),
                    model_settings.GLOSSARY_SELECTION_MODEL,
                    model_settings.GLOSSARY_SELECTION_REASONING,
                    model_settings.GLOSSARY_SELECTION_VERBOSITY,
                    model_settings.GLOSSARY_SELECTION_TEMPERATURE)

        self.translator = GptInvoker(self.client,
                    model_settings.instruct_translation(language = self.language),
                    model_settings.TRANSLATION_MODEL,
                    model_settings.TRANSLATION_REASONING,
                    model_settings.TRANSLATION_VERBOSITY,
                    model_settings.TRANSLATION_TEMPERATURE)

        self.cross_examinator = GptInvoker(self.client,
                    model_settings.instruct_cross_examination(language = self.language),
                    model_settings.CROSS_EXAMINATION_MODEL,
                    model_settings.CROSS_EXAMINATION_REASONING,
                    model_settings.CROSS_EXAMINATION_VERBOSITY,
                    model_settings.CROSS_EXAMINATION_TEMPERATURE)

        self.glossary_extractor = GptInvoker(self.client,
                    model_settings.instruct_glossary_extraction(language = self.language),
                    model_settings.GLOSSARY_EXTRACTION_MODEL,
                    model_settings.GLOSSARY_EXTRACTION_REASONING,
                    model_settings.GLOSSARY_EXTRACTION_VERBOSITY,
                    model_settings.GLOSSARY_EXTRACTION_TEMPERATURE)

        self.title_translator = GptInvoker(self.client,
                    model_settings.instruct_title_translation(language = self.language),
                    model_settings.TITLE_TRANSLATION_MODEL,
                    model_settings.TITLE_TRANSLATION_REASONING,
                    model_settings.TITLE_TRANSLATION_VERBOSITY,
                    model_settings.TITLE_TRANSLATION_TEMPERATURE)
        

        self.settings = f"punctuation:\n{self.punctuator.settings}"\
                      + f"glossary selection:\n {self.glossary_selector.settings}"\
                      + f"translation:\n {self.translator.settings}"\
                      + f"cross examination:\n {self.cross_examinator.settings}"\
                      + f"glossary extraction:\n {self.glossary_extractor.settings}"\
                      + f"title_translation:\n {self.title_translator.settings}"


############################################################################################


    def __getstate__(self):
        """Return picklable state (drop the OpenAI client)."""
        state = self.__dict__.copy()
        # client is not picklable
        state['client'] = None
        return state


    def __setstate__(self, state):
        """Restore state and recreate the OpenAI client."""
        self.__dict__.update(state)
        from sk import my_sk
        self.client = OpenAI(api_key=my_sk)
        # then re-bind every invoker to the client
        for inv in (
            self.punctuator,
            self.glossary_selector,
            self.translator,
            self.cross_examinator,
            self.glossary_extractor,
            self.title_translator,
        ):
            inv.bind_client(self.client)


############################################################################################
