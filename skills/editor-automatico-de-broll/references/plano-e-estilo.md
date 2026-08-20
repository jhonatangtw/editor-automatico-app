# Plano e estilo

Separa **o que o criativo diz** (plano) de **como ele é acabado** (estilo), e coloca um portão de
aprovação entre decupar e executar.

Antes, o `edicao.json` misturava as duas coisas: os inserts (conteúdo) e as escalas de punch
(acabamento) no mesmo arquivo, escrito à mão por job. O efeito prático era que nada era reutilizável
— mudar de ritmo significava reescrever o arquivo inteiro, e o padrão validado da casa vivia em
prosa no `estilo-ugc.md`, não em código.

Agora são quatro camadas, e cada uma tem um dono:

| Camada | Artefato | Quem produz |
|---|---|---|
| 1. Entender | `body.json` (Whisper, word timestamps) | `decupador` |
| 2. **Plano** | `plano.json` — beats com fala, intenção e mídia | agente + humano |
| 3. **Estilo** | `estilos/*.json` — densidade, punch, legenda, marcador | fixo, medido no acervo |
| 4. Executar | `edicao.json` + `marcadores.json` | `compilar.py` |

O plano roda em qualquer estilo. É essa a regra que justifica a separação: **nada de acabamento mora
no plano, nada de conteúdo mora no estilo.**

---

## O plano

```json
{
  "versao": 1,
  "job": "LEAFTIDE_AD01",
  "formato": "ugc-9x16",
  "estilo": "alta-densidade",
  "saida": "AD01_FINAL_9x16.mp4",
  "legenda": "AD01_LEGENDAS.mov",
  "fonte": {"body": "VIDEO DO BODY.mp4", "duracao": 133.6, "largura": 1080, "altura": 1920},
  "beats": [
    {"id": "B1", "tipo": "insert", "inicio": 8.52, "fim": 14.16,
     "fala": "tive que trocar o guarda-roupa",
     "intencao": "ela aparece de outra roupa",
     "midia": "BROLL/B1_guardaroupa.mp4"},

    {"id": "L1", "tipo": "lettering", "inicio": 5.90, "fim": 8.10,
     "texto": "22 POUNDS\nIN 12 DAYS"},

    {"id": "C1", "tipo": "copy", "inicio": 41.0, "fim": 43.0,
     "nota": "claim de resultado — conferir compliance"}
  ]
}
```

Quatro tipos de beat: `insert`, `lettering`, `copy` e `punch` (este último só como **override
manual** — no fluxo normal o punch é derivado do estilo).

Campos que carregam o porquê, e não só o quando:

- **`fala`** — a citação exata que justifica o insert. É o critério de casamento verbal-visual; sem
  ela não dá para revisar se o insert está no lugar certo.
- **`intencao`** — o que tem que aparecer na tela. Vira o prompt de geração e vira o nome do
  marcador.
- **`midia`** — `null` enquanto o b-roll não existe. É assim que o portão sabe o que falta gerar.

---

## O estilo

Estilo é um **token nomeado**, não uma decisão por job. Dois já medidos no acervo:

- **`alta-densidade`** — 1 corte a cada 3–5s, cobertura de b-roll ~25%, punch 1.10–1.16 nos vãos.
- **`talking-head-puro`** — zero insert, zero punch. O AD mais longo do acervo (251s) valida assim.

O estilo decide: faixa de escala do punch, intervalo mínimo entre eles, se pode punch por baixo de
insert, template e posição da legenda, teto de lettering, cor de marcador por tipo, e se entra flash
e SFX (padrão: `null` nos dois — **corte seco é o padrão aprovado**).

Estilo novo = arquivo novo em `estilos/`. Não é `if` no meio do fluxo.

---

## O portão

```bash
python3 scripts/revisar.py --plano plano.json
```

Imprime a régua da timeline, cada beat com a fala que o justifica, cobertura de b-roll medida contra
o alvo do estilo, o maior vão sem troca de imagem, e duas listas: **alertas** (revisar) e
**bloqueios** (impedem montar). Sai com código 1 se houver bloqueio.

É o passo que faltava. Antes, o erro só aparecia no `auditor-de-entrega`, depois de gerar b-roll e
escrever na timeline — quando consertar já custava crédito e retrabalho.

---

## A execução

```bash
python3 scripts/compilar.py --plano plano.json --out .
```

Gera dois artefatos do **mesmo** plano:

