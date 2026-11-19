# Reel: Projecta Gestão, narrado (27,6 s)

```
Seu escritório ainda controla obra em planilha?

Cliente numa aba, orçamento em outra, o prazo na cabeça de alguém. Funciona até o dia em que alguém pergunta "em que pé está aquele projeto?" e ninguém sabe responder rápido.

No Projecta Gestão fica tudo numa tela só:
📊 Dashboard com clientes, orçamentos e projetos ativos
📝 Orçamento aprovado vira projeto
✅ Cada etapa com responsável, status e prazo
💸 Financeiro com o que entra, o que sai e o mês fechado
🛡️ Auditoria: cada ação fica registrada, com quem fez e quando

Feito para escritório técnico: topografia, engenharia e agrimensura, aqui de Lages.

Quantas planilhas o seu escritório usa hoje para controlar uma obra?

Peça sua análise gratuita: link na bio.

#Lages #LagesSC #SerraCatarinense #SistemaDeGestao #Topografia
```

## Como foi feito
- **Telas:** reais, capturadas do projecta-demo.com.br (base de demonstração). Os nomes e e-mails foram trocados por genéricos ("Sua Empresa", "Cliente 5").
- **Animação ilustrativa:** a troca de status de APROVADO para PROJETO e a barra de progresso enchendo. O próprio vídeo avisa isso no rodapé.
- **Voz:** sintética, Microsoft Antonio (pt-BR-AntonioNeural, via `edge-tts`, gratuita e online). É a voz padrão dos Reels.
- **Música:** batida original sintetizada, sem direitos de terceiros.
- **Efeitos:** whoosh, clique e impacto, também sintetizados.
- **Volume:** -15 LUFS.

Para refazer:
0. `python scripts/video/voz.py posts/16-reel-gestao` gera as falas com o Antonio.
1. `python scripts/video/trilha.py posts/16-reel-gestao` monta a voz, a música, os efeitos e a legenda, a partir de `fonte/roteiro.json`.
2. `node scripts/video/renderizar.mjs posts/16-reel-gestao/fonte/reel.html posts/16-reel-gestao/fonte/prev/mudo.mp4` renderiza o vídeo sem som.
3. Junte o vídeo e o áudio com ffmpeg, usando `loudnorm=I=-14`.

Para trocar o texto: edite `fonte/roteiro.json` e rode os passos 0 a 3. O `voz.py` acelera sozinho a fala que não couber no tempo.
