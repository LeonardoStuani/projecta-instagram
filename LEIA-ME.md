# Projecta Tech · Agente do Instagram

Central do @projectatech para usar no Claude Code pelo terminal.

- **Escrever**: 13 skills `/ig-*` (do repositório MIT [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill), revisado em 17/11/2026: só Python padrão, sem rede, sem senha).
- **Publicar**: `scripts/ig.py` usa a API oficial da Meta (Business Login for Instagram). Posts aprovados saem sozinhos pelo GitHub Actions.
- **Regras**: `instagram/voice.md` e a skill `projecta-instagram`. Nada sai sem o seu OK.

```
.claude/skills/ig-*               skills de escrita (ganchos, legendas, carrossel, plano, humanizador…)
.claude/skills/projecta-instagram fluxo de publicação da Projecta
instagram/voice.md                tom, regras, provas, CTA
posts/                            artes originais (PNG/MP4 + legenda.md), destaques e foto de perfil
media/                            versão publicável (JPEG) que o Instagram baixa
calendario.json                   o que sai, quando e em que status
scripts/ig.py                     linha de comando
.github/workflows/                publicação automática de hora em hora
```

---

## 1. Instalar (uma vez, ~15 min)

### 1.1 Repositório no GitHub
1. Crie um repositório **público** chamado `projecta-instagram` (público porque o Instagram busca as imagens pelo link).
2. No terminal, dentro desta pasta:
   ```bash
   git init && git add -A && git commit -m "Agente do Instagram da Projecta"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/projecta-instagram.git
   git push -u origin main
   ```

### 1.2 Token da API (você faz; eu nunca vejo o token)
A Meta só oferece o **Login unificado** para apps novos: o token é de **usuário do sistema**, começa com `EAA`, **não expira** e usa `graph.facebook.com`.
1. Em **developers.facebook.com → Meus apps**, abra o app da Projecta.
2. **Casos de uso → API do Instagram → Login unificado → Gerar tokens de acesso** para o @projectatech.
3. Cole o token no painel (aba Conexões) ou no `.env`. O `IG_USER_ID` do @projectatech é `17841478285323581`.

### 1.3 Configurar
```bash
cp .env.example .env      # cole o token em IG_ACCESS_TOKEN e troque SEU_USUARIO na URL
pip install pillow        # só para o comando "preparar"
python3 scripts/ig.py conta   # deve terminar com "Conexão OK: @projectatech"
```
No GitHub: **Settings → Secrets and variables → Actions → New repository secret** → nome `IG_ACCESS_TOKEN`, valor = o token.
Em **Settings → Actions → General → Workflow permissions**, marque **Read and write permissions**.

### 1.4 Skills
As skills já estão em `.claude/skills/` (valem quando você abre o Claude Code nesta pasta). Para o tom:
```bash
mkdir -p ~/.claude/instagram && cp instagram/voice.md ~/.claude/instagram/voice.md
```
Abra `claude` nesta pasta e confira com `/skills`.

---

## 2. Usar no dia a dia

Fale com o Claude Code normalmente, ou rode os comandos:

| Quero… | Peça ao Claude ou rode |
|---|---|
| Ver o calendário | `python3 scripts/ig.py plano` |
| Criar um post novo | "/ig-carousel sobre Google Meu Negócio para clínicas" → depois "prepara para dia 02/12 às 18h" |
| Aprovar um post | `python3 scripts/ig.py aprovar 02-oferta-lages` + `git commit -am "aprova oferta" && git push` |
| Publicar agora | `python3 scripts/ig.py publicar 02-oferta-lages` (mostra a legenda e pergunta) |
| Ver comentários | `python3 scripts/ig.py comentarios` |
| Responder | "/ig-reply" para rascunhar → `python3 scripts/ig.py responder <id> "texto"` (pergunta antes) |
| Planejar a semana | "/ig-plan" |
| Ganchos de Reel | "/ig-reel" (traduz a estrutura para PT-BR) |
| Auditoria do perfil | "/ig-profile" e "/ig-audit" |
| Testar a conexão | `python3 scripts/ig.py conta` (o token não expira) |

**Agendamento**: o GitHub Actions roda de hora em hora e publica os posts `aprovado` cuja data e hora (horário de Brasília) já passaram. Depois ele grava o link no `calendario.json`. Também dá para disparar na mão em **Actions → Publicar posts aprovados → Run workflow**.

---

## 3. Calendário já carregado (tudo `pendente`, aguardando você aprovar)

| Data | Post | Observação |
|---|---|---|
| 18/11 18h | 02-oferta-lages | sem preço |
| 20/11 18h | 04-quem-somos | |
| 23/11 18h | 05-projecta-gestao | substitui o #3 antigo |
| 25/11 18h | 06-antes-depois | substitui o #8 |
| 27/11 18h | 08-dica-planilha | substitui o #25 |
| 30/11 18h | 07-por-que-sistema | substitui o #17 |
| sem data | 03-case-eixo-sul | Eixo Sul já autorizou; falta escolher a data |

Já publicados à mão em 17/11: post de virada e o Reel motion.

---

## 4. Limites honestos
- **Comentar em outros perfis, mandar DM e seguir** não são automatizados: a API oficial não permite, e automação por navegador viola os termos do Instagram e bloqueia contas. As skills `/ig-comment` e `/ig-dm` só escrevem o texto, e você envia.
- **Destaques, link da bio, categoria e botão de WhatsApp**: só pelo app do celular.
- **Stories pela API**: só para contas Empresa. Se a sua for Criador de conteúdo, poste stories no app.
- O Instagram limita **5 hashtags** por post e cerca de 50 a 100 publicações pela API a cada 24 h, o que dá folga.
- Nunca faça commit do `.env`. Ele já está no `.gitignore`.
