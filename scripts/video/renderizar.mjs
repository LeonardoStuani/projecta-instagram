// Renderiza um vídeo HTML do kit (window.render(t)) em MP4 1080x1920, 30 fps, para Reels e Stories.
// Uso:
//   node scripts/video/renderizar.mjs <arquivo.html> <saida.mp4> [--q "id=3"] [--preview 0,2.5,8] [--audio trilha.wav] [--mudo]
// --preview salva só PNGs desses segundos ao lado da saída (para conferir antes de renderizar tudo).
// Áudio: usa --audio, ou sozinho o audio/mix.wav ao lado do HTML (saída do trilha.py).
// Sem áudio, PARA com erro: vídeo com texto na tela precisa de narração. --mudo só para Stories sem som.
import { createRequire } from "node:module";
import { mkdirSync, rmSync, mkdtempSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const AQUI = dirname(fileURLToPath(import.meta.url));
const FERR = resolve(AQUI, "../../../../ferramentas");
const require = createRequire(import.meta.url);
const { chromium } = require(join(FERR, "node/node_modules/playwright-core"));

const [html, saida] = process.argv.slice(2);
if (!html || !saida) { console.log("uso: node renderizar.mjs <arquivo.html> <saida.mp4> [--q \"id=3\"] [--preview 0,2,5]"); process.exit(1); }
const opt = (k) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : null; };
const FPS = 30;
const url = pathToFileURL(resolve(html)).href + "?export=1" + (opt("--q") ? "&" + opt("--q") : "");

const { existsSync } = await import("node:fs");
const AUDIO = opt("--audio") ? resolve(opt("--audio")) : existsSync(join(dirname(resolve(html)), "audio", "mix.wav")) ? join(dirname(resolve(html)), "audio", "mix.wav") : null;
if (!opt("--preview") && !AUDIO && !process.argv.includes("--mudo")) {
  console.error("Sem áudio: rode scripts/video/voz.py e trilha.py (geram fonte/audio/mix.wav) ou passe --audio <arquivo>. Use --mudo só se o vídeo for mesmo sem som.");
  process.exit(1);
}
if (AUDIO) console.log(`áudio: ${AUDIO}`);

const browser = await chromium.launch({ channel: "msedge", headless: true, args: ["--allow-file-access-from-files"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
const erros = [];
page.on("pageerror", (e) => erros.push(e.message));
await page.goto(url, { waitUntil: "load" });
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
await page.waitForTimeout(300);
if (erros.length) { console.error("Erro na página:", erros.join(" | ")); await browser.close(); process.exit(1); }
const DUR = await page.evaluate(() => window.DUR);

if (opt("--preview")) {
  const base = resolve(saida).replace(/\.mp4$/, "");
  for (const t of opt("--preview").split(",").map(Number)) {
    await page.evaluate((x) => window.render(x), t);
    await page.screenshot({ path: `${base}-preview-${t}s.png` });
  }
  console.log(`previews salvos (${DUR}s no total)`);
  await browser.close();
  process.exit(0);
}

const FR = mkdtempSync(join(tmpdir(), "video-"));
const n = Math.round(DUR * FPS);
for (let i = 0; i < n; i++) {
  await page.evaluate((x) => window.render(x), i / FPS);
  await page.screenshot({ path: join(FR, `${String(i).padStart(4, "0")}.jpg`), type: "jpeg", quality: 92 });
  if (i % 150 === 0) console.log(`quadro ${i}/${n}`);
}
await browser.close();

const ffmpeg = execFileSync(join(FERR, "python/python.exe"), ["-c", "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())"]).toString().trim();
mkdirSync(dirname(resolve(saida)), { recursive: true });
execFileSync(ffmpeg, ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", join(FR, "%04d.jpg"),
  ...(AUDIO ? ["-i", AUDIO, "-map", "0:v", "-map", "1:a", "-af", "apad"] : ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]), "-shortest",
  "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "19", "-r", String(FPS),
  "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", resolve(saida)], { stdio: "inherit" });
rmSync(FR, { recursive: true, force: true });
console.log(`MP4 pronto: ${saida} (${DUR}s)`);
