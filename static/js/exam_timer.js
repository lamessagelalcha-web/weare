(() => {
  const timer = document.getElementById('examTimer');
  const form = document.getElementById('examForm');
  if (!timer || !form) return;
  let seconds = Number(timer.dataset.minutes || 30) * 60;
  const fmt = n => `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;
  timer.textContent = fmt(seconds);
  const interval = setInterval(() => {
    seconds -= 1;
    timer.textContent = fmt(Math.max(seconds,0));
    if (seconds <= 0) {
      clearInterval(interval);
      alert('Time is up. Your exam will be submitted now.');
      form.submit();
    }
  }, 1000);
  form.addEventListener('submit', () => clearInterval(interval));
})();
