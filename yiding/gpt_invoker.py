# ------------------------------------------------------------------------------------------
# gpt_invoker
# ------------------------------------------------------------------------------------------

import json

# ------------------------------------------------------------------------------------------

GPT_BOOLEAN_SCHEMA = {
    "type": "json_schema",
    "name": "bool_only",
    "strict": True,
    "schema": {
            "type": "object",
            "properties": {"b": {"type": "boolean"}},
            "required": ["b"],
            "additionalProperties": False}}

# ------------------------------------------------------------------------------------------

class GPT_Invoker:

    def __init__(self, client,
                 instructions,
                 model,
                 reasoning,
                 verbosity,
                 temperature,
                 top_p,
                 boolean_response = False):

        self.client = client

        self.instructions = instructions
        self.model = model
        self.verbosity = verbosity
        self.temperature = temperature
        self.top_p = top_p
        self.boolean_response = boolean_response
        self.reasoning = reasoning

    def invoke(self, prompt,
               instructions = None):

        instructions = self.instructions if instructions is None else instructions

        response = self.client.responses.create(
                model = self.model,
                instructions = instructions,
                input = prompt,
                **({"reasoning": {"effort": self.reasoning}} if self.reasoning is not None else {}),
                text = {
                    **({"verbosity": self.verbosity} if self.verbosity is not None else {}),
                       **({"format": GPT_BOOLEAN_SCHEMA} if self.boolean_response else {})
                        },
                **({"temperature": self.temperature} if self.temperature is not None else {}),
                **({"top_p": self.top_p} if self.top_p is not None else {})
                )
        if self.boolean_response:
            return json.loads(response.output_text)["b"]    # boolean True/False
        else:        
            return response.output_text
            
# ------------------------------------------------------------------------------------------

    def __getstate__(self):
        """Return picklable state (drop the LLM client)."""
        state = self.__dict__.copy()
        # client is not picklable
        state['client'] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.client = None  # PromptGateway will re-bind client

    def bind_client(self, client): # PromptGateway uses this to re-bind client
        self.client = client
        
# ------------------------------------------------------------------------------------------
