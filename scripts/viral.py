#!/usr/bin/env python3
"""
viral.py: monitor mensal de vídeos curtos que estão funcionando no nicho da Projecta.

    python scripts/viral.py                 pesquisa, ranqueia e grava instagram/swipe.md
    python scripts/viral.py --rapido        menos buscas (para testar)

Segue o método da skill /ig-viral: views sozinhas não provam nada; o que conta é
quantas vezes o vídeo superou a MEDIANA do próprio canal (outlier). Fonte: YouTube
Shorts públicos (views e legendas automáticas abertas, sem login). Lê pouco, em
ritmo humano, e nunca baixa os vídeos. Copie a fórmula, nunca o vídeo.

Saídas:
  instagram/viral/AAAA-MM-DD.tsv   dados brutos (conta, seguidores, mediana, views, gancho)
  instagram/viral/ultimo.json      resumo usado pelo painel
  instagram/swipe.md               swipe file (lido por /ig-reel e /ig-plan)
  ~/.claude/instagram/swipe.md     cópia para as skills
"""
import json, os, re, shutil, statistics, subprocess, sys, time
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "instagram", "viral")
SWIPE = os.path.join(ROOT, ".claude", "skills", "ig-viral", "swipe.py")
PY = sys.executable

BUSCAS = [
    "criação de site para empresa #shorts",
    "site para pequena empresa #shorts",
    "landing page que vende #shorts",
    "google meu negócio dicas #shorts",
    "sistema de gestão pequena empresa #shorts",
    "planilha ou sistema empresa #shorts",
    "botão whatsapp site vendas #shorts",
    "web designer freelancer cliente #shorts",
    "marketing para clínica de estética #shorts",
    "oficina mecânica marketing digital #shorts",
]
POR_BUSCA = 15
MAX_CANAIS = 14
SHORTS_POR_CANAL = 30
LIMITE_SEGUIDORES = 1_500_000   # canais gigantes só ensinam formato; ficam de fora do ranking
PAUSA = 1.5


