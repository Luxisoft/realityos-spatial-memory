// Authenticate on Send using this target's configured account and API.
// https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-send-request/
(function () {
  const origin = String(pm.variables.get("base_url") || "").replace(/\/$/, "");
  const email = pm.variables.get("email");
  const identity = JSON.stringify([origin, email]);
  const sameAccount = pm.variables.get("session_identity") === identity;
  const access = sameAccount ? pm.variables.get("access_token") : "";
  const refresh = sameAccount ? pm.variables.get("refresh_token") : "";

  function fail(message) {
    pm.execution.skipRequest();
    throw new Error(message);
  }

  function save(response) {
    let body;
    try { body = response.json(); } catch (_) { fail("Authentication returned invalid JSON."); }
    if (!body || typeof body.access_token !== "string" || !body.access_token ||
        typeof body.refresh_token !== "string" || !body.refresh_token) {
      fail("Authentication did not return both session tokens.");
    }
    pm.collectionVariables.set("access_token", body.access_token);
    pm.collectionVariables.set("refresh_token", body.refresh_token);
    pm.collectionVariables.set("session_identity", identity);
    if (pm.environment.has("access_token")) pm.environment.set("access_token", body.access_token);
    if (pm.environment.has("refresh_token")) pm.environment.set("refresh_token", body.refresh_token);
    if (pm.environment.has("session_identity")) pm.environment.set("session_identity", identity);
    pm.variables.set("access_token", body.access_token);
    pm.variables.set("refresh_token", body.refresh_token);
    pm.variables.set("session_identity", identity);
  }

  function post(path, body, done) {
    pm.sendRequest({
      url: origin + path,
      method: "POST",
      header: { "Content-Type": "application/json" },
      body: { mode: "raw", raw: JSON.stringify(body) }
    }, done);
  }

  function login() {
    post("/v1/auth/login", { email, password: pm.variables.get("password") }, (error, response) => {
      if (error || !response) fail("Automatic login could not reach the configured API.");
      if (response.code !== 200) fail("Automatic login failed (HTTP " + response.code + ").");
      save(response);
    });
  }

  function renew() {
    if (!refresh) return login();
    post("/v1/auth/refresh", { refresh_token: refresh }, (error, response) => {
      if (error || !response) fail("Automatic refresh could not reach the configured API.");
      if (response.code === 401) return login();
      if (response.code !== 200) fail("Automatic refresh failed (HTTP " + response.code + ").");
      save(response);
    });
  }

  if (!access) return renew();
  pm.sendRequest({
    url: origin + "/v1/auth/me",
    method: "GET",
    header: { Authorization: "Bearer " + access }
  }, (error, response) => {
    if (error || !response) fail("Session validation could not reach the configured API.");
    if (response.code === 401) return renew();
    if (response.code !== 200) fail("Session validation failed (HTTP " + response.code + ").");
  });
})();
