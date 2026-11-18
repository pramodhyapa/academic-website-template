"""Create original placeholder artwork; no traced or third-party geometry."""
from pathlib import Path
import math
import random

ASSETS = Path(__file__).resolve().parents[1] / 'src' / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)


def svg(name, width, height, body):
    (ASSETS / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">{body}</svg>', encoding='utf-8')


# Abstract lattice surface, constructed directly from parametric coordinates.
body = '<rect width="800" height="640" fill="#eff3f4"/><circle cx="460" cy="245" r="210" fill="#e1ece5"/>'
points = {}
for row in range(9):
    for col in range(9):
        x = 105 + col * 55 + row * 16
        y = 220 + row * 25 - col * 6 - 27 * math.sin(col * .8 + row * .65)
        points[row, col] = (x, y)
for row in range(9):
    coords = ' '.join(f'{points[row, col][0]:.1f},{points[row, col][1]:.1f}' for col in range(9))
    body += f'<polyline points="{coords}" fill="none" stroke="#236b9c" stroke-width="2" opacity=".65"/>'
for col in range(9):
    coords = ' '.join(f'{points[row, col][0]:.1f},{points[row, col][1]:.1f}' for row in range(9))
    body += f'<polyline points="{coords}" fill="none" stroke="#38694f" stroke-width="1.3" opacity=".45"/>'
for (row, col), (x, y) in points.items():
    body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3 if (row+col)%3 else 5}" fill="{["#38694f", "#236b9c", "#90b5a0"][(row+col)%3]}"/>'
body += '<path d="M130 475h540" stroke="#c6d4ce"/><circle cx="140" cy="475" r="4" fill="#38694f"/><circle cx="660" cy="475" r="4" fill="#236b9c"/>'
svg('research.svg', 800, 640, body)

body = '<rect width="800" height="440" fill="#eff3f4"/><rect x="70" y="80" width="660" height="280" fill="#e7efe9"/>'
for offset, opacity in [(0, 1), (45, .32), (-45, .15)]:
    coords = ' '.join(f'{x},{220 + offset - 65 * math.sin(x*.019):.2f}' for x in range(70, 731, 3))
    body += f'<polyline points="{coords}" fill="none" stroke="#236b9c" stroke-width="3" opacity="{opacity}"/>'
for x in range(84, 730, 28):
    y = 220 - 65 * math.sin(x*.019)
    body += f'<circle cx="{x}" cy="{y:.2f}" r="5" fill="#162f49"/>'
svg('wave.svg', 800, 440, body)

body = '<rect width="800" height="440" fill="#eef2ee"/><rect x="210" y="54" width="380" height="330" fill="#d8e2da" transform="rotate(5 400 220)"/><rect x="205" y="48" width="380" height="330" fill="#fff" stroke="#b7ccc0"/>'
body += '<path d="M250 108h160" stroke="#38694f" stroke-width="9"/>'
for y, w in [(150,280),(180,245),(210,265),(255,280),(285,240),(315,260)]:
    body += f'<path d="M250 {y}h{w}" stroke="#d7e0e5" stroke-width="4"/>'
body += '<path d="M555 310l48-157 17 5-48 157-14 15z" fill="#236b9c"/><path d="M558 330l14-15-17-5z" fill="#162f49"/>'
svg('notebook.svg', 800, 440, body)
svg('favicon.svg', 48, 48, '<rect width="48" height="48" rx="8" fill="#e9f2eb"/><path d="M6 26q6-22 12 0t12 0t12 0" fill="none" stroke="#236b9c" stroke-width="3"/>')

# One newly generated graph, including off-canvas nodes, not image extraction.
rng = random.Random(48192)
nodes = [(col * 190 - 90 + rng.uniform(-55,55), row * 170 - 70 + rng.uniform(-45,45)) for row in range(6) for col in range(9)]
edges = []
for row in range(6):
    for col in range(9):
        a = row * 9 + col
        if col < 8:
            edges.append((a, a + 1))
        if row < 5:
            edges.append((a, a + 9))
            if col < 8 and (row + col) % 2 == 0:
                edges.append((a, a + 10))
body = '<g stroke="#677581" stroke-width="1.6">'
for a, b in edges:
    x1, y1 = nodes[a]
    x2, y2 = nodes[b]
    body += f'<line data-a="{a}" data-b="{b}" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>'
body += '</g><g fill="#677581">'
for x, y in nodes:
    body += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{rng.uniform(5,11):.2f}"/>'
body += '</g>'
svg('network.svg', 1440, 750, body)
print('Created five original SVG assets.')
