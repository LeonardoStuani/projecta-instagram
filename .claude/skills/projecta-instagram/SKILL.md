---
name: projecta-instagram
description: Opera o Instagram @projectatech da Projecta Tech pelo terminal - preparar posts, montar o calendário, aprovar, publicar pela API oficial e responder comentários com confirmação. Use quando o Leo pedir para postar, agendar, planejar, ver o calendário, ver ou responder comentários do @projectatech.
---

# Instagram da Projecta Tech

Este repositório é a central do @projectatech. As skills /ig-* (escrita, ganchos,
legendas, plano, humanizador) criam o conteúdo; este fluxo publica.

## Antes de tudo
1. Leia `instagram/voice.md` (ou `~/.claude/instagram/voice.md`). Ele manda no tom e nas regras.
2. **Antes de criar qualquer post**, leia `instagram/referencias/benchmark-leventech.md`: princípios de autoridade (sistema visual travado, palavra-conceito na capa, legenda longa estruturada) e onde fazer melhor que a referência (pergunta ao leitor, Lages, tom próximo). Só princípios: nunca copiar texto, arte ou ideia da Leven.
3. Rode `python3 scripts/ig.py plano` para ver o calendário atual.

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
   Carrossel: escreva `posts/<nn>-<nome>/slides.json` e rode `node scripts/carrossel/renderizar.mjs posts/<nn>-<nome>`
   (template com o rodapé padrão; gera slide-01.png… em 1080×1350 e previa.png). Reel: um .mp4 9:16.
   Legenda em `legenda.md` (dentro de um bloco ```), na "Estrutura de legenda longa" do `voice.md`.
2. **Preparar**: `python3 scripts/ig.py preparar posts/<pasta> --data AAAA-MM-DD --hora HH:MM --pilar dica`
   (converte PNG em JPEG, copia para `media/`, põe no calendário como `pendente` e imprime o checklist).
3. **Revisar com o checklist antes de aprovar** (do benchmark). Confira cada item e diga ao Leo o resultado:
   - [ ] Capa com pessoa ou palavra-conceito grande
   - [ ] Rodapé padrão presente (projectatech.com.br · WhatsApp · Lages-SC)
   - [ ] Gancho com até 9 palavras no 1º slide
   - [ ] Legenda: problema → custo → verificação → solução → prova → pergunta
   - [ ] 1 CTA só (WhatsApp ou comentário)
   - [ ] Localização Lages-SC + até 5 hashtags
   - [ ] Nada inventado: o que faltar vai em [colchetes]
   Depois mostre ao Leo as imagens e a legenda e espere o OK.
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