- **`edicao.json`** — contrato do `montar.py`. O punch sai calculado do estilo, contíguo de `0` até
  a duração, respeitando a margem dos inserts (punch por baixo de insert é desperdício).
- **`marcadores.json`** — contrato do `pr_marcadores_criar`. Já com a convenção de cor
  (vermelho 1 = B-ROLL, azul 6 = LETTERING, roxo 2 = COPY), o vermelho esticado até o próximo
  — a cama de imagem — e o primeiro começando em `0`.

Trocar de estilo é trocar um argumento:

```bash
python3 scripts/compilar.py --plano plano.json --estilo talking-head-puro --out .
```

---

## De onde veio a ideia

Do Captions (captions.ai). O que eles acertaram e vale copiar não é o acabamento — é a ordem: a IA
entrega **plano revisável**, não vídeo pronto. O usuário aceita, desfaz corte a corte, e só então
renderiza.

O que não copiamos: eles processam no máximo 1–2 minutos por projeto. Nosso material é VSL de uma
hora, aula gravada, master ALL-I. A arquitetura serve; o serviço não.

### O documento deles, lido por dentro

Medido em 16/08/2026 num projeto real (`HkyYiFl3wvXCEG9a5rmZ`, estilo *Ignite*, 74,5s), capturando o
tráfego autenticado do app. A API é `internal.captions-api.com`; o documento vem de
`/proxy/camel/web/video/editor-project-details`.

```
data
├─ aiEditStyle        {id, name: "Ignite", tags:["premium","Bold"]}   ← ponteiro, não conteúdo
├─ projectDataUrl     data:application/x-protobuf;base64,…  (219 KB)  ← a timeline
├─ assetUrlMap        {assetId → URL}      49 assets
├─ assetMetadataMap   {assetId → {type: video|audio|image|pag}}
└─ creationMetadata   {productType: AI_EDIT, isEyeContact, isDenoise, fastMode, …}
```

Dentro do protobuf, o que importa:

| Campo | O que é |
|---|---|
| `shots[]` ×15 | a timeline **inteira particionada** — cada segundo pertence a um shot |
| `shot.template` | `{name: "Hook 3", id}` — o papel do shot |
| `captions[]` ×15 | frases, cada uma com `words[] {startMs, endMs, texto, flags}` |
| `sounds[]` ×28 | eventos de SFX com volume (0.2) |
| `captionStyle` | `{name: "Heat", cores RGBA, corpo 21, owner: captions_team_internal}` |

**Cinco papéis de shot**, e é isso que organiza tudo:
`HOOK` · `TALKING_HEAD` · `B_ROLL` · `TALKING_HEAD_B_ROLL` · `TEXT`

Cada papel tem **3 variantes** (13 templates no total) — a mesma razão pela qual variamos a escala do
punch: repetir o mesmo tratamento vira tique visível.

E cada variante é um trio de animações `.pag` (formato do After Effects) nomeadas por fase:
`ignite_broll_frame_2_IN.pag` · `_DURATION.pag` · `_OUT.pag`. Ou seja: **o "estilo" deles é um pacote
de composições de AE indexadas por papel**, não um conjunto de parâmetros.

### O que isso confirma e o que corrige

**Confirma** a separação plano × estilo: o estilo é um ponteiro (`aiEditStyle`), o conteúdo é o shot
list, e a mídia é referenciada por id num mapa à parte — trocar um b-roll é trocar uma entrada do
mapa.

**Confirma a cadência da casa.** 15 shots em 74,5s dá **1 troca a cada 5,0s** — exatamente dentro da
faixa de 3–5s medida nos 27 ADs validados. Dois acervos independentes, mesmo número.

**Corrige uma coisa nossa:** b-roll aparece em **10 dos 15 shots (67%)**, contra os 25% de cobertura
que o `alta-densidade` mira. O criativo deles é muito mais coberto que o nosso padrão.

**Uma divergência deliberada:** 28 eventos de SFX em 74s, a 0.2 de volume. Nosso padrão é
`sfx: null`, e continua sendo — corte seco é o que validou aqui. Registrado para não parecer
esquecimento.

**A diferença estrutural que sobra:** o plano deles particiona a timeline inteira em shots com papel;
o nosso modela só as exceções (inserts sobre um body contínuo). O modelo deles é mais robusto —
nenhum segundo fica sem dono — mas trocar para ele significa reescrever o `montar.py`. Fica anotado
como decisão em aberto, não como pendência.
