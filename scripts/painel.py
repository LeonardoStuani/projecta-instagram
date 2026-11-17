#!/usr/bin/env python3
"""
painel.py: painel web local do @projectatech.

    python scripts/painel.py            abre http://127.0.0.1:8765 no navegador

Roda só na sua máquina (127.0.0.1). Reaproveita o ig.py para falar com a API
oficial da Meta. O token fica no .env e nunca é enviado ao navegador.
"""
import json, os, re, subprocess, sys, threading, webbrowser, mimetypes, urllib.parse, urllib.request
from datetime import datetime, date, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig  # noqa: E402

ROOT = ig.ROOT
ENV = os.path.join(ROOT, ".env")
AUT = os.path.join(ROOT, "instagram", "autorizacoes.json")
UI = os.path.join(ROOT, "painel", "index.html")
PORT = int(os.environ.get("PAINEL_PORTA", "8765"))
LOCK = threading.Lock()
TOKEN_DIAS = 60

PILARES = {"dica": 40, "bastidores": 25, "prova": 20, "oferta": 15}
CTA = "peça sua análise gratuita: link na bio"
HASH_FIXAS = ["#lages", "#lagessc", "#serracatarinense"]
PROIBIDAS = ["alavancar", "disruptivo", "transformação digital", "solução robusta", "no mundo de hoje", "potencialize"]
PROMESSAS = ["primeira posição", "primeiro lugar no google", "1º lugar", "garantimos", "garantia de resultado", "dobrar seu faturamento"]
BUSCA = ["site", "landing page", "sistema de gestão", "sistema", "lages", "serra catarinense"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")


# ---------------- .env (o token nunca sai daqui) ----------------
def env_read():
    out = {}
    if os.path.exists(ENV):
        for line in open(ENV, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"')
    return out


def env_write(updates):
    cur = env_read()
    cur.update({k: v for k, v in updates.items() if v is not None})
    lines = ["# Gerado pelo painel. NUNCA faça commit deste arquivo."]
    lines += [f"{k}={v}" for k, v in cur.items()]
    open(ENV, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    for k, v in updates.items():
        if v is not None:
            os.environ[k] = v


def token_info():
    e = env_read()
    ok = bool(e.get("IG_ACCESS_TOKEN"))
    dias = None
    if ok and e.get("IG_TOKEN_SALVO_EM"):
        try:
            salvo = datetime.strptime(e["IG_TOKEN_SALVO_EM"], "%Y-%m-%d").date()
            dias = TOKEN_DIAS - (date.today() - salvo).days
        except ValueError:
            pass
    return {"configurado": ok, "dias_restantes": dias, "salvo_em": e.get("IG_TOKEN_SALVO_EM"),
            "media_base_url": e.get("IG_MEDIA_BASE_URL", ""),
            "base_url_ok": bool(e.get("IG_MEDIA_BASE_URL")) and "USUARIO" not in e.get("IG_MEDIA_BASE_URL", "")}


# ---------------- autorizações de clientes ----------------
def aut_load():
    if os.path.exists(AUT):
        return json.load(open(AUT, encoding="utf-8"))
    return {"Eixo Sul": False}


def aut_save(a):
    json.dump(a, open(AUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


# ---------------- checagem de regras (voice.md) ----------------
def checar(texto, entrada=None):
    erros, avisos = [], []
    t = texto or ""
    low = t.lower()
    if not t.strip():
        erros.append("Legenda vazia.")
    if len(t) > 2200:
        erros.append(f"Legenda com {len(t)} caracteres (limite do Instagram: 2.200).")
    if re.search(r"r\$\s*\d|\d+\s*reais|\d+\s*/\s*m[eê]s", low):
        erros.append("Tem preço. Valores só na conversa pelo WhatsApp.")
    ph = re.findall(r"\[[^\]]{2,}\]", t)
    if ph:
        erros.append("Falta preencher: " + ", ".join(ph[:3]))
    if "não publicar" in low:
        erros.append("A legenda tem uma nota de NÃO PUBLICAR.")
    tags = re.findall(r"#\w+", t)
    if len(tags) > 5:
        erros.append(f"{len(tags)} hashtags. O máximo é 5.")
    if CTA not in low:
        erros.append('Falta o CTA "Peça sua análise gratuita: link na bio."')
    for cliente, ok in aut_load().items():
        if not ok and cliente.lower() in low:
            erros.append(f"Cita {cliente} sem autorização por escrito.")
    falt = [h for h in HASH_FIXAS if h not in [x.lower() for x in tags]]
    if falt:
        avisos.append("Faltam as hashtags fixas: " + " ".join(falt))
    n_emoji = len(EMOJI.findall(t))
    if n_emoji > 1:
        avisos.append(f"{n_emoji} emojis. O tom pede no máximo um.")
    for p in PROIBIDAS:
        if p in low:
            avisos.append(f'Palavra fora do tom: "{p}".')
    for p in PROMESSAS:
        if p in low:
            avisos.append(f'Parece promessa de resultado: "{p}".')
    if not any(b in low for b in BUSCA):
        avisos.append("Sem palavra-chave de busca (site, sistema de gestão, Lages…).")
    if entrada is not None and not entrada.get("data"):
        avisos.append("Sem data no calendário.")
    if entrada is not None and not entrada.get("pilar"):
        avisos.append("Sem pilar definido (dica, bastidores, prova ou oferta).")
    return {"erros": erros, "avisos": avisos}


# ---------------- leitura do estado ----------------
def legenda_de(e):
    p = os.path.join(ROOT, e.get("legenda", ""))
    return open(p, encoding="utf-8").read().strip() if e.get("legenda") and os.path.exists(p) else ""


def git(*args, check=False):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit((r.stderr or r.stdout).strip()[-800:])
    return r


def git_info():
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        return {"repo": False}
    remote = git("remote", "get-url", "origin").stdout.strip()
    sujo = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
    ahead = git("rev-list", "--count", "@{u}..HEAD").stdout.strip() if remote else ""
    ultimo = git("log", "-1", "--format=%cd · %s", "--date=format:%d/%m %H:%M").stdout.strip()
    return {"repo": True, "remote": remote, "alteracoes": len(sujo), "a_enviar": int(ahead or 0) if ahead.isdigit() else None,
            "ultimo_commit": ultimo}


def pastas_novas(cal):
    ids = {e["id"] for e in cal}
    out = []
    pdir = os.path.join(ROOT, "posts")
    for d in sorted(os.listdir(pdir)):
        full = os.path.join(pdir, d)
        if not os.path.isdir(full) or d in ids or d in ("destaques", "perfil"):
            continue
        fs = os.listdir(full)
        slides = sorted(f for f in fs if f.startswith("slide-") and f.endswith(".png"))
        mp4 = [f for f in fs if f.endswith(".mp4")]
        if slides or mp4:
            out.append({"pasta": d, "capa": f"posts/{d}/{slides[0]}" if slides else None,
                        "video": f"posts/{d}/{mp4[0]}" if mp4 else None, "n": len(slides) or 1})
    return out


def estado():
    cal = ig.cal_load()
    posts = []
    for e in cal:
        leg = legenda_de(e)
        posts.append({**e, "texto": leg, "checagem": checar(leg, e),
                      "midia": [f"media/{f}" for f in e.get("arquivos", [])]})
    py = sys.version.split()[0]
    try:
        import PIL
        pil = PIL.__version__
    except ImportError:
        pil = None
    return {"agora": datetime.now(ig.TZ).strftime("%Y-%m-%d %H:%M"), "python": py, "pillow": pil,
            "token": token_info(), "git": git_info(), "posts": posts, "novas": pastas_novas(cal),
            "autorizacoes": aut_load(), "pilares": PILARES,
            "workflow": os.path.exists(os.path.join(ROOT, ".github", "workflows", "publicar-agendados.yml"))}


# ---------------- ações ----------------
def salvar_post(b):
    cal = ig.cal_load()
    e = ig.find(cal, b["id"])
    mudou = False
    for k in ("data", "hora", "pilar"):
        if k in b and b[k] != e.get(k):
            e[k] = b[k]; mudou = True
    if "texto" in b and b["texto"].strip() != legenda_de(e):
        open(os.path.join(ROOT, e["legenda"]), "w", encoding="utf-8").write(b["texto"].strip())
        md = os.path.join(ROOT, "posts", e["id"], "legenda.md")
        if os.path.exists(md):
            old = open(md, encoding="utf-8").read()
            head = old.split("```")[0] if "```" in old else f"# {e['id']}: legenda\n\n"
            tail = old.split("```", 2)[2] if old.count("```") >= 2 else "\n"
            open(md, "w", encoding="utf-8").write(f"{head}```\n{b['texto'].strip()}\n```{tail}")
        mudou = True
    aviso = None
    if mudou and e.get("status") == "aprovado":
        e["status"] = "pendente"
        aviso = "O post estava aprovado e foi alterado: voltou para pendente. Aprove de novo."
    ig.cal_save(sorted(cal, key=lambda x: (x.get("data") or "9999", x.get("hora", ""))))
    return {"ok": True, "aviso": aviso}


def aprovar(b):
    cal = ig.cal_load()
    e = ig.find(cal, b["id"])
    if not e.get("data"):
        raise SystemExit("Defina a data antes de aprovar.")
    c = checar(legenda_de(e), e)
    if c["erros"]:
        raise SystemExit("Corrija antes de aprovar: " + " ".join(c["erros"]))
    e["status"] = "aprovado"
    e.pop("erro", None)
    ig.cal_save(cal)
    return {"ok": True}


def voltar_pendente(b):
    cal = ig.cal_load()
    e = ig.find(cal, b["id"])
    if e.get("status") == "publicado":
        raise SystemExit("Post já publicado.")
    e["status"] = "pendente"
    ig.cal_save(cal)
    return {"ok": True}


def publicar(b):
    if b.get("confirmacao") != "PUBLICAR":
        raise SystemExit('Digite PUBLICAR para confirmar.')
    cal = ig.cal_load()
    e = ig.find(cal, b["id"])
    c = checar(legenda_de(e), e)
    if c["erros"]:
        raise SystemExit("Corrija antes: " + " ".join(c["erros"]))
    ig.load_env()
    link = ig.publish_entry(e)
    ig.cal_save(cal)
    return {"ok": True, "link": link}


def preparar(b):
    pasta = b["pasta"]
    if not re.fullmatch(r"[\w\-]+", pasta):
        raise SystemExit("Nome de pasta inválido.")
    args = [f"posts/{pasta}"]
    if b.get("data"):
        args += ["--data", b["data"]]
    args += ["--hora", b.get("hora") or "18:00"]
    ig.cmd_preparar(args)
    if b.get("pilar"):
        cal = ig.cal_load(); ig.find(cal, pasta)["pilar"] = b["pilar"]; ig.cal_save(cal)
    return {"ok": True}


def salvar_token(b):
    tok = (b.get("token") or "").strip()
    if not tok or len(tok) < 40 or " " in tok:
        raise SystemExit("Isso não parece um token do Instagram. Copie o token inteiro.")
    env_write({"IG_ACCESS_TOKEN": tok, "IG_TOKEN_SALVO_EM": date.today().isoformat()})
    return testar()


def testar(_=None):
    ig.load_env()
    if not env_read().get("IG_ACCESS_TOKEN"):
        raise SystemExit("Nenhum token salvo ainda.")
    os.environ["IG_ACCESS_TOKEN"] = env_read()["IG_ACCESS_TOKEN"]
    os.environ.pop("IG_USER_ID", None)
    me = ig.api("GET", "me", {"fields": "user_id,username,name,account_type,media_count,profile_picture_url"})
    return {"ok": True, "conta": me}


def renovar(_=None):
    tok = env_read().get("IG_ACCESS_TOKEN")
    if not tok:
        raise SystemExit("Nenhum token salvo ainda.")
    url = f"{ig.HOST}/refresh_access_token?" + urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": tok})
    try:
        r = json.loads(urllib.request.urlopen(url, timeout=60).read().decode())
    except Exception as err:  # noqa: BLE001
        raise SystemExit(f"Não deu para renovar: {getattr(err, 'reason', err)}")
    env_write({"IG_ACCESS_TOKEN": r["access_token"], "IG_TOKEN_SALVO_EM": date.today().isoformat()})
    return {"ok": True, "dias": r.get("expires_in", 0) // 86400,
            "lembrete": "Token novo salvo no .env. Atualize também o secret IG_ACCESS_TOKEN no GitHub."}


def conectar_github(b):
    url = (b.get("url") or "").strip().removesuffix("/")
    m = re.fullmatch(r"https://github\.com/([\w.\-]+)/([\w.\-]+?)(\.git)?", url)
    if not m:
        raise SystemExit("Cole o endereço do repositório, ex.: https://github.com/seu-usuario/projecta-instagram")
    user, repo = m.group(1), m.group(2)
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        git("init", check=True)
        git("checkout", "-B", "main", check=True)
    if git("remote", "get-url", "origin").returncode == 0:
        git("remote", "set-url", "origin", f"https://github.com/{user}/{repo}.git", check=True)
    else:
        git("remote", "add", "origin", f"https://github.com/{user}/{repo}.git", check=True)
    env_write({"IG_MEDIA_BASE_URL": f"https://raw.githubusercontent.com/{user}/{repo}/main/media"})
    return {"ok": True}


def enviar_github(b):
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        raise SystemExit("Conecte o GitHub primeiro.")
    git("add", "-A", check=True)
    if git("diff", "--cached", "--quiet").returncode != 0:
        msg = (b.get("mensagem") or "").strip() or "Instagram: atualiza calendário pelo painel"
        git("commit", "-m", msg, check=True)
    git("pull", "--rebase", "origin", "main")  # traz o que o robô publicou, se houver
    git("push", "-u", "origin", "main", check=True)
    return {"ok": True}


def autorizar(b):
    a = aut_load()
    nome = (b.get("cliente") or "").strip()
    if not nome:
        raise SystemExit("Informe o cliente.")
    if b.get("remover"):
        a.pop(nome, None)
    else:
        a[nome] = bool(b.get("autorizado"))
    aut_save(a)
    return {"ok": True}


def comentarios(_=None):
    ig.load_env()
    uid = ig.user_id()
    media = ig.api("GET", f"{uid}/media", {"fields": "id,caption,permalink,timestamp,media_url,thumbnail_url", "limit": 8}).get("data", [])
    out = []
    for m in media:
        cs = ig.api("GET", f"{m['id']}/comments", {"fields": "id,text,username,timestamp,replies{id,text,username}"}).get("data", [])
        out.append({"post": m, "comentarios": cs})
    return {"ok": True, "itens": out}


def responder(b):
    if b.get("confirmacao") is not True:
        raise SystemExit("Confirme o envio.")
    texto = (b.get("texto") or "").strip()
    if not texto:
        raise SystemExit("Resposta vazia.")
    ig.load_env()
    return {"ok": True, "res": ig.api("POST", f"{b['id']}/replies", {"message": texto})}


def checar_texto(b):
    return checar(b.get("texto", ""), None)


POST_ROUTES = {
    "/api/post/salvar": salvar_post, "/api/post/aprovar": aprovar, "/api/post/pendente": voltar_pendente,
    "/api/post/publicar": publicar, "/api/post/preparar": preparar, "/api/checar": checar_texto,
    "/api/conexao/token": salvar_token, "/api/conexao/testar": testar, "/api/conexao/renovar": renovar,
    "/api/github/conectar": conectar_github, "/api/github/enviar": enviar_github,
    "/api/autorizacoes": autorizar, "/api/comentarios/responder": responder,
}
GET_ROUTES = {"/api/estado": lambda: estado(), "/api/comentarios": lambda: comentarios()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        pass

    def _host_ok(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"erro": "Acesso só pela própria máquina."})
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, open(UI, "rb").read(), "text/html; charset=utf-8")
        if u.path == "/arquivo":
            rel = urllib.parse.parse_qs(u.query).get("p", [""])[0]
            full = os.path.realpath(os.path.join(ROOT, rel))
            allowed = [os.path.realpath(os.path.join(ROOT, d)) + os.sep for d in ("media", "posts")]
            if not any(full.startswith(a) for a in allowed) or not os.path.isfile(full):
                return self._send(404, {"erro": "Arquivo não encontrado."})
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            return self._send(200, open(full, "rb").read(), ctype)
        fn = GET_ROUTES.get(u.path)
        if not fn:
            return self._send(404, {"erro": "Rota não existe."})
        self._run(fn)

    def do_POST(self):
        if not self._host_ok() or self.headers.get("X-Painel") != "1":
            return self._send(403, {"erro": "Acesso negado."})
        fn = POST_ROUTES.get(urllib.parse.urlparse(self.path).path)
        if not fn:
            return self._send(404, {"erro": "Rota não existe."})
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"erro": "JSON inválido."})
        self._run(lambda: fn(body))

    def _run(self, fn):
        try:
            with LOCK:
                res = fn()
            self._send(200, res)
        except SystemExit as err:
            self._send(400, {"erro": scrub(str(err))})
        except Exception as err:  # noqa: BLE001
            self._send(500, {"erro": scrub(f"{type(err).__name__}: {err}")})


def scrub(msg):
    tok = env_read().get("IG_ACCESS_TOKEN")
    return msg.replace(tok, "•••") if tok else msg


def main():
    ig.load_env()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Painel do Instagram rodando em {url}  (Ctrl+C para fechar)")
    if "--sem-navegador" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nPainel fechado.")


if __name__ == "__main__":
    main()
