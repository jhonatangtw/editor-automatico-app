/* Editor Automático — interface.
   Sem framework e sem build: o app precisa empacotar com PyInstaller, e cada
   passo de build a mais é um jeito a mais de quebrar na máquina do aluno. */

const TOKEN = new URLSearchParams(location.search).get('t') || '';
const raiz  = document.getElementById('raiz');

let E = null;            // estado do app (conta, serviços, ferramentas)
let aba = 'inicio';
let projetoAberto = null;
let conversaAtual = null;
let ATT = null;          // versão nova publicada, quando houver
let IA = null;           // provedores e qual está ativo

// Retratos vivos das telas que dependem do estado da MÁQUINA (contas conectadas,
// dependências instaladas). Ficam aqui só para a tela pintar na hora ao voltar
// para a aba — nunca como resposta final: toda pintura dispara uma reconferência
// e se repinta quando a resposta chega. Ver `revalidar()`.
let SVC = null;          // /api/servicos + /api/claude + /api/ia
let AMB = null;          // /api/ambiente + plugin + ponte + skills
const CONFERENCIA = {};  // escopo -> {quando, erro, voando, esperando}

// ---------------------------------------------------------------- rede
async function api(rota, opcoes = {}) {
  const r = await fetch(rota, {
    ...opcoes,
    headers: { 'Content-Type': 'application/json', 'X-Token': TOKEN, ...(opcoes.headers || {}) },
  });
  const dados = await r.json().catch(() => ({ erro: 'Resposta inesperada do app.' }));
  if (!r.ok) throw new Error(dados.erro || 'Falhou.');
  return dados;
}
const post = (rota, corpo) => api(rota, { method: 'POST', body: JSON.stringify(corpo || {}) });

// ---------------------------------------------------------------- util
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function tc(s) {
  s = Math.max(0, +s || 0);
  const m = Math.floor(s / 60), r = (s % 60).toFixed(1).padStart(4, '0');
  return `${m}:${r}`;
}

function toast(msg, ruim) {
  const d = document.createElement('div');
  d.className = 'aviso' + (ruim ? ' ruim' : '');
  d.style.cssText = 'position:fixed;bottom:22px;left:50%;transform:translateX(-50%);z-index:99;box-shadow:var(--sombra)';
  d.textContent = msg;
  document.body.appendChild(d);
  setTimeout(() => d.remove(), 4200);
}

function modal(html, aoAbrir) {
  const v = document.createElement('div');
  v.className = 'veu';
  v.innerHTML = `<div class="modal">${html}</div>`;
  v.addEventListener('click', (e) => { if (e.target === v) v.remove(); });
  document.body.appendChild(v);
  aoAbrir && aoAbrir(v);
  return v;
}

// ------------------------------------------------- estado vivo da máquina
/* O bug que este bloco existe para matar: a tela mostrava uma FOTO do arranque.
   `E` era buscado uma vez em `iniciar()` e nunca mais, então conectar uma conta
   ou instalar uma dependência não mudava nada até fechar e abrir o app — e o
   pior é que o app estava certo sobre tudo, menos sobre o que estava na tela.

   A regra agora: nenhuma tela de estado de máquina desenha sem reconferir. O
   retrato guardado serve só para a tela aparecer NA HORA; a resposta fresca
   chega logo atrás e repinta se algo mudou. Reconferir acontece ao entrar na
   aba, ao voltar para a janela, depois de cada ação e enquanto um login de
   navegador estiver em andamento. */

const FONTES = {
  contas: async (forcar) => {
    const q = forcar ? '?forcar=1' : '';
    // em paralelo: em fila eram três esperas somadas, e esta leitura acontece
    // várias vezes por minuto agora
    const [svc, claude, ia] = await Promise.all([
      api('/api/servicos' + q),
      api('/api/claude').catch(() => null),
      api('/api/ia').catch(() => null),
    ]);
    if (ia) IA = ia;                      // o seletor do chat lê daqui
    return { ...svc, claude, ia };
  },
  ambiente: async (forcar) => {
    const q = forcar ? '?forcar=1' : '';
    const [amb, plugin, ponte, sk] = await Promise.all([
      api('/api/ambiente' + q),
      api('/api/plugin').catch(() => null),
      api('/api/ponte').catch(() => null),
      api('/api/skills').catch(() => null),
    ]);
    if (plugin && ponte) plugin.ponte = ponte;
    return { ...amb, plugin, skills: sk };
  },
};

const GUARDADO = {
  contas: () => SVC, ambiente: () => AMB,
};
const GUARDAR = {
  contas: (d) => { SVC = d; }, ambiente: (d) => { AMB = d; },
};

/* A assinatura é o que decide se vale repintar. Sem ela, cada reconferência de
   fundo apagaria a chave que a pessoa está digitando e o resultado do "Testar"
   que ela acabou de ler — a tela ficaria correta e inutilizável. */
function assinatura(escopo, d) {
  if (!d) return '';
  if (escopo === 'contas') {
    return JSON.stringify([
      (d.servicos || []).map((x) => [x.id, x.pronto, x.conta, x.fim, x.msg, x.saldo]),
      d.cofre,
      d.claude && [d.claude.conectado, d.claude.rotulo, d.claude.conta, d.claude.entrar, d.claude.instalar],
      d.ia && (d.ia.provedores || []).map((x) => [x.id, x.pronto, x.metodo, x.origem]),
    ]);
  }
  return JSON.stringify([
    (d.itens || []).map((i) => [i.id, i.tem, i.versao, i.instalavel]),
    d.pronto, d.brew, d.gerenciador,
    d.skills && [d.skills.instaladas, d.skills.total],
    d.plugin && [d.plugin.instalado, d.plugin.ultima, d.plugin.tem_nova,
                 d.plugin.ponte && d.plugin.ponte.tem_debug],
  ]);
}

/* Reconfere um escopo contra a máquina. Devolve {ok, mudou}.

   `silencioso` = reconferência de fundo (voltou para a aba, poll de login): não
   grita sucesso, só corrige a tela. Sem silencioso, avisa o que aconteceu —
   que é o que a pessoa precisa ver depois de clicar. */
async function revalidar(escopo, opcoes = {}) {
  const { forcar = false, silencioso = true, aviso = '' } = opcoes;
  const c = CONFERENCIA[escopo] || (CONFERENCIA[escopo] = {});

  /* Duas reconferências juntas viram uma — MENOS quando a nova pede mais que a
     em andamento. Clicar em "Atualizar status" durante uma conferência de fundo
     dava a resposta da de fundo: o clique não relia o PATH, não avisava nada e
     parecia que o botão não fazia coisa alguma. Agora ele espera a de fundo
     acabar e faz a dele. */
  if (c.voando && !(forcar && !c.voandoForcado)) return c.voando;
  if (c.voando) await c.voando.catch(() => {});

  const antes = assinatura(escopo, GUARDADO[escopo]());
  c.erro = null;
  pintarBarra(escopo, 'verificando');

  c.voandoForcado = forcar;
  c.voando = (async () => {
    let r;
    try {
      const d = await FONTES[escopo](forcar);
      GUARDAR[escopo](d);
      c.quando = Date.now();
      c.erro = null;
      r = { ok: true, mudou: assinatura(escopo, d) !== antes, dados: d };
    } catch (e) {
      c.erro = e.message || 'não consegui conferir';
      r = { ok: false, mudou: false, erro: c.erro };
    }
    /* ⚠️ Limpar a marca ANTES de pintar. Pintando de dentro do `try`, a marca
       ainda estava de pé e a barra desenhava "verificando…" com o botão
       desabilitado — para sempre, porque depois disso ninguém mais pintava.
       O app terminava a conferência e a tela dizia que ela não tinha
       terminado, que é a mesma mentira que este arquivo veio consertar. */
    c.voando = null;
    c.voandoForcado = false;

    if (aba === escopo && !projetoAberto) {
      if (r.ok && r.mudou) repintar(escopo);
      else pintarBarra(escopo);
    }
    if (!silencioso) {
      if (!r.ok) toast('Não consegui conferir: ' + r.erro, true);
      else if (aviso) toast(aviso);
    }
    return r;
  })();
  return c.voando;
}

/* Entrar na aba reconfere — mas repintar também chama a tela de novo, e sem
   esta guarda cada mudança viraria duas idas ao backend. */
function revalidarSeVelho(escopo, ms = 2000) {
  const c = CONFERENCIA[escopo] || {};
  if (c.voando) return c.voando;
  if (c.quando && Date.now() - c.quando < ms) return Promise.resolve({ ok: true, mudou: false });
  return revalidar(escopo);
}

/* Repintar preserva o que a PESSOA pôs na tela: a chave meio digitada e o
   resultado do "Testar". Perder isso a cada reconferência de fundo seria
   trocar um bug por outro. */
function repintar(escopo) {
  const guardados = {};
  document.querySelectorAll('[data-chave]').forEach((i) => {
    if (i.value) guardados['chave:' + i.dataset.chave] = i.value;
  });
  document.querySelectorAll('[data-saida]').forEach((o) => {
    if (o.innerHTML) guardados['saida:' + o.dataset.saida] = o.innerHTML;
  });
  const rolagem = (document.getElementById('palco') || {}).scrollTop || 0;

  desenhar().then(() => {
    Object.entries(guardados).forEach(([k, v]) => {
      const [tipo, id] = [k.slice(0, k.indexOf(':')), k.slice(k.indexOf(':') + 1)];
      const alvo = tipo === 'chave'
        ? document.querySelector(`[data-chave="${id}"]`)
        : document.querySelector(`[data-saida="${id}"]`);
      if (!alvo) return;
      if (tipo === 'chave') alvo.value = v; else alvo.innerHTML = v;
    });
    const p = document.getElementById('palco');
    if (p) p.scrollTop = rolagem;
  });
}

/* Primeira entrada numa aba: a conferência custa ~1s (pergunta a CLI e a
   disco). Mostrar a tela vazia nesse segundo é o que faz a pessoa clicar de
   novo; mostrar dado velho seria voltar ao bug. Então mostra o esqueleto. */
function esqueleto(titulo, dica) {
  moldura(`
    <div class="topo"><div class="topo-texto"><span class="eyebrow">${esc(titulo)}</span><h1>${esc(titulo)}</h1>
      <p class="sub">${esc(dica)}</p></div></div>
    <div class="surf lista-servicos">
      ${[0, 1, 2, 3].map(() => `<div class="servico esqueleto">
        <div style="flex:1"><div class="barra-fantasma" style="width:34%"></div>
          <div class="barra-fantasma fina" style="width:56%"></div></div>
        <div class="barra-fantasma botao"></div>
      </div>`).join('')}
    </div>`);
}

// Falhar a conferência não pode virar tela branca: sem saída, fechar e abrir o
// app volta a ser a única ideia que ocorre a quem está na frente dela.
function telaErroEstado(titulo, msg, escopo) {
  moldura(`
    <div class="topo"><div class="topo-texto"><span class="eyebrow">${esc(titulo)}</span><h1>${esc(titulo)}</h1>
      <p class="sub">Não consegui conferir o estado deste computador.</p></div></div>
    <div class="surf lista-servicos"><div class="servico"><div class="sv-corpo">
      <div class="titulo">Conferência falhou
        <span class="pastilha erro"><i class="ponto"></i>sem resposta</span></div>
      <div class="papel">${esc(msg || 'o app não respondeu')}</div>
    </div>
    <button class="bt principal" id="tentar-de-novo">Atualizar status</button>
    </div></div>`);
  document.getElementById('tentar-de-novo').onclick = async () => {
    const b = document.getElementById('tentar-de-novo');
    b.disabled = true; b.textContent = 'Conferindo…';
    const r = await revalidar(escopo, { forcar: true, silencioso: false });
    if (r.ok) desenhar();
    else { b.disabled = false; b.textContent = 'Atualizar status'; }
  };
}

// -------------------------------------------------- barra "conferido quando"
function barraEstado(escopo) {
  return `<div class="conferencia" id="barra-${escopo}"></div>`;
}

function pintarBarra(escopo, forcado) {
  const el = document.getElementById('barra-' + escopo);
  if (!el) return;
  const c = CONFERENCIA[escopo] || {};
  const estado = forcado || (c.voando ? 'verificando' : c.erro ? 'erro' : 'ok');
  const espera = c.esperando;

  const pastilha = estado === 'verificando'
    ? '<span class="pastilha conferindo"><i class="giro"></i>verificando…</span>'
    : estado === 'erro'
      ? `<span class="pastilha erro" title="${esc(c.erro || '')}"><i class="ponto"></i>não consegui conferir</span>`
      : `<span class="pastilha calma"><i class="ponto"></i>${esc(quando(c.quando))}</span>`;

  el.innerHTML = `
    ${espera ? `<span class="pastilha aviso"><i class="giro"></i>esperando o login do
        ${esc(espera.rotulo)}…</span>
      <button class="bt discreto" data-parar-espera="${escopo}">Cancelar</button>` : ''}
    ${pastilha}
    <button class="bt discreto" data-reconferir="${escopo}"
      ${estado === 'verificando' ? 'disabled' : ''}>Atualizar status</button>`;

  const b = el.querySelector('[data-reconferir]');
  if (b) b.onclick = async () => {
    const r = await revalidar(escopo, { forcar: true, silencioso: false });
    if (r.ok) toast(r.mudou ? 'Status atualizado.' : 'Já estava em dia.');
  };
  const p = el.querySelector('[data-parar-espera]');
  if (p) p.onclick = () => pararEspera(escopo);
}

function quando(t) {
  if (!t) return 'ainda não conferido';
  const s = Math.round((Date.now() - t) / 1000);
  if (s < 5) return 'conferido agora';
  if (s < 60) return `conferido há ${s}s`;
  return `conferido há ${Math.round(s / 60)} min`;
}

// ------------------------------------------------ esperar um login de fora
/* Login de CLI acontece no Terminal e no navegador — FORA do app. O app não tem
   como ser avisado quando termina, e era exatamente aí que a tela congelava:
   "Abri o navegador", e daí em diante nada. Então o app fica olhando: reconfere
   de tempo em tempo até o serviço virar, e avisa. Com hora para desistir, senão
   um login abandonado deixaria o app batendo em CLI para sempre. */
function esperarLogin(escopo, rotulo, pronto, minutos = 3) {
  pararEspera(escopo);
  const c = CONFERENCIA[escopo] || (CONFERENCIA[escopo] = {});
  const fim = Date.now() + minutos * 60000;

  const tique = async () => {
    const r = await revalidar(escopo);
    if (r.ok && pronto(GUARDADO[escopo]())) {
      pararEspera(escopo);
      toast(rotulo + ' conectado.');
      // O login pode ter começado por fora da aba: o seletor de IA do chat abre
      // este mesmo fluxo, e lá também há pastilha para corrigir. Mas repintar
      // o chat apagaria a mensagem que a pessoa está escrevendo — e ela nem
      // saberia por quê. Com texto na caixa, o aviso basta; a tela se acerta
      // na próxima pintura.
      const entrada = document.getElementById('entrada');
      if (aba !== escopo && !(entrada && entrada.value.trim())) desenhar();
      return;
    }
    if (Date.now() > fim) {
      pararEspera(escopo);
      toast('Não vi o login do ' + rotulo + ' terminar. Se concluiu, clique em '
            + 'Atualizar status.', true);
    }
  };
  c.esperando = { rotulo, timer: setInterval(tique, 2500) };
  pintarBarra(escopo);
}

function pararEspera(escopo) {
  const c = CONFERENCIA[escopo];
  if (!c || !c.esperando) return;
  clearInterval(c.esperando.timer);
  c.esperando = null;
  pintarBarra(escopo);
}

// ------------------------------------------------- voltar para a janela
/* O login termina no Terminal; a pessoa volta para o app e a resposta dela é
   olhar a tela. Se a tela ainda diz "sem credencial" naquele instante, ela
   conclui que não funcionou — e fecha e abre o app. Voltar o foco é o sinal
   mais honesto de "reconfira agora" que existe aqui. */
let voltouEm = 0;
function aoVoltar(porFoco) {
  /* ⚠️ O `focus` NÃO passa pela peneira do `document.hidden`. Voltando do
     Terminal, os dois eventos chegam quase juntos e a ordem não é garantida —
     o `focus` pode chegar com a página ainda marcada como escondida. Gatilho
     que se cancela sozinho por causa de ordem de evento é o tipo de coisa que
     funciona na minha máquina e falha na do editor. */
  if (!porFoco && document.hidden) return;
  const agora = Date.now();
  if (agora - voltouEm < 1500) return;    // foco pisca; não vira rajada
  voltouEm = agora;
  if (projetoAberto) return;
  if (FONTES[aba]) revalidar(aba);
  else if (aba === 'inicio') { adobeEm = 0; CONFERENCIA.contas && (CONFERENCIA.contas.quando = 0);
    CONFERENCIA.ambiente && (CONFERENCIA.ambiente.quando = 0); telaInicio(); }
}
window.addEventListener('focus', () => aoVoltar(true));
document.addEventListener('visibilitychange', () => aoVoltar(false));

// ---------------------------------------------------------------- entrada
function telaPorta(msg) {
  raiz.innerHTML = `
  <div class="porta"><div class="caixa">
    <div class="marca"><div class="selo">EA</div>
      <div><b>Editor Automático</b><span>Editor Black Belt</span></div></div>
    <div class="cartao">
      <h2>Entrar</h2>
      <p class="sub" style="margin-bottom:18px">Use a mesma conta do Tools PRO.</p>
      ${msg ? `<div class="aviso ruim" style="margin-bottom:14px">${esc(msg)}</div>` : ''}
      <div class="campo"><label>E-mail</label><input id="em" type="email" autocomplete="username"></div>
      <div class="campo"><label>Senha</label><input id="se" type="password" autocomplete="current-password"></div>
      <div style="display:flex;gap:8px;margin-top:18px">
        <button class="bt principal" id="entrar" style="flex:1">Entrar</button>
        <button class="bt" id="criar">Criar conta</button>
      </div>
      <button class="bt discreto" id="por-codigo" style="width:100%;margin-top:10px">
        Entrar com código por e-mail</button>
    </div>
  </div></div>`;

  const entrar = async () => {
    const b = document.getElementById('entrar');
    b.disabled = true; b.textContent = 'Entrando…';
    try {
      const r = await post('/api/conta/entrar', {
        email: document.getElementById('em').value.trim(),
        senha: document.getElementById('se').value,
      });
      if (!r.ok) { telaPorta(r.msg || 'Não consegui entrar.'); return; }
      iniciar();
    } catch (e) { telaPorta(e.message); }
  };
  document.getElementById('entrar').onclick = entrar;
  document.getElementById('se').onkeydown = (e) => { if (e.key === 'Enter') entrar(); };
  document.getElementById('criar').onclick = telaCadastro;
  document.getElementById('por-codigo').onclick = () =>
    telaCodigo(document.getElementById('em').value.trim());
}

/* Entrar sem senha: o servidor manda um código de 6 dígitos para o e-mail.
   A resposta do pedido é a MESMA para e-mail com e sem conta — a tela repete a
   frase do servidor e nunca diz "não achei este e-mail". O token que volta é
   o mesmo do login com senha, gravado no mesmo arquivo do painel do Premiere. */
