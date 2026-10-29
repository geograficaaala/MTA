#!/usr/bin/env python3
"""Migración puntual y conservadora del cintillo en index.html."""
from pathlib import Path
import re
import sys

p = Path('index.html')
html = p.read_text(encoding='utf-8')
original = html

# El índice antiguo puede incluir logos propios en lugar del cintillo maestro.
old = re.compile(r'<section\b(?=[^>]*\bclass="[^"]*\bpartners\b)(?=[^>]*\bid="instituciones")\s*[^>]*>.*?</section>\s*', re.S | re.I)
found = list(old.finditer(html))
if len(found) > 1:
    sys.exit('ERROR: varios cintillos originales; intervención manual requerida.')

master = '<section id="instituciones" class="partners mta-cintillo" data-mta-cintillo></section>\n'
if found:
    if 'data-mta-cintillo' in found[0].group():
        print('El contenedor maestro ya existe.')
    else:
        # Colocar al terminar main, igual que la página de boletines.
        html = old.sub('', html, count=1)
        close_main = html.find('</main>')
        footer = html.find('<footer')
        if close_main < 0 or footer < 0 or close_main > footer:
            sys.exit('ERROR: no se reconoció la posición de main/footer.')
        html = html[:close_main + len('</main>')] + '\n' + master + html[close_main + len('</main>'):]
else:
    if 'data-mta-cintillo' not in html:
        sys.exit('ERROR: no se encontró un cintillo reconocible. No se modificó el archivo.')

if html.count('data-mta-cintillo></section>') != 1:
    sys.exit('ERROR: el resultado no tiene exactamente un cintillo maestro.')

if 'data-mta-cintillo-css' not in html:
    html = html.replace('</head>', '<link rel="stylesheet" href="assets/css/cintillo.css" data-mta-cintillo-css>\n</head>', 1)
if 'data-mta-cintillo-js' not in html:
    html = html.replace('</body>', '<script defer src="assets/js/cintillo.js" data-mta-cintillo-js></script>\n</body>', 1)

# Comprobaciones conservadoras: nunca tocar footer ni tema.
def part(s, start, end):
    return s.split(start,1)[1].split(end,1)[0] if start in s and end in s else None
before_footer = part(original, '<footer', '</footer>')
after_footer = part(html, '<footer', '</footer>')
if before_footer != after_footer or 'assets/css/tema-mta.css' not in html:
    sys.exit('ERROR: el footer o el tema difieren; abortando.')
if html.count('data-mta-cintillo-js') != 1 or html.count('data-mta-cintillo-css') != 1:
    sys.exit('ERROR: se duplicó un recurso.')

if html != original:
    p.write_text(html, encoding='utf-8')
    print('OK: index.html usa el cintillo maestro. Footer intacto.')
else:
    print('Sin cambios: index.html ya estaba corregido.')
