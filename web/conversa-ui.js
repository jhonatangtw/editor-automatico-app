/* Conversa — o componente da tela de chat, no estilo do Claude Code.

   Reutilizável de propósito: o MESMO arquivo monta a Conversa no Editor
   Automático e no painel do Tools PRO, dentro do Premiere. Por isso:
   - não lê nenhuma global do app.js — tudo entra por `montarConversa(el, op)`;
   - toda chamada vai para `op.api + '/api/…'` com `X-Token: op.token`, sem
     supor que a página foi servida pelo próprio app;
   - o CSS (conversa-ui.css) traz as próprias cores, com as do app como base
     quando existirem.

   Uso:
     const cv = montarConversa(document.getElementById('x'), {
       api: 'http://127.0.0.1:PORTA', token: 'TOKEN', compacto: false,
       conversa: null,                      // id; null = a mais recente
       aoTrocarConversa(cid) {},            // /nova criou outra conversa
       aoTerminar({conversa, meta}) {},     // uma resposta acabou
       aoPedirConta(provedor) {},           // provedor sem login escolhido
       aoMudarPipeline() {},                // aprovou/recusou pelo cartão
       acoesFalha: [{ rotulo, acao }],      // botões extras quando a IA falha
       boasVindas: '<p>…</p>',              // HTML CONFIÁVEL do app (não do usuário)
       atalhos: ['Analise esta timeline'],
     });
     cv.desmontar();

   Segurança: todo texto que vem da IA, do usuário ou do disco passa por
   `esc()` antes de virar HTML. O markdown é feito à mão em cima do texto já
   escapado; link só sai como <a> se for http(s). Sem biblioteca, sem CDN —
   o app roda offline. */
