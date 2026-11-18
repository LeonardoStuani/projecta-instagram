# Swipe file · Projecta Tech

Lido por `/ig-reel` e `/ig-plan`. Atualizado todo mês pela rotina (`python scripts/viral.py`, depois o Claude relê e reescreve este arquivo).

**Pesquisa de 17/11/2026** · 193 Shorts de 8 canais brasileiros (YouTube, porque as views são públicas e não precisa de login) · temas: criação de site, landing page, Google Meu Negócio, sistema de gestão, planilha, WhatsApp, marketing para clínica e oficina.
Ranking pelo **multiplicador sobre a mediana do próprio canal**, não por views. Dados brutos: `instagram/viral/2026-11-17.tsv` e `instagram/viral/2026-11-17-ranking.md`.

**Confiança: baixa a média.** A amostra é pequena, os canais do mesmo porte que o @projectatech têm poucas views (sinal fraco) e o Omie tem números de anúncio pago, não orgânico. Use como direção, e confirme com as métricas dos seus próprios posts.

---

## O que está funcionando (por ordem de força da evidência)

### 1. Um vídeo por nicho, com o nicho no título (#14 The Callout)
O sinal mais consistente da amostra: o mesmo canal (CAZAR, produtora de vídeo) teve **4 dos seus vídeos mais fortes** com o formato "Vídeo para [ramo]".

| Multiplicador | Gancho | Link |
|---|---|---|
| 19,3× | "Vídeo para profissionais de Arquitetura" | https://www.youtube.com/shorts/WcZrFecLv4A |
| 12,5× | "Vídeo para empresa de limpeza" | @cazarvideo |
| 7,4× | "Vídeo para empresa de energia solar" | @cazarvideo |
| 4,0× | "Vídeo para arquitetura" | @cazarvideo |

**Por que funciona:** o dono do negócio se reconhece no primeiro segundo. Encaixa exatamente nos nichos da Projecta.

### 2. Cliente contando a própria história, em primeira pessoa (depoimento)
O Omie (sistema de gestão para PMEs) escalou com verba de anúncio justamente esse formato: um cliente real se apresentando pelo nome e cargo. Também apareceu em canal pequeno.

| Multiplicador | Gancho | Observação |
|---|---|---|
| anúncio | "Oi, tudo bem? Meu nome é Ana Clara, eu sou gerente de compras" | Omie, 2,7 mi views (pago) |
| anúncio | "Olá, tudo bem com vocês? Eu sou Cristiano Cerqueira, contador" | Omie, 1,3 mi views (pago) |
| anúncio | "A Francine não costuma falar muito" | Omie, 681 mil (pago) |
| 4,3× | "Meu movimento clínico e cirúrgico aumentou bastante" | @bezaleel_lucas (orgânico) |

**Por que importa:** o que uma empresa de sistema escolheu pagar para escalar é o formato que vende sistema. A Eixo Sul já autorizou o case: este é o formato para ela.

### 3. Lista numerada com custo ou risco (#11 / #1)
| Multiplicador | Gancho |
|---|---|
| anúncio | "Cinco mitos sobre migração de regime que podem custar caro" (Omie, 5,3 mi) |

A Projecta já tem esse formato pronto no `08-dica-planilha` ("5 riscos de gerenciar sua empresa por planilha").

### 4. Demonstração começando no meio da ação (#18 Cold Open Demo)
| Multiplicador | Gancho | Link |
|---|---|---|
| 33,3× | "Vamos colocar aqui, ó, chat: 'Desenvolva…'" | https://www.youtube.com/shorts/cbxTH0hAqKM |
| anúncio | "Ele apresentou o Omie" | Omie |

O Reel `10-reel-site-novo` já usa esse formato (abre na busca, sem introdução).

### 5. Pergunta que o dono de empresa faz (#16 The Verbatim Question)
| Multiplicador | Gancho |
|---|---|
| 5,3× | "Como controlar as contas de uma pequena empresa?" (@destravaaiseusrecebiveis) |
| 3,1× | "Qual a diferença entre custo e despesa?" (@destravaaiseusrecebiveis) |

### 6. Gravado no lugar, "a gente tá aqui em…" (bastidores em campo)
| Multiplicador | Gancho | Link |
|---|---|---|
| 41,7× | "Nossa, tem um restaurante italiano." | https://www.youtube.com/shorts/WFbERPK0qFU |
| 33,3× | "E agora a gente está aqui em Porto Velho, chegamos" | https://www.youtube.com/shorts/f4VqC-js4SU |

Canal pequeno (mediana 36 views): sinal fraco, mas é o formato de bastidores mais barato de gravar.

---

## Fora da regra: o que NÃO copiar
- **Os números do Omie** (de 2.000× a 17.000× a mediana) são de anúncio pago. Servem para escolher o formato, não como meta de alcance.
- **Abrir com "Oi, tudo bem?"** só funciona porque o anúncio já tem distribuição paga. No orgânico, o `hookscore` zera esse tipo de abertura: corte o cumprimento e comece na frase seguinte.

---

## A versão da Projecta (pronta para o `/ig-reel`)
Notas do `hookscore.py` (versão com suporte a PT-BR). Acima de 70 = STRONG.

| Nota | Fórmula | Gancho | Vira qual post |
|---|---|---|---|
| 87,0 | #11 lista + risco | "3 erros no site que mandam seu cliente pro concorrente." | Dica (Reel ou carrossel) |
| 81,6 | #16 pergunta / objeção | "Tem Instagram e acha que não precisa de site? Você está perdendo cliente." | Dica |
| 79,5 | #18 Cold Open | "Seu cliente te achou no Google. Esse é o site que ele abre." | **Já produzido:** 10-reel-site-novo |
| 74,2 | #16 pergunta | "Preciso de site se minha empresa já tem Instagram?" | Dica (versão curta) |
| 64,8 | #14 Callout | "Oficina sem site perde orçamento todo dia. 3 coisas que resolvem." | Série por nicho |
| 62,1 | Depoimento | "A Eixo Sul perdia horas em planilha. Esse é o sistema que trocou isso." | Prova (gravar na Eixo Sul) |
| 56,8 | #14 Callout | "Clínica de estética em Lages sem site perde paciente pro concorrente do lado." | Série por nicho |

**Série por nicho (achado nº 1):** um Reel por ramo, com o ramo no primeiro segundo: clínica de estética → oficina → escritório de topografia → comércio. Mesma estrutura, troca só o exemplo. Para fortalecer, comece pelo "você" ("Sua clínica…", "Sua oficina…"), que hoje é o ponto mais fraco desses ganchos (ADDRESS).

**Depoimento da Eixo Sul (achado nº 2):** 30 a 45 s, alguém da Eixo Sul falando para a câmera: nome, cargo, como era antes e o que mudou. Tudo com as palavras dela, sem roteiro inventado. Os números entram só se ela disser.
