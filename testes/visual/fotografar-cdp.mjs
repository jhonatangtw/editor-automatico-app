// Fotografa telas da banca visual pelo protocolo do Chrome (CDP), sem tocar
// na tela do Mac: Chrome headless com perfil próprio e porta própria, e a foto
// é SÓ da página (Page.captureScreenshot). `--headless --screenshot` puro às
// vezes não sai sozinho; aqui quem decide a hora da foto é o script.
//
// Precisa de Node 22+ (WebSocket nativo). Uso:
//   node testes/visual/fotografar-cdp.mjs <saida> <nome> <largura> <altura> <query> [espera-ms] [nome largura altura query espera]...
// O servidor estático (raiz do repo) sobe numa porta livre e é derrubado no fim.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync, statSync, createReadStream, existsSync } from 'node:fs';
import { createServer } from 'node:net';
import { createServer as criarHttp } from 'node:http';
import { basename, extname, normalize, sep } from 'node:path';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const portaLivre = () => new Promise((ok) => { const s = createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => ok(p)); }); });

const [saida, ...resto] = process.argv.slice(2);
const fotos = [];
for (let i = 0; i + 4 < resto.length + 1; ) {
  const [nome, larg, alt, query] = resto.slice(i, i + 4);
  let espera = 2500; i += 4;
  if (resto[i] && /^\d+$/.test(resto[i])) { espera = +resto[i]; i += 1; }
  if (!nome) break;
  // nome com "pagina:" na frente usa outra página da banca (ex.: compacto:minha-foto)
  const [pagina, nomeFoto] = nome.includes(':') ? nome.split(':') : ['tela', nome];
  fotos.push({ nome: nomeFoto, pagina, larg: +larg, alt: +alt, query, espera });
}
mkdirSync(saida, { recursive: true });

// Servidor estático da banca (era o http.server do Python). Além dos arquivos
// do repositório, responde /api/arquivo e /api/midia/quadro com a mídia
// SINTÉTICA de testes/visual/amostras (gerar-amostras.sh), pelo nome do
// arquivo — e com Range, como o app, para o <video> tocar de verdade.
const TIPOS = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm',
  '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };
function servir(res, req, arq) {
  if (!arq || !existsSync(arq) || !statSync(arq).isFile()) { res.writeHead(404); res.end(); return; }
  const tam = statSync(arq).size;
  const tipo = TIPOS[extname(arq).toLowerCase()] || 'application/octet-stream';
  const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
  if (m) {
    const ini = m[1] ? +m[1] : Math.max(0, tam - +m[2]);
    const fim = m[1] && m[2] ? Math.min(+m[2], tam - 1) : tam - 1;
    if (ini >= tam || fim < ini) { res.writeHead(416, { 'Content-Range': `bytes */${tam}` }); res.end(); return; }
    res.writeHead(206, { 'Content-Type': tipo, 'Content-Length': fim - ini + 1, 'Content-Range': `bytes ${ini}-${fim}/${tam}`, 'Accept-Ranges': 'bytes' });
    createReadStream(arq, { start: ini, end: fim }).pipe(res);
    return;
  }
  res.writeHead(200, { 'Content-Type': tipo, 'Content-Length': tam, 'Accept-Ranges': 'bytes' });
  createReadStream(arq).pipe(res);
}
const portaHttp = await portaLivre();
const http = criarHttp((req, res) => {
  const u = new URL(req.url, 'http://x');
  if (u.pathname === '/api/arquivo' || u.pathname === '/api/midia/quadro') {
    const arq = join(RAIZ, 'testes', 'visual', 'amostras', basename(u.searchParams.get('p') || ''));
    // quadro de vídeo = a capa jpg que gerar-amostras.sh tirou (o app faz isso com ffmpeg)
    return servir(res, req, u.pathname === '/api/midia/quadro' && /\.(mp4|mov|webm|m4v)$/i.test(arq) ? arq + '.capa.jpg' : arq);
  }
  const alvo = normalize(join(RAIZ, decodeURIComponent(u.pathname)));
  if (!alvo.startsWith(RAIZ + sep)) { res.writeHead(403); res.end(); return; }
  servir(res, req, alvo);
}).listen(portaHttp, '127.0.0.1');
http.kill = () => http.close();
const portaCdp = await portaLivre();
const perfil = mkdtempSync(join(tmpdir(), 'cdp-'));
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--user-data-dir=${perfil}`,
  '--no-first-run', '--no-default-browser-check', `--remote-debugging-port=${portaCdp}`, '--force-device-scale-factor=2', 'about:blank'],
  { stdio: 'ignore' });

function fim(cod) { try { chrome.kill(); } catch (_) {} try { http.kill(); } catch (_) {} setTimeout(() => { try { rmSync(perfil, { recursive: true, force: true }); } catch (_) {} process.exit(cod); }, 400); }
setTimeout(() => { console.error('prazo esgotado'); fim(2); }, 120000);

let alvo = null;
for (let i = 0; i < 60 && !alvo; i++) {
  await dormir(250);
  try { alvo = (await (await fetch(`http://127.0.0.1:${portaCdp}/json/list`)).json()).find((t) => t.type === 'page'); } catch (_) { /* ainda subindo */ }
}
if (!alvo) { console.error('o Chrome não abriu a porta de depuração'); fim(1); }

const ws = new WebSocket(alvo.webSocketDebuggerUrl);
await new Promise((ok, erro) => { ws.onopen = ok; ws.onerror = erro; });
let seq = 0; const pend = new Map();
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); return; }
  // erro de JS na página sai no terminal: foto bonita de tela quebrada não engana
  if (d.method === 'Runtime.exceptionThrown') console.error('ERRO NA PÁGINA:', d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
  if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') console.error('console.error:', d.params.args.map((a) => a.value ?? a.description).join(' '));
};
const cdp = (method, params = {}) => new Promise((ok) => { const id = ++seq; pend.set(id, ok); ws.send(JSON.stringify({ id, method, params })); });

await cdp('Page.enable');
await cdp('Runtime.enable');
for (const f of fotos) {
  await cdp('Emulation.setDeviceMetricsOverride', { width: f.larg, height: f.alt, deviceScaleFactor: 2, mobile: false });
  await cdp('Page.navigate', { url: `http://127.0.0.1:${portaHttp}/testes/visual/${f.pagina || "tela"}.html?${f.query}` });
  await dormir(f.espera);
  if (process.env.AVALIAR) {   // depuração: AVALIAR='expressão JS' imprime o valor na hora da foto
    const v = await cdp('Runtime.evaluate', { expression: process.env.AVALIAR, returnByValue: true, awaitPromise: true });
    console.log('AVALIAR:', JSON.stringify(v.result.result.value ?? v.result));
  }
  const r = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  const arq = join(saida, f.nome + '.png');
  writeFileSync(arq, Buffer.from(r.result.data, 'base64'));
  console.log(arq);
}
ws.close();
fim(0);
