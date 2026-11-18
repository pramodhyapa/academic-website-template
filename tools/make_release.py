"""Build and package the editable starter with a ready-to-open website."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('LICENSE', 'build.py', 'content/site.json',
         'content/publications.json', 'content/education.json', 'content/catalog.json',
         'src/page.html', 'src/assets/network.svg')
LAUNCHER = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="0;url=dist/index.html">
<title>Open the academic website</title></head>
<body><p><a href="dist/index.html">Open the academic website →</a></p></body></html>
'''


def package(root, output, version):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', version):
        raise ValueError('Use a version such as v1.0.0')
    if not (root / 'dist/index.html').is_file():
        raise ValueError('Build the website before packaging it')
    assets = json.loads((root / 'dist/.generated-assets.json').read_text(encoding='utf-8'))
    pages = json.loads((root / 'dist/.generated-pages.json').read_text(encoding='utf-8'))
    catalog = json.loads((root / 'content/catalog.json').read_text(encoding='utf-8'))
    names = set(FILES)
    names.update('src/' + name for name in assets)
    names.update('src/' + item['body'] for item in catalog)
    names.update('dist/' + name for name in assets + pages)
    names.update(['dist/.generated-assets.json', 'dist/.generated-pages.json'])
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            file = root / name
            if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
                raise ValueError(f'Cannot package a link outside the source: {name}')
            archive.write(file, 'academic-website-template/' + name)
        archive.writestr('academic-website-template/index.html', LAUNCHER)
        credits = (root / 'README.md').read_text(encoding='utf-8').split('## Licence and credits\n', 1)[1]
        archive.writestr('academic-website-template/README.md', f'''# Academic website starter {version}

Open `index.html` to view the built example. No server or Python is needed
to view it. The example researcher, Bodhi B. Björn, is fictional.

## Edit and rebuild

Requires Python 3.10 or newer, with no packages to install.

- `content/site.json`: name, introduction, contact, links and motion settings.
- `content/publications.json`: publication entries.
- `content/education.json`: education or experience entries.
- `content/catalog.json`: Writing and Resources entries and their body paths.
- `src/writing/`, `src/resources/`: sample article and resource bodies.
- `src/page.html`: shared page shell and footer.
- `src/assets/`: styles, browser interactions and original illustrations.
- `src/downloads/`: the sample download referenced by the catalogue.

Set `demo` to `false` in `content/site.json` after replacing the examples.
Run `python build.py` after editing; it checks local links and regenerates
`dist/`. Use `python3` instead if that is your system's Python command.
For an optional local server, run:
`python -m http.server 8767 --bind 127.0.0.1 --directory dist`
and open http://127.0.0.1:8767.
Publish the contents of `dist/` on any static host.

The two `.generated-*.json` files in `dist/` track generated files so rebuilds
can remove obsolete entries. Keep them locally; they need not be uploaded.
Repository tests, CI configuration, screenshots and release tools are not
needed to use this starter and are omitted from this download.

Full instructions and optional GitHub Pages workflows:
https://github.com/pramodhyapa/academic-website-template

## Licence and credits

{credits}''')
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='v1.0.1')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'build.py')], check=True)
    directory = ROOT / 'release'
    output = directory / 'academic-website-template.zip'
    digest = package(ROOT, output, args.version)
    (directory / 'SHA256SUMS').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
    (directory / 'RELEASE-NOTES.md').write_text(
        f'''Academic website template {args.version}

Download **academic-website-template.zip**, extract it, and open **index.html**.
The ZIP includes the built website and editable source. Python 3.10 or newer
is needed only to rebuild after changing the source.

- Fictional Bodhi B. Björn example website with research, publications,
  Writing, Resources, outreach and contact sections.
- Native browser interactions and original geometric artwork.
- MIT licence, historical theme credits, and concise customization instructions.
- Only referenced editable source and built output. Maintenance workflows,
  tests, screenshots, release tools and redundant documentation are excluded.

GitHub's automatic **Source code** downloads omit the built `dist/` directory;
run `python build.py` first if you choose those downloads.

`SHA256SUMS` records the checksum of the ready-to-open ZIP.
''', encoding='utf-8')
    print(f'Created {output.name} ({output.stat().st_size:,} bytes); SHA-256 {digest}')


if __name__ == '__main__':
    main()
