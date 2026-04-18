import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE
GEMINI_INVOKER_PATH = DATA_DIR / "gemini_invoker.py"


class FakeThinkingLevel:
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MINIMAL = "MINIMAL"


class FakeThinkingConfig:
    def __init__(self, thinking_level):
        self.thinking_level = thinking_level


class FakeGenerateContentConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModelsAPI:
    def __init__(self, text="TEXT"):
        self.text = text
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.text)


class FakeClient:
    def __init__(self, text="TEXT"):
        self.models = FakeModelsAPI(text=text)


@pytest.fixture(scope="session")
def gem_module():
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    types_mod = types.ModuleType("google.genai.types")
    types_mod.ThinkingLevel = FakeThinkingLevel
    types_mod.ThinkingConfig = FakeThinkingConfig
    types_mod.GenerateContentConfig = FakeGenerateContentConfig
    genai_mod.types = types_mod

    sys.modules["google"] = google_mod
    sys.modules["google.genai"] = genai_mod
    sys.modules["google.genai.types"] = types_mod

    try:
        return importlib.import_module("yiding.gemini_invoker")
    except Exception:
        package_name = "_gemini_invoker_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.gemini_invoker",
            GEMINI_INVOKER_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


def make_invoker(gem_module, client=None, **kwargs):
    client = client or FakeClient()
    params = {
        "client": client,
        "instructions": "BASE-INSTR",
        "model": "gemini-2.5-flash",
        "reasoning": None,
        "verbosity": None,
        "temperature": None,
        "top_p": None,
        "boolean_response": False,
    }
    params.update(kwargs)
    return gem_module.Gemini_Invoker(**params)


# ------------------------------
# init / reasoning mapping
# ------------------------------


def test_init_maps_reasoning_high(gem_module):
    inv = make_invoker(gem_module, reasoning="high")
    assert inv.reasoning == FakeThinkingLevel.HIGH


def test_init_maps_reasoning_none_and_false_to_none(gem_module):
    inv_none = make_invoker(gem_module, reasoning=None)
    inv_false = make_invoker(gem_module, reasoning=False)

    assert inv_none.reasoning is None
    assert inv_false.reasoning is None


def test_init_maps_unknown_reasoning_to_minimal(gem_module):
    inv = make_invoker(gem_module, reasoning="weird-value")
    assert inv.reasoning == FakeThinkingLevel.MINIMAL


def test_init_maps_minimal_aliases(gem_module):
    inv_none_word = make_invoker(gem_module, reasoning="none")
    inv_minimal = make_invoker(gem_module, reasoning="minimal")

    assert inv_none_word.reasoning == FakeThinkingLevel.MINIMAL
    assert inv_minimal.reasoning == FakeThinkingLevel.MINIMAL


# ------------------------------
# invoke
# ------------------------------


def test_invoke_uses_stored_instructions_when_none_are_passed(gem_module):
    client = FakeClient(text="RESULT")
    inv = make_invoker(gem_module, client=client)

    result = inv.invoke("PROMPT")

    assert result == "RESULT"
    call = client.models.calls[0]
    assert call["model"] == "gemini-2.5-flash"
    assert call["contents"] == "PROMPT"
    assert isinstance(call["config"], FakeGenerateContentConfig)
    assert call["config"].kwargs == {
        "system_instruction": "BASE-INSTR",
    }


def test_invoke_uses_override_instructions_when_provided(gem_module):
    client = FakeClient(text="RESULT")
    inv = make_invoker(gem_module, client=client)

    inv.invoke("PROMPT", instructions="OVERRIDE")

    assert client.models.calls[0]["config"].kwargs["system_instruction"] == "OVERRIDE"


