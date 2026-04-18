import importlib
import importlib.util
import pathlib
import sys

import pytest



def load_segmented_text_module():
    try:
        return importlib.import_module("yiding.segmented_text")
    except ModuleNotFoundError:
        path = pathlib.Path(__file__).resolve().parents[1] / "segmented_text.py"
        spec = importlib.util.spec_from_file_location("segmented_text", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


segmented_text_module = load_segmented_text_module()
SegmentedText = segmented_text_module.SegmentedText


class FakeRFONTS:
    def __init__(self):
        self.calls = []

    def set(self, key, value):
        self.calls.append((key, value))


class FakeRPr:
    def __init__(self):
        self.rFonts = FakeRFONTS()


class FakeElement:
    def __init__(self):
        self.rPr = FakeRPr()


class FakeColor:
    def __init__(self):
        self.rgb = None


class FakeFont:
    def __init__(self):
        self.name = None
        self.size = None
        self.bold = False
        self.italic = False
        self.color = FakeColor()


class FakeRun:
    def __init__(self, text):
        self.text = text
        self.font = FakeFont()
        self._element = FakeElement()


class FakeParagraph:
    def __init__(self):
        self.alignment = None
        self.runs = []

    def add_run(self, text):
        run = FakeRun(text)
        self.runs.append(run)
        return run


class FakeCell:
    def __init__(self):
        self.paragraphs = [FakeParagraph()]
        self.width = None


class FakeColumn:
    def __init__(self):
        self.width = None


class FakeRow:
    def __init__(self, cols):
        self.cells = [FakeCell() for _ in range(cols)]
        self.allow_break_across_pages = True


class FakeTable:
    def __init__(self, rows, cols):
        self.rows = [FakeRow(cols) for _ in range(rows)]
        self.columns = [FakeColumn() for _ in range(cols)]
        self.autofit = True

    def cell(self, i, j):
        return self.rows[i].cells[j]


class FakeSection:
    def __init__(self):
        self.orientation = None
        self.page_width = 1200
        self.page_height = 800
        self.left_margin = 100
        self.right_margin = 100


class FakeStyle:
    def __init__(self):
        self.font = FakeFont()


class FakeDocument:
    def __init__(self):
        self.sections = [FakeSection()]
        self.styles = {"Normal": FakeStyle()}
        self.paragraphs = []
        self.page_breaks = 0
        self.tables = []
        self.saved_filename = None

    def add_paragraph(self):
        paragraph = FakeParagraph()
        self.paragraphs.append(paragraph)
        return paragraph

    def add_page_break(self):
        self.page_breaks += 1

    def add_table(self, rows, cols):
        table = FakeTable(rows, cols)
        self.tables.append(table)
        return table

    def save(self, filename):
        self.saved_filename = filename


@pytest.fixture
def sample_settings():
    return {
        "punctuation": {
            "facsimile_span": 2,
            "punctuation_span": 1,
            "max_unsegmented_span": 500,
            "max_punctuation_attempts": 3,
            "cross_check": {"enabled": True},
            "punctuation": "mock-punctuator",
            "cross_examination": "mock-punctuation-exam",
            "cross_correction": "mock-punctuation-corrector",
            "guidelines": "Punctuation guidelines.",
        },
        "translation": {
            "language": "English",
            "glossary": "glossary.csv",
            "translation_span": 2,
            "cross_check": {"enabled": True},
            "llm_glossary_selection": {"enabled": True},
            "translation": "mock-translator",
            "glossary_extraction": "mock-glossary-extractor",
            "cross_examination": "mock-translation-exam",
            "cross_correction": "mock-translation-corrector",
            "glossary_selection": "mock-glossary-selector",
            "guidelines": "Translation guidelines.",
        },
    }


@pytest.fixture
def text(sample_settings):
    txt = SegmentedText()
    txt.settings = sample_settings
    txt.original_title = "道德經"
    txt.translated_title = "Daodejing"
    txt.properties = ["KR5 sample", "Genre: Daoist scripture"]
    txt.segment_labels = ["1a", "1b"]
    txt.punctuated_segments = ["道可道，非常道。", "名可名，非常名。"]
    txt.translated_segments = [
        "The Way that can be spoken is not the constant Way.",
        "The name that can be named is not the constant name.",
    ]
    return txt


@pytest.fixture
def fake_document_factory(monkeypatch):
    created = []

    def factory():
        doc = FakeDocument()
        created.append(doc)
        return doc

    monkeypatch.setattr(segmented_text_module, "Document", factory)
    return created


@pytest.mark.parametrize(
    ("original_title", "translated_title", "expected"),
    [
        (None, None, "Untitled"),
        ("道德經", None, "道德經"),
        ("道德經", "Daodejing", "道德經 - Daodejing"),
    ],
)
def test_full_title_variants(original_title, translated_title, expected):
    txt = SegmentedText()
    txt.original_title = original_title
    txt.translated_title = translated_title

    assert txt.full_title() == expected


def test_empty_translation_clears_translation_state_and_title_by_default():
    txt = SegmentedText()
    txt.translation_i = 5
    txt.translated_segments = ["one", "two"]
    txt.translation_glossary = {"道": "Way"}
    txt.translated_title = "Existing title"

    txt.empty_translation()

    assert txt.translation_i == 0
    assert txt.translated_segments == []
    assert txt.translation_glossary == {}
    assert txt.translated_title is None


def test_empty_translation_can_keep_title():
    txt = SegmentedText()
    txt.translated_title = "Existing title"
    txt.translated_segments = ["one"]
    txt.translation_i = 1
    txt.translation_glossary = {"道": "Way"}

    txt.empty_translation(empty_title=False)

    assert txt.translation_i == 0
    assert txt.translated_segments == []
    assert txt.translation_glossary == {}
    assert txt.translated_title == "Existing title"


def test_print_punctuation_settings_includes_optional_cross_check_fields_when_enabled(sample_settings):
    txt = SegmentedText()
    txt.settings = sample_settings

    rendered = txt.print_punctuation_settings()

    assert "facsimile_span: 2" in rendered
    assert "cross_examination: mock-punctuation-exam" in rendered
    assert "cross_correction: mock-punctuation-corrector" in rendered
    assert rendered.endswith("guidelines:\nPunctuation guidelines.")


def test_print_translation_settings_omits_optional_fields_when_disabled(sample_settings):
    txt = SegmentedText()
    sample_settings["translation"]["cross_check"]["enabled"] = False
    sample_settings["translation"]["llm_glossary_selection"]["enabled"] = False
    txt.settings = sample_settings

    rendered = txt.print_translation_settings()

    assert "language: English" in rendered
    assert "cross_examination:" not in rendered
    assert "cross_correction:" not in rendered
    assert "\nglossary_selection:" not in rendered
    assert rendered.endswith("guidelines:\nTranslation guidelines.")


def test_print_to_file_delegates_to_docx_printer(text, monkeypatch):
    called = {}

    def fake_print_to_docx(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(text, "print_to_docx", fake_print_to_docx)

    text.print_to_file(punctuation=False, translation=True, output_file="docx", table=False)

    assert called == {"punctuation": False, "translation": True, "table": False}


def test_print_to_docx_raises_on_length_mismatch(sample_settings):
    txt = SegmentedText()
    txt.settings = sample_settings
    txt.original_title = "道德經"
    txt.punctuated_segments = ["甲", "乙"]
    txt.translated_segments = ["A"]

    with pytest.raises(ValueError, match="Segment lists' length mismatch"):
        txt.print_to_docx(punctuation=True, translation=True, table=True)


def test_print_to_docx_table_mode_sets_landscape_builds_table_and_saves_expected_filename(
    text, fake_document_factory
):
    text.print_to_docx(punctuation=True, translation=True, table=True)

    doc = fake_document_factory[0]
    section = doc.sections[0]
    table = doc.tables[0]

    assert section.orientation == segmented_text_module.WD_ORIENTATION.LANDSCAPE
    assert section.page_width == 800
    assert section.page_height == 1200
    assert len(table.rows) == 2
    assert len(table.columns) == 2
    assert table.autofit is False
    assert all(row.allow_break_across_pages is False for row in table.rows)
    assert table.cell(0, 0).paragraphs[-1].runs[0].text == "1a\n"
    assert table.cell(0, 0).paragraphs[-1].runs[1].text == "道可道，非常道。"
    assert table.cell(0, 1).paragraphs[-1].runs[0].text == "1a\n"
    assert table.cell(0, 1).paragraphs[-1].runs[1].text == "The Way that can be spoken is not the constant Way."
    assert doc.saved_filename == "道德經 - Daodejing.docx"


def test_print_to_docx_punctuation_only_uses_suffix_and_no_table(text, fake_document_factory):
    text.print_to_docx(punctuation=True, translation=False, table=False)

    doc = fake_document_factory[0]

    assert doc.tables == []
    assert doc.saved_filename == "道德經 - Daodejing - Punctuated.docx"


def test_print_to_docx_translation_only_uses_suffix_and_no_table(text, fake_document_factory):
    text.print_to_docx(punctuation=False, translation=True, table=False)

    doc = fake_document_factory[0]

    assert doc.tables == []
    assert doc.saved_filename == "道德經 - Daodejing - Translated.docx"


def test_print_to_docx_uses_untitled_when_no_titles(sample_settings, fake_document_factory):
    txt = SegmentedText()
    txt.settings = sample_settings
    txt.segment_labels = ["1a"]
    txt.punctuated_segments = ["甲。"]

    txt.print_to_docx(punctuation=True, translation=False, table=False)

    doc = fake_document_factory[0]

    assert doc.saved_filename == "Untitled - Punctuated.docx"


def test_print_to_docx_truncates_long_filename(sample_settings, fake_document_factory):
    txt = SegmentedText()
    txt.settings = sample_settings
    txt.original_title = "甲" * 150
    txt.segment_labels = ["1a"]
    txt.punctuated_segments = ["甲。"]

    txt.print_to_docx(punctuation=True, translation=False, table=False)

    doc = fake_document_factory[0]

    expected_prefix = "甲" * segmented_text_module.CHARACTER_CAP
    assert doc.saved_filename == f"{expected_prefix} - Punctuated.docx"


def test_print_to_docx_includes_titles_and_page_breaks_in_full_output(text, fake_document_factory):
    text.print_to_docx(punctuation=True, translation=True, table=True)

    doc = fake_document_factory[0]

    assert doc.page_breaks == 2
    assert doc.paragraphs[0].runs[0].text == "\n\n\n道德經"
    assert doc.paragraphs[1].runs[0].text == "Daodejing"
    settings_block = doc.paragraphs[2].runs[0].text
    assert "Text properties:" in settings_block
    assert "KR5 sample" in settings_block
    assert "Punctuation settings:" in settings_block
    assert "Translation settings:" in settings_block


def test_print_to_docx_non_table_output_adds_separate_paragraphs_for_label_and_segments(
    text, fake_document_factory
):
    text.print_to_docx(punctuation=True, translation=True, table=False)

    doc = fake_document_factory[0]
    paragraph_texts = [run.text for paragraph in doc.paragraphs[3:] for run in paragraph.runs]

    assert "1a\n" in paragraph_texts
    assert "道可道，非常道。\n\n" in paragraph_texts
    assert "The Way that can be spoken is not the constant Way.\n\n" in paragraph_texts
    assert "1b\n" in paragraph_texts


