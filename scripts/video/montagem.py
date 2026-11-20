"""Reel de MONTAGEM: corta vídeos/fotos reais do cliente, põe os textos da marca por cima, cartela final
e trilha original (batida sintetizada do trilha.py, sem música de terceiros) mixada com o som original dos vídeos.

Uso: python scripts/video/montagem.py clientes/<slug>/posts/<pasta>
Lê  <pasta>/fonte/montagem.json:
  {"nome": "reel-voltei", "bpm": 104, "som_original": 0.7, "musica": 0.5,
   "clipes": [{"arq": "acervo/x.mp4", "ini": 1.2, "dur": 2.4, "texto": "Sumi por *2 anos*…", "sub": "...", "pos": "topo"},
              {"arq": "acervo/foto.jpg", "dur": 2.0, "texto": "..."}],          # foto = zoom lento
   "fim": {"titulo": "Me segue pra mais rotina de *Spitz*!", "sub": "...", "dur": 2.6}}
Caminhos de "arq" são relativos a clientes/<slug>/media/. Textos: marca/rotulo.html do cliente (via rotulos.mjs).
Gera <pasta>/<nome>.mp4 (1080x1920, 30 fps). Depois: ig.py --cliente <slug> preparar <pasta> ...
"""
import json, os, re, shutil, subprocess, sys
import numpy as np
import soundfile as sf
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
AQUI = os.path.dirname(os.path.abspath(__file__))
pasta = os.path.abspath(sys.argv[1])
fonte = os.path.join(pasta, "fonte")
media = os.path.abspath(os.path.join(pasta, "..", "..", "media"))
M = json.load(open(os.path.join(fonte, "montagem.json"), encoding="utf-8"))
tmp = os.path.join(fonte, "seg")
shutil.rmtree(tmp, ignore_errors=True)
os.makedirs(tmp)


def run(args):
    r = subprocess.run([FF, "-y", "-loglevel", "error", *args], capture_output=True, text=True, errors="ignore")
    if r.returncode:
        sys.exit("ffmpeg falhou: " + r.stderr[-800:])


def tem_audio(f):
    o = subprocess.run([FF, "-i", f], capture_output=True, text=True, errors="ignore").stderr
    return "Audio:" in o


# 1) rótulos (PNG transparentes) com a identidade do cliente
node = shutil.which("node") or "node"
r = subprocess.run([node, os.path.join(AQUI, "rotulos.mjs"), pasta], capture_output=True, text=True, errors="ignore")
if r.returncode:
    sys.exit("rotulos.mjs falhou: " + r.stderr[-800:])

COVER = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
segs, auds, cortes, t = [], [], [], 0.0
itens = list(enumerate(M["clipes"], 1))
if M.get("fim"):
    itens.append((0, {"arq": None, "dur": M["fim"].get("dur", 2.6)}))
for k, c in itens:
    dur = float(c["dur"])
    nfr = round(dur * 30)
    out = os.path.join(tmp, f"s{len(segs):02d}.mp4")
    rot = os.path.join(fonte, "rotulos", f"c{k:02d}.png" if k else "fim.png")
    if not k:  # cartela final: imagem opaca com zoom leve
        src, foto = rot, True
    else:
        src = os.path.join(media, c["arq"])
        foto = src.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    zoom = f"scale=w='trunc(1080*(1+0.07*t/{dur})/2)*2':h='trunc(1920*(1+0.07*t/{dur})/2)*2':eval=frame,crop=1080:1920"
    if foto:
        entrada = ["-loop", "1", "-framerate", "30", "-t", f"{dur}", "-i", src]
        vf = f"[0:v]{COVER},{zoom},fps=30,format=yuv420p[b]"
    else:
        entrada = ["-ss", f"{c.get('ini', 0)}", "-t", f"{dur}", "-i", src]
        vf = f"[0:v]{COVER},fps=30,format=yuv420p[b]"
    if k:
        entrada += ["-loop", "1", "-framerate", "30", "-t", f"{dur}", "-i", rot]
        vf += ";[1:v]format=rgba,fade=in:st=0.12:d=0.22:alpha=1[r];[b][r]overlay=0:0:format=auto,format=yuv420p[v]"
    else:
        vf += ";[b]null[v]"
    run([*entrada, "-filter_complex", vf, "-map", "[v]", "-frames:v", str(nfr), "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out])
    segs.append(out)
    # som original do trecho (ou silêncio)
    n = int(nfr / 30 * SR)
    a = np.zeros((n, 2), "float32")
    if k and not foto and tem_audio(src):
        w = os.path.join(tmp, f"a{len(auds):02d}.wav")
        run(["-ss", f"{c.get('ini', 0)}", "-t", f"{dur}", "-i", src, "-vn", "-ac", "2", "-ar", str(SR), w])
        x, _ = sf.read(w, dtype="float32")
        x = x.reshape(-1, 2)[:n]
        a[: len(x)] = x
        f = int(SR * 0.06)
        a[:f] *= np.linspace(0, 1, f)[:, None]
        a[-f:] *= np.linspace(1, 0, f)[:, None]
    auds.append(a)
    cortes.append(t)
    t += nfr / 30

total = round(t, 3)
# 2) junta os vídeos
lista = os.path.join(tmp, "lista.txt")
open(lista, "w", encoding="utf-8").write("".join(f"file '{s.replace(os.sep, '/')}'\n" for s in segs))
mudo = os.path.join(fonte, "mudo.mp4")
run(["-f", "concat", "-safe", "0", "-i", lista, "-vf", "scale=in_range=auto:out_range=tv,format=yuv420p", "-r", "30",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-color_range", "tv", mudo])

# 3) trilha original (trilha.py sem falas) com whoosh nos cortes
rot = {"bpm": M.get("bpm", 104), "fim": total, "drop": M.get("drop", 0.0), "falas": [],
       "sfx": [{"t": round(x, 2), "tipo": "whoosh", "g": 0.35} for x in cortes[1:]] + ([{"t": round(cortes[-1], 2), "tipo": "ding", "g": 0.5}] if M.get("fim") else []),
       "corte_batida": round(cortes[-1], 2) if M.get("fim") else None}
json.dump(rot, open(os.path.join(fonte, "roteiro.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
r = subprocess.run([sys.executable, os.path.join(AQUI, "trilha.py"), pasta], capture_output=True, text=True, errors="ignore")
if r.returncode:
    sys.exit("trilha.py falhou: " + r.stderr[-800:])
mus, _ = sf.read(os.path.join(fonte, "audio", "mix.wav"), dtype="float32")
orig = np.concatenate(auds)
N = min(len(orig), len(mus))
o = orig[:N]
o = o / (np.abs(o).max() + 1e-9) if np.abs(o).max() > 0 else o
mix = o * M.get("som_original", 0.7) + mus[:N, None] * M.get("musica", 0.5)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
final_wav = os.path.join(fonte, "audio", "final.wav")
sf.write(final_wav, mix, SR)

# 4) vídeo final
nome = M.get("nome") or "reel"
saida = os.path.join(pasta, nome + ".mp4")
for f in os.listdir(pasta):  # só um .mp4 na pasta (o preparar pega o primeiro)
    if f.endswith(".mp4"):
        os.remove(os.path.join(pasta, f))
run(["-i", mudo, "-i", final_wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
     "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart", saida])
shutil.rmtree(tmp, ignore_errors=True)
print(f"{os.path.relpath(saida)} · {total}s · {len(M['clipes'])} trechos")
