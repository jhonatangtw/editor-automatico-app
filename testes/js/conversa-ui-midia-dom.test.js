/* Conversa no DOM (0.22.1): prévia das entregas de mídia, lightbox, "Colocar
   na timeline" que só preenche, entrega remota baixando para o projeto, e a
   barra do topo com Histórico / + Nova / renomear / apagar com confirmação.

   jsdom da banca do Tools PRO, como o conversa-ui-dom.test.js. Armadilhas da
   banca respeitadas (memória banca-jsdom-painel-toolspro):
   - play/pause/load de mídia DUBLADOS (o jsdom lança "not implemented");
   - getContext do canvas dublado (sem o pacote canvas ele só reclama);
   - visibilidade pelo atributo `hidden`, nunca por getComputedStyle;
   - texto varrido nó a nó atrás de undefined/NaN (banca-nao-ve-nan-na-tela). */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const CANDIDATOS = [
  process.env.JSDOM_DIR,
  path.join(os.homedir(), 'Documents/03_Apps/Editor Black Belt/dist-toolspro/testes/node_modules/jsdom'),
].filter(Boolean);
let JSDOM = null;
for (const c of CANDIDATOS) { try { JSDOM = require(c).JSDOM; break; } catch (_) { /* próximo */ } }
const PULAR = !JSDOM && 'jsdom não encontrado';

const CODIGO = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'conversa-ui.js'), 'utf8');
const espera = (ms) => new Promise((r) => setTimeout(r, ms));
const P = '/Users/aluno/Documents/Editor Automático/Projetos/ad07/media';
const IMGS = Array.from({ length: 9 }, (_, i) => ({ tipo: 'imagem', caminho: `${P}/imagens/broll-0${i + 1}.png` }));
const MSGS_MIDIA = [
  { role: 'user', content: 'gere as imagens' },
  { role: 'assistant', content: 'pronto', provedor: 'claude', passos: [
    { tipo: 'ferramenta', nome: 'Bash', entrada: { command: 'higgsfield generate create x' }, estado: 'ok', resultado: 'ok', midias: IMGS },
    { tipo: 'ferramenta', nome: 'Bash', entrada: { command: 'heygen video get' }, estado: 'ok', resultado: '{}',
      midias: [{ tipo: 'video', caminho: `${P}/videos/hook.mp4` }] },
    { tipo: 'texto', texto: 'Locução pronta.', midias: [{ tipo: 'audio', caminho: `${P}/audio/voz.mp3` }, IMGS[0]] },
  ] },
];

