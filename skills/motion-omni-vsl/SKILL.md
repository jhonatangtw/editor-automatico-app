---
name: motion-omni-vsl
description: >-
  Gera lotes de MOTION GRAPHICS de overlay para VSL/criativo de direct response usando o Gemini Omni
  Flash no Higgsfield — cartelas de lettering, comparativos de preço, selos de garantia, cards de bônus
  e CTA, todos no mesmo sistema visual premium. Dois sistemas fechados, um por criativo: ESCURO (vazio
  preto, off-white, acento único) e CLARO (estúdio claro de saúde/farma, filamentos de sinapse, painel
  de vidro com borda azul, reveal em 5s e hold).
  Use quando houver uma timeline já marcada e for preciso produzir os motions das marcações de oferta
  e de frase de impacto, aplicá-los no Premiere e conferir grafia. NÃO é para gerar B-roll de cena nem
  avatar falante — é overlay que entra POR CIMA de um body já gravado.
---

# Motion Omni para VSL

Produz motions de overlay em lote no **Gemini Omni Flash**, confere e aplica no Premiere.
Validado no fechamento (CLOSE) da VSL LeafTide: 26 motions, 24 aplicados na timeline.

**O princípio:** o motion não é um clipe novo — é uma camada por cima do body que já existe.
Ninguém fala nele, ninguém aparece nele. Se um motion precisa de uma pessoa em quadro, ele está
competindo com o body em vez de reforçá-lo.

---

## 0. Antes de gerar um único clipe

**Leia as settings da sequência. Sempre. Antes de tudo.**

```bash
python3 cep.py '(function(){var st=app.project.activeSequence.getSettings();
return st.videoFrameWidth+"x"+st.videoFrameHeight})()'
```

O `pr_midia_info` **não** traz o frame size, e o tamanho dos brutos **não** diz o da sequência.
Nesta VSL os brutos eram 1920x1080 e a sequência era **1080x1350** — um lote inteiro de 26 motions
foi gerado em 16:9 e descartado. **870 créditos.** Um comando de dois segundos teria evitado.

Depois disso, levante também:

```
pr_marcadores_listar   → onde cada motion entra e quanto dura
pr_midia_info          → projeto e sequência ativos
higgsfield account status → autenticado? saldo?
```

---

## 1. O que o Omni Flash aguenta

| | |
|---|---|
| Duração | 10s (o `duration` default é 8 — sempre passar 10) |
| Aspect ratio | **só 16:9 ou 9:16** — não existe 4:5 nem 1:1 |
| Resolução | **só 720p**, sempre |
| FPS de saída | **24**, mesmo pedindo 25 no prompt |
| Referências | `image_references`, até 7 — **nunca `start-image`** |
| Custo | **30 créditos** por clipe de 10s |

**Formato de entrega diferente de 16:9 ou 9:16:** gere em **9:16 e corte**. Cortar 9:16 para 4:5
tira 15% em cima e 15% embaixo e **mantém a largura inteira**; cortar 16:9 para 4:5 comeria 58% da
largura e destruiria qualquer composição horizontal.

```
crop=iw:iw*1.25:0:(ih-iw*1.25)/2,scale=1080:1350
```

E declare o corte dentro do prompt, para o Omni compor na área que sobrevive:

> The top 15 percent and the bottom 15 percent of the frame will later be cropped away, so every
> product, every graphic and every letter must sit comfortably inside the central 70 percent of the
> frame height.

⚠️ **O workflow `reframe` não compensa:** 96 créditos contra 30 de uma geração nova, e nem entrega
4:5 (só 21:9, 16:9, 4:3, 1:1, 3:4, 9:16).

---

## 2. O DNA visual — dois sistemas, um por criativo

A skill tem **dois** sistemas visuais fechados. Escolha um no início do job e não misture:
preto profundo por cima de body claro faz o corte piscar.

