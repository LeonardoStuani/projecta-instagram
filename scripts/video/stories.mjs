// Gera os vídeos animados dos quadros "gravar" de uma semana de stories (campo "animado" no stories.json)
// e grava o caminho do MP4 em "video". Uso:
//   node scripts/video/stories.mjs posts/stories-2026-11-25 [--desde 2026-11-19] [--preview]
import { readFileSync, writeFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, "../..");
const pasta = process.argv[2];
const opt = (k) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : null; };
const desde = opt("--desde") || "0000-00-00";
const arq = join(RAIZ, pasta, "stories.json");
const st = JSON.parse(readFileSync(arq, "utf8"));

for (const dia of st.dias) {
  if (dia.data < desde) continue;
  for (const q of dia.quadros) {
    if (!q.animado) continue;
    const a = q.animado;
    const qs = new URLSearchParams({ m: a.m, t: a.t, tema: a.tema || "escuro", ...(a.img ? { img: a.img } : {}) }).toString();
    const nome = `dia-${dia.n}-q${q.n}.mp4`;
    const saida = join(RAIZ, pasta, nome);
    const args = [join(AQUI, "renderizar.mjs"), join(AQUI, "story.html"), saida, "--q", qs];
    if (process.argv.includes("--preview")) args.push("--preview", "4");
    console.log(`${dia.data} quadro ${q.n}: ${a.m}`);
    execFileSync(process.execPath, args, { stdio: "inherit" });
    if (!process.argv.includes("--preview")) q.video = `${pasta}/${nome}`.replace(/\\/g, "/");
  }
}
if (!process.argv.includes("--preview")) {
  writeFileSync(arq, JSON.stringify(st, null, 2) + "\n", "utf8");
  console.log("stories.json atualizado");
}