function montar(o = {}) {
  const dom = new JSDOM('<!doctype html><html><body><div id="c" style="height:700px"></div></body></html>',
    { runScripts: 'outside-only', pretendToBeVisual: true, url: 'http://127.0.0.1:9/' });
  const w = dom.window;
  w.HTMLMediaElement.prototype.play = function () { this._tocando = true; return Promise.resolve(); };
  w.HTMLMediaElement.prototype.pause = function () { this._tocando = false; };
  w.HTMLMediaElement.prototype.load = function () {};
  w.HTMLCanvasElement.prototype.getContext = () => null;
  w.confirm = () => { throw new Error('confirm() não pode ser usado'); };
  if (o.lembrada) w.localStorage.setItem('editor-automatico:conversa:' + (o.janela || 'app'), o.lembrada);
  const est = { posts: [], gets: [], tarefa: 'rodando', conversas: o.conversas || [
    { id: 'c1', titulo: 'B-roll do AD07', quando: Date.now() / 1000 - 60, mensagens: 2, projeto: 'ad07', projeto_nome: 'AD07 Body' },
    { id: 'c2', titulo: 'Legenda karaokê', quando: Date.now() / 1000 - 86400 * 1.2, mensagens: 6, projeto: null, projeto_nome: null },
  ], destino: o.destino !== undefined ? o.destino : { pasta: '/p', projeto: 'ad07', nome: 'AD07' } };
  const conversa = (cid) => ({
    c1: { conversa: 'c1', mensagens: o.mensagens || MSGS_MIDIA, meta: { id: 'c1', titulo: 'B-roll do AD07', criada: 1, projeto_nome: 'AD07', destino: est.destino } },
    c2: { conversa: 'c2', mensagens: [{ role: 'user', content: 'legenda karaokê' }, { role: 'assistant', content: 'Bora fazer a legenda.' }],
      meta: { id: 'c2', titulo: 'Legenda karaokê', criada: 1 } },
  }[cid] || { conversa: cid, mensagens: [], meta: { id: cid, titulo: cid } });
  w.fetch = async (url, op) => {
    const u = String(url).replace(/^http:\/\/[^/]+/, '');
    const metodo = (op && op.method) || 'GET';
    const corpo = op && op.body && typeof op.body === 'string' ? JSON.parse(op.body) : null;
    let d = { ok: true }, status = 200;
    if (metodo === 'GET') est.gets.push(u); else est.posts.push([u, corpo]);
    const rota = u.split('?')[0];
    if (rota === '/api/conversa' && metodo === 'GET') d = conversa('c1');
    else if (rota === '/api/conversas' && metodo === 'GET') {
      const q = new URL(u, 'http://x').searchParams.get('q');
      d = { conversas: est.conversas.filter((c) => !q || c.titulo.toLowerCase().includes(q.toLowerCase())) };
    } else if (rota === '/api/conversas/nova') d = { conversa: 'c9' };
    else if (rota === '/api/conversas/apagar') { est.conversas = est.conversas.filter((c) => c.id !== corpo.conversa); d = { ok: true }; }
    else if (/\/renomear$/.test(rota)) d = { ok: true, meta: { titulo: corpo.titulo, criada: 1 } };
    else if (/\/aprovacao$/.test(rota)) d = { cartao: null };
    else if (/\/destino$/.test(rota)) { est.destino = { pasta: '/p2', projeto: corpo.projeto, nome: 'AD08' }; d = { ok: true, destino: est.destino }; }
    else if (/^\/api\/conversas\/[^/]+$/.test(rota)) d = conversa(rota.split('/').pop());
    else if (rota === '/api/ia') d = { escolhido: 'claude', provedores: [{ id: 'claude', nome: 'Claude', pronto: true }] };
    else if (rota === '/api/midia/info') {
      const p = new URL(u, 'http://x').searchParams.get('p');
      d = /\.mp4$/.test(p) ? { tipo: 'video', largura: 1080, altura: 1920, duracao: 3.2 } : { tipo: 'audio', duracao: 12 };
    } else if (rota === '/api/midia/picos') d = { picos: [0.1, 0.5, 1, 0.4], duracao: 12 };
    else if (rota === '/api/midia/baixar') {
      if (!est.destino) { status = 409; d = { erro: 'Em qual projeto salvar?', precisa_destino: true, projetos: [{ id: 'ad08', nome: 'AD08' }] }; }
      else { await espera(o.atrasoBaixar || 80); d = { caminho: `${est.destino.pasta}/media/videos/entrega.mp4`, tipo: 'video', destino: est.destino }; }
    } else if (rota === '/api/conversa' && metodo === 'POST') d = { tarefa: 't1' };
    else if (rota.startsWith('/api/tarefas/')) d = { estado: est.tarefa, cancelavel: true, seq: 0, total: 0, novos: [], resultado: { conversa: 'c1' } };
    return { ok: status < 400, status, json: async () => JSON.parse(JSON.stringify(d)) };
  };
  w.eval(CODIGO);
  const el = w.document.getElementById('c');
  const cv = w.montarConversa(el, Object.assign({ api: 'http://127.0.0.1:9', token: 'tk' }, o.op || {}));
  test.after(() => { try { cv.desmontar(); } catch (_) { /* já saiu */ } est.tarefa = 'pronto'; setTimeout(() => w.close(), 1500); });
  return { w, el, cv, est, entrada: el.querySelector('.cv-entrada') };
}

const tecla = (w, alvo, key) => alvo.dispatchEvent(new w.KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
function lixo(w, el) {
  const ruins = [];
  const tw = w.document.createTreeWalker(el, 4);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) if (/\b(undefined|NaN|Infinity|null)\b/.test(n.nodeValue)) ruins.push(n.nodeValue);
  return ruins;
}

