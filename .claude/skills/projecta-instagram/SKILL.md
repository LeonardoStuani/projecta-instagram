---
name: projecta-instagram
description: Opera o Instagram @projectatech da Projecta Tech pelo terminal - preparar posts, montar o calendário, aprovar, publicar pela API oficial e responder comentários com confirmação. Use quando o Leo pedir para postar, agendar, planejar, ver o calendário, ver ou responder comentários do @projectatech.
---

# Instagram da Projecta Tech

Este repositório é a central do @projectatech. As skills /ig-* (escrita, ganchos,
legendas, plano, humanizador) criam o conteúdo; este fluxo publica.

## Antes de tudo
1. Leia `instagram/voice.md` (ou `~/.claude/instagram/voice.md`). Ele manda no tom e nas regras.
2. Rode `python3 scripts/ig.py plano` para ver o calendário atual.

## Regras que não mudam
- **Nada vai ao ar sem o Leo aprovar aquele post.** Aprovar = `ig.py aprovar <id>` feito por ele,
  ou um "sim" explícito no chat para aquele post específico. Um OK vale para um post.
- **Respostas a comentários sempre pedem confirmação** (`ig.py responder` pergunta antes de enviar).
- Não comentar em perfis de terceiros, não mandar DM, não seguir ninguém.
- Sem preços. Máximo 5 hashtags. CTA "Peça sua análise gratuita: link na bio." Local Lages-SC.
- Nunca inventar números, depoimentos ou resultados. O que faltar vai entre [colchetes] e não é publicado.
- Telas de sistema sempre com dados fictícios, marcadas como ilustrativas.
- Nunca imprimir, commitar ou colar o token (`IG_ACCESS_TOKEN`). Ele fica só no `.env` (fora do git) e no secret do GitHub.

## Fluxo de um post
1. **Criar**: use /ig-carousel, /ig-reel, /ig-caption e passe tudo por /ig-human.
   Gere as artes em `posts/<nn>-<nome>/` (slide-01.png… em 1080×1350, ou um .mp4 9:16) com `legenda.md`
   (a legenda dentro de um bloco ```).
2. **Preparar**: `python3 scripts/ig.py preparar posts/<pasta> --data AAAA-MM-DD --hora HH:MM`
   (converte PNG em JPEG, copia para `media/` e põe no calendário como `pendente`).
3. **Mostrar ao Leo**: as imagens e a legenda. Esperar o OK.
4. **Aprovar**: `python3 scripts/ig.py aprovar <id>` e depois `git add -A && git commit -m "..." && git push`.
   O GitHub Actions publica sozinho quando a data/hora chegar (verifica de hora em hora).
5. **Publicar já** (se o Leo pedir): `python3 scripts/ig.py publicar <id>`; mostra a legenda e pede confirmação.
   As imagens precisam estar no GitHub (push feito) antes, porque a API busca pela URL pública.

## Comentários
- `python3 scripts/ig.py comentarios --n 5` lista os comentários dos 5 posts mais recentes.
- Use /ig-reply para classificar e rascunhar respostas; mostre ao Leo.
- `python3 scripts/ig.py responder <comment_id> "texto"` só depois do OK dele (o script também confirma).

## Manutenção
- O token é de usuário do sistema (Login unificado, graph.facebook.com) e não expira. `ig.py conta` testa a conexão.
- Se trocar o token, atualize o `.env` (ou o painel) e o secret `IG_ACCESS_TOKEN` no GitHub.
- Se um post ficar com status `erro`, leia o campo `erro` no `calendario.json`, corrija e aprove de novo.
