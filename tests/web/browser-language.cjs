// Real React DOM checks with isolated HTTP fixtures and simulated speech; no production account access.
const fs = require("fs"),
  path = require("path"),
  http = require("http"),
  { spawn } = require("child_process");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../..");
let account = "en";
const checks = [];
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (url.pathname.startsWith("/v1/")) {
    let raw = "";
    for await (const chunk of req) raw += chunk;
    const body = raw ? JSON.parse(raw) : {};
    res.setHeader("content-type", "application/json");
    if (url.pathname === "/v1/me/preferences") {
      if (req.method === "PATCH") account = body.preferred_language;
      return res.end(JSON.stringify({ preferred_language: account }));
    }
    if (url.pathname === "/v1/workspaces")
      return res.end(
        JSON.stringify([
          { id: "test-workspace", name: "QA workspace", role: "admin" },
        ]),
      );
    if (url.pathname === "/v1/queries") {
      if (body.question === "error") {
        res.statusCode = 503;
        return res.end(JSON.stringify({ detail: "Provider unavailable" }));
      }
      const language = body.language;
      let text =
        language === "en"
          ? "No verified evidence yet."
          : "Aún no hay evidencia verificada.";
      if (body.question === "slow")
        text =
          language === "en"
            ? "Old English result."
            : "Resultado anterior en español.";
      if (body.question === "slow")
        await new Promise((r) => setTimeout(r, 650));
      return res.end(
        JSON.stringify({
          found: false,
          ambiguous: false,
          message: text,
          tts_text: text,
          response_language: language,
          zone_path: [],
          simulated: true,
          highlight_quality: "none",
          segmentation_status: "not_requested",
          can_refine: false,
        }),
      );
    }
    return res.end("[]");
  }
  const app = url.pathname.startsWith("/display/")
    ? "display-webapp"
    : "frontend";
  const local = url.pathname.replace(/^\/display/, "");
  let file = path.join(root, app, "dist", local === "/" ? "index.html" : local);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory())
    file = path.join(root, app, "dist/index.html");
  res.setHeader(
    "content-type",
    file.endsWith(".js")
      ? "text/javascript"
      : file.endsWith(".css")
        ? "text/css"
        : "text/html",
  );
  fs.createReadStream(file).pipe(res);
});
(async () => {
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const httpPort = server.address().port;
  const profile = fs.mkdtempSync("/tmp/realityos-language-chrome-");
  const chrome = spawn(
    process.env.CHROMIUM_BINARY || "chromium",
    [
      "--headless",
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--remote-debugging-port=0",
      "--user-data-dir=" + profile,
      "--no-first-run",
      "about:blank",
    ],
    { stdio: "ignore" },
  );
  let ws;
  try {
    let targets;
    for (let i = 0; i < 80; i++) {
      try {
        const debugPort = fs
          .readFileSync(path.join(profile, "DevToolsActivePort"), "utf8")
          .split("\n")[0];
        targets = await (
          await fetch("http://127.0.0.1:" + debugPort + "/json/list")
        ).json();
        break;
      } catch {
        await new Promise((r) => setTimeout(r, 100));
      }
    }
    assert(targets, "Chromium did not start");
    ws = new WebSocket(
      targets.find((x) => x.type === "page").webSocketDebuggerUrl,
    );
    await new Promise((r) => ws.addEventListener("open", r, { once: true }));
    let next = 0;
    let pageLoaded;
    const pending = new Map();
    ws.addEventListener("message", (e) => {
      const data = JSON.parse(e.data);
      if (data.method === "Page.loadEventFired" && pageLoaded) {
        pageLoaded();
        pageLoaded = null;
      }
      if (data.id) {
        const pair = pending.get(data.id);
        if (pair) {
          pending.delete(data.id);
          data.error
            ? pair[1](new Error(JSON.stringify(data.error)))
            : pair[0](data.result);
        }
      }
    });
    const call = (method, params = {}) =>
      new Promise((resolve, reject) => {
        const id = ++next;
        pending.set(id, [resolve, reject]);
        ws.send(JSON.stringify({ id, method, params }));
      });
    const evaluate = async (expression) => {
      const result = await call("Runtime.evaluate", {
        expression,
        returnByValue: true,
        awaitPromise: true,
      });
      if (result.exceptionDetails)
        throw new Error(JSON.stringify(result.exceptionDetails));
      return result.result.value;
    };
    const waitFor = async (expression) => {
      for (let i = 0; i < 100; i++) {
        if (await evaluate(expression)) return;
        await new Promise((r) => setTimeout(r, 50));
      }
      throw new Error("Timed out: " + expression);
    };
    const navigate = async (route) => {
      const loaded = new Promise((resolve) => {
        pageLoaded = resolve;
      });
      await call("Page.navigate", {
        url: "http://127.0.0.1:" + httpPort + route,
      });
      await loaded;
      await waitFor(
        'Boolean(document.querySelector(".language-picker select"))',
      );
    };
    const select = async (lang) => {
      await evaluate(
        `(()=>{const s=document.querySelector('.language-picker select');s.value=${JSON.stringify(lang)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`,
      );
      await waitFor(`document.documentElement.lang===${JSON.stringify(lang)}`);
    };
    await call("Page.enable");
    await call("Runtime.enable");
    await call("Page.addScriptToEvaluateOnNewDocument", {
      source: `window.__spoken=[];window.SpeechSynthesisUtterance=class {constructor(text){this.text=text}};Object.defineProperty(window,'speechSynthesis',{value:{cancel(){},getVoices(){return [{lang:'en-US'},{lang:'es-CO'}]},speak(value){window.__spoken.push({text:value.text,language:value.lang})},addEventListener(){},removeEventListener(){}}});`,
    });
    for (const [app, route] of [
      ["frontend", "/"],
      ["display-webapp", "/display/"],
    ]) {
      account = "en";
      await navigate(route);
      await select("es");
      checks.push({
        app,
        case: "login switches to Spanish",
        passed: await evaluate(
          `Boolean(document.querySelector('input[aria-label="Correo electrónico"]'))||Array.from(document.querySelectorAll('label')).some(x=>x.textContent.includes('Correo electrónico'))`,
        ),
      });
      await select("en");
      checks.push({
        app,
        case: "login switches to English",
        passed: await evaluate(
          `Boolean(document.querySelector('input[aria-label="Email"]'))||Array.from(document.querySelectorAll('label')).some(x=>x.textContent.includes('Email'))`,
        ),
      });
      await evaluate(
        `localStorage.setItem('realityos.tokens',JSON.stringify({access_token:'qa-only',refresh_token:'qa-only'}));localStorage.setItem('realityos.display.token','qa-only');`,
      );
      await navigate(route);
      if (app === "frontend") {
        await waitFor('document.querySelectorAll(".rail .nav").length>2');
        await evaluate(
          `Array.from(document.querySelectorAll('.rail .nav')).find(x=>x.textContent==='Query').click()`,
        );
        await waitFor('Boolean(document.querySelector(".query form"))');
      }
      const form = app === "frontend" ? ".query form" : "form.question";
      const input = form + " input";
      await evaluate(
        `(()=>{const input=document.querySelector(${JSON.stringify(input)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,'draft typed by user');input.dispatchEvent(new Event('input',{bubbles:true}));})()`,
      );
      await select("es");
      const spanishExample = await evaluate(
        `document.querySelector(${JSON.stringify(input)}).placeholder === '¿Dónde está el taladro amarillo?'`,
      );
      await select("en");
      checks.push({
        app,
        case: "system example changes language while user draft is preserved",
        passed:
          spanishExample &&
          (await evaluate(
            `document.querySelector(${JSON.stringify(input)}).placeholder === 'Where is the yellow drill?' && document.querySelector(${JSON.stringify(input)}).value === 'draft typed by user'`,
          )),
      });
      const submit = async (question) => {
        await evaluate(
          `(()=>{const input=document.querySelector(${JSON.stringify(input)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(question)});input.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector(${JSON.stringify(form)}).dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));})()`,
        );
      };
      await submit("error");
      await new Promise((r) => setTimeout(r, 350));
      checks.push({
        app,
        case: "query failure is visible before a result",
        passed: await evaluate(
          'document.body.innerText.includes("Could not complete the request.")',
        ),
      });
      await submit("missing");
      await waitFor(
        'document.body.innerText.includes("No verified evidence yet.")',
      );
      const voice = app === "frontend" ? ".query .voice" : ".answer .listen";
      checks.push({
        app,
        case: "no-match answer can be spoken",
        passed: await evaluate(
          `Boolean(document.querySelector(${JSON.stringify(voice)})&&!document.querySelector(${JSON.stringify(voice)}).disabled)`,
        ),
      });
      await evaluate(
        `document.querySelector(${JSON.stringify(voice)})?.click()`,
      );
      await new Promise((r) => setTimeout(r, 50));
      checks.push({
        app,
        case: "English TTS matches displayed result",
        passed: await evaluate(
          'window.__spoken.some(x=>x.language==="en"&&x.text==="No verified evidence yet.")',
        ),
      });
      await select("es");
      await new Promise((r) => setTimeout(r, 50));
      await submit("missing");
      await waitFor(
        'document.body.innerText.includes("Aún no hay evidencia verificada.")',
      );
      checks.push({
        app,
        case: "Spanish answer and interface",
        passed: await evaluate(
          'document.body.innerText.includes("Buscar")&&document.documentElement.lang==="es"',
        ),
      });
      await select("en");
      await new Promise((r) => setTimeout(r, 50));
      checks.push({
        app,
        case: "previous-language answer cleared",
        passed: await evaluate(
          '!document.body.innerText.includes("Aún no hay evidencia verificada.")',
        ),
      });
      await submit("slow");
      await new Promise((r) => setTimeout(r, 80));
      await select("es");
      await new Promise((r) => setTimeout(r, 50));
      await submit("missing");
      await waitFor(
        'document.body.innerText.includes("Aún no hay evidencia verificada.")',
      );
      await new Promise((r) => setTimeout(r, 800));
      checks.push({
        app,
        case: "late previous-language response cannot replace the new answer",
        passed: await evaluate(
          '!document.body.innerText.includes("Old English result.")&&document.body.innerText.includes("Aún no hay evidencia verificada.")',
        ),
      });
      await select("en");
      await new Promise((r) => setTimeout(r, 50));
      await submit("slow");
      await new Promise((r) => setTimeout(r, 80));
      await submit("missing");
      await new Promise((r) => setTimeout(r, 850));
      checks.push({
        app,
        case: "older same-language request cannot replace the latest answer",
        passed: await evaluate(
          '!document.body.innerText.includes("Old English result.")&&document.body.innerText.includes("No verified evidence yet.")',
        ),
      });
      await evaluate("localStorage.clear()");
    }
    fs.writeFileSync(
      root + "/.runtime/language-second-pass-browser.json",
      JSON.stringify(
        {
          checks,
          passed: checks.filter((x) => x.passed).length,
          total: checks.length,
        },
        null,
        2,
      ),
    );
    console.log(
      JSON.stringify({
        browser_checks: checks.length,
        passed: checks.filter((x) => x.passed).length,
      }),
    );
    assert(
      checks.every((x) => x.passed),
      "Some browser checks failed",
    );
  } finally {
    ws?.close();
    chrome.kill();
    await new Promise((r) => server.close(r));
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