function telaCodigo(email, etapa, msg, ruim) {
  const pedido = etapa === 'digitar';
  raiz.innerHTML = `
  <div class="porta"><div class="caixa">
    <div class="marca"><div class="selo">EA</div>
      <div><b>Editor Automático</b><span>Editor Black Belt</span></div></div>
    <div class="cartao">
      <h2>Entrar com código</h2>
      <p class="sub" style="margin-bottom:18px">${pedido
        ? 'Digite o código de 6 dígitos que chegou no seu e-mail.'
        : 'Enviamos um código de 6 dígitos para o seu e-mail. Sem senha.'}</p>
      ${msg ? `<div class="aviso${ruim ? ' ruim' : ''}" style="margin-bottom:14px">${esc(msg)}</div>` : ''}
      <div class="campo"><label>E-mail</label><input id="cod-em" type="email" autocomplete="username"
        value="${esc(email || '')}" ${pedido ? 'readonly' : ''}></div>
      ${pedido ? `<div class="campo"><label>Código</label><input id="cod-n" inputmode="numeric"
        autocomplete="one-time-code" maxlength="7" placeholder="000000"
        style="letter-spacing:.3em;font-size:18px"></div>` : ''}
      <div style="display:flex;gap:8px;margin-top:18px">
        <button class="bt principal" id="cod-ok" style="flex:1">${pedido ? 'Entrar' : 'Enviar código'}</button>
        <button class="bt" id="cod-voltar">Voltar</button>
      </div>
      ${pedido ? `<button class="bt discreto" id="cod-outro" style="width:100%;margin-top:10px">
        Não chegou? Pedir outro código</button>` : ''}
    </div>
  </div></div>`;

  const campoEmail = () => document.getElementById('cod-em').value.trim();
  const pedir = async () => {
    const b = document.getElementById('cod-ok');
    b.disabled = true; b.textContent = 'Enviando…';
    try {
      const r = await post('/api/conta/codigo', { email: campoEmail() });
      if (!r.ok) { telaCodigo(campoEmail(), '', r.msg || 'Não consegui pedir o código.', true); return; }
      telaCodigo(campoEmail(), 'digitar', r.msg);
    } catch (e) { telaCodigo(campoEmail(), '', e.message, true); }
  };
  const verificar = async () => {
    const b = document.getElementById('cod-ok');
    b.disabled = true; b.textContent = 'Entrando…';
    try {
      const r = await post('/api/conta/codigo/entrar', {
        email: campoEmail(), codigo: document.getElementById('cod-n').value,
      });
      if (!r.ok) { telaCodigo(campoEmail(), 'digitar', r.msg || 'Não consegui entrar.', true); return; }
      iniciar();
    } catch (e) { telaCodigo(campoEmail(), 'digitar', e.message, true); }
  };

  document.getElementById('cod-voltar').onclick = () => telaPorta();
  if (pedido) {
    const n = document.getElementById('cod-n');
    n.focus();
    n.onkeydown = (e) => { if (e.key === 'Enter') verificar(); };
    document.getElementById('cod-ok').onclick = verificar;
    document.getElementById('cod-outro').onclick = () => telaCodigo(campoEmail());
  } else {
    const em = document.getElementById('cod-em');
    if (!em.value) em.focus();
    em.onkeydown = (e) => { if (e.key === 'Enter') pedir(); };
    document.getElementById('cod-ok').onclick = pedir;
  }
}

