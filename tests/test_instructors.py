import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
INSTRUCTORS_PATH = next(
    path for path in (HERE.parent / "instructors.py", HERE / "instructors.py", HERE / "instructors(20261103-030237).py")
    if path.is_file()
)


@pytest.fixture(scope="session")
def instructors_module():
    if True:
        package_name = "_instructors_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.instructors",
            INSTRUCTORS_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


@pytest.fixture
def sample_settings():
    return {
        "punctuation": {
            "guidelines": "\n- Use Chinese punctuation naturally.\n- Preserve meaningful structure.",
        },
        "term_extraction": {"guidelines": "Prefer canonical term forms."},
        "glossary_extraction": {"guidelines": "Check attested renderings."},
        "translation": {
            "language": "English",
            "guidelines": "\n- Keep a clear scholarly tone.\n- Use simple modern English.",
        },
    }


# ------------------------------
# punctuation prompts
# ------------------------------


def test_instruct_punctuation_includes_break_contract_and_guidelines(instructors_module, sample_settings):
    text = instructors_module.instruct_punctuation(sample_settings)

    assert "literal token: <break>" in text
    assert "Text to be punctuated:" in text
    assert "If the user provides an empty string OR a single underscore character \"_\", output exactly \"_\"" in text
    assert "PUNCTUATION GUIDELINES" in text
    assert "Use Chinese punctuation naturally." in text
    assert "Preserve meaningful structure." in text



def test_instruct_punctuation_examination_requires_strict_json_boolean(instructors_module):
    text = instructors_module.instruct_punctuation_examination()

    assert '"b"' in text
    assert "Return ONLY a valid JSON object" in text
    assert "true  = there is at least one clear inconsistency" in text
    assert "false = no clear inconsistencies" in text



def test_instruct_punctuation_correction_includes_minimal_edit_and_no_break_rules(instructors_module, sample_settings):
    text = instructors_module.instruct_punctuation_correction(sample_settings)

    assert "make minimal edits" in text.lower()
    assert "do NOT insert <break>" in text
    assert "Do NOT change, replace, reorder, omit, or add ANY Chinese characters of segment B." in text
    assert "STYLE GUIDELINES (MUST FOLLOW)" in text
    assert "Use Chinese punctuation naturally." in text


# ------------------------------
# glossary selection / translation prompts
# ------------------------------


def test_instruct_glossary_selection_includes_target_language_and_title_rules(instructors_module, sample_settings):
    text = instructors_module.instruct_glossary_selection(sample_settings)

    assert "translate the text into English" in text
    assert "Output only the selected terms as plain lines" in text
    assert "If the segment contains a title" in text
    assert "Do not include any surrounding quote/title punctuation characters" in text



def test_instruct_translation_includes_language_guidelines_and_glossary_header(instructors_module, sample_settings):
    text = instructors_module.instruct_translation(sample_settings)

    assert "Translate the given Chinese segment into English." in text
    assert "Translate ONLY the portion labeled \"Text to be translated:\"." in text
    assert "STYLISTIC GUIDELINES (MUST FOLLOW)" in text
    assert "Keep a clear scholarly tone." in text
    assert "Use simple modern English." in text
    assert text.rstrip().endswith("GLOSSARY:")



def test_instruct_translation_examination_includes_language_and_inconsistency_examples(instructors_module, sample_settings):
    text = instructors_module.instruct_translation_examination(sample_settings)

    assert "their corresponding English translations" in text
    assert "Terms translated unjustifiably differently." in text
    assert "Different versions of the same Chinese character being translated differently." in text
    assert '"b" must be a boolean' in text



def test_instruct_translation_correction_includes_minimal_changes_and_style_guidelines(instructors_module, sample_settings):
    text = instructors_module.instruct_translation_correction(sample_settings)

    assert "make the smallest possible edits to B'" in text
    assert "Do not include any Chinese characters in the translated text." in text
    assert "STYLE GUIDELINES (MUST FOLLOW)" in text
    assert "Keep a clear scholarly tone." in text



def test_instruct_glossary_extraction_includes_exact_format_pinyin_and_normalization_rules(instructors_module, sample_settings):
    text = instructors_module.instruct_glossary_extraction(sample_settings)

    assert "its corresponding English translation" in text
    assert "Chinese term (accented Pinyin) = translation" in text
    assert "Provide accented Pinyin" in text
    assert "Give the translation in singular form" in text
    assert "Do NOT invent or improve translations." in text


# ------------------------------
# formatting / interpolation sanity checks
# ------------------------------


