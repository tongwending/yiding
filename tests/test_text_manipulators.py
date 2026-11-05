"""Tests for yiding.text_manipulators.

Run from the repository root:
    python -m pytest tests/test_text_manipulators.py -v

Planned API (not implemented in the uploaded source yet):
    find_character_variants(character) -> iterable of individual characters
    normalize_traditional(segment) -> str

Tests for these two functions skip only while the corresponding function is absent.
Once it exists, its tests execute normally and failures are reported.
"""

import importlib

import pytest


@pytest.fixture(scope="module")
def tm_module():
    # Import the actual package. Do not mask broken imports with a fallback.
    return importlib.import_module("yiding.text_manipulators")


@pytest.fixture
def find_character_variants(tm_module):
    function = getattr(tm_module, "find_character_variants", None)
    if function is None:
        pytest.skip("Planned function find_character_variants() is not implemented")
    return function


@pytest.fixture
def normalize_traditional(tm_module):
    function = getattr(tm_module, "normalize_traditional", None)
    if function is None:
        pytest.skip("Planned function normalize_traditional() is not implemented")
    return function


# ---- strip_punctuation -----------------------------------------------------


def test_strip_punctuation_keeps_chinese_parentheses_and_placeholders(tm_module):
    assert tm_module.strip_punctuation('道, 德 123abc。\n⬤(注)') == '道德⬤(注)'


@pytest.mark.parametrize("character", ['⬤', '■', '◆', '▲', '(', ')'])
def test_strip_punctuation_preserves_special_characters(tm_module, character):
    assert tm_module.strip_punctuation(f'甲{character}乙') == f'甲{character}乙'


@pytest.mark.parametrize("separator", ['，', '。', '！', '？', '：', '；', '、', '　', '\u00a0', '\n', '\t', 'Ａ', '1', 'a'])
def test_strip_punctuation_removes_known_separators(tm_module, separator):
    assert tm_module.strip_punctuation(f'甲{separator}乙') == '甲乙'


def test_strip_punctuation_empty_string(tm_module):
    assert tm_module.strip_punctuation('') == ''


# ---- strip_invalid_characters ---------------------------------------------


def test_strip_invalid_characters_removes_windows_invalid_filename_chars_and_controls(tm_module):
    assert tm_module.strip_invalid_characters('a<b>:c"d/e\\f|g?h*i\x00\x1f') == 'abcdefghi'


def test_strip_invalid_characters_preserves_chinese_and_valid_punctuation(tm_module):
    assert tm_module.strip_invalid_characters('道德，天地。-_.') == '道德，天地。-_.'


def test_strip_invalid_characters_empty_string(tm_module):
    assert tm_module.strip_invalid_characters('') == ''


# ---- segmentate -----------------------------------------------------------


@pytest.mark.parametrize('text', ['甲乙丙', '', '   \n\t'])
def test_segmentate_without_breaks_returns_only_leftover(tm_module, text):
    expected_leftover = text if text.strip() else ''
    assert tm_module.segmentate(text) == ([], expected_leftover)


def test_segmentate_splits_on_break_and_keeps_final_leftover(tm_module):
    assert tm_module.segmentate('甲<break>乙<break>丙') == (['甲', '乙'], '丙')


def test_segmentate_uses_last_segment_as_leftover_when_tail_is_whitespace(tm_module):
    assert tm_module.segmentate('甲<break>乙<break>   \n\t') == (['甲'], '乙')


def test_segmentate_retains_explicit_empty_segments(tm_module):
    assert tm_module.segmentate('甲<break><break>乙') == (['甲', ''], '乙')


def test_segmentate_final_break_leaves_previous_segment_as_leftover(tm_module):
    assert tm_module.segmentate('甲<break>乙<break>') == (['甲'], '乙')


# ---- chop_from_working_segment --------------------------------------------


def test_chop_single_line_returns_label_and_remainder(tm_module):
    result = tm_module.chop_from_working_segment('天地', '天地玄黃', [['1a', 1, 1]])
    assert result == ('天地', '玄黃', '1a.1', [['1a', 1, 1]])


