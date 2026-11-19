"""Gera a narração de um Reel com a voz padrão da Projecta: Antonio (pt-BR-AntonioNeural, Microsoft, via edge-tts).

Uso: python scripts/video/voz.py posts/<pasta>
Lê  posts/<pasta>/fonte/roteiro.json  {"fim", "falas":[{"t":inicio,"texto"}], "voz"?: "pt-BR-AntonioNeural"}
Gera posts/<pasta>/fonte/voz/l1..lN.wav (48 kHz, mono, sem silêncio nas pontas).
Cada fala precisa terminar antes da próxima (o "t" da seguinte, ou "fim"). Se não couber, a fala é
regerada um pouco mais rápida (até +40%). Se ainda assim não couber, aumente o intervalo no roteiro.
Depois rode scripts/video/trilha.py, que mixa voz, batida, efeitos e gera as legendas.

Precisa de internet (o texto vai para o serviço de voz da Microsoft) e de: pip install edge-tts soundfile numpy imageio-ffmpeg
"""
import json, os, subprocess, sys, tempfile
import numpy as np
import soundfile as sf
import imageio_ffmpeg

VOZ_PADRAO = "pt-BR-AntonioNeural"
RATE_BASE = 8  # % acima do normal: soa natural em Reel
RATE_MAX = 40
FOLGA = 0.15  # segundos livres antes da próxima fala

pasta = sys.argv[1]
fonte = os.path.join(pasta, "fonte")
rot = json.load(open(os.path.join(fonte, "roteiro.json"), encoding="utf-8"))
voz = rot.get("voz", VOZ_PADRAO)
falas = rot["falas"]
ff = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(os.path.join(fonte, "voz"), exist_ok=True)
tmp = tempfile.mkdtemp()


def gerar(texto, rate, saida):
    mp3 = os.path.join(tmp, "f.mp3")
    subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voz, f"--rate=+{rate}%",
                    "--text", texto, "--write-media", mp3], check=True, capture_output=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", mp3, "-ar", "48000", "-ac", "1", saida], check=True)
    a, sr = sf.read(saida, dtype="float32")
    on = np.abs(a) > 0.01
    i, j = np.argmax(on), len(a) - np.argmax(on[::-1])
    a = a[max(0, i - int(0.03 * sr)) : j + int(0.06 * sr)]
    sf.write(saida, a, sr)
    return len(a) / sr


for k, f in enumerate(falas, 1):
    vaga = (falas[k]["t"] if k < len(falas) else rot["fim"]) - f["t"] - FOLGA
    saida = os.path.join(fonte, "voz", f"l{k}.wav")
    rate = RATE_BASE
    d = gerar(f["texto"], rate, saida)
    if d > vaga:
        rate = min(RATE_MAX, int(np.ceil(((100 + RATE_BASE) * d / vaga) - 100)) + 2)
        d = gerar(f["texto"], rate, saida)
    aviso = "  << NÃO CABE: aumente o intervalo no roteiro" if d > vaga else ""
    print(f"l{k}: {d:.2f}s de {vaga:.2f}s (+{rate}%){aviso}")
print(f"Voz: {voz}")
