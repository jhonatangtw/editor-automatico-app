/* Testes do componente da Conversa (web/conversa-ui.js) — as peças puras.
   Rodar: node --test testes/js/   (o test_conversa_ui.py chama isto)
   Sem dependência: só node:test e node:assert. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const CV = require(path.join(__dirname, '..', '..', 'web', 'conversa-ui.js'));
const I = CV._interno;

// Varre o TEXTO do HTML (não as tags) atrás de undefined/NaN/Infinity — o
// defeito que já foi ao ar no painel porque a banca só pegava exceção.
function lixoNoTexto(html) {
  const texto = html.replace(/<[^>]+>/g, ' ');
  return (texto.match(/\b(undefined|NaN|Infinity|null)\b/g) || []);
}

test('a varredura de lixo pega o que tem que pegar', () => {
  assert.deepEqual(lixoNoTexto('<b>NaN</b>VSLs'), ['NaN']);
  assert.deepEqual(lixoNoTexto('<span title="undefined">ok</span>'), []);   // atributo não é texto
  assert.deepEqual(lixoNoTexto('<i>nada aqui</i>'), []);
});

// ------------------------------------------------------------------ markdown
test('markdown escapa HTML do modelo', () => {
  const h = I.md('<img src=x onerror=alert(1)> **negrito** <script>x</script>');
  assert.ok(!h.includes('<img'), h);
  assert.ok(!h.includes('<script'), h);
  assert.ok(h.includes('&lt;img src=x onerror=alert(1)&gt;'));
  assert.ok(h.includes('<b>negrito</b>'));
});

test('link só sai como <a> se for http(s)', () => {
  assert.ok(I.md('[site](https://exemplo.com)').includes('<a href="https://exemplo.com" target="_blank" rel="noopener noreferrer">site</a>'));
  const ruim = I.md('[clique](javascript:alert(1))');
  assert.ok(!ruim.includes('<a'), ruim);
  const aspas = I.md('[x](https://a.com/"onmouseover="alert(1))');
  assert.ok(!/href="[^"]*"onmouseover/.test(aspas), aspas);
});

test('bloco de código com botão Copiar e conteúdo escapado', () => {
  const h = I.md('Antes\n```bash\nffmpeg -i "a.mp4" <b>\n```\nDepois');
  assert.ok(h.includes('class="cv-codigo"'));
  assert.ok(h.includes('data-copiar'));
  assert.ok(h.includes('>bash<'));
  assert.ok(h.includes('ffmpeg -i &quot;a.mp4&quot; &lt;b&gt;'));
  assert.ok(h.indexOf('Antes') < h.indexOf('cv-codigo') && h.indexOf('cv-codigo') < h.indexOf('Depois'));
});

test('nada é formatado dentro de código em linha', () => {
  assert.equal(I.inline('use `**x**` aqui'), 'use <code>**x**</code> aqui');
});

test('cerca de código ainda aberta (texto chegando) não quebra', () => {
  const h = I.md('Olha:\n```js\nconst a = 1;');
  assert.ok(h.includes('const a = 1;'));
  assert.ok(h.includes('cv-codigo'));
});

test('listas, títulos e tabela', () => {
  const h = I.md('## Plano\n- um\n- dois\n\n1. a\n2. b\n\n| A | B |\n|---|---|\n| 1 | 2 |');
  assert.ok(h.includes('<h4>Plano</h4>'));
  assert.ok(h.includes('<ul><li>um</li><li>dois</li></ul>'));
  assert.ok(h.includes('<ol><li>a</li><li>b</li></ol>'));
  assert.ok(h.includes('<th>A</th>') && h.includes('<td>2</td>'));
});

// ------------------------------------------------------------------ rótulos
test('rótulos amigáveis em português', () => {
  const r = (nome, entrada, extra) => I.rotuloAcao(Object.assign({ tipo: 'ferramenta', nome, entrada }, extra || {})).texto;
  assert.equal(r('Read', { file_path: '/x/AD07/decupagem.md' }), 'Leu decupagem.md');
  assert.equal(r('Read', { file_path: '/x/frame.png' }), 'Viu frame.png');
  assert.equal(r('Bash', { command: 'cd "/a b" && ffmpeg -i x.mp4 y.mp4' }), 'Rodou ffmpeg');
  assert.equal(r('Bash', { command: 'higgsfield generate create --model nano_banana_pro --prompt x' }), 'Gerou imagem no Higgsfield');
  assert.equal(r('Bash', { command: 'FOO=1 higgsfield generate create --model kling3_0_turbo' }), 'Gerou vídeo no Higgsfield');
  assert.equal(r('Bash', { command: '/opt/homebrew/bin/whisper a.wav' }), 'Transcreveu com Whisper');
  assert.equal(r('Bash', { command: 'higgsfield generate cost --model nano_banana_pro' }), 'Orçou no Higgsfield');
  assert.equal(r('mcp__toolspro-pr__pr_timeline_colocar', { clipes: new Array(12).fill({}) }), 'Colocou 12 clipes na timeline (Tools PRO)');
  assert.equal(r('mcp__editor__adobe_estado', {}), 'Conferiu o Adobe');
  assert.equal(r('mcp__editor__etapa_rodar', { etapa: 'imagens' }), 'Rodou a etapa imagens');
  assert.equal(r('Skill', { skill: 'cortar-aula' }), 'Usou a skill Cortar aula');
  assert.equal(r('TodoWrite', { todos: [] }), 'Atualizou as tarefas');
  assert.equal(r('WebFetch', { url: 'https://docs.exemplo.com/a' }), 'Abriu docs.exemplo.com');
  // Codex: o servidor vem separado do nome
  assert.equal(r('pr_timeline_listar', {}, { servidor: 'toolspro-pr' }), 'Leu a timeline (Tools PRO)');
  assert.equal(r('terminal', undefined, { resumo: 'ffprobe -v error x.mp4' }), 'Mediu com ffprobe');
  // passo antigo, sem entrada: não escreve "undefined"
  const antigo = I.rotuloAcao({ tipo: 'ferramenta', nome: 'Read', resumo: '/a/b/copy.txt' });
  assert.equal(antigo.texto, 'Leu copy.txt');
});

// ------------------------------------------------------------------ menu "/" e "@"
test('gatilho do menu', () => {
  assert.deepEqual(I.lerGatilho('/', 1), { tipo: 'comando', consulta: '', inicio: 0 });
  assert.deepEqual(I.lerGatilho('/cu', 3), { tipo: 'comando', consulta: 'cu', inicio: 0 });
  assert.equal(I.lerGatilho('olá /cu', 7), null);                    // só no começo
  assert.deepEqual(I.lerGatilho('/skills cor', 11), { tipo: 'skills', consulta: 'cor', inicio: 0 });
  assert.deepEqual(I.lerGatilho('leia @deco', 10), { tipo: 'arquivo', consulta: 'deco', inicio: 5 });
  assert.equal(I.lerGatilho('email@dominio', 13), null);              // @ no meio da palavra não abre
  assert.equal(I.lerGatilho('leia @deco e', 12), null);               // passou do espaço
});

test('filtro de comandos', () => {
  assert.deepEqual(I.filtrarComandos('').map((c) => c.nome), ['/nova', '/limpar', '/skills', '/custo', '/parar']);
  assert.deepEqual(I.filtrarComandos('c').map((c) => c.nome)[0], '/custo');
  assert.deepEqual(I.filtrarComandos('memoria').map((c) => c.nome), ['/limpar']);   // sem acento casa a descrição
  assert.deepEqual(I.filtrarComandos('xyz'), []);
});

test('filtro de skills e inserção', () => {
  const sk = [{ nome: 'cortar-aula', descricao: 'Corta silêncios' }, { nome: 'pixar3d', descricao: 'personagem 3D' },
              { nome: 'conferir-ads-por-frame', descricao: 'QA de criativos' }];
  assert.deepEqual(I.filtrarSkills(sk, 'silencio').map((s) => s.nome), ['cortar-aula']);
  assert.deepEqual(I.filtrarSkills(sk, 'co').map((s) => s.nome).slice(0, 2), ['cortar-aula', 'conferir-ads-por-frame']);
  assert.equal(I.filtrarSkills(sk, '').length, 3);
});

test('escolher arquivo troca o @consulta pelo caminho', () => {
  const g = I.lerGatilho('leia @deco agora', 10);
  assert.deepEqual(I.aplicarArquivo('leia @deco agora', g, '/p/decupagem.md', 10),
                   { texto: 'leia /p/decupagem.md  agora', cursor: 21 });
  const g2 = I.lerGatilho('@a', 2);
  assert.equal(I.aplicarArquivo('@a', g2, '/p/com espaço.md', 2).texto, '"/p/com espaço.md" ');
});

// ------------------------------------------------------------------ fila
test('fila: entra, sai em ordem, remove e pausa', () => {
  const f = new I.Fila();
  f.por('um'); f.por('dois', ['/a.png']); f.por('três');
  assert.equal(f.tamanho, 3);
  f.remover(1);
  assert.deepEqual(f.tirar(), { texto: 'um', anexos: [] });
  f.pausada = true;
  assert.equal(f.tirar(), null);
  f.pausada = false;
  assert.deepEqual(f.tirar(), { texto: 'três', anexos: [] });
  assert.equal(f.tirar(), null);
});

test('mensagem escrita durante a resposta entra na fila e sai sozinha depois', async () => {
  const chamadas = [];
  let rodadas = 0;
  global.fetch = async (url, op) => {
    const metodo = (op && op.method) || 'GET';
    chamadas.push(metodo + ' ' + url.replace('http://h', ''));
    let corpo;
    if (metodo === 'POST' && url.endsWith('/api/conversa')) corpo = { tarefa: 't' + (++rodadas) };
    else if (url.includes('/api/tarefas/')) corpo = { estado: 'pronto', seq: 1, total: 0, novos: [], resultado: { conversa: 'c1' } };
    else corpo = { ok: true };
    return { ok: true, status: 200, json: async () => corpo };
  };
  const s = I.sessao('c-fila');
  s.cfg = { api: 'http://h', token: 'tk' };
  const fins = [];
  s.ouvintes.add((tipo, d) => { if (tipo === 'fim') fins.push(d.texto); });
  const primeira = I.enviarNaSessao(s, 'primeira', []);
  await I.enviarNaSessao(s, 'segunda', []);          // a primeira ainda está viva
  assert.equal(s.fila.tamanho, 1);
  await primeira;
  for (let i = 0; i < 60 && fins.length < 2; i++) await new Promise((r) => setTimeout(r, 50));
  assert.deepEqual(fins, ['primeira', 'segunda']);
  assert.equal(s.fila.tamanho, 0);
  const posts = chamadas.filter((c) => c.startsWith('POST'));
  assert.equal(posts.length, 2);
  delete global.fetch;
});

test('erro na resposta pausa a fila em vez de mandar a próxima', async () => {
  global.fetch = async (url, op) => {
    const metodo = (op && op.method) || 'GET';
    const corpo = metodo === 'POST' ? { tarefa: 'tx' } : { estado: 'erro', erro: 'limite de uso', seq: 0, total: 0, novos: [] };
    return { ok: true, status: 200, json: async () => corpo };
  };
  const s = I.sessao('c-erro');
  s.cfg = { api: '', token: '' };
  const p = I.enviarNaSessao(s, 'a', []);
  await I.enviarNaSessao(s, 'b', []);
  await p;
  assert.equal(s.fila.pausada, true);
  assert.equal(s.fila.tamanho, 1);
  delete global.fetch;
});

// ------------------------------------------------------------------ estados derivados
test('painel de tarefas: último TodoWrite; some quando tudo feito', () => {
  const t = (estados) => ({ tipo: 'ferramenta', nome: 'TodoWrite', tarefas: estados.map((e, i) => ({ texto: 't' + i, estado: e })) });
  assert.equal(I.tarefasAtuais([t(['feito', 'andamento'])], []).length, 2);
  assert.equal(I.tarefasAtuais([t(['andamento']), t(['feito', 'feito'])], []), null);
  // sem resposta viva: vem da última resposta guardada
  const msgs = [{ role: 'assistant', passos: [t(['andamento', 'pendente'])] }, { role: 'user', content: 'oi' }];
  assert.equal(I.tarefasAtuais(null, msgs).length, 2);
  assert.equal(I.tarefasAtuais(null, []), null);
});

test('/custo soma o que o stream-json informou', () => {
  const msgs = [
    { role: 'user', content: 'a' },
    { role: 'assistant', passos: [{ tipo: 'ferramenta', dur: 2 }, { tipo: 'texto', texto: 'x' }],
      uso: { duracao_ms: 8000, tokens_entrada: 1000, tokens_saida: 200, custo_usd: 0.25 } },
    { role: 'assistant', passos: [{ tipo: 'ferramenta' }], provedor: 'chatgpt' },
  ];
  const c = I.resumoCusto(msgs, [{ tipo: 'ferramenta', dur: 1 }]);
  assert.deepEqual(c, { respostas: 2, acoes: 3, tempo_ms: 8000, tokens_entrada: 1000, tokens_saida: 200,
                        custo_usd: 0.25, com_uso: 1 });
  const sem = I.resumoCusto([{ role: 'assistant', passos: [{ tipo: 'ferramenta', dur: 3 }] }], null);
  assert.equal(sem.com_uso, 0);
  assert.equal(sem.tempo_ms, 3000);
});

test('skill em uso vem da última chamada de Skill', () => {
  const msgs = [{ role: 'assistant', passos: [{ tipo: 'ferramenta', nome: 'Skill', entrada: { skill: 'pixar3d' } }] }];
  assert.equal(I.skillEmUso(msgs, null), 'pixar3d');
  assert.equal(I.skillEmUso(msgs, [{ tipo: 'ferramenta', nome: 'Skill', entrada: { skill: 'cortar-aula' } }]), 'cortar-aula');
  assert.equal(I.skillEmUso([], null), null);
});

// ------------------------------------------------------------------ histórico antigo abre na tela nova
const API = { arquivoUrl: (c) => '/api/arquivo?p=' + encodeURIComponent(c) };
const UI = () => ({ abertos: new Set(), mais: new Set(), grupos: new Set() });

test('conversa antiga (passos sem texto, anexos no content) abre igual', () => {
  const user = { role: 'user', content: 'veja isto\n\nArquivos anexados:\n- /a/ref.png\n- /a/copy.txt' };
  assert.deepEqual(I.partesUsuario(user), { texto: 'veja isto', anexos: ['/a/ref.png', '/a/copy.txt'] });
  const hu = I.htmlMensagem(user, 0, UI(), API);
  assert.ok(hu.includes('<img') && hu.includes('copy.txt'));
  const velha = { role: 'assistant', content: 'Pronto **feito**', provedor: 'claude',
                  passos: [{ tipo: 'ferramenta', nome: 'mcp__editor__adobe_estado', resumo: '', estado: 'ok', saida: 'Premiere aberto' },
                           { tipo: 'pensando' }] };
  const seq = I.sequenciaDa(velha);
  assert.equal(seq[seq.length - 1].tipo, 'texto');
  const h = I.htmlMensagem(velha, 1, UI(), API);
  assert.ok(h.includes('Conferiu o Adobe'));
  assert.ok(h.includes('<b>feito</b>'));
  assert.ok(h.includes('Pensou'));
  assert.deepEqual(lixoNoTexto(h), []);
  // mensagem "ferramenta" do caminho por chave de API
  const hf = I.htmlMensagem({ role: 'ferramenta', nome: 'rodar_etapa', entrada: { etapa: 'copy' }, saida: { recusado: true, porque: 'trava' } }, 2, UI(), API);
  assert.ok(hf.includes('Rodou a etapa copy') && hf.includes('est-erro'));
  assert.deepEqual(lixoNoTexto(hf), []);
});

test('mensagem nova intercala texto e ações, sem lixo na tela', () => {
  const m = { role: 'assistant', content: 'a\n\nb', provedor: 'claude', passos: [
    { tipo: 'pensando', estado: 'ok', dur: 3.2, texto: '' },
    { tipo: 'texto', texto: 'a' },
    { tipo: 'ferramenta', nome: 'Read', entrada: { file_path: '/x/y.md' }, estado: 'ok', dur: 0.4, resultado: 'conteúdo' },
    { tipo: 'ferramenta', nome: 'Bash', entrada: { command: 'ls' }, estado: 'erro', dur: 1 },
    { tipo: 'texto', texto: 'b' }] };
  const h = I.htmlMensagem(m, 0, UI(), API);
  assert.ok(h.indexOf('Pensou por 3 s') < h.indexOf('>a<'));
  assert.ok(h.indexOf('>a<') < h.indexOf('Leu y.md') && h.indexOf('Leu y.md') < h.indexOf('>b<'));
  assert.ok(h.includes('est-erro'));
  assert.ok(h.includes('0,4 s'));
  assert.deepEqual(lixoNoTexto(h), []);
  // aberto: mostra entrada e resultado; texto longo vem truncado com "ver mais"
  const ui = UI(); ui.abertos.add('m0:2');
  m.passos[2].resultado = 'x'.repeat(5000);
  const ha = I.htmlMensagem(m, 0, ui, API);
  assert.ok(ha.includes('Entrada') && ha.includes('Resultado'));
  assert.ok(ha.includes('ver mais'));
  assert.ok(!ha.includes('x'.repeat(1000)));
});

test('muitas ações seguidas ficam recolhidas', () => {
  const passos = Array.from({ length: 40 }, (_, i) => ({ tipo: 'ferramenta', nome: 'Read', entrada: { file_path: '/f' + i }, estado: 'ok' }));
  const h = I.htmlMensagem({ role: 'assistant', content: 'fim', passos }, 0, UI(), API);
  assert.ok(h.includes('mais 37 ações'));
  assert.equal((h.match(/class="cv-acao /g) || []).length, 3);
});

// ------------------------------------------------------------------ 0.22.1
test('nome da skill: nunca JSON cru, amigável na tela e técnico no tooltip', () => {
  const t = (p) => I.tecnicoDaSkill(Object.assign({ tipo: 'ferramenta', nome: 'Skill' }, p));
  assert.equal(t({ entrada: { skill: 'editor-automatico-de-broll' } }), 'editor-automatico-de-broll');
  assert.equal(t({ entrada: '{"skill": "editor-automatico-de-broll", "args": "x"}' }), 'editor-automatico-de-broll');
  assert.equal(t({ entrada: {}, resumo: '{"skill": "editor-autom…' }), 'editor-autom');
  assert.equal(t({ entrada: { skill: '{"skill": "pixar3d"' } }), 'pixar3d');
  assert.equal(t({ entrada: { command: '/cortar-aula' } }), 'cortar-aula');
  assert.equal(t({ entrada: {}, resumo: '' }), null);
  assert.equal(I.nomeSkill('editor-automatico-de-broll'), 'Editor automático de b-roll');
  assert.equal(I.nomeSkill('editor-autom'), 'Editor automático de b-roll');          // cortado no meio
  assert.equal(I.nomeSkill('editor-broll:marcar-vsl'), 'Marcar VSL');
  assert.equal(I.nomeSkill('analise-de-video-ugc'), 'Análise de vídeo UGC');
  const msgs = [{ role: 'assistant', passos: [{ tipo: 'ferramenta', nome: 'Skill', entrada: {}, resumo: '{"skill": "editor-automatico-de-broll", "a…' }] }];
  assert.equal(I.skillEmUso(msgs, null), 'editor-automatico-de-broll');
  assert.equal(I.rotuloAcao(msgs[0].passos[0]).texto, 'Usou a skill Editor automático de b-roll');
});

test('data relativa do histórico', () => {
  const agora = new Date(2026, 9, 6, 18, 0).getTime();
  const s = (d) => d.getTime() / 1000;
  assert.equal(I.quandoRelativo(s(new Date(2026, 9, 6, 17, 40)), agora), 'hoje 17:40');
  assert.equal(I.quandoRelativo(s(new Date(2026, 9, 5, 9, 5)), agora), 'ontem 09:05');
  assert.equal(I.quandoRelativo(s(new Date(2026, 9, 2, 10, 0)), agora), 'sex 10:00');
  assert.equal(I.quandoRelativo(s(new Date(2026, 8, 12, 10, 0)), agora), '12/09');
  assert.equal(I.quandoRelativo(s(new Date(2025, 8, 12, 10, 0)), agora), '12/09/25');
  assert.equal(I.quandoRelativo(0, agora), '');
});

const API_FALSA = { raiz: '', arquivoUrl: (c) => '/api/arquivo?p=' + encodeURIComponent(c), quadroUrl: (c, w) => '/api/midia/quadro?p=' + encodeURIComponent(c) + '&w=' + w };

test('mídias: grade, vídeo, áudio, remota, limite e sem repetir', () => {
  const ui = I.uiMidia({ api: API_FALSA });
  const imgs = Array.from({ length: 15 }, (_, i) => ({ tipo: 'imagem', caminho: `/p/media/imagens/i${i}.png` }));
  const h = I.htmlMidias(imgs.concat([{ tipo: 'video', caminho: '/p/v.mp4' }]), 'm1:2:m', ui);
  assert.equal((h.match(/class="cv-mid-img"/g) || []).length, 12);           // limite por mensagem
  assert.match(h, /ver todas \(16\)/);
  assert.equal(ui.lb.get('m1:2:m').length, 15);                              // o lightbox navega TODAS
  assert.deepEqual(lixoNoTexto(h), []);
  ui.midiasTodas.add('m1:2:m');
  const todas = I.htmlMidias(imgs.concat([{ tipo: 'video', caminho: '/p/v.mp4' }]), 'm1:2:m', ui);
  assert.equal((todas.match(/class="cv-mid-img"/g) || []).length, 15);
  assert.match(todas, /<video controls preload="metadata" playsinline poster="\/api\/midia\/quadro[^"]*" data-src="\/api\/arquivo/);
  assert.ok(!/<video[^>]* src=/.test(todas), 'vídeo não pode carregar antes de aparecer');
  const a = I.htmlMidias([{ tipo: 'audio', caminho: '/p/voz.mp3' }], 'k', ui);
  assert.match(a, /data-audio-play/); assert.match(a, /<canvas/); assert.match(a, /<audio preload="none" data-src=/);
  const r = I.htmlMidias([{ tipo: 'video', url: 'https://cdn.exemplo.invalid/x.mp4' }], 'r', ui);
  assert.match(r, /baixando…/); assert.match(r, /data-mid-url="https:\/\/cdn\.exemplo\.invalid\/x\.mp4"/);
  // a entrega que já desceu vira arquivo local, e não repete se aparecer de novo
  ui.baixas.set('https://cdn.exemplo.invalid/x.mp4', { estado: 'ok', caminho: '/p/media/videos/x.mp4', tipo: 'video' });
  const seq = I.dedupeMidias([{ tipo: 'ferramenta', midias: [{ tipo: 'video', url: 'https://cdn.exemplo.invalid/x.mp4' }] },
    { tipo: 'texto', texto: 'x', midias: [{ tipo: 'video', caminho: '/p/media/videos/x.mp4' }, { tipo: 'imagem', caminho: '/p/a.png' }] }], ui);
  assert.equal(seq[0].midias.length, 1);
  assert.deepEqual(seq[1].midias.map((m) => m.caminho), ['/p/a.png']);
  assert.equal(I.proporcao(1080, 1920), '9:16'); assert.equal(I.proporcao(1920, 1080), '16:9'); assert.equal(I.proporcao(1080, 1080), '1:1');
  assert.match(I.mensagemTimeline('/p/a b.mp4'), /"\/p\/a b\.mp4"/);
});
