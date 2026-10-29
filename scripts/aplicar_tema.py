#!/usr/bin/env python3
"""Agrega el CSS compartido sin reescribir ni reemplazar paginas existentes.

No toca cintillo.js, cintillo.css ni las secciones institucionales.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    'index.html', 'boletines.html', 'infografias.html', 'mapas.html',
    'comentarios_index.html',
    'docs/clima_index.html', 'docs/precipitaciones_index.html',
    'docs/temperatura_index.html', 'docs/viento_index.html',
    'docs/agroclima_index.html',
]
MARKER = 'data-mta-tema'


def main():
    if not (ROOT / 'assets/css/tema-mta.css').is_file():
        sys.exit('ERROR: falta assets/css/tema-mta.css')
    changed, missing = [], []
    for rel in TARGETS:
        path = ROOT / rel
        if not path.is_file():
            missing.append(rel)
            continue
        original = path.read_text(encoding='utf-8')
        if MARKER in original:
            print(f'YA INTEGRADO: {rel}')
            continue
        matches = list(re.finditer(r'</head\s*>', original, flags=re.I))
        if len(matches) != 1:
            sys.exit(f'ERROR: </head> ausente o duplicado en {rel}; no se modifico ese archivo.')
        href = ('../' if rel.startswith('docs/') else '') + 'assets/css/tema-mta.css'
        insert = f'<link rel="stylesheet" href="{href}" {MARKER}>\n'
        # Despues del CSS incluido en <head>; sin tocar los otros enlaces ni scripts.
        pos = matches[0].start()
        updated = original[:pos] + insert + original[pos:]
        # Salvaguarda: los bloques de cintillo tienen que permanecer byte-a-byte iguales.
        for token in ('data-mta-cintillo', 'cintillo.js', 'cintillo.css'):
            if original.count(token) != updated.count(token):
                sys.exit(f'ERROR: alteracion inesperada de {token} en {rel}')
        path.write_text(updated, encoding='utf-8')
        changed.append(rel)
        print(f'ACTUALIZADO: {rel}')
    print(f'RESUMEN: {len(changed)} modificados; {len(missing)} ausentes; no se toco el cintillo.')
    if missing:
        print('NO ENCONTRADOS:', ', '.join(missing))
    if not changed and len(missing) == len(TARGETS):
        sys.exit('ERROR: no se encontro ninguna pagina prevista.')


if __name__ == '__main__':
    main()
