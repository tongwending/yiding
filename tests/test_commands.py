import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
COMMANDS_PATH = DATA_DIR / "commands.py"


class DummyText:
    def __init__(self):
        self.translated_title = None
        self.translation_glossary = {"term": "value"}
        self.empty_translation_calls = []
        self.print_calls = []

    def empty_translation(self, empty_title=True):
        self.empty_translation_calls.append(empty_title)
        if empty_title:
            self.translated_title = None

    def print_to_file(self, **kwargs):
        self.print_calls.append(kwargs)


class DummyOrchestrator:
    def __init__(self, text=None, gate=None, log="ORCH-LOG"):
        self.text = text or DummyText()
        self.gate = gate
        self.log = log
        self.resume_translation_calls = 0
        self.resume_punctuation_calls = 0

    def resume_translation(self):
        self.resume_translation_calls += 1

    def resume_punctuation(self):
        self.resume_punctuation_calls += 1


class RecorderFactory:
    def __init__(self, obj):
        self.obj = obj
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        return self.obj


@pytest.fixture(scope="session")
def commands_module():
    try:
        return importlib.import_module("yiding.commands")
    except Exception:
        package_name = "_commands_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        # Minimal placeholder modules so relative imports succeed.
        kt_mod = types.ModuleType(f"{package_name}.kanripo_text")
        class PlaceholderKanripoText:  # pragma: no cover - import scaffold only
            pass
        kt_mod.KanripoText = PlaceholderKanripoText
        sys.modules[f"{package_name}.kanripo_text"] = kt_mod

        pg_mod = types.ModuleType(f"{package_name}.prompt_gateway")
        class PlaceholderPromptGateway:  # pragma: no cover - import scaffold only
            pass
        pg_mod.PromptGateway = PlaceholderPromptGateway
        sys.modules[f"{package_name}.prompt_gateway"] = pg_mod

        wo_mod = types.ModuleType(f"{package_name}.workflow_orchestrator")
        class PlaceholderWorkflowOrchestrator:  # pragma: no cover - import scaffold only
            pass
        wo_mod.WorkflowOrchestrator = PlaceholderWorkflowOrchestrator
        sys.modules[f"{package_name}.workflow_orchestrator"] = wo_mod

        gd_mod = types.ModuleType(f"{package_name}.glossary_dictate")
        gd_mod.load_glossary = lambda path: {}
        gd_mod.update_glossary = lambda base, new: None
        gd_mod.glossary_to_csv = lambda glossary, path: None
        sys.modules[f"{package_name}.glossary_dictate"] = gd_mod

        ding_mod = types.ModuleType(f"{package_name}.ding")
        ding_mod.DING = "DING!"
        sys.modules[f"{package_name}.ding"] = ding_mod

        spec = importlib.util.spec_from_file_location(f"{package_name}.commands", COMMANDS_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


@pytest.fixture
def sample_settings():
    return {
        "punctuation": {"enabled": True},
        "translation": {"enabled": True},
        "api_serial_keys": {"openai": "KEY", "google": "GKEY"},
    }



def test_translate_bulk_raises_for_mismatched_translated_titles(commands_module):
    with pytest.raises(ValueError, match="Unequal number of kanripo codes and translated titles"):
        commands_module.translate_bulk(["KR1", "KR2"], translated_titles=["One"])



def test_translate_bulk_calls_translate_for_each_code_and_prints_ding(commands_module, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(commands_module, "translate", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(commands_module.ding, "DING", "DING-SOUND", raising=False)

    commands_module.translate_bulk(
        ["KR1", "KR2"],
        settings="settings.toml",
        translated_titles=["Title 1", "Title 2"],
        output_file="docx",
        table=False,
        punctuation=False,
    )

    assert calls == [
        (("KR1",), {"settings": "settings.toml", "translated_title": "Title 1", "punctuation": False, "output_file": "docx", "table": False}),
        (("KR2",), {"settings": "settings.toml", "translated_title": "Title 2", "punctuation": False, "output_file": "docx", "table": False}),
    ]
    assert "DING-SOUND" in capsys.readouterr().out



def test_translate_loads_settings_constructs_objects_runs_translation_and_exports(commands_module, monkeypatch, sample_settings, capsys):
    text = DummyText()
    gate = object()
    orchestrator = DummyOrchestrator(text=text, gate=gate)
    text_factory = RecorderFactory(text)
    gate_factory = RecorderFactory(gate)
    orch_factory = RecorderFactory(orchestrator)

    monkeypatch.setattr(commands_module, "_load_settings", lambda filename: sample_settings)
    monkeypatch.setattr(commands_module, "KanripoText", text_factory)
    monkeypatch.setattr(commands_module, "PromptGateway", gate_factory)
    monkeypatch.setattr(commands_module, "WorkflowOrchestrator", orch_factory)
    monkeypatch.setattr(commands_module.ding, "DING", "DING-TXT", raising=False)

    commands_module.translate("KR5a0001", settings="custom.toml", translated_title="English Title", output_file="docx", table=False, punctuation=True)

    assert text_factory.calls == [{"args": ("KR5a0001",), "kwargs": {}}]
    assert gate_factory.calls == [{"args": (sample_settings,), "kwargs": {}}]
    assert orch_factory.calls == [{"args": (text, gate), "kwargs": {}}]
    assert text.translated_title == "English Title"
    assert orchestrator.resume_translation_calls == 1
    assert text.print_calls == [{"punctuation": True, "translation": True, "output_file": "docx", "table": False}]
    assert "DING-TXT" in capsys.readouterr().out



def test_continue_translating_loads_pickle_and_exports(commands_module, monkeypatch, capsys):
    orchestrator = DummyOrchestrator()
    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: orchestrator)
    monkeypatch.setattr(commands_module.ding, "DING", "DONE", raising=False)

    commands_module.continue_translating("state.pkl", output_file="txt", table=True, punctuation=False)

    assert orchestrator.resume_translation_calls == 1
    assert orchestrator.text.print_calls == [{"punctuation": False, "translation": True, "output_file": "txt", "table": True}]
    assert "DONE" in capsys.readouterr().out



def test_translate_anew_disables_punctuation_empties_translation_and_uses_new_gateway(commands_module, monkeypatch, sample_settings, capsys):
    old_text = DummyText()
    old_text.translated_title = "Old title"
    old_orchestrator = DummyOrchestrator(text=old_text)
    new_gate = object()
    new_orchestrator = DummyOrchestrator(text=old_text, gate=new_gate)

    monkeypatch.setattr(commands_module, "_load_settings", lambda filename: sample_settings)
    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: old_orchestrator)
    monkeypatch.setattr(commands_module, "PromptGateway", RecorderFactory(new_gate))
    monkeypatch.setattr(commands_module, "WorkflowOrchestrator", RecorderFactory(new_orchestrator))
    monkeypatch.setattr(commands_module.ding, "DING", "DING-ANEW", raising=False)

    commands_module.translate_anew("state.pkl", settings="custom.toml", translated_title="Fresh Title", output_file="docx", table=True, punctuation=False)

    assert sample_settings["punctuation"]["enabled"] is False
    assert old_text.empty_translation_calls == [True]
    assert old_text.translated_title == "Fresh Title"
    assert new_orchestrator.resume_translation_calls == 1
    assert old_text.print_calls == [{"punctuation": False, "translation": True, "output_file": "docx", "table": True}]
    assert "DING-ANEW" in capsys.readouterr().out



def test_punctuate_bulk_calls_punctuate_for_each_code_and_prints_ding(commands_module, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(commands_module, "punctuate", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(commands_module.ding, "DING", "BELL", raising=False)

    commands_module.punctuate_bulk(["KR1", "KR2"], settings="settings.toml", output_file="docx")

    assert calls == [
        (("KR1",), {"settings": "settings.toml", "output_file": "docx"}),
        (("KR2",), {"settings": "settings.toml", "output_file": "docx"}),
    ]
    assert "BELL" in capsys.readouterr().out



def test_punctuate_disables_translation_runs_punctuation_and_exports(commands_module, monkeypatch, sample_settings, capsys):
    text = DummyText()
    gate = object()
    orchestrator = DummyOrchestrator(text=text, gate=gate)

    monkeypatch.setattr(commands_module, "_load_settings", lambda filename: sample_settings)
    monkeypatch.setattr(commands_module, "KanripoText", RecorderFactory(text))
    monkeypatch.setattr(commands_module, "PromptGateway", RecorderFactory(gate))
    monkeypatch.setattr(commands_module, "WorkflowOrchestrator", RecorderFactory(orchestrator))
    monkeypatch.setattr(commands_module.ding, "DING", "PUNC-DING", raising=False)

    commands_module.punctuate("KR5b0002", settings="settings.toml", output_file="docx")

    assert sample_settings["translation"]["enabled"] is False
    assert orchestrator.resume_punctuation_calls == 1
    assert text.print_calls == [{"punctuation": True, "translation": False, "output_file": "docx", "table": False}]
    assert "PUNC-DING" in capsys.readouterr().out



def test_continue_punctuating_loads_pickle_and_exports(commands_module, monkeypatch, capsys):
    orchestrator = DummyOrchestrator()
    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: orchestrator)
    monkeypatch.setattr(commands_module.ding, "DING", "P-DONE", raising=False)

    commands_module.continue_punctuating("state.pkl", output_file="docx")

    assert orchestrator.resume_punctuation_calls == 1
    assert orchestrator.text.print_calls == [{"punctuation": True, "translation": False, "output_file": "docx", "table": False}]
    assert "P-DONE" in capsys.readouterr().out



def test_get_settings_copies_packaged_settings_to_cwd(commands_module, monkeypatch, tmp_path, capsys):
    module_dir = tmp_path / "module_dir"
    module_dir.mkdir()
    source = module_dir / "settings.toml"
    source.write_text("abc = 123\n", encoding="utf-8")
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    monkeypatch.setattr(commands_module, "__file__", str(module_dir / "commands.py"))
    monkeypatch.setattr(commands_module.os, "getcwd", lambda: str(workdir))

    commands_module.get_settings()

    destination = workdir / "settings.toml"
    assert destination.read_text(encoding="utf-8") == "abc = 123\n"
    assert str(destination) in capsys.readouterr().out



def test_export_loads_pickle_and_forwards_print_options(commands_module, monkeypatch):
    orchestrator = DummyOrchestrator()
    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: orchestrator)

    commands_module.export("state.pkl", punctuation=True, translation=False, output_file="docx", table=True)

    assert orchestrator.text.print_calls == [{"punctuation": True, "translation": False, "output_file": "docx", "table": True}]



def test_export_log_writes_orchestrator_log_to_suffixed_text_file(commands_module, monkeypatch, tmp_path):
    orch = DummyOrchestrator(log="LINE 1\nLINE 2")
    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: orch)

    target = tmp_path / "state.pkl"
    commands_module.export_log(str(target))

    out = tmp_path / "state_LOG.txt"
    assert out.read_text(encoding="utf-8") == "LINE 1\nLINE 2"



