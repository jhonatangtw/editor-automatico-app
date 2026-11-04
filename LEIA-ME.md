# Editor Automático — app

App de mesa da automação de b-roll. Roda na máquina do aluno, com as contas dele.
Separado do HW Creative Studio de propósito.

**A regra de edição não mora aqui.** `nucleo/skill.py` importa o `compilar.py` da skill
`editor-automatico-de-broll` — punch, cadência, marcador e validação têm UMA implementação,
e é a da skill. O app é a interface; a skill é a regra. Mexer na regra é mexer lá.

## Rodar

```bash
# durante o desenvolvimento
.venv/bin/python app.py

# ou duplo clique em "Abrir Editor Automático.command"
```

## Empacotar

```bash
./instalador/construir.sh     # → instalador/saida/*.pkg e *.dmg
```

## Estrutura

```
app.py                 janela pywebview + servidor local
nucleo/
  conta.py             login Tools PRO — divide a sessão com o painel do Premiere
  chaves.py            cofre: Chaveiro / Credential Manager
  claude.py            conta Anthropic — OAuth ou chave, com detecção de shadowing
  servicos.py          os 5 serviços: teste de conexão e saldo
  projetos.py          projeto em disco, ffprobe, troca atômica
  decupar.py           Whisper com timestamp por palavra
  skill.py             ponte com a skill — importa a regra, não copia
  pipeline.py          motor das 12 etapas — as travas de ordem e aprovação
  etapas.py            executores locais (análise, copy, marcação, plano)
  gerar.py             Higgsfield — imagem, b-roll, animação (motor escolhível)
  voz.py               ElevenLabs — ÚNICA fonte de voz do app
  conversa.py          o chat: Claude com ferramentas, sem furar o portão
  ambiente.py          confere e INSTALA ffmpeg, whisper, CLIs
web/                   interface, sem build e sem npm
instalador/            .pkg + .dmg
```

## Travas embutidas — cada uma veio de um erro real

**User-Agent no login.** O Worker está atrás do Cloudflare, que recusa o
`Python-urllib/3.x` com **erro 1010** — a resposta nem é JSON, é página de bloqueio.
O painel do Premiere nunca sofreu disso porque `fetch()` dentro do CEP já manda
User-Agent de navegador. Sem esta linha, **nenhum aluno consegue entrar**.

**Não fazer login próprio se já existe sessão.** O servidor conta máquinas por uma
impressão **aleatória** que o painel guarda em `~/.editorblackbelt/sessao.json` — não é
fingerprint de hardware, o app não consegue recalcular. O plano dá 2 computadores.
Login próprio = o mesmo computador vira a 2ª máquina e o aluno queima a vaga parado.

**`sys.exit` da skill isolado.** `carregar_estilo()` chama `sys.exit()` quando o estilo
não existe — educado num CLI, fatal num servidor. Todo ponto de entrada captura SystemExit.

**Token na URL do app.** Qualquer página aberta no navegador da máquina alcança
`127.0.0.1`. Sem o token, um site numa aba conseguiria listar e apagar projetos.

**HeyGen já nasce no v3.** O `/v2/user/remaining_quota` sai do ar em **31/10/2026** —
a própria API avisa no corpo.

**`ANTHROPIC_API_KEY` exportada silencia o perfil OAuth.** A ordem é env var → auth token
→ perfil. O app reporta qual credencial **de fato venceu**, não a que a pessoa configurou.

## Verificado ao vivo

- Login no Worker de produção (depois do conserto do User-Agent)
- Higgsfield `account status --json` → plano ultra, 39.060 créditos
- HeyGen `/v3/users/me` → e-mail + carteira
- Anthropic `/v1/models` → 401 com credencial inválida (caminho certo)
- Projeto real: ffprobe leu 1280×720 / 8,7s / 30fps; portão bloqueou por insert sem mídia
- Rota sem token → 403

## Sem teste com chave real

ElevenLabs e MiniMax. Escritos pela documentação. O primeiro "Testar conexão" fecha a conta;
404 ali significa endereço na `TABELA` desatualizado — é uma linha.


