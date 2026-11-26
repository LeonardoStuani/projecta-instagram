#!/usr/bin/env python3
"""
ig.py — linha de comando do Instagram da Projecta Tech (API oficial da Meta).

Comandos (para um cliente da agência, comece com --cliente <slug>, ex.: ig.py --cliente eixosul plano):
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
  python3 scripts/ig.py desempenho [--n 15]         validação semanal: alcance, envios/alcance, retenção por post
  python3 scripts/ig.py renovar-token              não é necessário: o token de usuário do sistema não expira

Variáveis de ambiente (arquivo .env na raiz ou secrets do GitHub):
  IG_ACCESS_TOKEN   token de usuário do sistema (Login unificado da Meta, começa com EAA, não expira)
  IG_USER_ID        ID da conta profissional do Instagram (@projectatech: 17841478285323581)
  IG_MEDIA_BASE_URL URL pública da pasta media/, ex.: https://raw.githubusercontent.com/USUARIO/REPO/main/media
  IG_API_HOST       opcional (padrão https://graph.facebook.com)
  IG_API_VERSION    opcional (padrão v23.0)

Só usa a biblioteca padrão do Python, exceto `preparar`, que usa Pillow (pip install pillow).
"""
import contextlib, json, os, sys, time, uuid, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "calendario.json")
MEDIA = os.path.join(ROOT, "media")
TZ = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão)
CONTA = "projectatech"

# Contexto do cliente atual. Vazio = @projectatech (raiz do repositório e .env), exatamente como antes.
# Para um cliente da agência: {"root": clientes/<slug>, "IG_ACCESS_TOKEN": ..., "IG_USER_ID": ..., ...}.
CTX = {}


@contextlib.contextmanager
def usar(ctx):
    """Troca o contexto (pasta + credenciais) durante um bloco e restaura depois."""
    global CTX
    antigo, CTX = CTX, dict(ctx or {})
    try:
        yield
    finally:
        CTX = antigo


def _root():
    return CTX.get("root") or ROOT


def _cal():
    return os.path.join(_root(), "calendario.json")


def _media():
    return os.path.join(_root(), "media")


def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def env(k, default=None, required=True):
    v = CTX.get(k) if k in CTX else os.environ.get(k, default)
    v = v or default
    if required and not v:
        sys.exit(f"Falta a variável {k}. Veja o LEIA-ME (seção Token).")
    return v


def ver():
    return CTX.get("IG_API_VERSION") or os.environ.get("IG_API_VERSION", "v23.0")


def host():
    """Token do Login do Instagram (começa com IG) usa graph.instagram.com; o do Login unificado (EAA), graph.facebook.com."""
    h = CTX.get("IG_API_HOST") or os.environ.get("IG_API_HOST")
    if not h:
        tok = env("IG_ACCESS_TOKEN", required=False) or ""
        h = "https://graph.instagram.com" if tok.startswith("IG") else "https://graph.facebook.com"
    return h.rstrip("/")


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
    return json.load(open(_cal(), encoding="utf-8")) if os.path.exists(_cal()) else []