function telaCadastro() {
  modal(`<h2>Criar conta</h2>
    <p class="sub" style="margin-bottom:16px">Depois de criar, o acesso passa por aprovação.</p>
    <div class="campo"><label>Nome</label><input id="c-nome"></div>
    <div class="campo"><label>E-mail</label><input id="c-email" type="email"></div>
    <div class="campo"><label>Senha</label><input id="c-senha" type="password"></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="c-ok">Criar</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#c-ok').onclick = async () => {
      try {
        const r = await post('/api/conta/cadastrar', {
          nome: v.querySelector('#c-nome').value.trim(),
          email: v.querySelector('#c-email').value.trim(),
          senha: v.querySelector('#c-senha').value,
        });
        v.remove();
        toast(r.msg || 'Pedido enviado. Aguarde a aprovação.');
      } catch (e) { toast(e.message, true); }
    };
  });
}

// ---------------------------------------------------------------- moldura
/* Ícones de traço, 1.6 px, desenhados para 20 px. SVG inline: o app abre sem
   internet, então nada de pacote de ícones de fora. */
const ICONE = {
  inicio: '<path d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z"/>',
  chat: '<path d="M5 5h14a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-8l-4.5 3.5V16H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/><path d="M8.5 10.5h7M8.5 13h4"/>',
  projetos: '<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>',
  contas: '<circle cx="9" cy="9" r="3.2"/><path d="M3.8 19c.6-3 2.6-4.6 5.2-4.6s4.6 1.6 5.2 4.6"/><path d="M15.5 6.2a3 3 0 0 1 0 5.6M17.8 14.8c1.3.7 2.1 2.1 2.4 4.2"/>',
  ambiente: '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M9 20h6M12 16v4"/><path d="m8.5 10.5 2 2 4-4"/>',
  aulas: '<rect x="3.5" y="5.5" width="17" height="12" rx="2"/><path d="m10.5 9.2 4 2.3-4 2.3z" fill="currentColor"/><path d="M8 20.5h8"/>',
  seta: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  mais: '<circle cx="6" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="18" cy="12" r="1.3" fill="currentColor"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  sair: '<path d="M14 5H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8"/><path d="m16 8.5 3.5 3.5L16 15.5M19.5 12H10"/>',
  atualizar: '<path d="M19 12a7 7 0 1 1-2.1-5"/><path d="M19 4.5V8h-3.5"/>',
  guia: '<path d="M5 5.5A1.5 1.5 0 0 1 6.5 4H19v14H6.5A1.5 1.5 0 0 0 5 19.5z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19v-3"/><path d="M9 8.5h6M9 11.5h4"/>',
  copiar: '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5V6a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5"/>',
  busca: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.2-4.2"/>',
};
const ic = (n, cls = '') => `<svg class="ic ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONE[n] || ''}</svg>`;

/* As seções com o que cada uma é, em uma frase. Quem abre o app pela primeira
   vez não sabe o que é "Ambiente" — a descrição é o que evita o chamado. */
const SECOES = {
  inicio:   ['Início', 'Seu painel: o que falta para editar e o próximo passo.'],
  chat:     ['Conversa', 'Peça a edição em português — a IA confere o Premiere e monta para você.'],
  projetos: ['Histórico', 'Suas conversas anteriores. Abrir uma volta com tudo o que já foi feito.'],
  contas:   ['Contas', 'As ferramentas de IA que o app usa, cada uma entrando com a SUA conta.'],
  ambiente: ['Ambiente', 'Os programas que o app precisa neste computador. Ele instala o que faltar.'],
  guia:     ['Guia de comandos', 'Os melhores pedidos para a IA, prontos para copiar — com o que cada um faz e o que precisa estar aberto.'],
};

function cabecalho(id, direita = '', titulo) {
  const [t, d] = SECOES[id] || [titulo || '', ''];
  return `<header class="topo">
      <div class="topo-texto">
        <span class="eyebrow">${esc(t)}</span>
        <h1>${esc(titulo || t)}</h1>
        <p class="sub">${esc(d)}</p>
      </div>
      ${direita ? `<div class="topo-acoes">${direita}</div>` : ''}
    </header>`;
}

function iniciais(nome) {
  const p = String(nome || '').trim().split(/\s+/).filter(Boolean);
  return ((p[0] || '?')[0] + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase();
}

function moldura(conteudo) {
  const abas = [
    ['inicio',    'inicio',   'Início'],
    ['chat',      'chat',     'Conversa', '<span class="selo-beta">beta</span>'],
    ['projetos',  'projetos', 'Histórico'],
    ['contas',    'contas',   'Contas'],
    ['ambiente',  'ambiente', 'Ambiente'],
    ['guia',      'guia',     'Guia de comandos'],
  ];
  const nome = E?.conta?.nome || 'Conectado';
  raiz.innerHTML = `
  <div class="app">
    <aside class="rail">
      <div class="marca">
        <div class="selo" aria-hidden="true"><i></i></div>
        <div><b>Editor Automático</b><span>Editor Black Belt</span></div>
      </div>
      <nav class="nav" aria-label="Seções">
        ${abas.map(([id, i, t, extra]) => `<button data-aba="${id}" class="${aba === id && !projetoAberto ? 'ativo' : ''}"
            ${aba === id ? 'aria-current="page"' : ''}>${ic(i)}<span>${t}</span>${extra || ''}</button>`).join('')}
        <div class="nav-sep"></div>
        <button class="nav-aulas" id="aulas" title="Abre a área do aluno no navegador, já conectado">
          ${ic('aulas')}<span>Minhas aulas</span>${ic('seta', 'mini')}</button>
      </nav>
      <div class="rodape">
        <div class="quem">
          <div class="avatar" aria-hidden="true">${esc(iniciais(nome))}</div>
          <div class="quem-texto"><b title="${esc(nome)}">${esc(nome)}</b>
            <span class="${E?.conta?.offline ? 'offline' : ''}">${E?.conta?.offline ? 'modo offline' : 'conta ativa'}</span></div>
          <button class="sair" id="sair" title="Sair da conta">${ic('sair')}</button>
        </div>
        ${controleAtualizacao()}
      </div>
    </aside>
    <main class="palco" id="palco"><div class="palco-dentro">${conteudo}</div></main>
  </div>`;
  raiz.querySelectorAll('[data-aba]').forEach((b) => {
    b.onclick = () => { aba = b.dataset.aba; projetoAberto = null; desenhar(); };
  });
  document.getElementById('sair').onclick = async () => {
    await post('/api/conta/sair'); iniciar();
  };
  const ba = document.getElementById('att');
  if (ba) ba.onclick = () => (ATT?.tem_nova ? atualizar() : procurarAtualizacao());
  const bl = document.getElementById('aulas');
  if (bl) bl.onclick = abrirAulas;
}

// "Minhas aulas": o app pede um passe de 60 s e abre o navegador padrão já
// logado na área do aluno. O link nunca passa pela tela.
async function abrirAulas() {
  const bs = document.querySelectorAll('#aulas, [data-aulas]');
  bs.forEach((b) => { b.disabled = true; b.classList.add('ocupado'); });
  try {
    const r = await post('/api/conta/aulas');
    if (r.ok) toast(r.msg || 'Abrindo a área do aluno no navegador…');
    else toast(r.msg || 'Não consegui abrir a área do aluno.', true);
  } catch (e) { toast(e.message, true); }
  bs.forEach((b) => { b.disabled = false; b.classList.remove('ocupado'); });
}

// O controle fica SEMPRE visível, mesmo em dia. Quando ele só aparecia havendo
// versão nova, quem estava atualizado via um rodapé mudo e concluía que não
// dava para atualizar — foi exatamente o que aconteceu no plugin antes.
function controleAtualizacao() {
  if (!ATT) return `<button class="att buscando" id="att"><i class="giro"></i>procurando atualização…</button>`;
  if (ATT.tem_nova) {
    return `<button class="att nova" id="att" title="${esc(ATT.notas || '')}">
      ${ic('atualizar')}Atualizar para ${esc(ATT.ultima)}</button>`;
  }
  if (ATT.erro) {
    return `<button class="att" id="att" title="${esc(ATT.erro)}">
      <span class="v">v${esc(ATT.versao)}</span>tentar de novo</button>`;
  }
  return `<button class="att" id="att" title="${ATT.rodando_codigo
    ? 'rodando código atualizado sem reinstalar' : 'Você está na versão mais nova'}">
    <span class="v">v${esc(ATT.versao)}</span>procurar atualização</button>`;
}

async function procurarAtualizacao() {
  const b = document.getElementById('att');
  if (b) { b.textContent = 'procurando…'; b.classList.add('buscando'); }
  try {
    ATT = await api('/api/atualizacao');
    desenhar();
    if (ATT.tem_nova) toast('Saiu a versão ' + ATT.ultima + '.');
    else if (ATT.erro) toast(ATT.erro, true);
    else toast('Você já está na versão mais nova (' + ATT.versao + ').');
  } catch (e) {
    toast(e.message, true);
    desenhar();
  }
}

// Atualização LEVE: quase toda correção é código, e código o app troca sozinho —
// ~120 KB e reabrir, sem instalador. Só cai no instalador quando a versão
// declara que mexeu no que vem dentro do pacote.
function atualizar() {
  if (ATT?.modo === 'codigo') return atualizarCodigo();
  return baixarAtualizacao();
}

function atualizarCodigo() {
  const v = modal(`<h2>Atualizando para ${esc(ATT.ultima)}</h2>
    ${ATT.notas ? `<p class="sub">${esc(ATT.notas)}</p>` : ''}
    <div class="portao" id="log" style="max-height:160px">baixando…</div>`);
  post('/api/atualizacao/codigo').then((r) => {
    const t = setInterval(async () => {
      const st = await api('/api/tarefas/' + r.tarefa);
      v.querySelector('#log').textContent = (st.log || []).slice(-3).join('\n') || 'trabalhando…';
      if (st.estado === 'pronto') {
        clearInterval(t);
        v.innerHTML = `<h2>Pronto — versão ${esc(ATT.ultima)}</h2>
          <p class="sub">${esc(st.resultado?.msg || 'Atualizado.')}</p>
          <div class="etapa-acoes">
            <button class="bt principal" id="reabrir">Reabrir agora</button>
            <button class="bt discreto" id="depois">Depois</button>
          </div>`;
        v.querySelector('#reabrir').onclick = () => {
          post('/api/atualizacao/reabrir').catch(() => {});
          v.querySelector('.sub').textContent = 'Reabrindo…';
        };
        v.querySelector('#depois').onclick = () => v.remove();
      } else if (st.estado === 'erro') {
        clearInterval(t); v.remove(); toast(st.erro, true);
      }
    }, 700);
  }).catch((e) => { v.remove(); toast(e.message, true); });
}

// A troca do .app é do usuário: baixo o .dmg e abro. Substituir por baixo um
// app que está rodando é onde nasce o app que não abre mais.
function baixarAtualizacao() {
  const v = modal(`<h2>Atualizando para ${esc(ATT.ultima)}</h2>
    ${ATT.notas ? `<p class="sub">${esc(ATT.notas)}</p>` : ''}
    <div class="portao" id="log" style="max-height:200px">começando…</div>`);
  post('/api/atualizacao/baixar').then((r) => {
    const t = setInterval(async () => {
      const st = await api('/api/tarefas/' + r.tarefa);
      v.querySelector('#log').textContent = (st.log || []).slice(-3).join('\n') || 'baixando…';
      if (st.estado === 'pronto') {
        clearInterval(t); v.remove();
        toast(st.resultado?.msg || 'Baixado.');
      } else if (st.estado === 'erro') { clearInterval(t); v.remove(); toast(st.erro, true); }
    }, 900);
  }).catch((e) => { v.remove(); toast(e.message, true); });
}

// ---------------------------------------------------------------- início
/* A tela que responde "o que eu faço agora?". Três passos, cada um em
   português de gente, e UMA ação — a do primeiro passo que falta. Quem precisa
   ver o detalhe vai para Contas ou Ambiente; aqui é só a direção.

   Lê os MESMOS retratos das abas (SVC e AMB) e reconfere os dois atrás, então
   o que está aqui nunca discorda do que está lá. */

// as ferramentas sem as quais a edição não sai: quem decide, quem gera a
// imagem e quem faz a voz. ChatGPT, HeyGen e MiniMax são extras.
const ESSENCIAIS = ['claude', 'higgsfield', 'elevenlabs'];
let ADOBE = null;          // última leitura do /api/adobe (só para o Início)
let adobeEm = 0;

function contasResumo(s) {
  if (!s) return null;
  const nomes = { claude: 'Claude', higgsfield: 'Higgsfield', elevenlabs: 'ElevenLabs' };
  const pronto = (id) => id === 'claude'
    ? !!(s.claude ? s.claude.conectado : (s.servicos || []).find((x) => x.id === id)?.pronto)
    : !!(s.servicos || []).find((x) => x.id === id)?.pronto;
  const faltam = ESSENCIAIS.filter((id) => !pronto(id)).map((id) => nomes[id]);
  const extras = (s.servicos || []).filter((x) => !ESSENCIAIS.includes(x.id) && x.pronto).length
    + (((s.ia && s.ia.provedores) || []).find((x) => x.id === 'chatgpt')?.pronto ? 1 : 0);
  return { faltam, ok: !faltam.length, total: ESSENCIAIS.length,
           prontas: ESSENCIAIS.length - faltam.length, extras };
}

function passosInicio() {
  const amb = AMB, c = contasResumo(SVC);
  const pl = amb && amb.plugin;
  const p1 = !amb ? { estado: 'conferindo', nota: 'conferindo os programas…' }
    : amb.pronto ? { estado: 'ok', nota: 'Tudo o que é essencial está instalado.' }
    : { estado: 'falta', nota: 'Falta instalar: ' + amb.faltam.join(', ') + '.',
        acao: ['preparar', 'Preparar este computador'] };
  const p2 = !c ? { estado: 'conferindo', nota: 'conferindo suas contas…' }
    : c.ok ? { estado: 'ok', nota: `Claude, Higgsfield e ElevenLabs conectados${c.extras ? ` · +${c.extras} extra${c.extras > 1 ? 's' : ''}` : ''}.` }
    : { estado: 'falta', nota: 'Falta conectar: ' + c.faltam.join(', ') + '.',
        acao: ['contas', 'Conectar minhas contas'] };
  let p3;
  if (!amb) p3 = { estado: 'conferindo', nota: 'procurando o plugin…' };
  else if (!pl || !pl.instalado) p3 = { estado: 'falta', nota: 'O plugin Tools PRO ainda não está no Premiere.', acao: ['plugin', 'Instalar o plugin'] };
  else if (pl.ponte && !pl.ponte.tem_debug) p3 = { estado: 'falta', nota: 'Plugin instalado, mas a conexão com o app ainda não foi preparada.', acao: ['ponte', 'Preparar a conexão'] };
  else if (ADOBE && ADOBE.utilizavel) p3 = { estado: 'ok', nota: 'Conectado agora' + (ADOBE.projeto ? ' — projeto ' + ADOBE.projeto : '') + '.' };
  else if (ADOBE && ADOBE.apps && !ADOBE.apps.premiere) p3 = { estado: 'espera', nota: 'Plugin pronto. Abra o Premiere quando for editar — o app conecta sozinho.' };
  else if (ADOBE) p3 = { estado: 'espera', nota: 'Premiere aberto: abra o painel em Janela › Extensões › Tools PRO.', acao: ['reconectar', 'Conectar agora'] };
  else p3 = { estado: 'ok', nota: `Plugin v${pl.instalado} instalado e conexão preparada.` };
  return [
    { n: 1, titulo: 'Programas instalados', porque: 'FFmpeg, Whisper e o Claude Code rodam a edição no seu computador.', ...p1 },
    { n: 2, titulo: 'Contas conectadas', porque: 'A IA que decide a edição, a que gera imagem e a que faz a voz.', ...p2 },
    { n: 3, titulo: 'Plugin conectado ao Premiere', porque: 'É por ele que o app escreve na sua timeline.', ...p3 },
  ];
}

const ROTULO_PASSO = { ok: 'Pronto', falta: 'Falta', espera: 'Quase', conferindo: 'Conferindo' };

function saudacao() {
  const h = new Date().getHours();
  return h < 5 ? 'Boa noite' : h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite';
}

async function telaInicio() {
  // na hora com o que já se sabe; reconfere atrás e repinta se mudou
  pintarInicio();
  const antes = JSON.stringify([assinatura('contas', SVC), assinatura('ambiente', AMB), ADOBE && ADOBE.utilizavel]);
  const vel = Date.now() - adobeEm > 20000;
  await Promise.all([
    revalidarSeVelho('contas', 8000), revalidarSeVelho('ambiente', 8000),
    vel ? api('/api/adobe').then((a) => { ADOBE = a; adobeEm = Date.now(); }).catch(() => {}) : null,
  ]);
  const depois = JSON.stringify([assinatura('contas', SVC), assinatura('ambiente', AMB), ADOBE && ADOBE.utilizavel]);
  if (aba === 'inicio' && !projetoAberto && antes !== depois) pintarInicio();
}

function pintarInicio() {
  const passos = passosInicio();
  const feitos = passos.filter((p) => p.estado === 'ok').length;
  const proximo = passos.find((p) => p.acao) || null;
  const tudo = feitos === passos.length || (!proximo && passos.every((p) => p.estado !== 'falta' && p.estado !== 'conferindo'));
  const conferindo = passos.some((p) => p.estado === 'conferindo');
  const primeiro = (E?.conta?.nome || '').trim().split(/\s+/)[0] || '';

  const destaque = conferindo && !proximo
    ? { titulo: 'Conferindo este computador…', texto: 'Leva um segundo. Nada é instalado sem você pedir.', botao: '' }
    : proximo
      ? { titulo: `Próximo passo: ${proximo.titulo.toLowerCase()}`, texto: proximo.nota,
          botao: `<button class="bt principal grande" id="proximo">${esc(proximo.acao[1])}${ic('seta')}</button>` }
      : { titulo: 'Tudo pronto para editar', texto: 'Abra a Conversa e diga o que quer fazer — por exemplo, "analise esta timeline".',
          botao: `<button class="bt principal grande" id="proximo">Começar uma edição${ic('seta')}</button>` };

  moldura(`
    <section class="inicio">
      <header class="topo">
        <div class="topo-texto">
          <span class="eyebrow">Início</span>
          <h1>${esc(saudacao())}${primeiro ? ', ' + esc(primeiro) : ''}.</h1>
          <p class="sub">${tudo ? 'Seu computador está pronto. É só editar.'
            : `${feitos} de 3 passos prontos. Faltam poucos cliques para o app editar por você.`}</p>
        </div>
      </header>

      <div class="inicio-grade">
        <div class="surf passos-cartao">
          <div class="passos-cab">
            <span class="rotulo">Para o app editar por você</span>
            <span class="progresso" aria-label="${feitos} de 3 prontos"><i style="width:${Math.round(feitos / 3 * 100)}%"></i></span>
            <span class="rotulo">${feitos}/3</span>
          </div>
          <ol class="passos-lista">
            ${passos.map((p) => `<li class="passo-inicio ${p.estado}">
              <span class="passo-n">${p.estado === 'ok' ? ic('check') : p.estado === 'conferindo' ? '<i class="giro"></i>' : p.n}</span>
              <div class="passo-txt">
                <div class="passo-titulo">${esc(p.titulo)}
                  <span class="chip ${p.estado === 'ok' ? 'ok' : p.estado === 'falta' ? 'atencao' : ''}">${ROTULO_PASSO[p.estado]}</span></div>
                <div class="passo-nota">${esc(p.nota)}</div>
                <div class="passo-porque">${esc(p.porque)}</div>
              </div>
            </li>`).join('')}
          </ol>
          <div class="proximo ${tudo ? 'pronto' : ''}">
            <div>
              <b>${esc(destaque.titulo)}</b>
              <p>${esc(destaque.texto)}</p>
            </div>
            ${destaque.botao}
          </div>
        </div>

        <div class="inicio-lado">
          <button class="surf aulas-cartao" data-aulas>
            <span class="aulas-ic">${ic('aulas')}</span>
            <span class="aulas-txt"><span class="eyebrow pequeno">Área do aluno</span>
              <b>Minhas aulas</b>
              <span>Abre as aulas no navegador, já conectado com a sua conta.</span></span>
            <span class="aulas-seta">${ic('seta')}</span>
          </button>
          <div class="surf versao-cartao">
            <span class="rotulo">Versão do app</span>
            <div class="versao-linha">
              <b class="mono">v${esc(ATT?.versao || '…')}</b>
              ${!ATT ? '<span class="chip"><i class="giro"></i>procurando</span>'
                : ATT.tem_nova ? `<span class="chip atencao">nova: v${esc(ATT.ultima)}</span>`
                : ATT.erro ? '<span class="chip">sem conferir</span>'
                : '<span class="chip ok">em dia</span>'}
            </div>
            <p class="sub">${ATT?.tem_nova ? esc(ATT.notas || 'Tem versão nova com melhorias.')
              : 'O app procura atualização sozinho quando abre.'}</p>
            <button class="bt ${ATT?.tem_nova ? 'principal' : ''}" id="inicio-att">${ATT?.tem_nova
              ? 'Atualizar agora' : 'Procurar atualização'}</button>
          </div>
        </div>
      </div>
    </section>`);

  document.querySelectorAll('[data-aulas]').forEach((b) => { b.onclick = abrirAulas; });
  const at = document.getElementById('inicio-att');
  if (at) at.onclick = () => (ATT?.tem_nova ? atualizar() : procurarAtualizacao());
  const px = document.getElementById('proximo');
  if (px) px.onclick = () => {
    const qual = proximo ? proximo.acao[0] : 'chat';
    if (qual === 'preparar') return prepararMaquina();
    if (qual === 'ponte') return prepararPonte();
    if (qual === 'reconectar') return reconectarToolsPro().then(() => { adobeEm = 0; telaInicio(); });
    aba = qual === 'plugin' ? 'ambiente' : qual; projetoAberto = null; desenhar();
  };
}

// ---------------------------------------------------------------- guia de comandos
/* Os pedidos que funcionam, prontos para copiar. A fonte é web/guia.json — o
   mesmo arquivo vira web/GUIA-DE-COMANDOS.md (gerar-guia.py), então a tela e o
   documento não se desencontram. Cada comando diz o que precisa estar aberto:
   é o que mais gera "não funcionou" quando falta. */
let GUIA = null;
let guiaBusca = '';

// ---- busca do guia (testes/test_guia.py roda este trecho no node: mexeu, rode)
/* Sem acento e sem caixa dos DOIS lados: o aluno digita "silencio" e o guia
   escreve "silêncio" — antes isso dava "nenhum comando". Espaço sobrando não
   conta, e cada palavra pode estar em qualquer parte do cartão. */
function normalizarBusca(t) {
  return String(t == null ? '' : t)
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/\s+/g, ' ').trim();
}
function indiceGuia(gr, c) {
  const t = normalizarBusca([gr.titulo, gr.descricao, c.titulo, c.nivel, c.ia, c.comando,
    c.faz, c.quando, c.tempo, (c.precisa || []).join(' '), (c.usa || []).join(' '),
    (c.tags || []).join(' ')].join(' '));
  // "broll" acha "b-roll", "pushin" acha "push-in"
  return t + ' ' + t.replace(/-/g, '');
}
function casaBusca(indice, q) {
  const termos = normalizarBusca(q).split(' ').filter(Boolean);
  return termos.every((x) => indice.includes(x));
}
// ---- fim da busca do guia

async function copiarTexto(t) {
  try { await navigator.clipboard.writeText(t); return true; } catch (_) { /* cai no plano B */ }
  const ta = document.createElement('textarea');
  ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px';
  document.body.appendChild(ta); ta.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
  ta.remove();
  return ok;
}

async function telaGuia() {
  if (!GUIA) {
    try { GUIA = await (await fetch('guia.json', { cache: 'no-store' })).json(); }
    catch (e) { moldura(cabecalho('guia') + `<div class="aviso ruim">Não consegui abrir o guia: ${esc(e.message)}</div>`); return; }
    // grupo que depende de uma skill só aparece quando ela vem no app (o
    // gerar-guia.py faz o mesmo filtro no .md) — pedido que cita skill que não
    // existe é pedido que não funciona
    if (GUIA.grupos.some((gr) => gr.requer_skill)) {
      let nomes = [];
      try { nomes = ((await api('/api/skills')).skills || []).map((x) => x.nome); } catch (_) { /* sem lista: esconde */ }
      GUIA.grupos = GUIA.grupos.filter((gr) => !gr.requer_skill || nomes.includes(gr.requer_skill));
    }
  }
  const g = GUIA;
  const total = g.grupos.reduce((n, gr) => n + gr.comandos.length, 0);
  moldura(`
    ${cabecalho('guia', `<label class="busca">${ic('busca')}
        <input id="guia-busca" type="search" placeholder="Buscar: zoom, legenda, b-roll…" value="${esc(guiaBusca)}"></label>`)}
    <p class="sub guia-intro">${esc(g.intro)}</p>
    <nav class="guia-indice" aria-label="Grupos">
      ${g.grupos.map((gr) => `<a href="#g-${esc(gr.id)}" data-ir="${esc(gr.id)}">${esc(gr.titulo)}<span>${gr.comandos.length}</span></a>`).join('')}
    </nav>
    <div id="guia-lista">
      ${g.grupos.map((gr) => `
        <section class="grupo guia-grupo" id="g-${esc(gr.id)}">
          <div class="grupo-cab"><h2>${esc(gr.titulo)}</h2><p class="sub">${esc(gr.descricao)}</p></div>
          <div class="guia-grade">
            ${gr.comandos.map((c, i) => `
              <article class="surf cmd" data-busca="${esc(indiceGuia(gr, c))}">
                <header class="cmd-cab">
                  <h3>${esc(c.titulo)}</h3>
                  <span class="cmd-selos">
                    <span class="chip ${c.nivel === 'completo' ? 'atencao' : ''}" title="${esc((g.niveis || {})[c.nivel] || '')}">${esc(c.nivel)}</span>
                    <span class="chip ${c.ia === 'Claude' ? '' : 'ok'}" title="${esc(g.legenda_ia[c.ia] || '')}">${esc(c.ia)}</span>
                  </span>
                </header>
                <p class="cmd-faz">${esc(c.faz)}</p>
                <div class="cmd-texto ${c.comando.split('\n').length > 7 ? 'longo' : ''}">${esc(c.comando)}</div>
                <div class="cmd-botoes">
                  <button class="bt principal cmd-copiar" data-copiar="${esc(gr.id)}:${i}">${ic('copiar')}Copiar</button>
                  ${c.comando.split('\n').length > 7 ? '<button class="bt discreto" data-expandir>Ver o comando inteiro</button>' : ''}
                  ${c.tempo ? `<span class="cmd-tempo">⏱ ${esc(c.tempo)}</span>` : ''}
                </div>
                <dl class="cmd-info">
                  <dt>Quando usar</dt><dd>${esc(c.quando)}</dd>
                  <dt>Precisa</dt><dd>${c.precisa.map((x) => `<span class="req">${esc(x)}</span>`).join('')}</dd>
                </dl>
                <div class="cmd-usa mono">${(c.usa || []).map(esc).join(' · ')}</div>
              </article>`).join('')}
          </div>
        </section>`).join('')}
      <div class="vazio" id="guia-vazio" hidden><h2>Nenhum comando com “<span></span>”</h2><p>Tente outra palavra — por exemplo “marcador”, “After” ou “prompt”.</p></div>
    </div>
    <p class="sub guia-rodape">${total} comandos · o mesmo conteúdo está em <span class="mono">GUIA-DE-COMANDOS.md</span>, dentro da pasta do app.</p>`);

  const filtrar = () => {
    const q = normalizarBusca(guiaBusca);
    let vistos = 0;
    document.querySelectorAll('.cmd').forEach((c) => {
      const ok = !q || casaBusca(c.dataset.busca, q);
      c.hidden = !ok; if (ok) vistos++;
    });
    document.querySelectorAll('.guia-grupo').forEach((gr) => {
      gr.hidden = ![...gr.querySelectorAll('.cmd')].some((c) => !c.hidden);
    });
    const v = document.getElementById('guia-vazio');
    v.hidden = vistos > 0; v.querySelector('span').textContent = guiaBusca.trim();
  };
  const busca = document.getElementById('guia-busca');
  busca.oninput = () => { guiaBusca = busca.value; filtrar(); };
  filtrar();
  document.querySelectorAll('[data-ir]').forEach((a) => {
    a.onclick = (e) => {
      e.preventDefault();
      const alvo = document.getElementById('g-' + a.dataset.ir);
      if (alvo) alvo.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    };
  });
  document.querySelectorAll('[data-expandir]').forEach((b) => {
    b.onclick = () => {
      const t = b.closest('.cmd').querySelector('.cmd-texto');
      const aberto = t.classList.toggle('aberto');
      b.textContent = aberto ? 'Recolher' : 'Ver o comando inteiro';
    };
  });
  document.querySelectorAll('[data-copiar]').forEach((b) => {
    b.onclick = async () => {
      const [gid, i] = b.dataset.copiar.split(':');
      const c = g.grupos.find((x) => x.id === gid).comandos[+i];
      const ok = await copiarTexto(c.comando);
      if (!ok) return toast('Não consegui copiar — selecione o texto e use Cmd/Ctrl+C.', true);
      b.classList.add('copiado'); b.innerHTML = `${ic('check')}Copiado`;
      setTimeout(() => { b.classList.remove('copiado'); b.innerHTML = `${ic('copiar')}Copiar`; }, 1800);
    };
  });
}

// ---------------------------------------------------------------- projetos
async function telaProjetos() {
  const { conversas } = await api('/api/conversas');

  const quando = (t) => {
    const d = new Date(t * 1000), hoje = new Date();
    const mesmo = d.toDateString() === hoje.toDateString();
    return mesmo ? d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
                 : d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  };

  moldura(`
    ${cabecalho('projetos', '<button class="bt principal" id="nova">+ Nova conversa</button>')}
    ${conversas.length ? `<div class="lista-proj">
      ${conversas.map((c) => `
        <div class="proj" data-conversa="${esc(c.id)}">
          <div>
            <div class="nome">${esc(c.titulo)}</div>
            <div class="meta">
              <span>${quando(c.quando)}</span>
              <span>${c.mensagens} mensagens</span>
              ${c.passos ? `<span>${c.passos} passos</span>` : ''}
              ${c.projeto ? `<span style="color:var(--ouro)">projeto ligado</span>` : ''}
            </div>
          </div>
          <button class="bt discreto perigo" data-apagar-conversa="${esc(c.id)}">Apagar</button>
        </div>`).join('')}
      </div>` : `
      <div class="vazio">
        <div class="icone">▤</div>
        <h2>Nada por aqui ainda</h2>
        <p>Vá para a Conversa e diga o que quer editar.</p>
        <button class="bt principal" id="ir-chat" style="margin-top:18px">Abrir a conversa</button>
      </div>`}`);

  const ir = document.getElementById('ir-chat');
  if (ir) ir.onclick = () => { aba = 'chat'; desenhar(); };
  document.getElementById('nova').onclick = async () => {
    const r = await post('/api/conversas/nova');
    conversaAtual = r.conversa; aba = 'chat'; desenhar();
  };
  document.querySelectorAll('[data-conversa]').forEach((c) => {
    c.onclick = (e) => {
      if (e.target.dataset.apagarConversa) return;
      conversaAtual = c.dataset.conversa; aba = 'chat'; desenhar();
    };
  });
  document.querySelectorAll('[data-apagar-conversa]').forEach((b) => {
    b.onclick = async (e) => {
      e.stopPropagation();
      await post('/api/conversas/apagar', { conversa: b.dataset.apagarConversa });
      desenhar();
    };
  });
}

function telaNovoProjeto() {
  modal(`<h2>Novo projeto</h2>
    <p class="sub" style="margin-bottom:16px">Aponte o bruto do avatar falante — o body em plano fixo.</p>
    <div class="campo"><label>Caminho do vídeo</label>
      <input id="n-video" placeholder="~/Documents/.../BODY.mp4"></div>
    <div class="campo"><label>Nome do job <span style="color:var(--texto-3)">(opcional)</span></label>
      <input id="n-nome" placeholder="LEAFTIDE_AD01"></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="n-ok">Criar</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#n-ok').onclick = async () => {
      const b = v.querySelector('#n-ok');
      b.disabled = true; b.textContent = 'Lendo o vídeo…';
      try {
        const p = await post('/api/projetos', {
          video: v.querySelector('#n-video').value.trim(),
          nome: v.querySelector('#n-nome').value.trim(),
        });
        v.remove(); projetoAberto = p.id; desenhar();
      } catch (e) {
        b.disabled = false; b.textContent = 'Criar';
        toast(e.message, true);
      }
    };
  });
}

// ---------------------------------------------------------------- projeto

// ---------------------------------------------------------------- pipeline
const CORES_TIPO = { insert: 'var(--broll)', lettering: 'var(--lettering)', copy: 'var(--decisao)' };
const PILL = { pendente: '', em_geracao: 'aviso', aguardando_aprovacao: 'aviso',
               aprovado: 'ok', concluido: 'ok', rejeitado: 'erro' };

let etapaAberta = null;

let conversando = false;

async function telaProjeto() {
  const p  = await api('/api/projetos/' + projetoAberto);
  const pp = await api(`/api/projetos/${projetoAberto}/pipeline`);
  const cv = await api(`/api/projetos/${projetoAberto}/conversa`);
  const pl = p.plano, dur = pl.fonte.duracao || 1;
  const pct = Math.round((pp.concluidas / pp.total) * 100);

  moldura(`
    <div class="chat-tela">
      <div class="chat-col">
        <div class="chat-topo">
          <div>
            <h1>${esc(pl.job)}</h1>
            <p class="sub">${tc(dur)} · ${pl.fonte.largura}×${pl.fonte.altura} ·
              <b style="color:var(--ouro)">${pp.concluidas}/${pp.total} etapas</b></p>
          </div>
          <button class="bt discreto" id="voltar">← Projetos</button>
        </div>

        <div class="nota-beta">
          <span class="nota-icone">▸</span>
          <div>Conversa em teste. Com tudo conectado, <b>tarefas longas rendem mais
            pelo Claude Code no VS Code</b> — o app segue guardando projeto,
            aprovações e credenciais.</div>
        </div>
        <div class="conversa" id="conversa">
          ${cv.mensagens.length ? cv.mensagens.map(bolha).join('') : boasVindas(pp)}
          <div id="fim-conversa"></div>
        </div>

        <div class="compositor">
          <div id="anexos" class="anexos"></div>
          <div class="compositor-linha">
            <button class="bt discreto" id="anexar" title="Anexar arquivo">＋</button>
            <textarea id="entrada" rows="1"
              placeholder="Fale o que quer fazer… (Enter envia, Shift+Enter quebra linha)"></textarea>
            <button class="bt principal" id="enviar">Enviar</button>
          </div>
          ${seletorIA()}
          <div class="atalhos">
            ${atalhos(pp).map((a) => `<button class="atalho" data-diz="${esc(a)}">${esc(a)}</button>`).join('')}
          </div>
        </div>
      </div>

      <aside class="pipe-lateral">
        <div class="barra"><div class="barra-cheia" style="width:${pct}%"></div></div>
        <div class="rotulo" style="margin:14px 0 8px">Pipeline</div>
        ${pp.etapas.map((e) => `
          <div class="mini-etapa ${e.status} ${e.id === pp.atual ? 'atual' : ''}"
               data-diz="me mostre a etapa ${e.n}, ${esc(e.nome)}">
            <div class="etapa-n ${e.status}">${e.status === 'concluido' ? '✓' : e.n}</div>
            <div style="flex:1;min-width:0">
              <div class="mini-nome">${esc(e.nome)}</div>
              <div class="mini-status">${esc(e.rotulo)}</div>
            </div>
            ${e.gasta ? '<span class="credito">cr</span>' : ''}
          </div>`).join('')}
      </aside>
    </div>`);

  document.getElementById('palco').classList.add('modo-chat');
  document.getElementById('voltar').onclick = () => { projetoAberto = null; desenhar(); };
  ligarChat(p, pp);
  rolarFim();
}

function boasVindas(pp) {
  return `<div class="msg resposta"><div class="bolha">
    <p>Pronto pra começar. Eu conduzo as <b>12 etapas</b> e paro em cada uma
    esperando sua aprovação — <b>nada gasta crédito sem você autorizar</b>.</p>
    <p style="margin-top:8px">Pode falar normalmente: <i>"analisa esse material"</i>,
    <i>"compara com a copy"</i>, <i>"quanto custa gerar os b-rolls?"</i>,
    <i>"usa o motor mais barato"</i>.</p>
  </div></div>`;
}

// O seletor fica na barra do compositor, colado no campo — é ali que a pessoa
// decide "quem vai responder isto", no momento em que escreve. Fora dali vira
// configuração, e configuração ninguém troca no meio do trabalho.
function seletorIA() {
  if (!IA) return '';
  return `<div class="ia-seletor" id="ia-seletor">
    ${IA.provedores.map((p) => `
      <button class="ia-op ${p.id === IA.escolhido ? 'ativa' : ''} ${p.pronto ? '' : 'sem'}"
              data-ia="${p.id}" title="${esc(p.pronto ? p.ferramentas : p.msg)}">
        <i class="ia-ponto"></i>${esc(p.nome)}</button>`).join('')}
  </div>`;
}

function ligarSeletorIA() {
  document.querySelectorAll('[data-ia]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.ia;
      const p = (IA?.provedores || []).find((x) => x.id === id);
      if (p && !p.pronto) return pedirChaveIA(p);
      try {
        const r = await post('/api/ia/escolher', { provedor: id });
        IA = r.estado;
        document.querySelectorAll('[data-ia]').forEach((o) =>
          o.classList.toggle('ativa', o.dataset.ia === id));
        toast('Falando com ' + (p ? p.nome : id) + '.');
      } catch (e) { toast(e.message, true); }
    };
  });
}

// A chave vai direto para o .env do app (permissão de dono) e NUNCA fica no
// front-end: nem em localStorage, nem em variável de tela.
function pedirChaveIA(p) {
  if (p.id !== 'chatgpt') {
    toast(p.msg || 'Conecte esta IA na aba Contas.', true);
    aba = 'contas'; projetoAberto = null; desenhar();
    return;
  }
  // Entrar com a conta vem PRIMEIRO: quem assina o ChatGPT já paga pelo modelo,
  // e a chave de API cobraria de novo por fora pelo mesmo acesso.
  modal(`<h2>Conectar o ChatGPT</h2>
    <p class="sub" style="margin-bottom:14px">Entre com a <b>sua conta</b> — é a
      mesma assinatura que você já usa. Cada pessoa entra na conta dela.</p>
    <button class="bt principal" id="ch-login" style="width:100%">
      Entrar com a conta do ChatGPT</button>
    <p class="sub" style="font-size:11px;margin:8px 0 16px">Abre o Terminal com
      <code>codex login</code>; você autoriza no navegador e volta.</p>
    <div class="rotulo" style="margin-bottom:8px">ou pague por uso</div>
    <p class="sub" style="margin-bottom:10px;font-size:11px">Cole a chave da
      OpenAI. Ela é gravada em <code>${esc(IA.env)}</code>, só o seu usuário lê,
      e nunca sai desta máquina.</p>
    <div class="campo"><input id="ch" type="password" placeholder="sk-..."></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt" id="ch-ok">Usar chave</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#ch-login').onclick = async () => {
      const b = v.querySelector('#ch-login');
      b.disabled = true; b.textContent = 'Abrindo o Terminal…';
      try {
        const r = await post('/api/ia/entrar');
        toast(r.msg, !r.ok);
        if (r.ok) {
          await post('/api/ia/metodo', { metodo: 'sessao' });
          v.remove();
          // ⚠️ Era um `setTimeout` de 12s: um chute em quanto tempo alguém
          // demora para autorizar no navegador. Quem demorava 13 segundos
          // ficava com a tela dizendo "não conectado" para sempre. Agora fica
          // olhando até acontecer — e desiste com aviso, não em silêncio.
          esperarLogin('contas', 'ChatGPT', (d) =>
            ((d.ia && d.ia.provedores || []).find((x) => x.id === 'chatgpt') || {}).pronto);
        }
      } catch (e) { toast(e.message, true); }
      b.disabled = false; b.textContent = 'Entrar com a conta do ChatGPT';
    };
    v.querySelector('#ch-ok').onclick = async () => {
      const valor = v.querySelector('#ch').value.trim();
      if (!valor) return;
      const b = v.querySelector('#ch-ok');
      b.disabled = true; b.textContent = 'Conferindo…';
      try {
        await post('/api/ia/chave', { provedor: 'chatgpt', valor });
        await post('/api/ia/metodo', { metodo: 'chave' });
        const t = await post('/api/ia/testar', { provedor: 'chatgpt' });
        if (!t.ok) { toast(t.msg, true); b.disabled = false; b.textContent = 'Conectar'; return; }
        const r = await post('/api/ia/escolher', { provedor: 'chatgpt' });
        IA = r.estado; v.remove();
        await revalidar('contas', { silencioso: false,
          aviso: t.msg + ' Falando com ChatGPT.' });
        if (aba !== 'contas') desenhar();
      } catch (e) { toast(e.message, true); b.disabled = false; b.textContent = 'Conectar'; }
    };
  });
}

