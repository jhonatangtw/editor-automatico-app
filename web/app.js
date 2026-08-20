/* Editor Automático — interface.
   Sem framework e sem build: o app precisa empacotar com PyInstaller, e cada
   passo de build a mais é um jeito a mais de quebrar na máquina do aluno. */

const TOKEN = new URLSearchParams(location.search).get('t') || '';
const raiz  = document.getElementById('raiz');

let E = null;            // estado do app (conta, serviços, ferramentas)
let aba = 'chat';
let projetoAberto = null;
let conversaAtual = null;
let ATT = null;          // versão nova publicada, quando houver

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
function moldura(conteudo) {
  const abas = [
    ['chat',      '▸', 'Conversa (beta)'],
    ['projetos',  '▤', 'Histórico'],
    ['contas',    '◈', 'Contas'],
    ['ambiente',  '⚙', 'Ambiente'],
  ];
  raiz.innerHTML = `
  <div class="app">
    <aside class="rail">
      <div class="marca"><div class="selo">EA</div>
        <div><b>Editor Automático</b><span>Editor Black Belt</span></div></div>
      <nav class="nav">
        ${abas.map(([id, g, t]) => `<button data-aba="${id}" class="${aba === id ? 'ativo' : ''}">
            <span class="glifo">${g}</span>${t}</button>`).join('')}
      </nav>
      <div class="rodape">
        ${controleAtualizacao()}
        <div class="quem"><b>${esc(E?.conta?.nome || 'Conectado')}</b>
          ${E?.conta?.offline ? 'modo offline' : 'sessão ativa'}</div>
        <button class="sair" id="sair">Sair</button>
      </div>
    </aside>
    <main class="palco" id="palco">${conteudo}</main>
  </div>`;
  raiz.querySelectorAll('[data-aba]').forEach((b) => {
    b.onclick = () => { aba = b.dataset.aba; projetoAberto = null; desenhar(); };
  });
  document.getElementById('sair').onclick = async () => {
    await post('/api/conta/sair'); iniciar();
  };
  const ba = document.getElementById('att');
  if (ba) ba.onclick = () => (ATT?.tem_nova ? atualizar() : procurarAtualizacao());
}

// O controle fica SEMPRE visível, mesmo em dia. Quando ele só aparecia havendo
// versão nova, quem estava atualizado via um rodapé mudo e concluía que não
// dava para atualizar — foi exatamente o que aconteceu no plugin antes.
function controleAtualizacao() {
  if (!ATT) return `<button class="att buscando" id="att">procurando atualização…</button>`;
  if (ATT.tem_nova) {
    return `<button class="att nova" id="att" title="${esc(ATT.notas || '')}">
      ⬆ Atualizar para ${esc(ATT.ultima)}</button>`;
  }
  if (ATT.erro) {
    return `<button class="att" id="att" title="${esc(ATT.erro)}">
      v${esc(ATT.versao)} · tentar de novo</button>`;
  }
  const leve = ATT.rodando_codigo ? ' ⬇' : '';
  return `<button class="att" id="att" title="${ATT.rodando_codigo
    ? 'rodando código atualizado sem reinstalar' : ''}">v${esc(ATT.versao)}${leve} · procurar atualização</button>`;
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
    <div class="topo">
      <div><h1>Histórico</h1>
        <p class="sub">Suas conversas. Abrir uma volta com o contexto inteiro —
          o que já foi feito, aprovado e gerado.</p></div>
      <button class="bt principal" id="nova">+ Nova conversa</button>
    </div>
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
  return `<div class="msg resposta">
    ${passos.length ? `<div class="passos">${passos.map(passoHtml).join('')}</div>` : ''}
    <div class="bolha">${marcar(m.content || '')}</div></div>`;
}

