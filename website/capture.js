// Nimmt website/index.html mit Playwright auf (Texturen fuer Blender) und testet das Formular.
// Aufruf: node website/capture.js
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const DIR = __dirname;
const SHOTS = path.join(DIR, "shots");
const URL = "file://" + path.join(DIR, "index.html");
const DPR = 2;

const WIDTHS = {
  handy: { width: 390, height: 844 },
  tablet: { width: 820, height: 1180 },
  laptop: { width: 1440, height: 900 },
};

// Geruest: alles transparent, nur tuerkise 2-px-Rahmen um Abschnitte, Karten und Felder
const GERUEST_CSS = `
  *, *::before, *::after {
    color: transparent !important;
    background: transparent !important;
    box-shadow: none !important;
    border-color: transparent !important;
    text-shadow: none !important;
  }
  svg, input::placeholder { visibility: hidden !important; opacity: 0 !important; }
  .kopf, .hero, section, .karte, .zeiten, form, input, select, .knopf, .fuss, .danke {
    border: 2px solid #2EE6D6 !important;
  }
  input, select, .knopf { outline: none !important; }
`;

const SECTIONS = ["#kopf", "#hero", "#angebot", "#zeiten", "#bestellen", "#fuss"];

function mkdir(p) {
  fs.mkdirSync(p, { recursive: true });
}

async function boxes(page) {
  return page.evaluate((sel) => {
    const r = (el) => {
      const b = el.getBoundingClientRect();
      return { x: b.x + scrollX, y: b.y + scrollY, w: b.width, h: b.height };
    };
    const out = { page: { w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight } };
    sel.forEach((s) => (out[s.slice(1)] = r(document.querySelector(s))));
    out.karten = [...document.querySelectorAll(".karte")].map(r);
    out.felder = ["#name", "#anzahl", "#tag", "#senden"].map((s) => r(document.querySelector(s)));
    out.titel_angebot = r(document.querySelector("#angebot h2"));
    out.titel_bestellen = r(document.querySelector("#bestellen h2"));
    out.formular = r(document.querySelector("#formular"));
    return out;
  }, SECTIONS);
}

async function clip(page, file, b, omit) {
  const pad = 4;
  await page.screenshot({
    path: file,
    clip: { x: Math.max(0, b.x - pad), y: Math.max(0, b.y - pad), width: b.w + 2 * pad, height: b.h + 2 * pad },
    omitBackground: !!omit,
    fullPage: true,
  });
}