def test_invoke_includes_optional_reasoning_temperature_and_top_p(gem_module):
    client = FakeClient(text="RESULT")
    inv = make_invoker(
        gem_module,
        client=client,
        model="gemini-2.5-pro",
        reasoning="medium",
        temperature=0.25,
        top_p=0.7,
    )

    inv.invoke("PROMPT")

    call = client.models.calls[0]
    config = call["config"]
    assert call["model"] == "gemini-2.5-pro"
    assert config.kwargs["temperature"] == 0.25
    assert config.kwargs["top_p"] == 0.7
    thinking_cfg = config.kwargs["thinking_config"]
    assert isinstance(thinking_cfg, FakeThinkingConfig)
    assert thinking_cfg.thinking_level == FakeThinkingLevel.MEDIUM


def test_invoke_boolean_response_adds_json_config_and_returns_true(gem_module):
    client = FakeClient(text='{"b": true}')
    inv = make_invoker(gem_module, client=client, boolean_response=True)

    result = inv.invoke("PROMPT")

    assert result is True
    config = client.models.calls[0]["config"]
    assert config.kwargs["response_mime_type"] == "application/json"
    assert config.kwargs["response_json_schema"] == gem_module.GEMINI_BOOLEAN_SCHEMA


def test_invoke_boolean_response_returns_false(gem_module):
    client = FakeClient(text='{"b": false}')
    inv = make_invoker(gem_module, client=client, boolean_response=True)

    result = inv.invoke("PROMPT")

    assert result is False


def test_invoke_returns_plain_text_when_not_in_boolean_mode(gem_module):
    client = FakeClient(text="Translated text")
    inv = make_invoker(gem_module, client=client)

    result = inv.invoke("PROMPT")

    assert result == "Translated text"


def test_invoke_raises_value_error_for_invalid_boolean_json(gem_module):
    client = FakeClient(text="not-json")
    inv = make_invoker(gem_module, client=client, boolean_response=True)

    with pytest.raises(ValueError):
        inv.invoke("PROMPT")


def test_invoke_raises_key_error_when_boolean_payload_lacks_b_field(gem_module):
    client = FakeClient(text='{"x": true}')
    inv = make_invoker(gem_module, client=client, boolean_response=True)

    with pytest.raises(KeyError):
        inv.invoke("PROMPT")


# ------------------------------
# pickling / rebinding
# ------------------------------


def test_getstate_drops_client_but_preserves_other_state(gem_module):
    inv = make_invoker(
        gem_module,
        client=FakeClient(),
        model="gemini-2.5-pro",
        reasoning="low",
        temperature=0.2,
        top_p=0.6,
        boolean_response=True,
    )

    state = inv.__getstate__()

    assert state["client"] is None
    assert state["instructions"] == "BASE-INSTR"
    assert state["model"] == "gemini-2.5-pro"
    assert state["temperature"] == 0.2
    assert state["top_p"] == 0.6
    assert state["boolean_response"] is True
    assert state["reasoning"] == FakeThinkingLevel.LOW


def test_setstate_restores_attributes_and_sets_client_to_none(gem_module):
    inv = make_invoker(gem_module, client=FakeClient())
    state = {
        "client": "OLD-CLIENT",
        "instructions": "RESTORED-INSTR",
        "model": "gemini-2.5-flash",
        "verbosity": "unused",
        "temperature": 0.9,
        "top_p": 0.4,
        "boolean_response": True,
        "reasoning": FakeThinkingLevel.HIGH,
    }

    inv.__setstate__(state)

    assert inv.client is None
    assert inv.instructions == "RESTORED-INSTR"
    assert inv.model == "gemini-2.5-flash"
    assert inv.verbosity == "unused"
    assert inv.temperature == 0.9
    assert inv.top_p == 0.4
    assert inv.boolean_response is True
    assert inv.reasoning == FakeThinkingLevel.HIGH


def test_bind_client_replaces_client_reference(gem_module):
    inv = make_invoker(gem_module, client=FakeClient())
    new_client = FakeClient(text="NEW")

    inv.bind_client(new_client)

    assert inv.client is new_client
