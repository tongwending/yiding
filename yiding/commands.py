# ------------------------------------------------------------------------------------------
# commands
# ------------------------------------------------------------------------------------------

import pickle
import os
import tomllib

from .kanripo_text import KanripoText
from .prompt_gateway import PromptGateway
from .workflow_orchestrator import WorkflowOrchestrator
from . import glossary_dictate
from . import ding

# ------------------------------------------------------------------------------------------

def translate_bulk(kanripo_codes, settings = None,
                   translated_titles = None,
                   output_file = "docx", table = True, punctuation = True):

    if kanripo_codes and translated_titles:
        if len(kanripo_codes) != len(translated_titles):
            raise ValueError("Error: Unequal number of kanripo codes and translated titles.")

    for i in range(0, len(kanripo_codes)):
        translate(kanripo_codes[i], settings = settings,
                  translated_title = translated_titles[i] if translated_titles else None, 
                  punctuation = punctuation, output_file = output_file, table = table)
        
    print(ding.DING)

# ------------------------------------------------------------------------------------------

def translate(kanripo_code, settings = None,
              translated_title = None,
              output_file = "docx", table = True, punctuation = True):

    settings = _load_settings(settings if settings else "settings.toml")

    # initialize the three main objects
    text = KanripoText(kanripo_code)
    gate = PromptGateway(settings)
    orchestrator = WorkflowOrchestrator(text, gate)

    if translated_title:
        orchestrator.text.translated_title = translated_title

    # start the process
    orchestrator.resume_translation()
    print(ding.DING)
    orchestrator.text.print_to_file(
                   punctuation = punctuation, translation = True,
                   output_file = output_file, table = table)

# ------------------------------------------------------------------------------------------

def continue_translating(filename,
                         output_file = "docx", table = True, punctuation = True):

    orchestrator = _load_pickle(filename)
    
    orchestrator.resume_translation()
    print(ding.DING)
    orchestrator.text.print_to_file(
                  punctuation = punctuation, translation = True,
                  output_file = output_file, table = table)

# ------------------------------------------------------------------------------------------

def translate_anew(filename, settings = None,
                   translated_title = None,
                   output_file = "docx", table = True, punctuation = True):

    settings = _load_settings(settings if settings else "settings.toml")
    settings["punctuation"]["enabled"] = False

    old_orchestrator = _load_pickle(filename)
    text = old_orchestrator.text
    gate = PromptGateway(settings)
    orchestrator = WorkflowOrchestrator(text, gate)

    orchestrator.text.empty_translation()

    if translated_title:
        orchestrator.text.translated_title = translated_title
    
    orchestrator.resume_translation()
    print(ding.DING)
    orchestrator.text.print_to_file(
                  punctuation = punctuation, translation = True,
                  output_file = output_file, table = table)
    
# ------------------------------------------------------------------------------------------

def punctuate_bulk(list_of_kanripo_codes, settings = None, output_file = "docx"):

    for x in list_of_kanripo_codes:
        punctuate(x, settings = settings,
                  output_file = output_file)
        
    print(ding.DING)

# ------------------------------------------------------------------------------------------

def punctuate(kanripo_code, settings = None, output_file = "docx"):

    settings =  _load_settings(settings if settings else "settings.toml")
    settings["translation"]["enabled"] = False

    # initialize the three main objects
    text = KanripoText(kanripo_code)
    gate = PromptGateway(settings)
    orchestrator = WorkflowOrchestrator(text, gate)
    
    # start the process
    orchestrator.resume_punctuation()
    print(ding.DING)
    orchestrator.text.print_to_file(
        punctuation = True, translation = False,
        output_file = output_file, table = False)

# ------------------------------------------------------------------------------------------

def continue_punctuating(filename, output_file = "docx"):
    orchestrator = _load_pickle(filename)
    orchestrator.resume_punctuation()
    print(ding.DING)
    orchestrator.text.print_to_file(
                  punctuation = True, translation = False,
                  output_file = output_file, table = False)

# ------------------------------------------------------------------------------------------
# i/o
# ------------------------------------------------------------------------------------------

def get_settings():
    source = os.path.join(os.path.dirname(__file__), "settings.toml")
    destination = os.path.join(os.getcwd(), "settings.toml")

    with open(source, "rb") as src, open(destination, "wb") as dst:
        dst.write(src.read())

    print(f"Copied settings.toml to {destination}")

# ------------------------------------------------------------------------------------------

def export(filename, punctuation = False, translation = False,
           output_file = "docx", table = False):
    orchestrator = _load_pickle(filename)
    orchestrator.text.print_to_file(
                  punctuation = punctuation, translation = translation,
                  output_file = output_file, table = table)

# ------------------------------------------------------------------------------------------

def export_log(filename):
    orchestrator = _load_pickle(filename)
    title, extension = os.path.splitext(filename)
    output_file = title + "_LOG.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(orchestrator.log)

# ------------------------------------------------------------------------------------------

def update_glossary(glossaryfile, picklefile, output_file = None):
    base_glossary = glossary_dictate.load_glossary(glossaryfile)
    orchestrator = _load_pickle(picklefile)
    glossary_dictate.update_glossary(base_glossary, orchestrator.text.translation_glossary)

    glossary_dictate.glossary_to_csv(base_glossary,
                                    (output_file if output_file else glossaryfile))
    
# ------------------------------------------------------------------------------------------

def _load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)

def _load_settings(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return tomllib.loads(f.read())
    
# ------------------------------------------------------------------------------------------
