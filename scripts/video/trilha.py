"""Monta a trilha de um Reel narrado: voz (falas do Kokoro em fonte/voz/l1..lN.wav), batida original
sintetizada (sem música de terceiros), efeitos (whoosh, clique, impacto, subida) e legendas palavra a palavra.

Uso: python scripts/video/trilha.py posts/<pasta>
Lê  posts/<pasta>/fonte/roteiro.json  {"bpm", "fim", "falas":[{"t":inicio,"texto"}], "sfx":[{"t","tipo"}], "drop"}
Gera posts/<pasta>/fonte/audio/mix.wav e posts/<pasta>/fonte/legendas.json (palavras com início e fim).
"""
import json, os, sys
import numpy as np
import soundfile as sf

SR = 48000
rng = np.random.default_rng(7)
pasta = sys.argv[1]
fonte = os.path.join(pasta, "fonte")
rot = json.load(open(os.path.join(fonte, "roteiro.json"), encoding="utf-8"))
N = int(rot["fim"] * SR)


def carregar(caminho):
    x, sr = sf.read(caminho, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:  # reamostragem linear (suficiente para voz)
        t = np.arange(int(len(x) * SR / sr)) / SR
        x = np.interp(t, np.arange(len(x)) / sr, x).astype("float32")
    return x


def por(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    buf[i : i + len(x)] += x * g


# ---------- voz + legendas ----------
voz = np.zeros(N, "float32")
legendas = []
for k, f in enumerate(rot["falas"], 1):
    x = carregar(os.path.join(fonte, "voz", f"l{k}.wav"))
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    por(voz, x, f["t"])
    # tempo de cada palavra proporcional ao tamanho, com pausa extra depois de pontuação
    ws = f["texto"].split()
    pesos = [len(w.strip(",.?!:")) + 2 + (3 if w[-1] in ",.?!:" else 0) for w in ws]
    dur = len(x) / SR
    # tira o silêncio do começo e do fim da fala
    env = np.abs(x) > 0.02
    ini = np.argmax(env) / SR
    fim = (len(env) - np.argmax(env[::-1])) / SR
    tot = sum(pesos)
    acc = ini
    for w, p in zip(ws, pesos):
        d = (fim - ini) * p / tot
        legendas.append({"w": w, "s": round(f["t"] + acc, 3), "e": round(f["t"] + acc + d, 3), "fala": k})
        acc += d

# ---------- batida ----------
bpm = rot["bpm"]
beat = 60 / bpm
drop = rot["drop"]  # a batida "cai" aqui (ex.: no "Olha isso")
t_ = np.arange(int(SR * 0.5)) / SR


def kick():
    f = 150 * np.exp(-t_ * 28) + 45
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t_ * 9)).astype("float32")


def hat():
    n = rng.standard_normal(int(SR * 0.06)).astype("float32")
    n = np.diff(n, prepend=0)  # passa-alta simples
    return n * np.exp(-np.arange(len(n)) / SR * 70) * 0.35


def clap():
    n = rng.standard_normal(int(SR * 0.18)).astype("float32")
    return np.diff(n, prepend=0) * np.exp(-np.arange(len(n)) / SR * 22) * 0.5


def nota(freq, dur, tipo="baixo"):
    tt = np.arange(int(SR * dur)) / SR
    if tipo == "baixo":
        s = np.sign(np.sin(2 * np.pi * freq * tt)) * 0.5 + np.sin(2 * np.pi * freq * tt)
        a = np.minimum(1, tt * 80) * np.exp(-tt * 3)
    else:  # pad
        s = sum(np.sin(2 * np.pi * freq * m * tt + m) / m for m in (1, 2, 3)) + 0.4 * np.sin(2 * np.pi * freq * 1.003 * tt)
        a = np.minimum(1, tt * 3) * np.minimum(1, (dur - tt) * 4)
    return (s * a).astype("float32")


