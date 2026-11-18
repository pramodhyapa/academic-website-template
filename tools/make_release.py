"""Build and package the editable starter with a ready-to-open website."""
from pathlib import Path
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('README.md', 'LICENSE', 'LICENSE-STATUS.md', 'CREDITS.md', 'build.py',
         'preview.py', '.gitignore', '.gitattributes')
DIRECTORIES = ('content', 'src', 'tools', 'docs', '.github', 'dist')
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
    files = [root / name for name in FILES]
    for name in DIRECTORIES:
        files.extend(p for p in (root / name).rglob('*') if p.is_file())
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(files):
            relative = file.relative_to(root)
            if any(part in ('__pycache__', '.git') for part in relative.parts):
                continue
            if file.suffix in ('.pyc', '.pyo') or file.name.startswith('.env'):
                continue
            if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
                raise ValueError(f'Cannot package a link outside the source: {relative}')
            archive.write(file, 'academic-website-template/' + relative.as_posix())
        archive.writestr('academic-website-template/index.html', LAUNCHER)
        archive.writestr('academic-website-template/VERSION', version + '\n')
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='v1.0.0')
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
- MIT licence, historical theme credits, and customization instructions.
- Build checks and optional GitHub Pages deployment workflows.

GitHub's automatic **Source code** downloads omit the built `dist/` directory;
run `python build.py` first if you choose those downloads.

`SHA256SUMS` records the checksum of the ready-to-open ZIP.
''', encoding='utf-8')
    print(f'Created {output.name} ({output.stat().st_size:,} bytes); SHA-256 {digest}')


if __name__ == '__main__':
    main()
