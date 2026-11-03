"""Tests for yiding/glossary_dictate.py, including the planned character matcher."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def gd_module():
    """Load the local source file so tests never accidentally use an installed version."""
    here = Path(__file__).resolve().parent
    candidates = (
        here.parent / "yiding" / "glossary_dictate.py",  # tests/ directory
        here.parent / "glossary_dictate.py",             # alternate project layout
        here / "yiding" / "glossary_dictate.py",         # tests at project root
        here / "glossary_dictate.py",                    # standalone local check
        here / "glossary_dictate(20261103-181525).py",  # uploaded source
    )
    module_path = next((p for p in candidates if p.is_file()), None)
    if module_path is None:
        pytest.fail("Cannot locate glossary_dictate.py; put this test in tests/.")

    spec = importlib.util.spec_from_file_location("glossary_dictate_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# load_glossary

def test_load_glossary_none(gd_module):
    assert gd_module.load_glossary(None) == {}


def test_load_glossary_multiline_text(gd_module):
    assert gd_module.load_glossary("道,dao,Way,Path\n德,de,Virtue\n") == {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }


@pytest.mark.parametrize("extension", ["txt", "csv"])
def test_load_glossary_reads_utf8_file(gd_module, tmp_path, extension):
    path = tmp_path / f"glossary.{extension}"
    path.write_text("氣,qi,breath,energy\n", encoding="utf-8")
    assert gd_module.load_glossary(str(path)) == {
        "氣": ["qi", {"breath", "energy"}]
    }


def test_load_glossary_accepts_two_column_rows_and_skips_one_column_rows(gd_module):
    assert gd_module.load_glossary("道,dao\ninvalid\n德,de,Virtue\n") == {
        "道": ["dao", set()],
        "德": ["de", {"Virtue"}],
    }


def test_load_glossary_strips_whitespace_and_omits_blank_translations(gd_module):
    assert gd_module.load_glossary(" 道 , dao , Way , , Path ,  \n") == {
        "道": ["dao", {"Way", "Path"}]
    }


def test_load_glossary_duplicate_term_uses_last_row(gd_module):
    assert gd_module.load_glossary("道,dao,Way\n道,dao,Path\n") == {
        "道": ["dao", {"Path"}]
    }


# update_glossary

def test_update_glossary_merges_translations_in_place(gd_module):
    original = {"道": ["dao", {"Way"}]}
    result = gd_module.update_glossary(original, {"道": ["different", {"Path"}]})
    assert result is None
    assert original == {"道": ["dao", {"Way", "Path"}]}


def test_update_glossary_deepcopies_new_entries(gd_module):
    original = {}
    addition = {"德": ["de", {"Virtue"}]}
    gd_module.update_glossary(original, addition)
    addition["德"][1].add("Changed")
    assert original == {"德": ["de", {"Virtue"}]}


# stylize_glossary / destylize_glossary

def test_stylize_glossary_empty(gd_module):
    assert gd_module.stylize_glossary({}) == ""


def test_stylize_glossary_includes_terms_and_translations(gd_module):
    result = gd_module.stylize_glossary({
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    })
    assert "\n道 (dao) = " in result
    assert "\n德 (de) = Virtue" in result
    assert "Way" in result and "Path" in result


def test_stylize_glossary_empty_translations(gd_module):
    assert gd_module.stylize_glossary({"道": ["dao", set()]}) == "\n道 (dao) = "


def test_destylize_glossary_ignores_unformatted_lines(gd_module):
    assert gd_module.destylize_glossary(
        "noise\n道 (dao) = Way, Path\nother noise\n德 (de) = Virtue\n"
    ) == {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }


def test_destylize_glossary_empty_translations_are_empty_set(gd_module):
    assert gd_module.destylize_glossary("道 (dao) = \n") == {
        "道": ["dao", set()]
    }


def test_stylize_destylize_roundtrip(gd_module):
    original = {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", set()],
    }
    assert gd_module.destylize_glossary(gd_module.stylize_glossary(original)) == original


# destylize_terms

def test_destylize_terms_extracts_terms_and_pinyin(gd_module):
    assert gd_module.destylize_terms(
        "道 (dao)\ninvalid line\n德 (de)\n"
    ) == {
        "道": ["dao", set()],
        "德": ["de", set()],
    }


def test_destylize_terms_empty_text(gd_module):
    assert gd_module.destylize_terms("") == {}


# unite_glossaries

def test_unite_glossaries_merges_without_mutating_inputs(gd_module):
    a = {"道": ["dao", {"Way"}]}
    b = {"道": ["dao", {"Path"}], "德": ["de", {"Virtue"}]}
    result = gd_module.unite_glossaries(a, b)
    assert result == {
        "道": ["dao", {"Way", "Path"}],
        "德": ["de", {"Virtue"}],
    }
    result["道"][1].add("Extra")
    result["德"][1].add("Extra")
    assert a == {"道": ["dao", {"Way"}]}
    assert b == {"道": ["dao", {"Path"}], "德": ["de", {"Virtue"}]}


# differentiate_glossaries

def test_differentiate_glossaries_subtracts_only_shared_translations(gd_module):
    a = {"道": ["dao", {"Way", "Path"}], "德": ["de", {"Virtue"}]}
    b = {"道": ["dao", {"Way"}]}
    assert gd_module.differentiate_glossaries(a, b) == {
        "道": ["dao", {"Path"}],
        "德": ["de", {"Virtue"}],
    }


def test_differentiate_glossaries_removes_term_when_all_translations_subtracted(gd_module):
    assert gd_module.differentiate_glossaries(
        {"道": ["dao", {"Way"}]}, {"道": ["dao", {"Way"}]}
    ) == {}


def test_differentiate_glossaries_keeps_term_with_original_empty_set(gd_module):
    assert gd_module.differentiate_glossaries(
        {"道": ["dao", set()]}, {"道": ["dao", {"Way"}]}
    ) == {"道": ["dao", set()]}


def test_differentiate_glossaries_does_not_mutate_inputs(gd_module):
    a = {"道": ["dao", {"Way", "Path"}]}
    b = {"道": ["dao", {"Way"}]}
    result = gd_module.differentiate_glossaries(a, b)
    result["道"][1].add("Extra")
    assert a == {"道": ["dao", {"Way", "Path"}]}
    assert b == {"道": ["dao", {"Way"}]}


# intersect_glossaries

def test_intersect_glossaries_intersects_translation_sets(gd_module):
    a = {"道": ["dao", {"Way", "Path"}], "德": ["de", {"Virtue"}]}
    b = {"道": ["different", {"Way", "Route"}], "天": ["tian", {"Sky"}]}
    assert gd_module.intersect_glossaries(a, b) == {
        "道": ["dao", {"Way"}]
    }


def test_intersect_glossaries_keeps_shared_term_even_with_no_shared_translations(gd_module):
    assert gd_module.intersect_glossaries(
        {"道": ["dao", {"Way"}]}, {"道": ["dao", {"Path"}]}
    ) == {"道": ["dao", set()]}


def test_intersect_glossaries_no_shared_terms(gd_module):
    assert gd_module.intersect_glossaries(
        {"道": ["dao", {"Way"}]}, {"德": ["de", {"Virtue"}]}
    ) == {}


# find_single_character_match — upcoming function, not yet in glossary_dictate.py
# Contract: two strings of Chinese text -> bool; True iff a Chinese character occurs in both.

@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("天地", "地人", True),                  # one shared character
        ("天地", "山水", False),                 # no shared characters
        ("道", "大道", True),                   # single-character input
        ("天地", "天地", True),                 # identical input
        ("天道自然", "人道天地", True),            # match anywhere in strings
        ("天天", "天", True),                   # repeated character
        ("", "天地", False),                   # empty first input
        ("天地", "", False),                   # empty second input
        ("", "", False),                       # both empty
        ("山水", "水山", True),                 # order irrelevant
        ("天地，山水", "人間山河", True),         # longer passages with punctuation
        ("天地，", "山水，", False),             # common punctuation alone does not count
        ("天地 ", "山水 ", False),             # common whitespace alone does not count
    ],
)
def test_find_single_character_match(gd_module, first, second, expected):
    result = gd_module.find_single_character_match(first, second)
    assert type(result) is bool
    assert result is expected