test('grade de imagens, vídeo com capa e proporção, áudio com tempo', { skip: PULAR }, async () => {
  const { w, el } = montar();
  await espera(150);
  const figs = el.querySelectorAll('.cv-mid-img');
  assert.equal(figs.length, 9, 'a imagem repetida no texto não aparece de novo');
  assert.match(figs[0].querySelector('img').getAttribute('src'), /\/api\/midia\/quadro\?p=.*broll-01\.png&w=480&t=tk/);
  assert.equal(figs[0].querySelector('img').getAttribute('loading'), 'lazy');
  const v = el.querySelector('.cv-mid-video video');
  assert.equal(v.getAttribute('preload'), 'metadata');
  assert.match(v.getAttribute('poster'), /\/api\/midia\/quadro/);
  assert.match(v.getAttribute('src'), /\/api\/arquivo\?p=.*hook\.mp4&t=tk/);          // sem IntersectionObserver: ativa já
  assert.equal(el.querySelector('.cv-mid-video .cv-mid-meta').textContent, '0:03 · 9:16');
  const au = el.querySelector('.cv-mid-audio');
  assert.equal(au.querySelector('.cv-mid-tempo').textContent, '0:00 / 0:12');
  assert.equal(au.querySelector('audio').getAttribute('src'), null, 'áudio só carrega no play');
  au.querySelector('[data-audio-play]').click();
  assert.match(au.querySelector('audio').getAttribute('src'), /voz\.mp3/);
  assert.equal(au.querySelector('audio')._tocando, true);
  // botões em cada mídia
  const rotulos = [...el.querySelector('.cv-mid-video').querySelectorAll('[data-mid-acao]')].map((b) => b.getAttribute('title'));
  assert.deepEqual(rotulos, ['Mostrar no Finder', 'Colocar na timeline', 'Copiar caminho']);
  assert.deepEqual(lixo(w, el), []);
});

test('lightbox: abre com contador, setas andam, Esc fecha e não para a resposta', { skip: PULAR }, async () => {
  const { w, el, est } = montar();
  await espera(150);
  const lb = el.querySelector('.cv-lb');
  assert.equal(lb.hidden, true);
  el.querySelectorAll('[data-lb]')[2].click();
  assert.equal(lb.hidden, false);
  assert.equal(lb.querySelector('.cv-lb-conta').textContent, '3 de 9');
  assert.match(lb.querySelector('.cv-lb-img').getAttribute('src'), /\/api\/arquivo\?p=.*broll-03\.png/);
  tecla(w, w.document.activeElement || w.document.body, 'ArrowRight');
  assert.equal(lb.querySelector('.cv-lb-conta').textContent, '4 de 9');
  tecla(w, w.document.body, 'ArrowLeft'); tecla(w, w.document.body, 'ArrowLeft');
  assert.equal(lb.querySelector('.cv-lb-conta').textContent, '2 de 9');
  lb.querySelector('[data-lb-ir="-1"]').click(); lb.querySelector('[data-lb-ir="-1"]').click();
  assert.equal(lb.querySelector('.cv-lb-conta').textContent, '9 de 9', 'a seta dá a volta');
  tecla(w, lb.querySelector('[data-lb-fechar]'), 'Escape');
  assert.equal(lb.hidden, true);
  assert.equal(est.posts.filter(([u]) => /cancelar/.test(u)).length, 0);
});

test('"Colocar na timeline" só preenche; quem envia é o clique', { skip: PULAR }, async () => {
  const { el, est, entrada } = montar();
  await espera(150);
  el.querySelector('.cv-mid-video [data-mid-acao="timeline"]').click();
  await espera(120);
  assert.match(entrada.value, /coloque na timeline ativa, na posição do playhead, pelo Tools PRO/);
  assert.ok(entrada.value.includes(`"${P}/videos/hook.mp4"`));
  assert.equal(est.posts.filter(([u]) => u === '/api/conversa').length, 0, 'enviou sem o clique');
  el.querySelector('.cv-enviar').click();
  await espera(60);
  const env = est.posts.filter(([u]) => u === '/api/conversa');
  assert.equal(env.length, 1);
  assert.ok(env[0][1].texto.includes('hook.mp4'));
});

