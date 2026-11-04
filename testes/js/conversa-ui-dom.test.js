/* Conversa no DOM: teclado do menu "/", fila visível, Esc e ↑.
   Usa o jsdom que já existe na banca do Tools PRO (nenhuma dependência nova
   no app). Sem jsdom na máquina, o teste é pulado — os testes puros de
   conversa-ui.test.js continuam valendo.

   Armadilhas da banca respeitadas (memória banca-jsdom-painel-toolspro):
   - nada de disparar DOMContentLoaded na mão;
   - visibilidade pelo atributo `hidden`, não por getComputedStyle. */
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

const CODIGO = fs.readFileSync(path.join(__dirname, '..', '..', 'web', 'conversa-ui.js'), 'utf8');
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

// app falso: responde às rotas que a Conversa usa e deixa a tarefa "rodando"
// até o teste mandar terminar
function montar(opcoes = {}) {
  const dom = new JSDOM('<!doctype html><html><body><div id="c" style="height:600px"></div></body></html>',
    { runScripts: 'outside-only', pretendToBeVisual: true, url: 'http://127.0.0.1:9/' });
  const w = dom.window;
  const estado = { tarefa: 'rodando', cancelou: 0, posts: [] };
  w.fetch = async (url, op) => {
    const u = String(url).replace(/^http:\/\/[^/]+/, '');
    const metodo = (op && op.method) || 'GET';
    let d = { ok: true };
    if (u === '/api/conversa' && metodo === 'GET') d = { conversa: 'c1', mensagens: opcoes.mensagens || [] };
    else if (u.startsWith('/api/conversas/c1/aprovacao')) d = { cartao: null };
    else if (u.startsWith('/api/conversas/c1')) d = { conversa: 'c1', mensagens: opcoes.mensagens || [], meta: { titulo: 'x', projeto_nome: 'AD07' } };
    else if (u === '/api/ia') d = { escolhido: 'claude', provedores: [{ id: 'claude', nome: 'Claude', pronto: true }, { id: 'chatgpt', nome: 'ChatGPT', pronto: true }] };
    else if (u === '/api/conversa' && metodo === 'POST') { estado.posts.push(JSON.parse(op.body)); d = { tarefa: 't' + estado.posts.length }; }
    else if (u.startsWith('/api/tarefas/') && u.includes('/cancelar')) { estado.cancelou += 1; estado.tarefa = 'cancelado'; d = { ok: true }; }
    else if (u.startsWith('/api/tarefas/')) {
      d = { estado: estado.tarefa, cancelavel: true, seq: 1, total: 1,
            novos: [[0, { tipo: 'ferramenta', nome: 'Read', entrada: { file_path: '/p/decupagem.md' }, estado: 'rodando', inicio: Date.now() / 1000 }]],
            resultado: { conversa: 'c1' } };
    }
    return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(d)) };
  };
  w.eval(CODIGO);
  const el = w.document.getElementById('c');
  const cv = w.montarConversa(el, { api: 'http://127.0.0.1:9', token: 'tk' });
  // o relógio do componente e a pesquisa da tarefa seguram o node aberto: desmonta no fim
  test.after(() => { try { cv.desmontar(); } catch (_) { /* já saiu */ } estado.tarefa = 'pronto'; setTimeout(() => w.close(), 1500); });
  return { w, el, cv, estado, entrada: el.querySelector('.cv-entrada') };
}

function digitar(w, entrada, texto) {
  entrada.value = texto;
  entrada.setSelectionRange(texto.length, texto.length);
  entrada.dispatchEvent(new w.Event('input', { bubbles: true }));
}
const tecla = (w, alvo, key, extra) => alvo.dispatchEvent(new w.KeyboardEvent('keydown', Object.assign({ key, bubbles: true, cancelable: true }, extra || {})));

