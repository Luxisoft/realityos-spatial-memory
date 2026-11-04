// Run generated scripts offline with Postman's collection/environment precedence.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const c = JSON.parse(fs.readFileSync('docs/postman/RealityOS.reference.postman_collection.json'));
const jury = JSON.parse(fs.readFileSync('docs/postman/RealityOS.postman_collection.json'));
const defaults = Object.fromEntries([...c.variable, ...jury.variable].map(v => [v.key, v.value]));
const contract = JSON.parse(fs.readFileSync('tests/contracts/openapi.json'));
const walk = items => items.flatMap(i => i.item ? walk(i.item) : [i]);
function execute(item, listen, values = {}, environment = {}, code = 200, body = {}, replies = [], local = {}) {
  let skipped = false;
  const collection = { ...defaults, ...values };
  environment = { ...environment };
  const failures = [];
  const calls = [];
  const scope = values => ({ get: k => values[k], has: k => Object.hasOwn(values, k), set: (k, v) => { values[k] = v; } });
  const pm = {
    collectionVariables: scope(collection), environment: scope(environment),
    variables: {
      get: k => Object.hasOwn(local, k) ? local[k] : Object.hasOwn(environment, k) ? environment[k] : collection[k],
      set: (k, v) => { local[k] = v; }
    },
    sendRequest: (request, callback) => {
      calls.push(request);
      const reply = replies[calls.length - 1] || { code: 200, body: { access_token: 'auto-access', refresh_token: 'auto-refresh' } };
      callback(reply.error, reply.error ? undefined : { code: reply.code, json: () => {
        if (reply.invalidJson) throw new Error('Invalid JSON');
        return reply.body;
      } });
    },
    execution: { skipRequest: () => { skipped = true; } },
    response: { code, json: () => body },
    test: (name, fn) => { try { fn(); } catch (e) { failures.push(name); } },
    expect: v => ({ to: { be: { below: n => assert(v < n) }, eql: n => assert.equal(v, n) } })
  };
  for (const e of item.event || []) {
    if (e.listen === listen) {
      try { vm.runInNewContext(e.script.exec.join('\n'), { pm, console: { warn: () => {} } }); }
      catch (error) { error.recordedFailures = failures; throw error; }
    }
  }
  return { collection, environment, local, calls, skipped, failures };
}
let guards = 0;
for (const [index, target] of c.item.entries()) {
  if (target.name === 'Server requests') {
    assert(execute(target, 'prerequest').skipped);
    assert.equal(defaults.server_base_url, '');
    assert.equal(defaults.server_password, '');
    for (const item of walk(target.item)) for (const event of item.event || []) new vm.Script(event.script.exec.join('\n'));
    continue;
  }
  const prefix = 'localhost_';
  const other = 'server_';
  const all = walk(target.item);
  for (const i of all) {
    for (const e of i.event || []) new vm.Script(e.script.exec.join('\n'));
    const [method, path] = i.name.split(' ');
    const operation = contract.paths[path]?.[method.toLowerCase()];
    if (operation) {
      const expected = Object.keys(operation.responses).filter(code => /^2\d\d$/.test(code)).map(Number);
      const assertion = { event: [{ listen: 'test', script: { exec: [i.event.find(e => e.listen === 'test').script.exec[0]] } }] };
      for (const code of expected) assert.equal(execute(assertion, 'test', {}, {}, code).failures.length, 0, i.name);
      for (const code of [199, 200, 201, 202, 204, 206, 301, 302, 304, 400, 401, 403, 404, 422, 429, 500]) {
        if (!expected.includes(code)) assert.equal(execute(assertion, 'test', {}, {}, code).failures.length, 1, i.name + ' accepted ' + code);
      }
    }
    if (JSON.stringify(i.event).includes('enable_write_requests')) {
      assert(execute(i, 'prerequest').skipped);
      assert.equal(execute(i, 'prerequest').calls.length, 0);
      assert(!execute(i, 'prerequest', { [prefix + 'enable_write_requests']: 'true' }).skipped);
      assert(!execute(i, 'prerequest', {}, { [prefix + 'enable_write_requests']: 'true' }).skipped);
      assert(execute(i, 'prerequest', { [other + 'enable_write_requests']: 'true' }, { enable_write_requests: 'true' }).skipped);
      guards++;
    }
    if (/POST \/v1\/auth\/(login|refresh|local-login|local-select|facebook|guest)$/.test(i.name)) {
      const tokens = { access_token: 'test-access', refresh_token: 'test-refresh' };
      for (const env of [{}, { [prefix + 'access_token']: '', [prefix + 'refresh_token']: '' }, { [other + 'access_token']: 'other-access', access_token: 'legacy-access' }]) {
        const result = execute(i, 'test', { [other + 'access_token']: 'other-access' }, env, 200, tokens);
        for (const [name, token] of Object.entries(tokens)) {
          assert.equal(result.collection[prefix + name], token);
          assert.equal(result.local[prefix + name], token);
          if (Object.hasOwn(env, prefix + name)) assert.equal(result.environment[prefix + name], token);
        }
        assert.equal(result.collection[other + 'access_token'], 'other-access');
        assert.deepEqual(Object.keys(result.environment), Object.keys(env));
        assert.equal(result.failures.length, 0);
      }
      for (const [code, body] of [[401, {}], [200, {}], [200, null], [200, { access_token: 'incomplete' }], [200, { access_token: '', refresh_token: 'incomplete' }]]) {
        const result = execute(i, 'test', { [prefix + 'access_token']: 'previous' }, {}, code, body);
        assert.equal(result.collection[prefix + 'access_token'], 'previous');
        assert(result.failures.length);
        if (code === 200) assert(result.failures.includes('Session tokens returned'));
      }
    }
  }
  const query = target.item[0].item.at(-1);
  assert(!execute(query, 'prerequest').skipped); // Explicit demo ID is preconfigured.
  assert.throws(() => execute(query, 'prerequest', { [prefix + 'workspace_id']: '' }), /workspace_id/);
  assert.throws(() => execute(query, 'prerequest', {}, { [prefix + 'workspace_id']: '' }), /workspace_id/);
  const login = target.item[0].item[1];
  const signedIn = execute(login, 'test', {}, {}, 200, { access_token: 'new-session', refresh_token: 'new-refresh' });
  const resolve = text => text.replace(/{{([^}]+)}}/g, (_, key) => signedIn.collection[key]);
  const me = target.item[0].item[2].request;
  assert.equal(resolve(me.auth.bearer[0].value), 'new-session');
  assert.equal(resolve(me.url.raw), (index ? 'http://localhost:8080' : 'https://realityos.luxisoft.com') + '/v1/auth/me');

  const origin = defaults[prefix + 'base_url'];
  const identity = JSON.stringify([origin, defaults[prefix + 'user_id']]);
  const cached = {
    [prefix + 'access_token']: 'old-access',
    [prefix + 'refresh_token']: 'old-refresh',
    [prefix + 'session_identity']: identity,
    [other + 'access_token']: 'other-access'
  };
  for (const env of [{}, { [prefix + 'access_token']: '', [prefix + 'refresh_token']: '', [prefix + 'session_identity']: '' }]) {
    const automatic = execute(query, 'prerequest', { [other + 'access_token']: 'other-access' }, env);
    assert.equal(automatic.calls.length, 1);
    assert.equal(automatic.calls[0].url, origin + '/v1/auth/local-select');
    assert.deepEqual(JSON.parse(automatic.calls[0].body.raw), {
      user_id: defaults[prefix + 'user_id']
    });
    assert.equal(automatic.collection[prefix + 'access_token'], 'auto-access');
    assert.equal(automatic.local[prefix + 'access_token'], 'auto-access');
    assert.equal(automatic.collection[prefix + 'session_identity'], identity);
    assert.equal(automatic.collection[other + 'access_token'], 'other-access');
    assert.deepEqual(Object.keys(automatic.environment), Object.keys(env));
    if (Object.keys(env).length) assert.equal(automatic.environment[prefix + 'access_token'], 'auto-access');
  }
  const valid = execute(query, 'prerequest', cached);
  assert.deepEqual(valid.calls.map(r => r.url), [origin + '/v1/auth/me']);
  assert.equal(valid.calls[0].header.Authorization, 'Bearer old-access');
  assert.equal(valid.collection[prefix + 'access_token'], 'old-access');
  const expired = execute(query, 'prerequest', cached, {}, 200, {}, [{ code: 401 }]);
  assert.deepEqual(expired.calls.map(r => r.url), [origin + '/v1/auth/me', origin + '/v1/auth/refresh']);
  assert.deepEqual(JSON.parse(expired.calls[1].body.raw), { refresh_token: 'old-refresh' });
  assert.equal(expired.collection[prefix + 'refresh_token'], 'auto-refresh');
  // Local variables persist across requests in the real Postman/Newman runner.
  // Explicit login and refresh must replace tokens shadowing collection/environment.
  const refresh = all.find(i => i.name === 'POST /v1/auth/refresh');
  const local = { ...expired.local };
  let state = expired;
  for (const item of [login, refresh, refresh]) {
    const before = execute(item, 'prerequest', state.collection, {}, 200, {}, [], local);
    if (item === refresh) {
      const raw = item.request.body.raw.replace(/{{([^}]+)}}/g, (_, key) => before.local[key] ?? before.collection[key]);
      assert.equal(JSON.parse(raw).refresh_token, state.collection[prefix + 'refresh_token']);
    }
    const tokens = { access_token: 'new-' + state.collection[prefix + 'access_token'], refresh_token: 'new-' + state.collection[prefix + 'refresh_token'] };
    state = execute(item, 'test', before.collection, {}, 200, tokens, [], local);
    assert.equal(local[prefix + 'access_token'], tokens.access_token);
    assert.equal(local[prefix + 'refresh_token'], tokens.refresh_token);
    assert.equal(local[prefix + 'session_identity'], identity);
  }
  const revoked = execute(query, 'prerequest', cached, {}, 200, {}, [{ code: 401 }, { code: 401 }]);
  assert.deepEqual(revoked.calls.map(r => r.url), [origin + '/v1/auth/me', origin + '/v1/auth/refresh', origin + '/v1/auth/local-select']);
  for (const changes of [{ [prefix + 'user_id']: 'other-local-id' }, { [prefix + 'base_url']: 'https://own.example.test' }]) {
    const changed = execute(query, 'prerequest', { ...cached, ...changes });
    assert.equal(changed.calls.length, 1);
    assert(changed.calls[0].url.endsWith('/v1/auth/local-select'));
  }
  for (const reply of [{ code: 401 }, { code: 429 }, { code: 503 }, { error: 'network failure' }, { code: 200, body: {} }, { code: 200, body: null }, { code: 200, invalidJson: true }]) {
    assert.throws(() => execute(query, 'prerequest', {}, {}, 200, {}, [reply]), error => /login|Authentication/.test(error.message) && error.recordedFailures.includes('Authentication ready'));
  }
  assert.throws(() => execute(query, 'prerequest', cached, {}, 200, {}, [{ code: 503 }]), /Session validation failed/);
}
const scenarios = jury.item[0].item.find(folder => folder.name === '00 Local scenarios').item;
assert.deepEqual(jury.item.map(folder => folder.name), ['Localhost requests', 'Server requests']);
for (const [index, target] of scenarios.entries()) {
  const prefix = ['security_', 'meta_social_', 'memory_'][index];
  for (const item of target.item) {
    const result = execute(item, 'prerequest');
    assert(!result.skipped);
    const values = { ...defaults, ...result.collection, ...result.local };
    const resolve = text => text.replace(/{{([^}]+)}}/g, (_, key) => {
      assert(values[key], 'Unfilled input: ' + key);
      assert(key.startsWith(prefix), 'Cross-scenario input: ' + key);
      return values[key];
    });
    const request = JSON.parse(resolve(JSON.stringify(item.request)));
    assert(request.url.raw.startsWith('http://localhost:8080/'));
    if (request.auth.type === 'bearer') assert.equal(request.auth.bearer[0].value, 'auto-access');
    if (request.body?.mode === 'raw') JSON.parse(request.body.raw);
    assert(!request.body?.formdata, 'Jury request requires a file selection');
    for (const call of result.calls) assert.equal(call.url, 'http://localhost:8080/v1/auth/local-select');
  }
}
for (const [index, target] of jury.item.entries()) {
  if (target.name === 'Server requests') {
    assert(execute(target, 'prerequest').skipped);
    assert.equal(defaults.server_base_url, '');
    assert.equal(defaults.server_password, '');
    for (const item of walk(target.item)) for (const event of item.event || []) new vm.Script(event.script.exec.join('\n'));
    continue;
  }
  const prefix = 'localhost_';
  const origin = 'http://localhost:8080';
  const quick = target.item.find(folder => folder.name === '00 Quick start').item;
  for (const item of quick) {
    const result = execute(item, 'prerequest');
    assert(!result.skipped);
    const values = { ...defaults, ...result.collection, ...result.local };
    const request = JSON.parse(JSON.stringify(item.request).replace(/{{([^}]+)}}/g, (_, key) => {
      assert(key.startsWith(prefix));
      assert(values[key], 'Unfilled quick-start input: ' + key);
      return values[key];
    }));
    assert(request.url.raw.startsWith(origin + '/'));
    for (const call of result.calls) {
      assert.equal(call.url, origin + '/v1/auth/local-select');
      assert.equal(JSON.parse(call.body.raw).user_id, defaults[prefix + 'user_id']);
    }
  }
  for (const item of walk(target.item)) {
    for (const event of item.event || []) {
      new vm.Script(event.script.exec.join('\n'));
    }
  }
}
console.log(`PASS: both destinations with prefilled quick starts; ${walk(scenarios).length} live scenario requests; ${walk(jury.item).length} total requests; ${guards} reference write guards; isolated server/local sessions. No HTTP requests.`);