function atalhos(pp) {
  const e = pp.etapas.find((x) => x.id === pp.atual) || {};
  if (e.status === 'aguardando_aprovacao')
    return ['Aprovar e continuar', 'Gerar novamente', 'Editar instruções', 'O que mudou?'];
  if (e.gasta && e.pode)
    return ['Quanto vai custar?', 'Usa o motor mais barato', 'Pode gerar'];
  if (e.pode) return [`Rodar: ${e.nome}`, 'Onde estamos?'];
  return ['Onde estamos?', 'O que falta para destravar?'];
}

function bolha(m) {
  if (m.role === 'user') {
    return `<div class="msg eu"><div class="bolha">${esc(m.content)}</div></div>`;
  }
  if (m.role === 'ferramenta') {
    const s = m.saida || {};
    const ruim = s.recusado || s.erro;
    return `<div class="msg ferramenta">
      <div class="ferr ${ruim ? 'ruim' : ''}">
        <span class="ferr-nome">${esc(m.nome)}</span>
        ${s.recusado ? `<span class="ferr-txt">⛔ ${esc(s.porque)}</span>`
          : s.erro ? `<span class="ferr-txt">${esc(s.erro)}</span>`
          : `<span class="ferr-txt">${esc(resumoFerr(m.nome, s))}</span>`}
      </div></div>`;
  }
  const passos = (m.passos || []).filter((p) => p.tipo === 'ferramenta');
  const quem = m.provedor === 'chatgpt' ? 'ChatGPT' : m.provedor === 'claude' ? 'Claude' : '';
  return `<div class="msg resposta">
    ${passos.length ? `<div class="passos">${passos.map(passoHtml).join('')}</div>` : ''}
    <div class="bolha">${quem ? `<span class="quem-ia">${esc(quem)}</span>` : ''}${marcar(m.content || '')}</div></div>`;
}

function passoHtml(p) {
  // streaming: a resposta aparece enquanto é escrita, em vez de surgir pronta
  if (p.tipo === 'parcial') {
    return p.texto ? `<div class="bolha vivo">${marcar(p.texto)}</div>` : '';
  }
  if (p.tipo === 'pensando') return `<div class="passo pensando"><span class="passo-bola"></span>pensando…</div>`;
  if (p.tipo === 'aviso')    return `<div class="passo"><span class="passo-bola"></span>${esc(p.texto)}</div>`;
  if (p.tipo !== 'ferramenta') return '';
  const est = p.estado || 'rodando';
  return `<div class="passo ${est}">
    <span class="passo-bola"></span>
    <div style="flex:1;min-width:0">
      <div class="passo-nome">${esc(nomeFerr(p.nome))}${p.resumo ? `<span class="passo-arg">${esc(p.resumo)}</span>` : ''}</div>
      ${p.saida ? `<div class="passo-saida">${esc(p.saida)}</div>` : ''}
    </div>
    <span class="passo-est">${est === 'rodando' ? '' : est === 'ok' ? '✓' : '✕'}</span>
  </div>`;
}

// nomes de MCP vêm como mcp__servidor__ferramenta — mostrar só o que importa
function nomeFerr(n) {
  const m = String(n || '').match(/^mcp__([^_]+(?:_[^_]+)*)__(.+)$/);
  return m ? `${m[2]} · ${m[1]}` : String(n || '');
}

function resumoFerr(nome, s) {
  if (s.aprovada) return `${s.aprovada} aprovada → liberou ${s.proxima || 'o fim'}`;
  if (s.rodando) return 'gerando…';
  if (s.pronto) return 'pronto — aguardando sua aprovação';
  if (s.concluidas) return `${s.concluidas} etapas`;
  if (s.opcoes) return `${s.opcoes.length} motores · saldo ${Math.round(s.saldo_creditos || 0)} cr`;
  if (s.saldo) return JSON.stringify(s.saldo);
  return 'ok';
}

// negrito, itálico e código — o suficiente para o texto do modelo ficar legível
function marcar(t) {
  return esc(t)
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/(^|\s)\*([^*\n]+)\*/g, '$1<i>$2</i>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

// Erro técnico não vai para a tela. O usuário vê o que aconteceu e o que fazer.
// ⚠️ Esta tela mostrava SEMPRE a mesma frase e jogava fora o erro que o
// servidor tinha mandado. O usuário via "não está disponível" para seis causas
// diferentes — sessão ocupada, limite de uso, CLI faltando — e nenhuma delas
// dizia o que fazer. O motivo agora vem junto.
function mostrarFalha(ultimoTexto, motivo) {
  const c = document.getElementById('conversa');
  if (!c) return;
  const quem = IA?.escolhido === 'chatgpt' ? 'o ChatGPT' : 'o Claude';
  c.insertAdjacentHTML('beforeend', `
    <div class="msg resposta"><div class="bolha">
      <p>${motivo ? esc(motivo) : `A conexão com ${quem} não está disponível agora.`}</p>
      <div class="falha-acoes">
        <button class="bt" id="f-toolspro">Reconectar ao Tools PRO</button>
        ${IA?.escolhido === 'chatgpt' ? '' : `
          <button class="bt" id="f-reconectar">Reconectar</button>
          <button class="bt" id="f-trocar">Trocar conta</button>`}
        <button class="bt principal" id="f-tentar">Tentar novamente</button>
      </div>
    </div></div>`);
  rolarFim();
  const fr = document.getElementById('f-reconectar');
  if (fr) fr.onclick = async () => {
    const r = await post('/api/claude/testar');
    toast(r.msg, !r.ok);
    if (r.ok) desenhar();
  };
  const ft = document.getElementById('f-toolspro');
  if (ft) ft.onclick = () => reconectarToolsPro();
  const ftr = document.getElementById('f-trocar');
  if (ftr) ftr.onclick = () => trocarMetodo();
  document.getElementById('f-tentar').onclick = () => {
    const e = document.getElementById('entrada');
    if (e) { e.value = ultimoTexto || ''; document.getElementById('enviar').click(); }
  };
}

// ---------------------------------------------- "Pensando…" enquanto a IA não fala
/* A primeira mensagem chegou a levar 2 minutos sem NADA na tela: o macOS estava
   pedindo acesso a uma pasta, com a janela do sistema escondida, e o app
   parecia travado. Agora a tela mostra na hora que está trabalhando, há
   quanto tempo, em que ponto (quando o servidor diz), e depois de um tempo
   sem novidade explica o caso do pedido de permissão. */
const VIVO_AJUDA_MS = 10000;

function vivoEstadoHtml() {
  return `<div class="vivo-estado" id="vivo-estado" role="status" aria-live="polite">
      <span class="vivo-giro" aria-hidden="true"></span>
      <b>Pensando…</b>
      <span class="vivo-tempo" id="vivo-tempo">0 s</span>
      <span class="vivo-etapa" id="vivo-etapa"></span>
      <button class="bt discreto vivo-cancelar" id="vivo-cancelar" hidden>Cancelar</button>
    </div>
    <div class="vivo-ajuda" id="vivo-ajuda" hidden>Se o macOS pedir acesso a uma pasta, clique em
      <b>Permitir</b> — a resposta continua depois disso.</div>`;
}

function tempoCurto(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
}

// em que ponto está: a ferramenta rodando agora vence a etapa do servidor
function etapaAtual(s) {
  const ps = (s && s.passos) || [];
  for (let i = ps.length - 1; i >= 0; i--) {
    if (ps[i].tipo === 'ferramenta' && (ps[i].estado || 'rodando') === 'rodando') return 'usando ' + nomeFerr(ps[i].nome);
  }
  return (s && s.etapa) || '';
}

function acompanharVivo() {
  const inicio = Date.now();
  let marca = inicio;          // última novidade: passo novo, etapa nova
  let assinatura = '';
  const ctl = { tarefa: null };
  const pintar = () => {
    const t = document.getElementById('vivo-tempo');
    if (!t) return;
    t.textContent = tempoCurto(Date.now() - inicio);
    const aj = document.getElementById('vivo-ajuda');
    if (aj) aj.hidden = Date.now() - marca < VIVO_AJUDA_MS;
  };
  const relogio = setInterval(pintar, 1000);
  ctl.atualizar = (s) => {
    const ps = (s && s.passos) || [];
    const ass = ps.length + '|' + ps.map((p) => p.estado || '').join(',') + '|' + ((s && s.etapa) || '');
    if (ass !== assinatura) { assinatura = ass; marca = Date.now(); }
    const et = document.getElementById('vivo-etapa');
    const txt = etapaAtual(s);
    if (et) et.textContent = txt ? '· ' + txt : '';
    // só existe Cancelar quando o servidor diz que há um processo para encerrar
    const b = document.getElementById('vivo-cancelar');
    if (b) b.hidden = !(s && s.cancelavel) || b.dataset.pedido === '1';
    pintar();
  };
  ctl.parar = () => clearInterval(relogio);
  const b = document.getElementById('vivo-cancelar');
  if (b) b.onclick = async () => {
    if (!ctl.tarefa) return;
    b.dataset.pedido = '1'; b.hidden = true;
    const et = document.getElementById('vivo-etapa');
    if (et) et.textContent = '· cancelando…';
    try {
      const r = await post('/api/tarefas/' + ctl.tarefa + '/cancelar');
      if (!r.ok) { toast(r.msg || 'Não deu para cancelar.', true); b.dataset.pedido = ''; }
    } catch (e) { toast(e.message, true); b.dataset.pedido = ''; }
  };
  pintar();
  return ctl;
}

const rolarFim = () => {
  const c = document.getElementById('conversa');
  if (c) c.scrollTop = c.scrollHeight;
};

function ligarChat(p, pp) {
  const entrada = document.getElementById('entrada');
  const anexos = [];

  const crescer = () => {
    entrada.style.height = 'auto';
    entrada.style.height = Math.min(entrada.scrollHeight, 160) + 'px';
  };
  entrada.oninput = crescer;

  const enviar = async () => {
    const texto = entrada.value.trim();
    if ((!texto && !anexos.length) || conversando) return;
    conversando = true;
    entrada.value = ''; crescer();

    const c = document.getElementById('conversa');
    c.insertAdjacentHTML('beforeend',
      `<div class="msg eu"><div class="bolha">${esc(texto)}</div></div>
       <div class="msg resposta" id="vivo"><div class="passos" id="passos-vivos"></div>${vivoEstadoHtml()}</div>`);
    rolarFim();
    // "Pensando…" na HORA do Enter, antes de qualquer resposta do servidor
    const vivo = acompanharVivo();

    try {
      const r = await post('/api/conversa',
        { texto, anexos, conversa: conversaAtual, provedor: IA?.escolhido });
      vivo.tarefa = r.tarefa;
      let desenhados = 0;
      const t = setInterval(async () => {
        let s;
        try { s = await api('/api/tarefas/' + r.tarefa); } catch (_) { return; }
        vivo.atualizar(s);
        const cx = document.getElementById('passos-vivos');
        if (cx) {
          // redesenha só o que mudou: o passo em curso vira ✓ quando termina
          const html = (s.passos || []).map(passoHtml).join('');
          if (html !== cx.dataset.ultimo) {
            cx.innerHTML = html; cx.dataset.ultimo = html;
            if ((s.passos || []).length !== desenhados) { desenhados = s.passos.length; rolarFim(); }
          }
        }
        if (s.estado === 'pronto') { clearInterval(t); vivo.parar(); conversando = false; desenhar(); }
        else if (s.estado === 'cancelado') {
          clearInterval(t); vivo.parar(); conversando = false;
          const v = document.getElementById('vivo');
          if (v) v.outerHTML = `<div class="msg resposta"><div class="passo cancelado"><span class="passo-bola"></span>
            Cancelado. Esta mensagem não foi guardada no histórico — o texto voltou para a caixa.</div></div>`;
          const e = document.getElementById('entrada');
          if (e && !e.value) { e.value = texto; crescer(); }
        }
        else if (s.estado === 'erro') {
          clearInterval(t); vivo.parar(); conversando = false;
          const v = document.getElementById('vivo');
          if (v) v.remove();
          mostrarFalha(texto, s.erro);
        }
      }, 900);
    } catch (e) {
      vivo.parar(); conversando = false; toast(e.message, true); desenhar();
    }
  };

  document.getElementById('enviar').onclick = enviar;
  entrada.onkeydown = (ev) => {
    if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); enviar(); }
  };

  document.querySelectorAll('[data-diz]').forEach((b) => {
    b.onclick = () => { entrada.value = b.dataset.diz; enviar(); };
  });

  document.getElementById('anexar').onclick = () => {
    modal(`<h2>Anexar arquivo</h2>
      <p class="sub" style="margin-bottom:12px">Cole o caminho do arquivo — copy, b-roll,
        referência. Ele fica no seu disco; nada sobe.</p>
      <div class="campo"><input id="ax" placeholder="~/Documents/.../copy.txt"></div>
      <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
        <button class="bt principal" id="ax-ok">Anexar</button></div>`, (v) => {
      v.querySelector('[data-fechar]').onclick = () => v.remove();
      v.querySelector('#ax-ok').onclick = () => {
        const a = v.querySelector('#ax').value.trim();
        if (a) {
          anexos.push(a);
          document.getElementById('anexos').innerHTML = anexos.map((x) =>
            `<span class="anexo">${esc(x.split('/').pop())}</span>`).join('');
        }
        v.remove(); entrada.focus();
      };
    });
  };

  ligarSeletorIA();
  entrada.focus();
}

const nomeEtapa = (pp, id) => (pp.etapas.find((e) => e.id === id) || {}).nome || id;

function cartaoEtapa(e, pp) {
  const aberta = e.id === etapaAberta;
  const dados = (pp.dados || {})[e.id] || {};
  return `
  <div class="etapa-cartao ${aberta ? 'aberta' : ''} ${e.status}" data-etapa="${e.id}">
    <div class="etapa-cab" data-abrir-etapa="${e.id}">
      <div class="etapa-n ${e.status}">${e.status === 'concluido' ? '✓' : e.n}</div>
      <div style="flex:1;min-width:0">
        <div class="etapa-nome">${esc(e.nome)}
          ${e.gasta ? '<span class="credito" title="Esta etapa gasta crédito">gasta crédito</span>' : ''}
          ${e.portao ? '<span class="credito portao">portão</span>' : ''}
        </div>
        <div class="etapa-resumo">${esc(e.resumo)}</div>
      </div>
      <span class="pastilha ${PILL[e.status] || ''}"><i class="ponto"></i>${esc(e.rotulo)}</span>
    </div>
    ${aberta ? `<div class="etapa-corpo">
      ${!e.pode && e.status === 'pendente'
        ? `<div class="aviso ruim">⛔ ${esc(e.bloqueio)}</div>`
        : corpoEtapa(e, dados)}
      ${acoesEtapa(e)}
    </div>` : ''}
  </div>`;
}

function corpoEtapa(e, d) {
  if (e.status === 'pendente') {
    return `<p class="sub">Pronta para rodar.${e.gasta
      ? ' <b style="color:var(--ouro)">Esta etapa consome crédito das suas contas.</b>' : ''}</p>`;
  }
  if (e.status === 'em_geracao') return `<p class="sub pulsando">Rodando…</p>`;

  switch (e.id) {
    case 'analise':  return corpoAnalise(d);
    case 'copy':     return corpoCopy(d);
    case 'marcacao': return corpoMarcacao(d);
    case 'plano':    return corpoPlano(d);
    case 'avatar':
    case 'imagens':
    case 'animacao':
      return corpoGerado(e, d);
    case 'montagem': return corpoMontagem(d);
    case 'qc':       return corpoQC(d);
    default:
      return e.por_item ? corpoItens(e, d)
        : `<pre class="portao">${esc(JSON.stringify(d, null, 1)).slice(0, 1600)}</pre>`;
  }
}

function corpoAnalise(d) {
  if (!d.projeto) return '<p class="sub">Sem dados.</p>';
  return `
    <div class="fatos">
      <div><span class="rotulo">Formato</span><b style="color:${d.formato_ok ? 'var(--ok)' : 'var(--ouro)'}">${esc(d.formato)}</b></div>
      <div><span class="rotulo">Geometria</span><b>${esc(d.geometria)}</b></div>
      <div><span class="rotulo">Duração</span><b>${tc(d.duracao)}</b></div>
      <div><span class="rotulo">Copy na pasta</span><b>${d.arquivos.copy.length || '—'}</b></div>
    </div>
    <p class="sub" style="margin-top:12px;font-size:12px">${esc(d.pasta)}</p>
    ${(d.alertas || []).map((a) => `<div class="aviso" style="margin-top:8px">${esc(a)}</div>`).join('')}`;
}

function corpoCopy(d) {
  if (!d.veredito) return '<p class="sub">Sem dados.</p>';
  const cor = d.cobertura >= 95 ? 'var(--ok)' : d.cobertura >= 80 ? 'var(--ouro)' : 'var(--broll)';
  return `
    <div class="fatos">
      <div><span class="rotulo">Copy × fala</span><b style="color:${cor}">${d.cobertura}%</b></div>
      <div><span class="rotulo">Divergências</span><b>${(d.divergencias || []).length}</b></div>
      <div><span class="rotulo">Graves</span><b style="color:${d.graves ? 'var(--broll)' : 'var(--ok)'}">${d.graves}</b></div>
      <div><span class="rotulo">Repetições</span><b style="color:${(d.repeticoes||[]).length ? 'var(--broll)' : 'inherit'}">${(d.repeticoes || []).length}</b></div>
    </div>
    <div class="aviso" style="margin-top:12px">${esc(d.veredito)}</div>
    ${(d.repeticoes || []).length ? `<div class="rotulo" style="margin-top:16px">Repetições — bug clássico de geração</div>
      ${d.repeticoes.map((r) => `<div class="diverg"><span class="tc">${tc(r.t)}</span>
        <span style="color:var(--broll)">"${esc(r.trecho)}" aparece duas vezes seguidas</span></div>`).join('')}` : ''}
    ${(d.divergencias || []).length ? `<div class="rotulo" style="margin-top:16px">Divergências</div>
      <div class="rolagem">${d.divergencias.map((x) => `
        <div class="diverg ${x.grave ? 'grave' : ''}">
          <span class="tc">${tc(x.t)}</span>
          <span class="dtipo ${x.tipo}">${x.tipo}</span>
          <span>${x.copy ? `<s style="color:var(--texto-3)">${esc(x.copy)}</s> ` : ''}${x.falado ? esc(x.falado) : ''}</span>
        </div>`).join('')}</div>` : ''}`;
}

