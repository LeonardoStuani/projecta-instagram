---
name: ig-story
description: >-
  Write the day's Instagram Stories - the frame-by-frame sequence, which
  stickers to use where, and the one that moves people into the DMs. Use when
  the user says "stories", "what do I post on my story", "story sequence",
  "poll idea", "I have nothing to story about", or wants to sell something
  without making a post about it.
---

# ig-story

Stories are not a smaller feed. The feed is how strangers find you. Stories are
how the people who already follow you decide whether you are a person worth
buying from, and they are the only surface on Instagram where a tap turns into
a conversation in one move.

Nobody outside your followers sees these, so the job is completely different:
depth, not reach.

## The daily shape

Three to seven frames a day. Beyond about seven, the tap-forward rate climbs
and the last frames play to nobody, which is exactly where people put the ask.

```
1       THE OPEN     something happening today, with a face or a hand in it.
2-3     THE MIDDLE   the actual content: the process, the result, the mistake.
4       THE ASK      one sticker. Poll, question box, quiz or link.
5       THE CLOSE    the answer, the outcome, or tomorrow's setup.
```

Put the ask at frame 4, not frame 7. Completion drops with every tap and the
ask should be seen by the people who are still there.

## The stickers, and what each is actually for

| sticker | job | use when |
| --- | --- | --- |
| **Poll** | the cheapest tap there is | you want volume of response, not information |
| **Question box** | harvesting the exact words people use | you need content ideas or objections, verbatim |
| **Quiz** | teaching by letting them be wrong | there is a common misconception in the niche |
| **Slider** | vibe check | nothing important. Fun, low value |
| **Link** | the only clickable surface besides the bio | there is somewhere real to go |
| **Countdown** | a deadline people can subscribe to | a launch, a live, a close date |
| **Add yours** | reach beyond your followers, occasionally | the prompt is one anyone in the niche can answer |

The question box is the most undervalued one in the list. Every answer is a
caption, a Reel hook or a DM opener written in the audience's own words. Feed
them to `/ig-reel` as formula #16.

## Rules

- **A face or a hand in the first frame.** Text on a coloured background gets
  tapped through, and the first frame decides whether the rest get watched.
- **One idea per frame.** Reading a paragraph on a story is not a thing anyone
  does.
- **Keep text inside the middle.** On 1080x1920, nothing above y=250 or below
  y=1600. The profile row sits on top and the reply bar sits underneath.
- **Talk to one person.** "You" singular. Stories are the closest thing to a
  DM that is not one.
- **Do not repost your own feed post to stories with no comment.** It is the
  single most ignored frame on the platform. If you are pointing at a post, say
  what happened in the comments and why it is worth going back for.
- **Sell on stories, not in posts.** Three frames of context, one frame of
  offer, one frame of proof. That sequence sells more than a feed post about
  the same thing and costs you no reach.

## The DM funnel, done honestly

The sequence that works: a story that names a problem, a question box or a poll
that lets people say "that's me", and then a reply to each person who answered.
The conversation starts because they spoke first.

Automated keyword DM replies are a real, supported feature for professional
accounts, through Instagram's own tools and approved partners. Bulk DMing
people who did not interact is not, and it is what gets accounts restricted.
The rule is simple: **they act first, then you reply.**

## Output

The frames in order, each with what is on screen, what is said, and which
sticker, plus what to do with the answers:

```
STORIES  ·  Tuesday  ·  5 frames

1  [selfie, walking]      "Third refund request this year. Same reason."
2  [screen recording]     the clause, highlighted
3  [talking]              "Approval is a feeling. Delivery is a date."
4  [poll]                 "Have you been burned by a late approval?"  Yes / Not yet
5  [text on photo]        "Reply and I will send you the clause."

After: everyone who votes Yes gets a reply. That is the whole funnel.
```

Nothing is posted. The user posts it.

## Projecta: "/ig-story da semana" (modo semanal, gera arquivos para o painel)

When the user asks for the week's stories, produce a ready-to-post week, not
just text. Everything in Portuguese, following `instagram/voice.md`.

1. **Read first:** `calendario.json` (feed posts of that week: stories should
   point to them, never repost them bare), the previous `posts/stories-*/stories.json`
   (do not repeat themes or questions), `instagram/voice.md` (provas, no prices,
   no invented numbers or testimonials, illustrative screens marked).
2. **Dates:** start the day after the last existing stories day. Six posting
   days, Sunday off, Saturday light (4 frames, question box).
3. **Create** `posts/stories-AAAA-MM-DD/stories.json` (date = first day) with:
   `titulo`, `resumo`, and `dias[]` each with `n, data, titulo, pasta, horario,
   postado:false, depois, quadros[]`. Each `quadro`:
   - frame 1: `{"n":1,"tipo":"gravar","texto":"what Leo films and says","adesivo":"Localização: Lages, SC"}`
   - image frames: `{"n", "img":"0N.png", "sobre":"what the image says and why it is there (1-2 sentences)", "adesivo"?, "link"?, "tela":{...}}`
   - `tela` fields: `fundo` ("" | "dark" | "laranja"), `kick`, `titulo` (`*x*` = orange italic),
     `tam` ("m" long, "g" short), `sub`, `nota`, `lista[]`, `check`, `arquivo`, `modelo:true`
     (background to answer the question box). One orange (`laranja`) frame per day at most.
   - the ask (poll, question box or link) on frame 4.
4. **Render:** `node scripts/stories/renderizar.mjs posts/stories-AAAA-MM-DD`
   (needs internet for the fonts). Open `previa.png` and every frame with a
   sticker: text must stay above y≈1050 so the sticker area is free.
5. The panel (aba Stories) reads the folder by itself. Tell the user to click
   **Enviar para o GitHub**. Nothing is posted automatically: Leo posts in the app.
