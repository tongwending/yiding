# ------------------------------------------------------------------------------------------
# commands
# ------------------------------------------------------------------------------------------

from copy import deepcopy
from pathlib import Path

import tomllib

from .kanripo_text import KanripoText
from .raw_text import RawText
from .segmented_text import SegmentedText
from .prompt_gateway import PromptGateway
from .workflow_orchestrator import WorkflowOrchestrator
from .settings_manager import load_settings
from . import glossary_dictate
from . import ding

from .yiding_file_io import (
    save_project,
    load_project,
    apply_project_to_text,
    finish_run,
    export_text_docx,
    export_text_txt,
    export_glossary_csv,
    export_log_txt,
)


# ------------------------------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------------------------------


def _load_settings(
    settings=None,
):

    # A settings dictionary was supplied directly.
    if isinstance(
        settings,
        dict,
    ):
        return deepcopy(
            settings
        )

    # A settings file was explicitly supplied.
    if settings is not None:

        path = Path(
            settings
        )

        with path.open(
            "rb",
        ) as file:

            return tomllib.load(
                file
            )

    # For CLI use, prefer settings.toml
    # in the current working directory.
    local_settings = (
        Path.cwd()
        / "settings.toml"
    )

    if local_settings.exists():

        with local_settings.open(
            "rb",
        ) as file:

            return tomllib.load(
                file
            )

    # Otherwise use Yiding's normal
    # user settings.
    return deepcopy(
        load_settings()
    )


# ------------------------------------------------------------------------------------------
# PROJECT LOADING
# ------------------------------------------------------------------------------------------


def _text_from_project(
    project,
):

    if project["text_type"] == "raw":

        text = RawText()

    elif project["text_type"] == "kanripo":

        # Do not call KanripoText.__init__ here.
        # Opening an existing project must not
        # fetch Kanripo again.
        text = KanripoText.__new__(
            KanripoText
        )

        SegmentedText.__init__(
            text
        )

    else:

        raise ValueError(
            "Unknown Yiding text type."
        )

    apply_project_to_text(
        project,
        text,
    )

    return text


def _workflow_from_project(
    projectfile,
    settings=None,
    *,
    punctuation_only=False,
):

    project = load_project(
        projectfile
    )

    text = _text_from_project(
        project
    )

    runtime_settings = _load_settings(
        settings
    )

    # A punctuation-only command should not
    # construct translation models.
    if punctuation_only:

        runtime_settings[
            "translation"
        ]["enabled"] = False

    gate = PromptGateway(
        runtime_settings
    )

    orchestrator = WorkflowOrchestrator(
        text,
        gate,
    )

    # Autosave back into the project that
    # was actually opened.
    orchestrator.project_file = str(
        Path(projectfile).resolve()
    )

    return orchestrator


# ------------------------------------------------------------------------------------------
# CREATE YIDING PROJECT
# ------------------------------------------------------------------------------------------


def create_yiding(
    projectfile,
    *,
    unpunctuated_text=None,
    unpunctuated_divider=None,
    unpunctuated_keep_divider=False,
    unpunctuated_divider_is_whole_line=False,

    punctuated_text=None,
    punctuated_divider=None,
    punctuated_keep_divider=False,
    punctuated_divider_is_whole_line=False,

    translated_text=None,
    translation_divider=None,
    translation_keep_divider=False,
    translation_divider_is_whole_line=False,

    original_title=None,
    translated_title=None,
    translation_language=None,
    properties=None,
    structured=False,

    settings=None,
):

    if (
        unpunctuated_text is None
        and punctuated_text is None
        and translated_text is None
    ):

        raise ValueError(
            "At least one text must be supplied."
        )

    text = RawText(
        unpunctuated_text=(
            unpunctuated_text
        ),
        unpunctuated_divider=(
            unpunctuated_divider
        ),
        unpunctuated_keep_divider=(
            unpunctuated_keep_divider
        ),
        unpunctuated_divider_is_whole_line=(
            unpunctuated_divider_is_whole_line
        ),

        punctuated_text=(
            punctuated_text
        ),
        punctuated_divider=(
            punctuated_divider
        ),
        punctuated_keep_divider=(
            punctuated_keep_divider
        ),
        punctuated_divider_is_whole_line=(
            punctuated_divider_is_whole_line
        ),

        translated_text=(
            translated_text
        ),
        translation_divider=(
            translation_divider
        ),
        translation_keep_divider=(
            translation_keep_divider
        ),
        translation_divider_is_whole_line=(
            translation_divider_is_whole_line
        ),

        original_title=(
            original_title
        ),
        translated_title=(
            translated_title
        ),
        translation_language=(
            translation_language
        ),

        structured=structured,
    )

    if properties:

        text.properties = list(
            properties
        )

    project_settings = _load_settings(
        settings
    )

    text.settings = project_settings

    return save_project(
        projectfile,
        text,
        project_settings,
    )


