/* Ponte FALSA para ver a tela sem o app rodando: responde às mesmas rotas que o
   app.py, com dois retratos — "cheio" (tudo conectado) e "vazio" (instalação
   nova). Só para a banca visual; nunca vai no pacote do app.
   Uso: testes/visual/tela.html?cenario=cheio&aba=contas */
(function () {
  const q = new URLSearchParams(location.search);
  const cheio = (q.get('cenario') || 'cheio') === 'cheio';
  const item = (id, nome, para, tem, essencial, extra) =>
    Object.assign({ id, nome, para, tem, essencial, instalavel: !tem, versao: tem ? '1.0' : '' }, extra || {});
  const DADOS = {
    '/api/estado': { conta: { entrou: true, nome: 'Marina Duarte', email: 'marina@estudio.com', adm: false } },
    '/api/servicos': { cofre: 'sistema', servicos: [
      { id: 'claude', titulo: 'Claude', papel: 'decide a edição', modo: 'anthropic', verificado: true, pronto: cheio },
      { id: 'elevenlabs', titulo: 'ElevenLabs', papel: 'voz — única fonte de áudio do app', modo: 'chave', verificado: false, pronto: cheio, fim: cheio ? 'chave …9f2a' : '' },
      { id: 'heygen', titulo: 'HeyGen', papel: 'avatar falante', modo: 'cli', verificado: true, pronto: cheio, conta: cheio ? 'marina@estudio.com' : '', saldo: cheio ? '1.240 créditos' : '', msg: cheio ? '' : 'CLI instalado, sem login.' },
      { id: 'minimax', titulo: 'MiniMax', papel: 'vídeo, imagem e música', modo: 'cli', verificado: true, pronto: false, msg: '' },
      { id: 'higgsfield', titulo: 'Higgsfield', papel: 'b-roll e imagem', modo: 'cli', verificado: true, pronto: cheio, conta: cheio ? 'marina@estudio.com' : '', saldo: cheio ? '820 créditos' : '' },
    ], ferramentas: { whisper: cheio, ffmpeg: cheio, ffprobe: cheio } },
    '/api/claude': cheio
      ? { metodo: 'sessao', rotulo: 'Sessão do Claude Code', conta: 'assinatura Max', conectado: true, msg: '', entrar: false, instalar: false }
      : { metodo: 'sessao', rotulo: 'Sessão do Claude Code', conta: '', conectado: false, msg: 'O Claude Code não está instalado neste computador.', entrar: false, instalar: true },
    '/api/ia': { escolhido: 'claude', env: '~/.editorblackbelt/.env', provedores: [
      { id: 'claude', nome: 'Claude', papel: '', pronto: cheio, origem: 'Sessão do Claude Code' },
      { id: 'chatgpt', nome: 'ChatGPT', papel: '', metodo: 'sessao', pronto: cheio, origem: cheio ? 'assinatura Plus' : '', msg: '' },
    ] },
    '/api/ambiente': { brew: cheio, gerenciador: 'brew', sistema: 'mac', pronto: cheio,
      faltam: cheio ? [] : ['FFmpeg', 'FFprobe', 'Whisper', 'Node.js', 'Claude Code', 'Higgsfield CLI'],
      itens: [
        item('ffmpeg', 'FFmpeg', 'cortar, montar e exportar o vídeo', cheio, true, { versao: cheio ? '7.1' : '' }),
        item('ffprobe', 'FFprobe', 'ler duração, formato e fps do bruto', cheio, true),
        item('whisper', 'Whisper', 'transcrever a fala palavra por palavra, sem subir nada', cheio, true),
        item('node', 'Node.js', 'é por ele que Claude, Higgsfield e MiniMax se instalam', cheio, true, { versao: cheio ? 'v22.9.0' : '' }),
        item('claude', 'Claude Code', 'é quem lê a fala e decide a edição — sem ele o app não pensa', cheio, true, { versao: cheio ? '2.4.1' : '' }),
        item('codex', 'Codex CLI (ChatGPT)', 'falar com o ChatGPT pela SUA assinatura', cheio, false),
        item('higgsfield', 'Higgsfield CLI', 'gerar imagem e b-roll', cheio, true),
        item('premiere', 'Adobe Premiere Pro', 'receber a timeline montada', true, false, { versao: '25.5', instalavel: false }),
      ] },
    '/api/plugin': { instalado: cheio ? '1.9.2' : null, ultima: '1.9.2', tem_nova: false, pagina: 'https://editorblackbelt.com.br' },
    '/api/ponte': { plugin_instalado: cheio, tem_debug: cheio, porta: 8899 },
    '/api/skills': { total: 14, instaladas: cheio ? 14 : 0, faltam: cheio ? [] : ['skill-black-belt', 'hooks-meat-hook'], atualizar: [], do_usuario: cheio ? ['pixar3d'] : [], destino: '~/.claude/skills', destinos: ['~/.claude/skills', '~/.codex/skills'], skills: [] },
    '/api/adobe': { apps: { premiere: cheio, aftereffects: false }, projeto: cheio ? 'AD07_Body.prproj' : '', ativa: cheio ? 'AD07 — corte 1' : '',
      verificado: { ponte: cheio, leu_timeline: cheio, resumo: cheio ? { clipes: 42, marcadores: 18 } : null }, mcp: { ok: cheio, ferramentas: 64 }, utilizavel: cheio },
    '/api/atualizacao': cheio ? { versao: '0.21.0', tem_nova: false } : { versao: '0.21.0', tem_nova: true, ultima: '0.21.1', notas: 'Correções na tela de Contas.', modo: 'codigo' },
    '/api/conversas': { conversas: cheio ? [
      { id: 'a', titulo: 'AD07 — b-roll do body', quando: Date.now() / 1000 - 3600, mensagens: 24, passos: 9, projeto: true },
      { id: 'b', titulo: 'Cortar silêncio da aula 3', quando: Date.now() / 1000 - 90000, mensagens: 8, passos: 3 },
    ] : [] },
    '/api/conversa': { conversa: null, mensagens: [] },
  };
  // Conversa em andamento (0.21.2): ?vivo=etapa|ferramenta|parado
  //   etapa      — o servidor só disse em que ponto está (abrindo o Claude)
  //   ferramenta — já há uma ferramenta rodando
  //   parado     — nada muda: depois de 10 s aparece a dica da permissão
  const vivo = q.get('vivo');
  const TAREFA = {
    estado: 'rodando', erro: null, log: [], cancelavel: true,
    etapa: vivo === 'parado' ? 'esperando o Claude responder' : 'abrindo o Claude Code',
    passos: vivo === 'ferramenta' ? [
      { tipo: 'ferramenta', nome: 'mcp__editor__adobe_estado', resumo: '', estado: 'ok', saida: 'Premiere aberto · AD07_Body.prproj · sequência AD07 — corte 1' },
      { tipo: 'ferramenta', nome: 'mcp__editor__adobe_extendscript', resumo: 'ler marcadores da sequência ativa', estado: 'rodando' },
    ] : [],
  };
  if (vivo) { DADOS['/api/tarefas/t1'] = TAREFA; }

  // Conversa nova (0.22): ?conversa=cheia — histórico com texto e ações
  // intercalados, lista de tarefas em andamento; ?cartao=1 — cartão de
  // aprovação; ?vivo=stream — resposta chegando, com TodoWrite e texto ao vivo.
  const agora = Date.now() / 1000;
  const TAREFAS_TODO = [
    { texto: 'Conferir o Premiere e a timeline', ativo: 'Conferindo o Premiere', estado: 'feito' },
    { texto: 'Marcar os pontos de b-roll', ativo: 'Marcando os pontos de b-roll', estado: 'feito' },
    { texto: 'Orçar as imagens no Higgsfield', ativo: 'Orçando as imagens', estado: 'andamento' },
    { texto: 'Gerar as 9 imagens (depois da sua aprovação)', ativo: 'Gerando as imagens', estado: 'pendente' },
  ];
  const MSGS = [
    { role: 'user', content: 'Analise a timeline do AD07 e prepare os b-rolls', provedor: 'claude' },
    { role: 'assistant', provedor: 'claude', content: '…', passos: [
      { tipo: 'pensando', estado: 'ok', dur: 4.2, texto: 'Primeiro preciso ver o que está aberto no Premiere e ler a decupagem.' },
      { tipo: 'texto', texto: 'Vou conferir o Premiere, ler a decupagem e marcar os pontos de b-roll.' },
      { tipo: 'ferramenta', nome: 'TodoWrite', estado: 'ok', dur: 0.1, entrada: { todos: [] }, tarefas: TAREFAS_TODO },
      { tipo: 'ferramenta', nome: 'mcp__editor__adobe_estado', entrada: {}, estado: 'ok', dur: 0.8,
        resultado: '{"apps":{"premiere":true},"projeto":"AD07_Body.prproj","ativa":"AD07 — corte 1"}' },
      { tipo: 'ferramenta', nome: 'Read', entrada: { file_path: '/Users/marina/Editor Automático/Projetos/ad07/decupagem.md' }, estado: 'ok', dur: 0.1,
        resultado: '# Decupagem AD07\n00:00.0 – Você já acordou com as pernas inchadas?\n00:03.2 – Isso tem nome…' },
      { tipo: 'ferramenta', nome: 'Bash', entrada: { command: 'ffprobe -v error -show_entries format=duration body.mp4', description: 'Mede a duração do body' }, estado: 'ok', dur: 0.3, resultado: 'duration=58.240000' },
      { tipo: 'ferramenta', nome: 'Bash', entrada: { command: 'ffmpeg -i body_v2.mp4 -t 2 teste.mp4', description: 'Corta 2 s para conferir o áudio' }, estado: 'erro', dur: 0.2,
        resultado: 'body_v2.mp4: No such file or directory' },
      { tipo: 'ferramenta', nome: 'mcp__toolspro-pr__pr_marcadores_criar', entrada: { marcadores: new Array(9).fill({}) }, estado: 'ok', dur: 2.1, resultado: '{"criados":9}' },
      { tipo: 'ferramenta', nome: 'mcp__toolspro-pr__pr_timeline_colocar', entrada: { clipes: new Array(12).fill({}) }, estado: 'ok', dur: 3.4, resultado: '{"colocados":12}' },
      { tipo: 'ferramenta', nome: 'mcp__editor__etapa_rodar', entrada: { etapa: 'imagens' }, estado: 'ok', dur: 0.1, recusado: true,
        porque: '“Imagens de B-roll” gasta crédito. Aprove a etapa 4 (Aprovação do planejamento) antes.' },
      { tipo: 'texto', texto: 'Marquei **9 pontos de b-roll** na sequência `AD07 — corte 1`:\n\n- 4 inserts de produto\n- 3 de rotina\n- 2 de dor\n\nPara gerar as imagens preciso da **sua aprovação** do planejamento. O orçamento:\n\n```txt\n9 imagens × 2 cr (nano_banana_pro) = 18 cr\nsaldo atual: 820 cr\n```' },
    ], uso: { duracao_ms: 41200, tokens_entrada: 184000, tokens_saida: 2310, custo_usd: 1.12, turnos: 9 } },
  ];
  if (q.get('conversa') === 'cheia') {
    DADOS['/api/conversa'] = { conversa: 'a', mensagens: MSGS };
    DADOS['/api/conversas/a'] = { conversa: 'a', mensagens: MSGS,
      meta: { id: 'a', titulo: 'AD07 — b-roll do body', projeto: 'ad07', projeto_nome: 'AD07 — Body Produto X' } };
  }
  DADOS['/api/conversas/a/aprovacao'] = { cartao: q.get('cartao') ? {
    projeto: 'ad07', etapa: 'plano', n: 4, nome: 'Aprovação do planejamento', libera: 'imagens', libera_nome: 'Imagens de B-roll',
    custo: { itens: 9, unitario: 2, motor: 'nano_banana_pro', total: 18, saldo: 820 } } : null };
  DADOS['/api/skills'].skills = [
    { nome: 'editor-automatico-de-broll', instalada: true, descricao: 'Edita um criativo UGC 9:16 a partir do bruto de um avatar falante' },
    { nome: 'cortar-aula', instalada: true, descricao: 'Corta silêncios e tempo morto de aulas gravadas' },
    { nome: 'conferir-ads-por-frame', instalada: true, descricao: 'QA de criativos de vídeo já prontos' },
  ];
  if (vivo === 'stream') {
    TAREFA.etapa = 'Claude conectado, pensando';
    TAREFA.passos = [
      { tipo: 'pensando', estado: 'ok', dur: 2.6, texto: '' },
      { tipo: 'ferramenta', nome: 'TodoWrite', estado: 'ok', dur: 0.1, entrada: {}, tarefas: TAREFAS_TODO },
      { tipo: 'ferramenta', nome: 'Bash', entrada: { command: 'higgsfield generate cost --model nano_banana_pro', description: 'Orça as 9 imagens' }, estado: 'ok', dur: 1.8, resultado: '2 credits' },
      { tipo: 'ferramenta', nome: 'mcp__editor__motores_listar', entrada: { tipo: 'imagem' }, estado: 'rodando', inicio: agora - 3 },
      { tipo: 'parcial', texto: 'O motor mais barato que mantém a **consistência do personagem** é o `nano_banana_pro`, a 2 cr por imagem. Com 9 inserts' },
    ];
  }
  // Pasta Documentos: ?pasta=lenta (o macOS perguntando) | negada
  const pasta = q.get('pasta');
  DADOS['/api/pasta'] = pasta === 'negada'
    ? { ok: false, negado: true, pasta: '~/Documents/Editor Automático', erro: 'Operation not permitted' }
    : { ok: true, pasta: '~/Documents/Editor Automático' };

  const real = window.fetch.bind(window);
  window.fetch = async (rota, op) => {
    const caminho = String(rota).split('?')[0];
    // arquivos estáticos do app (o guia) vêm de verdade, da pasta web/
    if (!caminho.startsWith('/api/')) return real('../../web/' + caminho.replace(/^\//, ''), op);
    const post = op && op.method === 'POST';
    let d = DADOS[caminho] || { ok: true };
    if (caminho === '/api/conversas/nova') d = { conversa: 'a' };
    if (post && caminho === '/api/conversa') d = { tarefa: 't1' };
    await new Promise((r) => setTimeout(r, caminho === '/api/pasta' && pasta === 'lenta' ? 60000 : 30));
    return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(d)) };
  };
})();
