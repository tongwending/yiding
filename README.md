Yiding 譯鼎
An AI-assisted punctuation and translation pipeline for pre-modern Chinese texts

======================================================================
INTRODUCTION
======================================================================

Yiding 譯鼎 is a Python package for:
a) fetching pre-modern Daoist texts from Kanseki Repository through the Kanripo API
   wrapper,
b) calling LLM models to punctuate, translate, check consistency, and extract 
   glossary terms
c) exporting the punctuated and translated texts to DOCX files.

The package is built around a controlled workflow rather than a
single one-shot prompt. In the default setup, it:

1. Fetch the Kanripo text by KR code.
2. Detect the title and text properties.
3. Slice the text into working sections.
4. Punctuate the text (LLM call) while preserving character integrity.
5. Split the punctuated result into segments.
6. Compare new punctuated segments against previous ones for consistency (LLM call).
7. Select glossary terms for each segment's translation (with optional LLM call).
8. Translate each punctuated segment with limited previous context (LLM call).
9. Compare each new translation against previous translations for consistency (LLM call).
10. Extract glossary entries from the translated output (LLM call).
11. Auto-save progress to a PKL file after major steps.
12. Export punctuated and/or translated text to DOCX.

======================================================================
INSTALLATION REQUIREMENTS
======================================================================

A) Python 3.11 or newer

	To install Python (if not already installed):
	
	1. Go to https://www.python.org/downloads/
	2. Download Python 3.11 or newer
	3. Run the installer and follow the steps.
	(Note: For Windows, make sure to check the box that says "Add Python to PATH".)
	
	After installation:
	open Command Prompt/PowerShell (Windows) or open Terminal (macOS/Linux) 
	and check that Python is installed:
	
		python --version

	(Note: On some systems, you may need to use:  python3 --version)


B) Python packages required

	The following Python packages must be installed:

	- python-docx
	- kanripo
	- openai (only if OpenAI models are used)
	- google-genai (only if Google models are used)
	
	Install the required packages with the following command line:

		pip install openai google-genai python-docx kanripo
	
	(Note: Skip openai or google-genai if you won't use the respective models.)


======================================================================
YIDING INSTALLATION
======================================================================

To install Yiding:

    1. Download or clone the Yiding repository to your computer:
   	- Open the YiDing GitHub page
   	- Click the green "Code" button
   	- Click "Download ZIP"
   	- Save the ZIP file to your computer
   	- Extract or unzip it

    2. Open the Yiding folder (the one that contains the pyproject.toml file)

    3. Open a command window in that folder:

       On Windows:
       - Open the Yiding folder in File Explorer
       - Click in the address bar and type: cmd
       - Press Enter

       On macOS:
       - Open Terminal
       - Type cd followed by a space
       - Drag the Yiding folder into the Terminal window
       - Press Enter

       On Linux:
       - Open Terminal
       - Type cd followed by a space
       - Drag the Yiding folder into the Terminal window, or type its path
       - Press Enter

    4. Once you open the command line inside the Yiding folder, run:

           python -m pip install .
	
	Note: On some systems, you may need to use: 
	   python3 -m pip install .
		
======================================================================
API KEYS REQUIREMENTS
======================================================================

YiDing requires API access for the language models you choose to use:

    - OpenAI API key (required if you use OpenAI models)
    - Google AI / Gemini API key (required if you use Google models)

You must obtain these keys yourself from OpenAI and/or Google:
	- OpenAI: Go to the OpenAI API platform, sign in, 
    		  and create a secret API key from the API Keys page.
    	- Google: Go to Google AI Studio, sign in, 
    		  and create a Gemini API key from the API Keys page.

(Note: The API keys are stored in a settings.toml or txt file. See below.)

======================================================================
WORKING FOLDER SET UP
======================================================================

To operate Yiding, you need to set up a working folder with your settings preferences.
(You can have many working folders with different settings.)

To create a working folder:
	a) Create a new folder (this is now the working folder)
	b) Open a command window in the folder (see YIDING INSTALLATION above) 
	c) Run the following command (to create settings.toml):
		yiding get-settings
	d) Open the newly created settings.toml in the working folder
	e) Change the settings according to your preferences (see below)

======================================================================
SETTINGS MANAGEMENT
======================================================================

Yiding is controlled by a TOML settings file, 
containing three main parts:
	A) API settings
	B) punctuation settings
	C) translation settings

Make sure to understand and review all the settings before running Yiding.
To change the settings, open the file (in notepad) and rewrite the existing values.
Change only the values; do not change the names of the parameters.
Make sure to keep the correct syntax for each value type:
	for string :
		parameter_name = "insert text here"
	for docstring
		parameter_name = """insert text here"""
	for integer:
		parameter_name = 4
	for float:
		parameter_name = 0.44
	for boolean:
		parameter_name = true OR false

