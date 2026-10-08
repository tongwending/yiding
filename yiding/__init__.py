# ------------------------------------------------------------------------------------------
# __init__
# ------------------------------------------------------------------------------------------

"""
Public API:

- create_yiding(
      "my_project.yiding",
      unpunctuated_text = "...",
      unpunctuated_divider = "\\n",
      original_title = "My Title",
      settings = "my_settings.toml",
  )

- translate(
      "my_project.yiding",
      settings = "my_settings.toml",
      output_file = "docx",
      table = True,
      punctuation = True,
  )

- translate_bulk(
      ["project_1.yiding", "project_2.yiding"],
      settings = "my_settings.toml",
      output_file = "docx",
      table = True,
      punctuation = True,
  )

- translate_anew(
      "my_project.yiding",
      settings = "my_settings.toml",
      translated_title = "My Title",
      output_file = "docx",
      table = True,
      punctuation = True,
  )

- translate_from_kanripo(
      "KR5h0008",
      settings = "my_settings.toml",
      translated_title = "My Title",
      output_file = "docx",
      table = True,
      punctuation = True,
  )

- translate_bulk_from_kanripo(
      ["KR5h0008", "KR5a0001"],
      settings = "my_settings.toml",
      translated_titles = ["Title 1", "Title 2"],
      output_file = "docx",
      table = True,
      punctuation = True,
  )

- punctuate(
      "my_project.yiding",
      settings = "my_settings.toml",
      output_file = "docx",
  )

- punctuate_bulk(
      ["project_1.yiding", "project_2.yiding"],
      settings = "my_settings.toml",
      output_file = "docx",
  )

- punctuate_from_kanripo(
      "KR5h0008",
      settings = "my_settings.toml",
      output_file = "docx",
  )

- punctuate_bulk_from_kanripo(
      ["KR5h0008", "KR5a0001"],
      settings = "my_settings.toml",
      output_file = "docx",
  )

- set_key(
      provider: (openai, google)
      api_key
  )

- get_settings()

- export(
      "my_project.yiding",
      punctuation = False,
      translation = False,
      output_file = "docx",
      table = False,
  )

- export_log(
      "my_project.yiding"
  )

- update_glossary(
      "my_glossary.csv",
      "my_project.yiding",
      output_file = "my_glossary_v2.0.csv",
  )
"""

# ------------------------------------------------------------------------------------------

from .commands import (
    create_yiding,

    translate,
    translate_bulk,
    translate_anew,
    translate_from_kanripo,
    translate_bulk_from_kanripo,

    punctuate,
    punctuate_bulk,
    punctuate_from_kanripo,
    punctuate_bulk_from_kanripo,

    set_key,
    get_settings,
    export,
    export_log,
    update_glossary,
)

__all__ = [
    "create_yiding",

    "translate",
    "translate_bulk",
    "translate_anew",
    "translate_from_kanripo",
    "translate_bulk_from_kanripo",

    "punctuate",
    "punctuate_bulk",
    "punctuate_from_kanripo",
    "punctuate_bulk_from_kanripo",

    "set_key",
    "get_settings",
    "export",
    "export_log",
    "update_glossary",
]

# ------------------------------------------------------------------------------------------
