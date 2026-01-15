############################################################################################
############################################################################################
############################################################################################
### CAULDRON: MAIN
############################################################################################
############################################################################################
############################################################################################


def main():


    Translate_From_Kanripo("KR5a0006", glossary = "my_glossary.csv")

    # This part is for later:
    # Continue_Translation("KR5a0006 - gpt-5.1 - PUNlow - GLSELlow - TRANSmedium - GLEXTlow.pkl",\
    #                     instructions = PromptEngine())


############################################################################################

# Standard libraries:
import pickle

# Cauldron modules:
from KanripoText import KanripoText
from PromptGateway import PromptGateway
from WorkflowOrchestrator import WorkflowOrchestrator
from glossary_dictate import *



############################################################################################
# USER COMMANDS
############################################################################################


def Translate_Kanripo_Corpus(kanripo_corpus_code,
                             instructions = None,
                             glossary = None):
    # This function is not used now but might be handy later.

    for i in range(1, 9999):
        kanripo_code = f"{kanripo_corpus_code}{i:04d}"
        try:
            Translate_From_Kanripo(kanripo_code,
                                   instructions = instructions,
                                   glossary = glossary)
        except Exception as e:
            print(f"Stopped at {kanripo_code} because of error: {e}")
            break
    
    herald_of_the_end()


############################################################################################


def Translate_From_Kanripo(kanripo_code,
                           language = None,
                           glossary = None):

    text = KanripoText(kanripo_code)

    gate = PromptGateway(language = language)

    orchestrator = WorkflowOrchestrator(text, gate,
                                glossary = load_glossary(glossary) if glossary else None)

    orchestrator.resume_translation()
    
    orchestrator.text.translation_to_docx()

    herald_of_the_end()


############################################################################################


def Continue_Translation(filename):

    orchestrator = load_pickle(filename)

    orchestrator.resume_translation()

    orchestrator.text.translation_to_docx()
    
    herald_of_the_end()


############################################################################################
# I/O
############################################################################################


def load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


############################################################################################


def scribe_translation_to_word_document(text):

    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    
    # Assign Word document class.
    doc = Document()

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)

   
    p = doc.add_paragraph()   # create an empty paragraph.

    # 1) Chinese title
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_cn = p.add_run("\n\n\n" + text.chinese_title)
    run_cn.font.name = 'SimSun'
    run_cn.font.size = Pt(28)
    run_cn.font.bold = True
    run_cn.font.color.rgb = RGBColor(0, 0, 0)
    r_cn = run_cn._element.rPr.rFonts
    r_cn.set(qn('w:eastAsia'), 'SimSun')

    # 2) English title
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_en = p.add_run(text.translated_title)
    run_en.font.name = 'Times New Roman'
    run_en.font.size = Pt(18)
    run_en.font.bold = True
    run_en.font.color.rgb = RGBColor(0, 0, 0)
    r_en = run_en._element.rPr.rFonts
    r_en.set(qn('w:eastAsia'), 'Times New Roman')


    doc.add_page_break()

    p = doc.add_paragraph()
    
    # 3) Properties
    properties_text = ""
    for prop in text.properties:
        properties_text += (prop + "\n\n")
    GPT_properties_text = ("GPT Prompting Properties:\n\n" + \
        f"punctuation reasoning: {text.prompt_engine.punctuation_GPT_reasoning}\n" + \
        f"glossary selection reasoning: {text.prompt_engine.glossary_selection_GPT_reasoning}\n" + \
        f"translation reasoning: {text.prompt_engine.translation_GPT_reasoning}\n" + \
        f"glossary extraction reasoning: {text.prompt_engine.glossary_extraction_GPT_reasoning}")
    run_num = p.add_run(f"{properties_text}\n{GPT_properties_text}")
    run_num.font.name = 'Times New Roman'
    run_num.font.size = Pt(12)
    run_num.font.color.rgb = RGBColor(0, 0, 0)
    r_num = run_num._element.rPr.rFonts
    r_num.set(qn('w:eastAsia'), 'Times New Roman')


    doc.add_page_break()
    
    # Fill in the segments.
    
    current_juan = 0

    for i in range(0, text.number_of_completed_segments):
        
        if "." in text.page_labels[i]:
            juan = int(text.page_labels[i].split(".", 1)[0])
            if juan != current_juan:
                current_juan = juan
    
                doc.add_page_break()
                
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(f"{juan}\n")
                run.font.size = Pt(19)
                run.font.name = 'Times New Roman'
                run.font.bold = True
                # Makes sure Word treats it as East Asian font
                r = run._element.rPr.rFonts
                r.set(qn('w:eastAsia'), 'Times New Roman')

        p = doc.add_paragraph()

        # Chapter and section
        run = p.add_run(text.page_labels[i] + "")
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'
        run.font.bold = True
        # Makes sure Word treats it as East Asian font
        r = run._element.rPr.rFonts
        r.set(qn('w:eastAsia'), 'Times New Roman')

        # Original text
       # p = doc.add_paragraph()
        
       # run = p.add_run("Original text:\n" + text.segments[i][j] + "\n")
       # run.font.size = Pt(12)
       # run.font.name = 'SimSun'
       # # Makes sure Word treats it as East Asian font
       # r = run._element.rPr.rFonts
       # r.set(qn('w:eastAsia'), 'SimSun')

        # Punctuated text
        p = doc.add_paragraph()
        
        run = p.add_run(text.punctuated_segments[i])
        run.font.size = Pt(12)
        run.font.name = 'SimSun'
        # Makes sure Word treats it as East Asian font
        r = run._element.rPr.rFonts
        r.set(qn('w:eastAsia'), 'SimSun')            

        # Translated text
        p = doc.add_paragraph()

        run = p.add_run(text.translated_segments[i])
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'
        # Makes sure Word treats it as East Asian font
        r = run._element.rPr.rFonts
        r.set(qn('w:eastAsia'), 'Times New Roman')

    
    doc.save(f'{text.full_title()}.docx')   

        
############################################################################################
############################################################################################
############################################################################################


def herald_of_the_end():
        print(r"""\n\n\n
          __________-------____                 ____-------__________\n
          \------____-------___--__---------__--___-------____------/\n
           \//////// / / / / / \   _-------_   / \ \ \ \ \ \\\\\\\\/\n
             \////-/-/------/_/_| /___   ___\ |_\_\------\-\-\\\\/\n
               --//// / /  /  //|| (O)\ /(O) ||\\  \  \ \ \\\\--\n
                    ---__/  // /| \_  /V\  _/ |\ \\  \__---\n
                         -//  / /\_ ------- _/\ \  \\-\n
                           \_/_/ /\---------/\ \_\_/\n
                               ----\   |   /----\n
                                    | -|- |\n
                                   /   |   \\n
                                   ---- \___|\n""")


############################################################################################


if __name__ == '__main__':
    main()