function corpoMarcacao(d) {
  if (!d.itens) return '<p class="sub">Sem dados.</p>';
  const dur = d.duracao || 1;
  return `
    <div class="regua">${d.itens.map((i) => {
      const esq = (i.inicio / dur) * 100, larg = Math.max(0.7, ((i.fim - i.inicio) / dur) * 100);
      return `<div class="faixa" style="left:${esq}%;width:${larg}%;background:${CORES_TIPO[i.tipo]}"
              title="${esc(i.intencao)}"></div>`;
    }).join('')}</div>
    <div class="legenda-cores">
      <span><i style="background:var(--broll)"></i>vermelho · b-roll (${d.por_cor.vermelho})</span>
      <span><i style="background:var(--lettering)"></i>azul · lettering (${d.por_cor.azul})</span>
      <span><i style="background:var(--decisao)"></i>roxo · decisão (${d.por_cor.roxo})</span>
      <span style="margin-left:auto">cobertura ${d.cobertura}%</span>
    </div>
    ${(d.sem_fala || []).length ? `<div class="aviso" style="margin-top:12px">
      ${d.sem_fala.length} marcador(es) sem fala que os justifique: ${esc(d.sem_fala.join(', '))}</div>` : ''}
    <div class="rolagem" style="margin-top:12px">
      ${d.itens.map((i) => `<div class="beat">
        <div class="tc">${tc(i.inicio)}</div>
        <div class="tipo" style="background:${CORES_TIPO[i.tipo]}"></div>
        <div><div class="intencao">${esc(i.intencao || '—')}</div>
          ${i.fala ? `<div class="fala">"${esc(i.fala)}"</div>` : ''}</div>
      </div>`).join('')}
    </div>`;
}

function corpoPlano(d) {
  if (!d.portao) return '<p class="sub">Sem dados.</p>';
  return `
    <div class="aviso ${d.liberado_pela_regra ? '' : 'ruim'}">
      ${d.liberado_pela_regra ? '✓ A regra liberou. Sua aprovação abre a geração visual.'
                              : '⛔ A regra apontou bloqueio — leia abaixo antes de aprovar.'}
    </div>
    <div class="fatos" style="margin-top:12px">
      <div><span class="rotulo">Estilo</span><b style="color:var(--ouro)">${esc(d.estilo)}</b></div>
      <div><span class="rotulo">A gerar</span><b>${(d.a_gerar || []).length} insert(s)</b></div>
      <div><span class="rotulo">Custo previsto</span><b>${esc(d.custo_previsto)}</b></div>
    </div>
    <div class="portao" style="margin-top:12px">${esc(d.portao)}</div>`;
}

function corpoItens(e, d) {
  const itens = d.itens || [];
  if (!itens.length) return '<p class="sub">Nada gerado ainda.</p>';
  const s = e.saldo || {};
  return `
    <div class="fatos">
      <div><span class="rotulo">Aprovados</span><b style="color:var(--ok)">${s.aprovados || 0}</b></div>
      <div><span class="rotulo">Rejeitados</span><b style="color:var(--broll)">${s.rejeitados || 0}</b></div>
      <div><span class="rotulo">Regerar</span><b style="color:var(--ouro)">${s.regerar || 0}</b></div>
      <div><span class="rotulo">Pendentes</span><b>${s.pendentes || 0}</b></div>
    </div>
    <p class="sub" style="margin:12px 0 8px">Somente os aprovados seguem para a etapa seguinte.</p>
    <div class="galeria">
      ${itens.map((it) => `<div class="item ${it.julgamento || ''}">
        <div class="item-id">${esc(it.id)}</div>
        <div class="item-acoes">
          <button class="bt discreto" data-item="${e.id}|${it.id}|aprovou" title="Aprovar">✓</button>
          <button class="bt discreto" data-item="${e.id}|${it.id}|regerar" title="Nova versão">↻</button>
          <button class="bt discreto perigo" data-item="${e.id}|${it.id}|rejeitou" title="Rejeitar">✕</button>
        </div>
        ${it.julgamento ? `<div class="item-selo ${it.julgamento}">${esc(it.julgamento)}</div>` : ''}
      </div>`).join('')}
    </div>`;
}

function corpoGerado(e, d) {
  const itens = d.itens || [];
  if (!itens.length) return '<p class="sub">Nada gerado ainda.</p>';
  const motores = [...new Set(itens.map((i) => i.modelo).filter(Boolean))];
  return `
    <div class="fatos">
      <div><span class="rotulo">Gerados</span><b>${itens.length}</b></div>
      <div><span class="rotulo">Motor</span><b>${esc(d.motor || motores.join(', ') || '—')}</b></div>
      <div><span class="rotulo">Crédito gasto</span><b style="color:var(--ouro)">${d.custo_gasto ?? '—'} cr</b></div>
    </div>
    ${itens[0] && itens[0].porque ? `<p class="sub" style="margin-top:10px;font-size:12px">
      escolha do motor: ${esc(itens[0].porque)}</p>` : ''}
    <div class="galeria" style="margin-top:12px">
      ${itens.map((it) => `<div class="item">
        <div class="item-id">${esc(it.id)}</div>
        ${it.modelo ? `<div class="sub" style="font-size:10px">${esc(it.modelo)}</div>` : ''}
      </div>`).join('')}
    </div>`;
}

function corpoMontagem(d) {
  if (!d.sequencia) return '<p class="sub">Sem dados.</p>';
  const c = d.conferido || {};
  const p = d.punch || {};
  const ok = d.inserts_postos === d.inserts_pedidos;
  return `
    <div class="fatos">
      <div><span class="rotulo">Sequência</span><b>${esc(d.sequencia)}</b></div>
      <div><span class="rotulo">B-roll na ${esc(d.trilha_apoio)}</span>
        <b style="color:${ok ? 'var(--ok)' : 'var(--broll)'}">${d.inserts_postos}/${d.inserts_pedidos}</b></div>
      <div><span class="rotulo">Punch</span><b>${p.pulado ? '—' : (p.clipes || []).filter((x) => x.ok).length + ' clipe(s)'}</b></div>
      <div><span class="rotulo">Marcadores</span><b>${(d.marcadores || {}).conferidos ?? 0}</b></div>
    </div>
    <p class="sub" style="margin-top:10px;font-size:12px">
      Lido de volta do Premiere: ${c.clipes ?? '—'} clipe(s), ${c.trilhas_video ?? '—'}V/${c.trilhas_audio ?? '—'}A,
      ${c.marcadores ?? '—'} marcador(es). ${esc(d.audio_do_broll)}.</p>
    <div class="rolagem" style="margin-top:12px">
      ${(d.itens || []).map((i) => `<div class="beat">
        <div class="tc">${i.ok ? tc(i.entra) : '—'}</div>
        <div class="tipo" style="background:${i.ok ? (i.curto ? 'var(--ouro)' : 'var(--ok)') : 'var(--broll)'}"></div>
        <div><div class="intencao">${esc(i.id)} ${i.ok ? `· ${i.durou}s de ${i.pedido}s pedidos` : '· não entrou'}</div>
          ${i.motivo ? `<div class="fala">${esc(i.motivo)}</div>` : ''}</div>
      </div>`).join('')}
    </div>
    ${(d.alertas || []).map((a) => `<div class="aviso" style="margin-top:8px">${esc(a)}</div>`).join('')}`;
}

function corpoQC(d) {
  if (!d.veredito) return '<p class="sub">Sem dados.</p>';
  const t = d.timeline || {}, a = d.arquivo || {};
  const cor = d.graves ? 'var(--broll)' : d.atencoes ? 'var(--ouro)' : 'var(--ok)';
  return `
    <div class="aviso ${d.graves ? 'ruim' : ''}">${esc(d.veredito)}</div>
    <div class="fatos" style="margin-top:12px">
      <div><span class="rotulo">Graves</span><b style="color:${cor}">${d.graves}</b></div>
      <div><span class="rotulo">Atenção</span><b>${d.atencoes}</b></div>
      <div><span class="rotulo">Cobertura</span><b>${t.cobertura != null ? t.cobertura + '%' : '—'}</b></div>
      <div><span class="rotulo">Maior vão</span><b>${t.maior_vao != null ? tc(t.maior_vao) : '—'}</b></div>
    </div>
    ${a.geometria ? `<p class="sub" style="margin-top:10px;font-size:12px">
      Export: ${esc(a.geometria)} · ${tc(a.duracao)} · ${esc(a.arquivo.split('/').pop())}</p>` : ''}
    ${a.mosaico ? `<img class="qc-mosaico" src="/api/arquivo?p=${encodeURIComponent(a.mosaico)}&t=${TOKEN}" alt="quadros do export">` : ''}
    <div class="rolagem" style="margin-top:12px">
      ${(d.achados || []).map((x) => `<div class="diverg ${x.severidade === 'grave' ? 'grave' : ''}">
        <span class="tc">${x.onde != null ? tc(x.onde) : '—'}</span>
        <span class="dtipo ${x.severidade === 'grave' ? 'ausente' : 'trocado'}">${x.severidade}</span>
        <span><b>${esc(x.o_que)}</b>${x.detalhe ? ' — ' + esc(x.detalhe) : ''}</span>
      </div>`).join('') || '<p class="sub">Nada a apontar.</p>'}
    </div>`;
}

function acoesEtapa(e) {
  const b = [];
  if (e.status === 'pendente' && e.pode) {
    b.push(`<button class="bt principal" data-rodar="${e.id}">
      ${e.gasta ? 'Gerar — consome crédito' : 'Rodar etapa'}</button>`);
  }
  if (e.status === 'aguardando_aprovacao' || e.status === 'rejeitado') {
    b.push(`<button class="bt principal" data-aprovar="${e.id}">Aprovar e liberar a próxima</button>`);
    b.push(`<button class="bt perigo" data-rejeitar="${e.id}">Rejeitar</button>`);
    if (e.status === 'rejeitado') b.push(`<button class="bt" data-rodar="${e.id}">Rodar de novo</button>`);
  }
  if (e.status === 'concluido') {
    b.push(`<button class="bt discreto" data-reabrir="${e.id}">Reabrir esta etapa</button>`);
  }
  return b.length ? `<div class="etapa-acoes">${b.join('')}</div>` : '';
}

function ligarEtapas(p, pp, dur) {
  document.querySelectorAll('[data-abrir-etapa]').forEach((c) => {
    c.onclick = () => {
      etapaAberta = etapaAberta === c.dataset.abrirEtapa ? null : c.dataset.abrirEtapa;
      desenhar();
    };
  });

  const chamar = async (rota, corpo, bt) => {
    if (bt) { bt.disabled = true; bt.textContent = '…'; }
    try { await post(rota, corpo || {}); desenhar(); }
    catch (err) { toast(err.message, true); desenhar(); }
  };

  document.querySelectorAll('[data-rodar]').forEach((b) => {
    b.onclick = async (ev) => {
      ev.stopPropagation();
      const eid = b.dataset.rodar;
      const e = pp.etapas.find((x) => x.id === eid);
      if (eid === 'copy') return pedirCopy(p.id, p.transcricao);
      if (eid === 'marcacao' && !(p.plano.beats || []).length) return telaBeat(p, dur);
      if (e.gasta) {
        return confirmarGasto(e, p.id, (corpo) => {
          if (eid === 'avatar') return pedirAvatar(p.id, corpo);
          rodarLonga(p.id, eid, { ...corpo, ancora: ancoraEscolhida(pp) }, e.nome);
        });
      }
      chamar(`/api/projetos/${p.id}/etapa/${eid}/iniciar`, {}, b);
    };
  });

  document.querySelectorAll('[data-aprovar]').forEach((b) => {
    b.onclick = (ev) => { ev.stopPropagation();
      pedirNota('Aprovar etapa', 'Observação (opcional)', (nota) =>
        chamar(`/api/projetos/${p.id}/etapa/${b.dataset.aprovar}/aprovar`, { nota })); };
  });
  document.querySelectorAll('[data-rejeitar]').forEach((b) => {
    b.onclick = (ev) => { ev.stopPropagation();
      pedirNota('Rejeitar etapa', 'O que precisa mudar?', (nota) =>
        chamar(`/api/projetos/${p.id}/etapa/${b.dataset.rejeitar}/rejeitar`, { nota })); };
  });
  document.querySelectorAll('[data-reabrir]').forEach((b) => {
    b.onclick = (ev) => { ev.stopPropagation();
      const eid = b.dataset.reabrir;
      const depois = pp.etapas.filter((x) => x.n > (pp.etapas.find((y) => y.id === eid) || {}).n
                                              && x.status !== 'pendente');
      pedirNota('Reabrir etapa',
        depois.length ? `Isto derruba ${depois.length} etapa(s) já feitas — inclusive material já gerado. Por quê?`
                      : 'Por que está reabrindo?',
        (nota) => chamar(`/api/projetos/${p.id}/etapa/${eid}/reabrir`, { nota })); };
  });

  document.querySelectorAll('[data-item]').forEach((b) => {
    b.onclick = (ev) => {
      ev.stopPropagation();
      const [eid, item, acao] = b.dataset.item.split('|');
      chamar(`/api/projetos/${p.id}/etapa/${eid}/item`, { item, acao });
    };
  });
}

async function confirmarGasto(e, pid, seguir) {
  const tipo = e.id === 'animacao' ? 'video' : 'imagem';
  const v = modal(`<h2>${esc(e.nome)}</h2>
    <p class="sub" style="margin-bottom:14px">Esta etapa consome crédito das <b>suas</b> contas.
      Escolha o motor — a diferença entre o mais barato e o mais caro passa de 3×.</p>
    <div id="motores" class="sub pulsando">consultando preços…</div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="g-ok" disabled>Gerar</button></div>`);
  v.querySelector('[data-fechar]').onclick = () => v.remove();

  let quantos = 1;
  try {
    const pp = await api(`/api/projetos/${pid}/pipeline`);
    const marc = (pp.dados || {}).marcacao || {};
    quantos = e.id === 'avatar' ? 3
      : (marc.por_cor ? marc.por_cor.vermelho : 1) || 1;
  } catch (_) {}

  let dados;
  try {
    dados = await api(`/api/projetos/${pid}/motores/${tipo}?q=${quantos}`);
  } catch (err) {
    v.querySelector('#motores').innerHTML = `<div class="aviso ruim">${esc(err.message)}</div>`;
    return;
  }

  let escolhido = (dados.opcoes.find((o) => o.sugerido) || dados.opcoes[0]).id;

  const pinta = () => {
    const sel = dados.opcoes.find((o) => o.id === escolhido) || {};
    const total = sel.total;
    const falta = dados.saldo != null && total != null && total > dados.saldo;
    v.querySelector('#motores').innerHTML = `
      <div class="motores">
        ${dados.opcoes.map((o) => `
          <label class="motor ${o.id === escolhido ? 'ativo' : ''}">
            <input type="radio" name="motor" value="${o.id}" ${o.id === escolhido ? 'checked' : ''}>
            <div style="flex:1;min-width:0">
              <div class="motor-nome">${esc(o.nome)}
                ${o.sugerido ? '<span class="credito">sugerido</span>' : ''}
                ${o.perde_ancora ? '<span class="credito" style="background:rgba(229,72,77,.14);color:#FF9599">perde a âncora</span>' : ''}
              </div>
              <div class="motor-nota">${esc(o.nota)}</div>
            </div>
            <div class="motor-preco">
              ${o.preco_na_hora ? '<span class="sub" style="font-size:11px">preço na hora</span>'
                : `<b>${o.credito}</b><span>cr cada</span>
                   <div class="motor-total">${o.total} total</div>`}
            </div>
          </label>`).join('')}
      </div>
      <div class="resumo-gasto ${falta ? 'ruim' : ''}">
        <div><span class="rotulo">Vai gerar</span><b>${quantos} item(ns)</b></div>
        <div><span class="rotulo">Custo estimado</span><b>${total != null ? total + ' cr' : '—'}</b></div>
        <div><span class="rotulo">Seu saldo</span><b>${dados.saldo != null ? Math.round(dados.saldo) + ' cr' : '—'}</b></div>
      </div>
      ${falta ? '<div class="aviso ruim" style="margin-top:10px">Seu saldo não cobre esta geração.</div>' : ''}`;

    v.querySelectorAll('input[name=motor]').forEach((r) => {
      r.onchange = () => { escolhido = r.value; pinta(); };
    });
    v.querySelector('#g-ok').disabled = false;
    v.querySelector('#g-ok').textContent = total != null ? `Gerar — ${total} cr` : 'Gerar';
  };
  pinta();

  v.querySelector('#g-ok').onclick = () => { v.remove(); seguir({ motor: escolhido }); };
}

async function rodarLonga(pid, eid, corpo, nome) {
  const v = modal(`<h2>${esc(nome)}</h2>
    <p class="sub">Chamando as plataformas. Não feche o app — o crédito já saiu
      e fechar no meio perde o que foi gerado.</p>
    <div class="portao" id="log" style="margin-top:14px;max-height:220px">iniciando…</div>`);
  try {
    const r = await post(`/api/projetos/${pid}/etapa/${eid}/iniciar`, corpo || {});
    if (!r.tarefa) { v.remove(); return desenhar(); }
    const log = v.querySelector('#log');
    const t = setInterval(async () => {
      const s = await api('/api/tarefas/' + r.tarefa);
      log.textContent = (s.log || []).join('\n') || 'processando…';
      log.scrollTop = log.scrollHeight;
      if (s.estado === 'pronto') { clearInterval(t); v.remove(); toast('Pronto — revise e aprove.'); desenhar(); }
      else if (s.estado === 'erro') { clearInterval(t); v.remove(); toast(s.erro, true); desenhar(); }
    }, 1500);
  } catch (err) { v.remove(); toast(err.message, true); desenhar(); }
}

function pedirNota(titulo, dica, seguir) {
  modal(`<h2>${esc(titulo)}</h2>
    <div class="campo"><label>${esc(dica)}</label><textarea id="nota" rows="3"></textarea></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="n-ok">Confirmar</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#n-ok').onclick = () => {
      const n = v.querySelector('#nota').value.trim(); v.remove(); seguir(n);
    };
  });
}

function pedirCopy(pid, tr) {
  // A verificação compara com a fala REAL — sem transcrição não há o que comparar.
  // Em vez de deixar a etapa falhar com erro, oferece o passo que falta.
  if (!tr || !tr.tem) {
    return modal(`<h2>Falta transcrever a fala</h2>
      <p class="sub" style="margin-bottom:14px">A verificação compara a copy com a
        <b>fala real</b>. Preciso transcrever o body primeiro — Whisper local,
        nada sobe para lugar nenhum.</p>
      <div class="acoes"><button class="bt discreto" data-fechar>Agora não</button>
        <button class="bt principal" id="d-ok">Transcrever agora</button></div>`, (v) => {
      v.querySelector('[data-fechar]').onclick = () => v.remove();
      v.querySelector('#d-ok').onclick = () => { v.remove(); rodarDecupagem(pid); };
    });
  }
  modal(`<h2>Verificação da copy</h2>
    <p class="sub" style="margin-bottom:14px">Cole a copy aprovada. Vou comparar com a fala
      real transcrita e apontar divergências, repetições e trechos ausentes.</p>
    <div class="campo"><textarea id="cp" rows="9" placeholder="Cole aqui a copy…"></textarea></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="cp-ok">Comparar</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#cp-ok').onclick = async () => {
      const bt = v.querySelector('#cp-ok'); bt.disabled = true; bt.textContent = 'Comparando…';
      try {
        await post(`/api/projetos/${pid}/etapa/copy/iniciar`, { texto: v.querySelector('#cp').value });
        v.remove(); desenhar();
      } catch (e) { bt.disabled = false; bt.textContent = 'Comparar'; toast(e.message, true); }
    };
  });
}

