// Gera os slides 1080x1350 de um carrossel a partir de posts/<pasta>/slides.json.
// Uso (na raiz do projeto):  node scripts/carrossel/renderizar.mjs posts/11-planilha-de-uma-pessoa
// Saída: slide-01.png, slide-02.png… na mesma pasta, e previa.png com todos lado a lado.
// Depois: python scripts/ig.py preparar posts/<pasta> --data AAAA-MM-DD --hora 18:00 --pilar dica
import { createRequire } from "node:module";
import { readFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const { chromium } = require(join(AQUI, "../../../../ferramentas/node/node_modules/playwright-core"));

const pasta = process.argv[2];
if (!pasta) { console.error("Informe a pasta do post, ex.: posts/11-planilha-de-uma-pessoa"); process.exit(1); }
const BASE = resolve(pasta);
const { slides } = JSON.parse(readFileSync(join(BASE, "slides.json"), "utf-8"));

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
// Cliente da agência: clientes/<slug>/marca/modelo.html (identidade do cliente) substitui o modelo da Projecta.
const MARCA = resolve(BASE, "../../marca/modelo.html");
const MODELO = /[\\/]clientes[\\/][^\\/]+[\\/]posts[\\/]/.test(BASE) && existsSync(MARCA) ? MARCA : join(AQUI, "modelo.html");
if (MODELO !== join(AQUI, "modelo.html")) console.log("Identidade do cliente:", MODELO);
await page.goto(pathToFileURL(MODELO).href);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
const thumbs = [];
for (let i = 0; i < slides.length; i++) {
  await page.evaluate(([t, n, tot]) => window.montar(t, n, tot), [slides[i], i + 1, slides.length]);
  await page.waitForTimeout(80);
  // texto não pode invadir o rodapé
  const estouro = await page.evaluate(() => { const b = document.querySelector(".box"); return b.scrollHeight > b.clientHeight + 2; });
  if (estouro) console.warn(`ATENÇÃO: slide ${i + 1} tem texto demais (passa da área útil).`);
  const nome = `slide-${String(i + 1).padStart(2, "0")}.png`;
  const buf = await page.screenshot({ path: join(BASE, nome) });
  thumbs.push("data:image/png;base64," + buf.toString("base64"));
  console.log(nome);
}
const prev = await browser.newPage({ viewport: { width: 1400, height: 400 } });
await prev.setContent(`<body style="margin:0;padding:24px;background:#D9D5CA;display:flex;flex-wrap:wrap;gap:14px;width:1352px">
${thumbs.map(s => `<img src="${s}" style="width:320px;height:400px">`).join("")}</body>`);
await prev.screenshot({ path: join(BASE, "previa.png"), fullPage: true });
await browser.close();
console.log("previa.png");
