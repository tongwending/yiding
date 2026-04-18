import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
PROMPT_GATEWAY_PATH = DATA_DIR / "prompt_gateway.py"


class FakeGPTInvoker:
    def __init__(self, client, instructions, model, reasoning, verbosity, temperature, top_p, boolean_response):
        self.client = client
        self.instructions = instructions
        self.model = model
        self.reasoning = reasoning
        self.verbosity = verbosity
        self.temperature = temperature
        self.top_p = top_p
        self.boolean_response = boolean_response
        self.bound_clients = []

    def bind_client(self, client):
        self.bound_clients.append(client)
        self.client = client


class FakeGeminiInvoker(FakeGPTInvoker):
    pass


class FakeOpenAI:
    def __init__(self, api_key):
        self.api_key = api_key


class FakeGoogleClient:
    def __init__(self, api_key):
        self.api_key = api_key


@pytest.fixture(scope="session")
def pg_module():
    """
    Prefer the real package import if available. Otherwise load the uploaded file
    into a fake package so its relative imports succeed.
    """
    try:
        return importlib.import_module("yiding.prompt_gateway")
    except Exception:
        package_name = "_pg_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        instructors_mod = types.ModuleType(f"{package_name}.instructors")
        sys.modules[f"{package_name}.instructors"] = instructors_mod

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.prompt_gateway",
            PROMPT_GATEWAY_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


@pytest.fixture
def patched_backend_modules(pg_module, monkeypatch):
    """Patch dynamic imports used inside create_invoker/create_client."""
    gpt_mod = types.ModuleType("gpt_invoker")
    gpt_mod.GPT_Invoker = FakeGPTInvoker
    gem_mod = types.ModuleType("gemini_invoker")
    gem_mod.Gemini_Invoker = FakeGeminiInvoker
    openai_mod = types.ModuleType("openai")
    openai_mod.OpenAI = FakeOpenAI
    google_genai_mod = types.ModuleType("google.genai")
    google_genai_mod.Client = FakeGoogleClient

    monkeypatch.setitem(sys.modules, f"{pg_module.__package__}.gpt_invoker", gpt_mod)
    monkeypatch.setitem(sys.modules, f"{pg_module.__package__}.gemini_invoker", gem_mod)
    monkeypatch.setitem(sys.modules, "openai", openai_mod)
    monkeypatch.setitem(sys.modules, "google.genai", google_genai_mod)


@pytest.fixture
def sample_settings():
    return {
        "api_serial_keys": {"openai": "OPENAI-KEY", "google": "GOOGLE-KEY"},
        "punctuation": {
            "enabled": True,
            "cross_check": {"enabled": False},
            "punctuation": {"model": "gpt-4o", "reasoning": False, "verbosity": False, "temperature": False, "top_p": False},
            "cross_examination": {"model": "gpt-4o", "reasoning": "medium", "verbosity": False, "temperature": False, "top_p": False},
            "cross_correction": {"model": "gpt-4o", "reasoning": False, "verbosity": "low", "temperature": False, "top_p": False},
        },
        "translation": {
            "enabled": True,
            "llm_glossary_selection": {"enabled": False},
            "cross_check": {"enabled": False},
            "glossary_selection": {"model": "gpt-4o", "reasoning": False, "verbosity": False, "temperature": False, "top_p": False},
            "translation": {"model": "gpt-4o", "reasoning": "high", "verbosity": "low", "temperature": 0.4, "top_p": 0.8},
            "cross_examination": {"model": "gpt-4o", "reasoning": "medium", "verbosity": False, "temperature": False, "top_p": False},
            "cross_correction": {"model": "gpt-4o", "reasoning": False, "verbosity": "low", "temperature": False, "top_p": False},
            "glossary_extraction": {"model": "gpt-4o", "reasoning": False, "verbosity": False, "temperature": False, "top_p": False},
        },
    }


@pytest.fixture
def patched_instructors(pg_module, monkeypatch):
    monkeypatch.setattr(pg_module.instructors, "instruct_punctuation", lambda settings: f"PUNC:{settings['punctuation']['punctuation']['model']}", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_punctuation_examination", lambda: "PUNC-EXAM", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_punctuation_correction", lambda settings: f"PUNC-CORR:{settings['punctuation']['cross_correction']['model']}", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_glossary_selection", lambda settings: f"GLOSS-SELECT:{settings['translation']['glossary_selection']['model']}", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_translation", lambda settings: f"TRANSLATE:{settings['translation']['translation']['model']}", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_translation_examination", lambda settings: f"TRANS-EXAM:{settings['translation']['cross_examination']['model']}", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_translation_correction", lambda settings: f"TRANS-CORR:{settings['translation']['cross_correction']['model']}", raising=False)
    monkeypatch.setattr(pg_module.instructors, "instruct_glossary_extraction", lambda settings: f"GLOSS-EXTRACT:{settings['translation']['glossary_extraction']['model']}", raising=False)


