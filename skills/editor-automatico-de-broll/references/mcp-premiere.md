# Operar o Premiere e o After Effects

Existem **dois** servidores que falam com o Adobe. Eles não competem — fazem coisas diferentes.

| | **Tools PRO** (`toolspro-pr` / `toolspro-ae`) | **Higgsfield** (`pr_*`, `ae_*`) |
|---|---|---|
| Onde roda | painel dentro do Premiere/AE, em `127.0.0.1` | nuvem |
| Latência | ~3 ms | centenas de ms; já devolveu 502 no meio do trabalho |
| Login | nenhum | conector no claude.ai |
| Marcadores | **lote inteiro numa chamada** | um por chamada |
| Importar / timeline | sim | sim |
| Ler e corrigir a timeline | sim | sim |
| Gerar imagem e vídeo | **não** | **sim — é insubstituível aqui** |

**Quem decide é o usuário — sempre pergunte.** O que muda: o Tools PRO opera a timeline mais rápido e sem cair; o Higgsfield é o único que gera imagem e vídeo. Não é um *ou* outro, é quem faz o quê.

---

## Perguntar qual usar — sempre

**A escolha é do usuário, não sua.** Mas pergunte com informação na mão, não no escuro:

1. Chame `pr_midia_info` (Tools PRO) — respondeu?
2. Chame `get_host_status` (Higgsfield) — veio `ppro: true`?
3. **Pergunte**, dizendo quais estão no ar e o que muda entre eles.
4. Se nenhum responder, **avise e pare.** Nunca editar o `.prproj` direto — ver `armadilhas.md`.

O que a pergunta precisa deixar claro: **o B-roll sai do Higgsfield de qualquer jeito.** A escolha é só sobre quem opera a timeline. Gerar no Higgsfield e montar no Tools PRO é o arranjo mais comum.

Depois de escolhido, **não trocar no meio** sem avisar — os nomes de ferramenta são diferentes e o usuário perde o rastro do que rodou onde.

---

## Ligar o Tools PRO

No Premiere: painel **Editor Black Belt Tools PRO** → rodapé → **Conectar IA** → **Ligar**. Copiar o comando e colar no terminal, **uma vez só** — o token não vence e sobrevive a fechar o app.

```
claude mcp add --transport http toolspro-pr http://127.0.0.1:7842/mcp --header "Authorization: Bearer <token>"
```

O After Effects usa a porta **7843** e o nome `toolspro-ae`. São dois registros separados de propósito: assim "organiza o projeto do AE" vai para o AE.

Depois de registrar, **reinicie o Claude Code** — servidores MCP carregam no início da sessão.

> Se aparecer `invalid_request: redirect_uri`, isso é do Higgsfield, não daqui. O Tools PRO não tem OAuth: não há para onde redirecionar.

---

## As ferramentas que a automação usa

**Ler antes de escrever** — sempre:

| | |
|---|---|
| `pr_midia_info` | projeto, sequência ativa, quantas trilhas |
| `pr_midia_listar` | nome exato e bin de cada item |
| `pr_marcadores_info` | nome, duração, quantos marcadores |
| `pr_autoclip_info` | marcadores **com contagem por cor** |

**Escrever:**

| | |
|---|---|
| `pr_midia_importar` | arquivos em lote, cria o bin |
| `pr_timeline_colocar` | clipes em lote, com recorte de entrada/saída |
| `pr_marcadores_criar` | marcadores em lote |
| `pr_zoom_aplicar` | punch-in nos clipes **selecionados** |
| `pr_titulos_inserir` | `.mogrt` na timeline com o texto trocado |

**Corrigir o que já está na timeline:**

| | |
|---|---|
| `pr_timeline_listar` | **o que existe em cada trilha**, de vídeo e de áudio |
| `pr_timeline_remover` | por trilha, nome ou janela de tempo |
| `pr_timeline_mudo` | silencia trilha inteira, e desfaz |

No After Effects: `ae_legendas_importar` monta a legenda a partir do `.srt`, com karaokê opcional. Cores em `[R,G,B]` de **0 a 1**, não hexadecimal.

---

## O B-roll entra com áudio — sempre tire

`pr_timeline_colocar` traz o áudio nativo do clipe para a trilha de áudio correspondente. Num criativo isso briga com a voz do avatar.

