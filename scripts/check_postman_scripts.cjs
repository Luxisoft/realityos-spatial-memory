// Run generated scripts offline with Postman's collection/environment precedence.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const c = JSON.parse(fs.readFileSync('docs/postman/RealityOS.postman_collection.json'));
const defaults = Object.fromEntries(c.variable.map(v => [v.key, v.value]));
const walk = items => items.flatMap(i => i.item ? walk(i.item) : [i]);
function execute(item, listen, values = {}, environment = {}, code = 200, body = {}) {
  let skipped = false;
  const collection = { ...defaults, ...values };
  environment = { ...environment };
  const failures = [];
  const scope = values => ({ get: k => values[k], has: k => Object.hasOwn(values, k), set: (k, v) => { values[k] = v; } });
  const pm = {
    collectionVariables: scope(collection), environment: scope(environment),
    variables: { get: k => Object.hasOwn(environment, k) ? environment[k] : collection[k] },
    execution: { skipRequest: () => { skipped = true; } },
    response: { code, json: () => body },
    test: (name, fn) => { try { fn(); } catch (e) { failures.push(name); } },
    expect: v => ({ to: { be: { below: n => assert(v < n) }, eql: n => assert.equal(v, n) } })
  };
  for (const e of item.event || []) {
    if (e.listen === listen) vm.runInNewContext(e.script.exec.join('\n'), { pm, console: { warn: () => {} } });
  }
  return { collection, environment, skipped, failures };
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
}
console.log(`PASS: ${walk(c.item).length} request scripts; ${guards} write guards; both targets work without an environment; isolated sessions/refresh/workspace IDs. No HTTP requests.`);
