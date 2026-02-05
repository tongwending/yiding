# ------------------------------------------------------------------------------------------
# __init__
# ------------------------------------------------------------------------------------------

"""
Public API:

- translate("kanripo_code",
            settings = "my_settings.py",
            translated_title = "my_title",
            output_file = "docx", table = True, punctuation = True)
                 
- punctuate("kanripo_code",
            settings = "my_settings.py",
            output_file = "docx")

- continue_translating("my_pickle.pkl",
                       output_file = "docx", table = True, punctuation = True)

- continue_punctuating("my_pickle.pkl",
                       output_file = "docx")

- translate_anew("my_pickle.pkl",
                 settings = "my_settings.py",
                 translated_title = "my_title",
                 output_file = "docx", table = True, punctuation = True)

- translate_bulk(["kanripo_code_1", "kanripo_code_2", "kanripo_code_n"],
                 translated_titles = ["title_1", "title_2", "title_n"],
                 settings = "my_settings.py",
                 list_of_translated_titles = None,
                 output_file = "docx", table = True, punctuation = True)

- punctuate_bulk(["kanripo_code_1", "kanripo_code_2", "kanripo_code_n"],
                 settings = "my_settings.py",
                 output_file = "docx")

- export("my_pickle.pkl",
         punctuation = False, translation = False
         output_file = "docx", table = False)
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
    export,
)

__all__ = [
    "translate",
    "translate_bulk",
    "punctuate",
    "punctuate_bulk",
    "continue_translating",
    "continue_punctuating",
    "translate_anew",
    "export",
]

# ------------------------------------------------------------------------------------------


