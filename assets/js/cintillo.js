/* Cintillo institucional maestro MTA Sololá — orden según guía oficial. */
(() => {
  'use strict';
  const script = document.currentScript || [...document.scripts].find(s => s.src.includes('/assets/js/cintillo.js'));
  const root = script ? new URL('../../', script.src) : new URL('./', location.href);
  const pathLogo = filename => new URL('docs/logos/' + filename, root).href;
  const pathRoot = filename => new URL(filename, root).href;

  // Cada fila mantiene el orden de izquierda a derecha de la referencia.
  // "logos" admite imágenes agrupadas de una misma entidad institucional.
  const filas = [
    [
      {nombre:'MAGA', url:'https://www.maga.gob.gt/', logos:['MAGA.png','MAGA02.png'], ancho:175},
      {nombre:'INSIVUMEH', url:'https://insivumeh.gob.gt/', logos:['INSIVUMEN02.png','INSIVUMEH.png'], ancho:260},
      {nombre:'ICTA', url:'https://www.icta.gob.gt/', logos:['ICTA.png'], ancho:81},
      {nombre:'Amigos del Lago de Atitlán',url:'https://amigosdeatitlan.org/',logos:['AmigosdelLago.png'],ancho:81},
      {nombre:'AxTech Solutions',url:null, archivo:'AxTEch.jpeg', ancho:119},
      {nombre:'AMSCLAE — Gobierno de Guatemala',url:'https://www.amsclae.gob.gt/', archivo:'gobierno_amsclae.jpg',ancho:263},
      {nombre:'AMSCLAE',url:'https://www.amsclae.gob.gt/', logos:['AMSCLAE.png'], ancho:85},
      {nombre:'ANACAFÉ',url:'https://www.anacafe.org/',logos:['Anacafe.png'],ancho:125}
    ],
    [
      {nombre:'Escuela de Formación Agrícola Sololá',url:'https://admisionesefasolol.wixsite.com/efasolola',logos:['EFA.png'],ancho:80},
      {nombre:'Vivamos Mejor',url:'https://vivamosmejor.org.gt/',logos:['VivamosMejor.png'],ancho:112},
      {nombre:'UVG y Centro de Estudios Agrícolas y Alimentarios',url:'https://www.uvg.edu.gt/',logos:['UVG.png'],ancho:240},
      {nombre:'MARN',url:'https://www.marn.gob.gt/',logos:['MARN.png'],ancho:180},
      {nombre:'Heifer y Futuro Sostenible',url:'https://www.heiferguatemala.org.gt/',logos:['HeiferInternational.png'],ancho:180},
      {nombre:'Feed the Children',url:'https://www.feedthechildren.org/our-work/around-the-world/guatemala/',logos:['FeedtheChildren.png'],ancho:110},
      {nombre:'Cáritas',url:'https://sites.google.com/view/caritas-nacional/',logos:['Caritas.png'],ancho:109},
      {nombre:'CONRED',url:'https://conred.gob.gt/',logos:['Logo_de_CONRED.png'],ancho:72},
      {nombre:'CERCAP',url:'https://asociacioncdro.org.gt/',logos:['CERCAP.png'],ancho:102},
      {nombre:'Rikolto',url:'https://latinoamerica.rikolto.org/',logos:['Rikolto.png'],ancho:103},
      {nombre:'Bélgica — Enabel',url:'https://www.enabel.be/',logos:['Belgica.png'],ancho:110}
    ]
  ];

  function montar() {
    document.querySelectorAll('[data-mta-cintillo]').forEach(mount => {
      if (mount.dataset.mtaCintilloListo === '1') return;
      mount.dataset.mtaCintilloListo = '1';
      mount.classList.add('partners','mta-cintillo');
      mount.setAttribute('aria-label','Instituciones que integran y acompañan la Mesa Técnica Agroclimática de Sololá');
      const shell=document.createElement('div');shell.className='shell';
      const titulo=document.createElement('h2');titulo.className='partners-title';titulo.id='institucionesTitle';
      titulo.textContent='Instituciones que integran y acompañan la Mesa Técnica Agroclimática de Sololá';
      shell.append(titulo);
      filas.forEach((fila,i)=>{
        const row=document.createElement('div');row.className='mta-logos-fila mta-logos-fila-'+(i+1);
        fila.forEach(inst=>{
          const el=document.createElement(inst.url?'a':'div');el.className='mta-logo-entidad';
          el.style.setProperty('--logo-ancho',inst.ancho+'px');
          if(inst.url){el.href=inst.url;el.target='_blank';el.rel='noopener noreferrer'}
          el.setAttribute('aria-label',inst.nombre);
          const images=inst.archivo?[pathRoot(inst.archivo)]:inst.logos.map(pathLogo);
          images.forEach((src,j)=>{const img=document.createElement('img');img.src=src;img.alt=j===0?inst.nombre:'';img.loading='lazy';el.append(img)});
          row.append(el);
        });
        shell.append(row);
      });
      mount.replaceChildren(shell);
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',montar,{once:true});else montar();
})();
