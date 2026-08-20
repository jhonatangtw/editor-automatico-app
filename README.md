# Editor Automático

App de mesa que edita criativo de b-roll do começo ao fim: decupa a fala, planeja
onde entra cada insert, gera o visual, **monta na sua timeline do Premiere** e
confere o resultado antes de liberar a exportação.

Roda na sua máquina, com as suas contas. O material não sobe para lugar nenhum
para ser transcrito — o Whisper roda local.

## Instalar

**macOS** — [Apple Silicon (M1/M2/M3…)](https://github.com/jhonatangtw/editor-automatico-app/releases/latest/download/EditorAutomatico.dmg) · [Intel](https://github.com/jhonatangtw/editor-automatico-app/releases/latest/download/EditorAutomatico-Intel.dmg)

> Em dúvida: menu  → Sobre este Mac. Se disser **Chip Apple**, é o primeiro;
> se disser **Processador Intel**, é o segundo. O app baixa o certo sozinho nas
> atualizações seguintes.

1. Abra o `.dmg` e arraste o **Editor Automático** para a pasta Aplicativos.
2. Na primeira abertura: **botão direito no app → Abrir → Abrir**. O app não é
   assinado com Developer ID, então o macOS avisa uma vez.

**Windows** — [baixar o instalador](https://github.com/jhonatangtw/editor-automatico-app/releases/latest/download/EditorAutomatico-Instalador.exe)

1. Rode o instalador. Ele **não pede senha de administrador** — instala em
   `%LOCALAPPDATA%` e cria atalho no menu Iniciar e na área de trabalho.
2. Na primeira execução o SmartScreen avisa (o instalador não é assinado):
   **Mais informações → Executar assim mesmo**.

Atualizações aparecem sozinhas dentro do app — pill **⬆ Atualizar** no rodapé da
barra lateral, e cada sistema baixa o seu instalador.

## O plugin do Premiere

O app fala com o Premiere pela extensão **Editor Black Belt Tools PRO**. Sem ela
o app planeja, gera e confere arquivo, mas não escreve na timeline.

Instale por dentro do app: aba **Ambiente → Instalar plugin no Premiere**. Ou
baixe direto: [EditorBlackBeltToolsPRO-Instalador.zip](https://github.com/jhonatangtw/editor-black-belt-tools-pro/releases/latest/download/EditorBlackBeltToolsPRO-Instalador.zip).

Depois de instalar, reabra o Premiere e deixe o painel aberto em
**Janela → Extensões → Tools PRO**: a ponte só existe com o painel aberto.

## As 12 etapas

O app é uma máquina de estados. Cada etapa só roda com a anterior concluída, e
as que gastam crédito exigem aprovação escrita — concluído pode ser automático,
aprovado nunca é.

| # | Etapa | Gasta |
|---|---|---|
| 1 | Análise inicial | |
| 2 | Verificação da copy contra a fala | |
| 3 | Marcação da timeline | |
| 4 | **Aprovação do planejamento** (portão) | |
| 5 | Criação dos avatares | crédito |
| 6 | Imagens de b-roll | crédito |
| 7 | Aprovação das imagens (uma a uma) | |
| 8 | Animação dos b-rolls | crédito |
| 9 | Aprovação dos vídeos (um a um) | |
| 10 | Letterings, voz e legendas | crédito |
| 11 | **Montagem no Premiere** | |
| 12 | **Controle de qualidade** (portão) | |

## Qual IA conduz a conversa

O seletor fica embaixo do campo de mensagem, colado no compositor. Cada mensagem
vai para a IA marcada, e a escolha fica guardada entre sessões.

| | Como entra | O que ela alcança |
|---|---|---|
| **Claude** | sessão do Claude Code (assinatura) ou chave de API | pipeline completo, **mais** as skills e ferramentas que você já tem no Claude Code |
| **ChatGPT** | API oficial da OpenAI | as ferramentas do app, por function calling — sem as skills do Claude Code |

Os dois passam pelos **mesmos portões**: se a IA tentar gerar b-roll antes da
aprovação do planejamento, recebe a recusa e tem que explicar. Não existe
caminho por fora do pipeline para nenhuma das duas.

**Histórico por conversa e por provedor.** A tela mostra tudo o que foi
conversado, com o nome de quem respondeu em cada resposta; mas cada IA só recebe
de volta o que foi trocado com ela. Misturar faria uma responder sobre o que a
outra fez como se tivesse feito — e ferramenta já executada não volta atrás.

### Configurar o ChatGPT

A chave nunca fica no código nem no front-end. O app procura nesta ordem:

1. **variável de ambiente** `OPENAI_API_KEY` — o jeito canônico;
2. **`~/.editorblackbelt/.env`** (permissão 0600) — copie o `.env.example`;
3. **shell de login**, perguntado na hora;
4. **cofre do sistema**, se você colou a chave pelo próprio app.

```bash
cp .env.example ~/.editorblackbelt/.env
chmod 600 ~/.editorblackbelt/.env
# edite e preencha OPENAI_API_KEY
```

⚠️ O passo 2 existe por um motivo prático: **um `.app` aberto pelo Finder não
herda o ambiente do shell**. `export OPENAI_API_KEY` no `.zshrc` é invisível
para ele — sem o arquivo, "use variável de ambiente" só funcionaria para quem
abre o app pelo terminal.

Pelo app: clique em **ChatGPT** no seletor. Sem chave, ele abre o pedido, testa
a credencial antes de aceitar e grava no `.env` acima.

Opcionais: `OPENAI_MODEL` (se o modelo não existir na sua conta, o app procura o
melhor equivalente e avisa qual usou) e `OPENAI_BASE_URL` (Azure ou proxy).

### Por que API e não CLI

O CLI da OpenAI é um agente de código, com autenticação e formato de saída
próprios — seria uma segunda superfície de integração para manter, sem contrato
estável, e ainda precisaria da nossa camada de ferramentas por outro caminho. A
API é versionada, documentada, faz streaming e function calling, e não depende
do site do ChatGPT. Está escrita em `urllib`, sem SDK: o app empacota com
PyInstaller e cada dependência a mais é uma chance a mais de quebrar no pacote
do aluno.

O Claude é o oposto e por isso continua como está: pela assinatura ele roda o
**Claude Code de verdade**, com as skills do usuário, e recebe as ferramentas do
app por MCP. Trocar isso por API seria perder o que ele tem de melhor.

## Para quem vai mexer no código

- `LEIA-ME.md` — arquitetura, decisões e as armadilhas que já custaram caro.
- `MANUAL.md` — o manual do usuário.
- A **regra de edição** (punch, cadência, marcador) mora na skill
  `editor-automatico-de-broll`, não aqui. `nucleo/skill.py` importa a de lá.

```bash
python3 -m venv .venv && .venv/bin/pip install pywebview keyring
.venv/bin/python app.py
```

Publicar uma versão: edite `version.json`, commite e rode `./publicar.sh` — ele
marca a tag e o GitHub Actions constrói os dois instaladores (o `.exe` só nasce
numa máquina Windows; o PyInstaller não faz build cruzado).
