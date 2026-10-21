#!/usr/bin/env python3
"""Cambios conservadores para cinco páginas climáticas; ejecución idempotente."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('clima_index.html', 'precipitaciones_index.html', 'temperatura_index.html', 'viento_index.html', 'agroclima_index.html')
MARK = 'data-mta-climaticas-responsive'
CSS = '../assets/css/responsive-climaticas.css'
report = ['# Revisión de páginas climáticas', '', 'Solo se procesan las cinco páginas climáticas.',
          'Los cambios no eliminan secciones ni alteran el cintillo institucional.',
          'La separación visible después del footer se debe confirmar en el navegador: podría ser un contenedor o un estilo externo.', '']
changes = 0
for filename in PAGES:
    path = ROOT / 'docs' / filename
    if not path.exists():
        report.append(f'- **{filename}**: archivo no encontrado, sin cambios.')
        continue
    raw = path.read_text(encoding='utf-8-sig')
    if not re.search(r'</head\s*>', raw, flags=re.I):
        report.append(f'- **{filename}**: falta cierre `</head>`, requiere revisión manual.')
        continue
    if MARK not in raw:
        link = f'<link rel="stylesheet" href="{CSS}" {MARK}>\n'
        updated = re.sub(r'</head\s*>', lambda m: link + m.group(0), raw, count=1, flags=re.I)
        path.write_text(updated, encoding='utf-8')
        changes += 1
        report.append(f'- **{filename}**: enlazado CSS móvil compartido.')
    else:
        report.append(f'- **{filename}**: ya enlazado, sin duplicados.')
    footer_n = len(re.findall(r'<footer\b', raw, flags=re.I))
    after_footer = re.search(r'</footer\s*>(.*?)</body\s*>', raw, re.I | re.S)
    if after_footer:
        tail = re.sub(r'<script\b[^>]*>.*?</script\s*>', '', after_footer.group(1), flags=re.I | re.S)
        tags = re.findall(r'<(div|section|iframe|main|aside)\b[^>]*>', tail, re.I)
        if tags:
            report.append(f'  - Aviso: posibles elementos estructurales posteriores al footer: {", ".join(tags[:8])}. Revisar antes de eliminar.')
    report.append(f'  - Footer detectados: {footer_n}.')
report += ['', f'Archivos HTML modificados: **{changes}**.', '',
           'Comprobar visualmente en móvil, especialmente gráficos, leyendas, modales y el espacio debajo del footer.', '']
(ROOT / 'reporte-climaticas-responsive.md').write_text('\n'.join(report), encoding='utf-8')
print('\n'.join(report))
