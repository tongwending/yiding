"""Offline pytest coverage for the revised WorkflowOrchestrator.
"""
import importlib
import importlib.util
import os
from pathlib import Path
import re
import sys
import types
from unittest.mock import Mock

import pytest


class DummyInvoker:
    def __init__(self, responses=None, instructions="SYS:"):
        self.responses = list(responses or [])
        self.instructions = instructions
        self.calls = []

    def invoke(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if not self.responses:
            raise AssertionError("Unexpected external invoker call")
        result = self.responses[0] if len(self.responses) == 1 else self.responses.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result(*args, **kwargs) if callable(result) else result


class DummyText:
    def __init__(self):
        self.settings = {}
        self.log = ""
        self.translation_glossary = {}
        self.new_glossary = {}
        self.extracted_terms = {}
        self.extracted_glossary = {}
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
        self.is_structured = False
        self.is_translated = False
        self.is_term_extracted = False
        self.is_glossary_extracted = False
        self.translation_i = 0
        self.term_extraction_i = 0
        self.glossary_extraction_i = 0
        self.translated_segments = []
        self.original_title = ""
        self.translated_title = ""
        self.translation_language = None
        self.yiding_runs = []
        self.yiding_provenance = {
            "punctuated_segment_run_ids": [],
            "translated_segment_run_ids": [],
        }
        self._update_log = Mock()

    def full_title(self):
        return self.original_title or "untitled"


class DummyGate:
    def __init__(self):
        self.log = "Mock gateway"
        self.glossary_selector = None
        self.glossary_extractor = DummyInvoker([""])
        self.punctuator = DummyInvoker()
        self.punctuation_examinator = DummyInvoker([False])
        self.punctuation_corrector = DummyInvoker()
        self.translator = DummyInvoker()
        self.translation_examinator = DummyInvoker([False])
        self.translation_corrector = DummyInvoker()
        self.mono_glossary_selector = DummyInvoker()
        self.mono_glossary_extractor = DummyInvoker()


@pytest.fixture
def settings():
    return {
        "translation": {
            "glossary": None, "language": "English", "translation_span": 2,
            "cross_check": {"enabled": False},
        },
        "punctuation": {
            "facsimile_span": 1, "max_unsegmented_span": 1000,
            "punctuation_span": 1, "max_punctuation_attempts": 2,
            "cross_check": {"enabled": False},
        },
        "term_extraction": {"span": 2},
        "glossary_extraction": {"span": 2},
    }


@pytest.fixture(scope="session")
def wf_module():
    standalone_path = os.environ.get("WORKFLOW_ORCHESTRATOR_PATH")
    if not standalone_path:
        return importlib.import_module("yiding.workflow_orchestrator")

    # For testing the single supplied file without installing the entire app.
    package_name = "_workflow_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(Path(standalone_path).parent)]
    sys.modules[package_name] = package

    segmented = types.ModuleType(f"{package_name}.segmented_text")
    segmented.SegmentedText = DummyText
    sys.modules[segmented.__name__] = segmented

    gateway = types.ModuleType(f"{package_name}.prompt_gateway")
    gateway.PromptGateway = DummyGate
    sys.modules[gateway.__name__] = gateway

    glossary = types.ModuleType(f"{package_name}.glossary_dictate")
    glossary.load_glossary = lambda path: {}
    glossary.stylize_glossary = lambda d: str(d)
    glossary.destylize_glossary = lambda s: {}
    glossary.destylize_terms = lambda s: {}
    glossary.differentiate_glossaries = lambda new, old: {k: v for k, v in new.items() if k not in old}
    glossary.update_glossary = lambda target, source: target.update(source)
    sys.modules[glossary.__name__] = glossary

    manipulators = types.ModuleType(f"{package_name}.text_manipulators")
    manipulators.find_possible_terms = lambda s: []
    manipulators.clean = lambda s: s
    manipulators.strip_punctuation = lambda s: re.sub(r"[^\w]", "", s)
    manipulators.segmentate = lambda s: ([s], "")
    manipulators.chop_from_working_segment = lambda s, text, labels: (text, "", "seg1", [])
    manipulators.strip_invalid_characters = lambda s: s
    sys.modules[manipulators.__name__] = manipulators

    io = types.ModuleType(f"{package_name}.yiding_file_io")
    io.autosave_project = Mock(return_value=Path("mock-project.yiding"))
    io.create_run = lambda operation, settings, run_id: {
        "id": run_id, "operation": operation, "status": "in_progress"}
    io.finish_run = lambda run: run.update(status="completed")
    sys.modules[io.__name__] = io

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.workflow_orchestrator", standalone_path)
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
def orch(wf_module, text, settings, gate, monkeypatch):
    # PromptGateway is created in the resume_* methods, not in __init__.
    monkeypatch.setattr(wf_module, "PromptGateway", Mock(return_value=gate))
    monkeypatch.setattr(wf_module, "load_glossary", Mock(return_value={}))
    monkeypatch.setattr(wf_module, "autosave_project", Mock(return_value=Path("test.yiding")))
    monkeypatch.setattr(wf_module, "create_run", lambda op, st, rid: {
        "id": rid, "operation": op, "status": "in_progress"})
    monkeypatch.setattr(wf_module, "finish_run", lambda run: run.update(status="completed"))
    return wf_module.WorkflowOrchestrator(text, settings)


def test_init_sets_up_empty_runs_and_provenance(orch):
    assert orch.gate is None
    assert orch.runs == []
    assert orch.active_runs == {}
    assert orch.provenance["translated_segment_run_ids"] == []


def test_init_restores_in_progress_run(wf_module, text, settings):
    text.yiding_runs = [{"id": "saved-1", "operation": "translation", "status": "in_progress"}]
    instance = wf_module.WorkflowOrchestrator(text, settings)
    assert instance.active_runs == {"translation": "saved-1"}
    assert instance._start_run("translation") == "saved-1"
    assert len(instance.runs) == 1


def test_start_finish_run(orch):
    rid = orch._start_run("translation")
    assert rid.startswith("translation-")
    assert orch._start_run("translation") == rid
    assert len(orch.runs) == 1
    orch._finish_run("translation")
    assert orch.runs[0]["status"] == "completed"
    assert "translation" not in orch.active_runs
    orch._finish_run("translation")  # idempotent


def test_emit_progress_with_segment(orch):
    callback = Mock()
    orch.progress_callback = callback
    orch._emit_progress("translation", 1, 2, segment=4)
    callback.assert_called_once_with({"phase": "translation", "current": 1, "total": 2, "segment": 4})


def test_cancelled(orch, wf_module):
    orch.cancel_check = lambda: True
    with pytest.raises(wf_module.TransformCancelled):
        orch._check_for_cancellation()


def test_save_as_yiding_builds_checkpoint(orch, wf_module):
    saved = []
    orch.checkpoint_callback = lambda: saved.append("called")
    orch.text.working_i = 3
    orch._start_run("punctuation")
    result = orch.save_as_yiding(filename="sample.yiding", operation="punctuation")
    assert result == Path("test.yiding")
    args, kwargs = wf_module.autosave_project.call_args
    assert args[0] == "sample.yiding"
    assert kwargs["workflow"]["working_i"] == 3
    assert kwargs["workflow"]["active_run_id"] == orch.active_runs["punctuation"]
    assert kwargs["provenance"] is orch.provenance
    assert saved == ["called"]


def test_save_checks_cancellation_before_writing(orch, wf_module):
    orch.cancel_check = lambda: True
    with pytest.raises(wf_module.TransformCancelled):
        orch.save_as_yiding()
    wf_module.autosave_project.assert_not_called()


def test_select_glossary_with_selector(orch, gate, wf_module, monkeypatch):
    orch.gate = gate
    orch.glossary = {"道": "Way", "德": "Virtue"}
    gate.glossary_selector = DummyInvoker(["道\n無"])
    monkeypatch.setattr(wf_module, "stylize_glossary", lambda d: f"STYLED:{d}")
    assert orch.select_glossary("道可道") == "STYLED:{'道': 'Way'}"
    assert gate.glossary_selector.calls[0][0][0] == "Chinese segment:\n道可道"


def test_select_glossary_without_selector(orch, gate, wf_module, monkeypatch):
    orch.gate = gate
    orch.glossary = {"空": "Emptiness"}
    monkeypatch.setattr(wf_module.tm, "find_possible_terms", lambda s: ["道", "空"])
    monkeypatch.setattr(wf_module, "stylize_glossary", lambda d: d)
    assert orch.select_glossary("色即是空") == {"空": "Emptiness"}


def test_extract_glossary_updates_three_dictionaries(orch, gate, wf_module, monkeypatch):
    orch.gate = gate
    orch.glossary = {}
    gate.glossary_extractor = DummyInvoker(["道: Way"])
    monkeypatch.setattr(wf_module, "destylize_glossary", lambda s: {"道": "Way"})
    orch.extract_glossary("道", "Way")
    assert orch.glossary == {"道": "Way"}
    assert orch.text.translation_glossary == {"道": "Way"}
    assert orch.text.new_glossary == {"道": "Way"}


def prepare_translation(orch, monkeypatch, segments, responses):
    orch.text.is_punctuated = True
    orch.text.punctuated_segments = segments
    orch.text.segment_labels = [f"s{i}" for i in range(len(segments))]
    orch.gate = None
    # This test deliberately isolates glossary selection/extraction.
    monkeypatch.setattr(orch, "select_glossary", lambda segment: "")
    monkeypatch.setattr(orch, "extract_glossary", Mock())
    monkeypatch.setattr(orch, "save_as_yiding", Mock())
    return responses


def test_resume_translation_two_segments(orch, gate, monkeypatch):
    prepare_translation(orch, monkeypatch, ["甲。", "乙。"], None)
    gate.translator = DummyInvoker([" one ", " two "])
    orch.resume_translation()
    assert orch.text.translated_segments == ["one", "two"]
    assert orch.text.translation_i == 2
    assert orch.text.is_translated
    assert orch.text.translation_language == "English"
    assert len(orch.provenance["translated_segment_run_ids"]) == 2
    second_prompt = gate.translator.calls[1][0][0]
    assert "Preceding text:\n甲。" in second_prompt
    assert "Preceding translation:\none" in second_prompt
    assert "Text to be translated:\n乙。" in second_prompt
    assert [c.kwargs["status"] for c in orch.save_as_yiding.call_args_list] == ["in_progress", "completed"]


def test_resume_translation_skips_completed_segments(orch, gate, monkeypatch):
    prepare_translation(orch, monkeypatch, ["甲。", "乙。"], None)
    orch.text.translation_i = 1
    orch.text.translated_segments = ["one"]
    orch.provenance["translated_segment_run_ids"] = ["previous-run"]
    gate.translator = DummyInvoker(["two"])
    orch.resume_translation()
    assert len(gate.translator.calls) == 1
    assert "Text to be translated:\n乙。" in gate.translator.calls[0][0][0]
    assert orch.text.translated_segments == ["one", "two"]
    assert orch.provenance["translated_segment_run_ids"][0] == "previous-run"


def test_resume_translation_cross_check_correction(orch, gate, monkeypatch, settings):
    prepare_translation(orch, monkeypatch, ["甲。", "乙。"], None)
    settings["translation"]["cross_check"]["enabled"] = True
    gate.translator = DummyInvoker(["first", "incorrect"])
    gate.translation_examinator = DummyInvoker([True])
    gate.translation_corrector = DummyInvoker([" corrected "])
    orch.resume_translation()
    assert orch.text.translated_segments == ["first", "corrected"]
    assert len(gate.translation_corrector.calls) == 1


def test_resume_translation_auto_punctuates(orch, gate, monkeypatch):
    call = Mock(side_effect=lambda: setattr(orch.text, "is_punctuated", True))
    monkeypatch.setattr(orch, "resume_punctuation", call)
    orch.resume_translation()
    call.assert_called_once_with()


def test_translate_title(orch, gate, monkeypatch):
    orch.gate = gate
    orch.text.original_title = "道德經"
    orch.glossary = {}
    gate.translator = DummyInvoker([" Dao De Jing "])
    monkeypatch.setattr(orch, "select_glossary", lambda x: "GLOSSARY")
    monkeypatch.setattr(orch, "extract_glossary", Mock())
    monkeypatch.setattr(orch, "save_as_yiding", Mock())
    orch.translate_title()
    assert orch.text.translated_title == "Dao De Jing"
    assert gate.translator.calls[0][1]["instructions"] == "SYS:GLOSSARY"
    orch.save_as_yiding.assert_called_once_with(operation="translation", status="in_progress")


def prepare_punctuation(orch, monkeypatch, responses):
    orch.text.segments = ["ABC"]
    orch.text.page_labels = ["p1"]
    orch.text.page_lines = [1]
    orch.gate = None
    monkeypatch.setattr(orch, "save_as_yiding", Mock())
    orch._test_punctuator = responses


def test_punctuation_retries_corruption_then_completes(orch, gate, monkeypatch, wf_module):
    prepare_punctuation(orch, monkeypatch, None)
    gate.punctuator = DummyInvoker(["XXX", "A.B.C"])
    monkeypatch.setattr(wf_module.tm, "strip_punctuation", lambda s: re.sub(r"[^A-Z]", "", s))
    monkeypatch.setattr(wf_module.tm, "segmentate", lambda s: ([s], ""))
    orch.resume_punctuation()
    assert orch.text.punctuated_segments == ["A.B.C"]
    assert orch.text.is_punctuated is True
    assert orch.text.is_structured is True
    assert len(gate.punctuator.calls) == 2
    assert len(orch.provenance["punctuated_segment_run_ids"]) == 1
    orch.save_as_yiding.assert_called_once_with(operation="punctuation", status="completed")


def test_punctuation_rejects_corrupted_responses(orch, gate, monkeypatch, wf_module):
    prepare_punctuation(orch, monkeypatch, None)
    gate.punctuator = DummyInvoker(["XXX", "YYY"])
    monkeypatch.setattr(wf_module.tm, "strip_punctuation", lambda s: re.sub(r"[^A-Z]", "", s))
    with pytest.raises(ValueError, match="Response corrupted original text"):
        orch.resume_punctuation()
    assert len(gate.punctuator.calls) == 2


def test_punctuation_rejects_unsegmented_text_over_limit(orch, monkeypatch, settings):
    prepare_punctuation(orch, monkeypatch, None)
    settings["punctuation"]["max_unsegmented_span"] = 2
    with pytest.raises(ValueError, match="Reached maximum unsegmented text span"):
        orch.resume_punctuation()


def test_punctuation_cross_check_corrects(orch, gate, monkeypatch, settings, wf_module):
    prepare_punctuation(orch, monkeypatch, None)
    orch.text.punctuated_segments = ["OLD."]
    orch.text.unpunctuated_segments = ["OLD"]
    orch.text.segment_labels = ["s0"]
    orch.provenance["punctuated_segment_run_ids"] = ["old-run"]
    settings["punctuation"]["cross_check"]["enabled"] = True
    gate.punctuator = DummyInvoker(["A.B.C"])
    gate.punctuation_examinator = DummyInvoker([True])
    gate.punctuation_corrector = DummyInvoker(["A,B,C"])
    monkeypatch.setattr(wf_module.tm, "strip_punctuation", lambda s: re.sub(r"[^A-Z]", "", s))
    orch.resume_punctuation()
    assert orch.text.punctuated_segments == ["OLD.", "A,B,C"]
    assert len(gate.punctuation_corrector.calls) == 1


def test_punctuation_filters_empty_segments(orch, gate, monkeypatch, wf_module):
    prepare_punctuation(orch, monkeypatch, None)
    gate.punctuator = DummyInvoker(["A.B.C"])
    monkeypatch.setattr(wf_module.tm, "strip_punctuation", lambda s: re.sub(r"[^A-Z]", "", s))
    monkeypatch.setattr(wf_module.tm, "segmentate", lambda s: (["", " ", "A.B.C"], ""))
    orch.resume_punctuation()
    assert orch.text.punctuated_segments == ["A.B.C"]


def test_term_extraction_batches_and_resumes(orch, gate, monkeypatch, wf_module):
    orch.text.punctuated_segments = ["甲", "乙", "丙"]
    gate.mono_glossary_selector = DummyInvoker(["first", "last"])
    monkeypatch.setattr(wf_module, "destylize_terms", lambda s: {s: "term"})
    monkeypatch.setattr(orch, "save_as_yiding", Mock())
    orch.resume_term_extraction()
    assert orch.text.term_extraction_i == 3
    assert orch.text.extracted_terms == {"first": "term", "last": "term"}
    assert orch.text.is_term_extracted
    assert len(gate.mono_glossary_selector.calls) == 2
    assert [c.kwargs["status"] for c in orch.save_as_yiding.call_args_list] == ["in_progress", "completed"]


def test_glossary_extraction_batches_and_completes(orch, gate, monkeypatch, wf_module):
    orch.text.punctuated_segments = ["甲", "乙", "丙"]
    orch.text.translated_segments = ["one", "two", "three"]
    orch.text.translation_language = "English"
    gate.mono_glossary_extractor = DummyInvoker(["first", "last"])
    monkeypatch.setattr(wf_module, "destylize_glossary", lambda s: {s: "entry"})
    monkeypatch.setattr(orch, "save_as_yiding", Mock())
    orch.resume_glossary_extraction()
    assert orch.text.glossary_extraction_i == 3
    assert orch.text.extracted_glossary == {"first": "entry", "last": "entry"}
    assert orch.text.is_glossary_extracted
    assert "English translation:" in gate.mono_glossary_extractor.calls[0][0][0]