## O chat não fura o portão

`conversa.py` dá ao Claude ferramentas que chamam as MESMAS funções dos botões.
Se ele tentar gerar b-roll antes da aprovação do planejamento, recebe o mesmo
`Bloqueado` — e explica ao usuário o que falta em vez de tentar outro caminho.

O contrário também vale: **aprovar por escrito é aprovação de verdade.** "pode gerar"
vira registro em `aprovacoes` com nome, hora e a frase exata que autorizou.

⚠️ **Segredo não entra no chat.** As chaves ficam no cofre do sistema e nunca são
passadas ao modelo — o histórico da conversa fica em disco, dentro do projeto, e
projeto vai parar no Drive.

## Etapa 11 — montagem no Premiere (`nucleo/montagem.py`)

Escreve na **sequência ativa** do projeto que o usuário já tem aberto. Não cria
projeto nem sequência: o job tem que nascer dentro do material dele, com as
trilhas dele, para ser ajustável à mão depois.

Cinco passos separados — preparar, importar, posicionar, punch, marcadores.
Uma chamada só ficaria minutos muda e, falhando no meio, ninguém saberia até
onde tinha ido.

**Nada é dado como feito sem reler.** O Premiere tem falha silenciosa demais
para acreditar em retorno de função: `addVideoEffect` não adiciona e não
reclama, `deleteSequence` do projectItem não apaga, e transform pelo nome em
inglês num Premiere PT-BR devolve sucesso sem mudar nada. Por isso:

- efeito por **`matchName`** (`AE.ADBE Motion`), nunca por nome de menu;
- a escala é procurada por nome em PT **e** EN e, se cair no índice, o relatório
  DIZ que caiu — em vez de afirmar um punch que ninguém conferiu;
- cada clipe posto é relido (entra/sai/duração) e a diferença entre o pedido e o
  que coube vira alerta.

**Punch sem razorar.** As janelas viram keyframe de escala com um quadro de
antecedência segurando o valor anterior — a virada é um snap, igual ao corte
seco, sem cortar o clipe e sem depender de conversão de timecode (que é onde
mora o bug de drop-frame).

⚠️ **Keyframe de clipe é medido no tempo da FONTE**, não da sequência:
`inPoint + (tempo_na_sequência − start)`.

⚠️ **B-roll entra só na trilha de vídeo.** `overwriteClip` numa videoTrack deixa
o áudio do b-roll de fora — que é o que se quer: áudio de IA por cima da voz do
avatar não se separa depois.

⚠️ Só marcador com o selo `EA:` no comentário é apagado ao remontar. Marcador do
editor não se toca.

**O plano passa a apontar a mídia.** A montagem grava `midia` em cada beat
(caminho RELATIVO à pasta do projeto). Sem isso o plano mentia: o vídeo existia
no disco e o beat continuava "sem mídia". Isso exigiu passar o `_caminho` para
`skill.compilar` — a régua da skill resolve b-roll relativo à pasta do plano e,
sem ele, o primeiro beat com mídia derrubava a compilação com `KeyError`.

## Etapa 12 — QC (`nucleo/qc.py`)

Duas provas, porque uma não cobre a outra: a **timeline** lida de volta do
Premiere responde "montou o que foi planejado?"; o **arquivo exportado** responde
"o que saiu presta?". A timeline pode estar perfeita e o export sair de outra
sequência; o arquivo pode estar lindo e ser o export de ontem.

Pega: insert sem b-roll, cobertura, maior vão, trilha muda, marcador que sumiu,
clipe de apoio fora do plano, formato fora do 9:16, quadro preto, silêncio longo
e duração que não bate. Sai um mosaico de 20 quadros em `saida/qc-mosaico.jpg`.

⚠️ **Áudio que acaba antes do vídeo não vira silêncio detectável** — a trilha
simplesmente termina e o `silencedetect` não tem o que ouvir. Só a comparação de
durações pega, e é erro comum de preset de export.

