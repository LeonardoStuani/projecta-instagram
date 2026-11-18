// Grava o reel.html quadro a quadro (30 fps) e gera o MP4 1080x1920 para o Instagram.
// Uso: node renderizar.mjs [--preview 0,3,10.5]   (preview salva só alguns quadros PNG)
import { createRequire } from "node:module";
import { mkdirSync, rmSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const AQUI = dirname(fileURLToPath(import.meta.url));
const FERR = join(AQUI, "../../../../../ferramentas");
const require = createRequire(import.meta.url);
const { chromium } = require(join(FERR, "node/node_modules/playwright-core"));
const FPS = 30, DUR = 25.5;
const FRAMES = process.env.REEL_FRAMES || join(AQUI, "frames");
const OUT = join(AQUI, "..", "reel-site-novo.mp4");
const arg = process.argv.indexOf("--preview");

const browser = await chromium.launch({ channel: "msedge", headless: true, args: ["--allow-file-access-from-files"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(AQUI, "reel.html")).href);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
await page.waitForTimeout(500);

if (arg > -1) {
  const ts = process.argv[arg + 1].split(",").map(Number);
  mkdirSync(FRAMES, { recursive: true });
  for (const t of ts) { await page.evaluate((x) => window.render(x), t); await page.screenshot({ path: join(FRAMES, `preview-${t}.png`) }); }
  console.log("previews em", FRAMES);
  await browser.close(); process.exit(0);
}

if (existsSync(FRAMES)) rmSync(FRAMES, { recursive: true });
mkdirSync(FRAMES, { recursive: true });
const n = Math.round(DUR * FPS);
for (let i = 0; i < n; i++) {
  await page.evaluate((x) => window.render(x), i / FPS);
  await page.screenshot({ path: join(FRAMES, `${String(i).padStart(4, "0")}.jpg`), type: "jpeg", quality: 93 });
  if (i % 90 === 0) console.log(`quadro ${i}/${n}`);
}
await browser.close();

const ffmpeg = execFileSync(join(FERR, "python/python.exe"), ["-c", "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())"]).toString().trim();
execFileSync(ffmpeg, ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", join(FRAMES, "%04d.jpg"),
  "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
  "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18", "-r", String(FPS),
  "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT], { stdio: "inherit" });
console.log("MP4 pronto:", OUT);
