// Plays the preview clips only while they're on screen, so they don't burn
// battery or data off-screen. Visitors who ask for reduced motion keep the
// still poster frame and get the native controls to play it themselves.
(() => {
  // "Sound on" restarts a clip from the top with sound, e.g. to hear the app
  // call out the distance. Browsers only autoplay muted, so sound is opt-in.
  for (const button of document.querySelectorAll(".sound-toggle")) {
    const clip = button.parentElement.querySelector("video[data-sound]");
    if (!clip) continue;
    button.hidden = false;
    button.addEventListener("click", () => {
      const turningOn = clip.muted;
      clip.muted = !turningOn;
      button.textContent = turningOn ? "Sound off" : "Sound on";
      if (turningOn) {
        clip.currentTime = 0;
        clip.play().catch(() => {});
      }
    });
  }

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
