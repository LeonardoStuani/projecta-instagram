# Reel: "Procurei você no Google", narrado (33 s)

```
Seu próximo cliente acabou de pegar o celular.

Ele pesquisou o que você faz, aqui em Lages, e apareceram os outros. Quando ele te acha, encontra só um perfil, sem horário nem endereço, e desiste. Em dez segundos ele já marcou com outro.

Post some em dois dias. Site fica no ar 24 horas por dia, trazendo quem já está procurando o que você vende.

Seu site no ar em 7 dias.
📲 Chama no WhatsApp: (49) 99959-2640

Você aparece quando alguém pesquisa o seu serviço em Lages?

#Lages #LagesSC #SerraCatarinense #CriacaoDeSites #GoogleMeuNegocio
```

## Como foi feito
- **Busca, resultados, perfil e site do concorrente:** são ilustrações genéricas. Não têm a marca de nenhum buscador e não aparece nome de empresa real (ficam desfocados). O rodapé do vídeo avisa: "Cena ilustrativa · nomes ocultos · sites do final são reais".
- **Sites do final:** capturas reais do projecta.tech e da Eixo Sul (cliente).
- **Voz:** Antonio (pt-BR-AntonioNeural, via edge-tts), a voz padrão.
- **Música e efeitos:** batida original sintetizada (trilha.py), sem direitos de terceiros.

Para refazer:
0. `python scripts/video/voz.py posts/20-reel-procurei-no-google`
1. `python scripts/video/trilha.py posts/20-reel-procurei-no-google`
2. `node scripts/video/renderizar.mjs posts/20-reel-procurei-no-google/fonte/reel.html posts/20-reel-procurei-no-google/fonte/prev/mudo.mp4`
3. Junte o vídeo e o áudio com ffmpeg, usando `loudnorm=I=-14`.

Variações do roteiro (troque o `BUSCA` no reel.html e o texto da fala 2 no roteiro.json): "limpeza de pele em Lages", "fotógrafo de casamento Lages", "almoço perto de mim".
