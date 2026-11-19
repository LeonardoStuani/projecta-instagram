#!/usr/bin/env python3
"""
clientes.py: espaços de trabalho dos clientes da agência.

    python scripts/clientes.py listar
    python scripts/clientes.py criar "Eixo Sul Engenharia" --arroba eixosulengenharia --ramo "topografia" --cidade "Lages-SC"

Cada cliente vive em clientes/<slug>/ (calendário, posts, mídia, pedidos, radar, voice.md).
Credenciais e chave do portal ficam em segredos/<slug>.env. As duas pastas estão no .gitignore:
nada de cliente vai para o GitHub público. O @projectatech continua na raiz, como sempre.
"""
import json, os, re, secrets, sys, unicodedata
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "clientes")
SEG = os.path.join(ROOT, "segredos")
CASA = "projectatech"   # a conta da própria agência (raiz do repositório)

REGRAS_PADRAO = {
    "cta": "chame no WhatsApp: link na bio",
    "hashtags_fixas": [],
    "proibidas": ["alavancar", "disruptivo", "solução robusta", "no mundo de hoje", "potencialize"],
    "promessas": ["garantimos", "garantia de resultado", "primeiro lugar"],
    "palavras_busca": [],
    "max_hashtags": 5,
    "max_emojis": 1,
    "sem_preco": True,
    "pilares": {"dica": 40, "bastidores": 25, "prova": 20, "oferta": 15},
}

VOICE_MODELO = """# Voz da marca: {nome}

Preencha com o cliente na primeira reunião. As skills ig-* leem este arquivo no lugar do voice.md global.

## Quem é
- Empresa: {nome} (@{arroba})
- Ramo: {ramo}
- Cidade / região: {cidade}
- Público: [quem compra, idade, onde está]

## Como fala
- Tom: [ex.: técnico e acessível, sem jargão]
- Pode: [palavras e expressões da casa]
- Nunca: preço na legenda, promessa de resultado, depoimento inventado, número inventado.

## CTA único
- {cta}

## Hashtags fixas (máx. 5 no total)
-

## Assuntos que vendem no ramo
- [serviço 1]: dúvida mais comum dos clientes
- [serviço 2]:

## Fotos e autorização
- Usar só fotos enviadas pelo cliente ou autorizadas por escrito.
"""


