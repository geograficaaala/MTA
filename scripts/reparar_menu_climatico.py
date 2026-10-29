#!/usr/bin/env python3
"""Repara SOLO el menú principal de cinco páginas climáticas existentes.
Seguro para repetición: no edita controladores, datos ni estructura del resto de la página.
"""
from pathlib import Path
import re
import sys

FILES = [
    'docs/clima_index.html', 'docs/precipitaciones_index.html',
    'docs/temperatura_index.html', 'docs/viento_index.html',
    'docs/agroclima_index.html',
]
NAV_RE = re.compile(r'<nav\b(?=[^>]*\bdata-nav\b)[^>]*>.*?</nav>', re.I | re.S)
STYLE = '<link rel="stylesheet" href="../assets/css/menu-climatico.css" data-mta-menu-climatico>'
SCRIPT = '<script defer src="../assets/js/menu-climatico.js" data-mta-menu-climatico></script>'

def new_nav(page):
    climate = [
        ('precipitaciones_index.html', 'Precipitación'),
        ('temperatura_index.html', 'Temperatura'),
        ('viento_index.html', 'Viento'),
        ('agroclima_index.html', 'Agroclima'),
        ('clima_index.html', 'Resumen climático'),
    ]
    links = '\n'.join(
        f'          <a href="./{path}"' + (' aria-current="page"' if page == path else '') + f'>{label}</a>'
        for path, label in climate)
    return f'''<nav class="nav mta-nav-climatica" aria-label="Navegación principal" data-nav>
      <a href="../index.html">Inicio</a>
      <details class="mta-nav-group">
        <summary>Recomendaciones agroclimáticas</summary>
        <div class="mta-nav-options">
          <a href="../boletines.html">Boletines</a>
          <a href="../infografias.html">Infografías</a>
          <a href="../mapas.html">Mapas</a>
        </div>
      </details>
      <details class="mta-nav-group">
        <summary{' aria-current="page"' if page in [x[0] for x in climate] else ''}>Información climática</summary>
        <div class="mta-nav-options">
{links}
        </div>
      </details>
      <a href="../spots-radiales.html">Spots radiales</a>
      <a href="../noticias.html">Noticias</a>
      <a href="../comentarios_index.html">Comentarios</a>
      <a href="../index.html#contacto">Contacto</a>
      <button type="button" data-search-open>Buscar</button>
    </nav>'''

def main():
    root = Path.cwd()
    errors = []
    changed = []
    for rel in FILES:
        path = root / rel
        if not path.exists():
            errors.append(f'No existe {rel}')
            continue
        original = path.read_text(encoding='utf-8')
        matches = list(NAV_RE.finditer(original))
        if len(matches) != 1:
            errors.append(f'{rel}: se esperaban 1 nav[data-nav], encontrados {len(matches)}')
            continue
        output = NAV_RE.sub(lambda _: new_nav(path.name), original, count=1)
        if 'data-mta-menu-climatico' not in output:
            if '</head>' not in output or '</body>' not in output:
                errors.append(f'{rel}: faltan cierres head/body')
                continue
            output = output.replace('</head>', '  ' + STYLE + '\n</head>', 1)
            output = output.replace('</body>', '  ' + SCRIPT + '\n</body>', 1)
        else:
            if STYLE not in output or SCRIPT not in output:
                errors.append(f'{rel}: marcadores del menú incompletos; revisar manualmente')
                continue
        if original != output:
            path.write_text(output, encoding='utf-8')
            changed.append(rel)
    print('HTML modificados:', ', '.join(changed) if changed else 'ninguno')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
