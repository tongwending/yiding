import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
TEXT_MANIPULATORS_PATH = DATA_DIR / "text_manipulators.py"


@pytest.fixture(scope="session")
def tm_module():
    try:
        return importlib.import_module("yiding.text_manipulators")
    except Exception:
        package_name = "_text_manipulators_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.text_manipulators",
            TEXT_MANIPULATORS_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


# ------------------------------
# strip_punctuation / strip_invalid_characters
# ------------------------------


def test_strip_punctuation_removes_punctuation_spaces_digits_and_latin_but_keeps_chinese_parentheses_and_placeholders(tm_module):
    text = '道, 德 123abc。\n⬤(注)'

    result = tm_module.strip_punctuation(text)

    assert result == '道德⬤(注)'



def test_strip_invalid_characters_removes_windows_invalid_filename_chars_and_controls(tm_module):
    text = 'a<b>:c"d/e\\f|g?h*i\x00\x1f'

    result = tm_module.strip_invalid_characters(text)

    assert result == 'abcdefghi'


# ------------------------------
# segmentate
# ------------------------------


def test_segmentate_without_breaks_returns_only_leftover(tm_module):
    segments, leftover = tm_module.segmentate('甲乙丙')

    assert segments == []
    assert leftover == '甲乙丙'



def test_segmentate_splits_on_break_and_keeps_final_leftover(tm_module):
    text = '甲<break>乙<break>丙'

    segments, leftover = tm_module.segmentate(text)

    assert segments == ['甲', '乙']
    assert leftover == '丙'



def test_segmentate_uses_last_segment_as_leftover_when_tail_is_only_whitespace(tm_module):
    text = '甲<break>乙<break>   \n\t'

    segments, leftover = tm_module.segmentate(text)

    assert segments == ['甲']
    assert leftover == '乙'


# ------------------------------
# chop_from_working_segment
# ------------------------------


def test_chop_from_working_segment_single_line_returns_label_and_remainder(tm_module):
    working = '天地玄黃'
    labels = [['1a', 1, 1]]

    chopped, remainder, label, new_labels = tm_module.chop_from_working_segment('天地', working, labels)

    assert chopped == '天地'
    assert remainder == '玄黃'
    assert label == '1a.1'
    assert new_labels == [['1a', 1, 1]]



def test_chop_from_working_segment_consumes_line_break_with_razorcut(tm_module):
    working = '甲乙\n丙丁'
    labels = [['1a', 1, 2]]

    chopped, remainder, label, new_labels = tm_module.chop_from_working_segment('甲乙', working, labels)

    assert chopped == '甲乙\n'
    assert remainder == '丙丁'
    assert label == '1a.1'
    assert new_labels == [['1a', 2, 2]]



def test_chop_from_working_segment_spans_multiple_lines_on_same_page(tm_module):
    working = '甲乙\n丙丁\n戊己'
    labels = [['1a', 1, 3]]

    chopped, remainder, label, new_labels = tm_module.chop_from_working_segment('甲乙丙丁', working, labels)

    assert chopped == '甲乙\n丙丁\n'
    assert remainder == '戊己'
    assert label == '1a.1–2'
    assert new_labels == [['1a', 3, 3]]



def test_chop_from_working_segment_can_span_page_boundaries(tm_module):
    working = '甲乙\n丙丁\n戊己'
    labels = [['1a', 1, 2], ['1b', 1, 1]]

    chopped, remainder, label, new_labels = tm_module.chop_from_working_segment('甲乙丙丁戊己', working, labels)

    assert chopped == '甲乙\n丙丁\n戊己'
    assert remainder == ''
    assert label == '1a.1–1b.1'
    assert new_labels == [['1b', 1, 1]]



def test_chop_from_working_segment_skips_leading_newlines_and_updates_start_line(tm_module):
    working = '\n甲乙'
    labels = [['1a', 1, 2]]

    chopped, remainder, label, new_labels = tm_module.chop_from_working_segment('甲乙', working, labels)

    assert chopped == '甲乙'
    assert remainder == ''
    assert label == '1a.2'
    assert new_labels == [['1a', 2, 2]]



def test_chop_from_working_segment_returns_none_when_chop_has_no_characters_after_stripping(tm_module):
    working = '甲乙'
    labels = [['1a', 1, 1]]

    chopped, remainder, label, new_labels = tm_module.chop_from_working_segment('，。!?', working, labels)

    assert chopped is None
    assert remainder == '甲乙'
    assert label is None
    assert new_labels == [['1a', 1, 1]]



def test_chop_from_working_segment_raises_for_missing_character(tm_module):
    working = '甲乙'
    labels = [['1a', 1, 1]]

    with pytest.raises(ValueError, match='Missing character: 丙'):
        tm_module.chop_from_working_segment('甲丙', working, labels)



def test_chop_from_working_segment_raises_label_error_when_labels_missing_for_leading_newline(tm_module):
    with pytest.raises(ValueError, match="Page'n'lines labels misaligned"):
        tm_module.chop_from_working_segment('甲', '\n甲', [])


# ------------------------------
# clean
# ------------------------------


def test_clean_removes_slashes_and_parenthetical_line_break_patterns(tm_module):
    result = tm_module.clean('甲/乙)\n(丙)\n　(丁)')

    assert result == '甲乙\n丙\n丁)'


def test_clean_returns_emptyish_values_unchanged(tm_module):
    assert tm_module.clean('') == ''
    assert tm_module.clean(None) is None


# ------------------------------
# pop_glosses
# ------------------------------


def test_pop_glosses_extracts_parenthetical_glosses_and_inserts_marker(tm_module):
    segment = '甲(注一)乙\n(注二)丙'

    stripped, glosses = tm_module.pop_glosses(segment, marker='*')

    assert stripped == '甲*乙\n*丙'
    assert glosses == ['注一', '注二']



def test_pop_glosses_without_marker_removes_parentheses_content(tm_module):
    stripped, glosses = tm_module.pop_glosses('甲(注)乙')

    assert stripped == '甲乙'
    assert glosses == ['注']


# ------------------------------
# find_possible_terms
# ------------------------------


def test_find_possible_terms_generates_all_substrings_of_each_phrase(tm_module):
    terms = tm_module.find_possible_terms('道德,經')

    assert terms == ['道', '德', '道德', '經']



def test_find_possible_terms_ignores_ascii_letters_digits_and_punctuation_as_separators(tm_module):
    terms = tm_module.find_possible_terms('A1道-B')

    assert terms == ['道']



def test_find_possible_terms_treats_placeholders_as_separators_because_snapshot_set_is_used(tm_module):
    terms = tm_module.find_possible_terms('道⬤德')

    assert terms == ['道', '德']
