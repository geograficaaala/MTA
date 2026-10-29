#!/usr/bin/env python3
"""Sincroniza el header de las subpáginas con el de index.html sin alterar otros bloques."""
from pathlib import Path
from bs4 import BeautifulSoup
import re, sys, os
ROOT=Path(__file__).resolve().parent.parent
FILES=['docs/clima_index.html','docs/precipitaciones_index.html','docs/temperatura_index.html','docs/viento_index.html','docs/agroclima_index.html','boletines.html','infografias.html','mapas.html','noticias.html','spots-radiales.html','comentarios_index.html']
html=(ROOT/'index.html').read_text(encoding='utf-8-sig')
soup=BeautifulSoup(html,'html.parser'); original=soup.select_one('header.header')
if not original or not original.select_one('nav[data-nav]'): sys.exit('ERROR: el index no tiene header.header con nav[data-nav]. No se modifica nada.')
source=str(original)
if not all(s in source for s in ['Información climática','Spots radiales','Noticias','Recomendaciones agroclimáticas']):sys.exit('ERROR: el header del index no contiene todos los menús esperados.')
changed=[]; skipped=[]
for name in FILES:
    path=ROOT/name
    if not path.is_file(): skipped.append(name+' (archivo no encontrado)');continue
    raw=path.read_text(encoding='utf-8-sig')
    match=re.search(r'<header\b[^>]*class=["\'][^"\']*\bheader\b[^"\']*["\'][^>]*>.*?</header\s*>',raw,re.I|re.S)
    if not match: skipped.append(name+' (header no reconocido)');continue
    prefix='../' if name.startswith('docs/') else './'
    h=BeautifulSoup(source,'html.parser').select_one('header')
    for a in h.select('[href]'):
        href=a.get('href','')
        if href.startswith('./'): a['href']=prefix+href[2:]
        elif href=='#contacto': a['href']=prefix+'index.html#contacto'
        if a.has_attr('aria-current'):del a['aria-current']
    for img in h.select('[src]'):
        src=img.get('src','')
        if src.startswith('./'):img['src']=prefix+src[2:]
    for a in h.select('a[href]'):
        link=a['href'].removeprefix(prefix)
        if link==name or (name.startswith('docs/') and link==name):a['aria-current']='page'
    h['data-mta-header-unificado']=''
    new=raw[:match.start()]+str(h)+raw[match.end():]
    stylesheet=prefix+'assets/css/header-unificado.css'
    javascript=prefix+'assets/js/header-unificado.js'
    if 'header-unificado.css' not in new:
        new=new.replace('</head>',f'<link rel="stylesheet" href="{stylesheet}" data-mta-header-style>\n</head>',1)
    if 'header-unificado.js' not in new:
        new=new.replace('</body>',f'<script defer src="{javascript}" data-mta-header-script></script>\n</body>',1)
    if new!=raw:path.write_text(new,encoding='utf-8');changed.append(name)
print('Modificados:',', '.join(changed) or 'ninguno')
print('Omitidos:',', '.join(skipped) or 'ninguno')
if any('header no reconocido' in x for x in skipped):sys.exit('ERROR: algun header no se pudo reconocer; revisar antes del PR.')
