# Reel: "Link da bio que vende", narrado (27 s)

```
O link da bio é a porta da sua empresa no Instagram. E quase sempre é uma lista de botões iguais.

O cliente abre, não sabe onde tocar e vai embora.

O nosso mostra o que importa de cara: uma ação clara no topo, os serviços por ícone, um projeto real e o WhatsApp sempre à mão, com a mensagem pronta. Tudo no endereço da própria empresa.

Toca no link da nossa bio e vê funcionando.
📲 Quer um assim? Chama no WhatsApp: (49) 99959-2640

O link da sua bio hoje é uma lista ou uma vitrine?

#Lages #LagesSC #SerraCatarinense #LinkNaBio #MarketingDigital
```

## Como foi feito
- **Primeira cena (link de lista):** ilustração genérica, sem a marca de nenhuma ferramenta. O rodapé avisa: "1ª cena ilustrativa · a 2ª página é real".
- **Segunda cena:** captura real de projectatech.com.br/links no celular (390 px, 3x), feita em 23/11.
- **Voz:** Antonio (pt-BR-AntonioNeural, via edge-tts), a voz padrão.
- **Música e efeitos:** batida original sintetizada (trilha.py), sem direitos de terceiros.

Para refazer:
0. `python scripts/video/voz.py posts/21-reel-link-da-bio`
1. `python scripts/video/trilha.py posts/21-reel-link-da-bio`
2. `node scripts/video/renderizar.mjs posts/21-reel-link-da-bio/fonte/reel.html posts/21-reel-link-da-bio/fonte/prev/mudo.mp4`
3. Junte o vídeo e o áudio com ffmpeg, usando `loudnorm=I=-14`.

Se a página /links mudar, refaça as capturas antes (`assets/links-pagina.png` e `assets/barra-whatsapp.png`).
