





############################################################################################
############################################################################################
############################################################################################
### THE KANRIPO FETCH
############################################################################################
############################################################################################
############################################################################################


import kanripo


############################################################################################


def fetch_from_kanripo(kanripo_code):

    title = ""
    properties = []
    segments = []
    page_labels = []
    

    raw_juan = fetch_segments(kanripo_code)

    if not raw_juan:
        
        print(f"Code {kanripo_code} is either nonexistent or not documented according to regular Kanripo Repository's conventions.")

    else:
        
        title = detect_title(raw_juan[0])

        properties = detect_properties(raw_juan[0])

        for i in range(0, len(raw_juan)):

            sectioned_juan, page = slice_into_sections(raw_juan[i])
            if sectioned_juan and page:
                for j in range(0, len(sectioned_juan)):
                    segments.append(sectioned_juan[j])
                    page_labels.append(page[j])
        

    return title, properties, page_labels, segments


############################################################################################


def fetch_segments(kanripo_code):

    list_of_juan = []

    kanripo_error = "404: Not Found"

    loop = True
    i = 0
    while loop == True:
        
        kanripo_juan_code = f"{kanripo_code}_{i:03d}"
        print(kanripo_juan_code)
        fetched_juan = kanripo.get_result_file(kanripo_juan_code)
        
        if fetched_juan != kanripo_error:
            print("Fetched text:\n" + fetched_juan)
            
        if "<pb:" in fetched_juan:
            list_of_juan.append(fetched_juan)
        i += 1
        
        if fetched_juan == kanripo_error or i == 999:   # Kanripo might give something else.
            loop = False                                # So, it might crush. Must be fixed.

    for i in range(0,len(list_of_juan)):
        list_of_juan[i] = list_of_juan[i].replace("¶", "")
        
    return list_of_juan


############################################################################################


def slice_into_sections(text):

    sections = [] # This is going to be the end product: a list of Chinese sections.
    current_section = []
    real_text = False

    # This loop goes through the text line by line
    # searching for brackets to define the divisions.
    for line in text.splitlines(True):
        if line.startswith('<pb:'):
            real_text = True
            # Saves the previous section if it exists.
            if current_section:
                sections.append(''.join(current_section))
                current_section = []
        if real_text == True:
            current_section.append(line)
        
    # Adds the last section if the file didn't end with a new section.
    if current_section:
            sections.append(''.join(current_section))

    page_labels = []
    for i in range(0, len(sections)):
        first_line, new_line, rest_of_text = sections[i].partition("\n")
        page_labels.append(detect_page(first_line))
        sections[i] = rest_of_text
                
                
    return sections, page_labels


############################################################################################


def detect_title(text):

    title = "Unknown Title"

    for line in text.splitlines():

        if line.startswith("#+TITLE: "):
            title = line[len("#+TITLE: "):]
            
            break

    return title


############################################################################################


def detect_properties(text):

    properties = []

    for line in text.splitlines():

        if line.startswith("#+PROPERTY: "):
            properties.append(line[len("#+PROPERTY: "):].strip())

    return properties


############################################################################################


def detect_page(line):

    final_form = line

    if len(line)>24:
        
        segment = int(line[17:20])  # To work, Kanripo documentation
                                    # convention needs to be kept.

        if segment > 0:
            segment_format = f"{segment}."
        else:
            segment_format = ""

        page = int(line[21:24])

        side = line[24]

        final_form = f"{segment_format}{page}{side}"
    

    return final_form

    
