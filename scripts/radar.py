#!/usr/bin/env python3
"""
radar.py: radar do Instagram da Projecta (seus posts + referências do nicho), só pela API oficial.

    python scripts/radar.py

Fontes:
  1. Seus posts (@projectatech): curtidas e comentários sempre. Alcance, salvamentos,
     compartilhamentos e visualizações quando o token tiver a permissão instagram_manage_insights.
  2. Contas do nicho (instagram/radar/contas.json): posts públicos de contas profissionais, via
     Business Discovery da API oficial (precisa da mesma permissão). Nada de raspagem.
  3. Coleta manual (instagram/radar/manual.json): posts que você ou o Cowork anotaram pelo app.
  4. YouTube (instagram/viral/ultimo.json, do viral.py antigo): só entra se for MUITO do nicho,
     e o painel esconde por padrão.

Tudo passa pelo filtro de relevância (palavras do nicho em contas.json). Post que não fala do
seu ramo não entra. O ranking é quanto cada post superou a MEDIANA da própria conta (×).

Saída: instagram/radar/ultimo.json (lido pelo painel) e instagram/radar/AAAA-MM-DD.json (histórico).
Nunca imprime o token.
"""
import json, os, re, statistics, sys, unicodedata
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig  # noqa: E402

ROOT = ig.ROOT
# RADAR_CLIENTE=<slug>: radar do nicho de um cliente da agência (pasta clientes/<slug>/radar).
CLIENTE = os.environ.get("RADAR_CLIENTE", "")
DIR = os.path.join(ROOT, "clientes", CLIENTE, "radar") if CLIENTE else os.path.join(ROOT, "instagram", "radar")
CONF = os.path.join(DIR, "contas.json")
MANUAL = os.path.join(DIR, "manual.json")
YT = os.path.join(ROOT, "instagram", "viral", "ultimo.json")

CONF_PADRAO = {
    "contas": ["leventech"],
    "palavras": ["site", "sites", "landing page", "pagina", "sistema", "sistemas", "software", "gestao", "erp",
                 "planilha", "excel", "automacao", "automatizar", "whatsapp", "google", "seo", "trafego",
                 "presenca online", "pequena empresa", "orcamento",
                 "financeiro", "aplicativo", "saas", "dashboard", "desenvolvimento",
                 "programacao", "codigo", "dominio", "hospedagem", "loja virtual", "e-commerce", "crm"],
}

TEMAS = {
    "Site e landing page": ["site", "landing", "pagina", "dominio", "hospedagem", "loja virtual", "e-commerce"],
    "Sistema e gestão": ["sistema", "gestao", "erp", "software", "saas", "crm", "dashboard", "aplicativo", " app"],
    "Planilha e organização": ["planilha", "excel", "organiza", "caderno", "retrabalho", "controle"],
    "Google e ser encontrado": ["google", "seo", "busca", "encontrad", "pesquis", "meu negocio"],
    "WhatsApp e atendimento": ["whatsapp", "atendimento", "responder", "mensagem"],
    "IA e automação": [" ia ", "inteligencia artificial", "automa", "chatgpt", "robo"],
    "Prova, case e bastidor": ["case", "antes e depois", "cliente real", "resultado", "bastidor", "equipe", "projeto entregue"],
    "Oferta e proposta": ["analise gratuita", "proposta", "orcamento", "promo", "desconto", "vagas"],
}


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return " " + "".join(c for c in s if not unicodedata.combining(c)) + " "


def relevancia(texto, palavras):
    t = norm(texto)
    return sum(1 for p in palavras if re.search(r"(?<![a-z])" + re.escape(p), t))


def temas(texto):
    t = norm(texto)
    achados = [nome for nome, ps in TEMAS.items() if any(p in t for p in ps)]
    return achados or ["Outros"]


def gancho(caption):
    linha = next((l.strip() for l in (caption or "").splitlines() if l.strip()), "")
    return linha[:160]