test('menu "/" abre, navega pelo teclado e roda /custo', { skip: !JSDOM && 'jsdom não encontrado' }, async () => {
  const { w, el, entrada } = montar({ mensagens: [{ role: 'user', content: 'oi' },
    { role: 'assistant', content: 'olá', passos: [], uso: { duracao_ms: 4000, tokens_entrada: 900, tokens_saida: 50, custo_usd: 0.1 } }] });
  await espera(60);
  digitar(w, entrada, '/');
  const menu = el.querySelector('.cv-menu');
  assert.equal(menu.hidden, false);
  assert.equal(entrada.getAttribute('aria-expanded'), 'true');
  const ops = () => [...menu.querySelectorAll('[role="option"]')];
  assert.deepEqual(ops().map((o) => o.querySelector('.cv-menu-nome').textContent), ['/nova', '/limpar', '/skills', '/custo', '/parar']);
  assert.equal(ops()[0].getAttribute('aria-selected'), 'true');
  tecla(w, entrada, 'ArrowDown'); tecla(w, entrada, 'ArrowDown'); tecla(w, entrada, 'ArrowDown');
  assert.equal(ops()[3].getAttribute('aria-selected'), 'true');
  assert.equal(entrada.getAttribute('aria-activedescendant'), ops()[3].id);
  tecla(w, entrada, 'Enter');
  assert.equal(menu.hidden, true);
  assert.equal(entrada.value, '');
  const resumo = el.querySelector('.cv-resumo');
  assert.ok(resumo, 'o /custo não desenhou o resumo');
  assert.match(resumo.textContent, /Respostas\s*1/);
  assert.match(resumo.textContent, /US\$ 0,10/);
  // Esc fecha o menu sem apagar o texto
  digitar(w, entrada, '/li');
  assert.equal(menu.hidden, false);
  tecla(w, entrada, 'Escape');
  assert.equal(menu.hidden, true);
  assert.equal(entrada.value, '/li');
});

test('enquanto a IA trabalha: fila visível, Esc para e ↑ traz a última', { skip: !JSDOM && 'jsdom não encontrado' }, async () => {
  const { w, el, entrada, estado } = montar();
  await espera(60);
  digitar(w, entrada, 'analise a timeline');
  tecla(w, entrada, 'Enter');
  await espera(900);
  assert.equal(estado.posts.length, 1);
  assert.equal(el.querySelector('.cv-vivo').hidden, false);
  assert.match(el.querySelector('.cv-vivo').textContent, /Leu decupagem\.md/);
  // segunda mensagem vai para a fila, à vista
  digitar(w, entrada, 'depois marque os b-rolls');
  tecla(w, entrada, 'Enter');
  await espera(20);
  const fila = el.querySelector('.cv-fila');
  assert.equal(fila.hidden, false);
  assert.match(fila.textContent, /depois marque os b-rolls/);
  assert.equal(estado.posts.length, 1, 'mandou a segunda antes da primeira acabar');
  // Esc interrompe
  tecla(w, entrada, 'Escape');
  await espera(900);
  assert.equal(estado.cancelou, 1);
  assert.match(el.querySelector('.cv-notas').textContent, /Cancelado/);
  // cancelado pausa a fila (não manda a próxima sozinha)
  assert.equal(estado.posts.length, 1);
  assert.match(fila.textContent, /pausada/);
  // ↑ com o campo vazio traz a última mensagem enviada
  entrada.value = '';
  tecla(w, entrada, 'ArrowUp');
  assert.equal(entrada.value, 'depois marque os b-rolls');
  tecla(w, entrada, 'ArrowUp');
  assert.equal(entrada.value, 'analise a timeline');
});

test('rodapé mostra IA, projeto; nada de undefined/NaN no texto', { skip: !JSDOM && 'jsdom não encontrado' }, async () => {
  const { w, el } = montar({ mensagens: [{ role: 'assistant', content: 'ok', passos: [{ tipo: 'ferramenta', nome: 'Skill', entrada: { skill: 'cortar-aula' }, estado: 'ok' }] }] });
  await espera(80);
  const rod = el.querySelector('.cv-rodape').textContent;
  assert.match(rod, /Claude/); assert.match(rod, /ChatGPT/); assert.match(rod, /AD07/); assert.match(rod, /Cortar aula/);
  assert.equal(el.querySelector('.cv-rod-skill').title, 'Skill em uso: cortar-aula');
  const ruins = [];
  const tw = w.document.createTreeWalker(el, 4);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) if (/\b(undefined|NaN|Infinity)\b/.test(n.nodeValue)) ruins.push(n.nodeValue);
  assert.deepEqual(ruins, []);
});
