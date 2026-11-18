#!/usr/bin/env python3
"""
ig.py — linha de comando do Instagram da Projecta Tech (API oficial da Meta).

Comandos:
  python3 scripts/ig.py conta                      mostra a conta ligada ao token
  python3 scripts/ig.py preparar <pasta> [--data AAAA-MM-DD --hora HH:MM --pilar dica]
                                                   converte os slides PNG em JPEG, põe o post no calendário (pendente)
                                                   e mostra o checklist antes de aprovar
  python3 scripts/ig.py plano                      lista o calendário
  python3 scripts/ig.py aprovar <id>               marca um post como aprovado (a automação publica na data)
  python3 scripts/ig.py publicar <id> [--sim]      publica agora (pede confirmação, exceto com --sim)
  python3 scripts/ig.py agendados                  publica os aprovados cuja data/hora já passou (usado pelo GitHub Actions)
  python3 scripts/ig.py comentarios [--n 5]        comentários recentes nos últimos N posts
  python3 scripts/ig.py responder <comment_id> "texto"   responde um comentário (sempre pede confirmação)
  python3 scripts/ig.py renovar-token              não é necessário: o token de usuário do sistema não expira

Variáveis de ambiente (arquivo .env na raiz ou secrets do GitHub):
  IG_ACCESS_TOKEN   token de usuário do sistema (Login unificado da Meta, começa com EAA, não expira)
  IG_USER_ID        ID da conta profissional do Instagram (@projectatech: 17841478285323581)
  IG_MEDIA_BASE_URL URL pública da pasta media/, ex.: https://raw.githubusercontent.com/USUARIO/REPO/main/media
  IG_API_HOST       opcional (padrão https://graph.facebook.com)
  IG_API_VERSION    opcional (padrão v23.0)

Só usa a biblioteca padrão do Python, exceto `preparar`, que usa Pillow (pip install pillow).
"""
import json, os, sys, time, uuid, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "calendario.json")
MEDIA = os.path.join(ROOT, "media")
TZ = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão)
CONTA = "projectatech"


def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def env(k, default=None, required=True):
    v = os.environ.get(k, default)
    if required and not v:
        sys.exit(f"Falta a variável {k}. Veja o LEIA-ME (seção Token).")
    return v


def ver():
    return os.environ.get("IG_API_VERSION", "v23.0")


def host():
    return os.environ.get("IG_API_HOST", "https://graph.facebook.com").rstrip("/")


def api(method, path, params=None, headers=None, data=None):
    params = dict(params or {})
    url = f"{host()}/{ver()}/{path.lstrip('/')}"
    hdrs = {"Authorization": f"Bearer {env('IG_ACCESS_TOKEN')}"}
    hdrs.update(headers or {})
    body = None
    if method == "GET":
        if params:
            url += "?" + urllib.parse.urlencode(params)
    elif data is not None:
        body = data
    else:
        body = urllib.parse.urlencode(params).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        raise SystemExit(f"Erro da API ({e.code}) em {path}: {msg}")


def user_id():
    return env("IG_USER_ID")


def conta():
    """Dados da conta ligada ao IG_USER_ID. Serve como teste do token."""
    return api("GET", user_id(), {"fields": "username,name,media_count,followers_count"})


# ---------------- calendário ----------------
def cal_load():
    return json.load(open(CAL, encoding="utf-8")) if os.path.exists(CAL) else []


