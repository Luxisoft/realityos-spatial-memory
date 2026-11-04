// Exercise the generated scripts in Newman's real sandbox, against localhost only.
// Install newman@6.2.3 outside the checkout and provide its node_modules in NODE_PATH.
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const assert = require('node:assert/strict');
const newman = require('newman');

const root = path.resolve(__dirname, '..');
const source = JSON.parse(fs.readFileSync(path.join(root, 'docs/postman/RealityOS.postman_collection.json')));
const walk = items => items.flatMap(item => item.item ? walk(item.item) : [item]);
const requests = walk(source.item);

async function run(items, handler, { prefix = 'localhost', environment = false } = {}) {
  let calls = 0;
  const server = http.createServer((request, response) => {
    let raw = '';
    request.on('data', chunk => { raw += chunk; });
    request.on('end', () => {
      calls++;
      handler(request, response, raw, calls);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const collection = structuredClone(source);
  collection.item = structuredClone(items);
  const origin = 'http://127.0.0.1:' + server.address().port;
  for (const variable of collection.variable) {
    if (variable.key.endsWith('_base_url')) variable.value = origin;
    if (variable.key.endsWith('_email')) variable.value = 'tester@example.test';
    if (variable.key.endsWith('_password')) variable.value = 'LocalRuntimeExample123!';
  }
  const options = {
    collection, reporters: [], timeoutRequest: 3000, timeoutScript: 5000,
    ignoreRedirects: true,
  };
  if (environment) {
    options.environment = { values: ['access_token', 'refresh_token', 'session_identity'].map(key => ({ key: prefix + '_' + key, value: '', enabled: true })) };
  }
  try {
    const summary = await new Promise((resolve, reject) => {
      newman.run(options, (error, result) => error ? reject(error) : resolve(result));
    });
    return { calls, summary };
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

function json(response, code, body) {
  response.writeHead(code, { 'Content-Type': 'application/json' });
  response.end(JSON.stringify(body));
}

function targetRequests(index) {
  return Object.fromEntries(walk(source.item[index].item).filter(item => !item.name.startsWith('Video ')).map(item => [item.name, item]));
}

async function main() {
  const historical = source.item.find(item => item.name === 'Server requests');
  const disabled = await run([historical], (_request, response) => json(response, 500, {}));
  assert.equal(disabled.calls, 0, 'Historical server must never reach HTTP');
  const writes = requests.filter(item => JSON.stringify(item.event).includes('enable_write_requests'));
  assert(writes.length > 0);
  const skipped = await run(writes, (_request, response) => json(response, 500, {}));
  assert.equal(skipped.calls, 0, 'Disabled writes must never reach HTTP');
  assert.equal(skipped.summary.run.failures.length, 0);

  let rotations = 0;
  let failedAuthChecks = 0;
  for (const [index, prefix] of ['localhost'].entries()) {
    const items = targetRequests(index);
    for (const environment of [false, true]) {
      let token = 0;
      let refresh = '';
      const sequence = [items['GET /v1/auth/me'], items['POST /v1/auth/local-select'], items['POST /v1/auth/refresh'], items['POST /v1/auth/refresh'], items['GET /v1/auth/me']];
      const result = await run(sequence, (request, response, raw) => {
        if (request.url === '/v1/auth/me') {
          return json(response, request.headers.authorization === 'Bearer access-' + token ? 200 : 401, { id: 'runtime-user' });
        }
        if (request.url === '/v1/auth/refresh' && JSON.parse(raw).refresh_token !== refresh) {
          return json(response, 401, { detail: 'Consumed refresh token' });
        }
        token++;
        refresh = 'refresh-' + token;
        json(response, 200, { access_token: 'access-' + token, refresh_token: refresh });
      }, { prefix, environment });
      assert.equal(result.summary.run.stats.items.total, 5);
      assert.equal(result.summary.run.failures.length, 0, 'Login/refresh kept a stale local token');
      assert.equal(token, 4, 'Expected automatic login, explicit login and two rotations');
      rotations++;
    }
    for (const failure of [401, 429, 503, 'invalid-json', 'missing-tokens', 'network']) {
      const result = await run([items['GET /v1/auth/me']], (request, response) => {
        assert.equal(request.url, '/v1/auth/local-select', 'Protected request escaped failed authentication');
        if (failure === 'network') return request.socket.destroy();
        if (failure === 'invalid-json') {
          response.writeHead(200, { 'Content-Type': 'application/json' });
          return response.end('not JSON');
        }
        json(response, typeof failure === 'number' ? failure : 200, {});
      }, { prefix });
      assert.equal(result.calls, 1);
      assert(result.summary.run.failures.some(f => f.error?.test === 'Authentication ready'), 'Authentication failure was silently skipped');
      failedAuthChecks++;
    }
    for (const body of [{}, null, { access_token: 'incomplete' }]) {
      const result = await run([items['POST /v1/auth/local-select']], (_request, response) => json(response, 200, body), { prefix });
      assert.equal(result.calls, 1);
      assert(result.summary.run.failures.some(f => f.error?.test === 'Session tokens returned'), 'Incomplete explicit login passed');
      failedAuthChecks++;
    }
    const health = items['GET /health/live'];
    for (const code of [200, 201, 302, 500]) {
      const result = await run([health], (_request, response) => json(response, code, {}), { prefix });
      assert.equal(result.summary.run.failures.length, code === 200 ? 0 : 1, 'Undeclared response status passed');
    }
  }
  console.log(`PASS: Newman sandbox; ${writes.length} disabled writes, ${rotations} login/rotation sequences, ${failedAuthChecks} reported authentication failures, exact response codes. Only local mock HTTP was used.`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
