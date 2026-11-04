---
name: plataforma-ia-higgsfield
description: Monta uma plataforma web própria de geração de imagem e vídeo com IA, com a marca do aluno, usando a API do Higgsfield (Kling, Seedance, Soul e os outros modelos da conta) e o ChatGPT ou o Claude para desenhar e programar — visual estilo Apple, modo claro e escuro, seletor de modelos, status do job, galeria e histórico. Sem assinatura: paga só o que gerar na conta do Higgsfield. Regra de segurança da chave embutida: a chave NUNCA vai no código nem no chat (no chat, `SUA_CHAVE_AQUI`); a plataforma pede a chave numa tela de configuração e guarda só no navegador, ou num servidor intermediário que lê de variável de ambiente. Use quando pedirem "minha plataforma de IA", "plataforma própria com a API do Higgsfield", "site de gerar imagem e vídeo com a minha marca", "monta o prompt de design", "cria a plataforma com o setup prompt do Higgsfield", "deu erro de CORS na minha plataforma", "como uso a chave do Higgsfield sem expor", ou colarem o setup prompt do Higgsfield. NÃO é para gerar b-roll de um job (use editor-automatico-de-broll) nem para vender a plataforma como SaaS (avise que isso exige servidor, contas e pagamentos).
---

# Plataforma de IA própria com a API do Higgsfield

O aluno sai com uma plataforma web de geração de imagem e vídeo **com a marca
dele**, que roda no navegador e cobra só o que ele gerar na conta do Higgsfield.
Dois caminhos, o mesmo resultado:

| Caminho | Quem programa | Quando |
|---|---|---|
| **A. Chat** (ChatGPT ou Claude no navegador) | o chat, a partir do prompt de design | o aluno quer fazer sozinho, copiando e colando |
| **B. Aqui** (Claude Code / Conversa do Editor Automático) | você, escrevendo os arquivos numa pasta | o aluno pede "monta pra mim" |

## Regra de segurança da chave (vale para tudo nesta skill)

1. **A chave nunca entra no código** — nem como exemplo preenchido, nem em comentário, nem em `.env` que vá junto.
2. **A chave nunca entra no chat.** No chat, no prompt e em qualquer arquivo de exemplo: `SUA_CHAVE_AQUI`. A chave real só é digitada na tela de configuração da plataforma, no computador do aluno.
3. Se o aluno **colar a chave** na conversa ou mostrar num print: avise na hora que ela está exposta e que o certo é **apagar essa chave no Higgsfield (API keys) e criar outra**. Não repita a chave, não grave em arquivo, não use.
4. Na plataforma: a chave fica **só no navegador** (`localStorage`), com aviso "Sua chave fica salva só neste navegador", botões **Trocar chave** e **Apagar chave**, e só os **4 últimos caracteres** visíveis depois de salva.
5. Se a API recusar chamada direta do navegador (CORS) ou exigir servidor: um **servidor intermediário pequeno que lê a chave de variável de ambiente** (`references/proxy-modelo.md`). Nunca "resolver" o CORS colocando a chave no código.
6. Aviso no topo do código e no README: não publicar com a chave, não subir a chave para o GitHub, não compartilhar print com a chave.

## Passo 1 — Criar a chave de API (o aluno faz)

- **open.higgsfield.ai** › login › **API keys** › **Create API key** (nome, ex.: `minha-plataforma`).
- Abre a janela **Save your API key** com **a chave** (botão Copy) e o **setup prompt** (a documentação da API em texto, feita para colar numa IA).
- **A chave só aparece uma vez**: guardar num gerenciador de senhas. Perdeu? Apaga a antiga e cria outra.
- Em **Explore models** estão os modelos que a plataforma vai poder usar; preços em **Pricing**.

Você não precisa (nem deve) ver a chave. Precisa só do **setup prompt** — ele não é segredo.

## Passo 2 — Preencher o prompt de design

O prompt completo está em `references/prompt-de-design.md`. Pergunte ao aluno, numa mensagem só:

- **nome** da plataforma;
- **cor de destaque** (hex);
- **tom** (premium, minimalista, criativo...);
- quais **modelos** quer no seletor (padrão: os de imagem e vídeo que o setup prompt listar, incluindo Kling, Seedance e Soul);
- se vai usar **sozinho** (local) ou **publicar** (muda a recomendação de servidor intermediário).