def test_chop_ignores_punctuation_in_requested_text(tm_module):
    result = tm_module.chop_from_working_segment('甲，乙。', '甲，乙丙', [['1a', 1, 1]])
    assert result == ('甲，乙', '丙', '1a.1', [['1a', 1, 1]])


def test_chop_consumes_line_break_with_razorcut(tm_module):
    result = tm_module.chop_from_working_segment('甲乙', '甲乙\n丙丁', [['1a', 1, 2]])
    assert result == ('甲乙\n', '丙丁', '1a.1', [['1a', 2, 2]])


def test_chop_spans_multiple_lines_on_same_page(tm_module):
    result = tm_module.chop_from_working_segment('甲乙丙丁', '甲乙\n丙丁\n戊己', [['1a', 1, 3]])
    assert result == ('甲乙\n丙丁\n', '戊己', '1a.1–2', [['1a', 3, 3]])


def test_chop_can_span_page_boundaries(tm_module):
    result = tm_module.chop_from_working_segment(
        '甲乙丙丁戊己', '甲乙\n丙丁\n戊己', [['1a', 1, 2], ['1b', 1, 1]]
    )
    assert result == ('甲乙\n丙丁\n戊己', '', '1a.1–1b.1', [['1b', 1, 1]])


def test_chop_skips_leading_newlines_and_updates_start_line(tm_module):
    result = tm_module.chop_from_working_segment('甲乙', '\n甲乙', [['1a', 1, 2]])
    assert result == ('甲乙', '', '1a.2', [['1a', 2, 2]])


def test_chop_returns_none_when_requested_text_is_only_punctuation(tm_module):
    result = tm_module.chop_from_working_segment('，。!?', '甲乙', [['1a', 1, 1]])
    assert result == (None, '甲乙', None, [['1a', 1, 1]])


def test_chop_raises_for_missing_character(tm_module):
    with pytest.raises(ValueError, match='Missing character: 丙'):
        tm_module.chop_from_working_segment('甲丙', '甲乙', [['1a', 1, 1]])


def test_chop_raises_label_error_when_labels_missing_for_leading_newline(tm_module):
    with pytest.raises(ValueError, match="Page'n'lines labels misaligned"):
        tm_module.chop_from_working_segment('甲', '\n甲', [])


def test_chop_raises_label_error_with_no_labels(tm_module):
    with pytest.raises(ValueError, match="Page'n'lines labels misaligned"):
        tm_module.chop_from_working_segment('甲', '甲', [])


# ---- clean ----------------------------------------------------------------


def test_clean_removes_slashes_and_parenthetical_line_break_patterns(tm_module):
    assert tm_module.clean('甲/乙)\n(丙)\n　(丁)') == '甲乙\n丙\n丁)'


@pytest.mark.parametrize('value', ['', None])
def test_clean_returns_emptyish_values_unchanged(tm_module, value):
    assert tm_module.clean(value) == value


def test_clean_preserves_unrelated_punctuation_and_text(tm_module):
    assert tm_module.clean('甲（注）\n乙。') == '甲（注）\n乙。'


# ---- pop_glosses ----------------------------------------------------------


def test_pop_glosses_extracts_multiple_glosses_and_inserts_marker(tm_module):
    assert tm_module.pop_glosses('甲(注一)乙\n(注二)丙', marker='*') == (
        '甲*乙\n*丙', ['注一', '注二']
    )


def test_pop_glosses_without_marker_removes_parenthetical_content(tm_module):
    assert tm_module.pop_glosses('甲(注)乙') == ('甲乙', ['注'])


def test_pop_glosses_leaves_unparenthesized_text_alone(tm_module):
    assert tm_module.pop_glosses('甲乙。') == ('甲乙。', [])


def test_pop_glosses_handles_multiline_gloss(tm_module):
    assert tm_module.pop_glosses('甲(注一\n注二)乙', marker='*') == (
        '甲*乙', ['注一\n注二']
    )