# ------------------------------------------------------------------------------------------
# EXPORT HELPERS
# ------------------------------------------------------------------------------------------


def _export_kind(
    punctuation,
    translation,
):

    if (
        punctuation
        and translation
    ):

        return (
            "punctuated_translation"
        )

    if punctuation:

        return "punctuated"

    if translation:

        return "translation"

    return "unpunctuated"


def _default_export_path(
    projectfile,
    export_kind,
    extension,
):

    projectfile = Path(
        projectfile
    )

    suffix = {
        "unpunctuated":
            " - Unpunctuated",

        "punctuated":
            " - Punctuated",

        "translation":
            " - Translated",

        "punctuated_translation":
            "",
    }[export_kind]

    return projectfile.with_name(
        projectfile.stem
        + suffix
        + f".{extension}"
    )


def _export_project(
    projectfile,
    *,
    punctuation,
    translation,
    output_file,
    table=True,
):

    project = load_project(
        projectfile
    )

    export_kind = _export_kind(
        punctuation,
        translation,
    )

    output_format = (
        str(output_file)
        .lower()
        .lstrip(".")
    )

    destination = (
        _default_export_path(
            projectfile,
            export_kind,
            output_format,
        )
    )

    if output_format == "docx":

        return export_text_docx(
            project,
            export_kind,
            destination,
            parallel_table=table,
        )

    if output_format == "txt":

        if export_kind == (
            "punctuated_translation"
        ):

            raise ValueError(
                "TXT export accepts one "
                "text type at a time."
            )

        return export_text_txt(
            project,
            export_kind,
            destination,
        )

    raise ValueError(
        "Unsupported output format: "
        f"{output_file}"
    )


# ------------------------------------------------------------------------------------------
# TRANSLATE
# ------------------------------------------------------------------------------------------


def translate(
    projectfile,
    settings=None,
    output_file="docx",
    table=True,
    punctuation=True,
):

    orchestrator = (
        _workflow_from_project(
            projectfile,
            settings,
        )
    )

    if not orchestrator.text.is_translated:

        orchestrator.resume_translation()

    print(
        ding.DING
    )

    return _export_project(
        projectfile,
        punctuation=punctuation,
        translation=True,
        output_file=output_file,
        table=table,
    )


# ------------------------------------------------------------------------------------------
# TRANSLATE BULK
# ------------------------------------------------------------------------------------------


def translate_bulk(
    projectfiles,
    settings=None,
    output_file="docx",
    table=True,
    punctuation=True,
):

    results = []

    for projectfile in projectfiles:

        result = translate(
            projectfile,
            settings=settings,
            output_file=output_file,
            table=table,
            punctuation=punctuation,
        )

        results.append(
            result
        )

    return results


# ------------------------------------------------------------------------------------------
# TRANSLATE FROM KANRIPO
# ------------------------------------------------------------------------------------------