Preencha os colchetes e entregue o prompt pronto para copiar.

## Passo 3A — Pelo chat (ChatGPT ou Claude)

Ordem de colagem num chat **novo**:
1. o **setup prompt** do Higgsfield;
2. o **prompt de design** preenchido;
3. no lugar de qualquer chave: `SUA_CHAVE_AQUI`.

O chat devolve a estrutura e depois o código. Oriente: salvar os arquivos numa pasta (ex.: `minha-plataforma/`) e abrir o `index.html`.

## Passo 3B — Aqui, escrevendo os arquivos

Peça ao aluno para **colar o setup prompt** (sem a chave) e a pasta de destino. Então:

1. Mostre em poucas linhas a estrutura que vai criar e espere o ok.
2. Escreva `index.html` (ou `index.html` + `app.js` + `estilo.css`) seguindo o prompt de design, com:
   - lista de modelos **numa constante de configuração no topo** (fácil de acrescentar), separada em Imagem e Vídeo, com as opções de cada um (proporção, duração, imagem de referência) tiradas do setup prompt;
   - status do job (na fila, gerando, pronto, erro) em português, com poll pelo endpoint de status que a documentação indicar;
   - galeria, player de vídeo, baixar / copiar prompt / gerar de novo;
   - histórico no navegador com miniatura, prompt, modelo, data, busca e limpar;
   - tela de configuração da chave (regra de segurança acima);
   - modo claro/escuro respeitando o sistema na 1ª visita e lembrando a escolha;
   - custo estimado antes de gerar, se a API informar.
3. **Confira antes de entregar:** `grep -rn "SUA_CHAVE_AQUI\|api[_-]\?key\s*[:=]\s*['\"][A-Za-z0-9]" <pasta>` — nenhuma chave real escrita; abra o `index.html` no navegador e verifique que a tela de chave aparece na primeira abertura.
4. Não gere nada com a conta do aluno para "testar" sem pedir — gerar gasta crédito dele.

## Passo 4 — Abrir e testar (o aluno faz)

- Abrir o `index.html` → a plataforma pede a chave → colar ali.
- **Primeiro teste com imagem** (barato), depois vídeo. Vídeo demora mais: esperar o "pronto" no histórico.
- **Erro de CORS ou de conexão** ("blocked by CORS policy", "Failed to fetch"): a API não aceita chamada direta do navegador. Solução: o servidor intermediário de `references/proxy-modelo.md` — a chave vai numa variável de ambiente no computador do aluno, a página chama o servidor local.

## Passo 5 — O pulo do gato: a mesma conta no Editor Automático

A conta do Higgsfield que paga a plataforma também gera os b-rolls da edição:

- **Editor Automático › Contas › Higgsfield**: entrar com a conta (login, sem copiar chave).
- Com o Premiere aberto e o Tools PRO conectado, pedir na Conversa:

```text
Gere os B-rolls de [PASTA DO JOB] casando com o que é dito na fala, anime no Kling 3.0 Turbo em 9:16 e coloque na V2 da timeline do Premiere, cada um no ponto da fala. Me peça aprovação antes de gastar crédito.
```

## Erros comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| "Perdi a chave" | ela só aparece uma vez | apagar a antiga em API keys e criar outra |
| Chave colada no código, no chat ou num print | exposição | apagar essa chave no Higgsfield na hora e criar nova; tirar do código |
| Gera mas não mostra o vídeo | vídeo leva mais tempo | esperar o status "pronto"; conferir que o poll continua |
| Imagem baixada pequena (~600 px) | pegou a miniatura | usar o campo do resultado em resolução cheia (`result_url`), não o `min_result_url` |
| CORS / Failed to fetch | API sem chamada direta do navegador | servidor intermediário com a chave em variável de ambiente |
| "Quero vender a plataforma" | aí é um SaaS | precisa de servidor, contas de usuário, pagamentos, armazenamento e a chave do lado do servidor — fora do escopo; para uso pessoal, o que foi montado basta |

## Resumo para o aluno

1. open.higgsfield.ai › API keys › Create API key.
2. Copie a chave (guarde, só aparece uma vez) e o setup prompt.
3. Chat novo: setup prompt + prompt de design, com `SUA_CHAVE_AQUI` no lugar da chave.
4. Abra o `index.html` e cole a chave na tela de configuração.
5. Editor Automático › Contas › Higgsfield, e peça os b-rolls na Conversa.