def tipo(m):
    pt, mt = m.get("media_product_type"), m.get("media_type")
    if pt == "REELS" or mt == "VIDEO":
        return "Reel"
    return {"CAROUSEL_ALBUM": "Carrossel", "IMAGE": "Imagem"}.get(mt, mt or "?")


def sem_permissao(msg):
    return "(#10)" in msg or "permission" in msg.lower() or "Public Content" in msg


def api(path, params):
    try:
        return ig.api("GET", path, params), None
    except SystemExit as e:
        return None, str(e)


def meus_posts(uid, seguidores, aviso):
    cal = {e.get("media_id"): e for e in ig.cal_load() if e.get("media_id")}
    out, after, insights_ok = [], None, True
    while True:
        p = {"fields": "id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", "limit": 50}
        if after:
            p["after"] = after
        r, err = api(f"{uid}/media", p)
        if err:
            aviso.append("Não consegui ler seus posts: " + err[:200])
            break
        for m in r.get("data", []):
            item = {"id": m["id"], "data": m["timestamp"][:10], "hora": m["timestamp"][11:16], "tipo": tipo(m),
                    "gancho": gancho(m.get("caption")), "legenda": (m.get("caption") or "")[:600],
                    "likes": m.get("like_count", 0), "comentarios": m.get("comments_count", 0),
                    "link": m.get("permalink"), "temas": temas(m.get("caption")),
                    "pilar": (cal.get(m["id"]) or {}).get("pilar"), "post": (cal.get(m["id"]) or {}).get("id")}
            if insights_ok:
                ins, err = api(f"{m['id']}/insights", {"metric": "reach,saved,shares,views,total_interactions"})
                if err and sem_permissao(err):
                    insights_ok = False
                elif ins:
                    for x in ins.get("data", []):
                        v = x.get("values", [{}])[0].get("value") if x.get("values") else x.get("total_value", {}).get("value")
                        item[{"reach": "alcance", "saved": "salvos", "shares": "compart", "views": "views",
                              "total_interactions": "interacoes_api"}[x["name"]]] = v
            item["interacoes"] = item["likes"] + item["comentarios"] + (item.get("salvos") or 0) + (item.get("compart") or 0)
            item["taxa"] = round(item["interacoes"] / seguidores * 100, 2) if seguidores else None
            out.append(item)
        after = (r.get("paging") or {}).get("cursors", {}).get("after") if (r.get("paging") or {}).get("next") else None
        if not after:
            break
    med = statistics.median([x["interacoes"] for x in out]) if out else 0
    for x in out:
        x["mult"] = round(x["interacoes"] / med, 2) if med else None
    return out, insights_ok


def contas_nicho(uid, contas, palavras, aviso):
    refs, resumo, ok = [], [], True
    for u in contas:
        u = u.strip().lstrip("@")
        if not u:
            continue
        f = ("business_discovery.username(%s){username,name,followers_count,media_count,"
             "media.limit(40){caption,like_count,comments_count,view_count,media_type,media_product_type,timestamp,permalink}}" % u)
        r, err = api(uid, {"fields": f})
        if err:
            if sem_permissao(err):
                ok = False
                resumo.append({"conta": u, "erro": "sem permissão no token"})
                continue
            resumo.append({"conta": u, "erro": "não encontrada ou não é conta profissional"})
            continue
        bd = r.get("business_discovery", {})
        posts = (bd.get("media") or {}).get("data", [])
        for m in posts:
            m["_int"] = m.get("like_count", 0) + m.get("comments_count", 0)
        med = statistics.median([m["_int"] for m in posts]) if posts else 0
        rel = 0
        for m in posts:
            cap = m.get("caption") or ""
            score = relevancia(cap, palavras)
            if score < 1:
                continue
            rel += 1
            refs.append({"fonte": "instagram", "conta": bd.get("username", u), "seguidores": bd.get("followers_count"),
                         "data": (m.get("timestamp") or "")[:10], "tipo": tipo(m), "gancho": gancho(cap),
                         "legenda": cap[:600], "likes": m.get("like_count", 0), "comentarios": m.get("comments_count", 0),
                         "views": m.get("view_count"), "interacoes": m["_int"], "mediana": med,
                         "mult": round(m["_int"] / med, 2) if med else None, "link": m.get("permalink"),
                         "temas": temas(cap), "relevancia": score})
        resumo.append({"conta": bd.get("username", u), "seguidores": bd.get("followers_count"), "posts": len(posts),
                       "relevantes": rel, "mediana": med})
    if not ok:
        aviso.append("Contas do nicho: o token não tem a permissão instagram_manage_insights (Business Discovery).")
    return refs, resumo, ok