A) api_settings

	[api_serial_keys]
	openai (string): Insert your OpenAI API key or name the TXT file containing it.
	google (string): Insert your Google API key or name the TXT file containing it.

B) punctuation_settings

	[punctuation]
	enabled (boolean): If true, Yiding will punctuate the text; 
			   if false, it will not punctuate (ignore punctuation settings)
	guidelines (docstring): Punctuation stylistic guidelines (fed to the LLM model).
	facsimile_span (integer): Number of facsimiles fed in a single punctuation prompt;
	punctuation_span (integer): Number of previous punctuated segments for context
				    in a single punctuation prompt
	max_unsegmented_span (integer): Maximum characters allowed in a punctuated segment
	max_punctuation_attempts (integer): Maximum punctuation attempts in case of 						    corruption of the original text.
    	
	[punctuation.punctuation]
	* Define the model and its parameters for punctuation prompts; see below.
	
	[punctuation.cross_check]
    	enabled (boolean): If true, it will cross check each punctuated segment
			   against previous segments for consistency;
		  	   if false, it will not (ignore punctuation cross-check settings)
		  	   (Note: Cross checking is done with LLM calls 
			    that grow quadratically)
		
		[punctuation.cross_examination]
		* Define the model and its parameters for cross examination; see below.
		
		[punctuation.cross_correction]
		* Define the model and its parameters for cross correction; see below.

C) translation_settings

	[translation]
	enabled (boolean): If true, Yiding will translate the text; 
			   if false, it will not translate (ignore translation settings)
	guidelines (docstring): Translation stylistic guidelines (fed to the LLM model).
	language (string): The target language of the translation;
			   it can be as simple as "English" or "Greek"
			   or even more specific "Old English" or "Koine Greek"
	glossary (string OR false): Name of the glossary CSV file in working folder;
			   	    if you don't want an initial glossary, write: false
	translation_span (integer): Number of previous punctuated and translated 
				    segments for context in a single translation prompt
	
	[translation.translation]
	* Define the model and its parameters for translation; see below.
	
	[translation.glossary_extraction]
	* Define the model and its parameters for glossary extraction; see below.

    	[translation.cross_check]
    	enabled (boolean): If true, it will cross check each translated segment
			   against previous segments for consistency;
		  	   if false, it will not (ignore translation cross-check settings)
		  	   (Note: Cross checking is done with LLM calls 
			    that grow quadratically)

		[translation.cross_examination]
		* Define the model and its parameters for cross examination; see below.
		
		[translation.cross_correction]
		* Define the model and its parameters for cross correction; see below.
	
	[translation.llm_glossary_selection]
	enabled (boolean): If true, it will select glossary terms for translation prompts
			   using LLM calls (instead of the default automatic process);
		  	   if false, it will use the default automatic process 
			   (if false, ignore glossary selection settings).
			   Note: LLM glossary selection is not suggested 
			   	 but is offered as an option.

		[translation.glossary_selection]
		* Define the model and its parameters for glossary selection; see below.

======================================================================
MODEL SELECTION AND PROMPTING PARAMETERS
======================================================================

Yiding allows the use of a different LLM model and its parameters for each prompting job.
The different prompting jobs are:
	- punctuation
	- punctuation cross examination
	- punctuation cross correction
	- translation
	- glossary extraction
	- translation cross examination 
	- translation cross correction
	- glossary selection

The user must define the LLM model and its parameters for each job (if the job is enabled):
	
	model (string): Name the LLM model for the job; make sure that the name is spelled
                        according to convention; make sure you have stored API key that allows
			access to the model provider's API (see above).
	reasoning (string or false): Defines reasoning or thinking level;
				     make sure to use correct term (e.g. low, medium, high)
				     the provider defines the option.
				     If false, the parameter will be ignored (no reasoning)
	verbosity (string or false): Defines verbosity level;
				     use the correct term ("low", "medium", "high");
				     the provider defines the options.
				     If false, the parameter will be ignored (default)
	temperature (float or false): Defines temperature value;
				      use a valid number (often 0 to 2);
				      the provider defines the options.
				      If false, the parameter will be ignored (default)
	top_p (float or false): Defines top p value;
				use a valid number (often 0 to 1);
				the provider defines the options.
				If false, the parameter will be ignored (default)

======================================================================
GLOSSARY CSV FILE
======================================================================

Yiding allows the use of a predefined glossary CSV file (not required but recommended).

The glossary CSV file should be located in the working folder
and given as the glossary parameter in the settings.toml (see above).

Each glossary term in the CSV file should be in the following format:
	
	Chinese term, pinyin, translation A, translation B, etc

