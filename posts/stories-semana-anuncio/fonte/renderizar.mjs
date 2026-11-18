// Gera os PNGs 1080x1920 dos stories da semana do anúncio.
// Uso: node renderizar.mjs            (captura o site no ar e gera tudo)
//      node renderizar.mjs --sem-site (reaproveita site-celular.png)
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const FERR = join(AQUI, "../../../../../ferramentas");
const require = createRequire(import.meta.url);
const { chromium } = require(join(FERR, "node/node_modules/playwright-core"));

const PASTAS = { d1: "dia-1-site-novo", d2: "dia-2-google", d3: "dia-3-case-eixo-sul", d4: "dia-4-sabado", d5: "dia-5-respostas", d6: "dia-6-analise-gratuita" };
const browser = await chromium.launch({ channel: "msedge", headless: true, args: ["--allow-file-access-from-files"] });

if (!process.argv.includes("--sem-site")) {
  // print do site no ar, como aparece no celular (primeira tela)
  const ctx = await browser.newContext({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, reducedMotion: "reduce" });
  const p = await ctx.newPage();
  await p.goto("https://projectatech.com.br/", { waitUntil: "networkidle" });
  await p.waitForTimeout(1200);
  await p.screenshot({ path: join(AQUI, "site-celular.png") });
  await ctx.close();
  console.log("site capturado");
}

const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(AQUI, "stories.html")).href);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
const ids = await page.evaluate(() => window.QUADROS);
for (const id of ids) {
  const [dia, n] = id.split("-");
  const pasta = join(AQUI, "..", PASTAS[dia]);
  mkdirSync(pasta, { recursive: true });
  await page.evaluate((x) => window.mostrar(x), id);
  await page.waitForTimeout(120);
  await page.screenshot({ path: join(pasta, `${n}.png`) });
  console.log(`${PASTAS[dia]}/${n}.png`);
}
await browser.close();