def manuais(palavras):
    if not os.path.exists(MANUAL):
        return []
    refs = []
    lista = json.load(open(MANUAL, encoding="utf-8"))
    por_conta = {}
    for m in lista:
        m["interacoes"] = (m.get("likes") or 0) + (m.get("comentarios") or 0)
        por_conta.setdefault(m.get("conta", "?"), []).append(m["interacoes"])
    for m in lista:
        txt = (m.get("legenda") or "") + " " + (m.get("gancho") or "")
        if relevancia(txt, palavras) < 1:
            continue
        vals = por_conta.get(m.get("conta", "?"), [])
        med = m.get("mediana") or (statistics.median(vals) if len(vals) >= 3 else None)
        mult = m.get("mult") or (round(m["interacoes"] / med, 2) if med else None)
        refs.append({"fonte": "manual", "conta": m.get("conta"), "seguidores": m.get("seguidores"), "data": m.get("data"),
                     "tipo": m.get("tipo", "?"), "gancho": m.get("gancho") or gancho(m.get("legenda")),
                     "legenda": (m.get("legenda") or "")[:600], "likes": m.get("likes"), "comentarios": m.get("comentarios"),
                     "views": m.get("views"), "interacoes": m["interacoes"], "mediana": med, "mult": mult,
                     "link": m.get("link"), "temas": temas(txt), "relevancia": relevancia(txt, palavras)})
    return refs


def youtube(palavras):
    if not os.path.exists(YT):
        return []
    d = json.load(open(YT, encoding="utf-8"))
    out = []
    for o in d.get("outliers", []):
        if o.get("anuncio"):
            continue
        txt = (o.get("hook") or "") + " " + (o.get("titulo") or o.get("title") or "")
        score = relevancia(txt, palavras)
        if score < 2:   # YouTube só entra se for muito do nicho
            continue
        out.append({"fonte": "youtube", "conta": o.get("canal"), "seguidores": o.get("seguidores"), "data": d.get("data"),
                    "tipo": "Short", "gancho": (o.get("hook") or "")[:160], "legenda": "", "views": o.get("views"),
                    "interacoes": None, "mult": o.get("mult"), "link": o.get("url"), "temas": temas(txt), "relevancia": score})
    return out


