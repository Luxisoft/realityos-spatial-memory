// Run generated scripts offline with Postman's collection/environment precedence.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const c = JSON.parse(fs.readFileSync('docs/postman/RealityOS.postman_collection.json'));
const defaults = Object.fromEntries(c.variable.map(v => [v.key, v.value]));
const walk = items => items.flatMap(i => i.item ? walk(i.item) : [i]);
function execute(item, listen, values = {}, environment = {}, code = 200, body = {}, replies = []) {
  let skipped = false;
  const collection = { ...defaults, ...values };
  environment = { ...environment };
  const failures = [];
  const calls = [];
  const local = {};
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
    if (e.listen === listen) vm.runInNewContext(e.script.exec.join('\n'), { pm, console: { warn: () => {} } });
  }
  return { collection, environment, local, calls, skipped, failures };
}
let guards = 0;
for (const [index, target] of c.item.entries()) {
  const prefix = index ? 'localhost_' : 'server_';
  const other = index ? 'server_' : 'localhost_';
  const all = walk(target.item);
  for (const i of all) {
    for (const e of i.event || []) new vm.Script(e.script.exec.join('\n'));
    if (JSON.stringify(i.event).includes('enable_write_requests')) {
      assert(execute(i, 'prerequest').skipped);
      assert.equal(execute(i, 'prerequest').calls.length, 0);
      assert(!execute(i, 'prerequest', { [prefix + 'enable_write_requests']: 'true' }).skipped);
      assert(!execute(i, 'prerequest', {}, { [prefix + 'enable_write_requests']: 'true' }).skipped);
      assert(execute(i, 'prerequest', { [other + 'enable_write_requests']: 'true' }, { enable_write_requests: 'true' }).skipped);
      guards++;
    }
    if (/POST \/v1\/auth\/(login|refresh|local-login|facebook|guest)$/.test(i.name)) {
      const tokens = { access_token: 'test-access', refresh_token: 'test-refresh' };
      for (const env of [{}, { [prefix + 'access_token']: '', [prefix + 'refresh_token']: '' }, { [other + 'access_token']: 'other-access', access_token: 'legacy-access' }]) {
        const result = execute(i, 'test', { [other + 'access_token']: 'other-access' }, env, 200, tokens);
        for (const [name, token] of Object.entries(tokens)) {
          assert.equal(result.collection[prefix + name], token);
          if (Object.hasOwn(env, prefix + name)) assert.equal(result.environment[prefix + name], token);
        }
        assert.equal(result.collection[other + 'access_token'], 'other-access');
        assert.deepEqual(Object.keys(result.environment), Object.keys(env));
        assert.equal(result.failures.length, 0);
      }
      for (const [code, body] of [[401, {}], [200, {}], [200, { access_token: 'incomplete' }]]) {
        const result = execute(i, 'test', { [prefix + 'access_token']: 'previous' }, {}, code, body);
        assert.equal(result.collection[prefix + 'access_token'], 'previous');
        if (code === 401) assert(result.failures.length);
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
  const identity = JSON.stringify([origin, defaults[prefix + 'email']]);
  const cached = {
    [prefix + 'access_token']: 'old-access',
    [prefix + 'refresh_token']: 'old-refresh',
    [prefix + 'session_identity']: identity,
    [other + 'access_token']: 'other-access'
  };
  for (const env of [{}, { [prefix + 'access_token']: '', [prefix + 'refresh_token']: '', [prefix + 'session_identity']: '' }]) {
    const automatic = execute(query, 'prerequest', { [other + 'access_token']: 'other-access' }, env);
    assert.equal(automatic.calls.length, 1);
    assert.equal(automatic.calls[0].url, origin + '/v1/auth/login');
    assert.deepEqual(JSON.parse(automatic.calls[0].body.raw), {
      email: defaults[prefix + 'email'], password: defaults[prefix + 'password']
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
  const revoked = execute(query, 'prerequest', cached, {}, 200, {}, [{ code: 401 }, { code: 401 }]);
  assert.deepEqual(revoked.calls.map(r => r.url), [origin + '/v1/auth/me', origin + '/v1/auth/refresh', origin + '/v1/auth/login']);
  for (const changes of [{ [prefix + 'email']: 'own@example.test' }, { [prefix + 'base_url']: 'https://own.example.test' }]) {
    const changed = execute(query, 'prerequest', { ...cached, ...changes });
    assert.equal(changed.calls.length, 1);
    assert(changed.calls[0].url.endsWith('/v1/auth/login'));
  }
  for (const reply of [{ code: 401 }, { code: 429 }, { code: 503 }, { error: 'network failure' }, { code: 200, body: {} }, { code: 200, body: null }, { code: 200, invalidJson: true }]) {
    assert.throws(() => execute(query, 'prerequest', {}, {}, 200, {}, [reply]), /login|Authentication/);
  }
  assert.throws(() => execute(query, 'prerequest', cached, {}, 200, {}, [{ code: 503 }]), /Session validation failed/);
}
console.log(`PASS: ${walk(c.item).length} request scripts; ${guards} write guards; automatic login/refresh on Send; account/origin changes and failures; isolated sessions and workspace IDs. No HTTP requests.`);