def translate_from_kanripo(
    kanripo_code,
    settings=None,
    translated_title=None,
    output_file="docx",
    table=True,
    punctuation=True,
    projectfile=None,
):

    runtime_settings = _load_settings(
        settings
    )

    text = KanripoText(
        kanripo_code
    )

    if translated_title:

        text.translated_title = (
            translated_title
        )

    if projectfile is None:

        projectfile = (
            f"{kanripo_code}.yiding"
        )

    projectfile = save_project(
        projectfile,
        text,
        runtime_settings,
    )

    gate = PromptGateway(
        runtime_settings
    )

    orchestrator = WorkflowOrchestrator(
        text,
        gate,
    )

    orchestrator.project_file = str(
        Path(projectfile).resolve()
    )

    orchestrator.resume_translation()

    print(
        ding.DING
    )

    return _export_project(
        projectfile,
        punctuation=punctuation,
        translation=True,
        output_file=output_file,
        table=table,
    )


# ------------------------------------------------------------------------------------------
# TRANSLATE BULK FROM KANRIPO
# ------------------------------------------------------------------------------------------


def translate_bulk_from_kanripo(
    kanripo_codes,
    settings=None,
    translated_titles=None,
    output_file="docx",
    table=True,
    punctuation=True,
):

    if (
        translated_titles
        and len(kanripo_codes)
        != len(translated_titles)
    ):

        raise ValueError(
            "Error: Unequal number of "
            "Kanripo codes and translated titles."
        )

    results = []

    for i, kanripo_code in enumerate(
        kanripo_codes
    ):

        translated_title = (
            translated_titles[i]
            if translated_titles
            else None
        )

        result = (
            translate_from_kanripo(
                kanripo_code,
                settings=settings,
                translated_title=(
                    translated_title
                ),
                output_file=output_file,
                table=table,
                punctuation=punctuation,
            )
        )

        results.append(
            result
        )

    return results


# ------------------------------------------------------------------------------------------
# TRANSLATE ANEW
# ------------------------------------------------------------------------------------------


def translate_anew(
    projectfile,
    settings=None,
    translated_title=None,
    output_file="docx",
    table=True,
    punctuation=True,
):

    project = load_project(
        projectfile
    )

    text = _text_from_project(
        project
    )

    # Cancel any unfinished old translation run.
    for run in getattr(
        text,
        "yiding_runs",
        [],
    ):

        if (
            run["operation"]
            == "translation"
            and run["status"]
            == "in_progress"
        ):

            finish_run(
                run,
                status="cancelled",
            )

    text.empty_translation()

    text.yiding_provenance[
        "translated_segment_run_ids"
    ] = []

    if translated_title:

        text.translated_title = (
            translated_title
        )

    runtime_settings = _load_settings(
        settings
    )

    gate = PromptGateway(
        runtime_settings
    )

    orchestrator = WorkflowOrchestrator(
        text,
        gate,
    )

    orchestrator.project_file = str(
        Path(projectfile).resolve()
    )

    orchestrator.resume_translation()

    print(
        ding.DING
    )

    return _export_project(
        projectfile,
        punctuation=punctuation,
        translation=True,
        output_file=output_file,
        table=table,
    )


# ------------------------------------------------------------------------------------------
# PUNCTUATE
# ------------------------------------------------------------------------------------------


def punctuate(
    projectfile,
    settings=None,
    output_file="docx",
):

    orchestrator = (
        _workflow_from_project(
            projectfile,
            settings,
            punctuation_only=True,
        )
    )

    if not orchestrator.text.is_punctuated:

        orchestrator.resume_punctuation()

    print(
        ding.DING
    )

    return _export_project(
        projectfile,
        punctuation=True,
        translation=False,
        output_file=output_file,
        table=False,
    )


# ------------------------------------------------------------------------------------------
# PUNCTUATE BULK
# ------------------------------------------------------------------------------------------


def punctuate_bulk(
    projectfiles,
    settings=None,
    output_file="docx",
):

    results = []

    for projectfile in projectfiles:

        result = punctuate(
            projectfile,
            settings=settings,
            output_file=output_file,
        )

        results.append(
            result
        )

    return results


# ------------------------------------------------------------------------------------------
# PUNCTUATE FROM KANRIPO
# ------------------------------------------------------------------------------------------