def test_pop_glosses_does_not_extract_unbalanced_parentheses(tm_module):
    assert tm_module.pop_glosses('甲(未完乙') == ('甲(未完乙', [])


# ---- find_possible_terms --------------------------------------------------


def test_find_possible_terms_generates_all_contiguous_substrings(tm_module):
    assert tm_module.find_possible_terms('道德,經') == ['道', '德', '道德', '經']


def test_find_possible_terms_ignores_ascii_letters_digits_and_punctuation(tm_module):
    assert tm_module.find_possible_terms('A1道-B') == ['道']


def test_find_possible_terms_treats_placeholders_as_separators(tm_module):
    # Implementation builds _NON_CHARACTERS_SET before removing placeholders
    # from the punctuation-stripping table; the two functions differ here.
    assert tm_module.find_possible_terms('道⬤德') == ['道', '德']


def test_find_possible_terms_empty_string(tm_module):
    assert tm_module.find_possible_terms('') == []


def test_find_possible_terms_repeated_characters_keep_duplicate_substrings(tm_module):
    assert tm_module.find_possible_terms('人人') == ['人', '人', '人人']


def test_find_possible_terms_splits_at_chinese_punctuation_and_whitespace(tm_module):
    assert tm_module.find_possible_terms('天地，玄黃\n道德') == [
        '天', '地', '天地', '玄', '黃', '玄黃', '道', '德', '道德'
    ]


# ---- Planned: Chinese character variants ----------------------------------
# Proposed return contract: iterable of unique, single-character strings,
# including the input character. This is a suggested contract, not yet
# established by the source file. Change these tests if the API differs.


@pytest.mark.parametrize('character,required', [
    ('车', {'车', '車'}),
    ('国', {'国', '國'}),
    ('学', {'学', '學'}),
    ('峰', {'峰', '峯'}),  # traditional alternate form
])
def test_find_character_variants_includes_known_forms(
    find_character_variants, character, required
):
    variants = find_character_variants(character)
    assert not isinstance(variants, str), 'Return an iterable of characters, not one string'
    variants = list(variants)
    assert all(isinstance(char, str) and len(char) == 1 for char in variants)
    assert len(variants) == len(set(variants))
    assert required <= set(variants)


def test_find_character_variants_handles_one_to_many_simplification(find_character_variants):
    # 发 is the simplified representation of two traditional characters.
    assert {'发', '發', '髮'} <= set(find_character_variants('发'))


def test_find_character_variants_accepts_traditional_input(find_character_variants):
    assert {'车', '車'} <= set(find_character_variants('車'))


# ---- Planned: normalize text to traditional Chinese -----------------------
# Proposed return contract: normalized Unicode text. Retain punctuation,
# whitespace, and symbols; use lexical context to resolve ambiguous forms.


@pytest.mark.parametrize('source,expected', [
    ('中国', '中國'),
    ('学生', '學生'),
    ('中國', '中國'),
    ('', ''),
])
def test_normalize_traditional_basic_conversions(normalize_traditional, source, expected):
    assert normalize_traditional(source) == expected


def test_normalize_traditional_preserves_punctuation_whitespace_and_placeholders(normalize_traditional):
    assert normalize_traditional('中国， 学生。\n⬤') == '中國， 學生。\n⬤'


def test_normalize_traditional_disambiguates_multi_mapping_characters(normalize_traditional):
    # Simple per-character conversion is not sufficient for these cases.
    assert normalize_traditional('头发发展') == '頭髮發展'


def test_normalize_traditional_preserves_semantically_distinct_characters(normalize_traditional):
    # 后 is not always 後: 皇后 is the empress, not an adverb of time.
    assert normalize_traditional('皇后和后来') == '皇后和後來'


def test_normalize_traditional_standardizes_historical_variant(normalize_traditional):
    assert normalize_traditional('山峯') == '山峰'


def test_normalize_traditional_is_idempotent(normalize_traditional):
    source = '中國，頭髮與發展。'
    once = normalize_traditional(source)
    assert normalize_traditional(once) == once