def ytdlp(*args, timeout=180):
    r = subprocess.run([PY, "-m", "yt_dlp", "--no-warnings", "--ignore-errors", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    time.sleep(PAUSA)
    return r.stdout


def buscar(q, n):
    out = ytdlp("--flat-playlist", "-J", f"ytsearch{n}:{q}")
    try:
        return json.loads(out).get("entries") or []
    except json.JSONDecodeError:
        return []


def shorts_do_canal(url):
    out = ytdlp("--flat-playlist", "--playlist-end", str(SHORTS_POR_CANAL), "-J", url.rstrip("/") + "/shorts")
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        return None
    return d


def gancho_falado(video_id):
    """Primeiras palavras ditas até 3 s, das legendas automáticas em português."""
    tmp = os.path.join(OUT, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    ytdlp("--skip-download", "--write-auto-subs", "--sub-langs", "pt.*", "--sub-format", "json3",
          "-o", os.path.join(tmp, "%(id)s"), f"https://www.youtube.com/shorts/{video_id}", timeout=120)
    words = {}  # chave = instante em ms: as legendas automáticas repetem trechos em janelas diferentes
    for f in sorted(os.listdir(tmp)):
        if f.startswith(video_id) and f.endswith(".json3"):
            try:
                d = json.load(open(os.path.join(tmp, f), encoding="utf-8"))
                for ev in d.get("events", []):
                    t0 = ev.get("tStartMs", 0)
                    for s in ev.get("segs", []) or []:
                        t = t0 + s.get("tOffsetMs", 0)
                        txt = s.get("utf8", "")
                        if t <= 3000 and txt.strip() and t not in words:
                            words[t] = txt
            except (OSError, json.JSONDecodeError):
                pass
            break  # um idioma basta
    shutil.rmtree(tmp, ignore_errors=True)
    return sem_repeticao(re.sub(r"\s+", " ", "".join(words[k] for k in sorted(words))).strip())


def sem_repeticao(s):
    """'Olha isso. >> Olha isso.' vira 'Olha isso.'"""
    s = s.replace(">>", " ").strip()
    s = re.sub(r"\s+", " ", s)
    n = len(s)
    for k in range(n // 2, 3, -1):
        if s[:k].strip() and s[k:].strip().startswith(s[:k].strip()[:max(8, k // 2)]):
            return s[:k].strip()
    return s


def limpa(s):
    return re.sub(r"\s+", " ", re.sub(r"#\w+", "", s or "")).strip(" -|·")


def main():
    rapido = "--rapido" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    buscas = BUSCAS[:3] if rapido else BUSCAS
    canais = {}
    for q in buscas:
        print(f"busca: {q}")
        for e in buscar(q, POR_BUSCA):
            dur = e.get("duration") or 0
            cid = e.get("channel_id") or e.get("channel_url")
            if not cid or (dur and dur > 70):
                continue
            c = canais.setdefault(cid, {"url": e.get("channel_url") or f"https://www.youtube.com/channel/{cid}",
                                        "nome": e.get("channel") or e.get("uploader") or cid, "hits": 0, "temas": set()})
            c["hits"] += 1
            c["temas"].add(q.replace(" #shorts", ""))
    escolhidos = sorted(canais.values(), key=lambda c: -c["hits"])[: (5 if rapido else MAX_CANAIS)]

    linhas, resumo = [], []
    for c in escolhidos:
        print(f"canal: {c['nome']}")
        d = shorts_do_canal(c["url"])
        if not d:
            continue
        seg = d.get("channel_follower_count") or 0
        vids = [v for v in (d.get("entries") or []) if v.get("view_count")]
        if len(vids) < 6 or (seg and seg > LIMITE_SEGUIDORES):
            continue
        med = statistics.median(v["view_count"] for v in vids)
        for v in vids:
            mult = v["view_count"] / med if med else 0
            linhas.append({"account": "@" + (d.get("uploader_id") or c["nome"]).lstrip("@"), "followers": seg, "median": int(med),
                           "views": v["view_count"], "hook": limpa(v.get("title")), "id": v.get("id"), "mult": mult,
                           "canal": c["nome"], "temas": sorted(c["temas"])})
        resumo.append({"canal": c["nome"], "seguidores": seg, "mediana": int(med), "shorts": len(vids)})

    linhas.sort(key=lambda r: -r["mult"])
    for r in linhas:  # acima de ~200x a mediana quase sempre é verba de anúncio, não alcance orgânico
        r["anuncio"] = r["mult"] >= 200
    top = [r for r in linhas if r["mult"] >= 3 and not r["anuncio"]][:12]
    top += [r for r in linhas if r["anuncio"]][:5]
    for r in top:
        print(f"gancho falado: {r['id']}")
        falado = gancho_falado(r["id"])
        r["falado"] = falado
        if falado:
            r["hook"] = falado

    hoje = date.today().isoformat()
    tsv = os.path.join(OUT, f"{hoje}.tsv")
    with open(tsv, "w", encoding="utf-8") as f:
        f.write("account\tfollowers\tmedian\tviews\thook\n")
        for r in linhas:
            if r["hook"]:
                f.write(f"{r['account']}\t{r['followers']}\t{r['median']}\t{r['views']}\t{r['hook'].replace(chr(9), ' ')}\n")
    # ranking bruto do swipe.py (classificador em inglês: a leitura em PT é feita à mão no swipe.md)
    ranking = os.path.join(OUT, f"{hoje}-ranking.md")
    subprocess.run([PY, SWIPE, tsv, "--out", ranking], check=False, capture_output=True)
    swipe = os.path.join(ROOT, "instagram", "swipe.md")
    os.makedirs(os.path.expanduser("~/.claude/instagram"), exist_ok=True)
    if os.path.exists(swipe):
        shutil.copy(swipe, os.path.expanduser("~/.claude/instagram/swipe.md"))
    print("Próximo passo: peça ao Claude para ler instagram/viral/ultimo.json e atualizar o instagram/swipe.md.")
    json.dump({"data": hoje, "videos": len(linhas), "canais": resumo,
               "outliers": [{k: r[k] for k in ("canal", "account", "views", "median", "mult", "hook", "id", "anuncio")} | {"url": f"https://www.youtube.com/shorts/{r['id']}"}
                            for r in top]},
              open(os.path.join(OUT, "ultimo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n{len(linhas)} vídeos de {len(resumo)} canais · {len(top)} outliers (3x ou mais) · {tsv}")


if __name__ == "__main__":
    main()
