# Padrão visual e de edição — upsell premium 9:16 (NNN_XX, aprovado 28/10/2026)

Formato 1080×1920, 25 fps, ~9–10 min. Tudo sai do build Python → `index.html` (HyperFrames + GSAP). Nunca editar o HTML.

## Ritmo e cortes
- O expert abre o vídeo (D) e conduz. Mistura medida no NNN_XX, de 590 s: expert sozinho ≈ 36 %, F/M (cards na frente dele desfocado) ≈ 28 %,
  B/R (b-roll em tela cheia) ≈ 30 %, T (lettering sobre 3D) ≈ 6 %.
- Um momento novo a cada 3–6 s no bloco de mecanismo/dor; o bloco de oferta pode respirar 6–10 s.
- Trecho de expert sozinho > 8 s só em respiros intencionais (antes de virada). O build lista os buracos > 8 s.
- Punch-in no expert alternando escala 1,00 ↔ 1,12 em início de frase, ≥ 2,2 s entre um e outro. Deriva contínua.
- Corte seco entre momentos. Entrada de b-roll: zoom 1,12→1 + blur 10→0 em 0,35 s e push lento 1→1,08 durante o plano.
- Entrada de T: o 3D de fundo entra com scale 1,25→1 + blur 18→0 (0,55 s) e push 1→1,12.
- **Motion blur em câmera 3D** (cards, celular, frascos): `rotationY 55, rotationX 12, z −600, x 260, blur 26px` → 0 em 0,7 s expo.out.
- Light leak (seus clipes de luz, screen, opacidade .7, 0,56 s) na entrada de cada B/R/T.

## Tipos de momento
| tipo | o que é | camadas |
|---|---|---|
| D | expert sozinho | vídeo do avatar + legenda pop |
| F | card/número/produto/celular na frente do expert | expert com `blur(22px) brightness(.6) saturate(1.2)` + `.fdark` (radial azul) + conteúdo |
| M | lettering curto centralizado (golpe) | igual F, conteúdo descido 520 px |
| T | lettering de impacto sobre 3D | 3D em tela cheia + `.tgrad` (escuro no terço de cima) + kicker + título no topo |
| B/R | b-roll em tela cheia | vídeo + gradiente; pode ter lettering que **bate** na frase ou chip embaixo |

## Tipografia e cores
- Título: Inter 900, −0,03 em, 132 px (big) / 170 px (huge), glow azul. Kicker: Archivo Narrow 700, 44 px, espaçamento .3 em, amarelo.
- Itálico de apoio: Newsreader Italic, amarelo, com glow. Números: Inter 900 380 px com **extrusão** (text-shadow em camadas 4/8/12/16 px).
- Paleta: amarelo #FFD23F, vermelho #FF4B3E, azul #2F7BFF, fundo #050914 → #12234a (radial).
- Cards de vidro: gradiente branco 14→4 %, borda 2 px branca 25 %, sombra 0 30 80. Calendário/contador anima o número (onUpdate).
- ✕ desenhado (SVG stroke-dashoffset) + dessaturar o 3D embaixo quando a fala nega algo.

## Psicologia das cores (pedido do usuário, 30/10 — NNN_XX curta)
Cor tem função, não enfeite. **Verde #2BD67B / #21c26b** = ganho, solução, preço novo, "✓" e palavras positivas (deep sleep, repair,
dips, protected, save, refund, together, younger). **Vermelho #FF4B3E / #D7262E** = dor, risco, preço antigo, "✕" e palavras de perigo
(heart attack, non-dipper, floating, too late, high alert, runs out, disappears). **Amarelo #FFD23F** = neutro/ênfase (kicker, palavra
falada, números sem juízo). Azul = palco. Aplicação: (1) **preço** — preço cheio sempre vermelho com risco desenhado (branco, entra na
palavra), oferta sempre verde grande com extrusão + setas verdes; o valor leva o `$` e centavos viram `$0.53`, nunca `53¢`; nunca escrever a
palavra "riscado" na tela (bug da V2). (2) **chips e listas** — ✓ em círculo verde, ✕ em círculo vermelho; chip com ✓/benefício fica
verde, chip de risco fica vermelho. (3) **números** — `[g]`/`[r]` no storyboard escolhe verde/vermelho; percentual negativo ganha anel
vermelho. (4) **legenda** — a palavra falada fica amarela, mas se estiver na lista positiva fica verde e na negativa fica vermelha
(listas POS1/NEG1/POS2/NEG2 no build; bigramas "deep sleep", "heart attack"). (5) **título com cor escolhida no storyboard não é
recolorido** pelo automático (senão "NO REPAIR SHIFT" fica com REPAIR verde). Comparação de decisão = dois cards de vidro: verde (clicar)
× vermelho (não clicar).