For example:
	
	譯, yi, translation, interpretation

In other words, the first column of the CSV file must have the Chinese term,
the second column must have the pinyin, and the rest should have the translation options.

======================================================================
HOW TO OPERATE YIDING
======================================================================

Yiding can be run from the command line of the working folder
(alternatively, its commands can be used in Python code; see below)

 First open the command window of the working folder:

       On Windows:
       - Open the working folder in File Explorer
       - Click in the address bar and type: cmd
       - Press Enter

       On macOS:
       - Open Terminal
       - Type cd followed by a space
       - Drag the working folder into the Terminal window
       - Press Enter

       On Linux:
       - Open Terminal
       - Type cd followed by a space
       - Drag the working folder into the Terminal window, or type its path
       - Press Enter

To give a command to Yiding, type in the command window:

	yiding COMMAND ARGUMENT_A ARGUMENT_B ARGUMENT_C

Examples:
	yiding translate KR5h0008
	yiding export my_file.pkl --punctuation --translation --table

For the commands available see below.
Most commands have required arguments; these arguments must be provided.
Optional arguments are preceded by - or -- and the name of the argument.

In other words:
- first write yiding
- then write the command
- then add the needed file name or Kanripo code
- then add optional extra settings such as --settings or --table

======================================================================
CLI COMMANDS
======================================================================

translate
    Translate a single Kanripo text.

    Required arguments:
        kanripo_code

    Optional arguments:
        -s, --settings PATH
        --translated-title TITLE
        -o, --output-file docx
        --table / --no-table
        --punctuation / --no-punctuation

translate-bulk
    Translate multiple Kanripo texts.

    Required arguments:
        one or more kanripo codes

    Optional arguments:
        -s, --settings PATH
        --translated-titles TITLE1 TITLE2 ...
        -o, --output-file docx
        --table / --no-table
        --punctuation / --no-punctuation

continue-translating
    Resume translating from a saved PKL file.

    Required arguments:
        picklefile

    Optional arguments:
        -o, --output-file docx
        --table / --no-table
        --punctuation / --no-punctuation

translate-anew
    Reload a saved PKL file and re-run translation from scratch.
    Punctuation is disabled in the new run, so it reuses the already
    punctuated text stored in the pickle.

    Required arguments:
        picklefile

    Optional arguments:
        -s, --settings PATH
        --translated-title TITLE
        -o, --output-file docx
        --table / --no-table
        --punctuation / --no-punctuation

punctuate
    Punctuate a single Kanripo text without translation.

    Required arguments:
        kanripo_code

    Optional arguments:
        -s, --settings PATH
        -o, --output-file docx

punctuate-bulk
    Punctuate multiple Kanripo texts without translation.

    Required arguments:
        one or more kanripo codes

    Optional arguments:
        -s, --settings PATH
        -o, --output-file docx

continue-punctuating
    Resume punctuation from a saved pickle.

    Required arguments:
        picklefile

    Optional arguments:
        -o, --output-file docx

get-settings
    Creates the initial settings.toml file in the working folder;
    (it can be used to recreate the file in case of syntax corruption).

export
    Export from a saved pickle without calling any model.

    Required arguments:
        picklefile

    Optional arguments:
        -o, --output-file docx
        --table / --no-table
        --punctuation / --no-punctuation
        --translation / --no-translation

export-log
    Write the orchestrator log to a text file.

    Required arguments:
        picklefile

update-glossary
    Merge the translation glossary stored in a pickle into a base
    glossary CSV.

    Required arguments:
        glossaryfile
        picklefile

    Optional arguments:
        -o, --output-file PATH

======================================================================
PYTHON API
======================================================================

YiDing also exposes the above commands in a simple Python API:

    from yiding import (
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

======================================================================
IMPORTANT CURRENT LIMITATIONS
======================================================================

- DOCX is the only implemented export format at the moment.
  The CLI accepts --output-file, but the actual exporter currently
  handles only "docx".

- The safest way to run Yiding is with an explicit settings path or
  with settings.toml present in the working directory.

- The default example setup requires both OpenAI and Google access,
  because the sample cross-check configuration uses Gemini.

- Word font rendering for Chinese is set to PMingLiU in the DOCX
  exporter. If that font is unavailable on your system, Word may
  substitute another font.

======================================================================
COMMON ERRORS
======================================================================

Possible errors include:

- Error: No API key in file.
  Cause:
      Your API key file exists but is empty.

- Error: Unknown LLM model.
  Cause:
      The model name in settings.toml is not recognized by the gateway.

- Error: Code <...> is nonexistent or unknown Kanripo documentation.
  Cause:
      The Kanripo code is invalid or cannot be parsed by the current
      parser assumptions.
