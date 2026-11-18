// Captura o site (http://localhost:3000) em tamanho de celular, em fatias de alta resolução.
// Uso: node capturar-site.mjs   (precisa do `npm run dev` rodando no site-projecta-tech)
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(join(dirname(fileURLToPath(import.meta.url)), "../../../../../ferramentas/node/node_modules/playwright-core"));

const AQUI = dirname(fileURLToPath(import.meta.url));
const OUT = join(AQUI, "assets");
const URL = process.env.SITE_URL || "http://localhost:3000/";
const W = 390, H = 844, DPR = 3, FATIA = 1800;
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DPR, isMobile: true, hasTouch: true, reducedMotion: "reduce", locale: "pt-BR" });
const page = await ctx.newPage();
await page.goto(URL, { waitUntil: "networkidle", timeout: 120000 });
await page.addStyleTag({ content: "nextjs-portal,[data-nextjs-toast],#__next-build-watcher{display:none!important}" });
await page.evaluate(() => document.fonts.ready);
// rola a página inteira para carregar imagens preguiçosas e disparar as revelações
const total0 = await page.evaluate(() => document.documentElement.scrollHeight);
for (let y = 0; y < total0; y += 500) { await page.evaluate((v) => window.scrollTo(0, v), y); await page.waitForTimeout(120); }
await page.evaluate(() => window.scrollTo(0, 0));
await page.waitForTimeout(800);

// cabeçalho e botão flutuante saem como camadas separadas (no vídeo ficam fixos sobre a rolagem)
await page.locator("header").first().screenshot({ path: join(OUT, "header.png") });
await page.locator('a[aria-label="Conversar no WhatsApp"]').first().screenshot({ path: join(OUT, "whats-float.png"), omitBackground: true });
const floatBox = await page.locator('a[aria-label="Conversar no WhatsApp"]').first().boundingBox();
const headerH = await page.evaluate(() => document.querySelector("header").getBoundingClientRect().height);
await page.addStyleTag({ content: 'header, a[aria-label="Conversar no WhatsApp"]{visibility:hidden!important}' });

// posições das seções que o vídeo visita (em px CSS)
const marcas = await page.evaluate(() => {
  const top = (el) => (el ? Math.round(el.getBoundingClientRect().top + window.scrollY) : null);
  const porTexto = (sel, txt) => [...document.querySelectorAll(sel)].find((e) => e.textContent.includes(txt));
  const sec = (el) => el?.closest("section");
  const zap = [...document.querySelectorAll("#comecar a")].find((a) => a.href.includes("wa.me"));
  return {
    servicos: top(document.querySelector("#servicos")),
    caseEixo: top(sec(porTexto("h2", "Eixo Sul"))),
    gestao: top(sec(porTexto("h2", "Um sistema pronto"))),
    comecar: top(document.querySelector("#comecar")),
    comecarBotao: top(zap),
    cta: top([...document.querySelectorAll("section.bg-accent")].pop()),
    total: document.documentElement.scrollHeight,
  };
});

const fatias = [];
for (let y = 0; y < marcas.total; y += FATIA) {
  const h = Math.min(FATIA, marcas.total - y);
  const nome = `site-${String(fatias.length).padStart(2, "0")}.png`;
  await page.screenshot({ path: join(OUT, nome), fullPage: true, clip: { x: 0, y, width: W, height: h } });
  fatias.push({ nome, y, h });
}
writeFileSync(join(OUT, "site.json"), JSON.stringify({ W, H, DPR, headerH, floatBox, marcas, fatias }, null, 2));
console.log(JSON.stringify({ headerH, floatBox, marcas, fatias: fatias.length }, null, 2));
await browser.close();