(function (raizGlobal) {
  'use strict';

  // ================================================================ util puro
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const semAcento = (t) => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  const base = (c) => String(c || '').replace(/[\\/]+$/, '').split(/[\\/]/).pop() || String(c || '');

  const IMAGEM = /\.(png|jpe?g|gif|webp|heic|bmp|svg)$/i;

  function duracao(seg) {
    if (seg == null || !isFinite(seg)) return '';
    seg = Math.max(0, +seg);
    if (seg < 1) return seg.toFixed(1).replace('.', ',') + ' s';
    if (seg < 60) return Math.round(seg) + ' s';
    const m = Math.floor(seg / 60), s = Math.round(seg % 60);
    return `${m} min ${String(s).padStart(2, '0')} s`;
  }

  function numero(n) {
    n = +n || 0;
    if (n >= 1e6) return (n / 1e6).toFixed(1).replace('.', ',') + ' mi';
    if (n >= 1e4) return Math.round(n / 1e3) + ' mil';
    return n.toLocaleString('pt-BR');
  }

  // ================================================================ markdown
  // Entrada: texto CRU. Saída: HTML seguro. Escapa primeiro, formata depois.
  function inline(cru) {
    const guardados = [];
    const guardar = (html) => { guardados.push(html); return '\u0000' + (guardados.length - 1) + '\u0000'; };
    let t = String(cru);
    // código em linha antes de tudo: o que está dentro não é formatado
    t = t.replace(/`([^`\n]+)`/g, (_, c) => guardar(`<code>${esc(c)}</code>`));
    // links [texto](http…) — qualquer outro esquema vira texto
    t = t.replace(/\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, txt, url) =>
      guardar(`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(txt)}</a>`));
    t = esc(t);
    t = t.replace(/\*\*([^*\n]+)\*\*/g, '<b>$1</b>')
         .replace(/__([^_\n]+)__/g, '<b>$1</b>')
         .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,;:!?]|$)/g, '$1<i>$2</i>')
         .replace(/~~([^~\n]+)~~/g, '<s>$1</s>');
    return t.replace(/\u0000(\d+)\u0000/g, (_, i) => guardados[+i]);
  }

  function blocoCodigo(linguagem, linhas) {
    return `<div class="cv-codigo"><div class="cv-codigo-topo"><span>${esc(linguagem || 'código')}</span>` +
      `<button type="button" class="cv-copiar" data-copiar>Copiar</button></div>` +
      `<pre><code>${esc(linhas.join('\n'))}</code></pre></div>`;
  }

  function md(texto) {
    const linhas = String(texto ?? '').replace(/\r\n?/g, '\n').split('\n');
    const out = [];
    let para = [], lista = null, codigo = null;
    const fecharPara = () => { if (para.length) { out.push(`<p>${para.map(inline).join('<br>')}</p>`); para = []; } };
    const fecharLista = () => {
      if (lista) { out.push(`<${lista.tipo}>${lista.itens.map((x) => `<li>${inline(x)}</li>`).join('')}</${lista.tipo}>`); lista = null; }
    };
    for (let i = 0; i < linhas.length; i++) {
      const l = linhas[i];
      if (codigo) {
        if (/^\s*```/.test(l)) { out.push(blocoCodigo(codigo.lang, codigo.linhas)); codigo = null; }
        else codigo.linhas.push(l);
        continue;
      }
      const cerca = l.match(/^\s*```\s*([\w+#.-]*)\s*$/);
      if (cerca) { fecharPara(); fecharLista(); codigo = { lang: cerca[1], linhas: [] }; continue; }
      if (!l.trim()) { fecharPara(); fecharLista(); continue; }
      const tit = l.match(/^(#{1,4})\s+(.*)$/);
      if (tit) { fecharPara(); fecharLista(); const n = Math.min(4, tit[1].length + 2); out.push(`<h${n}>${inline(tit[2])}</h${n}>`); continue; }
      if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(l)) { fecharPara(); fecharLista(); out.push('<hr>'); continue; }
      // tabela: | a | b | seguida de |---|---|
      if (/^\s*\|.*\|\s*$/.test(l) && /^\s*\|[\s:|-]+\|\s*$/.test(linhas[i + 1] || '')) {
        fecharPara(); fecharLista();
        const cel = (x) => x.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
        const cab = cel(l); i += 1;
        const corpo = [];
        while (i + 1 < linhas.length && /^\s*\|.*\|\s*$/.test(linhas[i + 1])) { i += 1; corpo.push(cel(linhas[i])); }
        out.push(`<div class="cv-tabela"><table><thead><tr>${cab.map((c) => `<th>${inline(c)}</th>`).join('')}</tr></thead>` +
          `<tbody>${corpo.map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`);
        continue;
      }
      const cit = l.match(/^\s*>\s?(.*)$/);
      if (cit) { fecharPara(); fecharLista(); out.push(`<blockquote>${inline(cit[1])}</blockquote>`); continue; }
      const ul = l.match(/^\s*[-*•]\s+(.*)$/), ol = l.match(/^\s*\d+[.)]\s+(.*)$/);
      if (ul || ol) {
        fecharPara();
        const tipo = ul ? 'ul' : 'ol';
        if (!lista || lista.tipo !== tipo) { fecharLista(); lista = { tipo, itens: [] }; }
        lista.itens.push((ul || ol)[1]);
        continue;
      }
      if (lista && /^\s{2,}\S/.test(l)) { lista.itens[lista.itens.length - 1] += ' ' + l.trim(); continue; }
      fecharLista();
      para.push(l);
    }
    if (codigo) out.push(blocoCodigo(codigo.lang, codigo.linhas));   // cerca aberta: ainda escrevendo
    fecharPara(); fecharLista();
    return out.join('');
  }

  // ================================================================ ícones
  const SVG = (d) => `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
  const ICONE = {
    arquivo: SVG('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'),
    lapis: SVG('<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M14 6l4 4"/>'),
    terminal: SVG('<path d="M4 6l6 6-6 6"/><path d="M12 19h8"/>'),
    busca: SVG('<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>'),
    globo: SVG('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>'),
    peca: SVG('<path d="M10 4a2 2 0 1 1 4 0v2h4v4h-2a2 2 0 1 0 0 4h2v4H6v-4h2a2 2 0 1 0 0-4H6V6h4z"/>'),
    lista: SVG('<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>'),
    agente: SVG('<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>'),
    imagem: SVG('<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 17l-6-6-9 9"/>'),
    filme: SVG('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 5v14M17 5v14M3 9h4M3 15h4M17 9h4M17 15h4"/>'),
    cerebro: SVG('<path d="M12 4a3 3 0 0 0-6 1 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1z"/><path d="M12 4a3 3 0 0 1 6 1 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1"/>'),
    estrela: SVG('<path d="M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z"/>'),
    aviso: SVG('<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>'),
    clipe: SVG('<path d="M21 11l-8.5 8.5a5 5 0 0 1-7-7L14 4a3.5 3.5 0 0 1 5 5l-8.5 8.5a2 2 0 0 1-3-3L15 7"/>'),
    enviar: SVG('<path d="M5 12h14M13 6l6 6-6 6"/>'),
    parar: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg>',
    pasta: SVG('<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'),
    timeline: SVG('<rect x="3" y="5" width="18" height="5" rx="1.5"/><rect x="3" y="14" width="11" height="5" rx="1.5"/><path d="M17 12v9"/>'),
    copiar: SVG('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>'),
    tocar: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>',
    pausar: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1" fill="currentColor"/><rect x="13.5" y="5" width="4" height="14" rx="1" fill="currentColor"/></svg>',
    baixar: SVG('<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>'),
  };

  // ================================================================ rótulos das ações
  // Nome amigável em português + o alvo curto, como o Claude Code mostra.
  const TOOLSPRO = {
    pr_marcadores_criar: 'Criou marcadores', pr_marcadores_listar: 'Leu os marcadores',
    pr_marcadores_apagar: 'Apagou marcadores', pr_timeline_listar: 'Leu a timeline',
    pr_timeline_remover: 'Removeu clipes da timeline', pr_timeline_mudo: 'Silenciou trilhas',
    pr_timeline_selecionar: 'Selecionou clipes', pr_projeto_salvar: 'Salvou o projeto',
    pr_sequencias_listar: 'Listou as sequências', pr_sequencia_ativar: 'Ativou uma sequência',
    pr_midia_importar: 'Importou mídia', pr_midia_listar: 'Listou a mídia',
    pr_zoom_aplicar: 'Aplicou zoom', pr_zoom_limpar: 'Limpou o zoom', pr_autoclip: 'Cortou com o Autoclip',
    pr_extendscript: 'Rodou script no Premiere', ae_extendscript: 'Rodou script no After Effects',
    ae_legendas_importar: 'Importou legendas no After', ae_legendas_limpar: 'Limpou as legendas no After',
    ae_titulos_inserir: 'Inseriu títulos no After', pr_organizar_aplicar: 'Organizou o projeto',
    pr_organizar_analisar: 'Analisou a organização', pr_organizar_desfazer: 'Desfez a organização',
    ae_organizar_aplicar: 'Organizou o projeto do After', pr_smoothify: 'Aplicou Smoothify',
    ae_smoothify: 'Aplicou Smoothify no After', pr_copiar_atributos: 'Copiou atributos', pr_anypaste: 'Colou com AnyPaste',
    pr_legenda_nativa_criar: 'Criou a faixa de legenda', pr_legendas_mogrt_info: 'Leu os estilos de legenda',
    pr_legendas_mogrt_aplicar: 'Colocou legendas animadas',
  };
  const EDITOR = {
    adobe_estado: 'Conferiu o Adobe', ver_adobe: 'Conferiu o Adobe', timeline_ler: 'Leu a timeline',
    adobe_verificar: 'Testou a ponte com o Adobe', adobe_extendscript: 'Rodou script no Premiere',
    projeto_criar: 'Criou o projeto', criar_projeto: 'Criou o projeto', projeto_estado: 'Conferiu o projeto',
    ver_estado: 'Conferiu o projeto', etapa_rodar: 'Rodou a etapa', rodar_etapa: 'Rodou a etapa',
    etapa_aprovar: 'Registrou a aprovação de', aprovar_etapa: 'Registrou a aprovação de',
    etapa_rejeitar: 'Registrou a recusa de', rejeitar_etapa: 'Registrou a recusa de',
    item_julgar: 'Julgou o item', julgar_item: 'Julgou o item', motores_listar: 'Consultou os preços dos motores',
    ver_motores: 'Consultou os preços dos motores', projetos_listar: 'Listou os projetos',
  };

  function rotuloComando(cmd, descricao) {
    let c = String(cmd || '').trim();
    // tira `cd pasta &&`, variáveis de ambiente e prefixos comuns
    c = c.replace(/^(cd\s+("[^"]*"|'[^']*'|\S+)\s*(&&|;)\s*)+/, '');
    c = c.replace(/^((\w+=("[^"]*"|'[^']*'|\S*))\s+)+/, '');
    c = c.replace(/^(sudo|env|time|nohup|exec)\s+/, '');
    const prog = base((c.match(/^("[^"]+"|'[^']+'|\S+)/) || [''])[0].replace(/^["']|["']$/g, ''));
    const p = prog.toLowerCase();
    const alvo = descricao || '';
    if (p === 'higgsfield') {
      if (/\b(cost|custo|price)\b/.test(c)) return { icone: 'imagem', texto: 'Orçou no Higgsfield', alvo };
      if (/\bgenerate\b/.test(c)) return { icone: /video|kling|seedance|wan|hailuo|minimax/i.test(c) ? 'filme' : 'imagem', texto: /video|kling|seedance|wan|hailuo|minimax/i.test(c) ? 'Gerou vídeo no Higgsfield' : 'Gerou imagem no Higgsfield', alvo };
      return { icone: 'imagem', texto: 'Usou o Higgsfield', alvo };
    }
    if (p === 'heygen') return { icone: 'agente', texto: 'Usou o HeyGen', alvo };
    if (p === 'whisper' || p === 'whisper-cli') return { icone: 'terminal', texto: 'Transcreveu com Whisper', alvo };
    if (p === 'ffprobe') return { icone: 'filme', texto: 'Mediu com ffprobe', alvo };
    if (p === 'ffmpeg') return { icone: 'filme', texto: 'Rodou ffmpeg', alvo };
    if (/^python[\d.]*$/.test(p)) return { icone: 'terminal', texto: 'Rodou um script Python', alvo };
    if (p === 'ls' || p === 'find') return { icone: 'busca', texto: 'Listou arquivos', alvo };
    if (p === 'cat' || p === 'head' || p === 'tail') return { icone: 'arquivo', texto: 'Leu um arquivo', alvo };
    return { icone: 'terminal', texto: prog ? `Rodou ${prog}` : 'Rodou um comando', alvo };
  }

  function rotuloAcao(p) {
    const e = (p && p.entrada) || {};
    let nome = String((p && p.nome) || '');
    let servidor = (p && p.servidor) || '';
    const m = nome.match(/^mcp__(.+?)__(.+)$/);
    if (m) { servidor = m[1]; nome = m[2]; }
    const arq = e.file_path || e.path || e.notebook_path || '';
    const resumo = (p && p.resumo) || '';
    const sv = semAcento(servidor);

    if (!servidor || sv === 'editor') {
      if (EDITOR[nome]) {
        const comEtapa = /etapa|aprova|recusa|item/.test(EDITOR[nome]) && !/Conferiu|Listou/.test(EDITOR[nome]);
        return { icone: 'peca', texto: EDITOR[nome] + (comEtapa && (e.etapa || e.item) ? ' ' + (e.item || e.etapa) : ''),
                 alvo: nome.includes('extendscript') ? (e.descricao || '') : '' };
      }
    }
    if (/toolspro|tools-pro/.test(sv)) {
      if (nome === 'pr_timeline_colocar') {
        const lst = e.clipes || e.itens || e.arquivos || e.midias || [];
        const n = Array.isArray(lst) ? lst.length : 0;
        return { icone: 'filme', texto: n ? `Colocou ${n} ${n === 1 ? 'clipe' : 'clipes'} na timeline (Tools PRO)` : 'Colocou clipes na timeline (Tools PRO)', alvo: '' };
      }
      if (TOOLSPRO[nome]) return { icone: 'filme', texto: TOOLSPRO[nome] + ' (Tools PRO)', alvo: '' };
      if (/_info$/.test(nome)) return { icone: 'peca', texto: 'Consultou o Tools PRO', alvo: nome.replace(/_info$/, '').replace(/_/g, ' ') };
      return { icone: 'filme', texto: nome.replace(/^(pr|ae)_/, '').replace(/_/g, ' ') + ' (Tools PRO)', alvo: '' };
    }
    if (/higgsfield/.test(sv)) {
      if (/video/i.test(nome)) return { icone: 'filme', texto: 'Gerou vídeo no Higgsfield', alvo: e.prompt ? String(e.prompt).slice(0, 80) : '' };
      if (/image|imagem|generate/i.test(nome)) return { icone: 'imagem', texto: 'Gerou imagem no Higgsfield', alvo: e.prompt ? String(e.prompt).slice(0, 80) : '' };
      return { icone: 'imagem', texto: 'Usou o Higgsfield', alvo: nome.replace(/_/g, ' ') };
    }
    if (servidor) return { icone: 'peca', texto: nome.replace(/_/g, ' '), alvo: servidor };

    switch (nome) {
      case 'Read': return { icone: IMAGEM.test(arq) ? 'imagem' : 'arquivo', texto: (IMAGEM.test(arq) ? 'Viu ' : 'Leu ') + base(arq || resumo), alvo: '' };
      case 'Write': return { icone: 'lapis', texto: 'Escreveu ' + base(arq || resumo), alvo: '' };
      case 'Edit': case 'MultiEdit': return { icone: 'lapis', texto: 'Editou ' + base(arq || resumo), alvo: '' };
      case 'NotebookEdit': return { icone: 'lapis', texto: 'Editou ' + base(arq || resumo), alvo: '' };
      case 'Glob': return { icone: 'busca', texto: 'Procurou arquivos', alvo: e.pattern || resumo };
      case 'Grep': return { icone: 'busca', texto: 'Buscou no texto', alvo: e.pattern || resumo };
      case 'WebFetch': { let h = e.url || resumo; try { h = new URL(h).host; } catch (_) { /* fica o texto */ } return { icone: 'globo', texto: 'Abriu ' + h, alvo: '' }; }
      case 'WebSearch': return { icone: 'globo', texto: 'Pesquisou na web', alvo: e.query || resumo };
      case 'Task': case 'Agent': return { icone: 'agente', texto: 'Chamou um agente', alvo: e.description || e.subagent_type || resumo };
      case 'Skill': return { icone: 'estrela', texto: 'Usou a skill ' + (nomeSkill(tecnicoDaSkill(p)) || 'do Claude'), alvo: '' };
      case 'TodoWrite': return { icone: 'lista', texto: 'Atualizou as tarefas', alvo: '' };
      case 'ToolSearch': return { icone: 'busca', texto: 'Carregou ferramentas', alvo: e.query || '' };
      case 'Bash': case 'terminal': case 'shell': return rotuloComando(e.command || resumo, e.description);
      default: return { icone: 'peca', texto: nome.replace(/_/g, ' ') || 'Ação', alvo: resumo };
    }
  }

  // ================================================================ estados derivados
  function tarefasAtuais(passosVivos, mensagens) {
    const achar = (ps) => { for (let i = (ps || []).length - 1; i >= 0; i--) if (ps[i] && Array.isArray(ps[i].tarefas)) return ps[i].tarefas; return null; };
    let itens = achar(passosVivos);
    if (!itens) {
      for (let i = (mensagens || []).length - 1; i >= 0; i--) {
        const m = mensagens[i];
        if (m.role === 'assistant') { itens = achar(m.passos); break; }
      }
    }
    if (!itens || !itens.length) return null;
    if (itens.every((t) => t.estado === 'feito')) return null;   // tudo feito: o painel some
    return itens;
  }

  // ---- nome da skill: o técnico (para o tooltip) e o amigável (para a tela)
  // ⚠️ A entrada da Skill às vezes chega como TEXTO JSON (ou truncada, com
  // "…" no fim) e o rodapé mostrava `{"skill": "editor-autom…` cru. Tudo
  // que vier passa por aqui antes de virar texto na tela.
  const SKILLS_NOMES = {
    'editor-automatico-de-broll': 'Editor automático de b-roll', 'skill-black-belt': 'Black Belt',
    'hooks-meat-hook': 'Hooks Meat Hook', 'blackbelt-omni': 'Black Belt Omni', 'motion-omni-vsl': 'Motion Omni VSL',
    'vibe-motion': 'Vibe Motion', 'motion-design': 'Motion design', 'photorealism-prompts': 'Prompts fotorrealistas',
    'video-prompt-builder': 'Prompts de vídeo', 'avatar-vsl-video-prompts': 'Prompts de avatar para VSL',
    pixar3d: 'Pixar 3D', 'storyboard-viral-3d': 'Storyboard viral 3D', 'omni-flash-reverse': 'Omni Flash reverso',
    'video-to-flow': 'Vídeo para o Flow', 'clone-ad-validado': 'Clone de AD validado',
    'plataforma-ia-higgsfield': 'Plataforma de IA (Higgsfield)', 'boas-praticas-black-belt': 'Boas práticas Black Belt',
    'editor-de-reels-do-jhon': 'Editor de Reels', 'cortar-aula': 'Cortar aula', 'conferir-ads-por-frame': 'Conferir ADs por quadro',
    'marcar-vsl': 'Marcar VSL', 'conferir-broll': 'Conferir b-roll', 'broll-narrativo': 'B-roll narrativo',
  };
  const PALAVRAS_PT = { automatico: 'automático', broll: 'b-roll', 'b': 'b', video: 'vídeo', videos: 'vídeos', pratica: 'prática',
    praticas: 'práticas', legenda: 'legenda', audio: 'áudio', analise: 'análise', criacao: 'criação', edicao: 'edição',
    conferencia: 'conferência', ads: 'ADs', ad: 'AD', vsl: 'VSL', ia: 'IA', ugc: 'UGC', '3d': '3D' };

  function tecnicoDaSkill(p) {
    if (!p) return null;
    let e = p.entrada;
    if (typeof e === 'string') { try { e = JSON.parse(e); } catch (_) { e = { skill: e }; } }
    let n = e && typeof e === 'object' ? (e.skill || e.command || e.name) : null;
    const doTexto = (t) => {
      t = String(t || '').trim();
      const m = t.match(/"(?:skill|command|name)"\s*:\s*"([^"…]+)/);
      if (m) return m[1];
      return /^\/?[\w:.-]+$/.test(t) ? t : null;
    };
    if (typeof n === 'string' && /^\s*[{\[]/.test(n)) n = doTexto(n);
    if (!n) n = doTexto(p.resumo);
    if (typeof n !== 'string') return null;
    n = n.trim().replace(/^\//, '');
    return n || null;
  }

  function nomeSkill(tecnico) {
    const t = String(tecnico || '').trim();
    if (!t) return '';
    const curto = t.includes(':') ? t.split(':').pop() : t;      // "editor-broll:marcar-vsl"
    if (SKILLS_NOMES[curto]) return SKILLS_NOMES[curto];
    // nome cortado no meio ("editor-autom"): completa se só uma skill conhecida começa assim
    if (curto.length >= 6) {
      const xs = Object.keys(SKILLS_NOMES).filter((k) => k.startsWith(curto));
      if (xs.length === 1) return SKILLS_NOMES[xs[0]];
    }
    const ps = curto.replace(/[_-]+/g, ' ').trim().split(/\s+/).map((w) => PALAVRAS_PT[w.toLowerCase()] || w.toLowerCase());
    const f = ps.join(' ');
    return f.charAt(0).toUpperCase() + f.slice(1);
  }

  // "hoje 17:40", "ontem 09:12", "seg 10:00", "12/09", "12/09/25"
  function quandoRelativo(seg, agoraMs) {
    if (!seg || !isFinite(seg)) return '';
    const d = new Date(seg * 1000), h = new Date(agoraMs || Date.now());
    const p2 = (n) => String(n).padStart(2, '0');
    const hm = `${p2(d.getHours())}:${p2(d.getMinutes())}`;
    const dia = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
    const dif = Math.round((dia(h) - dia(d)) / 86400000);
    if (dif <= 0) return 'hoje ' + hm;
    if (dif === 1) return 'ontem ' + hm;
    if (dif < 7) return ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'][d.getDay()] + ' ' + hm;
    return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}` + (d.getFullYear() !== h.getFullYear() ? '/' + String(d.getFullYear()).slice(2) : '');
  }

  function skillEmUso(mensagens, passosVivos) {
    const achar = (ps) => {
      for (let i = (ps || []).length - 1; i >= 0; i--) {
        const p = ps[i];
        if (p && p.tipo === 'ferramenta' && p.nome === 'Skill') { const n = tecnicoDaSkill(p); if (n) return n; }
      }
      return null;
    };
    const v = achar(passosVivos);
    if (v) return v;
    for (let i = (mensagens || []).length - 1; i >= 0; i--) {
      const s = achar(mensagens[i].passos);
      if (s) return s;
    }
    return null;
  }

  function resumoCusto(mensagens, passosVivos) {
    let ms = 0, acoes = 0, ent = 0, sai = 0, custo = 0, comUso = 0, respostas = 0, msDurAcoes = 0;
    const contar = (ps) => (ps || []).forEach((p) => {
      if (p && p.tipo === 'ferramenta') { acoes += 1; msDurAcoes += (+p.dur || 0) * 1000; }
    });
    (mensagens || []).forEach((m) => {
      if (m.role === 'ferramenta') acoes += 1;
      if (m.role !== 'assistant') return;
      respostas += 1;
      contar(m.passos);
      if (m.uso) {
        comUso += 1;
        ms += +m.uso.duracao_ms || 0;
        ent += +m.uso.tokens_entrada || 0;
        sai += +m.uso.tokens_saida || 0;
        custo += +m.uso.custo_usd || 0;
      }
    });
    contar(passosVivos);
    return { respostas, acoes, tempo_ms: ms || msDurAcoes, tokens_entrada: ent, tokens_saida: sai,
             custo_usd: custo, com_uso: comUso };
  }

  // texto e anexos de uma mensagem do usuário — inclusive das conversas antigas,
  // em que os anexos só existiam no fim do `content`
  function partesUsuario(m) {
    if (Array.isArray(m.anexos)) return { texto: m.texto != null ? m.texto : String(m.content || '').split('\n\nArquivos anexados:\n')[0], anexos: m.anexos };
    const c = String(m.content || '');
    const k = c.indexOf('\n\nArquivos anexados:\n');
    if (k < 0) return { texto: c, anexos: [] };
    return { texto: c.slice(0, k), anexos: c.slice(k + 21).split('\n').map((l) => l.replace(/^- /, '').trim()).filter(Boolean) };
  }

  // ================================================================ menu "/" e "@"
  const COMANDOS = [
    { id: 'nova', nome: '/nova', desc: 'Começa uma conversa nova' },
    { id: 'limpar', nome: '/limpar', desc: 'Apaga as mensagens desta conversa e a memória da IA' },
    { id: 'skills', nome: '/skills', desc: 'Lista as skills instaladas para escolher uma' },
    { id: 'custo', nome: '/custo', desc: 'Resumo desta conversa: tempo, ações, tokens e custo' },
    { id: 'parar', nome: '/parar', desc: 'Interrompe a resposta em andamento (Esc)' },
  ];

  // Que menu o texto pede, olhando até o cursor.
  function lerGatilho(texto, cursor) {
    texto = String(texto || '');
    if (cursor == null) cursor = texto.length;
    const antes = texto.slice(0, cursor);
    let m = antes.match(/^\/skills?\s+([^\n]*)$/i);
    if (m) return { tipo: 'skills', consulta: m[1], inicio: 0 };
    m = antes.match(/^\/(\S*)$/);
    if (m && !texto.slice(cursor).includes('\n')) return { tipo: 'comando', consulta: m[1], inicio: 0 };
    m = antes.match(/(^|\s)@([^\s@]*)$/);
    if (m) return { tipo: 'arquivo', consulta: m[2], inicio: cursor - m[2].length - 1 };
    return null;
  }

  function filtrarComandos(consulta) {
    const q = semAcento(consulta);
    const comeca = COMANDOS.filter((c) => c.nome.slice(1).startsWith(q));
    const contem = COMANDOS.filter((c) => !comeca.includes(c) && semAcento(c.nome + ' ' + c.desc).includes(q));
    return comeca.concat(contem);
  }

  function filtrarSkills(lista, consulta) {
    const q = semAcento(consulta).trim();
    const xs = (lista || []).filter((s) => !q || semAcento(s.nome + ' ' + (s.descricao || '')).includes(q));
    return xs.sort((a, b) => (semAcento(a.nome).startsWith(q) ? 0 : 1) - (semAcento(b.nome).startsWith(q) ? 0 : 1));
  }

  // troca o "@consulta" pelo caminho escolhido; devolve o texto novo e o cursor
  function aplicarArquivo(texto, gatilho, caminho, cursor) {
    const c = /\s/.test(caminho) ? `"${caminho}"` : caminho;
    const novo = texto.slice(0, gatilho.inicio) + c + ' ' + texto.slice(cursor);
    return { texto: novo, cursor: gatilho.inicio + c.length + 1 };
  }

  // ================================================================ fila
  // Mensagens escritas enquanto a IA trabalha: entram aqui, à vista, e saem
  // uma por vez, na ordem, quando a resposta em curso termina.
  class Fila {
    constructor() { this.itens = []; this.pausada = false; }
    por(texto, anexos) { this.itens.push({ texto: String(texto || ''), anexos: (anexos || []).slice() }); return this.itens.length; }
    tirar() { return this.pausada ? null : (this.itens.shift() || null); }
    remover(i) { this.itens.splice(i, 1); }
    get tamanho() { return this.itens.length; }
  }

  // ================================================================ sessão (sobrevive à remontagem)
  // A tela do app se redesenha inteira em vários momentos (conta, atualização,
  // troca de aba). Uma resposta em andamento e a fila não podem morrer nisso:
  // ficam aqui, por conversa, e a montagem nova se pendura de volta.
  const SESSOES = {};

  function sessao(cid) {
    if (!SESSOES[cid]) SESSOES[cid] = { cid, fila: new Fila(), viva: null, ouvintes: new Set(), cfg: null, provedor: null };
    return SESSOES[cid];
  }
  const avisar = (s, tipo, dados) => s.ouvintes.forEach((f) => { try { f(tipo, dados); } catch (e) { console.error(e); } });

  function cliente(cfg) {
    const raizApi = String(cfg.api || '').replace(/\/+$/, '');
    async function chamar(rota, opcoes = {}) {
      const r = await fetch(raizApi + rota, {
        ...opcoes,
        headers: { 'Content-Type': 'application/json', 'X-Token': cfg.token || '', ...(opcoes.headers || {}) },
      });
      const dados = await r.json().catch(() => ({ erro: 'Resposta inesperada do app.' }));
      if (!r.ok) { const e = new Error(dados.erro || 'Falhou.'); e.status = r.status; e.dados = dados; throw e; }
      return dados;
    }
    return {
      raiz: raizApi,
      get: (rota) => chamar(rota),
      post: (rota, corpo) => chamar(rota, { method: 'POST', body: JSON.stringify(corpo || {}) }),
      enviarArquivo: (rota, arquivo) => chamar(rota, { method: 'POST', body: arquivo,
        headers: { 'Content-Type': 'application/octet-stream', 'X-Nome': encodeURIComponent(arquivo.name || 'anexo') } }),
      arquivoUrl: (caminho) => `${raizApi}/api/arquivo?p=${encodeURIComponent(caminho)}&t=${encodeURIComponent(cfg.token || '')}`,
      quadroUrl: (caminho, w) => `${raizApi}/api/midia/quadro?p=${encodeURIComponent(caminho)}&w=${w || 480}&t=${encodeURIComponent(cfg.token || '')}`,
    };
  }

  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

  async function enviarNaSessao(s, texto, anexos) {
    if (s.viva) { s.fila.por(texto, anexos); avisar(s, 'fila'); return; }
    const api = cliente(s.cfg);
    const viva = { tarefa: null, seq: null, passos: [], estado: 'rodando', etapa: '', cancelavel: false,
                   inicio: Date.now(), marca: Date.now(), texto, anexos: anexos || [], erro: null };
    s.viva = viva;
    avisar(s, 'inicio', viva);
    try {
      const r = await api.post('/api/conversa', { texto, anexos: viva.anexos, conversa: s.cid, provedor: s.provedor });
      viva.tarefa = r.tarefa;
    } catch (e) {
      s.viva = null;
      avisar(s, 'fim', { estado: 'erro', erro: e.message, texto, anexos: viva.anexos });
      return;
    }
    let falhas = 0;
    while (s.viva === viva) {
      const escrevendo = viva.passos.some((p) => p && p.tipo === 'parcial');
      await dormir(escrevendo ? 300 : 650);
      let t;
      try {
        t = await api.get(`/api/tarefas/${viva.tarefa}` + (viva.seq != null ? `?v=${viva.seq}` : '?v=-1'));
        falhas = 0;
      } catch (e) {
        if (++falhas > 25) { t = { estado: 'erro', erro: 'O app parou de responder durante a conversa.' }; }
        else continue;
      }
      if (t.erro === 'sem tarefa') t = { estado: 'erro', erro: 'A conversa foi interrompida (o app reiniciou?).' };
      const antes = viva.passos.length + '|' + viva.etapa;
      if (Array.isArray(t.novos)) {
        t.novos.forEach(([i, p]) => { viva.passos[i] = p; });
        if (t.total != null) viva.passos.length = t.total;
        if (t.seq != null) viva.seq = t.seq;
      } else if (Array.isArray(t.passos)) {
        viva.passos = t.passos;
      }
      if (t.etapa != null) viva.etapa = t.etapa;
      viva.cancelavel = !!t.cancelavel;
      if (antes !== viva.passos.length + '|' + viva.etapa || (t.novos && t.novos.length)) viva.marca = Date.now();
      avisar(s, 'vivo', viva);
      if (t.estado && t.estado !== 'rodando') {
        viva.estado = t.estado;
        s.viva = null;
        avisar(s, 'fim', { estado: t.estado, erro: t.erro, resultado: t.resultado, texto, anexos: viva.anexos, passos: viva.passos });
        if (t.estado === 'pronto') {
          const prox = s.fila.tirar();
          if (prox) { avisar(s, 'fila'); setTimeout(() => enviarNaSessao(s, prox.texto, prox.anexos), 60); }
        } else if (s.fila.tamanho) {
          s.fila.pausada = true;     // erro ou cancelado: a fila espera a pessoa decidir
          avisar(s, 'fila');
        }
      }
    }
  }

  async function cancelarNaSessao(s) {
    const v = s.viva;
    if (!v || !v.tarefa) return { ok: false, msg: 'Nada em andamento.' };
    try { return await cliente(s.cfg).post(`/api/tarefas/${v.tarefa}/cancelar`); }
    catch (e) { return { ok: false, msg: e.message }; }
  }

  // ================================================================ HTML das peças
  const LIMITE_DETALHE = 700;
  const VISIVEIS_INICIO = 40;
  const GRUPO_MAX = 6;
  const VIVO_JANELA = 60;
  const VIVO_AJUDA_MS = 10000;

  function trecho(t, chave, mais) {
    t = String(t ?? '');
    if (!t) return '';
    if (t.length <= LIMITE_DETALHE || mais.has(chave)) {
      return `<pre>${esc(t)}</pre>` + (t.length > LIMITE_DETALHE ? `<button type="button" class="cv-mais" data-mais="${esc(chave)}">ver menos</button>` : '');
    }
    return `<pre>${esc(t.slice(0, LIMITE_DETALHE))}…</pre><button type="button" class="cv-mais" data-mais="${esc(chave)}">ver mais (${numero(t.length)} caracteres)</button>`;
  }

  function entradaLegivel(p) {
    const e = p.entrada;
    if (e && typeof e === 'object' && Object.keys(e).length) {
      if (typeof e.command === 'string' && Object.keys(e).length <= 3) return e.command;
      try { return JSON.stringify(e, null, 2); } catch (_) { return String(e); }
    }
    return p.resumo || '';
  }

  function htmlAcao(p, chave, ui) {
    const est = p.estado || 'rodando';
    const r = rotuloAcao(p);
    const aberto = ui.abertos.has(chave);
    const dur = p.dur != null ? duracao(p.dur) : (est === 'rodando' && p.inicio ? duracao(Date.now() / 1000 - p.inicio) : '');
    const marca = est === 'rodando' ? '<span class="cv-giro" aria-label="rodando"></span>'
      : est === 'ok' ? '<span class="cv-ok" aria-label="concluída">✓</span>'
      : est === 'interrompido' ? '<span class="cv-int" aria-label="interrompida">–</span>'
      : '<span class="cv-erro-x" aria-label="erro">✕</span>';
    let detalhe = '';
    if (aberto) {
      const ent = entradaLegivel(p);
      const res = p.resultado || p.saida || '';
      detalhe = `<div class="cv-acao-det" id="cv-det-${esc(chave)}">
        ${ent ? `<div class="cv-det-rot">Entrada</div>${trecho(ent, chave + ':e', ui.mais)}` : ''}
        ${p.recusado ? `<div class="cv-det-recusa">${ICONE.aviso} Recusado pelo portão: ${esc(p.porque || '')}</div>` : ''}
        ${res ? `<div class="cv-det-rot">Resultado</div>${trecho(res, chave + ':r', ui.mais)}` : (est === 'rodando' ? '<div class="cv-det-vazio">Rodando…</div>' : '')}
      </div>`;
    }
    return `<div class="cv-acao est-${esc(est)}${p.sub ? ' sub' : ''}${p.recusado ? ' recusada' : ''}">
      <button type="button" class="cv-acao-linha" data-abrir="${esc(chave)}" aria-expanded="${aberto}">
        <span class="cv-acao-ic">${ICONE[r.icone] || ICONE.peca}</span>
        <span class="cv-acao-txt"><span class="cv-acao-nome">${esc(r.texto)}</span>${r.alvo ? `<span class="cv-acao-alvo">${esc(r.alvo)}</span>` : ''}</span>
        <span class="cv-acao-dur" data-dur-inicio="${est === 'rodando' && p.inicio ? p.inicio : ''}">${esc(dur)}</span>
        <span class="cv-acao-est">${marca}</span>
      </button>${detalhe}</div>${htmlMidias(p.midias, chave + ':m', ui)}`;
  }

  function htmlPensou(p, chave, ui) {
    const rodando = p.estado === 'rodando';
    const aberto = ui.abertos.has(chave);
    const t = rodando ? (p.inicio ? 'Pensando… ' + duracao(Date.now() / 1000 - p.inicio) : 'Pensando…')
      : (p.dur != null ? 'Pensou por ' + duracao(p.dur) : 'Pensou');
    const tem = (p.texto || '').trim();
    return `<div class="cv-acao cv-pensou${rodando ? ' est-rodando' : ''}">
      <button type="button" class="cv-acao-linha" ${tem ? `data-abrir="${esc(chave)}" aria-expanded="${aberto}"` : 'tabindex="-1" aria-disabled="true"'}>
        <span class="cv-acao-ic">${ICONE.cerebro}</span>
        <span class="cv-acao-txt"><span class="cv-acao-nome cv-it" data-pensa-inicio="${rodando && p.inicio ? p.inicio : ''}">${esc(t)}</span></span>
      </button>${aberto && tem ? `<div class="cv-acao-det cv-pensamento">${trecho(tem, chave + ':t', ui.mais)}</div>` : ''}</div>`;
  }

  function htmlPasso(p, chave, ui) {
    if (!p) return '';
    if (p.tipo === 'texto' || p.tipo === 'parcial') {
      if (!(p.texto || '').trim()) return '';
      return `<div class="cv-texto${p.tipo === 'parcial' ? ' escrevendo' : ''}">${md(p.texto)}</div>${p.tipo === 'texto' ? htmlMidias(p.midias, chave + ':m', ui) : ''}`;
    }
    if (p.tipo === 'pensando') return htmlPensou(p, chave, ui);
    if (p.tipo === 'aviso') return `<div class="cv-aviso-linha">${ICONE.aviso}<span>${esc(p.texto)}</span></div>`;
    if (p.tipo === 'ferramenta') return htmlAcao(p, chave, ui);
    return '';
  }

  const ehAcao = (p) => p && (p.tipo === 'ferramenta' || p.tipo === 'pensando' || p.tipo === 'aviso');

  // A sequência que uma resposta desenha: texto e ações intercalados como
  // aconteceram. Conversa antiga (passos sem texto) = ações e depois a fala.
  function sequenciaDa(m) {
    const ps = (m.passos || []).filter(Boolean);
    if (ps.some((p) => p.tipo === 'texto')) return ps;
    return ps.concat(m.content ? [{ tipo: 'texto', texto: m.content, midias: m.midias }] : []);
  }

  function htmlGrupo(itens, chaveGrupo, ui) {
    // muitas ações seguidas: só as últimas ficam à vista, o resto recolhido
    if (itens.length > GRUPO_MAX && !ui.grupos.has(chaveGrupo)) {
      const ocultas = itens.length - 3;
      const erros = itens.slice(0, ocultas).filter(([p]) => p.estado === 'erro').length;
      return `<div class="cv-grupo"><button type="button" class="cv-grupo-mais" data-grupo="${esc(chaveGrupo)}" aria-expanded="false">
          ▸ mais ${ocultas} ações${erros ? ` · <span class="cv-vermelho">${erros} com erro</span>` : ''}</button>
        ${itens.slice(0, ocultas).map(([p, k]) => htmlMidias(p.midias, k + ':m', ui)).join('')}
        ${itens.slice(ocultas).map(([p, k]) => htmlPasso(p, k, ui)).join('')}</div>`;
    }
    const recolher = itens.length > GRUPO_MAX ? `<button type="button" class="cv-grupo-mais" data-grupo="${esc(chaveGrupo)}" aria-expanded="true">▾ recolher ${itens.length} ações</button>` : '';
    return `<div class="cv-grupo">${recolher}${itens.map(([p, k]) => htmlPasso(p, k, ui)).join('')}</div>`;
  }

  function htmlSequencia(seq, prefixo, ui) {
    seq = dedupeMidias(seq, ui);
    const out = [];
    let grupo = [], g = 0;
    const fechar = () => { if (grupo.length) { out.push(htmlGrupo(grupo, `${prefixo}g${g++}`, ui)); grupo = []; } };
    seq.forEach((p, i) => {
      if (ehAcao(p)) grupo.push([p, `${prefixo}${i}`]);
      else { fechar(); out.push(htmlPasso(p, `${prefixo}${i}`, ui)); }
    });
    fechar();
    return out.join('');
  }

  function htmlAnexos(lista, api) {
    if (!lista || !lista.length) return '';
    return `<div class="cv-anexos-msg">${lista.map((c) => IMAGEM.test(c)
      ? `<a class="cv-mini" title="${esc(c)}"><img src="${esc(api.arquivoUrl(c))}" alt="${esc(base(c))}" data-caminho="${esc(c)}" loading="lazy"></a>`
      : `<span class="cv-chip" title="${esc(c)}">${ICONE.clipe}<span>${esc(base(c))}</span></span>`).join('')}</div>`;
  }

  function htmlMensagem(m, i, ui, api) {
    if (ui && api && !ui.api) ui.api = api;
    if (m.role === 'user') {
      const u = partesUsuario(m);
      return `<div class="cv-msg cv-eu" data-msg="${i}">${u.texto ? `<div class="cv-bolha">${esc(u.texto)}</div>` : ''}${htmlAnexos(u.anexos, api)}</div>`;
    }
    if (m.role === 'ferramenta') {
      const s = m.saida || {};
      const p = { tipo: 'ferramenta', nome: m.nome, entrada: m.entrada, estado: (s && (s.erro || s.recusado)) ? 'erro' : 'ok',
                  resultado: (() => { try { return JSON.stringify(s, null, 2); } catch (_) { return String(s); } })(),
                  recusado: !!(s && s.recusado), porque: s && s.porque };
      p.midias = m.midias;
      return `<div class="cv-msg cv-ia" data-msg="${i}"><div class="cv-grupo">${htmlAcao(p, `m${i}:0`, ui)}</div></div>`;
    }
    if (m.role === 'assistant') {
      const quem = m.provedor === 'chatgpt' ? 'ChatGPT' : m.provedor === 'claude' ? 'Claude' : '';
      return `<div class="cv-msg cv-ia" data-msg="${i}">${quem ? `<div class="cv-quem">${esc(quem)}</div>` : ''}${htmlSequencia(sequenciaDa(m), `m${i}:`, ui)}</div>`;
    }
    return '';
  }

  // ================================================================ entregas de mídia
  // Prévia do que a IA entregou: imagens em grade (clique abre o lightbox),
  // vídeo com player e capa, áudio com a forma da onda. O SERVIDOR acha as
  // mídias (nucleo/midia.py) e manda em `passo.midias`; aqui só se desenha.
  // Entrega remota (link do Higgsfield/HeyGen) é baixada para a PASTA DO
  // PROJETO antes de aparecer — o link expira. Nada aqui gasta crédito.
  const LIMITE_MIDIAS = 12;
  const LIMITE_MIDIAS_COMPACTO = 6;
  const NO_WINDOWS = (() => {
    try { const n = raizGlobal.navigator; return !!n && /win/i.test((n.userAgentData && n.userAgentData.platform) || n.platform || ''); }
    catch (_) { return false; }
  })();
  const TIPO_EXT = (c) => {
    const e = String(c || '').split('?')[0].split('.').pop().toLowerCase();
    if (/^(png|jpe?g|webp|gif)$/.test(e)) return 'imagem';
    if (/^(mp4|mov|webm|m4v)$/.test(e)) return 'video';
    if (/^(mp3|wav|m4a|aac|ogg)$/.test(e)) return 'audio';
    return null;
  };

  function uiMidia(ui) {
    ui = ui || {};
    if (!ui.baixas) ui.baixas = new Map();       // url -> {estado, caminho, tipo, erro}
    if (!ui.infos) ui.infos = new Map();         // caminho -> {largura, altura, duracao}
    if (!ui.lb) ui.lb = new Map();               // chave do bloco -> [caminhos das imagens]
    if (!ui.midiasTodas) ui.midiasTodas = new Set();
    return ui;
  }

  // a entrega remota que já desceu vira o arquivo local
  function resolverMidia(m, ui) {
    if (!m || typeof m !== 'object') return null;
    if (m.url) {
      const b = ui.baixas.get(m.url);
      if (b && b.estado === 'ok' && b.caminho) return { tipo: b.tipo || TIPO_EXT(b.caminho), caminho: b.caminho, nome: base(b.caminho), de: m.url };
      return m;
    }
    if (!m.caminho) return null;
    return { tipo: m.tipo || TIPO_EXT(m.caminho), caminho: m.caminho, nome: m.nome || base(m.caminho) };
  }

  const chaveMidia = (m) => (m.caminho ? 'f:' + m.caminho : 'u:' + String(m.url || '').split('?')[0]);

  // a mesma mídia não aparece duas vezes na mesma resposta: fica na PRIMEIRA
  // ação que a entregou
  function dedupeMidias(seq, ui) {
    ui = uiMidia(ui);
    const vistos = new Set();
    return (seq || []).map((p) => {
      if (!p || !Array.isArray(p.midias) || !p.midias.length) return p;
      const novas = p.midias.filter((m) => {
        const r = resolverMidia(m, ui);
        if (!r) return false;
        const k = chaveMidia(r);
        if (vistos.has(k)) return false;
        vistos.add(k); return true;
      });
      return Object.assign({}, p, { midias: novas });
    });
  }

  function proporcao(w, h) {
    if (!w || !h) return '';
    const r = w / h;
    const xs = [['9:16', 9 / 16], ['16:9', 16 / 9], ['1:1', 1], ['4:5', 4 / 5], ['3:4', 3 / 4], ['4:3', 4 / 3], ['2:3', 2 / 3], ['21:9', 21 / 9]];
    for (const [n, v] of xs) if (Math.abs(r - v) / v < 0.03) return n;
    return `${w}×${h}`;
  }

  function relogioMidia(seg) {
    if (seg == null || !isFinite(seg)) return '–:––';
    seg = Math.max(0, Math.round(seg));
    return `${Math.floor(seg / 60)}:${String(seg % 60).padStart(2, '0')}`;
  }

  function htmlAcoesMidia(c, soIcone) {
    const pasta = NO_WINDOWS ? 'Mostrar na pasta' : 'Mostrar no Finder';
    const b = (acao, rot, ic) => `<button type="button" class="cv-mid-bt" data-mid-acao="${acao}" data-alvo="${esc(c)}" title="${esc(rot)}" aria-label="${esc(rot + ': ' + base(c))}">${ICONE[ic]}${soIcone ? '' : `<span>${esc(rot)}</span>`}</button>`;
    return `<div class="cv-mid-acoes">${b('mostrar', pasta, 'pasta')}${b('timeline', 'Colocar na timeline', 'timeline')}${b('copiar', 'Copiar caminho', 'copiar')}</div>`;
  }

  function htmlRemota(m, ui) {
    const b = ui.baixas.get(m.url) || { estado: 'baixando' };
    let host = '';
    try { host = new URL(m.url).host; } catch (_) { host = ''; }
    const tipo = m.tipo === 'video' ? 'o vídeo' : m.tipo === 'audio' ? 'o áudio' : m.tipo === 'imagem' ? 'a imagem' : 'a entrega';
    let corpo;
    if (b.estado === 'destino') {
      const ps = ui.destinoProjetos || [];
      corpo = `<div class="cv-mid-rem-topo">${ICONE.pasta}<b>Em qual projeto salvar?</b></div>
        <p>Antes de mostrar, o app baixa ${tipo} para a pasta do projeto — o link expira, e mídia fora da pasta do projeto fica offline no Premiere.</p>
        <div class="cv-mid-destinos">${ps.map((p) => `<button type="button" class="cv-bt mini" data-destino-projeto="${esc(p.id)}">${esc(p.nome)}</button>`).join('')}
          <button type="button" class="cv-bt mini" data-destino-escolher>Escolher pasta…</button></div>`;
    } else if (b.estado === 'erro') {
      corpo = `<div class="cv-mid-rem-topo">${ICONE.aviso}<b>Não consegui baixar ${tipo}</b></div><p>${esc(b.erro || '')}</p>
        <div class="cv-mid-destinos"><button type="button" class="cv-bt mini" data-mid-tentar="${esc(m.url)}">Tentar de novo</button></div>`;
    } else {
      corpo = `<div class="cv-mid-rem-topo"><span class="cv-giro"></span><b>baixando…</b><span class="cv-mid-host">${esc(host)}</span></div>
        <p>Salvando ${tipo} na pasta do projeto antes de mostrar.</p>`;
    }
    return `<div class="cv-mid-remota est-${esc(b.estado)}" data-mid-url="${esc(m.url)}" data-tipo="${esc(m.tipo || '')}" role="status">${corpo}</div>`;
  }

  function htmlMidias(lista, chave, ui) {
    if (!Array.isArray(lista) || !lista.length) return '';
    ui = uiMidia(ui);
    const api = ui.api;
    if (!api) return '';
    const res = lista.map((m) => resolverMidia(m, ui)).filter(Boolean);
    if (!res.length) return '';
    const imagensTodas = res.filter((m) => m.caminho && m.tipo === 'imagem').map((m) => m.caminho);
    ui.lb.set(chave, imagensTodas);
    const lim = ui.compacto ? LIMITE_MIDIAS_COMPACTO : LIMITE_MIDIAS;
    const todas = ui.midiasTodas.has(chave);
    const vis = todas ? res : res.slice(0, lim);
    const imgs = vis.filter((m) => m.caminho && m.tipo === 'imagem');
    const vids = vis.filter((m) => m.caminho && m.tipo === 'video');
    const auds = vis.filter((m) => m.caminho && m.tipo === 'audio');
    const rems = vis.filter((m) => m.url);
    const out = [];
    if (imgs.length) {
      out.push(`<div class="cv-mid-grade${imgs.length === 1 ? ' cv-mid-uma' : ''}">${imgs.map((m) => {
        const k = imagensTodas.indexOf(m.caminho);
        return `<figure class="cv-mid-img">
          <button type="button" class="cv-mid-abrir" data-lb="${esc(chave)}" data-lb-i="${k}" aria-label="${esc('Abrir ' + m.nome + ' em tamanho grande')}">
            <img src="${esc(api.quadroUrl(m.caminho, 480))}" alt="${esc(m.nome)}" loading="lazy" decoding="async" data-mid-img data-original="${esc(api.arquivoUrl(m.caminho))}"></button>
          <figcaption class="cv-mid-legenda"><span class="cv-mid-nome" title="${esc(m.caminho)}">${esc(m.nome)}</span>${htmlAcoesMidia(m.caminho, true)}</figcaption></figure>`;
      }).join('')}</div>`);
    }
    if (vids.length) {
      out.push(`<div class="cv-mid-videos${vids.length > 1 ? ' cv-mid-faixa' : ''}">${vids.map((m) => {
        const inf = ui.infos.get(m.caminho);
        const ar = inf && inf.largura && inf.altura ? ` style="aspect-ratio: ${inf.largura} / ${inf.altura}"` : '';
        const meta = inf ? [inf.duracao != null ? relogioMidia(inf.duracao) : '', proporcao(inf.largura, inf.altura)].filter(Boolean).join(' · ') : '';
        return `<figure class="cv-mid-video" data-mid="${esc(m.caminho)}">
          <div class="cv-mid-tela"${ar}><video controls preload="metadata" playsinline poster="${esc(api.quadroUrl(m.caminho, 640))}" data-src="${esc(api.arquivoUrl(m.caminho))}" aria-label="${esc('Vídeo ' + m.nome)}"></video></div>
          <figcaption class="cv-mid-legenda"><span class="cv-mid-nome" title="${esc(m.caminho)}">${esc(m.nome)}</span><span class="cv-mid-meta">${esc(meta)}</span></figcaption>
          ${htmlAcoesMidia(m.caminho, !!ui.compacto || vids.length > 1)}</figure>`;
      }).join('')}</div>`);
    }
    if (auds.length) {
      out.push(`<div class="cv-mid-audios">${auds.map((m) => {
        const inf = ui.infos.get(m.caminho);
        return `<figure class="cv-mid-audio" data-mid="${esc(m.caminho)}">
          <div class="cv-mid-player">
            <button type="button" class="cv-mid-play" data-audio-play aria-label="${esc('Tocar ' + m.nome)}">${ICONE.tocar}</button>
            <div class="cv-mid-onda-box" data-audio-onda title="Clique para pular"><canvas class="cv-mid-onda" aria-hidden="true"></canvas></div>
            <span class="cv-mid-tempo">0:00 / ${esc(relogioMidia(inf && inf.duracao))}</span>
            <audio preload="none" data-src="${esc(api.arquivoUrl(m.caminho))}"></audio>
          </div>
          <figcaption class="cv-mid-legenda"><span class="cv-mid-nome" title="${esc(m.caminho)}">${esc(m.nome)}</span></figcaption>
          ${htmlAcoesMidia(m.caminho, !!ui.compacto)}</figure>`;
      }).join('')}</div>`);
    }
    rems.forEach((m) => out.push(htmlRemota(m, ui)));
    if (res.length > lim) {
      out.push(`<button type="button" class="cv-mid-mais" data-mid-todas="${esc(chave)}" aria-expanded="${todas}">${todas ? 'ver menos' : `ver todas (${res.length})`}</button>`);
    }
    return `<div class="cv-midias" data-midias="${esc(chave)}">${out.join('')}</div>`;
  }

  function mensagemTimeline(c) {
    return `Importe este arquivo no projeto aberto do Premiere e coloque na timeline ativa, na posição do playhead, pelo Tools PRO:\n"${c}"\nSe ele não estiver dentro da pasta do projeto, copie para lá antes de importar.`;
  }

  // ================================================================ o componente
  function montarConversa(el, op) {
    op = op || {};
    const cfg = { api: op.api || '', token: op.token || '' };
    const api = cliente(cfg);
    const ui = uiMidia({ abertos: new Set(), mais: new Set(), grupos: new Set(), vivoTudo: false });
    ui.api = api;
    ui.compacto = !!op.compacto;
    const st = {
      cid: op.conversa || null, mensagens: [], meta: {}, ia: null, skills: null,
      visiveis: VISIVEIS_INICIO, notas: [], anexos: [], menu: null, enviados: [], volta: -1,
      cartao: null, cartaoErro: '', montado: true, carregou: false,
      tarefasAbertas: null,      // null = automático: aberto só enquanto a IA trabalha
      falha: null, desligar: null, relogio: null, buscaArq: 0,
    };
    let S = null;          // a sessão (fila + resposta viva) desta conversa

    el.classList.add('cv');
    el.classList.toggle('compacto', !!op.compacto);
    el.innerHTML = `
      <div class="cv-barra">
        <input class="cv-titulo" type="text" maxlength="120" aria-label="Título da conversa (clique para renomear)" value="Nova conversa">
        <button type="button" class="cv-bt mini cv-bt-hist" data-historico aria-expanded="false" title="Conversas anteriores">${ICONE.lista}<span>Histórico</span></button>
        <button type="button" class="cv-bt mini cv-bt-nova" data-nova title="Começar uma conversa do zero">+ Nova</button>
      </div>
      <div class="cv-hist" role="dialog" aria-label="Histórico de conversas" hidden></div>
      <div class="cv-tarefas" hidden></div>
      <div class="cv-lista" role="log" aria-live="off" aria-label="Conversa" tabindex="0"><div class="cv-msgs"></div><div class="cv-vivo" hidden></div><div class="cv-notas"></div></div>
      <div class="cv-anuncio" aria-live="polite" aria-atomic="true"></div>
      <div class="cv-aprovacao" hidden></div>
      <div class="cv-fila" hidden></div>
      <div class="cv-compositor">
        <div class="cv-menu" role="listbox" id="cv-menu-${Math.random().toString(36).slice(2, 8)}" hidden></div>
        <div class="cv-anexos"></div>
        <div class="cv-campo">
          <button type="button" class="cv-bt-ic cv-anexar" title="Anexar arquivo ou imagem" aria-label="Anexar arquivo">${ICONE.clipe}</button>
          <textarea class="cv-entrada" rows="1" aria-label="Mensagem" aria-autocomplete="list" aria-expanded="false"
            placeholder="Fale o que quer fazer…  /  comandos  ·  @  arquivos"></textarea>
          <button type="button" class="cv-bt-ic cv-parar" title="Parar (Esc)" aria-label="Parar a resposta" hidden>${ICONE.parar}</button>
          <button type="button" class="cv-bt-ic cv-enviar principal" title="Enviar (Enter)" aria-label="Enviar">${ICONE.enviar}</button>
        </div>
        <input type="file" class="cv-arquivo" multiple hidden>
        <div class="cv-rodape"></div>
        ${(op.atalhos || []).length ? `<div class="cv-atalhos">${op.atalhos.map((a) => `<button type="button" class="cv-atalho" data-diz="${esc(a)}">${esc(a)}</button>`).join('')}</div>` : ''}
      </div>
      <div class="cv-soltar" hidden><div>${ICONE.clipe}<b>Solte para anexar</b><span>arquivos e imagens vão junto da mensagem</span></div></div>
      <div class="cv-lb" role="dialog" aria-modal="true" aria-label="Imagem em tamanho grande" hidden>
        <div class="cv-lb-topo"><span class="cv-lb-conta" aria-live="polite"></span><span class="cv-lb-nome"></span>
          <button type="button" class="cv-lb-x" data-lb-fechar aria-label="Fechar (Esc)" title="Fechar (Esc)">✕</button></div>
        <div class="cv-lb-palco" data-lb-fundo>
          <button type="button" class="cv-lb-seta cv-lb-ant" data-lb-ir="-1" aria-label="Imagem anterior (←)" title="Anterior (←)">‹</button>
          <img class="cv-lb-img" alt="">
          <button type="button" class="cv-lb-seta cv-lb-prox" data-lb-ir="1" aria-label="Próxima imagem (→)" title="Próxima (→)">›</button>
        </div>
        <div class="cv-lb-acoes"></div>
      </div>`;

    const $ = (s) => el.querySelector(s);
    const lista = $('.cv-lista'), msgsEl = $('.cv-msgs'), vivoEl = $('.cv-vivo'), notasEl = $('.cv-notas');
    const entrada = $('.cv-entrada'), menuEl = $('.cv-menu');
    entrada.setAttribute('aria-controls', menuEl.id);
    if (op.compacto) entrada.placeholder = 'Mensagem…  / comandos · @ arquivos';

    const pertoDoFim = () => lista.scrollHeight - lista.scrollTop - lista.clientHeight < 90;
    const rolarFim = (forcar) => { if (forcar || st.colado) lista.scrollTop = lista.scrollHeight; };
    st.colado = true;
    lista.addEventListener('scroll', () => { st.colado = pertoDoFim(); }, { passive: true });

    // ---------------------------------------------------------- barra do topo + histórico
    // Título editável, "+ Nova" e "Histórico" DENTRO do componente: no painel
    // do Premiere não existe outra tela para trocar de conversa, e abrir sempre
    // na última prendia a pessoa num assunto velho.
    const JANELA = op.janela || (op.compacto ? 'painel' : 'app');
    const CHAVE_ULTIMA = 'editor-automatico:conversa:' + JANELA;
    const lembrar = (cid) => { try { if (cid) localStorage.setItem(CHAVE_ULTIMA, cid); else localStorage.removeItem(CHAVE_ULTIMA); } catch (_) { /* sem armazenamento */ } };
    const lembrada = () => { try { return localStorage.getItem(CHAVE_ULTIMA); } catch (_) { return null; } };
    const tituloEl = el.querySelector('.cv-titulo');
    const histEl = el.querySelector('.cv-hist');
    st.hist = { aberto: false, q: '', itens: null, carregando: false, confirma: null, erro: '', busca: 0 };

    function pintarBarra() {
      const t = (st.meta && st.meta.titulo) || 'Nova conversa';
      if (document.activeElement !== tituloEl) tituloEl.value = t === st.cid ? 'Nova conversa' : t;
      tituloEl.title = 'Clique para renomear a conversa';
      const b = el.querySelector('[data-historico]');
      b.setAttribute('aria-expanded', String(st.hist.aberto));
      b.classList.toggle('ativo', st.hist.aberto);
      if (st.cid) lembrar(st.cid);
    }

    async function renomear() {
      const novo = tituloEl.value.trim();
      const antes = (st.meta && st.meta.titulo) || 'Nova conversa';
      if (!novo) { tituloEl.value = antes; return; }
      if (novo === antes) return;
      try {
        await garantirConversa();
        const r = await api.post(`/api/conversas/${encodeURIComponent(st.cid)}/renomear`, { titulo: novo });
        st.meta = Object.assign({}, st.meta, r.meta || { titulo: novo });
        $('.cv-anuncio').textContent = 'Conversa renomeada.';
        op.aoTerminar && op.aoTerminar({ conversa: st.cid, meta: st.meta });
      } catch (e) { tituloEl.value = antes; nota('Não consegui renomear: ' + e.message, true); }
      pintarBarra();
    }
    tituloEl.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') { ev.preventDefault(); tituloEl.blur(); }
      else if (ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); tituloEl.value = (st.meta && st.meta.titulo) || 'Nova conversa'; tituloEl.blur(); }
    });
    tituloEl.addEventListener('blur', () => { renomear(); });

    function abrirHist() {
      st.hist.aberto = true; st.hist.confirma = null;
      pintarBarra(); pintarHist(); buscarHist();
      const b = histEl.querySelector('.cv-hist-busca'); b && b.focus();
    }
    function fecharHist(focoNoBotao) {
      if (!st.hist.aberto) return;
      st.hist.aberto = false; st.hist.confirma = null;
      pintarBarra(); pintarHist();
      if (focoNoBotao) { const b = el.querySelector('[data-historico]'); b && b.focus(); }
    }
    async function buscarHist() {
      const minha = ++st.hist.busca;
      st.hist.carregando = true; st.hist.erro = ''; pintarHistLista();
      try {
        const q = st.hist.q.trim();
        const r = await api.get('/api/conversas' + (q ? '?q=' + encodeURIComponent(q) : ''));
        if (minha !== st.hist.busca) return;
        st.hist.itens = r.conversas || [];
      } catch (e) { if (minha === st.hist.busca) st.hist.erro = e.message; }
      if (minha !== st.hist.busca) return;
      st.hist.carregando = false;
      if (st.montado) pintarHistLista();
    }
    function pintarHist() {
      if (!st.hist.aberto) { histEl.hidden = true; histEl.innerHTML = ''; return; }
      histEl.hidden = false;
      histEl.innerHTML = `<div class="cv-hist-topo"><b>Histórico</b>
          <button type="button" class="cv-bt mini principal" data-nova>+ Nova conversa</button>
          <button type="button" class="cv-x cv-hist-x" data-hist-fechar aria-label="Fechar o histórico (Esc)" title="Fechar (Esc)">✕</button></div>
        <input class="cv-hist-busca" type="search" placeholder="Buscar pelo título ou pelo que foi conversado…" aria-label="Buscar conversas" value="${esc(st.hist.q)}">
        <ul class="cv-hist-lista" role="list"></ul>`;
      pintarHistLista();
    }
    function pintarHistLista() {
      const ul = histEl.querySelector('.cv-hist-lista');
      if (!ul) return;
      const h = st.hist;
      if (h.erro) { ul.innerHTML = `<li class="cv-hist-vazio">${esc('Não consegui listar: ' + h.erro)}</li>`; return; }
      if (!h.itens) { ul.innerHTML = '<li class="cv-hist-vazio">carregando…</li>'; return; }
      if (!h.itens.length) { ul.innerHTML = `<li class="cv-hist-vazio">${h.q.trim() ? 'Nenhuma conversa com isso.' : 'Nenhuma conversa ainda.'}</li>`; return; }
      ul.innerHTML = h.itens.map((c) => {
        const atual = c.id === st.cid;
        if (h.confirma === c.id) {
          return `<li class="cv-hist-item confirma" role="alertdialog" aria-label="Confirmar exclusão">
            <span>Apagar <b>${esc(c.titulo)}</b>? As mensagens somem; o projeto e os arquivos ficam.</span>
            <span class="cv-hist-conf"><button type="button" class="cv-bt mini" data-hist-confirma="nao">Cancelar</button>
            <button type="button" class="cv-bt mini perigo" data-hist-confirma="${esc(c.id)}">Apagar</button></span></li>`;
        }
        const meta = [quandoRelativo(c.quando), c.projeto_nome || (c.projeto ? c.projeto : ''),
          `${c.mensagens} ${c.mensagens === 1 ? 'mensagem' : 'mensagens'}`].filter(Boolean).join(' · ');
        return `<li class="cv-hist-item${atual ? ' atual' : ''}">
          <button type="button" class="cv-hist-abrir" data-hist-abrir="${esc(c.id)}" ${atual ? 'aria-current="true"' : ''}>
            <span class="cv-hist-titulo">${esc(c.titulo)}${atual ? ' <em>aberta</em>' : ''}</span>
            <span class="cv-hist-meta">${esc(meta)}</span>
            ${c.trecho ? `<span class="cv-hist-trecho">${esc(c.trecho)}</span>` : ''}</button>
          <button type="button" class="cv-x cv-hist-apagar" data-hist-apagar="${esc(c.id)}" aria-label="${esc('Apagar a conversa ' + c.titulo)}" title="Apagar">✕</button></li>`;
      }).join('');
    }
    histEl.addEventListener('input', (ev) => {
      if (!ev.target.classList.contains('cv-hist-busca')) return;
      st.hist.q = ev.target.value;
      clearTimeout(st.hist.t); st.hist.t = setTimeout(buscarHist, 220);
    });
    histEl.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); if (st.hist.confirma) { st.hist.confirma = null; pintarHistLista(); } else fecharHist(true); }
    });

    function zerarTela() {
      st.notas = []; st.falha = null; st.cartao = null; st.cartaoErro = '';
      ui.abertos.clear(); ui.mais.clear(); ui.grupos.clear(); st.visiveis = VISIVEIS_INICIO;
    }
    async function abrirConversa(cid) {
      if (cid === st.cid) { fecharHist(); return; }
      if (S && S.viva) { nota('Espere a resposta atual acabar (ou aperte Esc) antes de trocar de conversa.'); return; }
      try {
        const r = await api.get('/api/conversas/' + encodeURIComponent(cid));
        zerarTela();
        st.cid = cid; st.mensagens = r.mensagens || []; st.meta = r.meta || {};
        st.enviados = st.mensagens.filter((m) => m.role === 'user').map((m) => partesUsuario(m).texto).filter(Boolean);
        ligarSessao(cid);
        fecharHist();
        pintarTudo(); rolarFim(true); buscarCartao();
        op.aoTrocarConversa && op.aoTrocarConversa(cid);
        entrada.focus();
      } catch (e) { nota('Não consegui abrir a conversa: ' + e.message, true); }
    }
    async function apagarConversa(cid) {
      if (cid === st.cid && S && S.viva) { nota('Esta conversa está respondendo agora — pare a resposta antes de apagar.', true); return; }
      try {
        await api.post('/api/conversas/apagar', { conversa: cid });
        st.hist.confirma = null;
        st.hist.itens = (st.hist.itens || []).filter((c) => c.id !== cid);
        if (cid === st.cid) {
          zerarTela();
          st.cid = null; st.mensagens = []; st.meta = {};
          lembrar(null);
          ligarSessao(null);
          pintarTudo();
          op.aoTrocarConversa && op.aoTrocarConversa(null);
        }
        pintarHistLista();
        $('.cv-anuncio').textContent = 'Conversa apagada.';
      } catch (e) { st.hist.confirma = null; st.hist.erro = e.message; pintarHistLista(); }
    }

    // ---------------------------------------------------------- entregas de mídia
    // Vídeo só ganha `src` quando aparece na tela (IntersectionObserver); áudio
    // só quando a pessoa aperta play. Dados (dimensão, duração, onda) vêm do
    // servidor uma vez por arquivo e ficam em memória.
    const infosP = new Map(), picosP = new Map();
    const filaBaixar = [];
    let baixandoN = 0;
    const visivel = typeof IntersectionObserver !== 'undefined'
      ? new IntersectionObserver((ents) => ents.forEach((e) => { if (e.isIntersecting) { visivel.unobserve(e.target); ativarMidia(e.target); } }),
        { root: lista, rootMargin: '240px 0px' })
      : null;

    function hidratar(raiz) {
      if (!raiz || !raiz.querySelectorAll) return;
      raiz.querySelectorAll('[data-mid]:not([data-hid])').forEach((fig) => {
        fig.dataset.hid = '1';
        if (visivel) visivel.observe(fig); else ativarMidia(fig);
      });
      raiz.querySelectorAll('[data-mid-url]').forEach((card) => {
        const u = card.dataset.midUrl;
        if (!ui.baixas.has(u)) baixarEntrega(u, card.dataset.tipo || null);
      });
    }

    function ativarMidia(fig) {
      const c = fig.dataset.mid;
      const v = fig.querySelector('video[data-src]');
      if (v && !v.getAttribute('src')) v.setAttribute('src', v.dataset.src);
      carregarInfo(c).then((inf) => { if (inf) aplicarInfo(fig, inf); });
      if (fig.querySelector('[data-audio-onda]')) carregarPicos(c).then((pk) => { if (pk) { fig._picos = pk; desenharOnda(fig); } });
    }

    function carregarInfo(c) {
      if (!infosP.has(c)) {
        infosP.set(c, api.get('/api/midia/info?p=' + encodeURIComponent(c))
          .then((d) => { ui.infos.set(c, d); return d; }).catch(() => null));
      }
      return infosP.get(c);
    }

    function carregarPicos(c) {
      if (!picosP.has(c)) {
        picosP.set(c, api.get(`/api/midia/picos?p=${encodeURIComponent(c)}&n=${op.compacto ? 64 : 110}`).catch(() => null));
      }
      return picosP.get(c);
    }

    function aplicarInfo(fig, inf) {
      const tela = fig.querySelector('.cv-mid-tela');
      if (tela && inf.largura && inf.altura) tela.style.aspectRatio = `${inf.largura} / ${inf.altura}`;
      const meta = fig.querySelector('.cv-mid-meta');
      if (meta) meta.textContent = [inf.duracao != null ? relogioMidia(inf.duracao) : '', proporcao(inf.largura, inf.altura)].filter(Boolean).join(' · ');
      const tempo = fig.querySelector('.cv-mid-tempo');
      const a = fig.querySelector('audio');
      if (tempo && a) tempo.textContent = `${relogioMidia(a.currentTime || 0)} / ${relogioMidia(inf.duracao)}`;
    }

    function desenharOnda(fig) {
      const cv = fig.querySelector('canvas.cv-mid-onda');
      const pk = fig._picos;
      if (!cv || !pk || !Array.isArray(pk.picos) || !cv.getContext) return;
      const ctx = cv.getContext('2d');
      if (!ctx) return;
      const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
      const w = Math.max(60, cv.clientWidth || 240), h = Math.max(20, cv.clientHeight || 36);
      if (cv.width !== Math.round(w * dpr)) cv.width = Math.round(w * dpr);
      if (cv.height !== Math.round(h * dpr)) cv.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const a = fig.querySelector('audio');
      const dur = (a && isFinite(a.duration) && a.duration) || pk.duracao || 0;
      const prog = dur && a ? Math.min(1, (a.currentTime || 0) / dur) : 0;
      const n = pk.picos.length, passo = w / n, larg = Math.max(1, passo * 0.62);
      const css = getComputedStyle(fig);
      const ouro = (css.getPropertyValue('--cv-ouro') || '').trim() || '#f2b33d';
      const apagado = 'rgba(255,255,255,.28)';
      for (let i = 0; i < n; i++) {
        const v = Math.max(0.06, +pk.picos[i] || 0);
        const bh = v * (h - 4);
        ctx.fillStyle = (i + 0.5) / n <= prog ? ouro : apagado;
        ctx.fillRect(i * passo + (passo - larg) / 2, (h - bh) / 2, larg, bh);
      }
    }

    function tocarAudio(fig, pular) {
      const a = fig.querySelector('audio');
      if (!a) return;
      if (!a.getAttribute('src')) a.setAttribute('src', a.dataset.src);
      if (pular != null) {
        const dur = (isFinite(a.duration) && a.duration) || (fig._picos && fig._picos.duracao) || 0;
        if (dur) { try { a.currentTime = pular * dur; } catch (_) { /* ainda sem metadados */ } }
        desenharOnda(fig);
        if (!a.paused) return;
      }
      if (a.paused) { try { const pr = a.play(); if (pr && pr.catch) pr.catch(() => {}); } catch (_) { /* sem player (teste) */ } }
      else { try { a.pause(); } catch (_) { /* idem */ } }
    }

    // ---- download das entregas remotas: no máximo 2 ao mesmo tempo
    function baixarEntrega(url, tipo) {
      ui.baixas.set(url, { estado: 'baixando', tipo });
      filaBaixar.push({ url, tipo });
      puxarFila();
    }

    function puxarFila() {
      while (baixandoN < 2 && filaBaixar.length) {
        const { url, tipo } = filaBaixar.shift();
        baixandoN += 1;
        (async () => {
          try {
            const r = await api.post('/api/midia/baixar', { conversa: st.cid, url, tipo });
            ui.baixas.set(url, { estado: 'ok', caminho: r.caminho, tipo: r.tipo || tipo });
            if (r.destino) st.meta.destino = r.destino;
          } catch (e) {
            if (e.status === 409 && e.dados && e.dados.precisa_destino) {
              ui.destinoProjetos = e.dados.projetos || [];
              ui.baixas.set(url, { estado: 'destino', tipo });
            } else ui.baixas.set(url, { estado: 'erro', erro: e.message, tipo });
          }
          baixandoN -= 1;
          if (st.montado) repintarDonos(url);
          puxarFila();
        })();
      }
    }

    // redesenha as mensagens (ou passos ao vivo) que mostram esta entrega
    function repintarDonos(url) {
      const sel = '[data-mid-url]';
      const msgs = new Set();
      let vivo = false;
      el.querySelectorAll(sel).forEach((card) => {
        if (url && card.dataset.midUrl !== url) return;
        const m = card.closest('[data-msg]');
        if (m) msgs.add(+m.dataset.msg);
        else if (vivoEl.contains(card)) vivo = true;
      });
      msgs.forEach((i) => {
        const velho = msgsEl.querySelector(`[data-msg="${i}"]`);
        if (!velho || !st.mensagens[i]) return;
        const t = document.createElement('div'); t.innerHTML = htmlMensagem(st.mensagens[i], i, ui, api);
        const novo = t.firstElementChild; velho.replaceWith(novo); hidratar(novo);
      });
      if (vivo) { vivoNos.forEach((n) => { n.dataset.ass = ''; }); pintarVivo(); }
    }

    async function escolherDestino(corpo, botao) {
      if (!st.cid) return;
      if (botao) botao.disabled = true;
      if (corpo.escolher) nota('Escolha a pasta do projeto na janela que abriu.');
      try {
        const r = await api.post(`/api/conversas/${encodeURIComponent(st.cid)}/destino`, corpo);
        if (!r.ok) { nota(r.cancelado ? 'Nenhuma pasta escolhida — as entregas continuam esperando.' : (r.erro || 'Não deu.'), !r.cancelado); return; }
        st.meta.destino = r.destino;
        nota(`As entregas desta conversa vão para ${r.destino ? r.destino.nome : 'o projeto'}.`);
        [...ui.baixas.entries()].forEach(([u, b]) => { if (b.estado === 'destino') ui.baixas.delete(u); });
        await recarregar();
        hidratar(vivoEl);
      } catch (e) { nota(e.message, true); }
      finally { if (botao && botao.isConnected) botao.disabled = false; }
    }

    // ---- lightbox
    const lbEl = el.querySelector('.cv-lb');
    const lb = { lista: [], i: 0, volta: null };
    const lbAberto = () => !lbEl.hidden;
    function abrirLb(chave, i, origem) {
      lb.lista = ui.lb.get(chave) || [];
      if (!lb.lista.length) return;
      lb.i = Math.max(0, Math.min(lb.lista.length - 1, +i || 0));
      lb.volta = origem || null;
      lbEl.hidden = false;
      el.classList.add('cv-com-lb');
      pintarLb();
      document.addEventListener('keydown', teclaLb);
      const x = lbEl.querySelector('[data-lb-fechar]'); x && x.focus({ preventScroll: true });
    }
    function pintarLb() {
      const c = lb.lista[lb.i];
      const img = lbEl.querySelector('.cv-lb-img');
      img.src = api.arquivoUrl(c);
      img.alt = base(c);
      lbEl.querySelector('.cv-lb-conta').textContent = `${lb.i + 1} de ${lb.lista.length}`;
      lbEl.querySelector('.cv-lb-nome').textContent = base(c);
      lbEl.querySelector('.cv-lb-nome').title = c;
      lbEl.querySelectorAll('[data-lb-ir]').forEach((b) => { b.hidden = lb.lista.length < 2; });
      lbEl.querySelector('.cv-lb-acoes').innerHTML = htmlAcoesMidia(c, false);
    }
    function irLb(d) {
      if (lb.lista.length < 2) return;
      lb.i = (lb.i + d + lb.lista.length) % lb.lista.length;
      pintarLb();
    }
    function fecharLb() {
      if (!lbAberto()) return;
      lbEl.hidden = true;
      el.classList.remove('cv-com-lb');
      lbEl.querySelector('.cv-lb-img').removeAttribute('src');
      document.removeEventListener('keydown', teclaLb);
      if (lb.volta && lb.volta.isConnected) lb.volta.focus({ preventScroll: true });
    }
    function teclaLb(ev) {
      if (!lbAberto()) return;
      if (ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); fecharLb(); }
      else if (ev.key === 'ArrowRight') { ev.preventDefault(); ev.stopPropagation(); irLb(1); }
      else if (ev.key === 'ArrowLeft') { ev.preventDefault(); ev.stopPropagation(); irLb(-1); }
      else if (ev.key === 'Tab') {           // o foco não sai do lightbox
        const f = [...lbEl.querySelectorAll('button:not([hidden])')];
        if (!f.length) return;
        const i = f.indexOf(document.activeElement);
        if (ev.shiftKey && i <= 0) { ev.preventDefault(); f[f.length - 1].focus(); }
        else if (!ev.shiftKey && i === f.length - 1) { ev.preventDefault(); f[0].focus(); }
      }
    }
    // dentro da Conversa, o lightbox atende ANTES do Esc que para a resposta
    el.addEventListener('keydown', (ev) => { if (lbAberto()) teclaLb(ev); }, true);

    async function copiarTexto(t) {
      try { await navigator.clipboard.writeText(t); return true; }
      catch (_) {
        const ta = document.createElement('textarea'); ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select();
        let ok = false; try { ok = document.execCommand('copy'); } catch (__) { ok = false; }
        ta.remove(); return ok;
      }
    }

    async function acaoMidia(acao, c, botao) {
      if (acao === 'copiar') {
        const ok = await copiarTexto(c);
        const rot = botao.querySelector('span');
        const antes = rot ? rot.textContent : '';
        botao.classList.add('cv-mid-feito'); botao.title = ok ? 'Copiado' : 'Não consegui copiar';
        if (rot) rot.textContent = ok ? 'Copiado' : 'Não copiou';
        $('.cv-anuncio').textContent = ok ? 'Caminho copiado.' : 'Não consegui copiar o caminho.';
        setTimeout(() => { botao.classList.remove('cv-mid-feito'); botao.title = 'Copiar caminho'; if (rot) rot.textContent = antes; }, 1400);
      } else if (acao === 'mostrar') {
        try { await api.post('/api/midia/mostrar', { p: c }); }
        catch (e) { nota(e.message, true); }
      } else if (acao === 'timeline') {
        // só PREENCHE: quem envia é a pessoa, no botão Enviar
        if (lbAberto()) fecharLb();
        entrada.value = mensagemTimeline(c);
        crescer(); fecharMenu();
        entrada.focus();
        entrada.setSelectionRange(entrada.value.length, entrada.value.length);
        $('.cv-anuncio').textContent = 'Pedido pronto no campo de mensagem. Confira e clique em Enviar.';
      }
    }

    // mídia: só uma tocando por vez; o botão e a onda acompanham o áudio
    el.addEventListener('play', (ev) => {
      el.querySelectorAll('video, audio').forEach((x) => { if (x !== ev.target && !x.paused) { try { x.pause(); } catch (_) { /* idem */ } } });
      const fig = ev.target.closest && ev.target.closest('.cv-mid-audio');
      const b = fig && fig.querySelector('[data-audio-play]');
      if (b) { b.innerHTML = ICONE.pausar; b.setAttribute('aria-label', b.getAttribute('aria-label').replace(/^Tocar/, 'Pausar')); }
    }, true);
    const aoParar = (ev) => {
      const fig = ev.target.closest && ev.target.closest('.cv-mid-audio');
      const b = fig && fig.querySelector('[data-audio-play]');
      if (b) { b.innerHTML = ICONE.tocar; b.setAttribute('aria-label', b.getAttribute('aria-label').replace(/^Pausar/, 'Tocar')); }
    };
    el.addEventListener('pause', aoParar, true);
    el.addEventListener('ended', aoParar, true);
    el.addEventListener('timeupdate', (ev) => {
      const fig = ev.target.closest && ev.target.closest('.cv-mid-audio');
      if (!fig) return;
      desenharOnda(fig);
      const t = fig.querySelector('.cv-mid-tempo');
      const dur = isFinite(ev.target.duration) ? ev.target.duration : (ui.infos.get(fig.dataset.mid) || {}).duracao;
      if (t) t.textContent = `${relogioMidia(ev.target.currentTime)} / ${relogioMidia(dur)}`;
    }, true);
    // miniatura: imagem muito larga (folha de contato, original × clone) ocupa a linha inteira
    el.addEventListener('load', (ev) => {
      const img = ev.target;
      if (img && img.tagName === 'IMG' && img.hasAttribute('data-mid-img') && img.naturalHeight && img.naturalWidth / img.naturalHeight > 1.9) {
        const f = img.closest('.cv-mid-img'); f && f.classList.add('cv-mid-larga');
      }
    }, true);
    // sem ffmpeg não sai miniatura: a grade cai no arquivo original
    el.addEventListener('error', (ev) => {
      const img = ev.target;
      if (img && img.tagName === 'IMG' && img.hasAttribute('data-mid-img') && img.dataset.original && img.src !== img.dataset.original) {
        img.src = img.dataset.original;
      }
    }, true);

    // ---------------------------------------------------------- desenho
    function pintarMensagens() {
      const ms = st.mensagens;
      const de = Math.max(0, ms.length - st.visiveis);
      let html = de > 0 ? `<button type="button" class="cv-anteriores" data-anteriores>Mostrar ${Math.min(VISIVEIS_INICIO, de)} mensagens anteriores (${de} ocultas)</button>` : '';
      if (!ms.length && !(S && S.viva)) html += op.boasVindas ? `<div class="cv-msg cv-ia cv-boas">${op.boasVindas}</div>` : '';
      for (let i = de; i < ms.length; i++) html += htmlMensagem(ms[i], i, ui, api);
      msgsEl.innerHTML = html;
      hidratar(msgsEl);
    }

    // a resposta viva: um nó por passo, redesenhado só quando o passo muda
    const vivoNos = new Map();
    function pintarVivo() {
      const v = S && S.viva;
      if (!v) { vivoEl.hidden = true; vivoEl.innerHTML = ''; vivoNos.clear(); return; }
      if (vivoEl.hidden || !vivoEl.firstChild) {
        vivoEl.hidden = false;
        vivoEl.innerHTML = `${v.texto || v.anexos.length ? `<div class="cv-msg cv-eu">${v.texto ? `<div class="cv-bolha">${esc(v.texto)}</div>` : ''}${htmlAnexos(v.anexos, api)}</div>` : ''}
          <div class="cv-msg cv-ia"><div class="cv-quem">${esc(S.provedor === 'chatgpt' ? 'ChatGPT' : 'Claude')}</div><div class="cv-vivo-passos"></div>
          <div class="cv-estado" role="status"><span class="cv-giro"></span><b>Pensando…</b><span class="cv-tempo" aria-hidden="true">0 s</span><span class="cv-etapa"></span>
            <span class="cv-esc">Esc para parar</span></div>
          <div class="cv-ajuda" hidden>Se o macOS pedir acesso a uma pasta, clique em <b>Permitir</b> — a resposta continua depois disso.</div></div>`;
        vivoNos.clear();
      }
      const cx = vivoEl.querySelector('.cv-vivo-passos');
      const ps = v.passos;
      const ini = ui.vivoTudo ? 0 : Math.max(0, ps.length - VIVO_JANELA);
      let cab = cx.querySelector(':scope > .cv-vivo-ocultas');
      if (ini > 0) {
        if (!cab) { cab = document.createElement('button'); cab.type = 'button'; cab.className = 'cv-grupo-mais cv-vivo-ocultas'; cab.dataset.vivoTudo = '1'; cx.prepend(cab); }
        cab.textContent = `▸ mais ${ini} ações anteriores`;
      } else if (cab) cab.remove();
      for (const [i, no] of vivoNos) if (i < ini || i >= ps.length) { no.remove(); vivoNos.delete(i); }
      const psD = dedupeMidias(ps, ui);
      for (let i = ini; i < ps.length; i++) {
        const p = psD[i];
        const ass = JSON.stringify(p) + '|' + ui.abertos.has('v' + i) + [...ui.mais].filter((k) => k.startsWith('v' + i + ':')).join();
        let no = vivoNos.get(i);
        if (!no) {
          no = document.createElement('div'); no.className = 'cv-vivo-passo';
          const depois = [...vivoNos.keys()].filter((k) => k > i).sort((a, b) => a - b)[0];
          if (depois != null) cx.insertBefore(no, vivoNos.get(depois)); else cx.appendChild(no);
          vivoNos.set(i, no);
        }
        if (no.dataset.ass !== ass) { no.dataset.ass = ass; no.innerHTML = htmlPasso(p, 'v' + i, ui); hidratar(no); }
      }
      // em que ponto está: a ação rodando agora vence a etapa do servidor
      let etapa = v.etapa || '', titulo = 'Pensando…';
      for (let i = ps.length - 1; i >= 0; i--) {
        const p = ps[i];
        if (p && p.tipo === 'ferramenta' && (p.estado || 'rodando') === 'rodando') { etapa = rotuloAcao(p).texto; titulo = 'Trabalhando…'; break; }
        if (p && p.tipo === 'parcial') { etapa = ''; titulo = 'Escrevendo…'; break; }
      }
      const tt = vivoEl.querySelector('.cv-estado b'); if (tt) tt.textContent = titulo;
      const e = vivoEl.querySelector('.cv-etapa'); if (e) e.textContent = etapa ? '· ' + etapa : '';
      const esc_ = vivoEl.querySelector('.cv-esc'); if (esc_) esc_.hidden = !v.cancelavel;
      $('.cv-parar').hidden = !v.cancelavel;
      relogio();
    }

    function relogio() {
      const v = S && S.viva;
      const t = vivoEl.querySelector('.cv-tempo');
      if (v && t) t.textContent = duracao((Date.now() - v.inicio) / 1000);
      const aj = vivoEl.querySelector('.cv-ajuda');
      if (v && aj) aj.hidden = Date.now() - v.marca < VIVO_AJUDA_MS || v.passos.length > 0;
      const agora = Date.now() / 1000;
      vivoEl.querySelectorAll('[data-dur-inicio]').forEach((n) => { if (n.dataset.durInicio) n.textContent = duracao(agora - +n.dataset.durInicio); });
      vivoEl.querySelectorAll('[data-pensa-inicio]').forEach((n) => { if (n.dataset.pensaInicio) n.textContent = 'Pensando… ' + duracao(agora - +n.dataset.pensaInicio); });
    }

    function pintarTarefas() {
      const box = $('.cv-tarefas');
      const itens = tarefasAtuais(S && S.viva ? S.viva.passos : null, st.mensagens);
      if (!itens) { box.hidden = true; box.innerHTML = ''; return; }
      const feitas = itens.filter((t) => t.estado === 'feito').length;
      const agora = itens.find((t) => t.estado === 'andamento');
      const aberto = st.tarefasAbertas == null ? !!(S && S.viva) && !op.compacto : st.tarefasAbertas;
      box.hidden = false;
      box.innerHTML = `<button type="button" class="cv-tarefas-topo" data-tarefas aria-expanded="${aberto}">
          ${ICONE.lista}<b>Tarefas</b><span class="cv-tarefas-conta">${feitas}/${itens.length}</span>
          <span class="cv-tarefas-agora">${agora ? esc(agora.ativo || agora.texto) : ''}</span><span class="cv-seta">${aberto ? '▾' : '▸'}</span></button>
        ${aberto ? `<ul class="cv-tarefas-lista">${itens.map((t) => `<li class="t-${esc(t.estado)}">
          <span class="cv-caixa" aria-hidden="true">${t.estado === 'feito' ? '✓' : t.estado === 'andamento' ? '' : ''}</span>
          <span>${esc(t.estado === 'andamento' ? (t.ativo || t.texto) : t.texto)}</span>
          <span class="cv-sr">${t.estado === 'feito' ? '(feito)' : t.estado === 'andamento' ? '(em andamento)' : '(pendente)'}</span></li>`).join('')}</ul>` : ''}`;
    }

    function pintarFila() {
      const box = $('.cv-fila');
      const f = S ? S.fila : null;
      if (!f || !f.tamanho) { box.hidden = true; box.innerHTML = ''; return; }
      box.hidden = false;
      box.innerHTML = `<div class="cv-fila-topo"><b>Na fila (${f.tamanho})</b><span>${f.pausada ? 'pausada — a última resposta não terminou bem' : 'vão uma por vez, quando a resposta atual acabar'}</span>
          ${f.pausada ? '<button type="button" class="cv-bt mini" data-fila-retomar>Retomar</button>' : ''}</div>
        <ol>${f.itens.map((x, i) => `<li><span>${esc(x.texto || '(só anexos)')}${x.anexos.length ? ` <em>+${x.anexos.length} anexo(s)</em>` : ''}</span>
          <button type="button" class="cv-x" data-fila-tirar="${i}" aria-label="Tirar da fila">✕</button></li>`).join('')}</ol>`;
    }

    function pintarAnexos() {
      const box = $('.cv-anexos');
      box.innerHTML = st.anexos.map((a, i) => `<span class="cv-chip${a.erro ? ' ruim' : ''}${a.enviando ? ' enviando' : ''}" title="${esc(a.caminho || a.nome)}">
          ${a.previa ? `<img src="${esc(a.previa)}" alt="">` : ICONE.clipe}
          <span>${esc(a.erro ? a.nome + ' — ' + a.erro : a.enviando ? a.nome + ' (enviando…)' : (a.caminho || a.nome))}</span>
          <button type="button" class="cv-x" data-anexo-tirar="${i}" aria-label="Remover anexo">✕</button></span>`).join('');
    }

    function pintarRodape() {
      const box = $('.cv-rodape');
      const ia = st.ia;
      const skill = skillEmUso(st.mensagens, S && S.viva ? S.viva.passos : null);
      const prov = ia ? ia.provedores.map((p) => `<button type="button" class="cv-ia-op${p.id === ia.escolhido ? ' ativa' : ''}${p.pronto ? '' : ' sem'}"
          data-ia="${esc(p.id)}" aria-pressed="${p.id === ia.escolhido}" title="${esc(p.pronto ? (p.ferramentas || p.origem || '') : (p.msg || 'Não conectado'))}"><i></i>${esc(p.nome)}</button>`).join('') : '';
      box.innerHTML = `<div class="cv-ia-sel" role="group" aria-label="IA">${prov}</div>
        <span class="cv-rod-item" title="Projeto">${ICONE.filme}<span>${esc(st.meta.projeto_nome || (st.meta.projeto ? st.meta.projeto : 'sem projeto'))}</span></span>
        ${skill ? `<span class="cv-rod-item cv-rod-skill" title="${esc('Skill em uso: ' + skill)}">${ICONE.estrela}<span>${esc(nomeSkill(skill))}</span></span>` : ''}
        <span class="cv-rod-dica">Enter envia · Shift+Enter quebra linha · ↑ última mensagem</span>`;
    }

    function pintarCartao() {
      const box = $('.cv-aprovacao');
      const c = st.cartao;
      if (!c) { box.hidden = true; box.innerHTML = ''; return; }
      const custo = c.custo
        ? `<div class="cv-custo"><span>${numero(c.custo.itens)} × ${esc(String(c.custo.unitario ?? '?'))} cr</span><span>motor <code>${esc(c.custo.motor || '')}</code></span>
            <b>≈ ${esc(String(c.custo.total))} créditos</b>${c.custo.saldo != null ? `<span>saldo ${esc(String(Math.round(c.custo.saldo)))} cr</span>` : ''}</div>`
        : `<div class="cv-custo"><span>O valor exato aparece na hora de gerar, pelo motor escolhido.</span></div>`;
      const itens = c.saldo_itens ? `<div class="cv-cartao-itens">${c.saldo_itens.aprovados} aprovados · ${c.saldo_itens.rejeitados} rejeitados · ${c.saldo_itens.pendentes} sem julgamento</div>` : '';
      box.hidden = false;
      box.innerHTML = `<div class="cv-cartao" role="region" aria-label="Aprovação necessária">
        <div class="cv-cartao-topo">${ICONE.aviso}<b>Precisa da sua aprovação</b><span class="cv-selo">gasta crédito</span></div>
        <p>Aprovar a etapa <b>${esc(c.n)} · ${esc(c.nome)}</b> libera <b>${esc(c.libera_nome)}</b>, que gasta crédito.</p>
        ${itens}${custo}
        ${st.cartaoErro ? `<div class="cv-cartao-erro">${esc(st.cartaoErro)}</div>` : ''}
        <div class="cv-cartao-acoes">
          <button type="button" class="cv-bt" data-recusar>Recusar</button>
          <button type="button" class="cv-bt principal" data-aprovar>Aprovar e liberar o gasto</button>
        </div>
        <div class="cv-cartao-nota">Nada é gerado sozinho: depois de aprovar, peça na conversa para seguir.</div></div>`;
    }

    function pintarNotas() {
      notasEl.innerHTML = st.notas.map((n) => `<div class="cv-msg cv-nota">${n}</div>`).join('');
      if (st.falha) {
        const f = st.falha;
        notasEl.insertAdjacentHTML('beforeend', `<div class="cv-msg cv-ia"><div class="cv-falha" role="alert">
          <p>${esc(f.motivo || 'A conexão com a IA não está disponível agora.')}</p>
          <div class="cv-falha-acoes">${(op.acoesFalha || []).map((a, i) => `<button type="button" class="cv-bt" data-falha-acao="${i}">${esc(a.rotulo)}</button>`).join('')}
            <button type="button" class="cv-bt principal" data-tentar>Tentar novamente</button></div></div></div>`);
      }
    }

    function pintarTudo() {
      pintarBarra(); pintarMensagens(); pintarVivo(); pintarNotas(); pintarTarefas(); pintarFila(); pintarAnexos(); pintarRodape(); pintarCartao();
      ocupado();
    }

    function ocupado() {
      const v = !!(S && S.viva);
      el.classList.toggle('trabalhando', v);
      $('.cv-enviar').setAttribute('aria-label', v ? 'Pôr na fila' : 'Enviar');
      $('.cv-enviar').title = v ? 'Pôr na fila (Enter)' : 'Enviar (Enter)';
      if (!v) $('.cv-parar').hidden = true;
    }

    // ---------------------------------------------------------- sessão
    function ligarSessao(cid) {
      if (st.desligar) st.desligar();
      S = sessao(cid || '__nova__');
      S.cfg = cfg;
      if (st.ia) S.provedor = st.ia.escolhido;
      const ouvir = (tipo, d) => {
        if (!st.montado) return;
        if (tipo === 'inicio') { st.falha = null; pintarNotas(); pintarVivo(); pintarTarefas(); ocupado(); rolarFim(true); }
        else if (tipo === 'vivo') {
          const antes = lista.scrollHeight;
          pintarVivo(); pintarTarefas();
          if (lista.scrollHeight !== antes) rolarFim();
          if (d.passos.some((p) => p && p.recusado) && !st._recusaVista) { st._recusaVista = true; buscarCartao(); }
        } else if (tipo === 'fila') pintarFila();
        else if (tipo === 'fim') terminou(d);
      };
      S.ouvintes.add(ouvir);
      st.desligar = () => S && S.ouvintes.delete(ouvir);
      if (S.viva) { pintarVivo(); rolarFim(true); }
    }

    async function terminou(d) {
      st._recusaVista = false;
      pintarVivo(); ocupado();
      if (d.estado === 'pronto') {
        const r = d.resultado || {};
        if (r.conversa && r.conversa !== st.cid) { trocarId(r.conversa); }
        await recarregar();
        const ult = [...st.mensagens].reverse().find((m) => m.role === 'assistant');
        if (ult) $('.cv-anuncio').textContent = 'Resposta: ' + String(ult.content || '').slice(0, 400);
        op.aoTerminar && op.aoTerminar({ conversa: st.cid, meta: st.meta });
        buscarCartao();
      } else if (d.estado === 'cancelado') {
        st.notas.push(`<div class="cv-cancelado">${ICONE.parar}<span>Cancelado. Esta mensagem não foi guardada no histórico — o texto voltou para a caixa.</span></div>`);
        pintarNotas();
        if (!entrada.value) { entrada.value = d.texto || ''; crescer(); }
        if (d.anexos && d.anexos.length && !st.anexos.length) { st.anexos = d.anexos.map((c) => ({ nome: base(c), caminho: c })); pintarAnexos(); }
        $('.cv-anuncio').textContent = 'Resposta cancelada.';
      } else {
        st.falha = { motivo: d.erro, texto: d.texto, anexos: d.anexos };
        pintarNotas();
        $('.cv-anuncio').textContent = 'A IA falhou: ' + (d.erro || '');
      }
      pintarTarefas(); pintarFila(); pintarRodape();
      rolarFim();
    }

    function trocarId(cid) {
      const velha = S;
      st.cid = cid;
      // a sessão provisória (sem id) passa a ser a desta conversa
      if (velha && velha.cid === '__nova__') {
        delete SESSOES.__nova__;
        velha.cid = cid;
        SESSOES[cid] = velha;
      } else ligarSessao(cid);
      op.aoTrocarConversa && op.aoTrocarConversa(cid);
    }

    async function garantirConversa() {
      if (st.cid) return st.cid;
      const r = await api.post('/api/conversas/nova');
      trocarId(r.conversa);
      return st.cid;
    }

    // ---------------------------------------------------------- dados
    async function recarregar() {
      if (!st.cid) return;
      try {
        const r = await api.get('/api/conversas/' + encodeURIComponent(st.cid));
        st.mensagens = r.mensagens || [];
        st.meta = r.meta || {};
      } catch (e) { /* mantém o que já tem na tela */ }
      if (!st.montado) return;
      pintarBarra(); pintarMensagens(); pintarTarefas(); pintarRodape();
      rolarFim();
    }

    async function carregar() {
      try {
        if (op.carregar) {
          const r = await op.carregar();
          st.cid = r.conversa || st.cid; st.mensagens = r.mensagens || []; st.meta = r.meta || {};
        } else if (st.cid) {
          const r = await api.get('/api/conversas/' + encodeURIComponent(st.cid));
          st.mensagens = r.mensagens || []; st.meta = r.meta || {};
        } else if ((op.aoAbrir || 'ultima') === 'nova') {
          // começa do zero; a pasta da conversa só nasce na 1ª mensagem
          st.cid = null; st.mensagens = []; st.meta = {};
        } else if (lembrada()) {
          // a última que ESTA janela tinha aberta (app e painel lembram cada um a sua)
          const cid = lembrada();
          let r = null;
          try { r = await api.get('/api/conversas/' + encodeURIComponent(cid)); } catch (_) { r = null; }
          if (r && r.meta && r.meta.criada) {
            st.cid = cid; st.mensagens = r.mensagens || []; st.meta = r.meta || {};
            op.aoTrocarConversa && op.aoTrocarConversa(cid);
          } else {
            lembrar(null);
            const r2 = await api.get('/api/conversa');
            st.cid = r2.conversa || null; st.mensagens = r2.mensagens || [];
            if (st.cid) { try { st.meta = (await api.get('/api/conversas/' + encodeURIComponent(st.cid))).meta || {}; } catch (_) { /* sem meta */ } }
            if (st.cid) op.aoTrocarConversa && op.aoTrocarConversa(st.cid);
          }
        } else {
          const r = await api.get('/api/conversa');
          st.cid = r.conversa || null; st.mensagens = r.mensagens || [];
          if (st.cid) { try { st.meta = (await api.get('/api/conversas/' + encodeURIComponent(st.cid))).meta || {}; } catch (_) { /* sem meta */ } }
          if (st.cid) op.aoTrocarConversa && op.aoTrocarConversa(st.cid);
        }
      } catch (e) {
        st.notas.push(`<div class="cv-falha">${esc('Não consegui abrir a conversa: ' + e.message)}</div>`);
      }
      st.carregou = true;
      st.enviados = st.mensagens.filter((m) => m.role === 'user').map((m) => partesUsuario(m).texto).filter(Boolean);
      ligarSessao(st.cid);
      if (!st.montado) return;
      pintarTudo();
      rolarFim(true);
      buscarCartao();
    }

    async function carregarIA() {
      try { st.ia = await api.get('/api/ia'); if (S) S.provedor = st.ia.escolhido; } catch (_) { st.ia = null; }
      if (st.montado) pintarRodape();
    }

    async function buscarCartao() {
      if (!st.cid) return;
      try { st.cartao = (await api.get(`/api/conversas/${encodeURIComponent(st.cid)}/aprovacao`)).cartao || null; }
      catch (_) { st.cartao = null; }
      if (st.montado) pintarCartao();
    }

    // ---------------------------------------------------------- enviar
    function crescer() {
      entrada.style.height = 'auto';
      entrada.style.height = Math.min(entrada.scrollHeight, op.compacto ? 120 : 180) + 'px';
    }

    async function enviar(textoForcado) {
      const texto = (textoForcado != null ? textoForcado : entrada.value).trim();
      if (st.anexos.some((a) => a.enviando)) { nota('Espere os anexos terminarem de enviar.'); return; }
      const anexos = st.anexos.filter((a) => a.caminho && !a.erro).map((a) => a.caminho);
      if (!texto && !anexos.length) return;
      if (texto.startsWith('/') && !anexos.length && /^\/\S+$/.test(texto)) {
        const c = COMANDOS.find((x) => x.nome === texto.toLowerCase() || x.nome === texto.toLowerCase().replace(/s$/, ''));
        if (c) { entrada.value = ''; crescer(); fecharMenu(); return comando(c.id); }
      }
      try { await garantirConversa(); } catch (e) { nota('Não consegui criar a conversa: ' + e.message, true); return; }
      if (textoForcado == null) { entrada.value = ''; crescer(); }
      st.anexos = []; pintarAnexos();
      st.falha = null; pintarNotas();
      if (texto) { st.enviados.push(texto); }
      st.volta = -1;
      fecharMenu();
      if (st.ia) S.provedor = st.ia.escolhido;
      await enviarNaSessao(S, texto, anexos);
    }

    function nota(texto, ruim) {
      st.notas.push(`<div class="cv-nota-txt${ruim ? ' ruim' : ''}">${esc(texto)}</div>`);
      pintarNotas(); rolarFim(true);
    }

    async function parar() {
      if (!S || !S.viva) return;
      if (!S.viva.cancelavel) { nota('Esta resposta não pode ser interrompida — ela não roda num processo que o app consiga encerrar.'); return; }
      const e = vivoEl.querySelector('.cv-etapa'); if (e) e.textContent = '· parando…';
      const r = await cancelarNaSessao(S);
      if (!r.ok) nota(r.msg || 'Não deu para parar.', true);
    }

    // ---------------------------------------------------------- comandos
    async function comando(id) {
      if (id === 'nova') {
        if (S && S.viva) { nota('Espere a resposta atual acabar (ou aperte Esc) antes de abrir outra conversa.'); return; }
        try {
          const r = await api.post('/api/conversas/nova');
          st.notas = []; st.falha = null; st.cartao = null;
          st.mensagens = []; st.meta = {};
          st.cid = r.conversa; ligarSessao(st.cid);
          st.hist.aberto = false; st.hist.confirma = null; pintarHist();
          ui.abertos.clear(); st.visiveis = VISIVEIS_INICIO;
          pintarTudo();
          op.aoTrocarConversa && op.aoTrocarConversa(st.cid);
          entrada.focus();
        } catch (e) { nota(e.message, true); }
      } else if (id === 'limpar') {
        if (!st.cid || !st.mensagens.length) { nota('A conversa já está vazia.'); return; }
        if (S && S.viva) { nota('Espere a resposta atual acabar (ou aperte Esc) antes de limpar.'); return; }
        st.notas.push(`<div class="cv-confirma" role="alertdialog" aria-label="Confirmar limpeza">
          <span>Apagar as <b>${st.mensagens.length}</b> mensagens desta conversa? A IA também esquece o que foi dito. O projeto e as aprovações continuam.</span>
          <button type="button" class="cv-bt" data-confirma="nao">Cancelar</button>
          <button type="button" class="cv-bt perigo" data-confirma="limpar">Limpar</button></div>`);
        pintarNotas(); rolarFim(true);
        const b = notasEl.querySelector('[data-confirma="nao"]'); b && b.focus();
      } else if (id === 'skills') {
        entrada.value = '/skills '; crescer(); entrada.focus();
        abrirMenu();
      } else if (id === 'custo') {
        const c = resumoCusto(st.mensagens, S && S.viva ? S.viva.passos : null);
        const linhas = [
          ['Respostas', numero(c.respostas)],
          ['Ações', numero(c.acoes)],
          ['Tempo', c.tempo_ms ? duracao(c.tempo_ms / 1000) : '—'],
        ];
        if (c.com_uso) {
          linhas.push(['Tokens', `${numero(c.tokens_entrada)} de entrada · ${numero(c.tokens_saida)} de saída`]);
          linhas.push(['Custo estimado', 'US$ ' + c.custo_usd.toFixed(2).replace('.', ',')]);
        }
        st.notas.push(`<div class="cv-resumo"><div class="cv-resumo-topo">${ICONE.lista}<b>Resumo desta conversa</b></div>
          <dl>${linhas.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>
          <p>${c.com_uso ? `Tokens e custo contam ${c.com_uso} resposta(s) do Claude Code. Na assinatura o custo é o equivalente em preço de API — não é cobrado à parte.`
            : 'O provedor desta conversa não informa tokens nem custo.'}</p></div>`);
        pintarNotas(); rolarFim(true);
      } else if (id === 'parar') {
        if (S && S.viva) parar(); else nota('Nada em andamento para parar.');
      }
    }

    // ---------------------------------------------------------- menu
    function fecharMenu() {
      st.menu = null; menuEl.hidden = true; menuEl.innerHTML = '';
      entrada.setAttribute('aria-expanded', 'false'); entrada.removeAttribute('aria-activedescendant');
    }

    function pintarMenu() {
      const m = st.menu;
      if (!m || !m.itens.length) {
        if (m && m.vazio) {
          menuEl.hidden = false;
          menuEl.innerHTML = `<div class="cv-menu-topo">${esc(m.titulo)}</div><div class="cv-menu-vazio">${esc(m.vazio)}</div>`;
          entrada.setAttribute('aria-expanded', 'true');
          return;
        }
        menuEl.hidden = true; menuEl.innerHTML = ''; entrada.setAttribute('aria-expanded', 'false'); return;
      }
      menuEl.hidden = false;
      entrada.setAttribute('aria-expanded', 'true');
      menuEl.innerHTML = `<div class="cv-menu-topo">${esc(m.titulo)}</div>` + m.itens.map((it, i) =>
        `<div class="cv-menu-op${i === m.sel ? ' sel' : ''}" role="option" id="${menuEl.id}-${i}" aria-selected="${i === m.sel}" data-op="${i}">
          <span class="cv-menu-nome">${esc(it.rotulo)}</span><span class="cv-menu-desc">${esc(it.desc || '')}</span></div>`).join('');
      entrada.setAttribute('aria-activedescendant', `${menuEl.id}-${m.sel}`);
      const sel = menuEl.querySelector('.sel'); if (sel && sel.scrollIntoView) sel.scrollIntoView({ block: 'nearest' });
    }

    async function abrirMenu() {
      const g = lerGatilho(entrada.value, entrada.selectionStart);
      if (!g) { fecharMenu(); return; }
      if (g.tipo === 'comando') {
        st.menu = { gatilho: g, titulo: 'Comandos', sel: 0,
          itens: filtrarComandos(g.consulta).map((c) => ({ rotulo: c.nome, desc: c.desc, comando: c.id })) };
        pintarMenu();
      } else if (g.tipo === 'skills') {
        if (!st.skills) {
          st.menu = { gatilho: g, titulo: 'Skills', sel: 0, itens: [], vazio: 'carregando…' }; pintarMenu();
          try {
            const r = await api.get('/api/skills');
            const daqui = (r.skills || []).filter((s) => s.instalada !== false).map((s) => ({ nome: s.nome, descricao: s.descricao || '' }));
            const nomes = new Set(daqui.map((s) => s.nome));
            (r.do_usuario || []).forEach((n) => { if (!nomes.has(n)) daqui.push({ nome: n, descricao: 'skill sua, instalada nesta máquina' }); });
            st.skills = daqui;
          } catch (e) { st.skills = []; }
        }
        const g2 = lerGatilho(entrada.value, entrada.selectionStart);
        if (!g2 || g2.tipo !== 'skills') return;
        const xs = filtrarSkills(st.skills, g2.consulta);
        st.menu = { gatilho: g2, titulo: `Skills instaladas (${st.skills.length})`, sel: 0,
          itens: xs.map((s) => ({ rotulo: s.nome, desc: s.descricao, skill: s.nome })),
          vazio: st.skills.length ? 'Nenhuma skill com esse nome.' : 'Nenhuma skill instalada — instale pela aba Ambiente.' };
        pintarMenu();
      } else if (g.tipo === 'arquivo') {
        const minha = ++st.buscaArq;
        if (!st.cid) {
          st.menu = { gatilho: g, titulo: 'Arquivos', sel: 0, itens: [], vazio: 'Mande a primeira mensagem para a conversa ganhar uma pasta.' };
          pintarMenu(); return;
        }
        await dormir(120);                           // espera a pessoa parar de digitar
        if (minha !== st.buscaArq) return;
        try {
          const r = await api.get(`/api/conversas/${encodeURIComponent(st.cid)}/arquivos?q=${encodeURIComponent(g.consulta)}`);
          if (minha !== st.buscaArq) return;
          const g2 = lerGatilho(entrada.value, entrada.selectionStart);
          if (!g2 || g2.tipo !== 'arquivo') return;
          st.menu = { gatilho: g2, titulo: r.raizes && r.raizes.length ? 'Arquivos em ' + r.raizes.map(base).join(', ') : 'Arquivos', sel: 0,
            itens: (r.arquivos || []).map((a) => ({ rotulo: a.rel, desc: a.raiz, caminho: a.caminho })),
            vazio: r.raizes && r.raizes.length ? 'Nenhum arquivo com esse nome.' : 'Esta conversa ainda não tem projeto — abra um projeto ou o Premiere para buscar arquivos.' };
          pintarMenu();
        } catch (e) { st.menu = { gatilho: g, titulo: 'Arquivos', sel: 0, itens: [], vazio: e.message }; pintarMenu(); }
      }
    }

    function escolherMenu(i) {
      const m = st.menu;
      if (!m || !m.itens[i]) return;
      const it = m.itens[i];
      if (it.comando) { entrada.value = ''; crescer(); fecharMenu(); comando(it.comando); return; }
      if (it.skill) {
        entrada.value = `Use a skill ${it.skill} para `; crescer(); fecharMenu();
        entrada.focus(); entrada.setSelectionRange(entrada.value.length, entrada.value.length);
        return;
      }
      if (it.caminho) {
        const r = aplicarArquivo(entrada.value, m.gatilho, it.caminho, entrada.selectionStart);
        entrada.value = r.texto; crescer(); fecharMenu();
        entrada.focus(); entrada.setSelectionRange(r.cursor, r.cursor);
      }
    }

    // ---------------------------------------------------------- anexos
    async function anexar(arquivos) {
      const lista_ = [...(arquivos || [])];
      if (!lista_.length) return;
      try { await garantirConversa(); } catch (e) { nota('Não consegui preparar a conversa para o anexo: ' + e.message, true); return; }
      for (const f of lista_) {
        const a = { nome: f.name || 'anexo', caminho: null, enviando: true, previa: null };
        if (IMAGEM.test(a.nome) && typeof URL !== 'undefined' && URL.createObjectURL) { try { a.previa = URL.createObjectURL(f); } catch (_) { /* sem prévia */ } }
        st.anexos.push(a); pintarAnexos();
        if (f.path) { a.caminho = f.path; a.enviando = false; pintarAnexos(); continue; }   // painel CEP/Electron: o caminho existe
        try {
          const r = await api.enviarArquivo(`/api/conversas/${encodeURIComponent(st.cid)}/anexo`, f);
          a.caminho = r.caminho;
        } catch (e) { a.erro = e.message; }
        a.enviando = false; pintarAnexos();
      }
      entrada.focus();
    }

    // ---------------------------------------------------------- eventos
    const sobre = (ev, sel) => ev.target && ev.target.closest && ev.target.closest(sel);

    el.addEventListener('click', async (ev) => {
      let b;
      // ---- barra do topo e histórico
      if (sobre(ev, '[data-historico]')) { st.hist.aberto ? fecharHist(true) : abrirHist(); return; }
      if (sobre(ev, '[data-nova]')) { comando('nova'); return; }
      if (sobre(ev, '[data-hist-fechar]')) { fecharHist(true); return; }
      if ((b = sobre(ev, '[data-hist-abrir]'))) { abrirConversa(b.dataset.histAbrir); return; }
      if ((b = sobre(ev, '[data-hist-apagar]'))) {
        st.hist.confirma = b.dataset.histApagar; pintarHistLista();
        const c = histEl.querySelector('[data-hist-confirma="nao"]'); c && c.focus(); return;
      }
      if ((b = sobre(ev, '[data-hist-confirma]'))) {
        if (b.dataset.histConfirma === 'nao') { const id = st.hist.confirma; st.hist.confirma = null; pintarHistLista(); const x = histEl.querySelector(`[data-hist-apagar="${typeof CSS !== 'undefined' && CSS.escape ? CSS.escape(id || '') : id}"]`); x && x.focus(); }
        else apagarConversa(b.dataset.histConfirma);
        return;
      }
      // ---- entregas de mídia e lightbox
      if ((b = sobre(ev, '[data-lb-fechar]'))) { fecharLb(); return; }
      if ((b = sobre(ev, '[data-lb-ir]'))) { irLb(+b.dataset.lbIr); return; }
      if ((b = sobre(ev, '[data-mid-acao]'))) { acaoMidia(b.dataset.midAcao, b.dataset.alvo, b); return; }
      if (lbAberto() && ev.target && ev.target.hasAttribute && ev.target.hasAttribute('data-lb-fundo')) { fecharLb(); return; }
      if ((b = sobre(ev, '[data-lb]'))) { abrirLb(b.dataset.lb, b.dataset.lbI, b); return; }
      if ((b = sobre(ev, '[data-mid-todas]'))) {
        const k = b.dataset.midTodas;
        ui.midiasTodas.has(k) ? ui.midiasTodas.delete(k) : ui.midiasTodas.add(k);
        redesenharDono(k); return;
      }
      if ((b = sobre(ev, '[data-audio-play]'))) { tocarAudio(b.closest('.cv-mid-audio')); return; }
      if ((b = sobre(ev, '[data-audio-onda]'))) {
        const r = b.getBoundingClientRect();
        const x = r.width ? Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width)) : 0;
        tocarAudio(b.closest('.cv-mid-audio'), x); return;
      }
      if ((b = sobre(ev, '[data-destino-projeto]'))) { escolherDestino({ projeto: b.dataset.destinoProjeto }, b); return; }
      if ((b = sobre(ev, '[data-destino-escolher]'))) { escolherDestino({ escolher: true }, b); return; }
      if ((b = sobre(ev, '[data-mid-tentar]'))) {
        const u = b.dataset.midTentar; const ant = ui.baixas.get(u) || {};
        ui.baixas.delete(u); baixarEntrega(u, ant.tipo || null); repintarDonos(u); return;
      }
      if ((b = sobre(ev, '[data-copiar]'))) {
        const pre = b.closest('.cv-codigo').querySelector('pre');
        const t = pre ? pre.textContent : '';
        try { await navigator.clipboard.writeText(t); }
        catch (_) {
          const ta = document.createElement('textarea'); ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
          document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (__) { /* sem área de transferência */ } ta.remove();
        }
        b.textContent = 'Copiado'; setTimeout(() => { b.textContent = 'Copiar'; }, 1400);
        return;
      }
      if ((b = sobre(ev, '[data-abrir]'))) {
        const k = b.dataset.abrir;
        ui.abertos.has(k) ? ui.abertos.delete(k) : ui.abertos.add(k);
        redesenharDono(k); return;
      }
      if ((b = sobre(ev, '[data-mais]'))) {
        const k = b.dataset.mais;
        ui.mais.has(k) ? ui.mais.delete(k) : ui.mais.add(k);
        redesenharDono(k.split(':').slice(0, 2).join(':').replace(/:[ert]$/, '')); return;
      }
      if ((b = sobre(ev, '[data-grupo]'))) {
        const k = b.dataset.grupo;
        ui.grupos.has(k) ? ui.grupos.delete(k) : ui.grupos.add(k);
        pintarMensagens(); return;
      }
      if (sobre(ev, '[data-vivo-tudo]')) { ui.vivoTudo = true; vivoNos.forEach((n) => n.remove()); vivoNos.clear(); pintarVivo(); return; }
      if (sobre(ev, '[data-anteriores]')) {
        const alt = lista.scrollHeight;
        st.visiveis += VISIVEIS_INICIO; pintarMensagens();
        lista.scrollTop += lista.scrollHeight - alt;       // mantém o que estava na tela no lugar
        return;
      }
      if ((b = sobre(ev, '[data-tarefas]'))) { st.tarefasAbertas = b.getAttribute('aria-expanded') !== 'true'; pintarTarefas(); return; }
      if ((b = sobre(ev, '[data-fila-tirar]'))) { S.fila.remover(+b.dataset.filaTirar); pintarFila(); return; }
      if (sobre(ev, '[data-fila-retomar]')) {
        S.fila.pausada = false; pintarFila();
        if (!S.viva) { const p = S.fila.tirar(); if (p) { pintarFila(); enviarNaSessao(S, p.texto, p.anexos); } }
        return;
      }
      if ((b = sobre(ev, '[data-anexo-tirar]'))) { st.anexos.splice(+b.dataset.anexoTirar, 1); pintarAnexos(); return; }
      if ((b = sobre(ev, '[data-ia]'))) {
        const id = b.dataset.ia;
        const p = (st.ia && st.ia.provedores || []).find((x) => x.id === id);
        if (p && !p.pronto) { op.aoPedirConta ? op.aoPedirConta(p) : nota(p.msg || 'Conecte esta IA na aba Contas.', true); return; }
        try { const r = await api.post('/api/ia/escolher', { provedor: id }); st.ia = r.estado; if (S) S.provedor = st.ia.escolhido; pintarRodape(); }
        catch (e) { nota(e.message, true); }
        return;
      }
      if ((b = sobre(ev, '[data-op]'))) { escolherMenu(+b.dataset.op); return; }
      if (sobre(ev, '[data-aprovar]') || sobre(ev, '[data-recusar]')) {
        const c = st.cartao; if (!c) return;
        const aprovar = !!sobre(ev, '[data-aprovar]');
        el.querySelectorAll('[data-aprovar],[data-recusar]').forEach((x) => { x.disabled = true; });
        try {
          await api.post(`/api/projetos/${encodeURIComponent(c.projeto)}/etapa/${encodeURIComponent(c.etapa)}/${aprovar ? 'aprovar' : 'rejeitar'}`,
            { nota: aprovar ? 'aprovado pelo cartão da conversa' : 'recusado pelo cartão da conversa' });
          st.cartaoErro = '';
          nota(aprovar ? `Etapa “${c.nome}” aprovada por você. “${c.libera_nome}” está liberada.` : `Etapa “${c.nome}” recusada por você. Nada foi gerado.`);
          if (aprovar && !entrada.value) { entrada.value = `Aprovei a etapa ${c.nome}. Pode seguir com ${c.libera_nome}.`; crescer(); entrada.focus(); }
          op.aoMudarPipeline && op.aoMudarPipeline();
          await buscarCartao();
        } catch (e) {
          st.cartaoErro = (e.status === 409 ? 'O portão recusou: ' : '') + e.message;
          pintarCartao();
        }
        return;
      }
      if ((b = sobre(ev, '[data-confirma]'))) {
        const caixa = b.closest('.cv-msg');
        const i = [...notasEl.children].indexOf(caixa);
        if (i >= 0) st.notas.splice(i, 1);
        if (b.dataset.confirma === 'limpar') {
          try {
            await api.post(`/api/conversas/${encodeURIComponent(st.cid)}/limpar`);
            st.mensagens = []; st.notas = []; st.falha = null; st.enviados = [];
            pintarTudo(); nota('Conversa limpa. A próxima mensagem começa do zero.');
          } catch (e) { nota(e.message, true); }
        } else pintarNotas();
        entrada.focus();
        return;
      }
      if ((b = sobre(ev, '[data-falha-acao]'))) { const a = (op.acoesFalha || [])[+b.dataset.falhaAcao]; a && a.acao(); return; }
      if (sobre(ev, '[data-tentar]')) {
        const f = st.falha; st.falha = null; pintarNotas();
        if (f) { if (f.anexos && f.anexos.length) st.anexos = f.anexos.map((c) => ({ nome: base(c), caminho: c })); enviar(f.texto || ''); }
        return;
      }
      if ((b = sobre(ev, '[data-diz]'))) { entrada.value = b.dataset.diz; enviar(); return; }
      if (sobre(ev, '.cv-enviar')) { enviar(); return; }
      if (sobre(ev, '.cv-parar')) { parar(); return; }
      if (sobre(ev, '.cv-anexar')) { $('.cv-arquivo').click(); return; }
    });

    // imagem de anexo que o app não serve (fora das pastas permitidas) vira chip
    el.addEventListener('error', (ev) => {
      const img = ev.target;
      if (img && img.tagName === 'IMG' && img.dataset.caminho) {
        const c = img.dataset.caminho;
        const chip = document.createElement('span');
        chip.className = 'cv-chip'; chip.title = c;
        chip.innerHTML = `${ICONE.imagem}<span>${esc(base(c))}</span>`;
        (img.closest('.cv-mini') || img).replaceWith(chip);
      }
    }, true);

    // redesenha só a mensagem (ou o passo vivo) dona de um detalhe aberto
    function redesenharDono(chave) {
      if (chave.startsWith('v')) {
        const i = parseInt(chave.slice(1), 10);
        const no = vivoNos.get(i); if (no) no.dataset.ass = '';
        pintarVivo();
      } else {
        const i = parseInt(chave.slice(1), 10);
        const velho = msgsEl.querySelector(`[data-msg="${i}"]`);
        if (velho && st.mensagens[i]) {
          const t = document.createElement('div'); t.innerHTML = htmlMensagem(st.mensagens[i], i, ui, api);
          const novo = t.firstElementChild;
          velho.replaceWith(novo);
          hidratar(novo);
        } else pintarMensagens();
      }
      const b = el.querySelector(`[data-abrir="${typeof CSS !== 'undefined' && CSS.escape ? CSS.escape(chave) : chave}"]`);
      if (b && document.activeElement !== b) b.focus({ preventScroll: true });
    }

    $('.cv-arquivo').addEventListener('change', (ev) => { anexar(ev.target.files); ev.target.value = ''; });

    entrada.addEventListener('input', () => { crescer(); st.volta = -1; abrirMenu(); });
    entrada.addEventListener('click', () => { if (st.menu) abrirMenu(); });
    entrada.addEventListener('paste', (ev) => {
      const fs = ev.clipboardData && ev.clipboardData.files;
      if (fs && fs.length) { ev.preventDefault(); anexar(fs); }
    });
    entrada.addEventListener('keydown', (ev) => {
      const m = st.menu;
      if (m && m.itens.length) {
        if (ev.key === 'ArrowDown') { ev.preventDefault(); m.sel = (m.sel + 1) % m.itens.length; pintarMenu(); return; }
        if (ev.key === 'ArrowUp') { ev.preventDefault(); m.sel = (m.sel - 1 + m.itens.length) % m.itens.length; pintarMenu(); return; }
        if ((ev.key === 'Enter' && !ev.shiftKey) || ev.key === 'Tab') { ev.preventDefault(); escolherMenu(m.sel); return; }
      }
      if (ev.key === 'Escape') {
        if (st.menu) { ev.preventDefault(); fecharMenu(); return; }
        if (S && S.viva) { ev.preventDefault(); parar(); return; }
      }
      if (ev.key === 'Enter' && !ev.shiftKey && !ev.isComposing) { ev.preventDefault(); enviar(); return; }
      // ↑ com o campo vazio (ou cursor no começo) traz a última mensagem; repetir anda para trás
      if (ev.key === 'ArrowUp' && st.enviados.length && (!entrada.value || (st.volta >= 0 && entrada.selectionStart === 0))) {
        ev.preventDefault();
        st.volta = Math.min(st.enviados.length - 1, st.volta + 1);
        entrada.value = st.enviados[st.enviados.length - 1 - st.volta]; crescer();
        entrada.setSelectionRange(0, 0);
        return;
      }
      if (ev.key === 'ArrowDown' && st.volta >= 0 && entrada.selectionStart === entrada.value.length) {
        ev.preventDefault();
        st.volta -= 1;
        entrada.value = st.volta >= 0 ? st.enviados[st.enviados.length - 1 - st.volta] : ''; crescer();
      }
    });
    // Esc também fora do campo, em qualquer lugar da conversa
    el.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape' && ev.target !== entrada && ev.target !== tituloEl && !histEl.contains(ev.target) && S && S.viva && !lbAberto()) { ev.preventDefault(); parar(); }
    });

    // arrastar e soltar
    let arrasto = 0;
    const temArquivo = (ev) => ev.dataTransfer && [...(ev.dataTransfer.types || [])].includes('Files');
    el.addEventListener('dragenter', (ev) => { if (!temArquivo(ev)) return; ev.preventDefault(); arrasto += 1; $('.cv-soltar').hidden = false; });
    el.addEventListener('dragover', (ev) => { if (!temArquivo(ev)) return; ev.preventDefault(); ev.dataTransfer.dropEffect = 'copy'; });
    el.addEventListener('dragleave', () => { arrasto = Math.max(0, arrasto - 1); if (!arrasto) $('.cv-soltar').hidden = true; });
    el.addEventListener('drop', (ev) => {
      if (!temArquivo(ev)) return;
      ev.preventDefault(); arrasto = 0; $('.cv-soltar').hidden = true;
      anexar(ev.dataTransfer.files);
    });

    st.relogio = setInterval(() => { if (!el.isConnected) { desmontar(); return; } if (S && S.viva) relogio(); }, 1000);

    function desmontar() {
      st.montado = false;
      document.removeEventListener('keydown', teclaLb);
      if (visivel) visivel.disconnect();
      if (st.desligar) st.desligar();
      clearInterval(st.relogio);
    }

    carregar();
    carregarIA();
    setTimeout(() => entrada.focus({ preventScroll: true }), 0);

    return {
      desmontar,
      enviar: (t) => enviar(t),
      comando,
      foco: () => entrada.focus(),
      abrirConversa: (cid) => abrirConversa(cid),
      historico: () => abrirHist(),
      get conversa() { return st.cid; },
      get meta() { return st.meta; },
      recarregar,
    };
  }

  const exportado = {
    montarConversa,
    // peças puras, para os testes (testes/js/conversa-ui.test.js)
    _interno: { esc, md, inline, rotuloAcao, rotuloComando, lerGatilho, filtrarComandos, filtrarSkills, aplicarArquivo,
                Fila, tarefasAtuais, skillEmUso, resumoCusto, partesUsuario, sequenciaDa, duracao, COMANDOS,
                htmlMensagem, htmlPasso, SESSOES, enviarNaSessao, sessao,
                htmlMidias, dedupeMidias, proporcao, mensagemTimeline, uiMidia,
                tecnicoDaSkill, nomeSkill, quandoRelativo },
  };
  raizGlobal.montarConversa = montarConversa;
  raizGlobal.ConversaUI = exportado;
  if (typeof module !== 'undefined' && module.exports) module.exports = exportado;
})(typeof window !== 'undefined' ? window : globalThis);
