// Gera os PNGs transparentes (1080x1920) dos textos de um Reel de montagem, a partir de fonte/montagem.json.
// Uso: node scripts/video/rotulos.mjs clientes/<slug>/posts/<pasta>
// Modelo: clientes/<slug>/marca/rotulo.html (window.montar). Saída: fonte/rotulos/c01.png..., fim.png
// Normalmente chamado pelo scripts/video/montagem.py.
import { createRequire } from "node:module";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const { chromium } = require(join(AQUI, "../../../../ferramentas/node/node_modules/playwright-core"));

const BASE = resolve(process.argv[2] || "");
const M = JSON.parse(readFileSync(join(BASE, "fonte", "montagem.json"), "utf-8"));
const MODELO = resolve(BASE, "../../marca/rotulo.html");
if (!existsSync(MODELO)) { console.error("Falta marca/rotulo.html do cliente:", MODELO); process.exit(1); }
const OUT = join(BASE, "fonte", "rotulos");
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(MODELO).href);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
const itens = M.clipes.map((c, k) => [`c${String(k + 1).padStart(2, "0")}.png`, { texto: c.texto, sub: c.sub, pos: c.pos }]);
if (M.fim) itens.push(["fim.png", { fim: true, ...M.fim }]);
for (const [nome, t] of itens) {
  await page.evaluate((x) => window.montar(x), t);
  await page.waitForTimeout(60);
  await page.screenshot({ path: join(OUT, nome), omitBackground: true });
  console.log(nome);
}
await browser.close();
