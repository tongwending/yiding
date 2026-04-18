import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
SEGMENTED_TEXT_PATH = DATA_DIR / "segmented_text.py"
KANRIPO_TEXT_PATH = DATA_DIR / "kanripo_text.py"


class FakeKanripoModule(types.ModuleType):
    def __init__(self):
        super().__init__("kanripo")
        self.responses = {}
        self.calls = []

    def get_result_file(self, code):
        self.calls.append(code)
        return self.responses.get(code, "404: Not Found")


@pytest.fixture(scope="session")
def kt_module():
    """
    Prefer the real package import if available. Otherwise load the uploaded file
    into a fake package so its relative imports succeed.
    """
    fake_kanripo = FakeKanripoModule()
    previous_kanripo = sys.modules.get("kanripo")
    sys.modules["kanripo"] = fake_kanripo

    try:
        try:
            module = importlib.import_module("yiding.kanripo_text")
        except Exception:
            package_name = "_kt_testpkg"
            package = types.ModuleType(package_name)
            package.__path__ = [str(DATA_DIR)]
            sys.modules[package_name] = package

            seg_spec = importlib.util.spec_from_file_location(
                f"{package_name}.segmented_text", SEGMENTED_TEXT_PATH
            )
            seg_module = importlib.util.module_from_spec(seg_spec)
            sys.modules[seg_spec.name] = seg_module
            assert seg_spec.loader is not None
            seg_spec.loader.exec_module(seg_module)

            tm_mod = types.ModuleType(f"{package_name}.text_manipulators")
            tm_mod.pop_glosses = lambda text: (text, [])
            sys.modules[f"{package_name}.text_manipulators"] = tm_mod

            spec = importlib.util.spec_from_file_location(
                f"{package_name}.kanripo_text", KANRIPO_TEXT_PATH
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            assert spec.loader is not None
            spec.loader.exec_module(module)

        module._fake_kanripo_for_tests = fake_kanripo
        return module
    finally:
        if previous_kanripo is not None:
            sys.modules["kanripo"] = previous_kanripo


@pytest.fixture
def fake_kanripo(kt_module, monkeypatch):
    fake = FakeKanripoModule()
    monkeypatch.setattr(kt_module, "kanripo", fake)
    return fake


# ------------------------------
# pure parser helpers
# ------------------------------


def test_detect_title_returns_title_when_present(kt_module):
    text = "#+TITLE: Daozang text\n#+PROPERTY: KR5\nBody"

    assert kt_module.detect_title(text) == "Daozang text"



def test_detect_title_returns_unknown_when_missing(kt_module):
    assert kt_module.detect_title("No title here") == "Unknown Title"



def test_detect_properties_collects_all_properties(kt_module):
    text = "#+TITLE: X\n#+PROPERTY: KR5a\n#+PROPERTY: Daoist canon\nBody"

    assert kt_module.detect_properties(text) == ["KR5a", "Daoist canon"]



def test_detect_page_returns_short_line_unchanged(kt_module):
    assert kt_module.detect_page("1a") == "1a"



def test_detect_page_formats_long_kanripo_label_with_segment(kt_module):
    label = "x" * 17 + "003" + "_" + "045" + "a"

    assert kt_module.detect_page(label) == "3.45a"



def test_detect_page_formats_long_kanripo_label_without_segment_prefix_when_zero(kt_module):
    label = "x" * 17 + "000" + "_" + "045" + "b"

    assert kt_module.detect_page(label) == "45b"



def test_detect_page_raises_for_invalid_long_label(kt_module):
    bad_label = "x" * 17 + "abc" + "_" + "045" + "a"

    with pytest.raises(ValueError, match="Label is"):
        kt_module.detect_page(bad_label)



def test_slice_into_sections_splits_by_page_breaks_and_removes_page_line(kt_module):
    text = (
        "header ignored\n"
        "<pb:" + "x" * 13 + "001" + "_" + "010" + "a>\n"
        "line A\n"
        "line B\n"
        "<pb:" + "x" * 13 + "000" + "_" + "011" + "b>\n"
        "line C\n"
    )

    sections, labels = kt_module.slice_into_sections(text)

    assert sections == ["line A\nline B\n", "line C\n"]
    assert labels == ["1.10a", "11b"]


# ------------------------------
# class behavior
# ------------------------------


def test_full_title_includes_kanripo_code_and_optional_translation(kt_module, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_and_parse", lambda self: None)

    text = kt_module.KanripoText("KR5a0001")
    text.original_title = "太上老君說常清靜經"
    text.translated_title = "Scripture of Clarity and Stillness"

    assert text.full_title() == "KR5a0001 - 太上老君說常清靜經 - Scripture of Clarity and Stillness"



def test_fetch_and_parse_raises_when_no_juan_found(kt_module, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_segments", lambda self: [])

    with pytest.raises(ValueError, match="nonexistent or unknown Kanripo documentation"):
        kt_module.KanripoText("KR5bad")



def test_fetch_and_parse_populates_title_properties_segments_and_labels(kt_module, monkeypatch):
    raw_juan = [
        (
            "#+TITLE: Sample Title\n"
            "#+PROPERTY: KR5 test\n"
            "#+PROPERTY: Daoist text\n"
            "<pb:" + "x" * 13 + "001" + "_" + "001" + "a>\n"
            "first page\n"
            "<pb:" + "x" * 13 + "001" + "_" + "001" + "b>\n"
            "second page\n"
        )
    ]
    monkeypatch.setattr(kt_module.KanripoText, "fetch_segments", lambda self: raw_juan)

    text = kt_module.KanripoText("KR5a0001")

    assert text.original_title == "Sample Title"
    assert text.properties == ["KR5 test", "Daoist text"]
    assert text.segments == ["first page\n", "second page\n"]
    assert text.page_labels == ["1.1a", "1.1b"]
    assert text.page_lines == [1, 1]



def test_init_with_glosses_off_strips_glosses_and_collects_them(kt_module, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_and_parse", lambda self: None)

    calls = []

    def fake_pop_glosses(segment):
        calls.append(segment)
        return (segment + "-clean", [segment + "-gloss"])

    monkeypatch.setattr(kt_module.text_manipulators, "pop_glosses", fake_pop_glosses)

    text = kt_module.KanripoText("KR5a0001", glosses_on=False)
    text.segments = ["seg1", "seg2"]
    text.glosses = []
    text.page_lines = []

    # rerun the gloss-removal loop directly by reconstructing with prepared data
    monkeypatch.setattr(
        kt_module.KanripoText,
        "fetch_and_parse",
        lambda self: (setattr(self, "segments", ["seg1", "seg2"]), setattr(self, "page_labels", ["1a", "1b"]), setattr(self, "original_title", "T")),
    )
    text = kt_module.KanripoText("KR5a0001", glosses_on=False)

    assert text.segments == ["seg1-clean", "seg2-clean"]
    assert text.glosses == [["seg1-gloss"], ["seg2-gloss"]]
    assert calls == ["seg1", "seg2"]



def test_fetch_segments_collects_valid_juan_and_strips_paragraph_marks(kt_module, fake_kanripo, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_and_parse", lambda self: None)
    text = kt_module.KanripoText("KR5a0001")

    fake_kanripo.responses = {
        "KR5a0001_000": "#+TITLE: T\n<pb:page1>\nA¶B",
        "KR5a0001_001": "#+TITLE: T\n<pb:page2>\nC",
        "KR5a0001_002": "404: Not Found",
    }

    result = text.fetch_segments()

    assert result == ["#+TITLE: T\n<pb:page1>\nAB", "#+TITLE: T\n<pb:page2>\nC"]
    assert fake_kanripo.calls == ["KR5a0001_000", "KR5a0001_001", "KR5a0001_002"]



def test_fetch_segments_raises_when_fetch_result_is_not_string(kt_module, fake_kanripo, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_and_parse", lambda self: None)
    text = kt_module.KanripoText("KR5a0001")
    fake_kanripo.responses = {"KR5a0001_000": None}

    with pytest.raises(ValueError, match="Something wrong"):
        text.fetch_segments()



def test_fetch_segments_raises_after_three_consecutive_misfetches(kt_module, fake_kanripo, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_and_parse", lambda self: None)
    text = kt_module.KanripoText("KR5a0001")
    fake_kanripo.responses = {
        "KR5a0001_000": "metadata only",
        "KR5a0001_001": "still metadata",
        "KR5a0001_002": "more metadata",
    }

    with pytest.raises(ValueError, match="Something is nonexistent or unknown Kanripo documentation"):
        text.fetch_segments()



def test_fetch_segments_tolerates_one_bad_fetch_between_valid_pages(kt_module, fake_kanripo, monkeypatch):
    monkeypatch.setattr(kt_module.KanripoText, "fetch_and_parse", lambda self: None)
    text = kt_module.KanripoText("KR5a0001")
    fake_kanripo.responses = {
        "KR5a0001_000": "<pb:page1>\nA",
        "KR5a0001_001": "metadata only",
        "KR5a0001_002": "<pb:page2>\nB",
        "KR5a0001_003": "404: Not Found",
    }

    result = text.fetch_segments()

    assert result == ["<pb:page1>\nA", "<pb:page2>\nB"]

