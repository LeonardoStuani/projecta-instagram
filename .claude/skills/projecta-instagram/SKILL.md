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
   (template com o rodapé padrão; gera slide-01.png… em 1080×1350 e previa.png).
   Reel sem gravar (o Leo não tem tempo de filmar): siga /bang-motion (um mundo contínuo, câmera que se move, nada de slideshow,
   no máximo 2 níveis de texto por cena). Escreva `posts/<nn>-reel-<nome>/fonte/reel.html` em 1080×1920 com GSAP
   (copie um dos reels 14 ou 15; `window.montar(tl, q)` + `scripts/video/kit.js` + `base.css`) e rode
   `node scripts/video/renderizar.mjs posts/<pasta>/fonte/reel.html posts/<pasta>/reel-<nome>.mp4 [--preview 2,8,15]`
   (Playwright + Edge capturam 30 fps; ffmpeg do Python portátil monta o MP4 H.264 com trilha muda).
   Confira as prévias (`python scripts/video/folha.py` monta a folha de contato) antes de mostrar ao Leo.
   Telas fictícias marcadas "Ilustrativo".
   **Padrão desde 19/11/2026: Reel narrado** (modelo: `posts/16-reel-gestao`). Voz padrão: **Antonio**
   (`pt-BR-AntonioNeural`, Microsoft, via edge-tts), aprovada pelo Leo. Não use Kokoro/`hyperframes tts`: o sotaque não é brasileiro.
   a) Escreva `fonte/roteiro.json` (`voz`, `bpm`, `drop`, `fim`, `corte_batida`, `falas` com `t` e `texto`, `sfx`);
   b) `python scripts/video/voz.py posts/<pasta>` gera `fonte/voz/lN.wav` e acelera a fala que não couber (se avisar "NÃO CABE", afaste os `t`);
   c) `python scripts/video/trilha.py posts/<pasta>` mixa voz + batida original + efeitos e gera `fonte/legendas.js` (palavra a palavra);
   d) renderize o `reel.html` (sincronize com `at(fala, "palavra")`) para `fonte/prev/mudo.mp4` e junte com
      `ffmpeg -i mudo.mp4 -i fonte/audio/mix.wav -c:v copy -c:a aac -b:a 192k -af loudnorm=I=-14:TP=-1.5:LRA=11 -shortest -movflags +faststart reel-<nome>.mp4`.
   O `preparar` grava `voz` no calendário e o painel mostra "Narração: Antonio". Publicar com o áudio original.
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
