"""Offline unit tests for the current, job-specific PromptGateway."""
import importlib.util
import pathlib
import sys
import types

import pytest

# These tests can run beside the two uploaded source files, without installing Yiding.
HERE = pathlib.Path(__file__).resolve().parent
SOURCE = next(path for path in (HERE.parent / 'prompt_gateway.py', HERE / 'prompt_gateway.py', HERE / 'prompt_gateway(20261103-030250).py') if path.is_file())
INSTRUCTORS = next(path for path in (HERE.parent / 'instructors.py', HERE / 'instructors.py', HERE / 'instructors(20261103-030237).py') if path.is_file())


class FakeGPTInvoker:
    def __init__(self, client, instructions, model, reasoning, verbosity, temperature, top_p, boolean_response):
        self.client, self.instructions, self.model = client, instructions, model
        self.reasoning, self.verbosity = reasoning, verbosity
        self.temperature, self.top_p = temperature, top_p
        self.boolean_response = boolean_response


class FakeGeminiInvoker(FakeGPTInvoker):
    pass


class FakeOpenAI:
    def __init__(self, api_key):
        self.api_key = api_key


class FakeGoogleClient:
    def __init__(self, api_key):
        self.api_key = api_key


@pytest.fixture
def pg_module(monkeypatch):
    """Load actual source with stubbed external dependencies and relative imports."""
    pkg = '_gateway_testpkg'
    package = types.ModuleType(pkg)
    package.__path__ = [str(HERE)]
    monkeypatch.setitem(sys.modules, pkg, package)

    provider_mod = types.ModuleType(f'{pkg}.llm_lists')
    def identify_model_provider(model):
        if model.startswith(('gpt-', 'o4-')):
            return 'OpenAI'
        if model.startswith('gemini-'):
            return 'Google'
        return None
    provider_mod.identify_model_provider = identify_model_provider
    monkeypatch.setitem(sys.modules, f'{pkg}.llm_lists', provider_mod)

    keyring = types.ModuleType('keyring')
    keyring.get_password = lambda service, provider: None
    monkeypatch.setitem(sys.modules, 'keyring', keyring)

    for name, cls in (('gpt_invoker', FakeGPTInvoker), ('gemini_invoker', FakeGeminiInvoker)):
        mod = types.ModuleType(f'{pkg}.{name}')
        setattr(mod, 'GPT_Invoker' if name == 'gpt_invoker' else 'Gemini_Invoker', cls)
        monkeypatch.setitem(sys.modules, f'{pkg}.{name}', mod)

    openai = types.ModuleType('openai')
    openai.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, 'openai', openai)
    google = types.ModuleType('google')
    google.__path__ = []
    google_genai = types.ModuleType('google.genai')
    google_genai.Client = FakeGoogleClient
    google.genai = google_genai
    monkeypatch.setitem(sys.modules, 'google', google)
    monkeypatch.setitem(sys.modules, 'google.genai', google_genai)

    spec = importlib.util.spec_from_file_location(f'{pkg}.instructors', INSTRUCTORS)
    instr = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, instr)
    spec.loader.exec_module(instr)
    package.instructors = instr

    spec = importlib.util.spec_from_file_location(f'{pkg}.prompt_gateway', SOURCE)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, mod)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def settings():
    def llm(model='gpt-4o', **overrides):
        return dict(model=model, reasoning=False, verbosity=False,
                    temperature=False, top_p=False, **overrides)
    return {
        'punctuation': {
            'guidelines': 'Keep original Chinese characters.',
            'cross_check': {'enabled': False},
            'punctuation': llm(),
            'cross_examination': llm(),
            'cross_correction': llm(),
        },
        'translation': {
            'language': 'English', 'guidelines': 'Use clear English.',
            'llm_glossary_selection': {'enabled': False},
            'cross_check': {'enabled': False},
            'glossary_selection': llm(),
            'translation': llm(),
            'cross_examination': llm(),
            'cross_correction': llm(),
            'glossary_extraction': llm(),
        },
        'term_extraction': {'guidelines': 'Prefer terms.', 'extraction': llm()},
        'glossary_extraction': {'guidelines': 'Keep attestations.', 'extraction': llm()},
    }