def cal_save(c):
    json.dump(c, open(_cal(), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def find(c, pid):
    for e in c:
        if e["id"] == pid:
            return e
    sys.exit(f"Post '{pid}' não está no calendário. Rode: ig.py plano")


def legenda(e):
    return open(os.path.join(_root(), e["legenda"]), encoding="utf-8").read().strip()


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
    if e["tipo"] == "story":  # um Story por quadro, na ordem; o link fica o do último
        mid = None
        for f in files[:10]:
            cid = api("POST", f"{uid}/media", {"media_type": "STORIES", "image_url": media_url(f)})["id"]
            wait_ready(cid)
            mid = api("POST", f"{uid}/media_publish", {"creation_id": cid})["id"]
        e.update(status="publicado", media_id=mid, link="",
                 publicado_em=datetime.now(TZ).strftime("%Y-%m-%d %H:%M"))
        return ""
    if e["tipo"] == "reel":
        par = {"media_type": "REELS", "upload_type": "resumable", "caption": cap, "share_to_feed": "true"}
        if e.get("capa_s"):  # segundo do vídeo usado como capa (quando o quadro 0 é escuro ou vazio)
            par["thumb_offset"] = str(int(float(e["capa_s"]) * 1000))
        c = api("POST", f"{uid}/media", par)
        cid = c["id"]
        path = os.path.join(_media(), files[0])
        blob = open(path, "rb").read()
        req = urllib.request.Request(
            f"https://rupload.facebook.com/ig-api-upload/{ver()}/{cid}", data=blob, method="POST",
            headers={"Authorization": f"OAuth {env('IG_ACCESS_TOKEN')}", "offset": "0",
                     "file_size": str(len(blob))})
        try:
            urllib.request.urlopen(req, timeout=600).read()
        except urllib.error.HTTPError as err:
            # Upload direto recusado (ex.: ProcessingFailedError): a Meta baixa o vídeo pela URL pública do GitHub.
            erro_upload = err.read().decode(errors="replace")
            par2 = {k: v for k, v in par.items() if k != "upload_type"}
            par2["video_url"] = media_url(files[0])
            try:
                cid = api("POST", f"{uid}/media", par2)["id"]
            except SystemExit as e2:
                raise SystemExit(f"Falha no upload do vídeo: {erro_upload} | e pela URL: {e2}")
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


def story_1080(im):
    """Quadro de Story 1080x1920: a foto inteira (sem corte) sobre ela mesma ampliada, bem desfocada e escurecida."""
    from PIL import Image, ImageEnhance, ImageFilter
    W, H = 1080, 1920
    im = im.convert("RGB")
    if im.size == (W, H):
        return im
    cobre = max(W / im.width, H / im.height)
    fundo = im.resize((round(im.width * cobre / 8) + 1, round(im.height * cobre / 8) + 1), Image.BILINEAR)
    fundo = fundo.filter(ImageFilter.GaussianBlur(6)).resize((round(im.width * cobre), round(im.height * cobre)), Image.BICUBIC)
    l, t = (fundo.width - W) // 2, (fundo.height - H) // 2
    fundo = ImageEnhance.Brightness(fundo.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(30))).enhance(0.55)
    esc = min(W / im.width, H / im.height)
    fr = im.resize((round(im.width * esc), round(im.height * esc)), Image.LANCZOS)
    fundo.paste(fr, ((W - fr.width) // 2, (H - fr.height) // 2))
    return fundo


def cmd_preparar(a):
    from PIL import Image  # pip install pillow
    pasta = a[0].rstrip("/")
    opts = dict(zip(a[1::2], a[2::2]))
    src = os.path.join(_root(), pasta) if not os.path.isabs(pasta) else pasta
    if not os.path.isdir(src) and os.path.isdir(os.path.join(ROOT, pasta)):  # aceita clientes/<slug>/posts/<pasta>
        src = os.path.join(ROOT, pasta)
    pid = os.path.basename(src)
    out = os.path.join(_media(), pid)
    os.makedirs(out, exist_ok=True)
    pngs = sorted(f for f in os.listdir(src) if f.startswith("slide-") and f.endswith(".png"))
    mp4 = sorted(f for f in os.listdir(src) if f.endswith(".mp4"))
    stories = sorted(f for f in os.listdir(src) if f.startswith("story-") and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
    arquivos = []
    if stories:  # Story: cada quadro vira 1080x1920 (foto inteira sobre fundo desfocado), sem legenda
        for f in stories:
            jpg = os.path.splitext(f)[0] + ".jpg"
            story_1080(Image.open(os.path.join(src, f))).save(os.path.join(out, jpg), quality=95)
            arquivos.append(f"{pid}/{jpg}")
        tipo = "story"
    elif mp4:
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
    open(os.path.join(_root(), leg_rel), "w", encoding="utf-8").write(leg)
    c = [e for e in cal_load() if e["id"] != pid]
    novo = {"id": pid, "tipo": tipo, "arquivos": arquivos, "legenda": leg_rel,
            "data": opts.get("--data", ""), "hora": opts.get("--hora", "18:00"), "status": "pendente"}
    if opts.get("--pilar"):
        novo["pilar"] = opts["--pilar"]
    rot = os.path.join(src, "fonte", "roteiro.json")
    if tipo == "reel" and os.path.exists(rot):  # Reel narrado: registra a voz (padrão: Antonio)
        novo["voz"] = json.load(open(rot, encoding="utf-8")).get("voz", "pt-BR-AntonioNeural")
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


def ja_publicado(e, horas=72):
    """Trava contra post duplicado: se a legenda já está num post recente da conta (publicado pelo painel
    ou pelo GitHub Actions), marca como publicado e devolve True em vez de publicar de novo."""
    alvo = " ".join(legenda(e).split())[:120]
    if not alvo:
        return False
    try:
        recentes = api("GET", f"{user_id()}/media", {"fields": "id,caption,permalink,timestamp", "limit": 12}).get("data", [])
    except SystemExit:
        return False
    limite = datetime.now(TZ) - timedelta(hours=horas)
    for m in recentes:
        if " ".join((m.get("caption") or "").split())[:120] != alvo:
            continue
        try:
            quando = datetime.strptime(m.get("timestamp", ""), "%Y-%m-%dT%H:%M:%S%z").astimezone(TZ)
        except ValueError:
            quando = datetime.now(TZ)
        if quando >= limite:
            e.update(status="publicado", media_id=m["id"], link=m.get("permalink", ""),
                     publicado_em=quando.strftime("%Y-%m-%d %H:%M"))
            return True
    return False


def cmd_agendados(a):
    # --folga N: só publica posts vencidos há N minutos ou mais. O GitHub Actions usa --folga 25 porque o painel
    # aberto publica na hora certa (janela de 0 a 20 min); assim os dois nunca disputam o mesmo post.
    folga = timedelta(minutes=int(dict(zip(a[::2], a[1::2])).get("--folga", 0)))
    c = cal_load(); now = datetime.now(TZ); feitos = 0
    for e in c:
        if e["status"] != "aprovado" or not e["data"]:
            continue
        quando = datetime.strptime(f"{e['data']} {e['hora']}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if quando + folga <= now:
            try:
                if ja_publicado(e):
                    print(f"{e['id']} já estava no ar ({e.get('link')}): só atualizei o calendário.")
                    cal_save(c)
                    continue
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


def cmd_desempenho(a):
    """Validação semanal: alcance, envios, salvamentos e seguidores por post, com a mediana da conta.
    Mostra o que o algoritmo usa para decidir se leva o post a quem não segue (envios por alcance, retenção)."""
    n = int(dict(zip(a[::2], a[1::2])).get("--n", 15))
    uid = user_id()
    c = api("GET", uid, {"fields": "username,followers_count,media_count"})
    agora = int(time.time())
    tot = api("GET", f"{uid}/insights", {"metric": "reach,views,profile_views,accounts_engaged,website_clicks", "period": "day",
                                         "metric_type": "total_value", "since": str(agora - 28 * 86400), "until": str(agora)})
    t = {x["name"]: x.get("total_value", {}).get("value", 0) for x in tot.get("data", [])}
    print(f"@{c.get('username')} · {c.get('followers_count')} seguidores · {c.get('media_count')} posts")
    print(f"Últimos 28 dias: alcance {t.get('reach')} · visualizações {t.get('views')} · visitas ao perfil {t.get('profile_views')}"
          f" · contas que interagiram {t.get('accounts_engaged')} · cliques no site {t.get('website_clicks')}\n")
    media = api("GET", f"{uid}/media", {"fields": "id,caption,media_product_type,media_type,timestamp", "limit": n}).get("data", [])
    linhas = []
    for m in media:
        reel = m.get("media_product_type") == "REELS"
        met = "reach,views,saved,shares,likes,comments" + (",ig_reels_avg_watch_time" if reel else ",follows")
        try:
            ins = {x["name"]: (x.get("values") or [{}])[0].get("value", 0) for x in api("GET", f"{m['id']}/insights", {"metric": met}).get("data", [])}
        except SystemExit:
            continue
        linhas.append((m, ins, reel))
    alc = sorted(i.get("reach", 0) for _, i, _ in linhas) or [0]
    med = alc[len(alc) // 2] or 1
    print(f"{'data':<11}{'tipo':<6}{'alcance':>8}{'x med':>7}{'envios':>8}{'env/alc':>9}{'salv':>6}{'curt':>6}{'coment':>8}{'ret(s)':>8}  legenda")
    for m, i, reel in linhas:
        r = i.get("reach", 0)
        tipo = "reel" if reel else ("carr" if m.get("media_type") == "CAROUSEL_ALBUM" else "foto")
        ret = f"{i.get('ig_reels_avg_watch_time', 0) / 1000:.1f}" if reel else "-"
        cap = " ".join((m.get("caption") or "").split())[:42]
        print(f"{m['timestamp'][:10]:<11}{tipo:<6}{r:>8}{r / med:>6.1f}x{i.get('shares', 0):>8}{(i.get('shares', 0) / r * 100 if r else 0):>8.1f}%"
              f"{i.get('saved', 0):>6}{i.get('likes', 0):>6}{i.get('comments', 0):>8}{ret:>8}  {cap}")
    env = sum(i.get("shares", 0) for _, i, _ in linhas); ra = sum(i.get("reach", 0) for _, i, _ in linhas)
    print(f"\nMediana de alcance: {med} · envios por alcance no período: {env / ra * 100 if ra else 0:.1f}% (meta do plano: 1% ou mais)")
    print("Leitura: alcance perto do nº de seguidores = o post não saiu da base (falta envio/retenção, não é bloqueio).")


def cmd_renovar(a):
    print("Não é necessário: o token é de usuário do sistema (Login unificado) e não expira.")


CMDS = {"conta": cmd_conta, "preparar": cmd_preparar, "plano": cmd_plano, "aprovar": cmd_aprovar,
        "publicar": cmd_publicar, "agendados": cmd_agendados, "comentarios": cmd_comentarios,
        "responder": cmd_responder, "renovar-token": cmd_renovar, "desempenho": cmd_desempenho}

if __name__ == "__main__":
    load_env()
    args = sys.argv[1:]
    ctx = {}
    if len(args) >= 2 and args[0] == "--cliente":   # ig.py --cliente <slug> <comando> …
        import clientes
        ctx = clientes.contexto(args[1])
        args = args[2:]
    if not args or args[0] not in CMDS:
        print(__doc__); sys.exit(1)
    with usar(ctx):
        CMDS[args[0]](args[1:])
