# ------------------------------------------------------------------------------------------
# invoker
# ------------------------------------------------------------------------------------------

from google.genai import types

import json

# ------------------------------------------------------------------------------------------

GPT_MODELS = ("o1", "o1-mini", "o1-pro",
              "o3", "o3-deep-research", "o4-mini-deep-research",
              "o4-mini")
GEMINI_MODELS = ()

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

GEMINI_BOOLEAN_SCHEMA = {
    "type": "object",
    "properties": {"b": {"type": "boolean"}},
    "required": ["b"],
    "additionalProperties": False}

_GEMINI_THINKING_LEVEL = {
    "high": types.ThinkingLevel.HIGH,
    "medium": types.ThinkingLevel.MEDIUM,
    "low": types.ThinkingLevel.LOW,
    "none": types.ThinkingLevel.MINIMAL,
    "minimal": types.ThinkingLevel.MINIMAL,}

# ------------------------------------------------------------------------------------------

class Invoker:

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

        if self.model in GPT_MODELS or self.model.startswith("gpt"):
            self.model_type = "gpt"
            self.reasoning = reasoning
        elif self.model in GEMINI_MODELS or self.model.startswith("gemini"):
            self.model_type = "gemini"
            self.reasoning = _GEMINI_THINKING_LEVEL.get((reasoning or "none").lower(),
                                                         types.ThinkingLevel.MINIMAL)
        else:
            raise ValueError("Error: Unknown LLM model.")

    def invoke(self, prompt,
               instructions = None):

        instructions = self.instructions if instructions is None else instructions

        if self.model_type == "gpt":
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
            
        elif self.model_type == "gemini":
            response = self.client.models.generate_content(
                model = self.model,
                contents = prompt,
                config = types.GenerateContentConfig(
                    system_instruction = instructions,
                    **({"thinking_config": types.ThinkingConfig(thinking_level = self.reasoning)}
                       if self.reasoning is not None else {}),
                    **({"temperature": self.temperature} if self.temperature is not None else {}),
                    **({"top_p": self.top_p} if self.top_p is not None else {}),
                    **({"response_mime_type": "application/json",
                        "response_json_schema": GEMINI_BOOLEAN_SCHEMA}
                       if self.boolean_response else {}))
                )
            if self.boolean_response:
                return json.loads(response.text)["b"]    # boolean True/False
            else:        
                return response.text

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
