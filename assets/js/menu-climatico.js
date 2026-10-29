/* Gestión de desplegables nativos sin interferir con scripts de clima o buscador. */
(() => {
  const nav = document.querySelector('nav[data-nav].mta-nav-climatica');
  if (!nav || nav.dataset.mtaDropdownReady) return;
  nav.dataset.mtaDropdownReady = '1';
  const groups = [...nav.querySelectorAll('details.mta-nav-group')];
  groups.forEach(group => {
    group.addEventListener('toggle', () => {
      if (group.open) groups.filter(other => other !== group).forEach(other => { other.open = false; });
    });
  });
  document.addEventListener('click', ev => {
    if (!nav.contains(ev.target)) groups.forEach(group => { group.open = false; });
  });
  document.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') {
      groups.forEach(group => { group.open = false; });
      if (nav.contains(document.activeElement)) document.querySelector('[data-menu-toggle]')?.focus();
    }
  });
})();
