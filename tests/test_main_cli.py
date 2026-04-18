import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
MAIN_PATH = DATA_DIR / "__main__.py"


@pytest.fixture(scope="session")
def main_module():
    try:
        return importlib.import_module("yiding.__main__")
    except Exception:
        package_name = "_main_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        commands_mod = types.ModuleType(f"{package_name}.commands")
        # minimal placeholders so import succeeds
        commands_mod.translate = lambda *a, **k: None
        commands_mod.translate_bulk = lambda *a, **k: None
        commands_mod.continue_translating = lambda *a, **k: None
        commands_mod.translate_anew = lambda *a, **k: None
        commands_mod.punctuate = lambda *a, **k: None
        commands_mod.punctuate_bulk = lambda *a, **k: None
        commands_mod.continue_punctuating = lambda *a, **k: None
        commands_mod.get_settings = lambda *a, **k: None
        commands_mod.export = lambda *a, **k: None
        commands_mod.export_log = lambda *a, **k: None
        commands_mod.update_glossary = lambda *a, **k: None
        sys.modules[f"{package_name}.commands"] = commands_mod

        spec = importlib.util.spec_from_file_location(f"{package_name}.__main__", MAIN_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


def make_recorder(return_exc=None):
    calls = []

    def _fn(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        if isinstance(return_exc, BaseException):
            raise return_exc

    _fn.calls = calls
    return _fn


# ------------------------------
# parser behavior
# ------------------------------


def test_build_parser_translate_defaults(main_module):
    parser = main_module.build_parser()

    args = parser.parse_args(["translate", "KR5h0008"])

    assert args.command == "translate"
    assert args._handler == "translate"
    assert args.kanripo_code == "KR5h0008"
    assert args.settings is None
    assert args.translated_title is None
    assert args.output_file == "docx"
    assert args.table is True
    assert args.punctuation is True



def test_build_parser_translate_boolean_flags_flip_off(main_module):
    parser = main_module.build_parser()

    args = parser.parse_args([
        "translate",
        "KR5h0008",
        "--no-table",
        "--no-punctuation",
    ])

    assert args.table is False
    assert args.punctuation is False



def test_build_parser_export_defaults_and_enable_flags(main_module):
    parser = main_module.build_parser()

    defaults = parser.parse_args(["export", "state.pkl"])
    enabled = parser.parse_args([
        "export",
        "state.pkl",
        "--table",
        "--punctuation",
        "--translation",
        "-o",
        "txt",
    ])

    assert defaults.table is False
    assert defaults.punctuation is False
    assert defaults.translation is False
    assert defaults.output_file == "docx"

    assert enabled.table is True
    assert enabled.punctuation is True
    assert enabled.translation is True
    assert enabled.output_file == "txt"


# ------------------------------
# main dispatch
# ------------------------------


def test_main_dispatches_translate_and_returns_zero(main_module, monkeypatch):
    rec = make_recorder()
    monkeypatch.setattr(main_module.commands, "translate", rec)

    rc = main_module.main([
        "translate",
        "KR5h0008",
        "-s",
        "custom.toml",
        "--translated-title",
        "My Title",
        "-o",
        "pdf",
        "--no-table",
        "--no-punctuation",
    ])

    assert rc == 0
    assert rec.calls == [{
        "args": ("KR5h0008",),
        "kwargs": {
            "settings": "custom.toml",
            "translated_title": "My Title",
            "output_file": "pdf",
            "table": False,
            "punctuation": False,
        },
    }]



def test_main_translate_bulk_converts_empty_translated_titles_to_none(main_module, monkeypatch):
    rec = make_recorder()
    monkeypatch.setattr(main_module.commands, "translate_bulk", rec)

    rc = main_module.main([
        "translate-bulk",
        "KR1",
        "KR2",
        "--translated-titles",
    ])

    assert rc == 0
    assert rec.calls == [{
        "args": (["KR1", "KR2"],),
        "kwargs": {
            "settings": None,
            "translated_titles": None,
            "output_file": "docx",
            "table": True,
            "punctuation": True,
        },
    }]



def test_main_translate_bulk_rejects_mismatched_translated_titles(main_module, capsys):
    rc = main_module.main([
        "translate-bulk",
        "KR1",
        "KR2",
        "--translated-titles",
        "Only One",
    ])

    assert rc == 1
    err = capsys.readouterr().err
    assert "--translated-titles count must match number of kanripo_codes" in err
    assert "1 != 2" in err



def test_main_dispatches_continue_translating(main_module, monkeypatch):
    rec = make_recorder()
    monkeypatch.setattr(main_module.commands, "continue_translating", rec)

    rc = main_module.main([
        "continue-translating",
        "state.pkl",
        "-o",
        "txt",
        "--no-table",
        "--no-punctuation",
    ])

    assert rc == 0
    assert rec.calls == [{
        "args": ("state.pkl",),
        "kwargs": {
            "output_file": "txt",
            "table": False,
            "punctuation": False,
        },
    }]



def test_main_dispatches_translate_anew(main_module, monkeypatch):
    rec = make_recorder()
    monkeypatch.setattr(main_module.commands, "translate_anew", rec)

    rc = main_module.main([
        "translate-anew",
        "state.pkl",
        "-s",
        "custom.toml",
        "--translated-title",
        "Fresh Title",
        "--no-punctuation",
    ])

    assert rc == 0
    assert rec.calls == [{
        "args": ("state.pkl",),
        "kwargs": {
            "settings": "custom.toml",
            "translated_title": "Fresh Title",
            "output_file": "docx",
            "table": True,
            "punctuation": False,
        },
    }]



def test_main_dispatches_punctuate_and_punctuate_bulk(main_module, monkeypatch):
    rec_single = make_recorder()
    rec_bulk = make_recorder()
    monkeypatch.setattr(main_module.commands, "punctuate", rec_single)
    monkeypatch.setattr(main_module.commands, "punctuate_bulk", rec_bulk)

    rc1 = main_module.main(["punctuate", "KR5a0001", "-s", "settings.toml", "-o", "docx"])
    rc2 = main_module.main(["punctuate-bulk", "KR1", "KR2", "-s", "s.toml", "-o", "txt"])

    assert rc1 == 0
    assert rc2 == 0
    assert rec_single.calls == [{
        "args": ("KR5a0001",),
        "kwargs": {"settings": "settings.toml", "output_file": "docx"},
    }]
    assert rec_bulk.calls == [{
        "args": (["KR1", "KR2"],),
        "kwargs": {"settings": "s.toml", "output_file": "txt"},
    }]



def test_main_dispatches_export_related_commands(main_module, monkeypatch):
    rec_export = make_recorder()
    rec_log = make_recorder()
    rec_gloss = make_recorder()
    monkeypatch.setattr(main_module.commands, "export", rec_export)
    monkeypatch.setattr(main_module.commands, "export_log", rec_log)
    monkeypatch.setattr(main_module.commands, "update_glossary", rec_gloss)

    rc1 = main_module.main(["export", "state.pkl", "--table", "--punctuation", "-o", "txt"])
    rc2 = main_module.main(["export-log", "state.pkl"])
    rc3 = main_module.main(["update-glossary", "base.csv", "state.pkl", "-o", "out.csv"])

    assert rc1 == 0
    assert rc2 == 0
    assert rc3 == 0
    assert rec_export.calls == [{
        "args": ("state.pkl",),
        "kwargs": {"punctuation": True, "translation": False, "output_file": "txt", "table": True},
    }]
    assert rec_log.calls == [{"args": ("state.pkl",), "kwargs": {}}]
    assert rec_gloss.calls == [{
        "args": ("base.csv", "state.pkl"),
        "kwargs": {"output_file": "out.csv"},
    }]



def test_main_dispatches_get_settings(main_module, monkeypatch):
    rec = make_recorder()
    monkeypatch.setattr(main_module.commands, "get_settings", rec)

    rc = main_module.main(["get-settings"])

    assert rc == 0
    assert rec.calls == [{"args": (), "kwargs": {}}]


# ------------------------------
# error handling
# ------------------------------


def test_main_returns_130_on_keyboard_interrupt(main_module, monkeypatch):
    monkeypatch.setattr(main_module.commands, "translate", make_recorder(return_exc=KeyboardInterrupt()))

    rc = main_module.main(["translate", "KR5h0008"])

    assert rc == 130



def test_main_returns_1_and_prints_stderr_on_generic_exception(main_module, monkeypatch, capsys):
    monkeypatch.setattr(main_module.commands, "translate", make_recorder(return_exc=RuntimeError("boom")))

    rc = main_module.main(["translate", "KR5h0008"])

    assert rc == 1
    assert capsys.readouterr().err.strip() == "boom"