```
pr_timeline_colocar  →  {"colocados": 2}          parece pronto
pr_timeline_listar   →  A3: 29.52–33.52 B1_guardaroupa.mp4   ← estava lá
pr_timeline_remover  →  {"sequencia":"...", "tipo":"audio", "trilha":2}
```

Isso aconteceu de verdade: dois b-rolls foram colocados, a ferramenta respondeu `colocados: 2`, e o áudio veio junto sem ninguém notar. Os b-rolls do fluxo antigo, na mesma timeline, não tinham áudio nenhum — o novo era o único errado.

---

## Ler de volta é obrigatório, não zelo extra

**Nunca reportar uma edição como pronta sem `pr_timeline_listar`.** Retorno de sucesso diz que a chamada não deu erro — não que o resultado está certo.

Foi assim que passaram, nesta skill: vídeo inteiro magenta, efeito vazando para todos os frames, legenda duplicada, e o áudio de b-roll acima. Todos invisíveis nos retornos de sucesso.

O `pr_timeline_remover` deixa o buraco por padrão (`ondular: false`). Fechar o buraco numa timeline já sincronizada com áudio desalinha tudo que vem depois — *ripple* tem que ser pedido, não presumido.

---

## Duas travas que existem por acidente real

### Declare a sequência

`pr_marcadores_apagar` **exige** o campo `sequencia`, e `pr_timeline_colocar` / `pr_autoclip` aceitam. Se o nome não bater com a sequência ativa, a operação morre sem tocar em nada.

Isso existe porque **17 marcadores de um job real foram apagados** — a ferramenta agiu na sequência ativa, que não era a que se pensava: o usuário tinha clicado noutra aba entre a leitura e a escrita.

```
pr_marcadores_info   →  {"name":"Testar tools com MCP", ...}
pr_marcadores_apagar →  {"sequencia":"Testar tools com MCP", "tudo":true}
```

Ler o nome **imediatamente antes** de escrever. O estado de minutos atrás não vale.

### Simule antes de destruir

`simular: true` existe em `pr_autoclip`, `pr_marcadores_apagar`, `pr_timeline_colocar` e `pr_midia_importar`. Devolve o que **seria** feito, sem fazer.

Use sempre que a operação for ampla e **mostre o número ao usuário** antes de executar. Não há desfazer pelo MCP.

---

## O AutoClip corta em marcador de anotação

`pr_autoclip` corta a timeline em cada marcador. Só que a automação usa marcador como **anotação** — vermelho para B-roll, azul para lettering, roxo para o que exige decisão humana.

Rodar o AutoClip numa sequência anotada pica o body em vinte pedaços.

```
pr_autoclip_info  →  {"porCor":{"1":10,"2":4,"6":6}}
pr_autoclip       →  {"ignorarCores":[1,2,6], "simular":true}
```

Sem filtro, ele corta em todos.

---

## Convenção de cor da casa

| Cor | Índice | Significa |
|---|---|---|
| 🔴 Vermelho | `1` | B-roll |
| 🔵 Azul | `6` | Lettering |
| 🟣 Roxo | `2` | Exige decisão humana (compliance, pessoa nomeada) |

Nome do marcador: `NN - TIPO - descrição`, numerado em ordem de timeline. Uma lista única para percorrer, em vez de três séries paralelas.

Marcador de **trecho**, não de ponto: `duracao` cobre a janela da fala a que ele se refere. Lettering ~3,5 s; B-roll 5–9 s; copy abrangendo a passagem inteira.

---

## Recuperar marcadores perdidos

Um `.prproj` é XML comprimido com gzip. Os marcadores ficam como JSON dentro de `<DVAMarker>`, com nome, comentário, ticks e cor ARGB. Dá para ler **sem abrir o Premiere** — inclusive de um auto-save.

```python
import gzip, re, json
x = gzip.open(caminho_prproj, 'rt', encoding='utf-8', errors='replace').read()
for b in re.findall(r'<DVAMarker>(.*?)</DVAMarker>', x, re.S):
    d = json.loads(b.replace('&quot;','"'))['DVAMarker']
    t = int(d['mStartTime']['ticks']) / 254016000000     # ticks por segundo
```

Os auto-saves ficam em `Adobe Premiere Pro Auto-Save/` ao lado do projeto. É a rede de segurança quando algo se perde.
