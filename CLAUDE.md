# Projecta Tech · Instagram

Central de conteúdo e publicação do @projectatech.

- Use a skill `projecta-instagram` para qualquer pedido de postar, agendar, ver calendário ou comentários.
- Use as skills `/ig-*` (pasta `.claude/skills/`) para escrever: ganchos, roteiros, legendas, carrosséis, plano da semana, auditoria. Sempre em português do Brasil.
- `instagram/voice.md` define tom, regras e o que nunca publicar (preços, dados de clientes sem autorização).
- Nada é publicado e nenhum comentário é respondido sem o OK explícito do Leo para aquele item.
- Nunca mostre, registre ou faça commit do token. Ele vive no `.env` (ignorado pelo git) e nos secrets do GitHub.
- **Agência (clientes):** o painel também atende clientes da agência, cada um em `clientes/<slug>/` (fora do git). Para qualquer conteúdo de cliente use a skill `agencia` (`/agencia <cliente> ...`): ela troca a voz, o CTA e as regras pelas do cliente. Fluxo: Claude cria → Leo envia ao cliente → cliente aprova no portal → Leo agenda → painel publica. Nunca leia nem mostre `segredos/`.
