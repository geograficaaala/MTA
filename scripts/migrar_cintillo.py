#!/usr/bin/env python3
"""Migración conservadora de cintillos a un componente maestro. Python estándar.
Por defecto informa qué cambiaría; --apply escribe los HTML reconocidos.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLACEHOLDER = '<section id="instituciones" class="partners mta-cintillo" data-mta-cintillo></section>'
CSS = '<link rel="stylesheet" href="{prefix}assets/css/cintillo.css" data-mta-cintillo-css>'
JS = '<script defer src="{prefix}assets/js/cintillo.js" data-mta-cintillo-js></script>'
# Sólo migrar secciones con id="instituciones" y clase="partners".
SECTION = re.compile(r'<section\b(?=[^>]*\bid\s*=\s*["\']instituciones["\'])(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bpartners\b)[^>]*>.*?</section\s*>', re.I | re.S)


def migrar(path):
    old = path.read_text(encoding='utf-8')
    if '<html' not in old.lower() or '</body>' not in old.lower():
        return 'omitido: no es una página HTML completa', None
    # No tocar vistas de datos, widgets o páginas auxiliares sin footer.
    if not re.search(r'<footer\b', old, re.I):
        return 'omitido: sin footer, revisar manualmente', None
    sections = list(SECTION.finditer(old))
    if len(sections) > 1:
        return 'REVISAR: varios cintillos encontrados', None
    updated = old
    if sections:
        m = sections[0]
        updated = updated[:m.start()] + PLACEHOLDER + updated[m.end():]
    elif 'data-mta-cintillo' not in updated:
        footer = re.search(r'<footer\b', updated, re.I)
        if footer is None: return 'omitido: sin footer', None
        updated = updated[:footer.start()] + PLACEHOLDER + '\n' + updated[footer.start():]
    # Evita insertar si hay un bloque diferente con el mismo id.
    if not sections and 'id="instituciones"' in old and 'data-mta-cintillo' not in old:
        return 'REVISAR: existe #instituciones con otra estructura', None
    prefix = '../' * (len(path.relative_to(ROOT).parts)-1)
    if 'data-mta-cintillo-css' not in updated:
        updated, n = re.subn(r'</head\s*>',CSS.format(prefix=prefix)+'\n</head>',updated,count=1,flags=re.I)
        if n != 1:return 'REVISAR: sin </head>', None
    if 'data-mta-cintillo-js' not in updated:
        updated, n = re.subn(r'</body\s*>',JS.format(prefix=prefix)+'\n</body>',updated,count=1,flags=re.I)
        if n != 1:return 'REVISAR: sin </body>', None
    return ('sin cambios' if updated == old else 'actualizado'), updated


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true',help='Guardar cambios (sin esto solo simula)')
    args=parser.parse_args()
    if not (ROOT/'assets/js/cintillo.js').exists() or not (ROOT/'assets/css/cintillo.css').exists():
        sys.exit('Faltan archivos del componente maestro')
    paths = sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('docs/*.html'))
    errors=0
    for path in paths:
        status,new=migrar(path)
        print(f'{path.relative_to(ROOT)}: {status}')
        if status.startswith('REVISAR'):errors+=1
        if args.apply and new is not None and status=='actualizado':path.write_text(new,encoding='utf-8')
    if errors:
        print(f'{errors} archivos requieren revisión; no se modificaron esos archivos.')
    return 0

if __name__=='__main__':sys.exit(main())
