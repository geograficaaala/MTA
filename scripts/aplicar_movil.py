#!/usr/bin/env python3
"""Inyecta recursos móviles en páginas HTML sin reescribir contenido ni romper IDs."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.git','node_modules','vendor','_site'}
count=0
for p in ROOT.rglob('*.html'):
    if any(x in EXCLUDE for x in p.parts) or not (p==ROOT/'index.html' or p.parent==ROOT or p.parent==ROOT/'docs'):
        continue
    html=p.read_text(encoding='utf-8')
    if not re.search(r'</head\s*>',html,re.I) or not re.search(r'</body\s*>',html,re.I):continue
    prefix='../' if p.parent==ROOT/'docs' else './'
    css=f'{prefix}assets/css/movil-global.css'
    js=f'{prefix}assets/js/movil-global.js'
    if 'movil-global.css' not in html:
        html=re.sub(r'</head\s*>',f'<link rel="stylesheet" href="{css}">\n</head>',html,count=1,flags=re.I)
    if 'movil-global.js' not in html:
        html=re.sub(r'</body\s*>',f'<script src="{js}" defer></script>\n</body>',html,count=1,flags=re.I)
    if html!=p.read_text(encoding='utf-8'):
        p.write_text(html,encoding='utf-8');count+=1;print('Actualizado:',p.relative_to(ROOT))
print('Páginas actualizadas:',count)