| | **ESCURO** (§2 abaixo) | **CLARO** (`references/estilo-clean-pharma.md`) |
|---|---|---|
| Mundo | Vazio preto, haze volumétrica | Estúdio claro arejado, filamentos de sinapse esparsos |
| Tipografia base | Off-white | Neutro escuro (tinta) |
| Acento | Cor do produto (verde no LeafTide) | Azul da marca com bloom |
| Ritmo | Seis beats nos 10s inteiros | Reveal em 5s + hold calmo de 5s |
| Fecho | Congela e dessatura | Segura flutuando |
| Serve para | Dor, urgência, escassez, contraste de preço | Oferta, prova, credibilidade, saúde/farma |
| Gerador | `scripts/gerar_lote.py` | `scripts/gerar_lote_clean.py` |

O resto desta seção descreve o **ESCURO**, validado no CLOSE LeafTide.

| Camada | O que é |
|---|---|
| Base | Vazio preto profundo com haze volumétrica lenta |
| Painéis | Retângulos de vidro, cantos arredondados, borda fina luminosa no acento |
| Conteúdo | Tipografia e line-art em off-white |
| Acento | **Uma cor só**, e só em dois lugares: a borda do painel no instante em que ele pousa, e o brilho da linha de ênfase |
| Fecho | Congela, dessatura um passo, uma barra do acento se desenha sob a última linha e para |

**Paleta:** preto `#0B0B0C` · off-white `#F6F3EC` · acento = a cor do produto.
No LeafTide o dourado padrão da skill original virou **verde `#3FB27A`**, tirado do rótulo.
Vermelho fica reservado para significado (preço riscado), nunca para decorar.

### Os seis beats de 10 segundos

```
0.0–1.5s   ABERTURA   quadro quase vazio, push-in lento, ZERO texto
1.5–3.5s   PAINEL     o vidro sobe, a borda acende, painel ainda vazio
3.5–5.5s   LINHA 1    primeira linha resolve em off-white
5.5–7.5s   PICO       linha de ênfase entra maior, com bloom do acento
7.5–8.8s   RESOLVE    o painel encolhe, desfoca e sai; o texto fica
8.8–10.0s  HERO       tudo para. Congela, dessatura, barra do acento, fim
```

O respiro do RESOLVE e do HERO é o que faz parecer editado em vez de gerado.

---

## 3. Os arquétipos

O `troca` só existe no sistema CLARO, onde o ritmo tem espaço para substituir uma frase pela outra;
no ESCURO as duas linhas convivem empilhadas. Manter os blocos STYLE / TECHNICAL / PALETTE / CAMERA / AUDIO / DO NOT
**byte a byte idênticos** entre todos os clipes do lote — é o que faz o lote emendar como
um sistema visual só. Varia apenas a string, a tipografia por linha e o TIMELINE.

| Arquétipo | Quando | Referência de imagem |
|---|---|---|
| **produto** | oferta, preço, kit, garantia, entrega | mockup do produto / do kit |
| **puro** | frase de impacto, benefício, quebra de objeção | nenhuma |
| **troca** | duas frases num clipe só — a primeira sai e a segunda entra (preço → oferta) | mockup |
| ~~avatar~~ | **não usar** | — |

⚠️ **Não coloque o expert nos motions.** Foi testado e reprovado: em formato vertical a pessoa come
metade da altura útil, empurra o lettering para a borda que vai ser cortada, e o guarda-roupa dela
muda a cada geração (o Omni não mantém figurino entre chamadas e o CLI não expõe seed). O único
elemento humano do criativo deve ser o body na V1.

---

## 4. A política de texto — onde tudo dá errado

Renderizar texto é o ponto fraco do Omni. **Quatro travas ao mesmo tempo**, sempre:

1. **Contagem explícita** — `the exact phrase "..." — 5 words, nothing else`
2. **Cada linha nomeada** — `Line 1 reads "IT WILL NOT". Line 2 reads "FIX ITSELF".`
3. **Repetir as palavras dentro do TIMELINE**, no beat em que entram
4. **`The phrase appears EXACTLY ONCE in the frame at any moment`**

Detalhe da 4: sem ela, o Omni escreve a mesma frase em dois cards. Aconteceu com `CLICK BELOW NOW`
e com `ORDER NOW`.