function passoHtml(p) {
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
function mostrarFalha(ultimoTexto) {
  const c = document.getElementById('conversa');
  if (!c) return;
  c.insertAdjacentHTML('beforeend', `
    <div class="msg resposta"><div class="bolha">
      <p>A conexão com o Claude não está disponível agora.</p>
      <div class="falha-acoes">
        <button class="bt" id="f-toolspro">Reconectar ao Tools PRO</button>
        <button class="bt" id="f-reconectar">Reconectar</button>
        <button class="bt" id="f-trocar">Trocar conta</button>
        <button class="bt principal" id="f-tentar">Tentar novamente</button>
      </div>
    </div></div>`);
  rolarFim();
  document.getElementById('f-reconectar').onclick = async () => {
    const r = await post('/api/claude/testar');
    toast(r.msg, !r.ok);
    if (r.ok) desenhar();
  };
  const ft = document.getElementById('f-toolspro');
  if (ft) ft.onclick = () => reconectarToolsPro();
  document.getElementById('f-trocar').onclick = () => trocarMetodo();
  document.getElementById('f-tentar').onclick = () => {
    const e = document.getElementById('entrada');
    if (e) { e.value = ultimoTexto || ''; document.getElementById('enviar').click(); }
  };
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
       <div class="msg resposta" id="vivo"><div class="passos" id="passos-vivos"></div></div>`);
    rolarFim();

    try {
      const r = await post('/api/conversa', { texto, anexos, conversa: conversaAtual });
      let desenhados = 0;
      const t = setInterval(async () => {
        const s = await api('/api/tarefas/' + r.tarefa);
        const cx = document.getElementById('passos-vivos');
        if (cx) {
          // redesenha só o que mudou: o passo em curso vira ✓ quando termina
          const html = (s.passos || []).map(passoHtml).join('');
          if (html !== cx.dataset.ultimo) {
            cx.innerHTML = html; cx.dataset.ultimo = html;
            if ((s.passos || []).length !== desenhados) { desenhados = s.passos.length; rolarFim(); }
          }
        }
        if (s.estado === 'pronto') { clearInterval(t); conversando = false; desenhar(); }
        else if (s.estado === 'erro') {
          clearInterval(t); conversando = false;
          const vivo = document.getElementById('vivo');
          if (vivo) vivo.remove();
          mostrarFalha(texto);
        }
      }, 900);
    } catch (e) {
      conversando = false; toast(e.message, true); desenhar();
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
  const s = E.servicos;
  const claudeHtml = await cartaoClaude();
  moldura(`
    <div class="topo">
      <div><h1>Contas</h1>
        <p class="sub">Suas credenciais ficam no ${esc(s.cofre === 'arquivo' ? 'disco' : 'cofre do sistema')}, nesta máquina. Nunca no nosso servidor.</p></div>
    </div>
    ${s.cofre === 'arquivo' ? `<div class="aviso" style="margin-bottom:16px">
        O cofre do sistema não está disponível — as chaves ficam num arquivo protegido.</div>` : ''}
    <div class="cartao" style="margin-bottom:12px">
      <div class="servico">
        <div>
          <div class="titulo">Sua conta
            <span class="pastilha ok"><i class="ponto"></i>${esc(E?.conta?.nome || 'conectado')}</span></div>
          <div class="papel">Editor Black Belt — é ela que libera o app${E?.conta?.adm ? ' · administrador' : ''}</div>
          <div id="saida-senha" style="margin-top:10px"></div>
        </div>
        <div style="display:flex;gap:8px;align-items:flex-start">
          <button class="bt" id="trocar-senha">Trocar senha</button>
          <button class="bt discreto perigo" id="sair-conta">Sair</button>
        </div>
      </div>
    </div>
    <div class="cartao">
      ${claudeHtml}
      ${s.servicos.filter((x) => x.id !== 'claude').map((x) => cartaoServico(x)).join('')}
    </div>`);

  document.getElementById('trocar-senha').onclick = () => telaSenha();
  document.getElementById('sair-conta').onclick = async () => {
    await post('/api/conta/sair'); iniciar();
  };
  ligarClaude();
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
      b.disabled = false; b.textContent = 'Testar';
    };
  });

  document.querySelectorAll('[data-salvar]').forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.salvar;
      const campo = document.querySelector(`[data-chave="${id}"]`);
      try {
        await post('/api/servicos/chave', { servico: id, valor: campo.value.trim() });
        campo.value = ''; toast('Guardada no cofre.'); iniciar();
      } catch (e) { toast(e.message, true); }
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
          try {
            const r = await post('/api/servicos/entrar',
              { servico: sv, chave: v.querySelector('#mk2').value.trim() });
            v.remove(); toast(r.msg, !r.ok); iniciar();
          } catch (e) { toast(e.message, true); }
        };
      });
    };
  });

  document.querySelectorAll('[data-entrar]').forEach((b) => {
    b.onclick = async () => {
      const r = await post('/api/servicos/entrar', { servico: b.dataset.entrar });
      toast(r.msg || 'Abri o navegador.', !r.ok);
    };
  });
}

async function cartaoClaude() {
  let c;
  try { c = await api('/api/claude'); } catch (e) { return ''; }
  return `<div class="servico" id="cartao-claude">
    <div>
      <div class="titulo">Claude
        <span class="pastilha ${c.conectado ? 'ok' : 'erro'}"><i class="ponto"></i>${c.conectado ? 'conectado' : 'não conectado'}</span>
      </div>
      <div class="papel">${esc(c.rotulo)}${c.conta ? ' · ' + esc(c.conta) : ''}</div>
      ${c.msg ? `<div class="aviso" style="margin-top:10px">${esc(c.msg)}</div>` : ''}
      <div id="saida-claude" style="margin-top:10px"></div>
    </div>
    <div style="display:flex;gap:8px;align-items:flex-start">
      ${c.entrar ? `<button class="bt principal" id="claude-entrar">Entrar</button>` : ''}
      ${c.instalar ? `<button class="bt principal" id="claude-instalar">Instalar</button>` : ''}
      <button class="bt" id="claude-testar">${c.conectado ? 'Testar' : 'Reconectar'}</button>
      <button class="bt discreto" id="claude-trocar">Trocar método</button>
    </div>
  </div>`;
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
    t.disabled = false; t.textContent = 'Testar';
  };
  const tr = document.getElementById('claude-trocar');
  if (tr) tr.onclick = () => trocarMetodo();

  // "Rode `claude` no Terminal" é o conselho que este app existe para não dar.
  const en = document.getElementById('claude-entrar');
  if (en) en.onclick = async () => {
    en.disabled = true;
    try { const r = await post('/api/claude/entrar'); toast(r.msg, !r.ok); }
    catch (e) { toast(e.message, true); }
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
        v.remove(); toast('Método atualizado.'); desenhar();
      } catch (e) { toast(e.message, true); }
    };
  });
}

function cartaoServico(x) {
  const conectado = x.pronto;
  const acao = x.modo === 'chave'
    ? `<div class="linha-chave">
         <input data-chave="${x.id}" type="password" placeholder="${conectado ? 'Trocar a chave…' : 'Cole a chave de API'}">
         <button class="bt" data-salvar="${x.id}">Guardar</button>
       </div>`
    : `<button class="bt ${conectado ? '' : 'principal'}" data-entrar="${x.id}">
         ${conectado ? 'Entrar de novo' : 'Entrar com a conta'}</button>
       ${x.id === 'minimax' ? '<button class="bt discreto" data-chave-cli="minimax">ou usar chave</button>' : ''}`;

  return `<div class="servico">
    <div>
      <div class="titulo">${esc(x.titulo)}
        <span class="pastilha ${conectado ? 'ok' : ''}"><i class="ponto"></i>${conectado ? 'conectado' : 'sem credencial'}</span>
        ${x.verificado === false ? '<span class="pastilha aviso">endereço não verificado</span>' : ''}
      </div>
      <div class="papel">${esc(x.papel)}${x.conta ? ' · ' + esc(x.conta) : ''}${x.fim ? ' · ' + esc(x.fim) : ''}</div>
      ${x.alerta ? `<div class="aviso" style="margin-top:10px">${esc(x.alerta)}</div>` : ''}
      ${x.modo === 'anthropic' && !x.tem_cli
        ? `<div class="sub" style="margin-top:8px;font-size:12px">Para entrar com a conta:
             <code>brew tap anthropics/tap && brew install ant</code> — ou cole uma chave de API.</div>
           <div class="linha-chave"><input data-chave="claude" type="password" placeholder="sk-ant-…">
             <button class="bt" data-salvar="claude">Guardar</button></div>` : ''}
      <div data-saida="${x.id}" style="margin-top:10px"></div>
    </div>
    <div style="display:flex;gap:8px;align-items:flex-start">
      ${acao}
      <button class="bt discreto" data-testar="${x.id}">Testar</button>
    </div>
  </div>`;
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
  const d = await api('/api/ambiente');
  const pl = await api('/api/plugin').catch(() => null);
  const pn = await api('/api/ponte').catch(() => null);
  if (pl && pn) pl.ponte = pn;
  const faltando = d.itens.filter((i) => !i.tem && i.essencial && i.instalavel);

  moldura(`
    <div class="topo">
      <div><h1>Ambiente</h1>
        <p class="sub">O app instala o que falta. Você não precisa abrir o Terminal.</p></div>
      ${faltando.length ? `<button class="bt principal" id="tudo">Instalar o que falta (${faltando.length})</button>` : ''}
    </div>
    ${d.pronto ? `<div class="aviso" style="background:rgba(61,214,140,.1);color:var(--ok);border-color:rgba(61,214,140,.2);margin-bottom:16px">
        ✓ Tudo que é essencial está instalado.</div>`
      : `<div class="aviso ruim" style="margin-bottom:16px">Falta: ${esc(d.faltam.join(', '))}</div>`}
    ${!d.brew ? (d.gerenciador === 'winget' ? `<div class="aviso" style="margin-bottom:16px">
      O <b>winget</b> não respondeu — sem ele não consigo instalar o FFmpeg sozinho.
      Ele vem no Windows 10 e 11: abra a Microsoft Store e instale o
      <b>Instalador de Aplicativo</b>.</div>` : `<div class="aviso" style="margin-bottom:16px">
      O Homebrew não está instalado — sem ele não consigo instalar FFmpeg sozinho.
      <button class="bt principal" id="brew" style="margin-top:10px">Instalar o Homebrew</button>
      <div style="font-size:11px;opacity:.7;margin-top:6px">Abre o Terminal com o
      instalador oficial. Ele pede a senha do seu Mac — é o instalador pedindo, não o app.</div>
      </div>`) : ''}
    ${pl ? cartaoPlugin(pl) : ''}
    <div class="cartao">
      ${d.itens.map((i) => `
        <div class="dep">
          <div class="dep-marca ${i.tem ? 'ok' : i.essencial ? 'falta' : 'opcional'}">${i.tem ? '✓' : i.essencial ? '!' : '○'}</div>
          <div style="flex:1;min-width:0">
            <div class="dep-nome">${esc(i.nome)}
              ${!i.essencial ? '<span class="credito" style="background:rgba(255,255,255,.06);color:var(--texto-3)">opcional</span>' : ''}</div>
            <div class="dep-para">${esc(i.para)}</div>
            ${!i.tem && i.manual ? `<div class="dep-para" style="color:var(--ouro)">${esc(i.manual)}</div>` : ''}
          </div>
          <div class="dep-versao">${esc(i.versao || '')}</div>
          ${!i.tem && i.instalavel ? `<button class="bt" data-inst="${i.id}">Instalar</button>` : ''}
        </div>`).join('')}
    </div>`);

  const rodar = (qual) => {
    const v = modal(`<h2>Instalando</h2>
      <div class="portao" id="log" style="max-height:280px">preparando…</div>`);
    post('/api/ambiente/instalar', qual ? { qual } : {}).then((r) => {
      const t = setInterval(async () => {
        const s = await api('/api/tarefas/' + r.tarefa);
        const l = v.querySelector('#log');
        l.textContent = (s.log || []).join('\n') || 'trabalhando…';
        l.scrollTop = l.scrollHeight;
        if (s.estado === 'pronto') { clearInterval(t); v.remove(); toast('Pronto.'); desenhar(); }
        else if (s.estado === 'erro') { clearInterval(t); v.remove(); toast(s.erro, true); desenhar(); }
      }, 1200);
    }).catch((e) => { v.remove(); toast(e.message, true); });
  };
  const bw = document.getElementById('brew');
  if (bw) bw.onclick = async () => {
    bw.disabled = true;
    try { const r = await post('/api/ambiente/gerenciador'); toast(r.msg, !r.ok); }
    catch (e) { toast(e.message, true); }
    bw.disabled = false;
  };
  const bt = document.getElementById('tudo');
  if (bt) bt.onclick = () => rodar(null);
  document.querySelectorAll('[data-inst]').forEach((b) => { b.onclick = () => rodar(b.dataset.inst); });
  ligarPlugin();
}

// O plugin é a PONTE: sem ele o app não escreve uma linha na timeline. Por isso
// ele fica no topo do Ambiente, e a instalação é um botão — não um tutorial.
function cartaoPlugin(pl) {
  const tem = !!pl.instalado;
  const cor = !tem ? 'var(--broll)' : pl.tem_nova ? 'var(--ouro)' : 'var(--ok)';
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
      <button class="bt ${tem && !pl.tem_nova ? '' : 'principal'}" id="pl-instalar"
        style="color:${tem && !pl.tem_nova ? '' : cor}">${rotulo}</button>
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
          toast(st.resultado?.msg || 'Instalador aberto.'); desenhar();
        } else if (st.estado === 'erro') { clearInterval(t); v.remove(); toast(st.erro, true); }
      }, 900);
    }).catch((e) => { v.remove(); toast(e.message, true); });
  };
}

// ---------------------------------------------------------------- ciclo
async function desenhar() {
  try {
    if (projetoAberto) return await telaProjeto();
    if (aba === 'chat') return await telaChatLivre();
    if (aba === 'contas') return await telaContas();
    if (aba === 'ambiente') return await telaAmbiente();
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
  // depois de desenhar, nunca antes: sem internet o app abre igual
  api('/api/atualizacao').then((a) => {
    ATT = a;
    desenhar();          // sempre: é o que tira o rodapé mudo
  }).catch(() => { ATT = { versao: '?', erro: 'não consegui conferir' }; desenhar(); });
}

iniciar();
