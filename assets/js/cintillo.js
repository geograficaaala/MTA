/* Cintillo institucional maestro MTA Sololá. Editar aquí instituciones y orden. */
(() => {
  'use strict';
  const instituciones = [
  {
    "nombre": "MAGA",
    "url": "https://www.maga.gob.gt/",
    "logo": "MAGA.png"
  },
  {
    "nombre": "MAGA",
    "url": "https://www.maga.gob.gt/",
    "logo": "MAGA02.png"
  },
  {
    "nombre": "INSIVUMEH",
    "url": "https://insivumeh.gob.gt/",
    "logo": "INSIVUMEH.png"
  },
  {
    "nombre": "INSIVUMEH",
    "url": "https://insivumeh.gob.gt/",
    "logo": "INSIVUMEN02.png"
  },
  {
    "nombre": "Cáritas de Guatemala",
    "url": "https://sites.google.com/view/caritas-nacional/",
    "logo": "Caritas.png"
  },
  {
    "nombre": "Heifer International Guatemala",
    "url": "https://www.heiferguatemala.org.gt/",
    "logo": "HeiferInternational.png"
  },
  {
    "nombre": "Feed the Children Guatemala",
    "url": "https://www.feedthechildren.org/our-work/around-the-world/guatemala/",
    "logo": "FeedtheChildren.png"
  },
  {
    "nombre": "AMSCLAE",
    "url": "https://www.amsclae.gob.gt/",
    "logo": "AMSCLAE.png"
  },
  {
    "nombre": "CERCAP",
    "url": "https://asociacioncdro.org.gt/",
    "logo": "CERCAP.png"
  },
  {
    "nombre": "Rikolto",
    "url": "https://latinoamerica.rikolto.org/",
    "logo": "Rikolto.png"
  },
  {
    "nombre": "Enabel",
    "url": "https://www.enabel.be/",
    "logo": "Belgica.png"
  },
  {
    "nombre": "ICTA",
    "url": "https://www.icta.gob.gt/",
    "logo": "ICTA.png"
  },
  {
    "nombre": "Anacafé",
    "url": "https://www.anacafe.org/",
    "logo": "Anacafe.png"
  },
  {
    "nombre": "Centro de Estudios Atitlán UVG",
    "url": "https://www.uvg.edu.gt/investigacion/ceaa",
    "logo": "UVG.png"
  },
  {
    "nombre": "Vivamos Mejor",
    "url": "https://vivamosmejor.org.gt/",
    "logo": "VivamosMejor.png"
  },
  {
    "nombre": "Escuela de Formación Agrícola Sololá",
    "url": "https://admisionesefasolol.wixsite.com/efasolola",
    "logo": "EFA.png"
  },
  {
    "nombre": "MARN",
    "url": "https://www.marn.gob.gt/",
    "logo": "MARN.png"
  },
  {
    "nombre": "Amigos del Lago de Atitlán",
    "url": "https://amigosdeatitlan.org/",
    "logo": "AmigosdelLago.png"
  },
  {
    "nombre": "CONRED",
    "url": "https://conred.gob.gt/",
    "logo": "Logo_de_CONRED.png"
  }
];
  function rutaBase() {
    const s = document.currentScript || Array.from(document.scripts).find(s => s.src.includes('/assets/js/cintillo.js'));
    return s ? new URL('../../docs/logos/', s.src).href : './docs/logos/';
  }
  const logosBase = rutaBase();
  function montar() {
    document.querySelectorAll('[data-mta-cintillo]').forEach(mount => {
      if (mount.dataset.mtaCintilloListo === '1') return;
      mount.dataset.mtaCintilloListo = '1';
      mount.setAttribute('aria-label','Instituciones que integran y acompañan la Mesa Técnica Agroclimática de Sololá');
      mount.classList.add('partners', 'mta-cintillo');
      const shell=document.createElement('div'); shell.className='shell';
      const title=document.createElement('h2'); title.className='partners-title';
      title.textContent='Instituciones que integran y acompañan la Mesa Técnica Agroclimática de Sololá';
      shell.appendChild(title);
      const grid=document.createElement('div'); grid.className='partner-grid';
      instituciones.forEach(({nombre,url,logo}) => {
        const a=document.createElement('a'); a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; a.setAttribute('aria-label',nombre);
        const image=document.createElement('img'); image.src=logosBase + encodeURIComponent(logo); image.alt=nombre; image.loading='lazy';
        a.appendChild(image); grid.appendChild(a);
      });
      shell.appendChild(grid); mount.replaceChildren(shell);
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',montar,{once:true}); else montar();
})();