def test_translation_related_prompts_interpolate_language_consistently(instructors_module, sample_settings):
    language = sample_settings["translation"]["language"]

    texts = [
        instructors_module.instruct_glossary_selection(sample_settings),
        instructors_module.instruct_translation(sample_settings),
        instructors_module.instruct_translation_examination(sample_settings),
        instructors_module.instruct_translation_correction(sample_settings),
        instructors_module.instruct_glossary_extraction(sample_settings),
    ]

    for text in texts:
        assert language in text



def test_prompt_builders_do_not_leave_unexpanded_settings_placeholders(instructors_module, sample_settings):
    texts = [
        instructors_module.instruct_punctuation(sample_settings),
        instructors_module.instruct_punctuation_correction(sample_settings),
        instructors_module.instruct_glossary_selection(sample_settings),
        instructors_module.instruct_translation(sample_settings),
        instructors_module.instruct_translation_examination(sample_settings),
        instructors_module.instruct_translation_correction(sample_settings),
        instructors_module.instruct_glossary_extraction(sample_settings),
        instructors_module.instruct_mono_glossary_selection(sample_settings),
        instructors_module.instruct_mono_glossary_extraction(sample_settings),
    ]

    for text in texts:
        assert '{settings[' not in text
        assert '{INCONSISTENCIES}' not in text



def test_inconsistencies_constant_contains_expected_categories(instructors_module):
    text = instructors_module.INCONSISTENCIES

    assert "Terms translated unjustifiably differently." in text
    assert "Idioms translated differently." in text
    assert "Phrases translated differently." in text
    assert "Verbatim (or near-verbatim) sentences or quotes translated differently." in text



def test_boolean_examination_prompts_both_forbid_extra_text(instructors_module, sample_settings):
    punctuation_text = instructors_module.instruct_punctuation_examination()
    translation_text = instructors_module.instruct_translation_examination(sample_settings)

    for text in (punctuation_text, translation_text):
        assert "Return no other keys, text, markdown, or code fences." in text



def test_edge_case_underscore_rule_appears_in_generation_prompts(instructors_module, sample_settings):
    texts = [
        instructors_module.instruct_punctuation(sample_settings),
        instructors_module.instruct_punctuation_correction(sample_settings),
        instructors_module.instruct_glossary_selection(sample_settings),
        instructors_module.instruct_translation(sample_settings),
        instructors_module.instruct_translation_correction(sample_settings),
        instructors_module.instruct_glossary_extraction(sample_settings),
        instructors_module.instruct_mono_glossary_selection(sample_settings),
        instructors_module.instruct_mono_glossary_extraction(sample_settings),
    ]

    for text in texts:
        assert 'output exactly "_"' in text.lower()


# New standalone term-selection and glossary-extraction prompt contracts.

def test_mono_glossary_selection_uses_accented_pinyin_and_guidelines(instructors_module, sample_settings):
    text = instructors_module.instruct_mono_glossary_selection(sample_settings)
    assert "Chinese term (accented Pinyin)" in text
    assert "道 (dào)" in text
    assert "Separate Pinyin syllables with spaces." in text
    assert "Prefer canonical term forms." in text
    assert "If the segment contains a title" in text
    assert "ignore them" in text  # fullwidth footnote markers


def test_mono_glossary_extraction_uses_provided_translation_and_guidelines(instructors_module, sample_settings):
    text = instructors_module.instruct_mono_glossary_extraction(sample_settings)
    assert "Chinese term (accented Pinyin) = translation" in text
    assert "Use ONLY the renderings that appear in the provided translation." in text
    assert "Give the translation in singular form" in text
    assert "Check attested renderings." in text


def test_punctuation_prompts_enforce_character_variants_and_unknown_character(instructors_module, sample_settings):
    punctuate = instructors_module.instruct_punctuation(sample_settings)
    correct = instructors_module.instruct_punctuation_correction(sample_settings)
    assert "sequence of Chinese characters in the output" in punctuate
    assert "If a character is ⬤" in punctuate
    assert "ALWAYS retain the character from segment B" in correct
    assert "do NOT insert <break>" in correct


def test_all_text_generation_prompts_handle_underscore(instructors_module, sample_settings):
    builders = (
        lambda: instructors_module.instruct_punctuation(sample_settings),
        lambda: instructors_module.instruct_punctuation_correction(sample_settings),
        lambda: instructors_module.instruct_glossary_selection(sample_settings),
        lambda: instructors_module.instruct_mono_glossary_selection(sample_settings),
        lambda: instructors_module.instruct_translation(sample_settings),
        lambda: instructors_module.instruct_translation_correction(sample_settings),
        lambda: instructors_module.instruct_glossary_extraction(sample_settings),
        lambda: instructors_module.instruct_mono_glossary_extraction(sample_settings),
    )
    for build in builders:
        assert 'output exactly "_"' in build().lower()
