---
name: agencia
description: Opera o Instagram de um CLIENTE da agência (não o @projectatech) - criar o espaço do cliente, montar a voz da marca, planejar o mês, criar carrossel/reel/legenda no ramo dele, produzir pedidos que o cliente mandou pelo portal e enviar para aprovação. Use quando o Leo disser "/agencia <cliente> ...", citar um cliente da agência pelo nome (ex.: Eixo Sul, padaria, clínica) junto de post, conteúdo, Instagram, pedido ou portal, ou pedir para cadastrar um cliente novo no painel.
---

# Agência: Instagram de clientes

O painel (`scripts/painel.py`) é a central: o @projectatech fica na raiz do repositório,
cada cliente em `clientes/<slug>/`. Clientes e credenciais NÃO vão para o GitHub
(`clientes/` e `segredos/` estão no .gitignore). Nunca mova arquivo de cliente para a raiz.

```
clientes/<slug>/
  cliente.json      nome, @, ramo, cidade, regras (cta, hashtags_fixas, palavras_busca, proibidas, promessas)
  voice.md          voz da marca DESTE cliente (manda no tom)
  calendario.json   posts e status · posts/<nn>-<nome>/ · media/
  pedidos.json      o que o cliente mandou pelo portal · pedidos/<id>/ (fotos dele)
  radar/contas.json contas de referência e palavras do ramo · radar/ultimo.json
segredos/<slug>.env token do cliente e chave do portal (nunca ler em voz alta, imprimir ou commitar)
```

## Antes de qualquer coisa
1. Descubra o slug: `python scripts/clientes.py listar`. Se não existir e o Leo pediu, crie:
   `python scripts/clientes.py criar "Nome" --arroba x --ramo "y" --cidade "Lages-SC" --cta "..."`.
2. Leia `clientes/<slug>/cliente.json` e `clientes/<slug>/voice.md`. **Para este cliente, o voice.md dele
   substitui `~/.claude/instagram/voice.md` e `instagram/voice.md`.** Quando uma skill ig-* mandar ler
   o voice.md global, leia o do cliente. Idem `swipe.md`: use `clientes/<slug>/radar/ultimo.json` como referência do ramo.
   O CTA e as hashtags fixas são os do `cliente.json`, não os da Projecta.
3. Se o voice.md ainda for o modelo (tem "[quem compra"), o primeiro trabalho é montar a voz:
   leia o site e o Instagram público do cliente, proponha o voice.md preenchido e peça o OK do Leo.
   Nada de inventar público, números ou diferenciais: o que não souber vai entre [colchetes].
4. `python scripts/ig.py --cliente <slug> plano` mostra o calendário dele.

## Regras que não mudam (valem para todo cliente)
- **Fluxo de aprovação: agência cria → envia ao cliente → cliente aprova ou pede ajuste no portal → o Leo agenda → o painel publica.**
  Você (Claude) só cria e coloca no calendário como pendente. Não envia ao cliente, não agenda,
  não publica: isso é clique do Leo no painel (ou um "sim" dele para aquele post específico).
- Sem preços, máx. 5 hashtags, um CTA só, nunca número/depoimento/resultado inventado.
- Só usar fotos que o cliente mandou (pedidos/) ou que ele autorizou por escrito. Pessoas na foto: precisa de autorização.
- Não citar outros clientes da agência nem a Projecta no conteúdo do cliente (a menos que ele peça).
- Sem comentários automáticos, DMs ou follows. Comentários só com confirmação.
- Nunca ler, imprimir ou colar o conteúdo de `segredos/`.

## Criar conteúdo
Use as skills de sempre, com a voz do cliente:
- Identidade do cliente: `clientes/<slug>/marca/` (modelo.html do carrossel, reel.html do Reel, logo, ícones).
  Se ainda não existir, crie a partir das cores, fontes e logo do site do cliente (exemplo pronto: `clientes/eixosulengenharia/marca/`).
- Carrossel: escreva `clientes/<slug>/posts/<nn>-<nome>/slides.json` e rode
  `node scripts/carrossel/renderizar.mjs clientes/<slug>/posts/<nn>-<nome>`. O renderizador usa sozinho
  `clientes/<slug>/marca/modelo.html` quando existe: nunca saia com "PROJECTA TECH" no slide de cliente.
- Reel narrado: copie `marca/reel.html` para `posts/<pasta>/fonte/`, escreva `fonte/roteiro.json` (falas) e
  `fonte/cenas.js` (uma cena por fala; `fala` conta do 0) e rode `scripts/video/voz.py` (voz Antonio) →
  `scripts/video/trilha.py` → `scripts/video/renderizar.mjs fonte/reel.html fonte/mudo.mp4` → ffmpeg com `fonte/audio/mix.wav`.