def test_update_glossary_merges_pickle_glossary_and_exports_to_default_path(commands_module, monkeypatch):
    orch = DummyOrchestrator()
    calls = {"load": [], "update": [], "csv": []}

    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: orch)
    monkeypatch.setattr(commands_module.glossary_dictate, "load_glossary", lambda path: calls["load"].append(path) or {"base": "A"})
    monkeypatch.setattr(commands_module.glossary_dictate, "update_glossary", lambda base, new: calls["update"].append((base.copy(), new.copy())))
    monkeypatch.setattr(commands_module.glossary_dictate, "glossary_to_csv", lambda glossary, path: calls["csv"].append((glossary, path)))

    commands_module.update_glossary("glossary.csv", "state.pkl")

    assert calls["load"] == ["glossary.csv"]
    assert calls["update"] == [({"base": "A"}, {"term": "value"})]
    assert calls["csv"] == [({"base": "A"}, "glossary.csv")]



def test_update_glossary_uses_explicit_output_file_when_provided(commands_module, monkeypatch):
    orch = DummyOrchestrator()
    exported = []

    monkeypatch.setattr(commands_module, "_load_pickle", lambda filename: orch)
    monkeypatch.setattr(commands_module.glossary_dictate, "load_glossary", lambda path: {"base": "A"})
    monkeypatch.setattr(commands_module.glossary_dictate, "update_glossary", lambda base, new: None)
    monkeypatch.setattr(commands_module.glossary_dictate, "glossary_to_csv", lambda glossary, path: exported.append(path))

    commands_module.update_glossary("glossary.csv", "state.pkl", output_file="merged.csv")

    assert exported == ["merged.csv"]



def test_load_pickle_reads_pickled_object(commands_module, tmp_path):
    import pickle

    target = tmp_path / "thing.pkl"
    payload = {"a": 1, "b": [2, 3]}
    with open(target, "wb") as f:
        pickle.dump(payload, f)

    assert commands_module._load_pickle(str(target)) == payload



def test_load_settings_reads_toml_file(commands_module, tmp_path):
    target = tmp_path / "settings.toml"
    target.write_text("[translation]\nenabled = true\n", encoding="utf-8")

    data = commands_module._load_settings(str(target))

    assert data == {"translation": {"enabled": True}}