def media(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def agrupar(itens, chave, valor):
    g = {}
    for x in itens:
        ks = x.get(chave)
        for k in (ks if isinstance(ks, list) else [ks or "sem"]):
            g.setdefault(k, []).append(x.get(valor))
    return sorted([{"nome": k, "n": len(v), "media": media(v)} for k, v in g.items()],
                  key=lambda r: -(r["media"] or 0))


def main():
    global TEMAS
    ig.load_env()
    os.makedirs(DIR, exist_ok=True)
    if not os.path.exists(CONF):
        json.dump({"contas": [], "palavras": [], "temas": {}} if CLIENTE else CONF_PADRAO,
                  open(CONF, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    conf = json.load(open(CONF, encoding="utf-8"))
    palavras = [norm(p).strip() for p in (conf.get("palavras") or ([] if CLIENTE else CONF_PADRAO["palavras"]))]
    if conf.get("temas"):   # temas do ramo do cliente: {"Nome do tema": ["palavra", ...]}
        TEMAS = {k: [norm(x).strip() for x in v] for k, v in conf["temas"].items()}
    aviso = []
    if CLIENTE and not palavras:
        aviso.append("Cadastre as palavras do ramo do cliente (Radar → Contas e palavras) para filtrar as referências.")

    uid = ig.user_id()   # conta da agência: é ela que consulta as contas do nicho (business_discovery)
    if CLIENTE:
        import clientes
        ctx = clientes.contexto(CLIENTE)
        if ctx.get("IG_ACCESS_TOKEN"):
            with ig.usar(ctx):
                cuid = ig.user_id()
                c, err = api(cuid, {"fields": "username,followers_count,media_count"})
                seguidores = (c or {}).get("followers_count") or 0
                meus, insights_ok = meus_posts(cuid, seguidores, aviso)
        else:
            c, seguidores, meus, insights_ok = {"username": clientes.carregar(CLIENTE).get("arroba")}, 0, [], True
            aviso.append("Instagram do cliente ainda não conectado: o radar mostra só as referências do nicho.")
    else:
        c, err = api(uid, {"fields": "username,followers_count,media_count"})
        seguidores = (c or {}).get("followers_count") or 0
        meus, insights_ok = meus_posts(uid, seguidores, aviso)
    if not insights_ok:
        aviso.append("Seus posts: sem alcance/salvos/compartilhamentos/views (falta a permissão instagram_manage_insights). "
                     "Por enquanto o radar usa curtidas + comentários.")
    refs_ig, contas, disc_ok = contas_nicho(uid, conf.get("contas", []), palavras, aviso)
    refs = refs_ig + manuais(palavras) + ([] if CLIENTE else youtube(palavras))
    refs.sort(key=lambda r: -(r.get("mult") or 0))

    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    for x in meus:
        x["dia_semana"] = dias[datetime.strptime(x["data"], "%Y-%m-%d").weekday()]
    ganchos = [{"texto": r["gancho"], "mult": r.get("mult"), "conta": r["conta"], "fonte": r["fonte"], "link": r.get("link")}
               for r in refs if r.get("gancho") and (r.get("mult") or 0) >= 1.5][:40]
    ganchos += [{"texto": x["gancho"], "mult": x.get("mult"), "conta": (c or {}).get("username") or "projectatech", "fonte": "seu", "link": x["link"]}
                for x in sorted(meus, key=lambda x: -(x.get("mult") or 0))[:5] if x.get("gancho")]

    ordem = sorted(meus, key=lambda x: -(x.get("mult") or 0))
    out = {
        "data": date.today().isoformat(), "gerado_em": datetime.now(ig.TZ).strftime("%Y-%m-%d %H:%M"),
        "conta": {"username": (c or {}).get("username"), "seguidores": seguidores, "posts": (c or {}).get("media_count")},
        "permissoes": {"insights": insights_ok, "contas_nicho": disc_ok}, "avisos": aviso,
        "meus": sorted(meus, key=lambda x: x["data"]),
        "melhores": [x["id"] for x in ordem[:3]] if len(meus) >= 2 else [],
        "piores": [x["id"] for x in ordem[-3:][::-1]] if len(meus) >= 4 else [],
        "por_formato": agrupar(meus, "tipo", "interacoes"),
        "por_pilar": agrupar(meus, "pilar", "interacoes"),
        "por_dia": agrupar(meus, "dia_semana", "interacoes"),
        "temas_meus": agrupar(meus, "temas", "interacoes"),
        "referencias": refs[:120],
        "temas_nicho": agrupar([r for r in refs if r["fonte"] != "youtube"], "temas", "mult"),
        "formatos_nicho": agrupar([r for r in refs if r["fonte"] != "youtube"], "tipo", "mult"),
        "ganchos": ganchos,
        "contas": contas,
    }
    for nome in ("ultimo.json", f"{out['data']}.json"):
        json.dump(out, open(os.path.join(DIR, nome), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Radar: {len(meus)} posts seus, {len(refs)} referências relevantes de {len(contas)} conta(s).")
    for a in aviso:
        print("Aviso:", a)


if __name__ == "__main__":
    main()
