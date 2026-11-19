// Abre uma janela do Edge com um perfil separado (ferramentas/perfil-sistema) para o Leo fazer login
// no projecta-demo.com.br. A senha não passa por aqui: só a sessão fica salva no perfil, para as capturas.
import { createRequire } from "node:module";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const PLANO = resolve(AQUI, "../../../..");
const require = createRequire(resolve(PLANO, "ferramentas/node/"));
const { chromium } = require("playwright-core");

const ctx = await chromium.launchPersistentContext(resolve(PLANO, "ferramentas/perfil-sistema"), {
  channel: "msedge", headless: false, viewport: null, args: ["--start-maximized"],
});
const p = ctx.pages()[0] || (await ctx.newPage());
await p.goto("https://projecta-demo.com.br/", { waitUntil: "domcontentloaded" });
console.log("Janela aberta. Aguardando o login (até 15 min)...");
const t0 = Date.now();
while (Date.now() - t0 < 15 * 60 * 1000) {
  const ok = await p.evaluate(() => /dashboard/i.test(document.body?.innerText || "") && !document.querySelector('input[type="password"]')).catch(() => false);
  if (ok) { console.log("LOGADO: " + new URL(p.url()).pathname); break; }
  await p.waitForTimeout(2000);
}
await p.waitForTimeout(3000);
await ctx.close();
console.log("Janela fechada, sessão salva no perfil.");