# ------------------------------
# create_client
# ------------------------------


def test_create_client_openai_uses_direct_key_and_caches_client(pg_module, patched_backend_modules, sample_settings):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    client1 = gateway.create_client("gpt-4o")
    client2 = gateway.create_client("gpt-4o")

    assert isinstance(client1, FakeOpenAI)
    assert client1.api_key == "OPENAI-KEY"
    assert client1 is client2



def test_create_client_openai_reads_key_from_text_file(pg_module, patched_backend_modules, sample_settings, tmp_path):
    keyfile = tmp_path / "openai_key.txt"
    keyfile.write_text("  TXT-KEY  ", encoding="utf-8")
    sample_settings["api_serial_keys"]["openai"] = str(keyfile)

    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    client = gateway.create_client("o4-mini")

    assert isinstance(client, FakeOpenAI)
    assert client.api_key == "TXT-KEY"



def test_create_client_raises_when_openai_key_file_is_empty(pg_module, patched_backend_modules, sample_settings, tmp_path):
    keyfile = tmp_path / "openai_key.txt"
    keyfile.write_text("   ", encoding="utf-8")
    sample_settings["api_serial_keys"]["openai"] = str(keyfile)

    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    with pytest.raises(ValueError, match=pg_module.NO_API_KEY_ERROR):
        gateway.create_client("gpt-4o")



def test_create_client_gemini_uses_direct_key_and_caches_client(pg_module, patched_backend_modules, sample_settings):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    client1 = gateway.create_client("gemini-2.5-pro")
    client2 = gateway.create_client("gemini-2.5-pro")

    assert isinstance(client1, FakeGoogleClient)
    assert client1.api_key == "GOOGLE-KEY"
    assert client1 is client2



def test_create_client_raises_for_unknown_model(pg_module, sample_settings):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    with pytest.raises(ValueError, match="Unknown model in settings"):
        gateway.create_client("llama-3")


# ------------------------------
# create_invoker
# ------------------------------


def test_create_invoker_builds_gpt_invoker_and_normalizes_false_values(pg_module, patched_backend_modules, sample_settings, monkeypatch):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    create_client_calls = []
    monkeypatch.setattr(gateway, "create_client", lambda model: create_client_calls.append(model) or f"CLIENT:{model}")

    spec = {"model": "gpt-4o", "reasoning": False, "verbosity": False, "temperature": False, "top_p": False}
    inv = gateway.create_invoker(spec, "INSTR", boolean_response=True)

    assert isinstance(inv, FakeGPTInvoker)
    assert create_client_calls == ["gpt-4o"]
    assert inv.client == "CLIENT:gpt-4o"
    assert inv.instructions == "INSTR"
    assert inv.model == "gpt-4o"
    assert inv.reasoning is None
    assert inv.verbosity is None
    assert inv.temperature is None
    assert inv.top_p is None
    assert inv.boolean_response is True



def test_create_invoker_builds_gemini_invoker(pg_module, patched_backend_modules, sample_settings, monkeypatch):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    monkeypatch.setattr(gateway, "create_client", lambda model: f"CLIENT:{model}")
    spec = {"model": "gemini-2.5-flash", "reasoning": "high", "verbosity": "low", "temperature": 0.2, "top_p": 0.7}

    inv = gateway.create_invoker(spec, "INSTR")

    assert isinstance(inv, FakeGeminiInvoker)
    assert inv.client == "CLIENT:gemini-2.5-flash"
    assert inv.reasoning == "high"
    assert inv.verbosity == "low"
    assert inv.temperature == 0.2
    assert inv.top_p == 0.7
    assert inv.boolean_response is False



def test_create_invoker_raises_for_unknown_model(pg_module, sample_settings):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    gateway.settings = sample_settings
    gateway.openai_client = None
    gateway.google_client = None

    bad = {"model": "claude-3", "reasoning": False, "verbosity": False, "temperature": False, "top_p": False}
    with pytest.raises(ValueError, match="Unknown LLM model"):
        gateway.create_invoker(bad, "INSTR")


# ------------------------------
# __init__ wiring and logging
# ------------------------------