Roda local e não gasta crédito: QC que custa dinheiro é QC que o aluno pula.

## Atualização do app (`nucleo/atualizacao.py`)

`version.json` diz a versão E o repositório (`repo`, `asset`). O mesmo arquivo é
anexado na Release "latest"; o app compara e oferece.

**O app não se substitui sozinho** — baixa o `.dmg` e abre para o usuário
arrastar. Trocar por baixo um bundle que está rodando é onde nasce o app que não
abre mais, e o custo de errar isso é suporte, não conveniência.

Falha de rede devolve `{"erro": ...}` e nunca levanta: sem internet o app abre
igual, só não mostra o aviso.

Publicar: edite o `version.json` e rode `./publicar.sh` (empacota, cria a
Release com os dois arquivos e confere o que o app vai enxergar).

## Plugin do Premiere (`nucleo/plugin.py`)

O Tools PRO é a ponte; sem ele as etapas 11 e 12 caem em "abra o painel". A aba
**Ambiente** mostra a versão instalada contra a publicada e instala com um
botão: baixa o pacote OFFLINE oficial da Release, descompacta e entrega ao
`INSTALAR-MAC.command` **num Terminal de verdade** — ele liga o PlayerDebugMode
e instala fontes, e disparado por Popen mudo um passo falha enquanto o app
relata sucesso.

## Windows (20/08/2026)

O app não era só-Mac por escolha: cada pedaço tinha aprendido o Mac por conta —
`pgrep` para achar o Premiere, `osascript` para abrir Terminal, `brew` para
instalar, `/Applications` para procurar programa. `nucleo/so.py` junta as
diferenças num lugar só; o resto do código não pergunta mais qual é o sistema.

⚠️ **CLI de npm no Windows é `.cmd`.** `subprocess.run(["higgsfield", ...])`
levanta `FileNotFoundError` com o binário instalado e funcionando — o
`CreateProcess` não executa `.cmd` por nome. `so.run`/`so.popen` resolvem o
argv[0] com `shutil.which` (que enxerga o `.cmd` por causa do PATHEXT) antes de
chamar. É por isso que TODA chamada de CLI passa por eles.

⚠️ **`os.path.expandvars` não expande `%VAR%` fora do Windows** — no Mac o
posixpath só entende `$VAR`, então um teste aqui veria o literal `%APPDATA%` e
passaria mentindo. Caminho de Windows se monta com `os.environ`.

⚠️ **PATH no Windows não tem o problema do Mac**: processo aberto pelo Explorer
HERDA o PATH do usuário. O `caminho.py` só acrescenta os cantos do npm e do pip.

⚠️ **`tasklist` filtra por NOME do executável**, não pela linha de comando. Por
isso o padrão do Premiere muda de casa: `Adobe Premiere Pro` no Mac,
`Adobe Premiere Pro.exe` no Windows.

Gerenciador de pacotes: `winget` (vem no Windows 10/11 pela Store). HeyGen CLI e
`ant` ficam marcados como manuais lá — receita que falha é pior do que aviso
honesto.

## Os dois instaladores

| | arquivo | como instala |
|---|---|---|
| macOS | `EditorAutomatico.dmg` | arrastar para Aplicativos |
| macOS | `EditorAutomatico.pkg` | assistente, **sem senha de admin** (domínio do usuário) |
| Windows | `EditorAutomatico-Instalador.exe` | NSIS, `%LOCALAPPDATA%`, **sem admin** |

⚠️ **O PyInstaller não faz build cruzado**: `.exe` só nasce em Windows. Por isso
`publicar.sh` deixou de construir na mesa e passou a marcar a tag —
`.github/workflows/publicar.yml` constrói nos dois runners e anexa os três
arquivos (os dois instaladores + `version.json`) na Release, conferindo no fim
se as URLs de `latest/download` respondem 200.

⚠️ Nenhum dos dois é assinado (sem Developer ID nem certificado Windows):
Gatekeeper e SmartScreen avisam na primeira abertura.