## Legenda
Montserrat 900, 80 px, caixa alta, contorno preto 3 px, top 1330 px; grupos de até 3 palavras ou até a pontuação;
a palavra falada fica amarela (#FFD23F) e cresce 1,08. Pop de entrada 0,16 s back.out. Sem legenda sob T/F/M e sob b-roll com texto.

## Motion graphics recorrentes
- Celular de pedido em processamento (abertura "don't close this page"), alerta vermelho tremendo.
- Mensagem recebida no celular (depoimento em texto): bolhas entram na hora da frase com pop.
- Produto: deslize da direita com rotationY e brilho amarelo + pílula com o nome, 2,4 s, a cada menção (≥ 6 s de intervalo).
- Relógio em contagem regressiva (05:00) por 5 s quando a fala pede "alguns minutos".
- Preço: frasco + preço cheio riscado (traço vermelho animado) → card do kit sobre b-roll do kit → "$X TOTAL" + setas verdes pulsando.
- CTA: pílula laranja-amarela (gradiente #FFD54A→#FF9A1F, texto escuro Montserrat 900) + seta redonda amarela pulsando; fixa no fim.
- Selo de garantia validado (`kit/selo_garantia_1year.png`) entra com scale 2,2→1 e impacto.

## B-roll
- Dor: cenas fotorreais com o mesmo casal/personagem (identidade travada pela imagem de referência), expressão natural, sem nudez.
- Mecanismo: 3D anatômico clínico em fundo preto, variando a escala (corpo inteiro → órgão → tecido → interior do vaso → macro).
- Metáfora da copy (banheira, rodovia…): 1,5–2 s do plano real e **match-cut** para a versão anatômica.
- Produto: packshot com o mockup oficial (Nano Banana Pro), kit, frasco na mão, caixa chegando em casa. Kling gira o rótulo:
  usar ida-e-volta (primeiros 2,4 s + reverso) para o nome ficar sempre legível.
- Orgânico do TikTok só quando acerta melhor que IA (lab, alimento real); nada com marca d'água.

## Áudio
Voz do avatar a 1,0; sua trilha a .34 subindo a .8 nos últimos 2,5 s; SFX: swish .035–.06 nas entradas de b-roll,
impacto .09 nos golpes, pop .05–.09 nos cards, clique .18 em listas, ding no contador, cash no preço, bass no reveal.
Master: loudnorm 2 passadas −16 LUFS, TP −1,5, AAC 256k 48 kHz (`templates/master.py`).

## Critérios de qualidade (antes de entregar)
1. `hyperframes check` sem erro (avisos de blur são esperados; conferir quadros pretos no render).
2. Snapshot de cada cena nova; nada fora do quadro (selo, chips longos), sem texto sobre texto.
3. Fala ↔ imagem: cada asset entra na frase que exemplifica; o lettering bate na palavra.
4. Nenhuma footage repetida; nenhum b-roll cortado no meio da frase; nenhum quadro de Kling com pose estranha.
5. Claims: nada de "prescription/Rx", selo FDA, antes/depois ou imagem que sugira remédio.
6. Render: 1080×1920, 25 fps, duração = áudio; −16 LUFS; varrer quadros pretos (`blackdetect`).

## Quantidade falada = quantidade na tela (usuário, 30/10/2026)
Toda quantidade falada aparece na tela igual à fala: "6 bottles" → cena com 6 frascos contáveis + lettering "6 BOTTLES" no padrão visual (cores/chips). Vale para dias, preços, anos de garantia. No check final, conferir que o número de objetos na imagem bate com a fala.

## Tamanho do frasco único e realista (usuário, 30/10/2026)
Frasco sempre na escala real e igual em todo o vídeo (sem frasco gigante nem miniatura). Prompt com âncora de escala ("real-world scale, ~4 inch tall bottle, fits in an adult hand, same height as a coffee mug"); vários frascos na cena = todos do mesmo tamanho; no HyperFrames, escala fixa em px por tipo de cena. Conferir no qc e no check final.

## Frasco por composição quando a IA não segura (usuário, 30/10/2026)
No NNN_XX o GPT Image variou o rótulo e a escala do MarcaG (conta-gotas) e errou a contagem de frascos (5 em vez de 6). Regra: frasco com rótulo que a IA não reproduz fiel entra por composição do packshot oficial recortado (sombra de contato, luz e grão casados, escala fixa). No qc, contar os frascos e comparar cada rótulo com o oficial em zoom.

## Rodada 30/10 (MarcaK Upsell 01, NNN_XX) — pedidos do usuário
- Lettering de destaque ATRÁS do expert agora é pedido (no consultório, não no palco azul): recorte alpha local (`hyperframes remove-background`) só dos trechos, texto no topo (2 linhas, 132 px), punch-in desligado no trecho para a cabeça não cobrir o texto; `hyperframes check` acusa `text_occluded` se uma linha ficar 99 % atrás.
- Transição: dissolve curto (0,3 s) + luz ao sair/voltar para o expert; entre duas telas, corte com luz.
- Reaproveitar b-roll de jobs anteriores do mesmo produto antes de gerar (manter um casal só por vídeo).
- Studio da empresa lento/502 em pico: disparar em paralelo com o MESMO .tsv (mesma idempotency key) e repetir o que der 502.

Ver também: REGRAS_JHON_3010.md (regras gerais de upsell do usuário, 30/10/2026).

## Trocar o nome do produto na fala (sem refazer avatar) — validado 30/10 no UP2 MarcaP
- TTS da frase de contexto com o nome novo, mesma voz/modelo/ajustes. Corte por DTW (log-mel) entre a frase nova e a original: o corte cai onde as duas ainda são iguais; a borda de entrada desce até o fechamento do "P"/consoante (vale de energia), senão sobra "Pro". Rubberband até 1,2×; o resto vira respiro antes do nome. Crossfade 5 ms/12 ms, RMS igualado. Script: MarcaP-up2/edicao/trocar_palavra.py; QC Whisper ±2 s sem prompt.
- Alinhamento por caractere da ElevenLabs erra o início da palavra em até 0,2 s; Whisper erra as bordas em ~0,1 s — nenhum dos dois sozinho serve para cortar.
- Onde a boca do expert/depoente estaria visível no nome, cobrir com card/b-roll do frasco (~0,3 s antes até 0,45 s depois).
- Nível da palavra trocada: conferir pelo p90 dos picos de 10 ms (método do revisor) contra a frase seguinte, não só por loudness momentâneo; em depoente com pausa antes do nome, o ebur128 mascarou 6 dB de diferença (30/10, Rick).

## Legenda × lettering (usuário, 30/10 noite — 349)
Nunca os dois juntos: enquanto lettering, chip, card, tela de preço, tarja ou card de abertura estiver na tela, a legenda some; volta quando o lettering sai. Sem legenda acima do botão fixo.
Glow (deep glow) em text-shadow na cor da palavra; filter drop-shadow só em chip/card (vira caixa em título).
B-roll curto: até 0,8×; nunca ida-e-volta.

## Régua de escala do frasco (usuário, 30/10 — medida real, substitui qualquer régua anterior)
- Frasco de cápsulas 300 ml (ex.: MarcaM): **13 cm de altura com a tampa × 6,9 cm de diâmetro** (≈1,9 : 1).
- Conta-gotas 1 fl oz (ex.: MarcaG): 0,9× o frasco = ~11,7 cm com a tampa → CC ÷ frasco 0,81–0,99.
- Referências na mesma cena (tolerância ±10 %; entre frascos da mesma cena ±3 %):
  - mão adulta 18–19 cm → frasco ÷ mão ≈ 0,7; os dedos envolvem ~2/3 da circunferência, não fecham; o frasco é um pouco mais estreito que a palma (~8,5 cm). Medida prática: quatro dedos empilhados (~8 cm) ≈ 60 % da altura do frasco.
  - caneca padrão 9,5–10 cm → frasco ÷ caneca 1,3–1,35 (faixa 1,17–1,49). O frasco É mais alto que a caneca.
  - caixa de depósito 30–40 cm → frasco ÷ caixa 0,33–0,43.
- Método: grade de pixels sobre o quadro do meio de cada cena; medir só contra referência na MESMA profundidade (objeto atrás parece menor). Folha de contato antes/depois em `_SAMURAI/escala_frascos*.jpg`. Só passa o que cair na faixa.
- Prompt (GPT Image 2.5): escrever os tamanhos reais em cm de TODOS os objetos de escala, pôr a referência ao lado e na mesma profundidade, e dizer "use the attached photos ONLY to copy the label design, NOT the size". O GPT amplia o produto de referência; com caixas, pedir caixa grande (45 cm) para cair em ~0,36. Medir ANTES de animar.
- (31/10) usuário apertou para a PONTA DE BAIXO da faixa: frasco ÷ caneca 1,15–1,25; ÷ mão 0,6–0,65; ÷ caixa de depósito 0,30–0,35. Caixa de envio de 6 potes ≈ 30×20×15 cm, frascos ≤ 60 % da área interna com kraft visível. Câmera mais aberta. Estoque em fileira única, nunca empilhado.
- Razão altura ÷ largura do pote real = 1,9. O GPT Image faz o frasco MAIS ESGUIO (2,2–2,6), não mais gordo; o PNG oficial já mede 2,1. Medir H/L junto.
- Truque que funcionou: caneca "11,3 cm, tall" encostada no frasco com as bases niveladas → 1,17–1,20. Caixas de depósito "50 cm" → 0,30–0,35. O conta-gotas CC sai sempre grande demais dentro da caixa de 6+1 (1,0–1,25 × NR) mesmo com tamanho em cm no prompt.

- **Tamanho do produto:** ver `PADRAO_TAMANHO_PRODUTO.md` + `regua_tamanho_produto.png`. Ouro = cabeceira NNN_XX (pote 28,5 % do quadro em plano aberto de mesa).
- (31/10, 362) Presentes: cada gift com capa própria gerada pronta no GPT Image 2.5 (série: mesma moldura/filigrana, cor por gift; play em filigrana nas vídeo-aulas; e-book com ornamento — casal em traço é barrado pelo filtro ou arrisca o Meta). Entrada: capa grande ~1 s sobre a cena do casal desfocada, depois vai ao canto; nunca capa sozinha em fundo vazio. Tela do tablet nunca aparece.
- (31/10, 362) Fala "N bottles" → tela só com os N frascos (packshot sem caixa) + número grande, legenda embaixo. Caixa premium do kit (ref do usuário: 6 dentro + 3 fora) nas telas de preço/oferta/resumo e no "envio do restante".
- (31/10, 362) Logo do produto: wordmark recortado do rótulo oficial (letras brancas, sem raios) + faixa do rótulo, no topo de todo card, nas telas de preço, presentes e CTA.

## Troca de oferta numa versão aprovada (31/10, NNN_XX V4)
- Refazer só as FRASES que mudaram, não o bloco inteiro: cortar o avatar aprovado no vale de energia do áudio entre frases (fim acústico = última letra/dígito, não a pontuação) e gerar só os trechos novos (TTS → STS → Avatar IV). Plano em JSON (mantido de/até frase × novo) e conferência do texto montado contra a copy antes de gastar. Corte cuja pausa original < 0,15 s: puxar a frase vizinha para o trecho novo.
- Emenda mantido × novo: pausa alvo 0,40 s (mediana natural entre frases); só o lado novo ganha silêncio, ANTES do lip sync. Punch-in forçado em toda emenda de bloco.
- Depoente seguido de cena a < 0,7 s: adiantar a cena seguinte para o fim do depoente (esticar o depoente congela o rosto).
- Lista em vidro: o vidro entra junto com o 1º item (vidro vazio na tela = reprovado pelo conferente).
- Ler/cortar mp4 direto da pasta do Drive corrompe a leitura (NAL inválido, zeros): copiar o projeto para pasta local, trabalhar lá e sincronizar de volta.
- Depoentes: início/fim sempre pelo bloco (`ini_bloco`), nunca tempo absoluto — qualquer mudança antes desloca tudo.

## Produto dentro da imagem e cards sem expert desfocado (usuário, 31/10 — NNN_XX V4)
- Frasco SEMPRE gerado dentro da cena (GPT Image 2.5 flare com o mockup oficial como 1ª referência + bloco de escala + LABEL LOCK no fim) e animado no Kling com câmera travada. Nada de PNG colado por código, nem na tela do celular (use um quadro do kit real gerado). Conferir o rótulo segundo a segundo no Kling: quando ele gira, usar só o trecho bom em ida-e-volta.
- Split de meses (padrão MarcaL): cada painel é um vídeo de cena real com os dois frascos no terço central da largura (o painel de 356 px mostra ~50 % da largura da imagem 9:16 quando a altura é ~1200 px; pedir "both bottles inside the central 40% of the width").
- Card sobre o expert desfocado não passa: o card ganha fundo de tela cheia que diz o mesmo (título no terço de cima, `.fbgv ~ .fs` com padding-top ≥ 240 px para não bater na tarja "VIDEO MESSAGE"). Card tipo M ("st f meio") desce 520 px — com fundo, zerar o deslocamento (`.st.f.meio .in:has(> .fbgv)`), senão sobra uma faixa do expert em cima.
- Trocar card por expert nítido cria trechos do expert > 8 s em sequência: medir com o "doutora sozinha" do build e dar fundo aos cards que fecham trechos longos.
- Depoente como fundo de card: usar quadro PARADO com boca fechada (push lento), nunca o clipe falando mudo.
- Armadilha: `FALLBACK_BR` guarda a função antiga; ao redefinir uma cena especial, atualizar também o fallback, senão a cena B/R sem vídeo volta para a versão velha.
- Armadilha de shell: `until ! pgrep -f "build_up4.py"` casa com o próprio comando de espera e nunca termina; usar o PID ou run_in_background.
- (31/10, MarcaL B) **Legenda 4:3 de linha única comprida** (≥ ~900 px na largura do Chrome) quebra em 2 linhas equilibradas: `max-width` inline ≈ 0,74 × largura + 44 px (medir com Montserrat 700 × 0,96). Quebra manual (`<br>`) quando a automática separa um destaque colorido ou joga travessão para o começo da linha.

## 01/11 — NNN_XX curta V2 (troca de oferta numa versão aprovada, segunda versão do mesmo job)
- **Avatar já gerado em outra versão com a MESMA fala = reaproveitar** (copiar o mp4 final + alin, cortar na frase se preciso): a curta usou 9 trechos da V4 longa e só gerou 3 Avatar IV (US$ 2,66). Conferir o texto do alin palavra a palavra antes — uma vírgula/frase diferente ("…six months, so you have…" × "…six months. That gives you…") obriga trecho novo.
- **Ler as cores de uma aba do Doc sem receptor:** o Docs bloqueia `fetch` para 127.0.0.1 (CSP) e `DOMParser` exige `trustedTypes.createPolicy`. Montar o texto marcado (<G>/<R>) no próprio JS e devolver em pedaços de ≤ 950 caracteres (o retorno trunca); conferir a fala montada por SHA-1 de cada linha contra o export.
- **Lettering na palavra, sem teto de 55 % da cena**, quando toda tela tem imagem por trás: âncora = palavra mais distintiva do item (a mais tardia das palavras do item dentro de 2,5 s — "SAME LABEL" ancora em "label", não no 1º "same"), procurada depois do item anterior; palavra só de PARE ("YOU") também ancora. Títulos de T e letra_em/chip de b-roll idem. Medir com um script (entrada `opacity:0` × alin); o conferente só aceitou depois de 6 rodadas.
- **Rosto sob o título/lista no fundo de tela cheia:** descer o vídeo (translateY 260–620 px) com `mask-image` em degradê no topo (sem a borda dura), em vez de trocar o plano.
- **Vidro de lista** entra junto com o 1º item; rótulo do anel (NON-DIPPERS) entra com o anel, não com a cena.
- **Kling com rótulo girando no packshot:** usar o 1º quadro como still com push (`cc_nr_mao97_parado`).

## Dinâmica + lettering Katana (usuário, 02/11 — padrão salvo)
Ver `PADRAO_DINAMICA_KATANA.md` (regra dos 2–3 s, batidas de câmera, lettering Katana Dark-Glass, SFX).