- Reel de montagem (vídeos/fotos reais do cliente, sem narração): escreva `posts/<pasta>/fonte/montagem.json`
  (clipes com `arq` relativo a `clientes/<slug>/media/`, `ini`, `dur`, `texto`, `sub`; `fim` = cartela final) e rode
  `python scripts/video/montagem.py clientes/<slug>/posts/<pasta>`. Textos usam `marca/rotulo.html` do cliente; trilha
  original do trilha.py (sem música de terceiros) + som original dos vídeos. Exemplo: `clientes/spitzzaroca/posts/01-reel-voltei`.
  Depois do preparar, ponha `capa_s` no calendário (segundo da capa do Reel).
- Stories da semana: `clientes/<slug>/posts/stories-AAAA-MM-DD/stories.json` (mesmo formato do @projectatech:
  dias → quadros com `tela`, `img`, `adesivo`, `link`, `sobre`; quadro "gravar" = foto/vídeo do cliente) e rode
  `node scripts/stories/renderizar.mjs clientes/<slug>/posts/stories-AAAA-MM-DD` (usa `marca/story.html` do cliente).
  Aparecem na aba Stories do painel com a conta do cliente selecionada. Link do adesivo = WhatsApp do cliente, nunca o da Projecta.
  O quadro 1 em vídeo animado (scripts/video/stories.mjs) ainda é só da Projecta.
- Legenda: `legenda.md` na pasta do post, entre ``` ```, passando por /ig-human.
- Depois: `python scripts/ig.py --cliente <slug> preparar clientes/<slug>/posts/<pasta> --data AAAA-MM-DD --hora 18:00`
  (ou o Leo clica em Preparar no Calendário). Mostre o print ao Leo.

## Diagnóstico e plano de crescimento orgânico (todo cliente novo, e toda segunda)
Modelo pronto, feito para o @projectatech em 20/11/2026: `PLANO/documentos/plano-crescimento-instagram-projecta.md`.
1. **Validar:** `python scripts/ig.py --cliente <slug> desempenho` (alcance x mediana, envios por alcance, retenção dos reels,
   totais de 28 dias). Alcance perto do nº de seguidores = o post não sai da base (falta envio/retenção), não é bloqueio.
   Pedir ao cliente o print de Configurações → Status da conta → Recomendações para descartar restrição.
2. **Diagnóstico** em tabela com os números reais (seguidores, alcance mediano, reel x carrossel, envios, comentários,
   buracos no calendário, posts genéricos de data, dois posts no mesmo dia, link na legenda).
3. **Métodos** (sinais confirmados pelo Mosseri: tempo assistido, curtidas e envios; envio pesa mais para quem não segue):
   conteúdo feito para ser enviado · gancho em até 2 s com texto na tela · pessoa real na câmera · séries fixas ·
   collab com clientes/parceiros · primeiros 100 seguidores pela rede local (convite pessoal, nunca comprar) ·
   responder na 1ª hora · SEO do Instagram (palavras de busca + localização) · Trial Reels quando liberar · constância.
4. **Plano de 12 semanas** (base → séries e testes → escala) com metas estimadas, marcadas como estimativa, e a lista
   do que parar de fazer. Impulsionar só o melhor reel orgânico, se o cliente quiser.

## Pedidos do portal
`clientes/<slug>/pedidos.json`: cada pedido tem tipo, texto, data_desejada, arquivos e conversa.
"Produzir os pedidos novos" = para cada pedido com status `novo`: ler o texto, olhar as fotos em
`clientes/<slug>/pedidos/<id>/`, criar o post com elas e avisar o Leo para mudar a situação para
"Em produção" e responder o cliente pelo painel. Não escreva no pedidos.json sem o Leo pedir.

## Radar do ramo
No painel (conta do cliente → Radar), o Leo cadastra contas de referência e palavras do ramo.
O radar consulta as contas com a conexão da agência. Ganchos: adapte a estrutura, nunca copie.

## Conexão e nuvem
- Conectar o Instagram do cliente: com o painel na nuvem (HTTPS + META_APP_ID/META_APP_SECRET),
  o cliente toca em "Conectar meu Instagram" no portal. Sem nuvem: o Leo cola o token em Conexões.
- Carrossel/foto de cliente precisa de URL pública para as imagens (painel na nuvem ou IG_MEDIA_BASE_URL do cliente).
  Reel não precisa (upload direto).
- Publicação dos clientes: o agendador do painel, a cada 5 min, enquanto o painel estiver aberto
  (no PC do Leo ou na VPS). O @projectatech continua no GitHub Actions.
- Deploy: `deploy/LEIA-ME.md`.
