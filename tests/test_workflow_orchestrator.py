import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
FALLBACK_MODULE_PATH = DATA_DIR / "workflow_orchestrator.py"


class DummyInvoker:
    def __init__(self, responses=None, instructions=""):
        self.responses = list(responses or [])
        self.instructions = instructions
        self.calls = []

    def invoke(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        if not self.responses:
            return None
        if len(self.responses) == 1:
            response = self.responses[0]
        else:
            response = self.responses.pop(0)
        return response(*args, **kwargs) if callable(response) else response


class DummyText:
    def __init__(self):
        self.settings = None
        self.log = "existing text log"
        self.translation_glossary = {}
        self.working_text = ""
        self.working_labels = []
        self.working_i = 0
        self.segments = []
        self.page_labels = []
        self.page_lines = []
        self.punctuated_segments = []
        self.unpunctuated_segments = []
        self.segment_labels = []
        self.is_punctuated = False
        self.translation_i = 0
        self.translated_segments = []
        self.original_title = ""
        self.translated_title = ""

    def full_title(self):
        return self.original_title or "untitled"


class DummyGate:
    def __init__(self):
        self.settings = {
            "translation": {
                "glossary": None,
                "language": "English",
                "translation_span": 2,
                "cross_check": {"enabled": False},
            },
            "punctuation": {
                "facsimile_span": 1,
                "max_unsegmented_span": 1000,
                "punctuation_span": 1,
                "max_punctuation_attempts": 2,
                "cross_check": {"enabled": False},
            },
        }
        self.glossary_selector = None
        self.glossary_extractor = DummyInvoker([""])
        self.punctuator = DummyInvoker([])
        self.punctuation_examinator = DummyInvoker([False])
        self.punctuation_corrector = DummyInvoker([])
        self.translator = DummyInvoker([], instructions="SYS:")
        self.translation_examinator = DummyInvoker([False])
        self.translation_corrector = DummyInvoker([])


@pytest.fixture(scope="session")
def wf_module():
    """
    Prefer the real package import if available. Otherwise load the uploaded file
    into a fake package so its relative imports succeed.
    """
    try:
        return importlib.import_module("yiding.workflow_orchestrator")
    except Exception:
        package_name = "_wf_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        segmented_text_mod = types.ModuleType(f"{package_name}.segmented_text")
        segmented_text_mod.SegmentedText = type("SegmentedText", (), {})
        sys.modules[f"{package_name}.segmented_text"] = segmented_text_mod

        prompt_gateway_mod = types.ModuleType(f"{package_name}.prompt_gateway")
        prompt_gateway_mod.PromptGateway = type("PromptGateway", (), {})
        sys.modules[f"{package_name}.prompt_gateway"] = prompt_gateway_mod

        glossary_mod = types.ModuleType(f"{package_name}.glossary_dictate")
        glossary_mod.load_glossary = lambda *_args, **_kwargs: {}
        glossary_mod.stylize_glossary = lambda glossary: glossary
        glossary_mod.destylize_glossary = lambda text: {}
        glossary_mod.update_glossary = lambda target, source: target.update(source)
        sys.modules[f"{package_name}.glossary_dictate"] = glossary_mod

        tm_mod = types.ModuleType(f"{package_name}.text_manipulators")
        tm_mod.find_possible_terms = lambda _segment: []
        tm_mod.clean = lambda text: text
        tm_mod.strip_punctuation = lambda text: text
        tm_mod.segmentate = lambda text: ([text], "")
        tm_mod.chop_from_working_segment = lambda x, working_text, working_labels: (
            working_text,
            "",
            "seg1",
            [],
        )
        tm_mod.strip_invalid_characters = lambda filename: filename
        sys.modules[f"{package_name}.text_manipulators"] = tm_mod

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.workflow_orchestrator",
            FALLBACK_MODULE_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


@pytest.fixture
def text():
    return DummyText()


@pytest.fixture
def gate():
    return DummyGate()


@pytest.fixture
def orch(wf_module, text, gate, monkeypatch):
    monkeypatch.setattr(wf_module, "load_glossary", lambda *_args, **_kwargs: {})
    return wf_module.WorkflowOrchestrator(text, gate)


# ------------------------------
# __init__
# ------------------------------


def test_init_loads_glossary_when_path_exists(wf_module, text, gate, monkeypatch):
    gate.settings["translation"]["glossary"] = "glossary.csv"
    monkeypatch.setattr(wf_module, "load_glossary", lambda path: {"道": "Way", "_path": path})

    orch = wf_module.WorkflowOrchestrator(text, gate)

    assert orch.text.settings is gate.settings
    assert orch.glossary == {"道": "Way", "_path": "glossary.csv"}



def test_init_uses_empty_glossary_when_no_glossary_path(wf_module, text, gate, monkeypatch):
    gate.settings["translation"]["glossary"] = None
    monkeypatch.setattr(wf_module, "load_glossary", lambda _path: {"should": "not be used"})

    orch = wf_module.WorkflowOrchestrator(text, gate)

    assert orch.glossary == {}
    assert orch.text.settings is gate.settings


# ------------------------------
# select_glossary / extract_glossary
# ------------------------------


def test_select_glossary_uses_selector_when_available(orch, monkeypatch):
    orch.glossary = {"道": "Way", "德": "Virtue"}
    orch.gate.glossary_selector = DummyInvoker(["道\n不存在"])
    monkeypatch.setattr(orch.__class__.__module__ and sys.modules[orch.__class__.__module__], "stylize_glossary", lambda d: f"STYLED:{d}")
    monkeypatch.setattr(sys.modules[orch.__class__.__module__].tm, "find_possible_terms", lambda _segment: pytest.fail("fallback should not be used"))

    result = orch.select_glossary("道可道")

    assert result == "STYLED:{'道': 'Way'}"
    assert orch.gate.glossary_selector.calls[0]["args"][0] == "Chinese segment:\n道可道"



def test_select_glossary_falls_back_to_find_possible_terms(orch, monkeypatch):
    orch.glossary = {"空": "Emptiness"}
    monkeypatch.setattr(sys.modules[orch.__class__.__module__].tm, "find_possible_terms", lambda _segment: ["道", "空"])
    monkeypatch.setattr(sys.modules[orch.__class__.__module__], "stylize_glossary", lambda d: d)

    result = orch.select_glossary("色即是空")

    assert result == {"空": "Emptiness"}



def test_extract_glossary_updates_both_global_and_translation_glossaries(orch, monkeypatch):
    updates = []

    def fake_update(target, source):
        updates.append((target, source.copy()))
        target.update(source)

    orch.gate.glossary_extractor = DummyInvoker(["道: Way"])
    monkeypatch.setattr(sys.modules[orch.__class__.__module__], "destylize_glossary", lambda _text: {"道": "Way"})
    monkeypatch.setattr(sys.modules[orch.__class__.__module__], "update_glossary", fake_update)

    orch.extract_glossary("道", "Way")

    assert orch.glossary == {"道": "Way"}
    assert orch.text.translation_glossary == {"道": "Way"}
    assert len(updates) == 2
    sent_prompt = orch.gate.glossary_extractor.calls[0]["args"][0]
    assert "Chinese segment:\n道" in sent_prompt
    assert "English translation:\nWay" in sent_prompt


# ------------------------------
# translate_title / resume_translation
# ------------------------------


def test_translate_title_sets_title_extracts_glossary_and_saves(orch, monkeypatch):
    saved = []
    extracted = []

    orch.text.original_title = "道德經"
    orch.gate.translator = DummyInvoker(["  Dao De Jing  "], instructions="SYS:")
    monkeypatch.setattr(orch, "select_glossary", lambda _segment: "GLOSSARY")
    monkeypatch.setattr(orch, "extract_glossary", lambda original, translation: extracted.append((original, translation)))
    monkeypatch.setattr(orch, "save_as_pickle", lambda filename=None: saved.append(filename))

    orch.translate_title()

    assert orch.text.translated_title == "Dao De Jing"
    assert orch.gate.translator.calls[0]["args"][0] == "道德經"
    assert orch.gate.translator.calls[0]["kwargs"]["instructions"] == "SYS:GLOSSARY"
    assert extracted == [("道德經", "Dao De Jing")]
    assert len(saved) == 1



def test_resume_translation_calls_translate_title_when_needed(orch, monkeypatch):
    called = []
    orch.text.original_title = "題目"
    orch.text.translated_title = ""
    orch.text.is_punctuated = True
    orch.text.punctuated_segments = []

    monkeypatch.setattr(orch, "translate_title", lambda: called.append("translate_title"))

    orch.resume_translation()

    assert called == ["translate_title"]



def test_resume_translation_calls_resume_punctuation_when_text_not_punctuated(orch, monkeypatch):
    called = []
    orch.text.is_punctuated = False
    orch.text.punctuated_segments = []

    monkeypatch.setattr(orch, "resume_punctuation", lambda: called.append("resume_punctuation"))

    orch.resume_translation()

    assert called == ["resume_punctuation"]



def test_resume_translation_translates_segments_increments_state_and_uses_previous_context(orch, monkeypatch):
    extracted = []
    saved = []

    orch.text.is_punctuated = True
    orch.text.punctuated_segments = ["甲。", "乙。"]
    orch.text.segment_labels = ["seg1", "seg2"]
    orch.gate.translator = DummyInvoker([" one ", " two "], instructions="SYS:")

    monkeypatch.setattr(orch, "select_glossary", lambda _segment: "")
    monkeypatch.setattr(orch, "extract_glossary", lambda original, translation: extracted.append((original, translation)))
    monkeypatch.setattr(orch, "save_as_pickle", lambda filename=None: saved.append(filename))

    orch.resume_translation()

    assert orch.text.translated_segments == ["one", "two"]
    assert orch.text.translation_i == 2
    assert extracted == [("甲。", "one"), ("乙。", "two")]
    assert len(saved) == 2

    second_prompt = orch.gate.translator.calls[1]["args"][0]
    assert "Preceding text:\n甲。" in second_prompt
    assert "Preceding translation:\none" in second_prompt
    assert "Text to be translated:\n乙。" in second_prompt
    assert orch.gate.translator.calls[0]["kwargs"]["instructions"] == "SYS:No glossary provided."



def test_resume_translation_corrects_inconsistent_segment_when_cross_check_fails(orch, monkeypatch):
    orch.text.is_punctuated = True
    orch.text.punctuated_segments = ["甲。", "乙。"]
    orch.text.segment_labels = ["seg1", "seg2"]
    orch.gate.settings["translation"]["cross_check"]["enabled"] = True
    orch.gate.translator = DummyInvoker(["first", "bad second"], instructions="SYS:")
    orch.gate.translation_examinator = DummyInvoker([True])
    orch.gate.translation_corrector = DummyInvoker([" corrected second "])

    monkeypatch.setattr(orch, "select_glossary", lambda _segment: "")
    monkeypatch.setattr(orch, "extract_glossary", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(orch, "save_as_pickle", lambda filename=None: None)

    orch.resume_translation()

    assert orch.text.translated_segments == ["first", "corrected second"]
    assert len(orch.gate.translation_examinator.calls) == 1
    assert len(orch.gate.translation_corrector.calls) == 1


# ------------------------------
# resume_punctuation
# ------------------------------


def _letters_only(text):
    return "".join(ch for ch in text if ch.isalpha())



def test_resume_punctuation_retries_until_response_is_uncorrupted(orch, monkeypatch):
    saved = []
    orch.text.segments = ["ABC"]
    orch.text.page_labels = ["p1"]
    orch.text.page_lines = [1]
    orch.gate.punctuator = DummyInvoker(["XXX", "A.B.C"])

    module = sys.modules[orch.__class__.__module__]
    monkeypatch.setattr(module.tm, "clean", lambda text: text)
    monkeypatch.setattr(module.tm, "strip_punctuation", _letters_only)
    monkeypatch.setattr(module.tm, "segmentate", lambda _text: (["A.B.C"], ""))
    monkeypatch.setattr(module.tm, "chop_from_working_segment", lambda x, working_text, working_labels: ("ABC", "", "seg1", []))
    monkeypatch.setattr(orch, "save_as_pickle", lambda filename=None: saved.append(filename))

    orch.resume_punctuation()

    assert orch.text.unpunctuated_segments == ["ABC"]
    assert orch.text.segment_labels == ["seg1"]
    assert orch.text.punctuated_segments == ["A.B.C"]
    assert orch.text.is_punctuated is True
    assert len(orch.gate.punctuator.calls) == 2
    assert len(saved) == 1



def test_resume_punctuation_raises_after_max_corruption_attempts(orch, monkeypatch):
    orch.text.segments = ["ABC"]
    orch.text.page_labels = ["p1"]
    orch.text.page_lines = [1]
    orch.gate.punctuator = DummyInvoker(["XXX", "YYY"])

    module = sys.modules[orch.__class__.__module__]
    monkeypatch.setattr(module.tm, "clean", lambda text: text)
    monkeypatch.setattr(module.tm, "strip_punctuation", _letters_only)

    with pytest.raises(ValueError, match="Response corrupted original text"):
        orch.resume_punctuation()

    assert len(orch.gate.punctuator.calls) == 2



def test_resume_punctuation_applies_cross_check_correction(orch, monkeypatch):
    orch.text.segments = ["NEW"]
    orch.text.page_labels = ["p1"]
    orch.text.page_lines = [1]
    orch.text.punctuated_segments = ["OLD."]
    orch.text.unpunctuated_segments = ["OLD"]
    orch.text.segment_labels = ["seg0"]
    orch.gate.settings["punctuation"]["cross_check"]["enabled"] = True
    orch.gate.punctuator = DummyInvoker(["N.E.W"])
    orch.gate.punctuation_examinator = DummyInvoker([True])
    orch.gate.punctuation_corrector = DummyInvoker(["N,E,W"])

    module = sys.modules[orch.__class__.__module__]
    monkeypatch.setattr(module.tm, "clean", lambda text: text)
    monkeypatch.setattr(module.tm, "strip_punctuation", _letters_only)
    monkeypatch.setattr(module.tm, "segmentate", lambda _text: (["N.E.W"], ""))
    monkeypatch.setattr(module.tm, "chop_from_working_segment", lambda x, working_text, working_labels: ("NEW", "", "seg1", []))
    monkeypatch.setattr(orch, "save_as_pickle", lambda filename=None: None)

    orch.resume_punctuation()

    assert orch.text.punctuated_segments == ["OLD.", "N,E,W"]
    assert orch.text.unpunctuated_segments == ["OLD", "NEW"]
    assert orch.text.segment_labels == ["seg0", "seg1"]
    assert len(orch.gate.punctuation_examinator.calls) == 1
    assert len(orch.gate.punctuation_corrector.calls) == 1



def test_resume_punctuation_raises_when_working_text_exceeds_cap(orch, monkeypatch):
    orch.text.segments = ["TOOLONG"]
    orch.text.page_labels = ["p1"]
    orch.text.page_lines = [1]
    orch.gate.settings["punctuation"]["max_unsegmented_span"] = 3

    module = sys.modules[orch.__class__.__module__]
    monkeypatch.setattr(module.tm, "clean", lambda text: text)

    with pytest.raises(ValueError, match="Reached maximum unsegmented text span"):
        orch.resume_punctuation()



def test_resume_punctuation_appends_leftover_and_marks_text_punctuated(orch, monkeypatch):
    orch.text.segments = ["ABC"]
    orch.text.page_labels = ["p1"]
    orch.text.page_lines = [1]
    orch.gate.punctuator = DummyInvoker(["A.B.C"])

    module = sys.modules[orch.__class__.__module__]
    monkeypatch.setattr(module.tm, "clean", lambda text: text)
    monkeypatch.setattr(module.tm, "strip_punctuation", _letters_only)
    monkeypatch.setattr(module.tm, "segmentate", lambda _text: ([], "A.B.C"))
    monkeypatch.setattr(module.tm, "chop_from_working_segment", lambda x, working_text, working_labels: ("ABC", "", "seg1", []))
    monkeypatch.setattr(orch, "save_as_pickle", lambda filename=None: None)

    orch.resume_punctuation()

    assert orch.text.punctuated_segments == ["A.B.C"]
    assert orch.text.unpunctuated_segments == ["ABC"]
    assert orch.text.segment_labels == ["seg1"]
    assert orch.text.is_punctuated is True
