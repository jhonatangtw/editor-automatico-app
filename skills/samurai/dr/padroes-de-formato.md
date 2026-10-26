# Padrões de edição da casa — AD, Microlead, VSL e Upsell

Medido em 22/10/2026 em 14 vídeos finalizados: 4 ADs, 5 microleads, 2 VSLs e 3 upsells. As fichas, com caminho de origem e medições, estão em `dr/referencias/`.

O que este arquivo é: o **estilo e o modelo de edição** que a casa entrega, para o Editor de Vídeo e o IA Creator reproduzirem. Ele **não** diz o que vende. Não há dado de venda por vídeo, então nenhum destes é "vencedor". Onde os vídeos divergem entre si, a regra aqui escolhe o padrão mais consistente e diz qual foi o contraexemplo.

## Tabela rápida

| | AD 9:16 | Microlead | VSL | Upsell |
|---|---|---|---|---|
| Proporção | 9:16, 1080×1920 | a da VSL de destino (9:16, 4:5 ou 16:9) | 9:16, 1080×1920 | 16:9 |
| fps | 30 (casa misturava 23,976/25/30) | o da VSL de destino | 30 | 29,97/30 |
| Duração vista | 74–231 s | 76–141 s | 28–64 min | 4–6 min |
| Fala | 168–199 palavras/min, quase sem pausa | 163–176 palavras/min | — | — |
| Cortes/min | 11–27 (limiar 0.12); punch-in carrega o ritmo | UGC 17–21 · celebridade/porta-voz ~14 · telejornal 6–7 | 12–17 no geral, varia por bloco | 15–17 |
| Talking head na tela | 60–77% | depende do registro | 18–50% | 18–50% |
| Legenda | 1–4 palavras, faixa de 50–73% da altura | igual à da VSL de destino | frase curta em caixa escura translúcida, 55–70% da altura | pílula branca, palavra ativa preta, resto cinza |
| CTA | gráfico (pílula/seta) nos últimos 10–15%, entra com a fala do link | nenhum clique: ponte "3, 2, 1" / "watch the next…" | botão/pitch no fechamento | "só nesta página" depois do preço |
| Loudness alvo | −14 LUFS, TP ≤ −1 dB | ±1 LU da VSL de destino | −16 LUFS, TP ≤ −1 dB | −16 LUFS, TP ≤ −1 dB |
| Áudio | 48 kHz; trilha baixa sob a voz | trilha sob a voz (4 de 5) | trilha contínua sob a voz | trilha sob a voz |

O loudness alvo é decisão da casa, não média do que foi medido. Os vídeos medidos variaram de −31 a −16 LUFS, e uma VSL clipou (+0,4 dBTP). Padronizar é parte do trabalho.

## AD (criativo 9:16, hook + body)

- **Hook é módulo próprio**, de 5 a 15 s, com layout diferente do body: split com inset, split horizontal, faixa fixa ou troca de personagem. Em 3 de 4, uma **manchete fica fixa no topo** durante o hook e sai quando o body entra.
- **Body:** talking head com punch-in a cada 3 a 6 s. B-roll de 24 a 33% do tempo, sempre ilustrando a palavra dita.
- **Legenda:** 1 a 4 palavras por vez, centralizada entre 50% e 73% da altura, com caixa ou glow. O premium da casa (ProdutoJ, skill `edicao-prosperidade-adhw`) é caixa alta com karaokê, palavra ativa roxa e lettering amarelo com deep glow nas frases fortes. Contraexemplo: o MarcaB usou legenda pequena demais.
- **Transição de bloco:** flash ou light leak. Lettering neon só em frase forte.
- **CTA:** pílula LEARN MORE / CLICK BELOW com seta, entrando no instante em que a fala menciona o link e ficando até o fim.
- **Produto:** quando é nomeado, pack-shot em motion (pote sobre tipografia cinética) ou nome em lettering com glow.

## Microlead

- **Microlead é a abertura de uma VSL, não um AD.** Várias aberturas (6 no MarcaH) entram no mesmo corpo de VSL. A emenda cai entre 76 e 133 s.
- **Herda tudo da VSL de destino:** proporção, fps, legenda e volume (no máximo 1 LU de diferença). Teste 5 s antes e depois da emenda.
- **Estrutura:** hook com objeto de prova na mão do apresentador desde o 1º quadro, promessa, vilão, autoridade, **nome do mecanismo antes dos 75 s** (reforçado em lettering) e ponte para quem fala a seguir ("3, 2, 1", "team roll the video", "watch the next…"). Não tem CTA de clique.
- **Registro define o ritmo:**
  - UGC/receita: 17–21 cortes/min, planos de ~2 s, punch-in no rosto, B-roll orgânico de corpo e mãos de cima.
  - Porta-voz de autoridade: ~14 cortes/min, planos de ~4 s.
  - Noticiário: 6–7 cortes/min, plano âncora longo, inserts nos números e manchetes.
- **Abertura:** primeira fala em até 1 s, sem tela preta. Os casos de 2,5 s de preto + 8,8 s sem fala só servem se forem emenda deliberada; para feed, nunca.

## VSL

- **Ritmo varia por bloco, sempre nesta forma:**

| bloco | cortes/min |
|---|---|
| hook / primeiro minuto | > 20 (MarcaF: 28) |
| mecanismo e argumento | 15–21 |
| história e depoimento | 5–8, planos de 7–11 s |
| oferta / garantia | 8–10 |
| fechamento | volta a acelerar (~16) |

- **Apresentador** em 18 a 50% do tempo. Volta para ele no preço, na garantia e no CTA. No resto, B-roll, motion ou lettering cobrem de 50 a 80%.
- **Legenda** sempre presente: frase curta em caixa escura translúcida, texto branco.
- **Lettering** pouco e no ponto-chave: fundo desfocado e escurecido + uma palavra em neon (amarelo ou verde). **Preço** em neon verde gigante ("ONLY $67"). **Garantia** com selo dourado. Uma única família de fonte por vídeo (a MarcaF misturou 3).
- **Oferta:** começa entre 63% e 88% da duração.
- Motion de overlay (cartelas, preço, selo, bônus): skill `motion-omni-vsl` ou `vsl-motion-ae`.

## Upsell

- 16:9, 4 a 6 min, 15 a 17 cortes/min.
- **Preço entre 74% e 80% da duração**, seguido da garantia de 180 dias e de "só nesta página".
- Legenda em pílula branca com a palavra ativa em preto.
- Upsell 1:1 do MarcaB tem padrão visual próprio (skill `padrao-visual-MarcaB`).

## Continuidade (vale para tudo, e entre vídeos do mesmo funil)

Defeitos que apareceram e que o padrão evita:
- Apresentador com figurino que aparece e some entre planos (solidéu no UP1/UP2).
- Rosto do apresentador trocado dentro do mesmo funil (UP3).
- Personagem do B-roll com outra roupa ou outro rosto entre planos (MarcaB AD).
- 6 clipes de B-roll repetidos entre UP1 e UP2. Repetição se confere no funil inteiro, não só no vídeo (memória `footage-sem-repeticao-na-timeline`).
- Legenda fora do padrão de caixa (minúscula no meio de caixa alta).
- Master sem padrão: fps, sample rate e loudness diferentes entre entregáveis do mesmo job.
