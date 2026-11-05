(() => {
  for (const task of document.querySelectorAll('[data-task][id], [data-theory-block][id]')) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Скопировать ссылку';
    button.setAttribute('aria-label', `Скопировать ссылку: ${task.getAttribute('data-theory-block') || task.querySelector('strong')?.textContent || 'задание'}`);
    button.style.cssText = 'display:block;margin:8px 0 16px;padding:5px 0;border:0;background:transparent;color:var(--accent);font-size:12px;text-align:left';
    const status = document.createElement('span');
    status.setAttribute('role', 'status');
    status.style.cssText = 'font-size:12px;color:var(--muted)';
    task.append(button, status);
    button.addEventListener('click', async () => {
      const url = new URL(location.href);
      url.hash = task.id;
      try {
        await navigator.clipboard.writeText(url.href);
        status.textContent = 'Ссылка скопирована';
        setTimeout(() => { status.textContent = ''; }, 2500);
      } catch {
        window.prompt('Скопируйте ссылку на этот блок:', url.href);
      }
    });
  }
  const sectionNav = document.querySelector('.section-nav');
  if (sectionNav) {
    const links = Array.from(sectionNav.querySelectorAll('a'));
    const sections = Array.from(document.querySelectorAll('.lesson-section'));
    const toc = document.querySelector('.page-toc');
    const tocLinks = Array.from(document.querySelectorAll('.toc-links a'));
    const tocTargets = tocLinks.map(link => document.getElementById(link.hash.slice(1)));
    const desktop = window.matchMedia('(min-width: 1100px)');
    const adaptToc = () => { if (toc) toc.open = desktop.matches; };
    desktop.addEventListener('change', adaptToc);
    adaptToc();
    let scheduled = false;
    const update = () => {
      scheduled = false;
      const threshold = sectionNav.getBoundingClientRect().bottom + 36;
      let active = sections[0];
      for (const section of sections) if (section.getBoundingClientRect().top <= threshold) active = section;
      if (window.scrollY > 0 && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 8) active = sections.at(-1);
      for (const link of links) {
        if (link.hash === `#${active.id}`) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
      let current = 0;
      for (let i = 0; i < tocTargets.length; i++) {
        if (tocTargets[i]?.getBoundingClientRect().top <= threshold) current = i;
      }
      if (window.scrollY > 0 && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 8) current = tocLinks.length - 1;
      for (let i = 0; i < tocLinks.length; i++) {
        if (i === current) tocLinks[i].setAttribute('aria-current', 'location');
        else tocLinks[i].removeAttribute('aria-current');
      }
    };
    window.addEventListener('scroll', () => {
      if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener('resize', update);
    for (const detail of document.querySelectorAll('details.solution')) {
      const summary = detail.querySelector('summary');
      const original = summary.textContent;
      detail.addEventListener('toggle', () => {
        summary.textContent = detail.open ? original.replace('Показать', 'Скрыть') : original;
        update();
      });
    }
    update();
  }
})();
