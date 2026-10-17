// Plays the preview clips only while they're on screen, so they don't burn
// battery or data off-screen. Visitors who ask for reduced motion keep the
// still poster frame and get the native controls to play it themselves.
(() => {
  const clips = document.querySelectorAll("video.clip");
  if (!clips.length || !("IntersectionObserver" in window)) return;

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const onScreen = new Set();

  const sync = () => {
    for (const clip of clips) {
      clip.controls = reduce.matches;
      if (!reduce.matches && onScreen.has(clip)) {
        clip.play().catch(() => {}); // Low Power Mode can refuse; the poster stays.
      } else if (!reduce.matches) {
        clip.pause();
      }
    }
  };

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) onScreen.add(entry.target);
      else onScreen.delete(entry.target);
    }
    sync();
  }, { threshold: 0.25 });

  clips.forEach((clip) => observer.observe(clip));
  reduce.addEventListener("change", sync);
})();