def punctuate_from_kanripo(
    kanripo_code,
    settings=None,
    output_file="docx",
    projectfile=None,
):

    runtime_settings = _load_settings(
        settings
    )

    # This is a punctuation-only operation.
    # Do this before PromptGateway is created.
    runtime_settings[
        "translation"
    ]["enabled"] = False

    text = KanripoText(
        kanripo_code
    )

    if projectfile is None:

        projectfile = (
            f"{kanripo_code}.yiding"
        )

    projectfile = save_project(
        projectfile,
        text,
        runtime_settings,
    )

    gate = PromptGateway(
        runtime_settings
    )

    orchestrator = WorkflowOrchestrator(
        text,
        gate,
    )

    orchestrator.project_file = str(
        Path(projectfile).resolve()
    )

    orchestrator.resume_punctuation()

    print(
        ding.DING
    )

    return _export_project(
        projectfile,
        punctuation=True,
        translation=False,
        output_file=output_file,
        table=False,
    )


# ------------------------------------------------------------------------------------------
# PUNCTUATE BULK FROM KANRIPO
# ------------------------------------------------------------------------------------------


def punctuate_bulk_from_kanripo(
    kanripo_codes,
    settings=None,
    output_file="docx",
):

    results = []

    for kanripo_code in kanripo_codes:

        result = (
            punctuate_from_kanripo(
                kanripo_code,
                settings=settings,
                output_file=output_file,
            )
        )

        results.append(
            result
        )

    return results


# ------------------------------------------------------------------------------------------
# GET SETTINGS
# ------------------------------------------------------------------------------------------


def get_settings():

    source = (
        Path(__file__).resolve()
        .with_name("settings.toml")
    )

    destination = (
        Path.cwd()
        / "settings.toml"
    )

    destination.write_bytes(
        source.read_bytes()
    )

    print(
        "Copied settings.toml to "
        f"{destination}"
    )

    return destination


# ------------------------------------------------------------------------------------------
# EXPORT
# ------------------------------------------------------------------------------------------


def export(
    projectfile,
    punctuation=False,
    translation=False,
    output_file="docx",
    table=False,
):

    return _export_project(
        projectfile,
        punctuation=punctuation,
        translation=translation,
        output_file=output_file,
        table=table,
    )


# ------------------------------------------------------------------------------------------
# EXPORT LOG
# ------------------------------------------------------------------------------------------


def export_log(
    projectfile,
):

    project = load_project(
        projectfile
    )

    path = Path(
        projectfile
    )

    output_file = path.with_name(
        path.stem
        + "_LOG.txt"
    )

    return export_log_txt(
        project["log"],
        output_file,
    )


# ------------------------------------------------------------------------------------------
# UPDATE GLOSSARY
# ------------------------------------------------------------------------------------------


def update_glossary(
    glossaryfile,
    projectfile,
    output_file=None,
):

    base_glossary = (
        glossary_dictate.load_glossary(
            glossaryfile
        )
    )

    project = load_project(
        projectfile
    )

    project_glossary = {}

    for row in (
        project["glossaries"]
        ["translation_glossary"]
        ["rows"]
    ):

        chinese = row[
            "chinese"
        ]

        pinyin = row.get(
            "pinyin",
            "",
        )

        translations = set(
            row.get(
                "translations",
                [],
            )
        )

        project_glossary[
            chinese
        ] = [
            pinyin,
            translations,
        ]

    glossary_dictate.update_glossary(
        base_glossary,
        project_glossary,
    )

    return export_glossary_csv(
        base_glossary,
        (
            output_file
            if output_file
            else glossaryfile
        ),
    )


# ------------------------------------------------------------------------------------------
# UPDATE GLOSSARY
# ------------------------------------------------------------------------------------------

def set_key(provider, api_key):

    providers = {
        "openai": "OpenAI",
        "google": "Google",
    }

    provider_key = provider.strip().lower()

    if provider_key not in providers:
        raise ValueError(
            "Provider must be 'openai' or 'google'."
        )

    if not api_key or not api_key.strip():
        raise ValueError(
            "API key cannot be empty."
        )

    keyring.set_password(
        "Yiding",
        providers[provider_key],
        api_key.strip(),
    )
    
# ------------------------------------------------------------------------------------------
