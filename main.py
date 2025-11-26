





############################################################################################
############################################################################################
############################################################################################
### CAULDRON PROJECT
############################################################################################
############################################################################################
############################################################################################


def main():


    Translate_From_Kanripo("KR5a0006", glossary = "my_glossary.csv")

    # This part is for later:
    # Continue_Translation("KR5a0006 - gpt-5.1 - PUNlow - GLSELlow - TRANSmedium - GLEXTlow.pkl",\
    #                     instructions = InstructionsProfile())


############################################################################################

# Standard libraries:

# Third-party libraries:
from openai import OpenAI

# Cauldron modules:
from kanripo_fetch import fetch_from_kanripo
from glossary_dictate import *
from gpt_engines import *


############################################################################################
# LEVEL 0: USER COMMANDS
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


def Translate_From_Kanripo(kanripo_code, instructions = None, glossary = None):

    text = KanripoText(kanripo_code)

    if instructions:
        text.instructions = instructions

    if glossary:
        update_glossary(text.instructions.glossary, load_glossary(glossary))
        
    text.resume_translation()

    text.translation_to_docx()

    herald_of_the_end()


############################################################################################


def Continue_Translation(filename, instructions = None, glossary = None):

    text = load_pickle(filename)

    if instructions:
        text.instructions = instructions

    if glossary:
        update_glossary(text.instructions.glossary, load_glossary(glossary))

    text.resume_translation()

    text.translation_to_docx()
    
    herald_of_the_end()

    

############################################################################################
# LEVEL -1: CLASSES
############################################################################################


class KanripoText:
    

    def __init__(self, kanripo_code: str):

        self.kanripo_code = kanripo_code

        self.Chinese_title, self.properties, self.page_labels, self.segments = \
                                                    fetch_from_kanripo(self.kanripo_code)
        self.instructions = InstructionsProfile()
        
        self.translated_title = "Untranslated Title"
        

        # Inquisition attributes:
        self.cites = []
        for i in range(0, len(self.page_labels)):
            self.cites.append(f"{self.kanripo_code} {self.page_labels[i]}")
        self.citelogs = []

        
        # Translation attributes:
        self.translation_glossary = {}
        self.punctuated_segments = []
        self.segment_glossaries = []
        self.translated_segments = []
        self.number_of_completed_segments = 0
        

        save_pickle(self, f"{self.kanripo_code} {self.Chinese_title}.pkl")
        

    def resume_translation(self):

        if self.translated_title == "Untranslated Title":
            self.translate_title()
        
        for i in range(self.number_of_completed_segments, len(self.segments)):

            print(f"\n{self.page_labels[i]}\n")

            #punctuate:

            if i == 0:
                self.punctuated_segments.append(GPT_Punctuator(i, self))
            if i < len(self.segments)-1:
                self.punctuated_segments.append(GPT_Punctuator(i+1, self))                           
            
            #create_glossaries:
        
            segment_glossary = {}

            pre_segment =self.punctuated_segments[i-1] if i > 0 else None
            fol_segment =self.punctuated_segments[i+1] if i < len(self.segments)-1 else None


            selection_text = GPT_Glossary_Selector(self.instructions,
                                                    self.punctuated_segments[i],
                                                    preceding_section = pre_segment,
                                                    following_section = fol_segment)

            for term in selection_text.splitlines():
                    if term in self.instructions.glossary:
                           segment_glossary[term] = self.instructions.glossary[term]
                
            self.segment_glossaries.append(segment_glossary)
            
            # translate:
        
            self.translated_segments.append(GPT_Translator(i, self))

            # extract_glossary:
        
            extracted_glossary = GPT_Glossator(i, self)
            update_glossary(self.instructions.glossary, extracted_glossary)
            update_glossary(self.translation_glossary, extracted_glossary)

            # save progress:
            self.number_of_completed_segments +=1
            save_pickle(self, f"{self.full_title()} - Translation.pkl")


    def translate_title(self):
        

        selection_text = GPT_Glossary_Selector(self.instructions,
                                               self.Chinese_title)
        
        segment_glossary = {}
        for term in selection_text.splitlines():
                if term in self.instructions.glossary:
                       segment_glossary[term] = self.instructions.glossary[term]

        self.translated_title = GPT_Title_Translator(self.instructions,
                                                  segment_glossary,
                                                  self.Chinese_title)

        glossary_additions = GPT_Title_Glossator(self, self.translated_title)
        update_glossary(self.instructions.glossary, glossary_additions)
        update_glossary(self.translation_glossary, glossary_additions)
                                    

    def full_title(self):
        fulltitle = \
            f"{self.kanripo_code} {self.Chinese_title} - {self.instructions.title_extension}"
        return fulltitle

            
    def translation_to_docx(self):
        # Check if the KanripoText instance is eady to be printed:
        if self.number_of_completed_segments > 0:
            scribe_translation_to_word_document(self)
        else:
            print(f"Error: There are no translated segments.")


    def glossary_to_csv(self): # This function is not used now but might be handy later.
        glossaryfile = self.full_title() + " - Glossary.csv"
        with open(glossaryfile, "w", encoding="utf-8") as file:
            for key, value in self.translation_glossary.items():
                file.write(f"{key},{value[0]}")
                for translation in value[1]:
                    file.write(f",{translation}")
                file.write("\n")


############################################################################################
# I/O
############################################################################################

import pickle

############################################################################################


def save_pickle(obj, filename):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)


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
    run_cn = p.add_run("\n\n\n" + text.Chinese_title)
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
             f"punctuation reasoning: {text.instructions.punctuation_GPT_reasoning}\n" + \
             f"glossary selection reasoning: {text.instructions.glossary_selection_GPT_reasoning}\n" + \
             f"translation reasoning: {text.instructions.translation_GPT_reasoning}\n" + \
             f"glossary extraction reasoning: {text.instructions.glossary_extraction_GPT_reasoning}")
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

