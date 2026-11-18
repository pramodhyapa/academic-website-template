"""Exercise catalogue growth/removal in a temporary copy, leaving the site alone."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(root, expect_ok=True):
    result = subprocess.run([sys.executable, str(root / 'build.py')], capture_output=True, text=True)
    if (result.returncode == 0) != expect_ok:
        raise AssertionError(result.stdout + result.stderr)


with tempfile.TemporaryDirectory(prefix='academic-template-check-') as folder:
    root = Path(folder)
    for name in ('content', 'src'):
        shutil.copytree(ROOT / name, root / name)
    shutil.copy2(ROOT / 'build.py', root / 'build.py')
    run(root)
    catalog_file = root / 'content/catalog.json'
    original = json.loads(catalog_file.read_text(encoding='utf-8'))
    expanded = original.copy()
    for index in range(5):
        entry = original[0].copy()
        entry.update(slug=f'added-{index}', title=f'Added article {index}', date=f'2026-11-{20+index}')
        expanded.append(entry)
    catalog_file.write_text(json.dumps(expanded), encoding='utf-8')
    run(root)
    output = root / 'dist'
    collection = (output / 'writing/index.html').read_text(encoding='utf-8')
    assert 'data-search-input' in collection
    # Menus are bounded while all seven entries remain discoverable.
    assert collection.count('class="card"') == 7
    menu = collection.split('<div class="dropdown">')[1].split('</div>')[0]
    assert menu.count('<small>') == 3
    assert menu.index('Added article 4') < menu.index('Added article 3') < menu.index('Added article 2')
    home = (output / 'index.html').read_text(encoding='utf-8')
    assert home.count('class="card"') == 2
    catalog_file.write_text(json.dumps(original), encoding='utf-8')
    run(root)
    assert not (output / 'writing/added-4/index.html').exists()
    assert 'data-search-input' not in (output / 'writing/index.html').read_text(encoding='utf-8')
    catalog_file.write_text(json.dumps(original + [original[0]]), encoding='utf-8')
    run(root, expect_ok=False)
    catalog_file.write_text(json.dumps(original), encoding='utf-8')
    (root / 'src/downloads/reading-notes.md').unlink()
    run(root, expect_ok=False)
    assert not (output / 'downloads/reading-notes.md').exists()
print('Passed: build, catalogue growth, latest-menu cap/order, search threshold, entry removal, duplicate rejection and missing-download detection.')
