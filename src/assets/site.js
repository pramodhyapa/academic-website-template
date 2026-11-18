/* Fresh, dependency-free interactions for the academic website starter. */
(() => {
  'use strict';
  document.body.classList.add('js');
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#main-navigation');
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });
  const groups = [...document.querySelectorAll('.nav-group')];
  groups.forEach(group => group.addEventListener('toggle', () => {
    if (group.open) groups.forEach(other => { if (other !== group) other.open = false; });
  }));
  document.addEventListener('click', event => {
    groups.forEach(group => { if (!group.contains(event.target)) group.open = false; });
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const open = groups.find(group => group.open);
    if (open) { open.open = false; open.querySelector('summary').focus(); }
    else if (nav.classList.contains('is-open')) {
      nav.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
    }
  });
  document.querySelectorAll('[data-collection]').forEach(collection => {
    const tools = collection.querySelector('[data-collection-tools]');
    const cards = [...collection.querySelectorAll('.card')];
    const filters = [...collection.querySelectorAll('[data-filter]')];
    const search = collection.querySelector('[data-search-input]');
    const status = collection.querySelector('[role="status"]');
    let category = 'all';
    tools.hidden = !(filters.length || search);
    function update() {
      const query = (search?.value || '').toLocaleLowerCase().trim();
      cards.forEach(card => {
        card.hidden = (category !== 'all' && card.dataset.category !== category) || !card.dataset.search.toLocaleLowerCase().includes(query);
      });
      status.hidden = cards.some(card => !card.hidden);
    }
    filters.forEach(button => button.addEventListener('click', () => {
      category = button.dataset.filter;
      filters.forEach(other => other.setAttribute('aria-pressed', String(other === button)));
      update();
    }));
    search?.addEventListener('input', update);
  });

  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const network = document.querySelector('.network svg');
  const nodes = network ? [...network.querySelectorAll('circle')].map(circle => ({
    circle, x: Number(circle.getAttribute('cx')), y: Number(circle.getAttribute('cy'))
  })) : [];
  const edges = network ? [...network.querySelectorAll('line')].map(line => ({
    line, a: nodes[Number(line.dataset.a)], b: nodes[Number(line.dataset.b)]
  })) : [];
  function drawNetwork(t) {
    nodes.forEach(node => {
      // A gentle decorative travelling wave. Geometry is independently authored.
      const phase = node.x * .007 + node.y * .004 - t * .8;
      node.px = node.x + (reduced.matches ? 0 : 7 * Math.sin(phase));
      node.py = node.y + (reduced.matches ? 0 : 5 * Math.cos(phase + .5));
      node.circle.setAttribute('cx', node.px); node.circle.setAttribute('cy', node.py);
    });
    edges.forEach(({line, a, b}) => {
      line.setAttribute('x1', a.px); line.setAttribute('y1', a.py);
      line.setAttribute('x2', b.px); line.setAttribute('y2', b.py);
    });
  }
  const demos = [...document.querySelectorAll('[data-wave-demo]')].map(root => {
    const canvas = root.querySelector('canvas'), ctx = canvas.getContext('2d');
    const slider = root.querySelector('input'), output = root.querySelector('output');
    slider.addEventListener('input', () => { output.value = `${slider.value} sites`; drawWave({canvas, ctx, slider}, 0); });
    return {canvas, ctx, slider};
  });
  function drawWave({canvas, ctx, slider}, time) {
    const w = canvas.width, h = canvas.height, n = 33;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = '#dbe3e9'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(22, h / 2); ctx.lineTo(w - 22, h / 2); ctx.stroke();
    const points = Array.from({length:n}, (_, i) => [24 + i * (w - 48) / (n - 1), h / 2 - 75 * Math.sin(i * Math.PI * 2 / Number(slider.value) - time * 1.7)]);
    ctx.strokeStyle = '#9ab1c0'; ctx.lineWidth = 3; ctx.beginPath();
    points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
    points.forEach(([x, y], i) => { ctx.fillStyle = i === 16 ? '#38694f' : '#236b9c'; ctx.beginPath(); ctx.arc(x, y, i === 16 ? 8 : 5, 0, Math.PI * 2); ctx.fill(); });
  }
  const motion = document.body.dataset.networkMotion === 'true';
  let frame = 0, previous = -100;
  function animate(ms) {
    frame = 0;
    if (document.hidden) return;
    if (ms - previous > 40) {
      const t = reduced.matches ? 0 : ms / 1000;
      if (motion && network && network.getBoundingClientRect().bottom > 0) drawNetwork(t);
      demos.forEach(demo => { const box = demo.canvas.getBoundingClientRect(); if (box.bottom > 0 && box.top < innerHeight) drawWave(demo, t); });
      previous = ms;
    }
    if (!reduced.matches && ((motion && network) || demos.length)) frame = requestAnimationFrame(animate);
  }
  function start() {
    if (frame) cancelAnimationFrame(frame);
    previous = -100;
    if (network) drawNetwork(0);
    demos.forEach(demo => drawWave(demo, 0));
    frame = requestAnimationFrame(animate);
  }
  reduced.addEventListener('change', start);
  document.addEventListener('visibilitychange', start);
  start();
})();
