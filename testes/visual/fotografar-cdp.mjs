// Fotografa telas da banca visual pelo protocolo do Chrome (CDP), sem tocar
// na tela do Mac: Chrome headless com perfil próprio e porta própria, e a foto
// é SÓ da página (Page.captureScreenshot). `--headless --screenshot` puro às
// vezes não sai sozinho; aqui quem decide a hora da foto é o script.
//
// Precisa de Node 22+ (WebSocket nativo). Uso:
//   node testes/visual/fotografar-cdp.mjs <saida> <nome> <largura> <altura> <query> [espera-ms] [nome largura altura query espera]...
// O servidor estático (raiz do repo) sobe numa porta livre e é derrubado no fim.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'node:fs';
import { createServer } from 'node:net';
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

const portaHttp = await portaLivre();
const http = spawn('python3', ['-m', 'http.server', String(portaHttp), '--bind', '127.0.0.1'], { cwd: RAIZ, stdio: 'ignore' });
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