@pytest.fixture
def keys(pg_module, monkeypatch):
    calls = []
    def get_password(service, provider):
        calls.append((service, provider))
        return {'OpenAI': 'OPENAI-KEY', 'Google': 'GOOGLE-KEY'}.get(provider)
    monkeypatch.setattr(pg_module.keyring, 'get_password', get_password)
    return calls


def blank_gateway(pg_module, settings):
    obj = pg_module.PromptGateway.__new__(pg_module.PromptGateway)
    obj.settings = settings
    obj.openai_client = None
    obj.google_client = None
    return obj


def test_create_client_openai_uses_keyring_and_caches(pg_module, settings, keys):
    gateway = blank_gateway(pg_module, settings)
    a = gateway.create_client('gpt-4o')
    b = gateway.create_client('o4-mini')
    assert a is b
    assert isinstance(a, FakeOpenAI)
    assert a.api_key == 'OPENAI-KEY'
    assert keys == [('Yiding', 'OpenAI')]


def test_create_client_google_uses_keyring_and_caches(pg_module, settings, keys):
    gateway = blank_gateway(pg_module, settings)
    a = gateway.create_client('gemini-2.5-pro')
    b = gateway.create_client('gemini-2.5-flash')
    assert a is b
    assert isinstance(a, FakeGoogleClient)
    assert a.api_key == 'GOOGLE-KEY'
    assert keys == [('Yiding', 'Google')]


@pytest.mark.parametrize('model,provider,message', [
    ('gpt-4o', 'OpenAI', 'No OpenAI API key is saved in Yiding.'),
    ('gemini-2.5-pro', 'Google', 'No Google API key is saved in Yiding.'),
])
def test_create_client_missing_key(pg_module, settings, monkeypatch, model, provider, message):
    gateway = blank_gateway(pg_module, settings)
    calls = []
    monkeypatch.setattr(pg_module.keyring, 'get_password', lambda service, p: calls.append((service, p)) or None)
    with pytest.raises(ValueError, match=message):
        gateway.create_client(model)
    assert calls == [('Yiding', provider)]


def test_create_client_unknown_model(pg_module, settings):
    with pytest.raises(ValueError, match='Unknown model in settings: llama-3'):
        blank_gateway(pg_module, settings).create_client('llama-3')


def test_create_invoker_gpt_normalizes_false_and_boolean(pg_module, settings, monkeypatch):
    gateway = blank_gateway(pg_module, settings)
    calls = []
    monkeypatch.setattr(gateway, 'create_client', lambda model: calls.append(model) or 'CLIENT')
    spec = settings['punctuation']['cross_examination']
    inv = gateway.create_invoker(spec, 'PROMPT', boolean_response=True)
    assert isinstance(inv, FakeGPTInvoker)
    assert (inv.client, inv.instructions, inv.model) == ('CLIENT', 'PROMPT', 'gpt-4o')
    assert (inv.reasoning, inv.verbosity, inv.temperature, inv.top_p) == (None, None, None, None)
    assert inv.boolean_response is True
    assert calls == ['gpt-4o']


def test_create_invoker_gemini_passes_parameters(pg_module, settings, monkeypatch):
    gateway = blank_gateway(pg_module, settings)
    monkeypatch.setattr(gateway, 'create_client', lambda model: 'GOOGLE-CLIENT')
    spec = dict(model='gemini-2.5-flash', reasoning='high', verbosity='low', temperature=0.2, top_p=0.7)
    inv = gateway.create_invoker(spec, 'PROMPT')
    assert isinstance(inv, FakeGeminiInvoker)
    assert (inv.client, inv.instructions, inv.model) == ('GOOGLE-CLIENT', 'PROMPT', 'gemini-2.5-flash')
    assert (inv.reasoning, inv.verbosity, inv.temperature, inv.top_p) == ('high', 'low', 0.2, 0.7)
    assert inv.boolean_response is False