(async () => {
  mkdir(SHOTS);
  const browser = await chromium.launch();
  const meta = { dpr: DPR, breiten: {}, konsolenfehler: [] };

  for (const [name, vp] of Object.entries(WIDTHS)) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: DPR });
    const page = await ctx.newPage();
    page.on("console", (m) => m.type() === "error" && meta.konsolenfehler.push(`${name}: ${m.text()}`));
    page.on("pageerror", (e) => meta.konsolenfehler.push(`${name}: ${e.message}`));
    await page.goto(URL);
    // a) ganze Seite
    await page.screenshot({ path: path.join(SHOTS, `seite_${name}.png`), fullPage: true });
    await page.screenshot({ path: path.join(SHOTS, `viewport_${name}.png`) });
    const b = await boxes(page);
    meta.breiten[name] = { viewport: vp, boxen: b };

    if (name === "handy") {
      const d = path.join(SHOTS, "abschnitte");
      mkdir(d);
      // c) Abschnitte, Karten, Felder einzeln – gestylt
      const teile = { ...Object.fromEntries(SECTIONS.map((s) => [s.slice(1), b[s.slice(1)]])),
        titel_angebot: b.titel_angebot, titel_bestellen: b.titel_bestellen, formular: b.formular };
      b.karten.forEach((k, i) => (teile[`karte${String(i + 1).padStart(2, "0")}`] = k));
      ["name", "anzahl", "tag", "senden"].forEach((f, i) => (teile[`feld_${f}`] = b.felder[i]));
      for (const [k, box] of Object.entries(teile)) await clip(page, path.join(d, `stil_${k}.png`), box, false);
      // b) Geruest-Zustand
      await page.addStyleTag({ content: GERUEST_CSS });
      await page.screenshot({ path: path.join(SHOTS, `geruest_${name}.png`), fullPage: true, omitBackground: true });
      for (const [k, box] of Object.entries(teile)) await clip(page, path.join(d, `geruest_${k}.png`), box, true);
      meta.teile = teile;
    } else {
      await page.addStyleTag({ content: GERUEST_CSS });
      await page.screenshot({ path: path.join(SHOTS, `geruest_${name}.png`), fullPage: true, omitBackground: true });
    }
    await ctx.close();
  }

  // d) Formular-Sequenz (Handy): je ein Frame pro Buchstabe, Button gedrueckt, Bestaetigung
  {
    const ctx = await browser.newContext({ viewport: WIDTHS.handy, deviceScaleFactor: DPR });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => meta.konsolenfehler.push(`formular: ${e.message}`));
    page.on("console", (m) => m.type() === "error" && meta.konsolenfehler.push(`formular: ${m.text()}`));
    await page.goto(URL);
    const d = path.join(SHOTS, "formular");
    mkdir(d);
    let n = 0;
    const box = (await boxes(page)).bestellen;
    const snap = async (label) => {
      const file = `f${String(n).padStart(3, "0")}.png`;
      await clip(page, path.join(d, file), box, false);
      meta.formular = meta.formular || [];
      meta.formular.push({ datei: file, schritt: label });
      n++;
    };
    await snap("leer");
    await page.click("#name");
    for (const ch of "Anna") {
      await page.keyboard.type(ch);
      await snap(`name:${ch}`);
    }
    await page.click("#anzahl");
    await page.keyboard.type("2");
    await snap("anzahl:2");
    await page.selectOption("#tag", "Samstag");
    await snap("abholtag:Samstag");
    const btn = await page.$("#senden");
    const bb = await btn.boundingBox();
    await page.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2);
    await page.mouse.down();
    await page.waitForTimeout(200);
    await snap("button:gedrueckt");
    await page.mouse.up();
    await page.waitForTimeout(100);
    const sichtbar = await page.isVisible("#danke");
    const text = await page.textContent("#danke");
    await snap("bestaetigung");
    // Bestaetigungsansicht als Handy-Display (Szene 11)
    await page.evaluate(() => document.querySelector("#bestellen").scrollIntoView({ block: "center" }));
    await page.screenshot({ path: path.join(SHOTS, "handy_bestaetigung.png") });
    meta.formular_test = { bestaetigung_sichtbar: sichtbar, text: text.trim() };
    await ctx.close();
  }

  // Formular-Pruefung: leeres Absenden zeigt Fehlermeldung
  {
    const ctx = await browser.newContext({ viewport: WIDTHS.handy });
    const page = await ctx.newPage();
    await page.goto(URL);
    await page.click("#senden");
    meta.formular_test.leer_fehlermeldung = (await page.textContent("#fehler")).trim();
    await ctx.close();
  }

  await browser.close();
  const lines = fs.readFileSync(path.join(DIR, "index.html"), "utf8").split("\n");
  const metaPath = path.join(DIR, "meta.json");
  const old = fs.existsSync(metaPath) ? JSON.parse(fs.readFileSync(metaPath, "utf8")) : {};
  fs.writeFileSync(path.join(SHOTS, "boxen.json"), JSON.stringify(meta, null, 1));
  fs.writeFileSync(metaPath, JSON.stringify({ ...old, playwright: {
    konsolenfehler: meta.konsolenfehler, formular_test: meta.formular_test } }, null, 2) + "\n");
  console.log("Shots fertig:", JSON.stringify(meta.formular_test), "Konsolenfehler:", meta.konsolenfehler.length);
  if (meta.konsolenfehler.length || !meta.formular_test.bestaetigung_sichtbar) process.exit(1);
})();
