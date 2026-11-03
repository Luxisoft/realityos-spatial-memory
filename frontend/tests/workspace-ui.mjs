// Isolated browser regression: all API responses are synthetic; no real accounts or mail.
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, resolve, extname } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const fixture = JSON.parse(
  await readFile(resolve(root, "simulator/workspaces/hospital.json"), "utf8"),
);
const people = fixture.batch.records.filter((r) => r.kind === "person");
const rows = Array.from({ length: 51 }, (_, i) => ({
  ...people[i % people.length],
  id: `test-${i}`,
  title: i < 2 ? people[i].title : `Synthetic record ${i}`,
  external_id: `test-${i}`,
  data: {},
  version: 1,
}));
let role = "query",
  heldPhoto = null,
  heldNote = null;
const apiCalls = [];
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://localhost");
    const send = (value) => {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(value));
    };
    if (url.pathname.startsWith("/v1/")) {
      apiCalls.push(url.pathname + url.search);
      assert.equal(req.headers.authorization, "Bearer synthetic-browser-token");
      if (url.pathname === "/v1/me/preferences")
        return send({ preferred_language: "en" });
      if (url.pathname === "/v1/workspaces")
        return send([{ id: "work", name: "Synthetic clinic", role }]);
      if (url.pathname.endsWith("/connections")) return send([]);
      if (url.pathname.endsWith("/records"))
        return send(
          rows.slice(
            Number(url.searchParams.get("offset") || 0),
            Number(url.searchParams.get("offset") || 0) + 50,
          ),
        );
      if (url.pathname.endsWith("/record-media/photo")) {
        heldPhoto = res;
        return;
      }
      if (url.pathname.endsWith("/records/test-0/notes")) {
        heldNote = res;
        return;
      }
      const id = url.pathname.split("/").at(-1);
      const record = rows.find((r) => r.id === id);
      if (record)
        return send({
          ...record,
          related: [],
          notes: [],
          media:
            id === "test-0"
              ? [
                  {
                    id: "photo",
                    mime_type: "image/png",
                    url: "/v1/workspaces/work/record-media/photo",
                  },
                ]
              : [],
        });
      res.writeHead(404);
      res.end();
      return;
    }
    const path = resolve(
      root,
      "frontend/dist",
      url.pathname === "/" ? "index.html" : url.pathname.slice(1),
    );
    if (!path.startsWith(resolve(root, "frontend/dist") + "/")) {
      res.writeHead(404);
      res.end();
      return;
    }
    res.setHeader(
      "Content-Type",
      { ".html": "text/html", ".js": "text/javascript", ".css": "text/css" }[
        extname(path)
      ] || "application/octet-stream",
    );
    res.end(await readFile(path));
  } catch (error) {
    res.writeHead(500);
    res.end(String(error));
  }
});
await new Promise((done) => server.listen(0, "127.0.0.1", done));
const executablePath =
  process.env.CHROMIUM_BIN ||
  [
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
  ].find(existsSync);
assert.ok(
  executablePath,
  "Set CHROMIUM_BIN to an installed Chromium/Chrome browser",
);
const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.setViewport({ width: 1440, height: 1000 });
await page.evaluateOnNewDocument(() =>
  localStorage.setItem(
    "realityos.tokens",
    JSON.stringify({
      access_token: "synthetic-browser-token",
      refresh_token: "synthetic-refresh",
    }),
  ),
);
const click = async (text) => {
  await page.waitForFunction(
    (text) =>
      [...document.querySelectorAll("button")].some(
        (b) => b.textContent.trim() === text && !b.disabled,
      ),
    {},
    text,
  );
  await page.evaluate(
    (text) =>
      [...document.querySelectorAll("button")]
        .find((b) => b.textContent.trim() === text)
        .click(),
    text,
  );
};
const choose = async (name) => {
  await page.waitForFunction(
    (name) =>
      [
        ...document.querySelectorAll(".record-layout > div > button strong"),
      ].some((b) => b.textContent === name),
    {},
    name,
  );
  await page.evaluate(
    (name) =>
      [...document.querySelectorAll(".record-layout > div > button")]
        .find((b) => b.querySelector("strong")?.textContent === name)
        .click(),
    name,
  );
  await page.waitForFunction(
    (name) => document.querySelector("article h2")?.textContent === name,
    {},
    name,
  );
};
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/`, {
    waitUntil: "networkidle0",
  });
  await click("Workspace records");
  await page.waitForFunction(
    () =>
      document.querySelectorAll(".record-layout > div > button").length === 50,
  );
  await click("Next records");
  await page.waitForFunction(
    () =>
      document.querySelectorAll(".record-layout > div > button").length === 1,
  );
  assert.ok(apiCalls.some((path) => path.includes("offset=50")));
  await click("Previous records");
  await choose(people[0].title);
  assert.equal(
    await page.$$("article textarea").then((v) => v.length),
    0,
    "Read-only role must not show a note editor",
  );
  await click("Open attachment");
  for (let i = 0; !heldPhoto && i < 50; i++)
    await new Promise((r) => setTimeout(r, 20));
  assert.ok(heldPhoto, "Photo request must be pending");
  await choose(people[1].title);
  const received = page.waitForResponse((r) =>
    r.url().endsWith("/record-media/photo"),
  );
  heldPhoto.writeHead(200, { "Content-Type": "image/png" });
  heldPhoto.end(
    await readFile(
      resolve(root, "simulator/workspaces/assets/patient-ana.png"),
    ),
  );
  heldPhoto = null;
  await received;
  await page.waitForNetworkIdle({ idleTime: 500 });
  assert.equal(
    await page.$$("article img").then((v) => v.length),
    0,
    "Late photo from previous patient must not appear",
  );
  role = "admin";
  await page.reload({ waitUntil: "networkidle0" });
  await click("Workspace records");
  await choose(people[0].title);
  assert.equal(
    await page.$$("article textarea").then((v) => v.length),
    1,
    "Writable role should have note editor",
  );
  await page.type("article textarea", "Synthetic note for first patient");
  await click("Save note");
  for (let i = 0; !heldNote && i < 50; i++)
    await new Promise((r) => setTimeout(r, 20));
  assert.ok(heldNote, "Note save must be pending");
  await page.type("section > label input", people[1].title);
  await choose(people[1].title);
  await page.type("article textarea", "Draft for second patient");
  const saved = page.waitForResponse((r) => r.url().endsWith("/test-0/notes"));
  heldNote.writeHead(200, { "Content-Type": "application/json" });
  heldNote.end("{}");
  heldNote = null;
  await saved;
  await page.waitForNetworkIdle({ idleTime: 500 });
  assert.equal(
    await page.$eval("article h2", (n) => n.textContent),
    people[1].title,
  );
  assert.equal(
    await page.$eval("article textarea", (n) => n.value),
    "Draft for second patient",
    "Saving a previous patient's note must preserve current patient and draft",
  );
  await page.setViewport({ width: 390, height: 844 });
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    "Record view must fit mobile width",
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS: 51-record pagination, role-aware notes, stale patient photo/note rejection, mobile layout. Synthetic API only.",
  );
} finally {
  if (heldPhoto) heldPhoto.end();
  if (heldNote) heldNote.end();
  await browser.close();
  server.closeAllConnections();
  await new Promise((done) => server.close(done));
}
