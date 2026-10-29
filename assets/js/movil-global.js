/* MTA · reparación de navegación móvil y acceso accesible a PDF. */
(()=>{'use strict';
const mobile=()=>window.matchMedia('(max-width:860px)').matches;
function initNav(){
 document.querySelectorAll('header.header').forEach(header=>{
  const nav=header.querySelector('nav[data-nav]'),toggle=header.querySelector('[data-menu-toggle]');if(!nav||!toggle)return;
  if(header.dataset.mtaMobileReady)return;header.dataset.mtaMobileReady='1';
  const close=()=>{nav.classList.remove('mta-mobile-open','mta-nav-abierta','is-open','open');toggle.setAttribute('aria-expanded','false');header.querySelectorAll('details.nav-dropdown').forEach(d=>d.open=false)};
  toggle.addEventListener('click',e=>{if(!mobile())return;e.preventDefault();e.stopImmediatePropagation();const isOpen=nav.classList.contains('mta-mobile-open');if(isOpen)close();else{nav.classList.add('mta-mobile-open');toggle.setAttribute('aria-expanded','true')}},true);
  nav.querySelectorAll('details.nav-dropdown').forEach(d=>d.addEventListener('toggle',()=>{if(!mobile()||!d.open)return;nav.querySelectorAll('details.nav-dropdown').forEach(other=>{if(other!==d)other.open=false})}));
  nav.addEventListener('click',e=>{const a=e.target.closest('a[href]');if(!a||!mobile())return;const url=new URL(a.getAttribute('href'),location.href);if(url.origin!==location.origin)return;close();if(url.pathname===location.pathname&&url.hash){location.hash=url.hash;return} /* no preventDefault: preserve browser navigation */},true);
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});document.addEventListener('click',e=>{if(mobile()&&!header.contains(e.target))close()});
  window.addEventListener('resize',()=>{if(!mobile())close()},{passive:true});
 });
}
function initPdfs(){
 const selector='iframe[src],embed[src],object[data]';
 document.querySelectorAll(selector).forEach(el=>{const raw=el.getAttribute('src')||el.getAttribute('data')||'';if(!/\.pdf(?:[?#]|$)/i.test(raw))return;
  if(el.dataset.mtaPdfReady)return;el.dataset.mtaPdfReady='1';el.classList.add('mta-pdf-embed');
  const bar=document.createElement('div');bar.className='mta-pdf-mobile-actions';
  const link=document.createElement('a');link.href=raw;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Abrir PDF en pantalla completa';bar.appendChild(link);
  const download=document.createElement('a');download.href=raw;download.setAttribute('download','');download.textContent='Descargar PDF';bar.appendChild(download);el.before(bar);
 });
 /* Los PDF enlazados directamente siguen usando el visor nativo del sistema; no se modifica el archivo original. */
}
function start(){initNav();initPdfs()};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
