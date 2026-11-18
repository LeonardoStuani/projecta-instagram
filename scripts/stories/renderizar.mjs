// Gera os PNGs 1080x1920 de uma semana de Stories a partir do stories.json dela.
// Uso (na raiz do projeto):  ferramentas\node\node.exe scripts/stories/renderizar.mjs posts/stories-2026-11-25
// Cada quadro com "tela" vira <pasta do dia>/<img>. Quadros "gravar" (o Leo grava) não geram imagem.
// No fim gera previa.png com todos os dias, para conferir de uma vez.
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const FERR = join(AQUI, "../../../../ferramentas");
const require = createRequire(import.meta.url);
const { chromium } = require(join(FERR, "node/node_modules/playwright-core"));

const semana = process.argv[2];
if (!semana) { console.error("Informe a pasta da semana, ex.: posts/stories-2026-11-25"); process.exit(1); }
const BASE = resolve(semana);
const S = JSON.parse(readFileSync(join(BASE, "stories.json"), "utf-8"));

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(AQUI, "modelo.html")).href);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });

const linhas = [];
for (const dia of S.dias) {
  const pasta = join(BASE, dia.pasta);
  mkdirSync(pasta, { recursive: true });
  const thumbs = [];
  for (const q of dia.quadros) {
    if (!q.tela) { thumbs.push({ gravar: q.texto || "" }); continue; }
    await page.evaluate(([t, a]) => window.montar(t, a), [q.tela, !!q.adesivo]);
    await page.waitForTimeout(80);
    const buf = await page.screenshot({ path: join(pasta, q.img) });
    thumbs.push({ src: "data:image/png;base64," + buf.toString("base64") });
    console.log(`${dia.pasta}/${q.img}`);
  }
  linhas.push({ t: `Dia ${dia.n} · ${dia.data.split("-").reverse().slice(0, 2).join("/")} · ${dia.titulo}`, thumbs });
}

// prévia: uma linha por dia
const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const html = `<body style="margin:0;padding:30px;background:#E7E4DB;font:600 22px system-ui;width:1240px">
${linhas.map(l => `<div style="margin-bottom:26px"><div style="margin-bottom:10px">${esc(l.t)}</div><div style="display:flex;gap:12px">
${l.thumbs.map(x => x.src ? `<img src="${x.src}" style="width:180px;height:320px;border-radius:10px">`
  : `<div style="width:180px;height:320px;border-radius:10px;background:#111110;color:#F3F1EA;font:500 15px system-ui;padding:14px;box-sizing:border-box"><b style="color:#F04E12">VOCÊ GRAVA</b><br><br>${esc(x.gravar)}</div>`).join("")}
</div></div>`).join("")}</body>`;
const prev = await browser.newPage({ viewport: { width: 1300, height: 800 } });
await prev.setContent(html);
await prev.screenshot({ path: join(BASE, "previa.png"), fullPage: true });
await browser.close();
console.log("previa.png");
