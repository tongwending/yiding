# ------------------------------------------------------------------------------------------
# llm_lists
# ------------------------------------------------------------------------------------------

GPT_MODELS = (
    "o1",
    "o1-mini",
    "o1-pro",
    "o3",
    "o3-deep-research",
    "o4-mini-deep-research",
    "o4-mini",
    "gpt-5.2",
    "gpt-5.6"
)


GEMINI_MODELS = ()

# ------------------------------------------------------------------------------------------

def is_open_ai(model_name):

    if model_name in GPT_MODELS or model_name.startswith("gpt"):
        return True
    else:
        return False

def is_google(model_name):

    if model_name in GEMINI_MODELS or model_name.startswith("gemini"):
        return True
    else:
        return False
