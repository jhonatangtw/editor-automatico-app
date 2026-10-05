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
    if (post && caminho === '/api/conversa') d = { tarefa: 't1' };
    await new Promise((r) => setTimeout(r, caminho === '/api/pasta' && pasta === 'lenta' ? 60000 : 30));
    return { ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(d)) };
  };
})();