def test_init_without_cross_checks_or_llm_selection_creates_expected_invokers(pg_module, patched_backend_modules, patched_instructors, sample_settings):
    gateway = pg_module.PromptGateway(sample_settings)

    assert isinstance(gateway.punctuator, FakeGPTInvoker)
    assert gateway.punctuation_examinator is None
    assert gateway.punctuation_corrector is None
    assert gateway.glossary_selector is None
    assert isinstance(gateway.translator, FakeGPTInvoker)
    assert gateway.translation_examinator is None
    assert gateway.translation_corrector is None
    assert isinstance(gateway.glossary_extractor, FakeGPTInvoker)
    assert len(gateway.invokers) == 3
    assert "PUNC:gpt-4o" in gateway.log
    assert "TRANSLATE:gpt-4o" in gateway.log
    assert "GLOSS-EXTRACT:gpt-4o" in gateway.log



def test_init_with_cross_checks_and_llm_selection_creates_all_invokers(pg_module, patched_backend_modules, patched_instructors, sample_settings):
    sample_settings["punctuation"]["cross_check"]["enabled"] = True
    sample_settings["translation"]["cross_check"]["enabled"] = True
    sample_settings["translation"]["llm_glossary_selection"]["enabled"] = True

    gateway = pg_module.PromptGateway(sample_settings)

    assert isinstance(gateway.punctuation_examinator, FakeGPTInvoker)
    assert gateway.punctuation_examinator.boolean_response is True
    assert isinstance(gateway.punctuation_corrector, FakeGPTInvoker)
    assert isinstance(gateway.glossary_selector, FakeGPTInvoker)
    assert isinstance(gateway.translation_examinator, FakeGPTInvoker)
    assert gateway.translation_examinator.boolean_response is True
    assert isinstance(gateway.translation_corrector, FakeGPTInvoker)
    assert len(gateway.invokers) == 8
    assert "PUNC-EXAM" in gateway.log
    assert "PUNC-CORR:gpt-4o" in gateway.log
    assert "GLOSS-SELECT:gpt-4o" in gateway.log
    assert "TRANS-EXAM:gpt-4o" in gateway.log
    assert "TRANS-CORR:gpt-4o" in gateway.log



def test_init_with_punctuation_disabled_omits_punctuation_invokers(pg_module, patched_backend_modules, patched_instructors, sample_settings):
    sample_settings["punctuation"]["enabled"] = False

    gateway = pg_module.PromptGateway(sample_settings)

    assert not hasattr(gateway, "punctuator")
    assert isinstance(gateway.translator, FakeGPTInvoker)
    assert len(gateway.invokers) == 2



def test_init_with_translation_disabled_omits_translation_invokers(pg_module, patched_backend_modules, patched_instructors, sample_settings):
    sample_settings["translation"]["enabled"] = False

    gateway = pg_module.PromptGateway(sample_settings)

    assert isinstance(gateway.punctuator, FakeGPTInvoker)
    assert not hasattr(gateway, "translator")
    assert len(gateway.invokers) == 1


# ------------------------------
# pickling helpers
# ------------------------------


def test_getstate_drops_unpicklable_clients(pg_module, patched_backend_modules, patched_instructors, sample_settings):
    gateway = pg_module.PromptGateway(sample_settings)

    state = gateway.__getstate__()

    assert "openai_client" not in state
    assert "google_client" not in state
    assert "invokers" in state
    assert state["settings"] is gateway.settings



def test_setstate_recreates_clients_and_rebinds_invokers(pg_module, patched_backend_modules, sample_settings, monkeypatch):
    gateway = pg_module.PromptGateway.__new__(pg_module.PromptGateway)

    inv1 = FakeGPTInvoker(None, "I1", "gpt-4o", None, None, None, None, False)
    inv2 = FakeGPTInvoker(None, "I2", "gpt-4o", None, None, None, None, False)
    inv3 = FakeGeminiInvoker(None, "I3", "gemini-2.5-pro", None, None, None, None, False)

    created = {}

    def fake_create_client(model):
        created.setdefault(model, f"CLIENT:{model}")
        return created[model]

    monkeypatch.setattr(gateway, "create_client", fake_create_client)

    state = {
        "settings": sample_settings,
        "invokers": [inv1, inv2, inv3],
        "log": "existing log",
    }

    gateway.__setstate__(state)

    assert gateway.openai_client is None
    assert gateway.google_client is None
    assert inv1.bound_clients == ["CLIENT:gpt-4o"]
    assert inv2.bound_clients == ["CLIENT:gpt-4o"]
    assert inv3.bound_clients == ["CLIENT:gemini-2.5-pro"]
    assert gateway.log == "existing log"
