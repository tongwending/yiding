from pathlib import Path
import tomllib

import pytest


REQUIRED_MODEL_KEYS = {"model", "reasoning", "verbosity", "temperature", "top_p"}


@pytest.fixture(scope="module")
def settings_path() -> Path:
    try:
        import yiding  # type: ignore

        candidate = Path(yiding.__file__).resolve().with_name("settings.toml")
        if candidate.exists():
            return candidate
    except Exception:
        pass

    candidates = [
        Path(__file__).resolve().parents[1] / "settings.toml",
        Path.cwd() / "settings.toml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError("Could not locate settings.toml")


@pytest.fixture(scope="module")
def settings(settings_path: Path) -> dict:
    with settings_path.open("rb") as f:
        return tomllib.load(f)


def test_settings_file_exists_and_loads(settings_path: Path, settings: dict):
    assert settings_path.exists()
    assert isinstance(settings, dict)
    assert settings


def test_top_level_sections_exist(settings: dict):
    assert {"api_serial_keys", "punctuation", "translation"} <= set(settings)


def test_api_serial_keys_are_present_and_nonempty(settings: dict):
    api = settings["api_serial_keys"]
    assert isinstance(api["openai"], str) and api["openai"].strip()
    assert isinstance(api["google"], str) and api["google"].strip()


def test_punctuation_section_has_required_keys(settings: dict):
    punctuation = settings["punctuation"]
    required = {
        "enabled",
        "guidelines",
        "facsimile_span",
        "punctuation_span",
        "max_unsegmented_span",
        "max_punctuation_attempts",
        "punctuation",
        "cross_check",
        "cross_examination",
        "cross_correction",
    }
    assert required <= set(punctuation)
    assert isinstance(punctuation["enabled"], bool)
    assert isinstance(punctuation["guidelines"], str)
    assert isinstance(punctuation["facsimile_span"], int)
    assert isinstance(punctuation["punctuation_span"], int)
    assert isinstance(punctuation["max_unsegmented_span"], int)
    assert isinstance(punctuation["max_punctuation_attempts"], int)
    assert isinstance(punctuation["cross_check"]["enabled"], bool)


@pytest.mark.parametrize(
    "path",
    [
        ("punctuation", "punctuation"),
        ("punctuation", "cross_examination"),
        ("punctuation", "cross_correction"),
        ("translation", "translation"),
        ("translation", "glossary_extraction"),
        ("translation", "cross_examination"),
        ("translation", "cross_correction"),
        ("translation", "glossary_selection"),
    ],
)
def test_model_blocks_have_required_shape(settings: dict, path: tuple[str, str]):
    block = settings[path[0]][path[1]]
    assert REQUIRED_MODEL_KEYS <= set(block)
    assert isinstance(block["model"], str) and block["model"].strip()


@pytest.mark.parametrize(
    "path",
    [
        ("punctuation", "punctuation"),
        ("punctuation", "cross_examination"),
        ("punctuation", "cross_correction"),
        ("translation", "translation"),
        ("translation", "glossary_extraction"),
        ("translation", "cross_examination"),
        ("translation", "cross_correction"),
        ("translation", "glossary_selection"),
    ],
)
def test_model_names_match_supported_prefixes(settings: dict, path: tuple[str, str]):
    model = settings[path[0]][path[1]]["model"]
    assert model.startswith("gpt") or model.startswith("gemini") or model in {
        "o1",
        "o1-mini",
        "o1-pro",
        "o3",
        "o3-deep-research",
        "o4-mini-deep-research",
        "o4-mini",
    }


def test_translation_section_has_required_keys(settings: dict):
    translation = settings["translation"]
    required = {
        "enabled",
        "guidelines",
        "language",
        "glossary",
        "translation_span",
        "translation",
        "glossary_extraction",
        "cross_check",
        "cross_examination",
        "cross_correction",
        "llm_glossary_selection",
        "glossary_selection",
    }
    assert required <= set(translation)
    assert isinstance(translation["enabled"], bool)
    assert isinstance(translation["guidelines"], str)
    assert isinstance(translation["language"], str) and translation["language"].strip()
    assert isinstance(translation["glossary"], str)
    assert isinstance(translation["translation_span"], int)
    assert isinstance(translation["cross_check"]["enabled"], bool)
    assert isinstance(translation["llm_glossary_selection"]["enabled"], bool)


def test_numeric_settings_are_nonnegative_and_spans_are_positive(settings: dict):
    punctuation = settings["punctuation"]
    translation = settings["translation"]

    assert punctuation["facsimile_span"] > 0
    assert punctuation["punctuation_span"] >= 0
    assert punctuation["max_unsegmented_span"] > 0
    assert punctuation["max_punctuation_attempts"] > 0
    assert translation["translation_span"] >= 0


def test_guidelines_are_not_blank(settings: dict):
    assert settings["punctuation"]["guidelines"].strip()
    assert settings["translation"]["guidelines"].strip()
