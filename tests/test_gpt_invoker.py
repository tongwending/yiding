import importlib
import importlib.util
import pathlib
import sys
import types

import pytest


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent
GPT_INVOKER_PATH = DATA_DIR / "gpt_invoker.py"


class FakeResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class FakeResponsesAPI:
    def __init__(self, output_text="TEXT"):
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.output_text)


class FakeClient:
    def __init__(self, output_text="TEXT"):
        self.responses = FakeResponsesAPI(output_text=output_text)


@pytest.fixture(scope="session")
def gi_module():
    try:
        return importlib.import_module("yiding.gpt_invoker")
    except Exception:
        package_name = "_gpt_invoker_testpkg"
        package = types.ModuleType(package_name)
        package.__path__ = [str(DATA_DIR)]
        sys.modules[package_name] = package

        spec = importlib.util.spec_from_file_location(
            f"{package_name}.gpt_invoker",
            GPT_INVOKER_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


def make_invoker(gi_module, client=None, **kwargs):
    client = client or FakeClient()
    params = {
        "client": client,
        "instructions": "BASE-INSTR",
        "model": "gpt-4o",
        "reasoning": None,
        "verbosity": None,
        "temperature": None,
        "top_p": None,
        "boolean_response": False,
    }
    params.update(kwargs)
    return gi_module.GPT_Invoker(**params)


# ------------------------------
# invoke
# ------------------------------


def test_invoke_uses_stored_instructions_when_none_are_passed(gi_module):
    client = FakeClient(output_text="RESULT")
    inv = make_invoker(gi_module, client=client)

    result = inv.invoke("PROMPT")

    assert result == "RESULT"
    assert client.responses.calls == [{
        "model": "gpt-4o",
        "instructions": "BASE-INSTR",
        "input": "PROMPT",
        "text": {},
    }]



def test_invoke_uses_override_instructions_when_provided(gi_module):
    client = FakeClient(output_text="RESULT")
    inv = make_invoker(gi_module, client=client)

    inv.invoke("PROMPT", instructions="OVERRIDE")

    assert client.responses.calls[0]["instructions"] == "OVERRIDE"



def test_invoke_includes_all_optional_parameters_when_set(gi_module):
    client = FakeClient(output_text="RESULT")
    inv = make_invoker(
        gi_module,
        client=client,
        model="o4-mini",
        reasoning="high",
        verbosity="low",
        temperature=0.3,
        top_p=0.8,
    )

    inv.invoke("PROMPT")

    assert client.responses.calls == [{
        "model": "o4-mini",
        "instructions": "BASE-INSTR",
        "input": "PROMPT",
        "reasoning": {"effort": "high"},
        "text": {"verbosity": "low"},
        "temperature": 0.3,
        "top_p": 0.8,
    }]



def test_invoke_boolean_response_adds_schema_and_returns_true(gi_module):
    client = FakeClient(output_text='{"b": true}')
    inv = make_invoker(
        gi_module,
        client=client,
        boolean_response=True,
    )

    result = inv.invoke("PROMPT")

    assert result is True
    assert client.responses.calls[0]["text"] == {
        "format": gi_module.GPT_BOOLEAN_SCHEMA,
    }



def test_invoke_boolean_response_with_verbosity_includes_both_text_keys(gi_module):
    client = FakeClient(output_text='{"b": false}')
    inv = make_invoker(
        gi_module,
        client=client,
        verbosity="medium",
        boolean_response=True,
    )

    result = inv.invoke("PROMPT")

    assert result is False
    assert client.responses.calls[0]["text"] == {
        "verbosity": "medium",
        "format": gi_module.GPT_BOOLEAN_SCHEMA,
    }



def test_invoke_returns_plain_output_text_when_not_boolean_mode(gi_module):
    client = FakeClient(output_text="Translated text")
    inv = make_invoker(gi_module, client=client, boolean_response=False)

    result = inv.invoke("PROMPT")

    assert result == "Translated text"



def test_invoke_raises_json_error_for_invalid_boolean_payload(gi_module):
    client = FakeClient(output_text="not-json")
    inv = make_invoker(gi_module, client=client, boolean_response=True)

    with pytest.raises(ValueError):
        inv.invoke("PROMPT")



def test_invoke_raises_key_error_when_boolean_payload_lacks_b_field(gi_module):
    client = FakeClient(output_text='{"x": true}')
    inv = make_invoker(gi_module, client=client, boolean_response=True)

    with pytest.raises(KeyError):
        inv.invoke("PROMPT")


# ------------------------------
# pickling / rebinding helpers
# ------------------------------


def test_getstate_drops_client_but_preserves_other_state(gi_module):
    client = FakeClient()
    inv = make_invoker(
        gi_module,
        client=client,
        reasoning="medium",
        verbosity="low",
        temperature=0.2,
        top_p=0.7,
        boolean_response=True,
    )

    state = inv.__getstate__()

    assert state["client"] is None
    assert state["instructions"] == "BASE-INSTR"
    assert state["model"] == "gpt-4o"
    assert state["reasoning"] == "medium"
    assert state["verbosity"] == "low"
    assert state["temperature"] == 0.2
    assert state["top_p"] == 0.7
    assert state["boolean_response"] is True



def test_setstate_restores_attributes_and_sets_client_to_none(gi_module):
    inv = make_invoker(gi_module, client=FakeClient())
    state = {
        "client": "OLD-CLIENT",
        "instructions": "RESTORED-INSTR",
        "model": "gpt-5",
        "verbosity": "high",
        "temperature": 0.9,
        "top_p": 0.4,
        "boolean_response": True,
        "reasoning": "low",
    }

    inv.__setstate__(state)

    assert inv.client is None
    assert inv.instructions == "RESTORED-INSTR"
    assert inv.model == "gpt-5"
    assert inv.verbosity == "high"
    assert inv.temperature == 0.9
    assert inv.top_p == 0.4
    assert inv.boolean_response is True
    assert inv.reasoning == "low"



def test_bind_client_replaces_client_reference(gi_module):
    inv = make_invoker(gi_module, client=FakeClient())
    new_client = FakeClient(output_text="NEW")

    inv.bind_client(new_client)

    assert inv.client is new_client
