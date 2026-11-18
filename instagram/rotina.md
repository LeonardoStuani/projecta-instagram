# Rotina do @projectatech

Painel: dois cliques em `PLANO\Abrir painel do Instagram.bat`. Nada é publicado nem respondido sem o seu OK.

## Todo dia · 15 minutos
1. **Painel → Hoje.** Resolva o que estiver em vermelho: post pendente para os próximos 7 dias, erro de publicação ou conexão.
2. **Comentários** (aba Comentários do painel, ou `ig comentarios`). Peça ao Claude: "/ig-reply nos comentários de hoje". Ele rascunha, você aprova cada resposta.
3. **5 comentários de valor em perfis de empresas locais.** Peça "/ig-comment para estes 5 posts" (cole os links). O Claude só escreve o texto, e você posta pelo app. Nada de "ótimo post!": comente algo útil sobre o negócio da pessoa.
4. **Quem pedir a análise gratuita** (DM ou comentário com "SITE"): peça "/ig-dm para quem pediu análise". Você envia pelo app e marca a conversa no WhatsApp: https://wa.me/5549999592640
5. **Stories (dias úteis), de 4 a 5 quadros.** Quadro 1 com você (rosto ou mão), enquete, caixinha ou link no quadro 4. Pelo app, porque a API não põe adesivo. Tudo fica na aba **Stories** do painel: imagem, o que é cada uma, adesivo, link e horário. Quando o painel avisar que os Stories estão acabando, peça ao Claude "/ig-story da semana". Responda no direct quem votou ou respondeu, nunca quem não interagiu.

## Toda segunda · 20 minutos
1. **"/ig-audit da semana passada"**: o que teve mais alcance, salvamentos e cliques no perfil.
2. **Ajuste do plano**: arraste posts no Calendário do painel se algo precisar mudar de dia.
3. **Aprove os posts da semana** (Calendário → abrir post → Aprovar). Depois clique em **Enviar para o GitHub**. O robô publica cada um no horário.

## Todo mês · primeira segunda · 30 minutos · MONITORAMENTO DE VIRAIS
1. **Painel → Hoje → "Rodar pesquisa viral"** (ou `python scripts/viral.py`). Leva uns 5 minutos. Pesquisa Shorts públicos dos seus temas, mede quanto cada vídeo superou a média do próprio canal e separa os destaques. Os destaques acima de 200× a média são marcados como "provável anúncio".
2. Peça ao Claude: **"lê o instagram/viral/ultimo.json e atualiza o swipe.md"**. Ele compara com o mês anterior, diz o que entrou e o que saiu, e reescreve os ganchos na versão da Projecta com nota do `hookscore`.
3. Opcional, e melhor que tudo: abra a sua aba **Salvos** do Instagram e mande ao Claude 5 Reels de que você gostou, com views e seguidores do perfil. Eles entram no mesmo ranking.
4. O `/ig-plan` do mês seguinte já parte do `swipe.md` novo.

O painel avisa em **Hoje** quando a última pesquisa passa de 30 dias.

## Regras que valem sempre
- Sem preços. No máximo 5 hashtags (#Lages #LagesSC #SerraCatarinense + 2). CTA: "Peça sua análise gratuita: link na bio."
- Cliente citado só com autorização (Eixo Sul: autorizada em 17/11/2026). Telas de sistema sempre com dados fictícios e marcadas como ilustrativas.
- Copie a fórmula, nunca o vídeo de outra pessoa.
- Não comente, não siga e não mande DM pela automação: só pelo app, por você.