function telaBeat(p, dur) {
  modal(`<h2>Novo beat</h2>
    <div class="campo"><label>Tipo</label>
      <select id="b-tipo">
        <option value="insert">insert — b-roll cobrindo a fala</option>
        <option value="lettering">lettering — texto na tela</option>
        <option value="copy">copy — decisão humana / compliance</option>
      </select></div>
    <div class="grade dois" style="margin-top:12px">
      <div><label>Entra (s)</label><input id="b-ini" type="number" step="0.1" value="0"></div>
      <div><label>Sai (s)</label><input id="b-fim" type="number" step="0.1" value="4"></div>
    </div>
    <div class="campo"><label>Intenção — o que precisa aparecer na tela</label>
      <input id="b-int" placeholder="ela aparece de outra roupa"></div>
    <div class="campo"><label>Mídia <span style="color:var(--texto-3)">(vazio = ainda vai gerar)</span></label>
      <input id="b-mid" placeholder="broll/B1.mp4"></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="b-ok">Adicionar</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#b-ok').onclick = async () => {
      const pl = p.plano;
      const tipo = v.querySelector('#b-tipo').value;
      const ini = +v.querySelector('#b-ini').value, fim = +v.querySelector('#b-fim').value;
      if (!(fim > ini)) { toast('O beat precisa terminar depois de começar.', true); return; }
      if (fim > dur) { toast('Esse beat passa do fim do vídeo.', true); return; }
      const n = { id: tipo[0].toUpperCase() + (pl.beats.length + 1), tipo, inicio: ini, fim,
                  intencao: v.querySelector('#b-int').value.trim() };
      const mid = v.querySelector('#b-mid').value.trim();
      if (tipo === 'insert') n.midia = mid || null;
      if (tipo === 'lettering') n.texto = n.intencao;
      pl.beats.push(n);
      pl.beats.sort((a, b) => a.inicio - b.inicio);
      try {
        await post(`/api/projetos/${p.id}/plano`, { plano: pl });
        v.remove(); desenhar();
      } catch (e) { toast(e.message, true); }
    };
  });
}

async function rodarDecupagem(pid) {
  const v = modal(`<h2>Decupando a fala</h2>
    <p class="sub">Whisper local, palavra por palavra. Nada sobe para lugar nenhum.</p>
    <div class="portao" id="log" style="margin-top:14px;max-height:200px">iniciando…</div>`);
  try {
    const { tarefa } = await post(`/api/projetos/${pid}/decupar`, { modelo: 'medium' });
    const log = v.querySelector('#log');
    const timer = setInterval(async () => {
      const t = await api('/api/tarefas/' + tarefa);
      log.textContent = (t.log || []).join('\n') || 'processando o áudio…';
      if (t.estado === 'pronto') {
        clearInterval(timer); v.remove();
        toast(`Decupagem pronta — ${t.resultado.palavras} palavras.`); desenhar();
      } else if (t.estado === 'erro') {
        clearInterval(timer); v.remove(); toast(t.erro, true);
      }
    }, 1200);
  } catch (e) { v.remove(); toast(e.message, true); }
}

// ---------------------------------------------------------------- contas
async function telaContas() {
  // Nunca de `E`: `E` é a foto do arranque. Se ainda não há retrato, espera o
  // primeiro (com esqueleto na tela); se já há, pinta na hora e reconfere atrás.
  if (!SVC) {
    esqueleto('Contas', 'Conferindo o que está conectado nesta máquina…');
    const r = await revalidar('contas');
    if (!r.ok && !SVC) return telaErroEstado('Contas', r.erro, 'contas');
  } else {
    revalidarSeVelho('contas');
  }
  const s = SVC;
  const outros = s.servicos.filter((x) => x.id !== 'claude');
  moldura(`
    ${cabecalho('contas', barraEstado('contas'))}
    ${s.cofre === 'arquivo' ? `<div class="aviso" style="margin-bottom:16px">
        O cofre do sistema não está disponível — as chaves ficam num arquivo protegido.</div>` : ''}

    <section class="grupo">
      <div class="grupo-cab">
        <h2>Sua conta Editor Black Belt</h2>
        <p class="sub">É ela que libera o app, o plugin e as aulas.</p>
      </div>
      <div class="surf lista-servicos">
        <div class="servico">
          <div class="sv-marca conta">${esc(iniciais(E?.conta?.nome || ''))}</div>
          <div class="sv-corpo">
            <div class="titulo">${esc(E?.conta?.nome || 'Sua conta')}
              <span class="chip ok"><i class="ponto"></i>Conectado</span></div>
            <div class="papel">${esc(E?.conta?.email || 'Editor Black Belt')}${E?.conta?.adm ? ' · administrador' : ''}${E?.conta?.offline ? ' · sem internet agora' : ''}</div>
            <div id="saida-senha"></div>
          </div>
          <div class="sv-acoes">
            <button class="bt" data-aulas>${ic('aulas')}Minhas aulas</button>
            ${menuMais('conta', `
              <button class="item-menu" id="trocar-senha">Trocar senha</button>
              <button class="item-menu perigo" id="sair-conta">Sair da conta</button>`)}
          </div>
        </div>
      </div>
    </section>

    <section class="grupo">
      <div class="grupo-cab">
        <h2>Ferramentas de IA conectadas</h2>
        <p class="sub">Cada uma entra com a sua conta. As chaves ficam no ${esc(s.cofre === 'arquivo' ? 'disco' : 'cofre do sistema')}, neste computador — nunca no nosso servidor.</p>
      </div>
      <div class="surf lista-servicos">
        ${cartaoClaude(s.claude)}
        ${cartaoChatGPT(s.ia)}
        ${outros.map((x) => cartaoServico(x)).join('')}
      </div>
    </section>`);

  ligarMenus();
  document.querySelectorAll('[data-aulas]').forEach((b) => { b.onclick = abrirAulas; });
  pintarBarra('contas');
  document.getElementById('trocar-senha').onclick = () => telaSenha();
  document.getElementById('sair-conta').onclick = async () => {
    await post('/api/conta/sair'); iniciar();
  };
  ligarClaude();
  ligarChatGPT();
  ligarDesconectar();
  document.querySelectorAll('[data-testar]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.testar;
      b.disabled = true; b.textContent = 'Testando…';
      try {
        const r = await post('/api/servicos/testar', { servico: id });
        const cx = document.querySelector(`[data-saida="${id}"]`);
        cx.innerHTML = `<span class="pastilha ${r.ok ? 'ok' : 'erro'}"><i class="ponto"></i>${esc(r.msg)}</span>
          ${r.saldo ? `<span class="pastilha" style="margin-left:6px">${esc(r.saldo)}</span>` : ''}
          ${r.conta ? `<span class="pastilha" style="margin-left:6px">${esc(r.conta)}</span>` : ''}`;
      } catch (e) { toast(e.message, true); }
      b.disabled = false; b.textContent = 'Testar conexão';
    };
  });

  // Guardar chave: some do cofre para a tela na mesma ação. Era `iniciar()` —
  // que refaz o app inteiro, bate no servidor de licença e pisca a tela toda
  // para trocar uma pastilha.
  document.querySelectorAll('[data-salvar]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.salvar;
      const campo = document.querySelector(`[data-chave="${id}"]`);
      const valor = campo.value.trim();
      b.disabled = true; b.textContent = valor ? 'Guardando…' : 'Removendo…';
      try {
        await post('/api/servicos/chave', { servico: id, valor });
        campo.value = '';
        await revalidar('contas', { silencioso: false,
          aviso: valor ? 'Chave guardada no cofre.' : 'Chave removida do cofre.' });
      } catch (e) {
        toast('Não consegui guardar: ' + e.message, true);
        b.disabled = false; b.textContent = 'Guardar';
      }
    };
  });

  document.querySelectorAll('[data-remover]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.remover;
      b.disabled = true; b.textContent = 'Removendo…';
      try {
        await post('/api/servicos/chave', { servico: id, valor: '' });
        await revalidar('contas', { silencioso: false, aviso: 'Chave removida do cofre.' });
      } catch (e) {
        toast('Não consegui remover: ' + e.message, true);
        b.disabled = false; b.textContent = 'Remover chave';
      }
    };
  });

  document.querySelectorAll('[data-chave-cli]').forEach((b) => {
    b.onclick = () => {
      const sv = b.dataset.chaveCli;
      modal(`<h2>Chave da MiniMax</h2>
        <p class="sub" style="margin-bottom:12px">O CLI guarda a chave por você.
          A conta via navegador continua sendo o caminho recomendado por eles.</p>
        <div class="campo"><input id="mk2" type="password" placeholder="sk-…"></div>
        <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
          <button class="bt principal" id="mk-ok">Guardar</button></div>`, (v) => {
        v.querySelector('[data-fechar]').onclick = () => v.remove();
        v.querySelector('#mk-ok').onclick = async () => {
          const ok = v.querySelector('#mk-ok');
          ok.disabled = true; ok.textContent = 'Guardando…';
          try {
            const r = await post('/api/servicos/entrar',
              { servico: sv, chave: v.querySelector('#mk2').value.trim() });
            v.remove();
            await revalidar('contas', { silencioso: false,
              aviso: r.msg || 'Chave guardada.' });
          } catch (e) {
            toast(e.message, true);
            ok.disabled = false; ok.textContent = 'Guardar';
          }
        };
      });
    };
  });

  // O login abre no Terminal e termina no navegador — FORA do app. Aqui começa
  // a espera que troca a pastilha sozinha quando ele terminar; antes a tela
  // parava em "Abri o navegador" e só o reinício do app a movia.
  document.querySelectorAll('[data-entrar]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.entrar;
      const nome = (SVC.servicos.find((x) => x.id === id) || {}).titulo || id;
      b.disabled = true;
      try {
        const r = await post('/api/servicos/entrar', { servico: id });
        toast(r.msg || 'Abri o navegador.', !r.ok);
        if (r.ok !== false) {
          esperarLogin('contas', nome,
            (d) => ((d.servicos || []).find((x) => x.id === id) || {}).pronto);
        }
      } catch (e) { toast(e.message, true); }
      b.disabled = false;
    };
  });
}

// O backend já sabia desconectar (`/api/servicos/sair`), mas nenhuma tela
// chamava — desconectar era coisa de Terminal. E sem o botão não havia como
// nem testar que a tela reage a uma conta que CAI.
function ligarDesconectar() {
  document.querySelectorAll('[data-sair-servico]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.sairServico;
      const nome = (SVC.servicos.find((x) => x.id === id) || {}).titulo || id;
      b.disabled = true; b.textContent = 'Saindo…';
      try {
        await post('/api/servicos/sair', { servico: id });
        pararEspera('contas');
        await revalidar('contas', { silencioso: false, aviso: nome + ' desconectado.' });
      } catch (e) {
        toast('Não consegui desconectar: ' + e.message, true);
        b.disabled = false; b.textContent = 'Desconectar';
      }
    };
  });
}

// Recebe os dados em vez de buscar: a tela inteira é reconferida de uma vez,
// e um cartão que busca por conta própria volta a ser uma foto solta — que é o
// bug que este arquivo está consertando.
function cartaoClaude(c) {
  if (!c) return '';
  const primaria = c.conectado ? ''
    : c.instalar ? `<button class="bt principal" id="claude-instalar">Instalar</button>`
    : c.entrar ? `<button class="bt principal" id="claude-entrar">Conectar</button>`
    : `<button class="bt principal" id="claude-testar">Reconectar</button>`;
  return linhaServico({
    id: 'claude', marca: 'C', nome: 'Claude',
    descricao: 'A IA que lê a fala, decide a edição e opera o Premiere por você.',
    estado: c.conectado ? 'ok' : 'atencao',
    meta: [c.rotulo, c.conta].filter(Boolean).join(' · '),
    ajuda: !c.conectado && c.msg ? c.msg : '',
    saida: '<div id="saida-claude" class="saida"></div>',
    primaria,
    menu: `${c.conectado ? `<button class="item-menu" id="claude-testar">Testar conexão</button>` : ''}
           <button class="item-menu" id="claude-trocar">Trocar método de entrada</button>`,
  });
}

/* Uma linha de ferramenta: marca, nome, para que serve, estado em palavras e
   SÓ a ação principal à vista. O resto (testar, trocar, desconectar) fica no
   "⋯" — quem está bem conectado não precisa de seis botões olhando para ele. */
const CHIP = { ok: ['ok', 'Conectado'], atencao: ['atencao', 'Precisa de atenção'], nao: ['', 'Não conectado'] };

function linhaServico(o) {
  const [cls, txt] = CHIP[o.estado] || CHIP.nao;
  return `<div class="servico" id="cartao-${esc(o.id)}">
    <div class="sv-marca">${esc(o.marca)}</div>
    <div class="sv-corpo">
      <div class="titulo">${esc(o.nome)}
        <span class="chip ${cls}"><i class="ponto"></i>${txt}</span></div>
      <div class="papel">${esc(o.descricao)}</div>
      ${o.meta ? `<div class="meta">${esc(o.meta)}</div>` : ''}
      ${o.ajuda ? `<div class="ajuda">${esc(o.ajuda)}</div>` : ''}
      ${o.extra || ''}
      ${o.saida || ''}
    </div>
    <div class="sv-acoes">
      ${o.primaria || ''}
      ${o.menu ? menuMais(o.id, o.menu) : ''}
    </div>
  </div>`;
}

function menuMais(id, itens) {
  return `<div class="mais">
    <button class="bt icone" data-mais="${esc(id)}" aria-haspopup="menu" aria-expanded="false"
      title="Mais opções">${ic('mais')}</button>
    <div class="menu" role="menu" data-menu="${esc(id)}" hidden>${itens}</div>
  </div>`;
}

/* Abre e fecha os "⋯". Os botões de dentro continuam com os mesmos ids e
   data-* de antes — quem liga o clique deles não sabe que mudaram de lugar. */
function ligarMenus() {
  const fechar = (exceto) => document.querySelectorAll('.menu').forEach((m) => {
    if (m === exceto) return;
    m.hidden = true;
    const b = document.querySelector(`[data-mais="${m.dataset.menu}"]`);
    if (b) b.setAttribute('aria-expanded', 'false');
  });
  document.querySelectorAll('[data-mais]').forEach((b) => {
    b.onclick = (e) => {
      e.stopPropagation();
      const m = document.querySelector(`[data-menu="${b.dataset.mais}"]`);
      fechar(m);
      m.hidden = !m.hidden;
      b.setAttribute('aria-expanded', String(!m.hidden));
    };
  });
  // clicar num item faz a ação E fecha; clicar fora fecha
  document.querySelectorAll('.menu').forEach((m) => {
    m.addEventListener('click', (e) => {
      if (e.target.closest('[data-revelar]')) return;
      setTimeout(() => fechar(), 0);
    });
  });
  if (!window.__menusLigados) {
    window.__menusLigados = true;
    document.addEventListener('click', (e) => { if (!e.target.closest('.mais')) fechar(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fechar(); });
  }
  // "Trocar a chave" mostra o campo que estava guardado
  document.querySelectorAll('[data-revelar]').forEach((b) => {
    b.onclick = () => {
      const alvo = document.getElementById(b.dataset.revelar);
      if (alvo) { alvo.hidden = false; const i = alvo.querySelector('input'); if (i) i.focus(); }
      fechar();
    };
  });
}

// O ChatGPT é uma CONTA como as outras — tem que estar aqui, não só escondido
// no seletor do chat. Foi onde o usuário foi procurar, e com razão.
function cartaoChatGPT(d) {
  if (!d) return '';
  const p = (d.provedores || []).find((x) => x.id === 'chatgpt');
  if (!p) return '';
  const assinatura = p.metodo === 'sessao';
  const primaria = p.pronto ? ''
    : assinatura ? `<button class="bt" id="gpt-entrar">Conectar</button>`
    : `<button class="bt" id="gpt-chave">Colar chave</button>`;
  const menu = assinatura
    ? `${p.pronto ? `<button class="item-menu" id="gpt-entrar">Entrar de novo</button>` : ''}
       <button class="item-menu" id="gpt-metodo">Usar chave de API</button>`
    : `${p.pronto ? `<button class="item-menu" id="gpt-chave">Colar outra chave</button>` : ''}
       <button class="item-menu" id="gpt-metodo">Usar a assinatura</button>`;
  return linhaServico({
    id: 'gpt', marca: 'G', nome: 'ChatGPT',
    descricao: 'Opcional: uma segunda IA para conversar, pela sua assinatura do ChatGPT.',
    estado: p.pronto ? 'ok' : 'nao',
    meta: [assinatura ? 'Assinatura, pelo Codex' : 'Chave de API', p.origem].filter(Boolean).join(' · '),
    ajuda: !p.pronto && p.msg ? p.msg : '',
    saida: '<div id="saida-gpt" class="saida"></div>',
    primaria, menu,
  });
}

function ligarChatGPT() {
  const en = document.getElementById('gpt-entrar');
  if (en) en.onclick = async () => {
    en.disabled = true; en.textContent = 'Abrindo o Terminal…';
    try {
      const r = await post('/api/ia/entrar');
      const cx = document.getElementById('saida-gpt');
      if (cx) cx.innerHTML = `<span class="pastilha ${r.ok ? 'ok' : 'erro'}"><i class="ponto"></i>${esc(r.msg)}</span>`;
      // o login do Codex acontece no Terminal: fica olhando até virar
      if (r.ok !== false) {
        esperarLogin('contas', 'ChatGPT', (d) =>
          ((d.ia && d.ia.provedores || []).find((x) => x.id === 'chatgpt') || {}).pronto);
      }
    } catch (e) { toast(e.message, true); }
    en.disabled = false; en.textContent = en.classList.contains('item-menu') ? 'Entrar de novo' : 'Conectar';
  };
  const ch = document.getElementById('gpt-chave');
  if (ch) ch.onclick = async () => {
    IA = (SVC && SVC.ia) || await api('/api/ia').catch(() => IA);
    pedirChaveIA({ id: 'chatgpt', nome: 'ChatGPT' });
  };
  const mt = document.getElementById('gpt-metodo');
  if (mt) mt.onclick = async () => {
    const querAssinatura = mt.textContent.includes('assinatura');
    mt.disabled = true;
    try {
      await post('/api/ia/metodo', { metodo: querAssinatura ? 'sessao' : 'chave' });
      await revalidar('contas', { silencioso: false,
        aviso: querAssinatura ? 'ChatGPT agora entra pela assinatura.'
                              : 'ChatGPT agora usa chave de API.' });
    } catch (e) { toast(e.message, true); mt.disabled = false; }
  };
}

function ligarClaude() {
  const t = document.getElementById('claude-testar');
  if (t) t.onclick = async () => {
    t.disabled = true; t.textContent = 'Testando…';
    try {
      const r = await post('/api/claude/testar');
      document.getElementById('saida-claude').innerHTML =
        `<span class="pastilha ${r.ok ? 'ok' : 'erro'}"><i class="ponto"></i>${esc(r.msg)}</span>`;
    } catch (e) { toast(e.message, true); }
    t.disabled = false; t.textContent = t.classList.contains('item-menu') ? 'Testar conexão' : 'Reconectar';
  };
  const tr = document.getElementById('claude-trocar');
  if (tr) tr.onclick = () => trocarMetodo();

  // "Rode `claude` no Terminal" é o conselho que este app existe para não dar.
  const en = document.getElementById('claude-entrar');
  if (en) en.onclick = async () => {
    en.disabled = true;
    try {
      const r = await post('/api/claude/entrar');
      toast(r.msg, !r.ok);
      if (r.ok !== false) {
        esperarLogin('contas', 'Claude', (d) => d.claude && d.claude.conectado);
      }
    } catch (e) { toast(e.message, true); }
    en.disabled = false;
  };
  const ins = document.getElementById('claude-instalar');
  if (ins) ins.onclick = () => { aba = 'ambiente'; projetoAberto = null; desenhar(); };
}

function telaSenha() {
  modal(`<h2>Trocar senha</h2>
    <div class="aviso" style="margin-bottom:14px">
      Ao trocar, <b>as outras sessões caem</b> — inclusive o painel do Tools PRO
      dentro do Premiere, que vai pedir login de novo. Esta janela continua conectada.
    </div>
    <div class="campo"><label>Senha atual</label>
      <input id="s-atual" type="password" autocomplete="current-password"></div>
    <div class="campo"><label>Nova senha <span style="color:var(--texto-3)">(mínimo 8 caracteres)</span></label>
      <input id="s-nova" type="password" autocomplete="new-password"></div>
    <div class="campo"><label>Repita a nova senha</label>
      <input id="s-rep" type="password" autocomplete="new-password"></div>
    <div id="s-erro"></div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="s-ok">Trocar</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    const erro = (m) => { v.querySelector('#s-erro').innerHTML =
      `<div class="aviso ruim" style="margin-top:10px">${esc(m)}</div>`; };

    v.querySelector('#s-ok').onclick = async () => {
      const atual = v.querySelector('#s-atual').value;
      const nova = v.querySelector('#s-nova').value;
      const rep = v.querySelector('#s-rep').value;
      if (!atual) return erro('Digite a senha atual.');
      if (nova.length < 8) return erro('A nova senha precisa ter pelo menos 8 caracteres.');
      if (nova !== rep) return erro('As duas novas senhas não batem.');

      const b = v.querySelector('#s-ok');
      b.disabled = true; b.textContent = 'Trocando…';
      try {
        const r = await post('/api/conta/senha', { atual, nova });
        if (!r.ok) { b.disabled = false; b.textContent = 'Trocar'; return erro(r.msg || 'Não consegui trocar.'); }
        v.remove();
        toast(r.msg || 'Senha alterada.');
        const cx = document.getElementById('saida-senha');
        if (cx) cx.innerHTML = '<span class="pastilha ok"><i class="ponto"></i>senha alterada — o painel do Premiere vai pedir login</span>';
      } catch (e) {
        b.disabled = false; b.textContent = 'Trocar'; erro(e.message);
      }
    };
    v.querySelector('#s-atual').focus();
  });
}