def cal_save(c):
    json.dump(c, open(CAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def find(c, pid):
    for e in c:
        if e["id"] == pid:
            return e
    sys.exit(f"Post '{pid}' não está no calendário. Rode: ig.py plano")


def legenda(e):
    return open(os.path.join(ROOT, e["legenda"]), encoding="utf-8").read().strip()


# ---------------- publicação ----------------
def wait_ready(cid, tries=40):
    for _ in range(tries):
        s = api("GET", cid, {"fields": "status_code,status"})
        code = s.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Container {cid} falhou: {s}")
        time.sleep(6)
    raise SystemExit(f"Container {cid} não ficou pronto a tempo.")


def media_url(rel):
    base = env("IG_MEDIA_BASE_URL").rstrip("/")
    return f"{base}/{urllib.parse.quote(rel)}"


def publish_entry(e):
    uid = user_id()
    cap = legenda(e)
    files = e["arquivos"]
    if e["tipo"] == "reel":
        c = api("POST", f"{uid}/media", {"media_type": "REELS", "upload_type": "resumable",
                                         "caption": cap, "share_to_feed": "true"})
        cid = c["id"]
        path = os.path.join(MEDIA, files[0])
        blob = open(path, "rb").read()
        req = urllib.request.Request(
            f"https://rupload.facebook.com/ig-api-upload/{ver()}/{cid}", data=blob, method="POST",
            headers={"Authorization": f"OAuth {env('IG_ACCESS_TOKEN')}", "offset": "0",
                     "file_size": str(len(blob))})
        try:
            urllib.request.urlopen(req, timeout=600).read()
        except urllib.error.HTTPError as err:
            raise SystemExit(f"Falha no upload do vídeo: {err.read().decode(errors='replace')}")
        wait_ready(cid)
    elif len(files) == 1:
        cid = api("POST", f"{uid}/media", {"image_url": media_url(files[0]), "caption": cap})["id"]
        wait_ready(cid)
    else:
        kids = []
        for f in files[:10]:
            k = api("POST", f"{uid}/media", {"image_url": media_url(f), "is_carousel_item": "true"})["id"]
            wait_ready(k)
            kids.append(k)
        cid = api("POST", f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(kids),
                                           "caption": cap})["id"]
        wait_ready(cid)
    mid = api("POST", f"{uid}/media_publish", {"creation_id": cid})["id"]
    link = api("GET", mid, {"fields": "permalink"}).get("permalink", "")
    e.update(status="publicado", media_id=mid, link=link,
             publicado_em=datetime.now(TZ).strftime("%Y-%m-%d %H:%M"))
    return link


def confirm(msg):
    return input(f"{msg} [s/N] ").strip().lower() in ("s", "sim", "y", "yes")


# ---------------- comandos ----------------
def cmd_conta(a):
    c = conta()
    print(json.dumps(c, ensure_ascii=False, indent=2))
    if c.get("username") == CONTA:
        print(f"Conexão OK: @{CONTA}.")
    else:
        sys.exit(f"Atenção: o token responde pela conta @{c.get('username')}, não @{CONTA}.")


# Checklist antes de aprovar (instagram/referencias/benchmark-leventech.md).
# Cada item: (texto, função(legenda) -> True/False, ou None quando precisa olhar a arte).
RODAPE = "projectatech.com.br · WhatsApp · Lages-SC"


def _antes_do_cta(leg):
    return leg.lower().split("peça sua análise gratuita")[0]


CHECKLIST = [
    ("Capa com pessoa ou palavra-conceito grande", None),
    (f"Rodapé padrão em todos os slides ({RODAPE})", None),
    ("Gancho com até 9 palavras no 1º slide", None),
    ("Legenda: pergunta → sinal → custo → verificação → solução → prova → pergunta",
     lambda t: len(t) >= 700 and t.strip().split("\n")[0].rstrip().endswith("?") and "?" in _antes_do_cta(t)[-400:]),
    ("1 CTA só (análise gratuita: link na bio)", lambda t: t.lower().count("link na bio") == 1),
    ("Localização Lages-SC (no app ou no agendamento) + até 5 hashtags",
     lambda t: 0 < len([w for w in t.split() if w.startswith("#")]) <= 5),
    ("Nada inventado: nenhum [colchete] sobrando", lambda t: "[" not in t),
]


def checklist(leg):
    out = []
    for item, f in CHECKLIST:
        out.append((item, None if f is None else bool(f(leg))))
    return out


def imprimir_checklist(leg):
    print("\nChecklist antes de aprovar (benchmark):")
    for item, ok in checklist(leg):
        print(f"  [{'ok' if ok else 'olhe' if ok is None else 'X '}] {item}")
    print("  'olhe' = confira na arte. 'X' = corrija antes de aprovar.\n")


def cmd_preparar(a):
    from PIL import Image  # pip install pillow
    pasta = a[0].rstrip("/")
    opts = dict(zip(a[1::2], a[2::2]))
    src = os.path.join(ROOT, pasta) if not os.path.isabs(pasta) else pasta
    pid = os.path.basename(src)
    out = os.path.join(MEDIA, pid)
    os.makedirs(out, exist_ok=True)
    pngs = sorted(f for f in os.listdir(src) if f.startswith("slide-") and f.endswith(".png"))
    mp4 = sorted(f for f in os.listdir(src) if f.endswith(".mp4"))
    arquivos = []
    if mp4:
        import shutil
        shutil.copy(os.path.join(src, mp4[0]), os.path.join(out, mp4[0]))
        arquivos = [f"{pid}/{mp4[0]}"]
        tipo = "reel"
    else:
        for f in pngs:
            jpg = f.replace(".png", ".jpg")
            Image.open(os.path.join(src, f)).convert("RGB").save(os.path.join(out, jpg), quality=95)
            arquivos.append(f"{pid}/{jpg}")
        tipo = "carrossel" if len(arquivos) > 1 else "imagem"
    leg_src = os.path.join(src, "legenda.md")
    leg = open(leg_src, encoding="utf-8").read() if os.path.exists(leg_src) else ""
    if "```" in leg:
        leg = leg.split("```")[1].strip()
    leg_rel = f"media/{pid}/legenda.txt"
    open(os.path.join(ROOT, leg_rel), "w", encoding="utf-8").write(leg)
    c = [e for e in cal_load() if e["id"] != pid]
    novo = {"id": pid, "tipo": tipo, "arquivos": arquivos, "legenda": leg_rel,
            "data": opts.get("--data", ""), "hora": opts.get("--hora", "18:00"), "status": "pendente"}
    if opts.get("--pilar"):
        novo["pilar"] = opts["--pilar"]
    c.append(novo)
    cal_save(sorted(c, key=lambda e: (e["data"] or "9999", e["hora"])))
    print(f"OK: {pid} ({tipo}, {len(arquivos)} arquivo(s)) entrou no calendário como pendente.")
    imprimir_checklist(leg)
    print("Faça commit e push para as imagens ficarem públicas antes de aprovar.")


def cmd_plano(a):
    for e in cal_load():
        print(f"{e['data'] or 'sem data':10} {e['hora']:5}  {e['status']:10} {e['tipo']:9} {e['id']}"
              + (f"  {e.get('link','')}" if e.get("link") else ""))


def cmd_aprovar(a):
    c = cal_load(); e = find(c, a[0])
    if not e["data"]:
        sys.exit("Defina a data antes: edite calendario.json ou rode preparar com --data.")
    e["status"] = "aprovado"; cal_save(c)
    print(f"Aprovado: {e['id']} sai em {e['data']} às {e['hora']} (horário de Brasília). Faça commit e push.")


def cmd_publicar(a):
    c = cal_load(); e = find(c, a[0])
    print(f"\n{e['tipo'].upper()} · {e['id']} · {len(e['arquivos'])} arquivo(s)\n" + "-" * 60)
    print(legenda(e)); print("-" * 60)
    if "--sim" not in a and not confirm("Publicar agora no @projectatech?"):
        sys.exit("Cancelado.")
    print("Publicado:", publish_entry(e)); cal_save(c)


def cmd_agendados(a):
    c = cal_load(); now = datetime.now(TZ); feitos = 0
    for e in c:
        if e["status"] != "aprovado" or not e["data"]:
            continue
        quando = datetime.strptime(f"{e['data']} {e['hora']}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if quando <= now:
            try:
                print(f"Publicando {e['id']}…", publish_entry(e)); feitos += 1
            except SystemExit as err:
                e["status"] = "erro"; e["erro"] = str(err)[:500]; print(err)
            cal_save(c)
    print(f"{feitos} post(s) publicado(s).")


def cmd_comentarios(a):
    n = int(dict(zip(a[::2], a[1::2])).get("--n", 5))
    uid = user_id()
    media = api("GET", f"{uid}/media", {"fields": "id,caption,permalink", "limit": n}).get("data", [])
    for m in media:
        cs = api("GET", f"{m['id']}/comments", {"fields": "id,text,username,timestamp"}).get("data", [])
        if not cs:
            continue
        print(f"\n{m.get('permalink')}\n  {(m.get('caption') or '')[:70]}…")
        for x in cs:
            print(f"  [{x['id']}] @{x.get('username')}: {x.get('text')}")


def cmd_responder(a):
    cid, texto = a[0], a[1]
    print(f"Responder o comentário {cid} com:\n  {texto}")
    if not confirm("Enviar esta resposta?"):
        sys.exit("Cancelado.")
    print(api("POST", f"{cid}/replies", {"message": texto}))


def cmd_renovar(a):
    print("Não é necessário: o token é de usuário do sistema (Login unificado) e não expira.")


CMDS = {"conta": cmd_conta, "preparar": cmd_preparar, "plano": cmd_plano, "aprovar": cmd_aprovar,
        "publicar": cmd_publicar, "agendados": cmd_agendados, "comentarios": cmd_comentarios,
        "responder": cmd_responder, "renovar-token": cmd_renovar}

if __name__ == "__main__":
    load_env()
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])
