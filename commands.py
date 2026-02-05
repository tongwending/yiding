# ------------------------------------------------------------------------------------------
# commands
# ------------------------------------------------------------------------------------------

import pickle
import importlib.util
from importlib.machinery import SourceFileLoader

from .kanripo_text import KanripoText
from .prompt_gateway import PromptGateway
from .workflow_orchestrator import WorkflowOrchestrator
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

    # initialize the three main objects
    text = KanripoText(kanripo_code)
    gate = PromptGateway(settings = _load_settings(settings) if settings else None)
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

    old_orchestrator = _load_pickle(filename)
    text = old_orchestrator.text
    gate = PromptGateway(settings = _load_settings(settings) if settings else None)
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

    # initialize the three main objects
    text = KanripoText(kanripo_code)
    gate = PromptGateway(settings = _load_settings(settings) if settings else None)
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

def export(filename, punctuation = False, translation = False,
           output_file = "docx", table = False):
    orchestrator = _load_pickle(filename)
    orchestrator.text.print_to_file(
                  punctuation = punctuation, translation = translation,
                  output_file = output_file, table = table)

# ------------------------------------------------------------------------------------------
# i/o
# ------------------------------------------------------------------------------------------

def _load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)

def _load_settings(filename):
    loader = SourceFileLoader("loaded_settings", filename)
    spec = importlib.util.spec_from_loader("loaded_settings", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
    
# ------------------------------------------------------------------------------------------
