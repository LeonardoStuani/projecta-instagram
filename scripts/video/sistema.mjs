// Entra no projecta-demo.com.br (base de demonstração) com um perfil separado e captura telas para os Reels.
// Credenciais só por variável de ambiente (SIS_EMAIL, SIS_SENHA), nunca em arquivo.
// Uso: node scripts/video/sistema.mjs explorar <pasta-saida>
import { createRequire } from "node:module";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdirSync, writeFileSync } from "node:fs";

const AQUI = dirname(fileURLToPath(import.meta.url));
const PLANO = resolve(AQUI, "../../../..");
const require = createRequire(resolve(PLANO, "ferramentas/node") + "/");
const { chromium } = require("playwright-core");

export async function abrir({ largura = 1440, altura = 900, escala = 2 } = {}) {
  const ctx = await chromium.launchPersistentContext(resolve(PLANO, "ferramentas/perfil-sistema"), {
    channel: "msedge", headless: true, viewport: { width: largura, height: altura }, deviceScaleFactor: escala,
  });
  const p = ctx.pages()[0] || (await ctx.newPage());
  await p.goto("https://projecta-demo.com.br/", { waitUntil: "networkidle" });
  if (await p.$('input[type="password"]')) {
    if (!process.env.SIS_EMAIL || !process.env.SIS_SENHA) throw new Error("Defina SIS_EMAIL e SIS_SENHA.");
    await p.fill('input[type="email"], input[name="email"], input[type="text"]', process.env.SIS_EMAIL);
    await p.fill('input[type="password"]', process.env.SIS_SENHA);
    await p.keyboard.press("Enter");
    await p.waitForLoadState("networkidle");
    await p.waitForTimeout(2500);
  }
  return { ctx, p };
}

/** Esconde o nome do cliente (Eixo Sul) e e-mails reais antes de qualquer captura. */
export async function limpar(p) {
  await p.evaluate(() => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n; (n = w.nextNode()); ) {
      n.nodeValue = n.nodeValue
        .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, (m) => (m.startsWith("admin") ? "admin@empresa.com.br" : "usuario@empresa.com.br"))
        .replace(/eixo\s*sul( engenharia)?/gi, "Sua Empresa")
        .replace(/leo teste/gi, "Cliente 8").replace(/maria/gi, "Cliente 5").replace(/gustavo/gi, "Cliente 9").replace(/joão/gi, "Cliente 6");
    }
    document.querySelectorAll("input").forEach((i) => { if (/eixo|@/.test(i.value)) i.value = ""; });
  });
}

if (process.argv[2] === "capturar") {
  const out = resolve(process.argv[3]);
  mkdirSync(out, { recursive: true });
  const { ctx, p } = await abrir();
  const rotas = ["dashboard", "clients", "budgets", "projects", "financial", "auditoria", "users"];
  const info = {};
  for (const r of rotas) {
    await p.click(`a[href="/${r}"]`);
    await p.waitForLoadState("networkidle");
    await p.waitForTimeout(2500);
    await limpar(p);
    await p.screenshot({ path: join(out, `${r}.png`), fullPage: true });
    info[r] = await p.$$eval("button, a, h1, h2, h3, th", (els) => [...new Set(els.map((e) => (e.innerText || e.title || e.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").slice(0, 50)).filter(Boolean))]);
    console.log(r, "ok");
  }
  writeFileSync(join(out, "info.json"), JSON.stringify(info, null, 1));
  await ctx.close();
}

if (process.argv[2] === "detalhe") {
  const out = resolve(process.argv[3]);
  const { ctx, p } = await abrir();
  await p.click('a[href="/projects"]');
  await p.waitForLoadState("networkidle");
  await p.waitForTimeout(2000);
  await p.locator("tbody tr").first().locator("button").first().click();
  await p.waitForLoadState("networkidle");
  await p.waitForTimeout(2500);
  await limpar(p);
  await p.screenshot({ path: join(out, "projeto.png"), fullPage: true });
  const txt = await p.evaluate(() => document.body.innerText.replace(/\s+/g, " ").slice(0, 1500));
  console.log(p.url(), txt);
  await ctx.close();
}

if (process.argv[2] === "explorar") {
  const out = resolve(process.argv[3]);
  mkdirSync(out, { recursive: true });
  const { ctx, p } = await abrir({ escala: 1 });
  await p.screenshot({ path: join(out, "00-inicio.png") });
  const links = await p.$$eval("a, button", (els) =>
    els.map((e) => ({ t: (e.innerText || "").trim().slice(0, 40), href: e.getAttribute("href") })).filter((x) => x.t));
  writeFileSync(join(out, "links.json"), JSON.stringify({ url: p.url(), links }, null, 1));
  console.log(p.url());
  console.log(links.map((l) => `${l.t} -> ${l.href ?? ""}`).join("\n"));
  await ctx.close();
}