musica = np.zeros(N, "float32")
K, H, C = kick(), hat(), clap()
acordes = [(110.0, [220, 261.6, 329.6]), (87.31, [174.6, 220, 261.6]), (130.8, [261.6, 329.6, 392]), (98.0, [196, 246.9, 293.7])]  # Am F C G
# antes do drop: só pad + subida (tensão no gancho)
n_beat = int((rot["fim"] - drop) / beat) + 1
for b in range(-int(drop / beat), n_beat):
    tb = drop + b * beat
    if tb < 0:
        continue
    compasso = (b // 4) % 4
    raiz, pad = acordes[compasso]
    if b % 4 == 0:
        for fr in pad:
            por(musica, nota(fr, beat * 4, "pad"), tb, 0.05)
    if tb >= drop:
        por(musica, K, tb, 0.9)
        por(musica, H, tb + beat / 2, 1.0)
        if b % 2 == 1:
            por(musica, C, tb, 0.6)
        por(musica, nota(raiz / 2 if b % 2 else raiz, beat * 0.9), tb, 0.22)
# final: a batida para no CTA e fica só o pad
corte = rot.get("corte_batida")
if corte:
    i = int(corte * SR)
    sobra = musica[i:].copy()
    musica[i:] = sobra * np.linspace(1, 0.15, len(sobra))

# ---------- efeitos ----------
sfx = np.zeros(N, "float32")


def whoosh(d=0.45):
    n = rng.standard_normal(int(SR * d)).astype("float32")
    tt = np.arange(len(n)) / SR
    # filtro móvel com janela que diminui = varredura de grave para agudo
    out = np.zeros_like(n)
    janelas = np.linspace(40, 3, len(n)).astype(int)
    cs = np.cumsum(np.concatenate([[0], n]))
    idx = np.arange(len(n))
    out = (cs[idx + 1] - cs[np.maximum(0, idx + 1 - janelas)]) / janelas
    env = np.sin(np.pi * tt / d) ** 2
    return out * env * 2.2


def clique():
    tt = np.arange(int(SR * 0.05)) / SR
    return (np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 120) * 0.6).astype("float32")


def impacto():
    tt = np.arange(int(SR * 1.2)) / SR
    f = 90 * np.exp(-tt * 4) + 32
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
    n = rng.standard_normal(len(tt)) * np.exp(-tt * 18) * 0.3
    return (s + n).astype("float32") * 0.9


def subida(d=1.3):
    tt = np.arange(int(SR * d)) / SR
    f = 200 + 1400 * (tt / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15 + rng.standard_normal(len(tt)) * 0.12 * (tt / d)
    return (s * (tt / d) ** 1.5).astype("float32")


def ding():
    tt = np.arange(int(SR * 0.9)) / SR
    s = sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((1318.5, 0.5), (1975.5, 0.3), (2637, 0.15)))
    return (s * np.exp(-tt * 5)).astype("float32")


SFX = {"whoosh": whoosh, "clique": clique, "impacto": impacto, "subida": subida, "ding": ding}
for e in rot["sfx"]:
    x = SFX[e["tipo"]]()
    t0 = e["t"] - (len(x) / SR if e["tipo"] == "subida" else (0.2 if e["tipo"] == "whoosh" else 0))
    por(sfx, x, max(0, t0), e.get("g", 0.5))

# ---------- mixagem: música abaixa quando a voz fala ----------
env = np.abs(voz)
jan = int(SR * 0.12)
env = np.convolve(env, np.ones(jan) / jan, mode="same")
duck = 1 - 0.6 * np.clip(env / 0.08, 0, 1)
mix = voz * 1.0 + musica * 0.55 * duck + sfx * 0.7
# fade de entrada e saída
f = int(SR * 0.04)
mix[:f] *= np.linspace(0, 1, f)
f = int(SR * 0.8)
mix[-f:] *= np.linspace(1, 0, f)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
os.makedirs(os.path.join(fonte, "audio"), exist_ok=True)
sf.write(os.path.join(fonte, "audio", "mix.wav"), mix, SR)
sf.write(os.path.join(fonte, "audio", "so-voz.wav"), voz / (np.abs(voz).max() + 1e-9) * 0.95, SR)
json.dump(legendas, open(os.path.join(fonte, "legendas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
open(os.path.join(fonte, "legendas.js"), "w", encoding="utf-8").write("window.LEG=" + json.dumps(legendas, ensure_ascii=False) + ";")
print(f"mix.wav {rot['fim']}s · {len(legendas)} palavras")
