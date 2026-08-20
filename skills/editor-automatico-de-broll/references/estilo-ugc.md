# Estilo de edição — medido no acervo de ativos validados

Base: **5 dos 27 ADs validados** da H&W (Diabetes, Joint Pain, Memory Loss, Weight Loss), medidos por detecção de cena em 28/07/2026.

Quando houver vídeo de referência no job, **ele manda** — extrair o padrão dele por mosaico de frames e sobrescrever o que está aqui.

---

## Existem DOIS formatos validados, não um

Os dados não mostram um padrão médio. Mostram dois grupos separados, sem meio-termo:

| Formato | Cortes | Exemplos medidos |
|---|---|---|
| **Alta densidade** | 1 a cada **3–5s** | Diabetes 44 cortes/145s · ML-2 32/151s · WL-15 33/168s |
| **Talking head puro** | **zero cortes** | ML-33 (74s) · JP-03 (251s) |

**Insert NÃO é obrigatório.** O criativo mais longo do acervo — 251 segundos — é também o mais simples: plano fixo do primeiro ao último frame, sem um corte. Ele valida do mesmo jeito.

A escolha entre os dois é de estratégia, não de ofício:

- **Talking head puro** aposta em carisma e história. Funciona quando o rosto e a fala seguram sozinhos. Cortar aqui atrapalha.
- **Alta densidade** aposta em estímulo e prova. Cenário caseiro, receita sendo feita, balança, ingredientes, prova visual.

**Perguntar ao usuário qual formato antes de decidir a densidade.** Se o brief definir, seguir o brief.

---

## Calibragem de densidade

Se o formato for **alta densidade**, a referência é **1 corte a cada 3 a 5 segundos**.

> Para dimensionar: o AD01 do LeafTide saiu com **15 cortes em 134s — 1 a cada 8,9s**. Está entre os dois grupos, e provavelmente **subcortado** para o padrão de alta densidade da casa. Serviu como corte seco conservador; não serve como referência de ritmo.

Contar corte inclui entrada e saída de insert, punch-in e troca de plano — tudo que muda a imagem.

Medir com:
```bash
ffmpeg -v info -i video.mp4 -vf "select='gt(scene,0.30)',metadata=print" -an -f null - 2>&1 | grep -c pts_time
```
> Usar `-v info`. Com `-v error` o filtro não imprime nada e a contagem volta zero — parece que o vídeo não tem corte.

---

## O que é igual em TODOS os validados

Isto é padrão da casa, não escolha por job:

- **9:16 vertical**, 1080x1920 (alguns 720x1280)
- **Legenda em pílula branca, texto preto, 3–4 palavras**, centro-baixo. Sem exceção nos cinco medidos.
- **Talking head domina o tempo**, mesmo no formato de alta densidade
- **Pessoa comum, cenário doméstico real** — cozinha, quintal, sala

---

## Inserts — onde entram, quando entram

Critério único: **casamento verbal-visual.** O insert entra no segundo em que a fala o descreve.

Os tipos que aparecem nos validados de alta densidade:

| Tipo | Exemplo do acervo |
|---|---|
| Preparo / receita | ingredientes na bancada, mistura sendo feita no Pyrex |
| Prova numérica | balança marcando o peso, tela de celular |
| Produto / mecanismo | macro do pó, microscopia |
| Reação / prova social | print, depoimento |

**Roupa diferente em cada B-roll da mesma pessoa** — lê como dias diferentes, que é o cheiro de UGC real.

---

## Punch-in

Escala entre **110% e 116%**, variando entre as janelas. Escala igual em todas vira tique perceptível.

Corte seco para dentro e para fora — nada de zoom animado, que lê como corporativo.

---

## Transição

**Nenhuma.** Corte seco.

Testado de forma comparativa no AD01: foram produzidas duas versões, uma limpa e outra com Flash Transition do Premiere Composer mais whoosh. **O usuário escolheu a limpa.** Em UGC, transição denuncia produção.

Se pedirem explicitamente, só flash e discreto. Ver `armadilhas.md`.

---

## Áudio

Body de TTS já vem empacotado, sem tempo morto — não procurar silêncio para cortar.

Música de fundo e transição são finalização humana no Premiere.

---

## Limites desta medição

- **5 de 27 ADs** foram medidos. A amostra pode não representar o acervo.
- **"Validado" ainda não está definido** — não se sabe se significa "escalou" ou apenas "não foi reprovado". Se alguns escalaram muito mais, a densidade correta é a deles, não a média.
- Não há dado de performance por criativo. Sem isso, tudo aqui é padrão observado, não causa comprovada.
