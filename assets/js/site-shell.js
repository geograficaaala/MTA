(()=>{
  const mobileToggle=document.querySelector("[data-mobile-toggle]");
  const nav=document.querySelector("[data-site-nav]");
  const dropdowns=[...document.querySelectorAll(".site-dropdown")];
  const closeMenus=()=>{
    dropdowns.forEach(item=>item.classList.remove("is-open"));
  };
  if(mobileToggle&&nav){
    mobileToggle.addEventListener("click",()=>{
      const open=mobileToggle.getAttribute("aria-expanded")==="true";
      mobileToggle.setAttribute("aria-expanded",String(!open));
      nav.classList.toggle("is-open",!open);
      if(open)closeMenus();
    });
  }
  dropdowns.forEach(item=>{
    const button=item.querySelector(".site-dropdown-toggle");
    if(!button)return;
    button.addEventListener("click",event=>{
      if(window.innerWidth<=1080){
        event.preventDefault();
        const opening=!item.classList.contains("is-open");
        closeMenus();
        item.classList.toggle("is-open",opening);
      }
    });
  });
  document.addEventListener("keydown",event=>{
    if(event.key==="Escape"){
      closeMenus();
      if(nav)nav.classList.remove("is-open");
      if(mobileToggle)mobileToggle.setAttribute("aria-expanded","false");
      closeSearch();
    }
  });
  document.addEventListener("click",event=>{
    if(!event.target.closest(".site-header"))closeMenus();
  });
  const revealTargets=[...document.querySelectorAll(".home-section,.area-card,.product-card,.climate-card,main .panel,main .section-block")];
  revealTargets.forEach((element,index)=>{
    element.setAttribute("data-reveal","");
    element.style.transitionDelay=`${Math.min(index%4,3)*45}ms`;
  });
  if("IntersectionObserver" in window&&window.matchMedia("(prefers-reduced-motion: no-preference)").matches){
    const observer=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{
        if(entry.isIntersecting){
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },{threshold:.08,rootMargin:"0px 0px -35px 0px"});
    revealTargets.forEach(element=>observer.observe(element));
  }else{
    revealTargets.forEach(element=>element.classList.add("is-visible"));
  }
  const inDocs=location.pathname.includes("/docs/")||location.pathname.endsWith("/docs");
  const root=inDocs?"../":"./";
  const destinations=[
    ["Inicio","Portada de la Mesa Técnica Agroclimática",`${root}index.html`],
    ["Clima","Precipitación, temperatura y viento",`${root}docs/clima_index.html`],
    ["Precipitación","Observación, pronóstico e histórico",`${root}docs/precipitaciones_index.html`],
    ["Temperatura","Observación, pronóstico e histórico",`${root}docs/temperatura_index.html`],
    ["Viento","Observación, pronóstico e histórico",`${root}docs/viento_index.html`],
    ["Agroclima","Balance hídrico, suelo y estrés agrícola",`${root}docs/agroclima_index.html`],
    ["Boletines agroclimáticos","Producto en preparación",`${root}index.html#boletines`],
    ["Datos y estaciones","Fuentes y observación meteorológica",`${root}index.html#productos`],
    ["Instituciones","Integrantes de la MTA Sololá",`${root}index.html#instituciones`],
    ["Contacto","Canales de contacto",`${root}index.html#contacto`]
  ];
  const overlay=document.createElement("div");
  overlay.className="site-search-overlay";
  overlay.setAttribute("aria-hidden","true");
  overlay.innerHTML='<div class="site-search-dialog" role="dialog" aria-modal="true" aria-label="Buscar en el portal"><div class="site-search-head"><input class="site-search-input" type="search" autocomplete="off" placeholder="Buscar precipitación, temperatura, viento o agroclima" aria-label="Buscar en el portal"><button class="site-search-close" type="button">Cerrar</button></div><div class="site-search-results"></div></div>';
  document.body.appendChild(overlay);
  const input=overlay.querySelector(".site-search-input");
  const results=overlay.querySelector(".site-search-results");
  const renderResults=query=>{
    const normalized=query.trim().toLocaleLowerCase("es");
    const filtered=normalized?destinations.filter(item=>`${item[0]} ${item[1]}`.toLocaleLowerCase("es").includes(normalized)):destinations.slice(0,6);
    results.innerHTML=filtered.length?filtered.map(item=>`<a class="site-search-result" href="${item[2]}"><strong>${item[0]}</strong><span>${item[1]}</span></a>`).join(""):'<div class="site-search-empty">No se encontraron resultados.</div>';
  };
  const openSearch=()=>{
    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden","false");
    renderResults("");
    requestAnimationFrame(()=>input.focus());
  };
  function closeSearch(){
    overlay.classList.remove("is-open");
    overlay.setAttribute("aria-hidden","true");
  }
  document.querySelectorAll("[data-search-open]").forEach(button=>button.addEventListener("click",openSearch));
  overlay.querySelector(".site-search-close").addEventListener("click",closeSearch);
  overlay.addEventListener("click",event=>{if(event.target===overlay)closeSearch();});
  input.addEventListener("input",()=>renderResults(input.value));
  const year=document.querySelector("[data-current-year]");
  if(year)year.textContent=new Date().getFullYear();
})();