function trocarMetodo() {
  modal(`<h2>Como entrar no Claude</h2>
    <p class="sub" style="margin-bottom:14px">O app usa só o método escolhido —
      não tenta o outro por conta própria.</p>
    <div class="motores">
      <label class="motor"><input type="radio" name="mm" value="sessao" checked>
        <div style="flex:1"><div class="motor-nome">Sessão do Claude Code</div>
          <div class="motor-nota">Usa a conta já conectada no CLI. Nada para colar.</div></div></label>
      <label class="motor"><input type="radio" name="mm" value="chave">
        <div style="flex:1"><div class="motor-nome">Chave de API</div>
          <div class="motor-nota">Cole uma chave do console.anthropic.com.</div></div></label>
    </div>
    <div id="campo-chave" style="display:none;margin-top:12px">
      <input id="mk" type="password" placeholder="sk-ant-…">
    </div>
    <div class="acoes"><button class="bt discreto" data-fechar>Cancelar</button>
      <button class="bt principal" id="mm-ok">Usar este</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelectorAll('input[name=mm]').forEach((r) => {
      r.onchange = () => {
        v.querySelector('#campo-chave').style.display = r.value === 'chave' ? 'block' : 'none';
        v.querySelectorAll('.motor').forEach((m) =>
          m.classList.toggle('ativo', m.querySelector('input').checked));
      };
    });
    v.querySelector('#mm-ok').onclick = async () => {
      const m = v.querySelector('input[name=mm]:checked').value;
      try {
        if (m === 'chave') {
          const k = v.querySelector('#mk').value.trim();
          if (k) await post('/api/servicos/chave', { servico: 'claude', valor: k });
        }
        await post('/api/claude/metodo', { metodo: m });
        v.remove();
        await revalidar('contas', { silencioso: false, aviso: 'Método atualizado.' });
      } catch (e) { toast(e.message, true); }
    };
  });
}

const DESCRICAO = {
  elevenlabs: ['E', 'A voz do vídeo — narração e locução. É a única fonte de áudio do app.'],
  heygen:     ['Hg', 'Opcional: avatar falante, quando o criativo pede um apresentador.'],
  minimax:    ['M', 'Opcional: mais um gerador de vídeo, imagem e música.'],
  higgsfield: ['Hf', 'Gera as imagens e os b-rolls que entram na sua timeline.'],
};

function cartaoServico(x) {
  const conectado = x.pronto;
  const [marca, descricao] = DESCRICAO[x.id] || [String(x.titulo || '?')[0], x.papel];
  const essencial = ESSENCIAIS.includes(x.id);
  const chave = x.modo === 'chave';
  const campo = (escondido) => `<div class="linha-chave" id="chave-${x.id}" ${escondido ? 'hidden' : ''}>
       <input data-chave="${x.id}" type="password" autocomplete="off"
         placeholder="${conectado ? 'Cole a chave nova' : 'Cole aqui a chave de API'}">
       <button class="bt ${conectado ? '' : 'principal'}" data-salvar="${x.id}">Guardar</button>
     </div>`;
  const primaria = conectado ? ''
    : chave ? ''
    : `<button class="bt ${essencial ? 'principal' : ''}" data-entrar="${x.id}">Conectar</button>`;
  const menu = [
    `<button class="item-menu" data-testar="${x.id}">Testar conexão</button>`,
    conectado && chave ? `<button class="item-menu" data-revelar="chave-${x.id}">Trocar a chave</button>` : '',
    conectado && !chave ? `<button class="item-menu" data-entrar="${x.id}">Entrar de novo</button>` : '',
    x.id === 'minimax' ? `<button class="item-menu" data-chave-cli="minimax">Usar chave em vez da conta</button>` : '',
    conectado ? (chave
      ? `<button class="item-menu perigo" data-remover="${x.id}">Remover chave</button>`
      : `<button class="item-menu perigo" data-sair-servico="${x.id}">Desconectar</button>`) : '',
  ].join('');
  // "endereço não verificado" era uma pastilha solta que ninguém entendia: o
  // teste automático deste serviço não foi conferido por nós ainda. Vira uma
  // frase de ajuda, embaixo, só onde importa.
  const ajudas = [
    x.alerta || '',
    !conectado && x.msg ? x.msg : '',
    x.verificado === false
      ? 'Se o “Testar conexão” falhar com a chave certa, a chave continua valendo — o teste desta ferramenta ainda está em observação.'
      : '',
  ].filter(Boolean);
  return linhaServico({
    id: x.id, marca, nome: x.titulo, descricao,
    estado: conectado ? (x.alerta ? 'atencao' : 'ok') : essencial ? 'atencao' : 'nao',
    meta: [x.conta, x.saldo, x.fim].filter(Boolean).join(' · '),
    extra: (chave ? campo(conectado) : '') +
      ajudas.map((a) => `<div class="ajuda">${esc(a)}</div>`).join(''),
    saida: `<div data-saida="${x.id}" class="saida"></div>`,
    primaria, menu,
  });
}

// ---------------------------------------------------------------- chat livre
async function telaChatLivre() {
  const cv = conversaAtual
    ? await api('/api/conversas/' + conversaAtual)
    : await api('/api/conversa');
  if (cv.conversa) conversaAtual = cv.conversa;
  moldura(`
    <div class="chat-tela">
      <div class="chat-col">
        <div class="chat-topo">
          <div><h1>Conversa <span class="selo-beta">beta</span></h1>
            <p class="sub">${cv.meta && cv.meta.titulo && cv.meta.titulo !== 'Nova conversa'
              ? esc(cv.meta.titulo) : 'Fale o que quer fazer. Eu confiro o Adobe e conduzo daqui.'}</p></div>
          <button class="bt discreto" id="nova-conversa">+ Nova conversa</button>
        </div>
        <div class="nota-beta">
          <span class="nota-icone">▸</span>
          <div>Esta conversa ainda está em teste. Com tudo já conectado aqui,
            <b>as tarefas longas rendem mais pelo Claude Code no VS Code</b> —
            lá o contexto é maior e dá para acompanhar cada passo.
            O app continua sendo quem guarda o projeto, as aprovações e as credenciais.</div>
        </div>
        <div class="conversa" id="conversa">
          ${cv.mensagens.length ? cv.mensagens.map(bolha).join('') : `
            <div class="msg resposta"><div class="bolha">
              <p>Pronto. Antes de mexer em qualquer coisa eu confiro o que está aberto
              no Premiere ou no After Effects e te mostro aqui para confirmar.</p>
              <p style="margin-top:8px">Pode falar normalmente:
                <i>"analise esta timeline"</i>, <i>"verifique a copy"</i>,
                <i>"marque os pontos de b-roll"</i>, <i>"gere as imagens"</i>.</p>
            </div></div>`}
          <div id="fim-conversa"></div>
        </div>
        <div class="compositor">
          <div id="anexos" class="anexos"></div>
          <div class="compositor-linha">
            <button class="bt discreto" id="anexar" title="Anexar arquivo">＋</button>
            <textarea id="entrada" rows="1"
              placeholder="Fale o que quer fazer… (Enter envia, Shift+Enter quebra linha)"></textarea>
            <button class="bt principal" id="enviar">Enviar</button>
          </div>
          ${seletorIA()}
          <div class="atalhos">
            ${['O que está aberto no Premiere?', 'Analise esta timeline',
               'Quero editar um criativo novo'].map((a) =>
              `<button class="atalho" data-diz="${esc(a)}">${esc(a)}</button>`).join('')}
          </div>
        </div>
      </div>
      <aside class="pipe-lateral" id="lado-adobe">
        <div class="rotulo" style="margin-bottom:10px">Adobe</div>
        <div class="sub pulsando">conferindo…</div>
      </aside>
    </div>`);

  document.getElementById('palco').classList.add('modo-chat');
  const nc = document.getElementById('nova-conversa');
  if (nc) nc.onclick = async () => {
    const r = await post('/api/conversas/nova'); conversaAtual = r.conversa; desenhar();
  };
  ligarChat({ id: null }, null);
  rolarFim();
  pintarAdobe();
}

async function pintarAdobe() {
  const lado = document.getElementById('lado-adobe');
  if (!lado) return;
  let a;
  try { a = await api('/api/adobe'); }
  catch (e) { lado.innerHTML = `<div class="sub">${esc(e.message)}</div>`; return; }

  const v = a.verificado || {};
  const linha = (rot, val, cor) =>
    `<div class="adobe-linha"><span class="rotulo">${esc(rot)}</span>
      <b style="${cor ? 'color:' + cor : ''}">${esc(val)}</b></div>`;

  // "conectada" só quando o Claude CONSEGUE usar: leu a timeline E o servidor
  // de ferramentas subiu. Antes bastava existir um painel na porta — e a tela
  // dizia conectada enquanto o Claude ficava sem ferramenta nenhuma.
  const ok = a.utilizavel;
  const parcial = v.ponte && !ok;

  lado.innerHTML = `
    <div class="rotulo" style="margin-bottom:10px">Adobe</div>
    ${linha('Premiere', a.apps.premiere ? 'aberto' : 'fechado',
            a.apps.premiere ? 'var(--ok)' : 'var(--texto-3)')}
    ${linha('After Effects', a.apps.aftereffects ? 'aberto' : 'fechado',
            a.apps.aftereffects ? 'var(--ok)' : 'var(--texto-3)')}
    ${linha('Tools PRO', ok ? 'em uso' : parcial ? 'painel aberto, sem uso' : 'sem painel',
            ok ? 'var(--ok)' : 'var(--broll)')}
    ${a.projeto ? linha('Projeto', a.projeto, 'var(--ouro)') : ''}
    ${a.ativa ? linha('Sequência', a.ativa) : ''}
    ${v.resumo ? linha('Timeline lida',
        `${v.resumo.clipes} clipes · ${v.resumo.marcadores} marcadores`) : ''}
    ${a.mcp && a.mcp.ok ? linha('Ferramentas', `${a.mcp.ferramentas} disponíveis ao Claude`)
      : linha('Ferramentas', 'indisponíveis', 'var(--broll)')}
    ${!ok ? `<div class="aviso ruim" style="margin-top:12px;font-size:12px">
        ${esc(v.detalhe || (a.mcp && a.mcp.msg) || 'O Claude não consegue usar as ferramentas do editor.')}
      </div>
      ${v.preparar_ponte
        ? `<button class="bt principal" id="preparar-ponte" style="width:100%;margin-top:10px">
             Preparar a ponte (1 clique)</button>`
        : `<button class="bt principal" id="reconectar" style="width:100%;margin-top:10px">
             Reconectar ao Tools PRO</button>`}
      ${v.instalar_plugin || !v.ponte ? `<button class="bt discreto" id="ir-plugin" style="width:100%;margin-top:8px">
        Instalar o plugin do Premiere</button>` : ''}` : ''}
    <button class="bt discreto" id="rever-adobe" style="width:100%;margin-top:8px">Conferir de novo</button>`;

  const rv = document.getElementById('rever-adobe');
  if (rv) rv.onclick = () => pintarAdobe();
  const rc = document.getElementById('reconectar');
  if (rc) rc.onclick = () => reconectarToolsPro();
  const ip = document.getElementById('ir-plugin');
  if (ip) ip.onclick = () => { aba = 'ambiente'; projetoAberto = null; desenhar(); };
  const pp = document.getElementById('preparar-ponte');
  if (pp) pp.onclick = () => prepararPonte();
}

// O painel do Tools PRO não abre porta de conexão por padrão: falta o `.debug`
// na pasta da extensão. Sem ele o app dizia "abra o painel" para quem já estava
// com o painel aberto — conselho certo, causa errada.
async function prepararPonte() {
  const v = modal(`<h2>Preparando a ponte</h2>
    <p class="sub" id="pp-txt">Escrevendo a configuração na pasta do plugin…</p>`);
  try {
    const r = await post('/api/ponte/preparar');
    revalidar('ambiente');
    v.querySelector('h2').textContent = 'Ponte preparada';
    v.querySelector('#pp-txt').innerHTML =
      `O painel do Tools PRO passa a abrir a porta <b>${r.porta}</b>.<br><br>
       <b>Feche e reabra o Premiere</b> e abra <b>Janela &gt; Extensões &gt; Tools PRO</b>.
       A porta só nasce quando o Premiere arranca lendo esse arquivo — por isso o
       reinício não é frescura.`;
  } catch (e) {
    v.querySelector('#pp-txt').textContent = e.message;
  }
}

async function reconectarToolsPro() {
  const v = modal(`<h2>Reconectando</h2>
    <p class="sub" id="rc-txt">Procurando o painel do Tools PRO…</p>`);
  for (let i = 0; i < 6; i++) {
    try {
      const a = await api('/api/adobe?forcar=1');
      if (a.utilizavel) {
        v.remove(); toast('Tools PRO em uso.'); pintarAdobe(); return;
      }
      v.querySelector('#rc-txt').textContent =
        (a.verificado && a.verificado.detalhe) || 'Ainda sem resposta…';
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 2000));
  }
  v.querySelector('#rc-txt').innerHTML =
    'Não consegui. No Premiere abra <b>Janela &gt; Extensões &gt; Tools PRO</b> ' +
    'e clique em Reconectar de novo.';
  setTimeout(() => v.remove(), 6000);
}

// ---------------------------------------------------------------- ambiente
async function telaAmbiente() {
  if (!AMB) {
    esqueleto('Ambiente', 'Conferindo o que está instalado nesta máquina…');
    const r = await revalidar('ambiente');
    if (!r.ok && !AMB) return telaErroEstado('Ambiente', r.erro, 'ambiente');
  } else {
    revalidarSeVelho('ambiente');
  }
  const d = AMB, pl = AMB.plugin, sk = AMB.skills;
  const faltando = d.itens.filter((i) => !i.tem && i.essencial && i.instalavel);
  // "pendente" é tudo que o botão único resolve — não só os essenciais que já
  // dava para instalar na foto de agora. Sem Node, Claude e Higgsfield vêm como
  // "não instalável"; o orquestrador instala o Node e eles passam a caber.
  const pendente = !d.brew
    || d.itens.some((i) => !i.tem && i.id !== 'premiere' && i.id !== 'toolspro' && i.id !== 'regra')
    || (sk && (sk.faltam.length || (sk.atualizar || []).length))
    || (pl && (!pl.instalado || pl.tem_nova || (pl.ponte && !pl.ponte.tem_debug)));

  moldura(`
    ${cabecalho('ambiente', `${barraEstado('ambiente')}
        ${pendente ? `<button class="bt principal" id="preparar">Preparar este computador</button>`
                   : `<span class="chip ok"><i class="ponto"></i>Tudo pronto</span>`}`)}
    ${d.pronto ? `<div class="aviso bom" style="margin-bottom:16px">
        ${ic('check')} Tudo o que é essencial está instalado. Você não precisa abrir o Terminal.</div>`
      : `<div class="aviso ruim" style="margin-bottom:16px">Falta instalar: ${esc(d.faltam.join(', '))}. O botão “Preparar este computador” instala na ordem certa.</div>`}
    ${!d.brew ? (d.gerenciador === 'winget' ? `<div class="aviso" style="margin-bottom:16px">
      O <b>winget</b> não respondeu — sem ele não consigo instalar o FFmpeg sozinho.
      Ele vem no Windows 10 e 11: abra a Microsoft Store e instale o
      <b>Instalador de Aplicativo</b>.</div>` : `<div class="aviso" style="margin-bottom:16px">
      O Homebrew não está instalado — sem ele não consigo instalar FFmpeg sozinho.
      <button class="bt principal" id="brew" style="margin-top:10px">Instalar o Homebrew</button>
      <div style="font-size:11px;opacity:.7;margin-top:6px">Abre o Terminal com o
      instalador oficial. Ele pede a senha do seu Mac — é o instalador pedindo, não o app.</div>
      </div>`) : ''}
    ${sk ? cartaoSkills(sk) : ''}
    ${pl ? cartaoPlugin(pl) : ''}
    <div class="grupo-cab"><h2>Programas deste computador</h2>
      <p class="sub">Os essenciais precisam estar instalados. Os opcionais só valem para quem usa aquela ferramenta.</p></div>
    <div class="surf lista-servicos deps">
      ${d.itens.map((i) => `
        <div class="dep">
          <div class="dep-marca ${i.tem ? 'ok' : i.essencial ? 'falta' : 'opcional'}">${i.tem ? '✓' : i.essencial ? '!' : '○'}</div>
          <div style="flex:1;min-width:0">
            <div class="dep-nome">${esc(i.nome)}
              ${!i.essencial ? '<span class="chip">opcional</span>' : ''}</div>
            <div class="dep-para">${esc(i.para)}</div>
            ${!i.tem && i.manual ? `<div class="dep-para" style="color:var(--ouro)">${esc(i.manual)}</div>` : ''}
          </div>
          <div class="dep-versao">${esc(i.versao || '')}</div>
          ${(i.acoes || []).includes('testar') ? `<button class="bt" data-inst="${i.id}-teste" title="Renderiza 1 segundo de vídeo para provar que funciona">Testar</button>` : ''}
          ${(i.acoes || []).includes('reparar') ? `<button class="bt" data-inst="${i.id}">Reparar</button>`
            : !i.tem && i.instalavel ? `<button class="bt" data-inst="${i.id}">Instalar</button>` : ''}
        </div>`).join('')}
    </div>`);

  // Terminada a instalação, quem diz se deu certo é a RECONFERÊNCIA, não o
  // "pronto" da tarefa. `forcar` porque o instalador pode ter posto o binário
  // numa pasta que ainda não estava no PATH deste processo.
  const rodar = (qual) => {
    // "x-teste" é o teste de um item instalado (hoje só o HyperFrames)
    const teste = !!qual && qual.endsWith('-teste');
    const base = teste ? qual.slice(0, -6) : qual;
    const nome = qual ? (d.itens.find((i) => i.id === base) || {}).nome || base : null;
    const v = modal(`<h2>${teste ? 'Testando' : 'Instalando'}${nome ? ' — ' + esc(nome) : ''}</h2>
      <div class="portao" id="log" style="max-height:280px">preparando…</div>`);
    post('/api/ambiente/instalar', qual ? { qual } : {}).then((r) => {
      const t = setInterval(async () => {
        const s = await api('/api/tarefas/' + r.tarefa);
        const l = v.querySelector('#log');
        l.textContent = (s.log || []).join('\n') || 'trabalhando…';
        l.scrollTop = l.scrollHeight;
        if (s.estado === 'pronto') {
          clearInterval(t); v.remove();
          await revalidar('ambiente', { forcar: true, silencioso: true });
          if (teste) toast('Render de teste ok — o ' + nome + ' está funcionando.');
          else conferirInstalacao(qual, nome, s.resultado);
        } else if (s.estado === 'erro') {
          clearInterval(t); v.remove();
          toast((teste ? 'O teste falhou: ' : 'A instalação falhou: ') + s.erro, true);
          revalidar('ambiente', { forcar: true });
        }
      }, 1200);
    }).catch((e) => { v.remove(); toast(e.message, true); });
  };

  // O Homebrew instala num Terminal de fora — o app não é avisado quando
  // termina. Mesma espera dos logins: fica olhando até o `brew` aparecer.
  const bw = document.getElementById('brew');
  if (bw) bw.onclick = async () => {
    bw.disabled = true;
    try {
      const r = await post('/api/ambiente/gerenciador');
      toast(r.msg, !r.ok);
      if (r.ok && !r.ja_tinha) {
        esperarLogin('ambiente', 'Homebrew', (x) => x && x.brew, 10);
      } else if (r.ja_tinha) {
        revalidar('ambiente', { forcar: true });
      }
    } catch (e) { toast(e.message, true); }
    bw.disabled = false;
  };
  const bt = document.getElementById('preparar');
  if (bt) bt.onclick = prepararMaquina;
  document.querySelectorAll('[data-inst]').forEach((b) => { b.onclick = () => rodar(b.dataset.inst); });
  pintarBarra('ambiente');
  ligarSkills();
  ligarPlugin();
}

// ---------------------------------------------- um botão para tudo
/* A tela tinha cinco botões para a mesma pergunta — Homebrew, "o que falta",
   cada opcional, skills e plugin — e o aluno tinha que saber a ORDEM (Node antes
   do Claude, Homebrew antes de tudo). Aqui é uma fila só no servidor; a tela
   mostra o plano antes (o Terminal vai abrir e pedir senha — melhor saber
   antes de clicar) e depois uma lista de checagem viva. */
const ESTADO_PASSO = {
  fila:       ['○', 'var(--texto-3)', 'na fila'],
  rodando:    ['◌', 'var(--ouro)',    ''],
  terminal:   ['⧉', 'var(--ouro)',    ''],
  aguardando: ['…', 'var(--ouro)',    ''],
  ok:         ['✓', 'var(--ok)',      ''],
  pulado:     ['–', 'var(--texto-3)', ''],
  manual:     ['✎', 'var(--texto-3)', ''],
  erro:       ['!', 'var(--broll)',   ''],
};

function listaPassos(passos) {
  return `<div class="check">${(passos || []).map((p) => {
    const [marca, cor, padrao] = ESTADO_PASSO[p.estado] || ESTADO_PASSO.fila;
    return `<div class="check-item">
      <span class="check-marca" style="color:${cor}">${marca}</span>
      <span class="check-nome">${esc(p.nome)}</span>
      <span class="check-nota" style="${p.estado === 'erro' ? 'color:var(--broll)' : ''}">${esc(p.nota || padrao)}</span>
    </div>`;
  }).join('')}</div>`;
}

async function prepararMaquina() {
  const v = modal(`<h2>Preparar esta máquina</h2>
    <p class="sub" id="pm-txt">Conferindo o que falta…</p>
    <div id="pm-corpo"></div>
    <div class="acoes" id="pm-acoes"></div>`);
  const corpo = v.querySelector('#pm-corpo'), txt = v.querySelector('#pm-txt'),
        acoes = v.querySelector('#pm-acoes');
  let plano;
  try { plano = await api('/api/ambiente/plano'); }
  catch (e) { txt.textContent = e.message; return; }

  if (plano.nada) {
    txt.textContent = 'Não há nada que eu consiga instalar sozinho agora.';
    corpo.innerHTML = listaPassos(plano.passos.map((p) => ({ ...p, estado: 'manual', nota: p.para })));
    acoes.innerHTML = `<button class="bt" id="pm-fechar">Fechar</button>`;
    v.querySelector('#pm-fechar').onclick = () => v.remove();
    return;
  }

  const temOpc = plano.passos.some((p) => p.tipo === 'opcional' && !p.manual && p.id !== 'plugin' && p.id !== 'ponte');
  const temPlugin = plano.passos.some((p) => p.id === 'plugin' || p.id === 'ponte');
  txt.textContent = 'Vou instalar, nesta ordem, reconferindo entre um passo e outro:';
  corpo.innerHTML = listaPassos(plano.passos.map((p) => ({
    ...p, estado: p.manual ? 'manual' : 'fila', nota: p.para })))
    + `<div class="pm-opcoes">
      ${temOpc ? `<label><input type="checkbox" id="pm-opc" checked> incluir os opcionais (Codex, MiniMax, Anthropic CLI, HeyGen)</label>` : ''}
      ${temPlugin ? `<label><input type="checkbox" id="pm-plugin" checked> instalar o plugin do Premiere e preparar a ponte</label>` : ''}
    </div>`
    + (plano.abre_terminal ? `<div class="aviso" style="margin-top:12px">
      Uma janela do <b>Terminal</b> vai abrir uma ou duas vezes — é o instalador
      oficial (Homebrew pede a <b>senha do seu Mac</b>; o plugin liga o modo de
      depuração do Premiere). Não feche essa janela: o app fica esperando ela
      terminar e segue sozinho.</div>` : '');
  acoes.innerHTML = `<button class="bt" id="pm-cancelar">Cancelar</button>
    <button class="bt principal" id="pm-ir">Começar</button>`;
  v.querySelector('#pm-cancelar').onclick = () => v.remove();
  v.querySelector('#pm-ir').onclick = async () => {
    const opcionais = !temOpc || v.querySelector('#pm-opc').checked;
    const comPlugin = !temPlugin || v.querySelector('#pm-plugin').checked;
    acoes.innerHTML = '';
    txt.textContent = 'Instalando. Pode demorar alguns minutos — o Whisper e o plugin são os mais pesados.';
    corpo.innerHTML = listaPassos([]) + `<div class="portao" id="pm-log" style="max-height:110px;margin-top:10px">começando…</div>`;
    // clicar fora não fecha mais: fechar aqui não cancela nada, só esconde
    v.onclick = null;
    let r;
    try { r = await post('/api/ambiente/preparar', { opcionais, plugin: comPlugin }); }
    catch (e) { txt.textContent = e.message; return; }

    const t = setInterval(async () => {
      let st;
      try { st = await api('/api/tarefas/' + r.tarefa); } catch (e) { return; }
      const lista = corpo.querySelector('.check');
      if (lista) lista.outerHTML = listaPassos(st.passos);
      const l = corpo.querySelector('#pm-log');
      if (l) { l.textContent = (st.log || []).slice(-3).join('\n') || 'trabalhando…'; l.scrollTop = l.scrollHeight; }
      if (st.estado !== 'pronto' && st.estado !== 'erro') return;
      clearInterval(t);
      await revalidar('ambiente', { forcar: true, silencioso: true });
      pintarBarra('ambiente');
      if (st.estado === 'erro') {
        txt.textContent = 'Parou no meio: ' + st.erro;
        acoes.innerHTML = `<button class="bt" id="pm-fechar">Fechar</button>`;
        v.querySelector('#pm-fechar').onclick = () => { v.remove(); desenhar(); };
        return;
      }
      const res = st.resultado || {};
      const partes = [];
      if (res.instalados?.length) partes.push('Instalei ' + res.instalados.join(', ') + '.');
      if (res.aguardando?.length) partes.push('Ainda esperando terminar no Terminal: ' + res.aguardando.join(', ') + '.');
      if (res.erros?.length) partes.push('Falhou: ' + res.erros.join(' · '));
      if (res.pulados?.length) partes.push('Fica por sua conta: ' + res.pulados.join(', ') + '.');
      if (res.reiniciar_premiere) partes.push('Feche e reabra o Premiere: a porta do painel só nasce no arranque.');
      txt.textContent = partes.join(' ') || 'Nada precisou ser instalado.';
      const ok = !(res.erros && res.erros.length);
      const pendente = !!(res.aguardando && res.aguardando.length);
      toast(!ok ? 'Terminei, mas alguma coisa falhou — veja a lista.'
            : pendente ? 'Terminei o que dava — falta o Terminal acabar.' : 'Máquina preparada.', !ok);
      acoes.innerHTML = `<button class="bt principal" id="pm-fechar">Fechar</button>`;
      v.querySelector('#pm-fechar').onclick = () => { v.remove(); desenhar(); };
      // o plugin pode ter ficado rodando no Terminal depois do tempo de espera
      if (res.aguardando && res.aguardando.includes('Plugin do Premiere')) {
        const antes = (AMB && AMB.plugin && AMB.plugin.instalado) || null;
        esperarLogin('ambiente', 'plugin do Premiere',
          (x) => x && x.plugin && x.plugin.instalado && x.plugin.instalado !== antes, 10);
      }
    }, 1200);
  };
}

/* "Pronto." não é resposta: o comando pode terminar com código 0 e o binário
   continuar sem aparecer (PATH, stub de loja, receita que instalou outra
   coisa). Quem responde é a lista reconferida. */
function conferirInstalacao(qual, nome, resultado) {
  const itens = (AMB && AMB.itens) || [];
  if (qual) {
    const i = itens.find((x) => x.id === qual);
    if (i && i.tem) return toast((nome || qual) + ' instalado.');
    return toast('Rodou sem erro, mas ainda não encontro ' + (nome || qual)
      + ' nesta máquina. Clique em Atualizar status; se continuar, veja o log.', true);
  }
  const feitos = (resultado && resultado.instalados) || [];
  const erros = (resultado && resultado.erros) || [];
  const faltam = (AMB && AMB.faltam) || [];
  if (erros.length) return toast('Instalei ' + feitos.length + ', mas falhou: '
    + erros.join(' · '), true);
  if (faltam.length) return toast('Instalei ' + feitos.length
    + '. Ainda falta: ' + faltam.join(', '), true);
  toast(feitos.length ? 'Pronto — instalei ' + feitos.join(', ') + '.'
                      : 'Tudo que é essencial já estava instalado.');
}

// As skills são o REPERTÓRIO do Claude. Sem elas o mesmo app, com o mesmo
// Claude, responde com um vocabulário completamente diferente conforme a
// máquina — e sem aviso nenhum. Por isso a tela mostra quantas ele tem.
function cartaoSkills(sk) {
  const falta = sk.faltam.length, novas = (sk.atualizar || []).length;
  const suas = (sk.do_usuario || []).length;
  const codex = (sk.destinos || []).length > 1;
  const pendente = falta + novas;
  return `
    <div class="plugin">
      <div class="selo-pl">✦</div>
      <div style="flex:1;min-width:0">
        <div class="pl-nome">Skills da IA — o repertório Editor Black Belt</div>
        <div class="pl-sub">${falta
          ? `<span style="color:var(--gold2)">${falta} de ${sk.total} faltando</span> — sem elas a IA edita sem o método da casa`
          : novas ? `<span style="color:var(--gold2)">${novas} com versão nova</span> no app`
          : `${sk.total} instaladas e em dia — inclusive a skill mestra (skill-black-belt)`}${codex ? ' · Claude e ChatGPT (Codex)' : ' · Claude'}</div>
        ${suas ? `<div class="pl-sub">${suas} você modificou — o app não mexe nelas sem você pedir.</div>` : ''}
      </div>
      ${pendente ? `<button class="bt principal" id="sk-instalar" data-modo="instalar">${falta ? 'Instalar' : 'Atualizar'} (${pendente})</button>`
                 : `<button class="bt discreto" id="sk-instalar" data-modo="reinstalar">Reinstalar</button>`}
    </div>`;
}

function ligarSkills() {
  const b = document.getElementById('sk-instalar');
  if (!b) return;
  b.onclick = () => {
    const jaTem = b.dataset.modo === 'reinstalar';
    const v = modal(`<h2>Skills do Claude</h2>
      <p class="sub">${jaTem
        ? 'Reinstalar troca TODAS pelas versões que vieram no app — inclusive as que você modificou. As suas ficam guardadas em ~/.editorblackbelt/skills-anteriores, não apagadas.'
        : 'Vou instalar e atualizar as skills do app para a IA. As que você modificou não são tocadas.'}</p>
      <div class="portao" id="log" style="max-height:160px;margin-top:10px">começando…</div>`);
    post('/api/skills/instalar', { substituir: jaTem }).then((r) => {
      const t = setInterval(async () => {
        const st = await api('/api/tarefas/' + r.tarefa);
        v.querySelector('#log').textContent = (st.log || []).slice(-4).join('\n') || 'trabalhando…';
        if (st.estado === 'pronto') {
          clearInterval(t); v.remove();
          await revalidar('ambiente');
          const sk2 = AMB && AMB.skills;
          toast(sk2 && sk2.faltam && sk2.faltam.length
            ? 'Instalei, mas ainda faltam ' + sk2.faltam.length + ' skills.'
            : (st.resultado?.msg || 'Skills instaladas.'),
            !!(sk2 && sk2.faltam && sk2.faltam.length));
        } else if (st.estado === 'erro') {
          clearInterval(t); v.remove();
          toast('Não consegui instalar as skills: ' + st.erro, true);
          revalidar('ambiente');
        }
      }, 600);
    }).catch((e) => { v.remove(); toast(e.message, true); });
  };
}

// O plugin é a PONTE: sem ele o app não escreve uma linha na timeline. Por isso
// ele fica no topo do Ambiente, e a instalação é um botão — não um tutorial.
function cartaoPlugin(pl) {
  const tem = !!pl.instalado;
  const rotulo = !tem ? 'Instalar plugin no Premiere'
    : pl.tem_nova ? `Atualizar para ${esc(pl.ultima)}` : 'Reinstalar';
  return `
    <div class="plugin">
      <div class="selo-pl">⧉</div>
      <div style="flex:1;min-width:0">
        <div class="pl-nome">Plugin do Premiere — Editor Black Belt Tools PRO</div>
        <div class="pl-sub">${tem
          ? `instalado v${esc(pl.instalado)}${pl.ultima ? ` · publicado v${esc(pl.ultima)}` : ''}`
          : 'não encontrado — é ele que deixa o app ler e escrever na sua timeline'}</div>
        ${pl.erro ? `<div class="pl-sub" style="color:var(--ouro)">${esc(pl.erro)}</div>` : ''}
        ${tem && pl.ponte && !pl.ponte.tem_debug ? `<div class="pl-sub" style="color:var(--broll)">
          ⚠ A ponte com o Premiere não está preparada — o painel não abre porta de
          conexão, então o app não consegue escrever na timeline.</div>` : ''}
        ${tem && pl.ponte && pl.ponte.tem_debug ? `<div class="pl-sub" style="color:var(--ok)">
          ponte preparada na porta ${pl.ponte.porta}</div>` : ''}
      </div>
      ${tem && pl.ponte && !pl.ponte.tem_debug
        ? `<button class="bt principal" id="pl-ponte">Preparar a ponte</button>` : ''}
      <a class="bt discreto" href="${esc(pl.pagina)}" target="_blank" rel="noreferrer">Página</a>
      <button class="bt ${tem && !pl.tem_nova ? '' : 'principal'}" id="pl-instalar">${rotulo}</button>
    </div>`;
}

function ligarPlugin() {
  const pb = document.getElementById('pl-ponte');
  if (pb) pb.onclick = async () => { await prepararPonte(); };
  const b = document.getElementById('pl-instalar');
  if (!b) return;
  b.onclick = () => {
    const v = modal(`<h2>Plugin do Premiere</h2>
      <p class="sub">Baixando o instalador oficial (~100 MB). Ele abre numa janela
      de terminal; quando terminar, feche e reabra o Premiere e vá em
      <b>Janela &gt; Extensões &gt; Tools PRO</b>.</p>
      <div class="portao" id="log" style="max-height:200px">começando…</div>`);
    post('/api/plugin/instalar').then((r) => {
      const t = setInterval(async () => {
        const st = await api('/api/tarefas/' + r.tarefa);
        v.querySelector('#log').textContent = (st.log || []).slice(-3).join('\n') || 'trabalhando…';
        if (st.estado === 'pronto') {
          clearInterval(t); v.remove();
          toast(st.resultado?.msg || 'Instalador aberto.');
          // ⚠️ Aqui a tarefa terminar significa só que o INSTALADOR abriu — ele
          // roda num Terminal de fora, e a versão só muda na pasta do CEP quando
          // ele termina. Por isso é espera, não uma conferida só.
          const antes = (AMB && AMB.plugin && AMB.plugin.instalado) || null;
          esperarLogin('ambiente', 'plugin do Premiere',
            (x) => x && x.plugin && x.plugin.instalado && x.plugin.instalado !== antes, 10);
        } else if (st.estado === 'erro') {
          clearInterval(t); v.remove();
          toast('Não consegui instalar o plugin: ' + st.erro, true);
          revalidar('ambiente');
        }
      }, 900);
    }).catch((e) => { v.remove(); toast(e.message, true); });
  };
}

// ------------------------------------------- acesso à pasta Documentos (Mac)
/* O app guarda conversas e projetos em Documentos/Editor Automático. No Mac,
   a primeira escrita ali faz o sistema perguntar se o app pode acessar a pasta
   — e a chamada fica parada até a resposta. Antes isso caía no meio da
   primeira mensagem da Conversa, com a janela do sistema às vezes escondida
   atrás do app. Agora a pergunta vem ao abrir, e a tela explica enquanto ela
   está aberta. Se responder rápido (já liberado, ou Windows), nada aparece. */
const PASTA_AVISO_MS = 700;

async function conferirPasta() {
  let veu = null;
  const aviso = setTimeout(() => {
    veu = modal(`<h2>Liberando a pasta de trabalho</h2>
      <p class="sub" style="margin-bottom:10px">O app guarda suas conversas e projetos em
        <span class="mono">Documentos/Editor Automático</span>. Se o macOS perguntar se o
        <b>Editor Automático</b> pode acessar a pasta Documentos, clique em <b>Permitir</b>.</p>
      <p class="sub">A janela do sistema pode ter aberto atrás deste app — se não estiver vendo,
        procure por ela no Dock ou com Cmd+Tab. Isto só acontece uma vez.</p>
      <div class="vivo-estado" style="margin-top:14px"><span class="vivo-giro" aria-hidden="true"></span>
        <b>Esperando a resposta do macOS…</b></div>`);
  }, PASTA_AVISO_MS);
  let r;
  try { r = await api('/api/pasta'); }
  catch (_) { clearTimeout(aviso); if (veu) veu.remove(); return; }
  clearTimeout(aviso);
  if (veu) veu.remove();
  if (r.ok) { if (veu) toast('Pasta liberada. Pode conversar.'); return; }
  modal(`<h2>${r.negado ? 'O app ficou sem acesso à pasta Documentos' : 'Não consegui abrir a pasta de trabalho'}</h2>
    <p class="sub" style="margin-bottom:10px">Sem ela a Conversa e os projetos não conseguem ser guardados
      (<span class="mono">${esc(r.pasta || '')}</span>).</p>
    ${r.negado ? `<p class="sub">Para liberar: <b>Ajustes do Sistema › Privacidade e Segurança ›
      Arquivos e Pastas › Editor Automático</b> e ligue <b>Pasta Documentos</b>. Depois clique em Tentar de novo.</p>`
      : `<p class="sub mono">${esc(r.erro || '')}</p>`}
    <div class="acoes"><button class="bt discreto" data-fechar>Fechar</button>
      <button class="bt principal" id="pasta-de-novo">Tentar de novo</button></div>`, (v) => {
    v.querySelector('[data-fechar]').onclick = () => v.remove();
    v.querySelector('#pasta-de-novo').onclick = () => { v.remove(); conferirPasta(); };
  });
}

// ---------------------------------------------------------------- ciclo
async function desenhar() {
  try {
    if (projetoAberto) return await telaProjeto();
    if (aba === 'inicio') return await telaInicio();
    if (aba === 'chat') return await telaChatLivre();
    if (aba === 'contas') return await telaContas();
    if (aba === 'ambiente') return await telaAmbiente();
    if (aba === 'guia') return await telaGuia();
    return await telaProjetos();
  } catch (e) {
    toast(e.message, true);
  }
}

async function iniciar() {
  try {
    E = await api('/api/estado');
  } catch (e) {
    raiz.innerHTML = `<div class="vazio"><h2>O app não respondeu</h2><p>${esc(e.message)}</p></div>`;
    return;
  }
  if (!E.conta.entrou) return telaPorta(E.conta.msg);
  desenhar();
  conferirPasta();
  // depois de desenhar, nunca antes: sem internet o app abre igual
  api('/api/ia').then((d) => { IA = d; desenhar(); }).catch(() => {});
  api('/api/atualizacao').then((a) => {
    ATT = a;
    desenhar();          // sempre: é o que tira o rodapé mudo
  }).catch(() => { ATT = { versao: '?', erro: 'não consegui conferir' }; desenhar(); });
}

iniciar();
