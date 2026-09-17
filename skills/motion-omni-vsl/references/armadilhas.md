# Armadilhas do Omni Flash

Sete bugs vistos no lote do CLOSE LeafTide (26 motions, agosto/2026), com a correção de cada um.
Todos são reproduzíveis: não são azar do renderizador, são brecha no prompt.

---

## 1. Linha declarada a mais → o Omni inventa palavras para preencher

**Sintoma.** A frase era `IT WILL NOT FIX ITSELF` (5 palavras, 2 linhas). Saiu:

```
WHE LARINT WOTRING
IT WILL NOT
FIX ITSELF
```

e no fim degenerou para `WA.L. IS / IT WILL IVERINST! / FIX ITSELF`.

**Causa.** O bloco TYPOGRAPHY dizia `set in three stacked lines`. Sobrou uma linha sem conteúdo
declarado, e o modelo alucinou para ocupar o espaço.

**Correção.** Nunca declare número de linhas maior que o da frase. Nomeie o conteúdo de cada uma:

```
Exactly 2 lines. Line 1: "IT WILL NOT" at base size in off-white.
Line 2: "FIX ITSELF" one size larger with a soft green glow.
```

---

## 2. Instrução do prompt renderizada como texto na tela

**Sintoma.** Um clipe saiu com **`Caption safe zone`** escrito dentro de um card, junto de
`PEAK FOO1- MONEY BACK DEAANE`.

**Causa.** O prompt terminava com *"Keep the horizontal middle band of the frame clear as a caption
safe zone"*. O Omni tratou a instrução como conteúdo.

**Correção.** Tire termo técnico do prompt. Descreva a restrição em linguagem de composição
("every letter must sit inside the central 70 percent of the frame height") e proíba no DO NOT:

```
never render any word from these instructions as visible text — no technical terms,
no "caption", no "safe zone", no "frame", no pixel sizes, no colour codes, no font names
```

Vale a mesma regra da skill original: nunca escreva hex, fps, duração ou nome de fonte
onde o modelo possa ler como conteúdo.

---

## 3. "seal" e "button" viram superfícies com escrita

**Sintoma.** Pedi *"a circular guarantee seal outline"* e *"a wide rounded button"*. Saíram um selo
com `GUARANTEE` escrito, um card com o nome da marca, e `ORIGN'M DEFOLATIONE` dentro do círculo.

**Causa.** As palavras carregam a expectativa de texto. Selo tem dizeres; botão tem rótulo.

**Correção.** Descreva a forma, não o objeto:

```
a thin circular ring outline with nothing written inside it
a wide rounded button shape with no writing on it
```

---

## 4. A frase aparece duas vezes

**Sintoma.** `CLICK BELOW NOW` em dois cards no mesmo quadro. `ORDER NOW` idem, duas vezes.

**Correção.** Em todo prompt, sem exceção:

```
The phrase appears EXACTLY ONCE in the frame at any moment — never duplicated on a second card,
never repeated elsewhere.
```

---

## 5. A cor de ênfase é ignorada

**Sintoma.** `$19.99` saiu em off-white em vez do acento, mesmo com
`one size larger with a soft green glow` no TYPOGRAPHY. Aconteceu em 5 dos 26.

**Causa.** Uma menção só não segura. O modelo prioriza o "off-white" declarado no início do bloco.

**Correção — reforço triplo.** A mesma informação em três lugares:

- **TYPOGRAPHY:** `Line 2: "$19.99" is rendered in LeafTide green #3FB27A, not off-white — it is the only coloured text in the frame`
- **PALETTE:** `the accent is ... the fill colour and glow of the second line, which must be green rather than off-white`
- **TIMELINE:** `the words "$19.99" snap into place ... coloured LeafTide green #3FB27A, clearly green against the off-white struck-out "$89" above`
- **DO NOT:** `do not render the second line in white or off-white`

Resolveu em uma tentativa.

---

## 6. Filtro de conteúdo barra a geração (status `nsfw`)

