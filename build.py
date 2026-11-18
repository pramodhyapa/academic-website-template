"""Build a small static academic site. Python standard library only."""
from pathlib import Path
from string import Template
from datetime import date
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
import shutil
import hashlib

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / 'src', ROOT / 'dist'


def read_json(name):
    return json.loads((ROOT / 'content' / name).read_text(encoding='utf-8'))


def e(value):
    return escape(str(value), quote=True)


def href(url):
    """Reject active URLs, accidental local paths and remote protocol relatives."""
    parsed = urlsplit(url)
    if parsed.scheme not in ('', 'https', 'http', 'mailto') or url.startswith('//') or '\\' in url:
        raise ValueError(f'Unsupported URL: {url}')
    return e(url)


def nice_date(value):
    return date.fromisoformat(value).strftime('%d %B %Y').lstrip('0')


def build():
    site = read_json('site.json')
    catalog = read_json('catalog.json')
    publications = read_json('publications.json')
    education = read_json('education.json')
    slugs = set()
    for item in catalog:
        if item['collection'] not in ('writing', 'resources'):
            raise ValueError('Collection must be writing or resources')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', item['slug']):
            raise ValueError('Use a lowercase URL slug with hyphens')
        key = (item['collection'], item['slug'])
        if key in slugs:
            raise ValueError(f'Duplicate entry: {key}')
        slugs.add(key)
        date.fromisoformat(item['date'])
        if not (SRC / item['body']).resolve().is_relative_to(SRC.resolve()):
            raise ValueError('Article bodies must be inside src/')
    catalog.sort(key=lambda item: (item['date'], item.get('order', 0), item['slug']), reverse=True)
    count = int(site.get('latest_menu_count', 3))
    if not 1 <= count <= 5:
        raise ValueError('latest_menu_count must be between 1 and 5')
    OUT.mkdir(exist_ok=True)
    manifest = OUT / '.generated-pages.json'
    previous_pages = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    generated_pages = []
    asset_manifest = OUT / '.generated-assets.json'
    previous_assets = json.loads(asset_manifest.read_text(encoding='utf-8')) if asset_manifest.exists() else []
    template = Template((SRC / 'page.html').read_text(encoding='utf-8'))
    asset_version = hashlib.sha256((SRC / 'assets/site.css').read_bytes() + (SRC / 'assets/site.js').read_bytes()).hexdigest()[:10]

    def path(item):
        return f"{item['collection']}/{item['slug']}/"

    def nav(prefix, current):
        def link(label, url, active=False):
            state = ' aria-current="page"' if active else ''
            return f'<a href="{href(url)}"{state}>{e(label)}</a>'
        result = link('Home', f'{prefix}/index.html', current == 'home')
        result += link('Publications', f'{prefix}/index.html#publications')
        for collection in ('writing', 'resources'):
            recent = [item for item in catalog if item['collection'] == collection][:count]
            title = collection.title()
            state = ' aria-current="page"' if current == collection else ''
            result += f'<details class="nav-group"><summary{state}>{title}</summary><div class="dropdown">'
            for item in recent:
                result += f'<a href="{prefix}/{path(item)}"><small>{e(item["label"])}</small>{e(item["title"])}</a>'
            result += f'<a class="view-all" href="{prefix}/{collection}/">View all {collection} →</a></div></details>'
        result += link('Outreach', f'{prefix}/outreach.html', current == 'outreach')
        result += link('Contact', '#contact')
        return result

    def page(relative, title, description, body, current):
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        depth = len(Path(relative).parts) - 1
        prefix = '/'.join(['..'] * depth) or '.'
        socials = ''.join(f'<a href="{href(s["url"])}">{e(s["label"])}</a>' for s in site.get('socials', []))
        network = (SRC / 'assets/network.svg').read_text(encoding='utf-8')
        network = f'<div class="network" aria-hidden="true">{network}</div>'
        output = template.substitute(
            title=e(f'{title} · {site["name"]}' if title != site['name'] else title),
            description=e(description), prefix=prefix, name=e(site['name']),
            asset_version=asset_version,
            navigation=nav(prefix, current), body=body, network=network,
            email=href(site['email']), display_email=e(site['email'].replace('@', ' (at) ')),
            department=e(site['department']), institution=e(site['institution']), location=e(site['location']),
            socials=f'<div class="socials">{socials}</div>' if socials else '',
            motion=str(bool(site.get('network_motion', True))).lower(),
            year=date.today().year, demo_footer='<span>Fictional sample website</span>' if site.get('demo') else '')
        # Explicit filenames also work when opened directly with file://.
        def direct_link(match):
            url = urlsplit(match[2])
            if not url.scheme and not url.netloc and url.path.endswith('/'):
                value = url._replace(path=url.path + 'index.html').geturl()
                return match[1] + value + match[3]
            return match[0]
        output = re.sub(r"(href=[\"'])([^\"']+)([\"'])", direct_link, output)
        target.write_text(output, encoding='utf-8')
        generated_pages.append(relative)

    def card(item, prefix, heading='h2'):
        return f'''<article class="card" data-category="{e(item['category'])}" data-search="{e(item['title'] + ' ' + item['summary'] + ' ' + item['category'])}">
<img class="card-image" src="{prefix}/{e(item['image'])}" alt="" width="800" height="440" loading="lazy">
<div class="card-content"><span class="eyebrow">{e(item['label'])}</span>
<{heading}><a href="{prefix}/{path(item)}">{e(item['title'])}</a></{heading}>
<time datetime="{e(item['date'])}">{nice_date(item['date'])}</time><p>{e(item['summary'])}</p>
<div class="actions"><a class="button" href="{prefix}/{path(item)}">{'Read the article' if item['collection'] == 'writing' else 'Open resource'} <span aria-hidden="true">→</span></a></div></div></article>'''

    pub_html = ''
    for pub in publications:
        links = ''.join(f'<a class="button" href="{href(link["url"])}">{e(link["label"])}</a>' for link in pub.get('links', []))
        abstract = f'<details><summary>Abstract</summary><p>{e(pub["abstract"])}</p></details>' if pub.get('abstract') else ''
        pub_html += f'''<article class="publication"><img src="{e(pub['image'])}" alt="" width="140" height="140" loading="lazy"><div>
<span class="eyebrow">{e(pub['topic'])}</span><h3>{e(pub['title'])}</h3><p class="meta">{e(pub['venue'])}<br>{e(pub['authors'])}</p>
<p>{e(pub['summary'])}</p>{f'<div class="actions">{links}</div>' if links else ''}{abstract}</div></article>'''
    timeline = ''.join(f'<div class="timeline-item"><span class="years">{e(item["years"])}</span><div><h3>{e(item["degree"])}</h3><p class="institution">{e(item["institution"])}</p><p>{e(item["description"])}</p></div></div>' for item in education)
    latest = ''.join(card(item, '.', 'h3') for item in [entry for entry in catalog if entry['collection'] == 'writing'][:2])
    demo = '<span class="demo-label">Example academic website</span>' if site.get('demo') else ''
    cv = f'<a class="button" href="{href(site["cv_url"])}">Download CV</a>' if site.get('cv_url') else ''
    body = f'''<div class="wrap"><section class="hero" aria-labelledby="intro-title"><div class="hero-copy">{demo}<h1 id="intro-title">{e(site['name'])}</h1>
<p class="role">{e(site['role'])}<br>{e(site['institution'])}</p><p class="intro">{e(site['intro'])}</p><p>{e(site['about'])}</p>
<div class="actions"><a class="button primary" href="#publications">Explore my research ↓</a>{cv}</div></div>
<div class="hero-art"><img src="assets/research.svg" alt="An abstract illustration of waves crossing an ordered lattice" width="800" height="640"><p>Curiosity, calculations &amp; the occasional surprise</p></div></section></div>
<section class="section" id="publications"><div class="wrap"><div class="section-head"><h2>Selected publications</h2></div><div class="publication-list">{pub_html}</div></div></section>
<section class="section wash"><div class="wrap"><div class="section-head"><h2>Latest writing</h2><a href="writing/">All writing →</a></div><div class="cards">{latest}</div></div></section>
<section class="section" id="education"><div class="wrap"><div class="section-head"><h2>Education &amp; experience</h2></div><div class="timeline">{timeline}</div></div></section>'''
    page('index.html', site['name'], site['description'], body, 'home')

    for collection, deck in [('writing', 'Notes on research, ideas worth exploring, and things learned along the way.'), ('resources', 'Templates, practical guides and small tools you can use in your own work.')]:
        entries = [item for item in catalog if item['collection'] == collection]
        categories = sorted(set(item['category'] for item in entries))
        filters = '<button class="filter" data-filter="all" aria-pressed="true">All</button>'
        filters += ''.join(f'<button class="filter" data-filter="{e(category)}" aria-pressed="false">{e(category)}</button>' for category in categories)
        search = '<label class="search-label">Search<input type="search" placeholder="Find an entry" data-search-input></label>' if len(entries) >= 6 else ''
        tools = f'<div class="collection-tools" data-collection-tools hidden>{filters if len(categories) > 1 else ""}{search}</div>'
        body = f'''<div class="wrap collection" data-collection><header class="page-heading"><span class="eyebrow">{'Ideas &amp; explanations' if collection == 'writing' else 'Made to be useful'}</span><h1>{collection.title()}</h1><p>{deck}</p></header>
{tools}<div class="cards">{''.join(card(item, '..') for item in entries)}</div><p class="empty-state" role="status" hidden>No entries match. Try another search or category.</p></div>'''
        page(f'{collection}/index.html', collection.title(), deck, body, collection)

    for item in catalog:
        collection = item['collection']
        article = (SRC / item['body']).read_text(encoding='utf-8')
        download = f'<div class="actions"><a class="button primary" href="../../{href(item["download"])}" download>Download template ↓</a></div>' if item.get('download') else ''
        body = f'''<div class="wrap"><header class="article-header"><div class="article-bar"><span class="eyebrow">{e(item['label'])}</span><a class="button back-button" href="../">← All {collection}</a></div>
<h1>{e(item['title'])}</h1><p class="article-deck">{e(item['summary'])}</p><p class="meta">{e(site['name'])} · <time datetime="{e(item['date'])}">{nice_date(item['date'])}</time></p>{download}</header>
<article class="article-body">{'<p class="sample-note">This is a sample entry included with the website template.</p>' if site.get('demo') else ''}{article}<div class="article-end"><a class="button" href="../">← Explore all {collection}</a></div></article></div>'''
        page(f'{path(item)}index.html', item['title'], item['summary'], body, collection)

    body = '''<div class="wrap"><header class="page-heading"><span class="eyebrow">Beyond the paper</span><h1>Talks &amp; outreach</h1><p>A place for conversations, teaching and projects that bring research to a wider audience.</p></header>
<div class="outreach-grid"><article><h2>Public talks</h2><p>Add a talk title, a short description and a recording or slides when you have them. A few thoughtful examples are enough to start.</p></article><article><h2>Creative projects</h2><p>Use this section for films, workshops, community activities or other ways you share your work. These are placeholder sections to replace with your own projects.</p></article></div></div>'''
    page('outreach.html', 'Talks & outreach', 'Talks, teaching and public engagement.', body, 'outreach')
    page('404.html', 'Page not found', 'This page could not be found.', '<div class="wrap section"><h1>Page not found</h1><p>The page may have moved.</p><a class="button" href="./index.html">Back to home →</a></div>', '')
    generated_assets = copy_used_assets(generated_pages, previous_assets)
    for relative in set(previous_pages) - set(generated_pages):
        stale = (OUT / relative).resolve()
        if stale.is_relative_to(OUT.resolve()) and stale.suffix == '.html' and stale.is_file():
            stale.unlink()
    manifest.write_text(json.dumps(generated_pages, indent=2), encoding='utf-8')
    asset_manifest.write_text(json.dumps(generated_assets, indent=2), encoding='utf-8')
    check_links()
    print(f'Built {len(list(OUT.rglob("*.html")))} HTML pages in {OUT}')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            if attrs['id'] in self.ids:
                raise ValueError(f'Duplicate HTML id: {attrs["id"]}')
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if attrs.get(name):
                self.urls.append(attrs[name])