test('entrega remota: "baixando…" e depois a prévia do arquivo no projeto', { skip: PULAR }, async () => {
  const msgs = [{ role: 'assistant', content: 'ok', passos: [{ tipo: 'ferramenta', nome: 'Bash', estado: 'ok',
    midias: [{ tipo: 'video', url: 'https://cdn.exemplo.invalid/hf.mp4' }] }] }];
  const { el, est } = montar({ mensagens: msgs, atrasoBaixar: 200 });
  await espera(100);
  assert.match(el.querySelector('.cv-mid-remota').textContent, /baixando…/);
  await espera(300);
  assert.equal(el.querySelector('.cv-mid-remota'), null);
  assert.match(el.querySelector('.cv-mid-video video').getAttribute('src'), /%2Fp%2Fmedia%2Fvideos%2Fentrega\.mp4/);
  const b = est.posts.filter(([u]) => u === '/api/midia/baixar');
  assert.equal(b.length, 1, 'não baixa duas vezes');
  assert.deepEqual(b[0][1], { conversa: 'c1', url: 'https://cdn.exemplo.invalid/hf.mp4', tipo: 'video' });
});

test('sem projeto: o cartão pergunta em qual projeto salvar e só baixa depois', { skip: PULAR }, async () => {
  const msgs = [{ role: 'assistant', content: 'ok', passos: [{ tipo: 'ferramenta', nome: 'Bash', estado: 'ok',
    midias: [{ tipo: 'video', url: 'https://cdn.exemplo.invalid/hf.mp4' }] }] }];
  const { el, est } = montar({ mensagens: msgs, destino: null });
  await espera(150);
  const card = el.querySelector('.cv-mid-remota');
  assert.match(card.textContent, /Em qual projeto salvar\?/);
  assert.ok(card.querySelector('[data-destino-escolher]'));
  card.querySelector('[data-destino-projeto="ad08"]').click();
  await espera(300);
  assert.ok(est.posts.some(([u, c]) => /\/destino$/.test(u) && c.projeto === 'ad08'));
  assert.equal(est.posts.filter(([u]) => u === '/api/midia/baixar').length, 2);    // a recusa e a de verdade
  assert.match(el.querySelector('.cv-mid-video video').getAttribute('src'), /%2Fp2%2Fmedia/);
});

test('barra: título, Histórico com busca, abrir, apagar com confirmação na tela, + Nova', { skip: PULAR }, async () => {
  const { w, el, est } = montar({ mensagens: [{ role: 'user', content: 'oi' }] });
  await espera(120);
  const titulo = el.querySelector('.cv-titulo');
  assert.equal(titulo.value, 'B-roll do AD07');
  // histórico
  el.querySelector('[data-historico]').click();
  await espera(60);
  const hist = el.querySelector('.cv-hist');
  assert.equal(hist.hidden, false);
  const itens = () => [...hist.querySelectorAll('.cv-hist-item')];
  assert.equal(itens().length, 2);
  assert.match(itens()[0].textContent, /B-roll do AD07/); assert.match(itens()[0].textContent, /hoje \d\d:\d\d · AD07 Body · 2 mensagens/);
  assert.match(itens()[0].textContent, /aberta/);
  assert.match(itens()[1].textContent, /ontem \d\d:\d\d · 6 mensagens/);
  // busca
  const busca = hist.querySelector('.cv-hist-busca');
  busca.value = 'karaok'; busca.dispatchEvent(new w.Event('input', { bubbles: true }));
  await espera(320);
  assert.ok(est.gets.some((u) => u === '/api/conversas?q=karaok'));
  assert.equal(itens().length, 1);
  // abrir
  hist.querySelector('[data-hist-abrir="c2"]').click();
  await espera(80);
  assert.equal(hist.hidden, true);
  assert.equal(titulo.value, 'Legenda karaokê');
  assert.match(el.querySelector('.cv-msgs').textContent, /Bora fazer a legenda/);
  assert.equal(w.localStorage.getItem('editor-automatico:conversa:app'), 'c2');
  // apagar: pede confirmação DENTRO da tela (confirm() lançaria)
  el.querySelector('[data-historico]').click();
  await espera(60);
  hist.querySelector('[data-hist-apagar="c2"]').click();
  assert.match(hist.querySelector('.cv-hist-item.confirma').textContent, /Apagar Legenda karaokê\?/);
  hist.querySelector('[data-hist-confirma="nao"]').click();
  assert.equal(hist.querySelector('.cv-hist-item.confirma'), null);
  assert.equal(est.posts.filter(([u]) => u === '/api/conversas/apagar').length, 0);
  hist.querySelector('[data-hist-apagar="c2"]').click();
  hist.querySelector('[data-hist-confirma="c2"]').click();
  await espera(60);
  assert.deepEqual(est.posts.filter(([u]) => u === '/api/conversas/apagar').map(([, c]) => c), [{ conversa: 'c2' }]);
  assert.equal(titulo.value, 'Nova conversa', 'apagou a aberta: a tela zera');
  assert.equal(el.querySelector('.cv-msgs').textContent.includes('Bora'), false);
  assert.equal(itens().length, 0);                              // a busca "karaok" segue aplicada
  assert.match(hist.querySelector('.cv-hist-vazio').textContent, /Nenhuma conversa com isso/);
  // Esc fecha o histórico
  tecla(w, hist.querySelector('.cv-hist-busca'), 'Escape');
  assert.equal(hist.hidden, true);
  // + Nova
  el.querySelector('.cv-barra [data-nova]').click();
  await espera(60);
  assert.ok(est.posts.some(([u]) => u === '/api/conversas/nova'));
  assert.equal(w.localStorage.getItem('editor-automatico:conversa:app'), 'c9');
  assert.deepEqual(lixo(w, el), []);
});

