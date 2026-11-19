/* Kit de vídeo da Projecta: cada vídeo é um HTML 1080x1920 que define window.montar(tl).
   - No navegador: toca em loop (R reinicia, espaço pausa).
   - Na renderização (?export=1): o renderizador chama window.render(t) quadro a quadro.
   Regras do bang-motion: nada de "slides". Um mundo contínuo, câmera que se move, no máximo 2 níveis de texto. */
(async () => {
  const q = new URLSearchParams(location.search);
  if (document.fonts) await document.fonts.ready;
  const tl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });
  window.montar(tl, q);
  window.DUR = Math.round(tl.duration() * 100) / 100;
  // Não devolve a timeline: ela é "thenable" e o page.evaluate ficaria esperando para sempre.
  window.render = (t) => { tl.seek(t, false); };
  if (!q.has("export")) {
    tl.eventCallback("onComplete", () => tl.play(0));
    tl.play(0);
    addEventListener("keydown", (e) => {
      if (e.key === "r" || e.key === "R") tl.play(0);
      if (e.key === " ") { e.preventDefault(); tl.paused(!tl.paused()); }
    });
  }
  window.READY = true;
})();

/* Ajuda: quebra um texto em palavras <span class="w"> para animar uma a uma.
   *trecho* vira itálico laranja (mesmo padrão dos carrosséis). */
window.palavras = (el) => {
  const txt = el.textContent;
  el.innerHTML = txt
    .split(/(\*[^*]+\*)/)
    .map((p) =>
      /^\*.*\*$/.test(p)
        ? `<em>${p.slice(1, -1).split(" ").map((w) => `<span class="w">${w}</span>`).join(" ")}</em>`
        : p.split(" ").filter(Boolean).map((w) => `<span class="w">${w}</span>`).join(" "),
    )
    .join(" ");
  return el.querySelectorAll(".w");
};