Ver `references/armadilhas.md` para os sete bugs conhecidos e a correção de cada um.

---

## 5. O pipeline

```
1. ler settings da sequência        → formato e fps reais
2. montar o lote (scripts/gerar_lote.py)
3. QC no formato FINAL              → contact-sheet do beat de pico, JÁ CORTADO
4. regerar o que falhar             → 30 cr cada
5. aplicar na timeline (scripts/aplicar_timeline.py)
6. ler a timeline de volta          → posição, duração, escala, sobreposição
```

**O QC tem que ser no formato de entrega, não no formato de geração.** Extrair o frame de pico já
com o crop aplicado julga grafia e enquadramento de uma vez, e é o único jeito de ver se alguma
letra encostou na faixa que vai ser cortada.

### Regra de entrada no clipe

O motion tem 10s, a marcação quase nunca tem. Entre pelo trecho que **termina no fim do RESOLVE**
(8,8s) e recue a duração da marcação:

```
entrada = max(0, 8.8 - duracao_da_marcacao)
saida   = min(10, entrada + duracao_da_marcacao)
```

Assim o trecho usado sempre contém o texto já resolvido e o beat de pico, e nunca os 1,5s de
abertura vazia. Marcação maior que 8,8s usa o clipe do 0 e o resto fica com o body.

**No sistema CLARO a fórmula é outra**, porque o quadro final vale de 5,0s até 10,0s:

```
entrada = max(0, min(5.0, 10 - duracao_da_marcacao))
saida   = min(10, entrada + duracao_da_marcacao)
```

Marcação de até 5s cai inteira dentro do hold, começando no instante em que a linha de ênfase pousa.
Isso torna o claro bem mais tolerante a marcação curta que o escuro.

---

## 6. Escrever no Premiere

Pelo Tools PRO (`http://127.0.0.1:7842/mcp`, token em `~/.editor-black-belt/mcp-ppro.json`):

- `pr_midia_importar` → campo **`arquivos`** (não `caminhos`), aceita `bin`
- `pr_timeline_colocar` → campo **`clipes`** (array), e **`trilha` é número base 0** — V1 é `0`, V2 é `1`
- `modo` só aceita `sobrescrever` ou `inserir`; erro volta como **texto puro**, não JSON

Gere os arquivos já no tamanho exato da sequência: aí a escala entra em 100% e não há reenquadramento
a corrigir. Confirme lendo de volta — `pr_timeline_listar` arredonda em 2 casas, então para gaps
finos meça em ticks (`ticks/254016000000`).

**Guarde os motions na pasta do projeto**, não no scratchpad, com o número da marcação no nome:
`4.Motion/<bloco>/08-MO-13_89-19-99.mp4`. O nome amarra o arquivo ao marcador que o originou.

---

## 7. Custo real

| | |
|---|---:|
| 1 motion de 10s | 30 cr |
| Lote de 26 | 780 cr |
| Regeração típica (10–15% do lote) | 90–120 cr |

Rode sempre um **piloto de 2** (um de oferta, um de lettering) antes do lote. 60 créditos que
provam o padrão e evitam repetir um erro 26 vezes.

---

## Referências

- `references/prompt-template.md` — sistema ESCURO: o esqueleto completo, na ordem obrigatória, com um exemplo pronto de cada arquétipo
- `references/estilo-clean-pharma.md` — sistema CLARO: DNA, os quatro beats, blocos comuns, arquétipo `troca` e as três correções sobre o prompt de referência
- `references/armadilhas.md` — os sete bugs do Omni Flash e a correção de cada um
- `scripts/gerar_lote.py` — monta e submete o lote ESCURO com os blocos comuns travados
- `scripts/gerar_lote_clean.py` — o mesmo para o lote CLARO (`SECO=1` monta os prompts sem gastar crédito)
- `scripts/qc_contact_sheet.py` — baixa, corta no formato final e monta o contact-sheet
- `scripts/aplicar_timeline.py` — copia para o projeto, importa e coloca na trilha
- `assets/` — as referências de produto usadas neste job
