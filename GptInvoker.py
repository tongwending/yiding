############################################################################################
############################################################################################
############################################################################################
### GPT INVOKER CLASS
############################################################################################
############################################################################################
############################################################################################


import json


############################################################################################


BOOLEAN_SCHEMA = {
    "type": "json_schema",
    "name": "bool_only",
    "strict": True,
    "schema": {
            "type": "object",
            "properties": {"b": {"type": "boolean"}},
            "required": ["b"],
            "additionalProperties": False}}



############################################################################################


class GptInvoker:


    def __init__(self, client,
                 instructions,
                 model,
                 reasoning,
                 verbosity,
                 temperature,
                 boolean_response = False):

        self.client = client

        self.instructions = instructions
        self.model = model
        self.reasoning = reasoning
        self.verbosity = verbosity
        self.temperature = temperature
        self.boolean_response = boolean_response

        self.settings =  f"- model: {self.model}\n"\
                       + f"- reasoning: {self.reasoning}\n"\
                       + f"- verbosity: {self.verbosity}\n"\
                       + f"- temperature: {self.temperature}"


    def invoke(self, prompt,
               instructions = None,
               model = None,
               reasoning = None,
               verbosity = None,
               temperature = None):

        instructions = instructions if instructions else self.instructions
        model = model if model else self.model
        reasoning = reasoning if reasoning else self.reasoning
        verbosity = verbosity if verbosity else self.verbosity
        temperature = temperature if temperature else self.temperature
        
        response = self.client.responses.create(
                model = model,
                input=[
                    {
                        "role": "developer",
                        "content": instructions
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }],
                reasoning={"effort": reasoning},
                text={"verbosity": verbosity,
                      **({"format": BOOLEAN_SCHEMA} if self.boolean_response else {} )
                      },
                temperature = temperature
                )

        if self.boolean_response:
            return json.loads(response.output_text)["b"]    # boolean True/False
        else:        
            return response.output_text
            

############################################################################################


    def __getstate__(self):
        """Return picklable state (drop the OpenAI client)."""
        state = self.__dict__.copy()
        # client is not picklable
        state['client'] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.client = None  # PromptGateway will re-bind client

    def bind_client(self, client): # PromptGateway uses this to re-bind client
        self.client = client
        
        
############################################################################################