def slugify(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "cliente"


def valido(slug):
    return bool(slug) and bool(re.fullmatch(r"[a-z0-9][a-z0-9\-]{0,39}", slug))


def pasta(slug):
    if slug == CASA:
        return ROOT
    if not valido(slug):
        raise SystemExit("Cliente inválido.")
    return os.path.join(DIR, slug)


def existe(slug):
    return slug == CASA or (valido(slug) and os.path.exists(os.path.join(DIR, slug, "cliente.json")))


def _jload(p, padrao):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else padrao


def _jsave(p, dados):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    json.dump(dados, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, p)


# ---------------- cadastro ----------------
def carregar(slug):
    if slug == CASA:
        return {"slug": CASA, "nome": "Projecta Tech", "arroba": "projectatech", "ramo": "sites e sistemas",
                "cidade": "Lages-SC", "casa": True}
    if not existe(slug):
        raise SystemExit(f"Cliente {slug} não existe.")
    c = _jload(os.path.join(DIR, slug, "cliente.json"), {})
    c["slug"] = slug
    c["regras"] = {**REGRAS_PADRAO, **(c.get("regras") or {})}
    return c


def salvar(slug, dados):
    if slug == CASA:
        raise SystemExit("As regras do @projectatech ficam no voice.md e no painel.py.")
    atual = carregar(slug)
    for k in ("nome", "arroba", "ramo", "cidade", "cor", "observacoes"):
        if k in dados:
            atual[k] = str(dados[k]).strip().lstrip("@") if k == "arroba" else str(dados[k]).strip()
    if "regras" in dados:
        r = {**atual["regras"]}
        for k, v in dados["regras"].items():
            if k in REGRAS_PADRAO:
                r[k] = v
        atual["regras"] = r
    atual.pop("slug", None)
    _jsave(os.path.join(DIR, slug, "cliente.json"), atual)
    return carregar(slug)


def criar(nome, arroba="", ramo="", cidade="", cta=None):
    nome = (nome or "").strip()
    if len(nome) < 2:
        raise SystemExit("Informe o nome do cliente.")
    slug = slugify(arroba or nome)
    if slug == CASA or existe(slug):
        raise SystemExit(f"Já existe um cliente com o código {slug}.")
    base = os.path.join(DIR, slug)
    for d in ("posts", "media", "pedidos", "radar"):
        os.makedirs(os.path.join(base, d), exist_ok=True)
    regras = dict(REGRAS_PADRAO)
    if cta:
        regras["cta"] = cta.strip()
    c = {"nome": nome, "arroba": (arroba or "").strip().lstrip("@"), "ramo": ramo.strip(), "cidade": cidade.strip(),
         "criado_em": datetime.now().strftime("%Y-%m-%d"), "regras": regras}
    _jsave(os.path.join(base, "cliente.json"), c)
    _jsave(os.path.join(base, "calendario.json"), [])
    _jsave(os.path.join(base, "pedidos.json"), [])
    _jsave(os.path.join(base, "radar", "contas.json"), {"contas": [], "palavras": [], "temas": {}})
    open(os.path.join(base, "voice.md"), "w", encoding="utf-8").write(
        VOICE_MODELO.format(nome=nome, arroba=c["arroba"] or "?", ramo=ramo or "?", cidade=cidade or "?", cta=regras["cta"]))
    segredos_salvar(slug, {"PORTAL_CHAVE": secrets.token_urlsafe(18)})
    return carregar(slug)


def listar():
    out = [carregar(CASA)]
    if os.path.isdir(DIR):
        for d in sorted(os.listdir(DIR)):
            if existe(d):
                out.append(carregar(d))
    return out


# ---------------- segredos (token, chave do portal) ----------------
def _seg_path(slug):
    if not valido(slug) or slug == CASA:
        raise SystemExit("Cliente inválido.")
    return os.path.join(SEG, f"{slug}.env")


def segredos(slug):
    out, p = {}, _seg_path(slug)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"')
    return out


def segredos_salvar(slug, upd):
    os.makedirs(SEG, exist_ok=True)
    cur = segredos(slug)
    for k, v in upd.items():
        if v is None:
            cur.pop(k, None)
        else:
            cur[k] = str(v)
    lines = [f"# Segredos do cliente {slug}. Gerado pelo painel. NUNCA faça commit deste arquivo."]
    lines += [f"{k}={v}" for k, v in cur.items()]
    tmp = _seg_path(slug) + ".tmp"
    open(tmp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    os.replace(tmp, _seg_path(slug))


def contexto(slug):
    """Contexto para ig.usar(): pasta do cliente + credenciais dele. Vazio para o @projectatech."""
    if slug in (None, "", CASA):
        return {}
    if not existe(slug):
        raise SystemExit(f"Cliente {slug} não existe.")
    s = segredos(slug)
    ctx = {"root": pasta(slug), "slug": slug,
           "IG_ACCESS_TOKEN": s.get("IG_ACCESS_TOKEN", ""), "IG_USER_ID": s.get("IG_USER_ID", "")}
    base = s.get("IG_MEDIA_BASE_URL") or (
        os.environ.get("PAINEL_URL_PUBLICA", "").rstrip("/") + f"/midia/{slug}" if os.environ.get("PAINEL_URL_PUBLICA") else "")
    ctx["IG_MEDIA_BASE_URL"] = base
    return ctx


# ---------------- pedidos do cliente ----------------
def pedidos(slug):
    return _jload(os.path.join(pasta(slug), "pedidos.json"), [])


def pedidos_salvar(slug, lista):
    _jsave(os.path.join(pasta(slug), "pedidos.json"), lista)


def _main(a):
    if not a or a[0] == "listar":
        for c in listar():
            print(f"{c['slug']:24} @{c.get('arroba',''):24} {c.get('ramo','')}")
    elif a[0] == "criar" and len(a) > 1:
        o = dict(zip(a[2::2], a[3::2]))
        c = criar(a[1], o.get("--arroba", ""), o.get("--ramo", ""), o.get("--cidade", ""), o.get("--cta"))
        print(f"Criado: clientes/{c['slug']}/ (abra o painel → Clientes para gerar o link do portal)")
    else:
        print(__doc__)


if __name__ == "__main__":
    _main(sys.argv[1:])
