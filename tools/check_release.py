"""Check project-subdirectory hosting and the ready-to-open release archive."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen
import importlib.util
import json
import shutil
import tempfile
import threading
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
spec = importlib.util.spec_from_file_location('release_package', ROOT / 'tools/make_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

assert (ROOT / 'dist/index.html').is_file(), 'Run python build.py first'
assert 'MIT License' in (ROOT / 'LICENSE').read_text(encoding='utf-8')
assert (ROOT / 'docs/preview.jpg').is_file(), 'README screenshot is missing'
build.check_links()


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


with tempfile.TemporaryDirectory(prefix='academic-template-release-check-') as folder:
    temp = Path(folder)
    prefix = 'a-repository-subdirectory'
    shutil.copytree(ROOT / 'dist', temp / prefix)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(temp)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}/{prefix}/'
    checked = set()
    try:
        for page in (ROOT / 'dist').rglob('*.html'):
            parser = build.Links()
            parser.feed(page.read_text(encoding='utf-8'))
            current = base + page.relative_to(ROOT / 'dist').as_posix()
            for value in [current, *parser.urls]:
                target = urljoin(current, value)
                parsed = urlsplit(target)
                if parsed.netloc != urlsplit(base).netloc:
                    continue
                assert parsed.path.startswith('/' + prefix + '/'), f'Escapes project URL: {value}'
                target = parsed._replace(fragment='').geturl()
                if target not in checked:
                    with urlopen(target, timeout=10) as response:
                        assert response.status == 200, target
                    checked.add(target)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    output = temp / 'academic-website-template.zip'
    release.package(ROOT, output, 'v1.0.0')
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        for required in ('index.html', 'dist/index.html', 'LICENSE', 'CREDITS.md',
                         'README.md', 'content/site.json', 'src/page.html', 'build.py'):
            assert 'academic-website-template/' + required in names, required
        assert 'url=dist/index.html' in archive.read('academic-website-template/index.html').decode('utf-8')
        assert not any('/.git/' in n or '/__pycache__/' in n or '/.env' in n for n in names)
        config = json.loads(archive.read('academic-website-template/content/site.json'))
        assert config['name'] == json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))['name']
print(f'Passed: {len(checked)} project-subdirectory URLs, release licence/screenshot and editable offline ZIP.')
