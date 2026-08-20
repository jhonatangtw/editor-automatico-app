# Como pedir as marcações

Guia para quem vai **usar** a automação. Se você é a automação, o fluxo está no `SKILL.md`.

---

## O prompt

```
Marca a sequência "Avatar Video_1080p" do projeto aberto.

Copy: /caminho/para/copy.docx        (ou o link do Google Doc)

Marcador de TRECHO, com início e fim cobrindo a janela da fala.
Numerado em ordem de timeline, padrão NN - TIPO - descrição:
  vermelho = B-ROLL
  azul     = LETTERING
  roxo     = COPY  (o que a copy exige, ou o que precisa da minha decisão)

Ancora tudo na fala transcrita, não em tempo redondo.
Só marca — não gera b-roll ainda.
```

Versão curta, quando estiver com pressa:

```
Marca a sequência "<nome exato>" conforme a copy em <caminho>.
Padrão numerado, marcador de trecho. Só marcar.
```

---

## A palavra que mais importa é o nome da sequência

Sem o nome, a automação age na **sequência ativa** — e ela muda quando você clica noutra aba da timeline. Já aconteceu de **17 marcadores de um job real serem apagados** por causa disso: a leitura foi feita numa sequência, o clique mudou a aba, e a escrita caiu na outra.

Hoje a ferramenta exige declarar qual sequência espera e recusa se não bater. Mas ela só sabe qual você quer se **você disser**.

Não sabe o nome exato? Peça antes:

```
lista as sequências
```

---

## O que a automação faz sem você pedir

Não precisa estar no prompt:

- Transcreve o áudio com timestamp **por palavra**
- Pergunta qual MCP usar (Tools PRO ou Higgsfield)
- Confere o nome do projeto e da sequência antes de escrever
- Simula antes de qualquer operação destrutiva, e mostra o número
- Lê de volta e confere o que escreveu
- Sinaliza compliance — antes/depois, marca de medicamento, endosso médico, pessoa nomeada — **sem decidir por você**

---

## Três coisas que mudam o resultado

**Mandar a copy.** Sem ela a marcação sai da transcrição crua do Whisper, que erra justamente os nomes próprios que mais importam. Num job real, *Mounjaro* virou *"MANJARO"* duas vezes.

**Dizer se é criativo ou lead.** Muda a densidade. Criativo UGC pede **poucos** inserts em ponto estratégico. Lead aguenta mais, e aceita lettering explicativo.

**Dizer o que já está montado.** Se a timeline já tem b-roll, a automação lê e marca só o que falta, em vez de sugerir o que já existe.

---

## Depois de marcar

Gerar b-roll fica separado **de propósito**, porque gasta crédito:

```
Gera os b-rolls dos marcadores vermelhos 05, 10 e 12.
```

Assim você olha as marcações, corta o que não quer, e só então gasta.

---

## O que precisa estar instalado

### Essencial

| | |
|---|---|
| **Git** | `git --version` — o plugin é instalado clonando um repositório, sem git não instala |
| **Premiere Pro** | com o projeto aberto |
| **Tools PRO 1.2.0+** | painel aberto → *Conectar IA* → *Ligar* → comando colado no terminal |
| **Claude Code** | reiniciado depois de registrar o MCP |
| **A skill** | `/plugin marketplace add jhonatangtw/creative-automation` |

### Para ancorar na fala

O marcador cobre a janela da fala, então precisa da transcrição — a menos que o job já tenha `.srt` ou `.json`:

| | |
|---|---|
| **ffmpeg** | `brew install ffmpeg` |
| **Python 3** | já vem no macOS |
| **Whisper** | `pip3 install openai-whisper` |
| **modelo large-v3** | **~3 GB**, baixa sozinho na primeira vez |

> Baixe o modelo **antes** do primeiro job. Rodar pela primeira vez no meio de uma demanda dá a impressão de que travou.
> ```bash
> whisper --model large-v3 --help
> ```

### O que NÃO precisa para marcar

- **Higgsfield** — só entra para **gerar** b-roll. Marcar é 100% local.
- **Pillow** — só para legenda e lettering.
- **Chave de API** — nenhuma.

Isso importa: a parte que mais trava na instalação — o conector do Higgsfield, com o erro `invalid_request: redirect_uri` — **não é necessária** para marcação. Quem só quer marcar pode pular inteiro.

---

## Conferir a máquina

```bash
cd ~/Documents/hw-creative-automation && bash diagnostico.sh
```

Checa tudo isso e **não expõe nenhuma chave** — dá para colar a saída em qualquer lugar.

Em **SERVIDORES MCP LOCAIS** tem que aparecer `toolspro-pr`. Se aparecer só os conectores do claude.ai, o painel não foi registrado: volte ao passo *Conectar IA → Ligar*, cole o comando **no terminal** (não no chat) e reinicie o Claude Code.

---

## Convenção de cor

| Cor | Significa |
|---|---|
| 🔴 Vermelho | B-roll |
| 🔵 Azul | Lettering |
| 🟣 Roxo | Exige decisão humana |

Nome: `NN - TIPO - descrição`, numerado em ordem de timeline. Uma lista única para percorrer, em vez de três séries paralelas.

Marcador de **trecho**, não de ponto: a duração cobre a janela da fala a que ele se refere. Lettering ~3,5 s; B-roll 5–9 s; copy abrangendo a passagem inteira.

---

## Aviso

**Não rode o AutoClip numa sequência com marcações da automação.** Ele corta a timeline em **todos** os marcadores, inclusive nos de sugestão — um criativo com 20 marcações vira 20 pedaços.

A automação sabe filtrar por cor. Se for rodar na mão, cuidado.
