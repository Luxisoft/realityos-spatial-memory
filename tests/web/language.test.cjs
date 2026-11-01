const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'frontend/node_modules/typescript'));

function fixture(app, stored = 'en') {
  let effects = [], calls = [], spoken = [], cancelled = 0, voices = [{ lang: 'en-US' }, { lang: 'es-CO' }];
  let account = 'es', rejectSave = false;
  let speechResponse = async () => ({ ok: false, status: 503 });
  const audio = [], revoked = [];
  const storage = new Map([['realityos.language', stored]]);
  const document = { documentElement: { lang: '' } };
  const window = { addEventListener() {}, removeEventListener() {}, speechSynthesis: {
    cancel() { cancelled++; }, getVoices() { return voices; }, speak(value) { spoken.push(value); },
    addEventListener() {}, removeEventListener() {},
  } };
  function load(file) {
    const filename = path.join(root, app, 'src', file + '.ts');
    const source = fs.readFileSync(filename, 'utf8').replace('import.meta.env.VITE_API_URL', 'undefined');
    const output = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } }).outputText;
    const exports = {};
    vm.runInNewContext(output, { exports, require(name) {
      if (name === './translations') return load('translations');
      if (name === 'react') return {
        useEffect(callback) { effects.push(callback); },
        useState(value) { return [value, () => {}]; },
        useSyncExternalStore(subscribe, snapshot) { return snapshot(); },
      };
      throw new Error(name);
    }, localStorage: { getItem(key) { return storage.get(key); }, setItem(key, value) { storage.set(key, value); } },
    document, window, Intl, setTimeout, clearTimeout, AbortController,
    URL: { createObjectURL() { return 'blob:test-audio'; }, revokeObjectURL(url) { revoked.push(url); } },
    Audio: class {
      constructor(url) { this.src = url; audio.push(this); }
      async play() { this.played = true; }
      pause() { this.paused = true; }
    },
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    fetch: async (url, init) => {
      calls.push({ url, ...init });
      if (url.endsWith('/v1/tts')) return speechResponse(url, init);
      if (rejectSave && init.method === 'PATCH') return { ok: false, status: 503 };
      if (init.method === 'PATCH' && (!url.includes('initialize') || account === null)) account = JSON.parse(init.body).preferred_language;
      return { ok: true, json: async () => ({ preferred_language: account }) };
    } }, { filename });
    return exports;
  }
  const module = load('language');
  return { module, calls, spoken, document, audio, revoked, setSpeech(fn) { speechResponse = fn; }, get cancelled() { return cancelled; }, setAccount(value) { account = value; }, setReject(value) { rejectSave = value; }, setVoices(value) { voices = value; }, mount(token) { const hook = module.useLanguage(token); effects.splice(0).forEach(effect => effect()); return hook; } };
}

for (const app of ['frontend', 'display-webapp']) {
  test(`${app}: authenticated Seamless audio and resource cleanup`, async () => {
    const f = fixture(app);
    f.mount('owner-token');
    await f.module.requestLanguage('owner-token');
    f.setSpeech(async () => ({ ok: true, status: 200, headers: { get() { return 'audio/wav'; } }, blob: async () => ({ size: 100 }) }));
    f.module.speakLocalized('Hola', 'es', () => assert.fail('Remote speech succeeds'));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(f.audio.length, 1);
    assert.equal(f.audio[0].played, true);
    assert.equal(f.spoken.length, 0);
    const call = f.calls.find(call => call.url.endsWith('/v1/tts'));
    assert.equal(call.headers.Authorization, 'Bearer owner-token');
    assert.deepEqual(JSON.parse(call.body), { text: 'Hola', language: 'es' });
    f.module.stopLocalizedSpeech();
    assert.equal(f.audio[0].paused, true);
    assert.equal(f.revoked.length, 1);
  });

  test(`${app}: server failure falls back once; unauthorized requests do not`, async () => {
    const f = fixture(app);
    f.mount('owner-token');
    await f.module.requestLanguage('owner-token');
    const notices = [];
    f.module.speakLocalized('Hola', 'es', message => notices.push(message));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(f.spoken.length, 1);
    assert.equal(f.spoken[0].lang, 'es');
    assert(notices[0].includes('dispositivo'));
    assert.equal(f.calls.filter(call => call.url.endsWith('/v1/tts')).length, 1);
    f.setSpeech(async () => ({ ok: false, status: 401 }));
    f.module.speakLocalized('Privado', 'es', message => notices.push(message));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(f.spoken.length, 1);
    assert(notices[1].includes('sesión'));
  });

  test(`${app}: stopping or changing language cancels pending speech without fallback`, async () => {
    const f = fixture(app);
    const hook = f.mount('owner-token');
    await f.module.requestLanguage('owner-token');
    let release;
    f.setSpeech(() => new Promise(resolve => { release = resolve; }));
    f.module.speakLocalized('Hola', 'es', () => assert.fail('Cancelled request must stay silent'));
    const call = f.calls.find(call => call.url.endsWith('/v1/tts'));
    await hook.save('en');
    assert.equal(call.signal.aborted, true);
    release({ ok: false, status: 503 });
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(f.spoken.length, 0);
    assert.equal(f.audio.length, 0);
  });

  test(`${app}: account language, failed save, both directions and source text`, async () => {
    const f = fixture(app);
    const hook = f.mount('owner-token');
    await f.module.requestLanguage('owner-token');
    assert.equal(f.module.languageTag(), 'es');
    assert.equal(f.module.t('Search'), 'Buscar');
    await hook.save('en');
    assert.equal(f.module.t('Search'), 'Search');
    assert.equal(f.document.documentElement.lang, 'en');
    f.setReject(true);
    await hook.save('es');
    assert.equal(f.module.languageTag(), 'en');
    f.setReject(false);
    await hook.save('es');
    assert.equal(f.module.t('Evidence of {name}', { name: 'Taladro José' }), 'Evidencia de Taladro José');
    assert(f.calls.every(call => call.headers.Authorization === 'Bearer owner-token'));
  });

  test(`${app}: missing preference initializes once and honors existing account`, async () => {
    const f = fixture(app, 'en');
    f.setAccount(null);
    f.mount('owner-token');
    await f.module.requestLanguage('owner-token');
    assert.equal(f.module.languageTag(), 'en');
    assert.equal(f.calls.filter(call => call.method === 'PATCH').length, 1);
    f.setAccount('es');
    await f.module.requestLanguage('owner-token');
    assert.equal(f.module.languageTag(), 'es');
    assert.equal(f.calls.filter(call => call.method === 'PATCH').length, 1);
  });

  test(`${app}: voice matches displayed language and stops on switch`, async () => {
    const f = fixture(app);
    const hook = f.mount('');
    f.module.speakLocalized('Hello', 'en', () => assert.fail('English voice exists'));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(f.spoken[0].lang, 'en');
    assert.equal(f.spoken[0].text, 'Hello');
    await hook.save('es');
    f.module.speakLocalized('Stale English', 'en', () => assert.fail('Stale text must be ignored'));
    assert.equal(f.spoken.length, 1);
    assert(f.cancelled > 0);
    f.setVoices([{ lang: 'en-US' }]);
    let notice = '';
    f.module.speakLocalized('Hola', 'es', text => { notice = text; });
    await new Promise(resolve => setImmediate(resolve));
    assert(notice.startsWith('La voz'));
    assert.equal(f.spoken.length, 1);
  });
}
