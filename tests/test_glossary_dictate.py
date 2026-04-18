import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
GLOSSARY_DICTATE_PATH = DATA_DIR / "glossary_dictate.py"


@pytest.fixture(scope="session")
def gd_module():
    try:
        return importlib.import_module("yiding.glossary_dictate")
    except Exception:
        package_name = "_glossary_dictate_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.glossary_dictate",
            GLOSSARY_DICTATE_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


# ------------------------------
# load_glossary
# ------------------------------


def test_load_glossary_returns_empty_dict_for_none(gd_module):
    assert gd_module.load_glossary(None) == {}



def test_load_glossary_parses_multiline_text_input(gd_module):
    text = "道,dao,Way,Path\n德,de,Virtue\n"

    glossary = gd_module.load_glossary(text)

    assert glossary == {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }



def test_load_glossary_reads_txt_file(tmp_path, gd_module):
    path = tmp_path / "glossary.txt"
    path.write_text("神,shen,spirit,divinity\n", encoding="utf-8")

    glossary = gd_module.load_glossary(str(path))

    assert glossary == {"神": ["shen", {"spirit", "divinity"}]}



def test_load_glossary_reads_csv_file(tmp_path, gd_module):
    path = tmp_path / "glossary.csv"
    path.write_text("氣,qi,breath,energy\n", encoding="utf-8")

    glossary = gd_module.load_glossary(str(path))

    assert glossary == {"氣": ["qi", {"breath", "energy"}]}



def test_load_glossary_ignores_rows_with_fewer_than_three_columns(gd_module):
    text = "too-short,row\nvalid,ok,a,b\njustone\n"

    glossary = gd_module.load_glossary(text)

    assert glossary == {"valid": ["ok", {"a", "b"}]}



def test_load_glossary_strips_whitespace_and_ignores_empty_translations(gd_module):
    text = " 道 , dao , Way , , Path ,   \n"

    glossary = gd_module.load_glossary(text)

    assert glossary == {"道": ["dao", {"Way", "Path"}]}


# ------------------------------
# update_glossary
# ------------------------------



def test_update_glossary_merges_translation_sets_for_existing_term(gd_module):
    glossary = {"道": ["dao", {"Way"}]}
    addition = {"道": ["dao", {"Path", "Way"}]}

    gd_module.update_glossary(glossary, addition)

    assert glossary == {"道": ["dao", {"Way", "Path"}]}



def test_update_glossary_adds_new_terms(gd_module):
    glossary = {"道": ["dao", {"Way"}]}
    addition = {"德": ["de", {"Virtue"}]}

    gd_module.update_glossary(glossary, addition)

    assert glossary == {
        "道": ["dao", {"Way"}],
        "德": ["de", {"Virtue"}],
    }


# ------------------------------
# stylize / destylize
# ------------------------------



def test_stylize_glossary_returns_empty_string_for_empty_dict(gd_module):
    assert gd_module.stylize_glossary({}) == ""



def test_stylize_glossary_includes_terms_pinyin_and_translations(gd_module):
    glossary = {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }

    result = gd_module.stylize_glossary(glossary)

    assert "\n道 (dao) = " in result
    assert "\n德 (de) = Virtue" in result
    assert "Way" in result
    assert "Path" in result



def test_destylize_glossary_parses_stylized_lines_and_skips_noise(gd_module):
    text = (
        "noise line\n"
        "道 (dao) = Way, Path\n"
        "ignore this too\n"
        "德 (de) = Virtue\n"
    )

    glossary = gd_module.destylize_glossary(text)

    assert glossary == {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }



def test_destylize_glossary_keeps_empty_translation_when_nothing_follows_equals(gd_module):
    text = "道 (dao) = \n"

    glossary = gd_module.destylize_glossary(text)

    assert glossary == {"道": ["dao", {""}]}


# ------------------------------
# glossary_to_csv
# ------------------------------



def test_glossary_to_csv_writes_rows_with_term_pinyin_and_translations(tmp_path, gd_module):
    glossary = {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }
    path = tmp_path / "out.csv"

    gd_module.glossary_to_csv(glossary, str(path))

    text = path.read_text(encoding="utf-8")
    lines = {line for line in text.splitlines() if line}

    assert any(line.startswith("道,dao,") for line in lines)
    assert any(line.startswith("德,de,") for line in lines)
    dao_line = next(line for line in lines if line.startswith("道,dao,"))
    assert "Way" in dao_line
    assert "Path" in dao_line



def test_stylize_then_destylize_preserves_glossary_content(gd_module):
    original = {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }

    round_tripped = gd_module.destylize_glossary(gd_module.stylize_glossary(original))

    assert round_tripped == original