test('renomear pelo título: Enter grava, Esc desfaz', { skip: PULAR }, async () => {
  const { w, el, est } = montar({ mensagens: [{ role: 'user', content: 'oi' }] });
  await espera(120);
  const t = el.querySelector('.cv-titulo');
  t.focus(); t.value = 'Legenda do AD07'; tecla(w, t, 'Enter'); t.blur();
  await espera(60);
  const r = est.posts.filter(([u]) => /\/renomear$/.test(u));
  assert.deepEqual(r.map(([u, c]) => [u, c.titulo]), [['/api/conversas/c1/renomear', 'Legenda do AD07']]);
  t.focus(); t.value = 'outro'; tecla(w, t, 'Escape');
  await espera(30);
  assert.equal(t.value, 'Legenda do AD07');
  assert.equal(est.posts.filter(([u]) => /\/renomear$/.test(u)).length, 1);
});

test('aoAbrir: "nova" começa vazia; padrão reabre a última DESTA janela', { skip: PULAR }, async () => {
  const a = montar({ op: { aoAbrir: 'nova', compacto: true } });
  await espera(100);
  assert.equal(a.el.querySelector('.cv-titulo').value, 'Nova conversa');
  assert.equal(a.est.gets.includes('/api/conversa'), false);
  assert.equal(a.cv.conversa, null);
  const b = montar({ lembrada: 'c2', janela: 'painel', op: { compacto: true } });
  await espera(100);
  assert.equal(b.cv.conversa, 'c2');
  assert.equal(b.el.querySelector('.cv-titulo').value, 'Legenda karaokê');
  assert.equal(b.est.gets.includes('/api/conversa'), false);
});

test('chip da skill no rodapé: nome amigável, nunca JSON cru', { skip: PULAR }, async () => {
  const { w, el } = montar({ mensagens: [{ role: 'assistant', content: 'ok', passos: [
    { tipo: 'ferramenta', nome: 'Skill', entrada: '{"skill": "editor-automatico-de-broll", "args": "x"}', resumo: '{"skill": "editor-autom…', estado: 'ok' }] }] });
  await espera(120);
  const chip = el.querySelector('.cv-rod-skill');
  assert.equal(chip.textContent.trim(), 'Editor automático de b-roll');
  assert.equal(chip.title, 'Skill em uso: editor-automatico-de-broll');
  assert.equal(/[{}"]/.test(el.querySelector('.cv-rodape').textContent), false);
  assert.deepEqual(lixo(w, el), []);
});