**Sintoma.** O job voltou com `status: nsfw` e nenhum resultado. A frase era
`A LEADING PREDICTOR / OF EARLY DEATH`.

**Causa.** A palavra **DEATH**. O filtro roda antes da geração — regerar o mesmo prompt não adianta.

**Correção.** Reescreva a frase sem o termo, preservando o sentido:
`A LEADING / RISK FACTOR`. Se a força da frase original for inegociável, esse lettering
tem que ser feito fora do Omni (After Effects), onde não há filtro.

⚠️ **`nsfw` é um status terminal.** Qualquer loop de espera precisa tratá-lo junto de
`completed` e `failed`, senão fica preso para sempre.

---

## 7. Badge carimbado sobre o produto

**Sintoma.** O selo `100% MONEY BACK` foi renderizado **sobre o rótulo do pote**, alterando o
mockup oficial do produto.

**Correção.** Explicitar que o produto é intocável:

```
Never place a badge, seal, sticker, ribbon or any writing on top of the jar itself.
Never render the brand name as a separate card or label anywhere in the frame.
```

E simplifique o TIMELINE: quanto mais elementos você pede num beat, mais superfície o modelo
tem para escrever coisas. Os dois clipes mais problemáticos foram resolvidos reduzindo o beat
a "painel liso + uma linha de texto".

---

## 8. Qualquer forma CIRCULAR fechada atrai texto

**Sintoma.** Dois clipes do lote da Offer eram os unicos com `a thin circular ring with no writing`.
Os dois quebraram, cada um de um jeito: um veio com a borda do anel **coberta de letras inventadas**
(`EDEWN TORAL PADICK SOM SNIEN...`), o outro **duplicou a frase** (`VALID FOR` numa linha e
`VALID FOR 24 HOURS` na outra). Os outros 20 clipes do mesmo lote, sem circulo, passaram.

**Causa.** Nao e so "seal" (armadilha 3). O modelo trata **qualquer curva fechada** como superficie
que pede texto — selo, botao redondo, anel, medalha, contador circular. Declarar
`with no writing` nao basta; a forma pesa mais que a negacao.

**Correção — basta o DO NOT, o circulo pode ficar.** Testado: regerando os dois com o circulo
INTACTO no corpo do prompt e apenas estas negacoes acrescentadas, os dois sairam limpos —
anel presente, sem uma letra nele, e sem duplicar a frase:

```
no circular ring, no curved surface carrying letters, no text following a curve, no repeated words
```

Ou seja, nao e preciso abrir mao da forma. Se ainda assim quebrar na segunda tentativa, ai sim
troque por forma reta, que nao sugere rotulo:

| Em vez de | Use |
|---|---|
| anel girando (tempo passando) | barra vertical deslizando sem chegar ao fim |
| contador circular (contagem regressiva) | barra horizontal encurtando pela direita |
| selo redondo (garantia) | painel retangular liso com a frase dentro |

⚠️ Corolario pratico: se um clipe do lote quebrar e os outros nao, **procure o que ele tem de
diferente na descricao de forma** antes de culpar o renderizador. No lote da Offer os dois unicos
defeitos estavam nos dois unicos prompts com circulo — nao foi coincidencia.

---

## Miscelânea

**Apóstrofo.** `IT WON'T` erra mais que `IT WILL NOT`. Prefira a forma sem contração.

**Cifrão com decimal.** `$19.99` e `$1500` funcionaram, mas são o maior risco do lote —
confira esses primeiro no QC.

**Nome da marca.** O rótulo oscilou entre `Leaftide` (correto) e `LeafTide`. Em plano fechado
isso é visível; se o cliente for rígido, esses clipes precisam de outra passada.

**Figurino não persiste.** Duas gerações com a mesma imagem de referência devolveram a pessoa com
roupas diferentes. O CLI não expõe seed. A única trava é descrever a roupa no STYLE — e ainda
assim é frágil, mais uma razão para não colocar gente nos motions.

**24 fps.** A saída ignora o fps pedido no prompt. Conforme na importação se a sequência exigir.