def copy_used_assets(pages, previous):
    """Copy only local assets referenced by generated pages or their stylesheets."""
    pending, used = [], set()

    def include(base, value):
        url = urlsplit(value)
        if url.scheme or url.netloc or not url.path:
            return
        target = (base / unquote(url.path)).resolve()
        if target.is_relative_to(OUT.resolve()):
            relative = target.relative_to(OUT.resolve()).as_posix()
            if relative.startswith(('assets/', 'downloads/')) and relative not in used:
                pending.append(relative)

    for relative in pages:
        page = OUT / relative
        parser = Links()
        parser.feed(page.read_text(encoding='utf-8'))
        for value in parser.urls:
            include(page.parent, value)
    while pending:
        relative = pending.pop()
        if relative in used:
            continue
        source = (SRC / relative).resolve()
        target = OUT / relative
        if not source.is_relative_to(SRC.resolve()) or source.is_symlink() or not source.is_file():
            if target.resolve().is_relative_to(OUT.resolve()) and target.is_file():
                target.unlink()
            raise ValueError(f'Missing or unsafe source asset: {relative}')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        used.add(relative)
        if source.suffix == '.css':
            text = source.read_text(encoding='utf-8')
            values = re.findall(r'url\(\s*[\"\']?([^\"\')]+)', text)
            values += re.findall(r'@import\s+[\"\']([^\"\']+)', text)
            for value in values:
                include(target.parent, value.strip())
    for relative in set(previous) - used:
        stale = (OUT / relative).resolve()
        if stale.is_relative_to(OUT.resolve()) and stale.is_file():
            stale.unlink()
    return sorted(used)


def check_links():
    parsed = {}
    for file in OUT.rglob('*.html'):
        parser = Links()
        parser.feed(file.read_text(encoding='utf-8'))
        parsed[file.resolve()] = parser
    errors = []
    for file, parser in parsed.items():
        for value in parser.urls:
            url = urlsplit(value)
            if url.scheme or value.startswith('//'):
                continue
            target = (file.parent / unquote(url.path)).resolve() if url.path else file
            if target.is_dir():
                target /= 'index.html'
            if not target.is_relative_to(OUT.resolve()) or not target.exists():
                errors.append(f'{file.relative_to(OUT)}: missing {value}')
            elif url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
                errors.append(f'{file.relative_to(OUT)}: missing anchor {value}')
    if errors:
        raise ValueError('\n'.join(errors))
    print('Local links, assets and HTML anchors checked.')


if __name__ == '__main__':
    build()