def test_create_invoker_unknown_model(pg_module, settings):
    with pytest.raises(ValueError, match='Unknown LLM model'):
        blank_gateway(pg_module, settings).create_invoker(settings['punctuation']['punctuation'] | {'model': 'claude-3'}, 'PROMPT')


@pytest.mark.parametrize('job,expected_names', [
    ('punctuation', ['punctuator']),
    ('translation', ['translator', 'glossary_extractor']),
    ('term_extraction', ['mono_glossary_selector']),
    ('glossary_extraction', ['mono_glossary_extractor']),
    ('unknown_job', []),
])
def test_init_builds_only_invokers_for_selected_job(pg_module, settings, keys, job, expected_names):
    gateway = pg_module.PromptGateway(settings, job)
    all_names = ('punctuator', 'punctuation_examinator', 'punctuation_corrector',
                 'glossary_selector', 'translator', 'translation_examinator',
                 'translation_corrector', 'glossary_extractor',
                 'mono_glossary_selector', 'mono_glossary_extractor')
    assert gateway.job == job
    assert len(gateway.invokers) == len(expected_names)
    assert [getattr(gateway, name) for name in expected_names] == gateway.invokers
    for name in set(all_names) - set(expected_names):
        assert getattr(gateway, name) is None
    assert gateway.log.count('------------') == len(expected_names)
    for inv in gateway.invokers:
        assert inv.instructions in gateway.log


@pytest.mark.parametrize('job,flag,expected_names', [
    ('punctuation', 'cross_check', ['punctuator', 'punctuation_examinator', 'punctuation_corrector']),
    ('translation', 'cross_check', ['translator', 'translation_examinator', 'translation_corrector', 'glossary_extractor']),
])
def test_cross_check_enables_examination_and_correction(pg_module, settings, keys, job, flag, expected_names):
    settings[job][flag]['enabled'] = True
    gateway = pg_module.PromptGateway(settings, job)
    assert len(gateway.invokers) == len(expected_names)
    assert [getattr(gateway, name) for name in expected_names] == gateway.invokers
    examiner = getattr(gateway, 'punctuation_examinator' if job == 'punctuation' else 'translation_examinator')
    assert examiner.boolean_response is True
    assert all(inv.boolean_response is False for inv in gateway.invokers if inv is not examiner)


def test_translation_llm_selection_enabled(pg_module, settings, keys):
    settings['translation']['llm_glossary_selection']['enabled'] = True
    gateway = pg_module.PromptGateway(settings, 'translation')
    assert gateway.invokers == [gateway.glossary_selector, gateway.translator, gateway.glossary_extractor]
    assert gateway.glossary_selector is not None


def test_translation_all_optional_invokers(pg_module, settings, keys):
    settings['translation']['cross_check']['enabled'] = True
    settings['translation']['llm_glossary_selection']['enabled'] = True
    gateway = pg_module.PromptGateway(settings, 'translation')
    assert gateway.invokers == [gateway.glossary_selector, gateway.translator,
                                gateway.translation_examinator, gateway.translation_corrector,
                                gateway.glossary_extractor]
    assert gateway.translation_examinator.boolean_response is True


def test_job_specific_guidelines_are_used(pg_module, settings, keys):
    a = pg_module.PromptGateway(settings, 'term_extraction')
    b = pg_module.PromptGateway(settings, 'glossary_extraction')
    assert 'Prefer terms.' in a.mono_glossary_selector.instructions
    assert 'Keep attestations.' in b.mono_glossary_extractor.instructions


def test_update_log_wraps_message_in_newlines(pg_module, settings):
    gateway = blank_gateway(pg_module, settings)
    gateway.log = ''
    gateway._update_log('MESSAGE')
    assert gateway.log == '\nMESSAGE\n'
