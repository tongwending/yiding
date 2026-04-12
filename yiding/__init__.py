# ------------------------------------------------------------------------------------------
# __init__
# ------------------------------------------------------------------------------------------

"""
Public API:

- translate("kanripo_code",
            settings = "my_settings.toml",
            translated_title = "my_title",
            output_file = "docx", table = True, punctuation = True)
                 
- punctuate("kanripo_code",
            settings = "my_settings.toml",
            output_file = "docx")

- continue_translating("my_pickle.pkl",
                       output_file = "docx", table = True, punctuation = True)

- continue_punctuating("my_pickle.pkl",
                       output_file = "docx")

- translate_anew("my_pickle.pkl",
                 settings = "my_settings.toml",
                 translated_title = "my_title",
                 output_file = "docx", table = True, punctuation = True)

- translate_bulk(["kanripo_code_1", "kanripo_code_2", "kanripo_code_n"],
                 translated_titles = ["title_1", "title_2", "title_n"],
                 settings = "my_settings.toml",
                 output_file = "docx", table = True, punctuation = True)

- punctuate_bulk(["kanripo_code_1", "kanripo_code_2", "kanripo_code_n"],
                 settings = "my_settings.toml",
                 output_file = "docx")
                 
- get_settings()

- export("my_pickle.pkl",
         punctuation = False, translation = False,
         output_file = "docx", table = False)
         
- export_log("my_pickle.pkl")

- update_glossary("my_glossary.csv",
                  "my_pickle.pkl",
                  output_file = "my_glossary_v2.0.csv")
"""

# ------------------------------------------------------------------------------------------

from .commands import (
    translate,
    translate_bulk,
    punctuate,
    punctuate_bulk,
    continue_translating,
    continue_punctuating,
    translate_anew,
    get_settings,
    export,
    export_log,
    update_glossary,
)

__all__ = [
    "translate",
    "translate_bulk",
    "punctuate",
    "punctuate_bulk",
    "continue_translating",
    "continue_punctuating",
    "translate_anew",
    "get_settings",
    "export",
    "export_log",
    "update_glossary",
]

# ------------------------------------------------------------------------------------------


