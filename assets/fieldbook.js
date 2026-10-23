/* Small progressive enhancements; the notes and directory work without JS. */
(() => {
  document.querySelectorAll('.markdown .highlight').forEach((block) => {
    const code = block.querySelector('pre code');
    if (!code) return;
    const toolbar = document.createElement('div');
    toolbar.className = 'code-toolbar';
    const label = document.createElement('span');
    label.className = 'code-label';
    label.textContent = code.dataset.lang || [...code.classList].find((name) => name.startsWith('language-'))?.slice(9) || 'payload / notes';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy-button';
    button.textContent = 'COPY';
    button.setAttribute('aria-label', 'Copy code block');
    button.addEventListener('click', async () => {
      const payload = code.textContent;
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(payload);
        } else {
          const text = document.createElement('textarea');
          text.value = payload;
          text.style.position = 'fixed';
          text.style.opacity = '0';
          document.body.append(text);
          text.select();
          const copied = document.execCommand('copy');
          text.remove();
          if (!copied) throw new Error('Copy unavailable');
          button.focus();
        }
        button.textContent = 'COPIED ✓';
      } catch {
        button.textContent = 'SELECT CODE';
        const range = document.createRange();
        range.selectNodeContents(code);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      }
      setTimeout(() => { button.textContent = 'COPY'; }, 1800);
    });
    toolbar.append(label, button);
    block.prepend(toolbar);
  });

  const progress = document.querySelector('.reading-progress');
  let pending = false;
  const updateProgress = () => {
    const available = document.documentElement.scrollHeight - window.innerHeight;
    progress?.style.setProperty('--reading-progress', `${available > 0 ? Math.min(100, window.scrollY / available * 100) : 0}%`);
    pending = false;
  };
  window.addEventListener('scroll', () => {
    if (!pending) { pending = true; requestAnimationFrame(updateProgress); }
  }, { passive: true });
  window.addEventListener('resize', updateProgress);
  updateProgress();

  const menuControl = document.querySelector('#menu-control');
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      if (menuControl) menuControl.checked = false;
      const toc = document.querySelector('#toc-control');
      if (toc) toc.checked = false;
    }
    const typing = event.target.closest('input, textarea, select, [contenteditable="true"]');
    if (!typing && (event.key === '/' || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k'))) {
      if (window.matchMedia('(max-width: 56rem)').matches && menuControl) menuControl.checked = true;
    }
  });

  if ('IntersectionObserver' in window) {
    const tocLinks = [...document.querySelectorAll('.book-toc a[href^="#"]')];
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting);
      if (!visible.length) return;
      const id = visible[0].target.id;
      tocLinks.forEach((link) => {
        const active = decodeURIComponent(link.hash.slice(1)) === id;
        link.classList.toggle('is-current', active);
        if (active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin: '-5% 0px -70% 0px' });
    document.querySelectorAll('.markdown h2[id], .markdown h3[id]').forEach((heading) => observer.observe(heading));
  }
})();
