# Padrão copy de referência (DA) — upsell 4:3 com versões de preço

Consolidado do MarcaE NNN_XX (22–23/10/2026) e do Upsell #1 MarcaK (29–31/10/2026, 7 versões A–G aprovadas pelo usuário).
Vale para toda demanda de upsell do copywriter **copy de referência** (sufixo `_DA`). Complementa `LICOES.md` (MarcaE) e
`ESTILO_UPSELL.md`. Projeto de referência vivo: `<pasta de trabalho>/_SAMURAI/MarcaK-up1/` (`edicao/build.py`,
`scripts/build_versoes.sh`, `scripts/render_final.sh`, `ledger.md`).

## Como o copy briefa
- Manda um **upsell de referência** (até aqui o MarcaE NNN_XX) e pede para **espelhar cena a cena**: a referência manda
  em sequência, ritmo, momento dos destaques, tipo de b-roll e estilo de legenda. Mapear a referência antes de tudo
  (`ref/mapa_ref_bruto.tsv`, `ref/cortes.txt`) e montar o storyboard com o tempo de cada cena da referência ao lado.
- **Reaproveitar** o que der (acervo do produto, DTC VSL, MarcaE/MarcaB recortados de 9:16 para 4:3) antes de gerar.
- Pede **100% real, sem cara de IA**. Avatar das depoentes pode vir de pins do Pinterest na copy.
- Copy em Google Doc com comentários + thread no Slack (às vezes com imagem do kit). Ler tudo, inclusive os comentários.
- **Muitas versões de preço** (MarcaK: A–G) em **4:3 1440×1080, 25 fps**. Só muda o trecho de preço/kit/CTA
  (no MarcaK, de ~320 s ao fim); o resto é igual em todas.
- **Não avisar o copy sobre a conta da oferta** quando o usuário disser isso. A fala segue a copy, a conta fica fora da tela.

## O que a cor e o produto seguem
- **Psicologia das cores vence a cor da referência** (verde ganho/preço da oferta, vermelho dor/preço cheio riscado,
  amarelo neutro), combinada com a identidade do produto. Listar os conflitos no relatório.
- Rótulo sempre do mockup oficial, conferido letra por letra (o GPT erra o 1º bullet — "Testostorone"; corrigir por
  script, `scripts/corrigir_bullet.py`). Frasco **em pé**, **um tamanho só** (30 cáps ≈ 11 × 6 cm, razão 1,79).
- Cor da cápsula confirmada com o usuário antes de gerar (MarcaK = **preta**).
- **Quantidade falada = quantidade na tela.** Se a conta frascos × preço não fecha, não mostrar número de frascos.

## Cenas que o padrão DA tem (e como saíram aprovadas)
- **Expert/apresentadora (Susan)** em 4:3 com **letterings premium atrás dela** (bbkatana + deep glow: camadas bloom,
  halo, core, sweep) e a Susan recortada por cima (`assets/susan_rec/*.webm`). Largura útil do lettering ≤ 360 px
  medida na fonte real (PIL mede ~10% menor que o Chrome); nada encostando na borda nem cortado pela cabeça.
- **Depoimentos em vídeo** com tarja nome·idade·cidade (o revisor marcou risco de compliance em depoente IA com nome e
  idade — decisão do usuário, perguntar).
- **Split café/almoço/jantar** (3 painéis 476×1080) **animado** — still parado reprovou ("take tem que ser animado").
  Cápsula preta + mão nos 3 painéis, rótulos no alto, fundo azul-marinho.
- **Envio/entrega no estilo MarcaE** (57 embalando, 65 fechando caixa, 66 entregador carregando caixas): aqui o usuário
  **pediu logo do produto nas caixas** — na bancada e nas prateleiras do fundo. Desde 31/10 isso virou regra para todo upsell
  (caixa com logo, padrão premium; ref. em `upsell-premium-916/(exemplo visual que não acompanha o app)). A 1ª rodada sem logo foi reprovada como "muito fake".
  Usar só o trecho do Kling em que o texto das caixas não deforma (66: 3–5 s).
- **Kit premium** (caixa aberta com nichos + frascos soltos em pé, mármore, sol lateral) — ver
  `referencias/kit_padrao_premium_jhon.png` do MarcaK. Card de preço translúcido com glow verde, título do kit no alto.
- **Transições de luz / light leak** sem nunca vazar o plano anterior na borda (`scripts/varrer_bordas.py`).

## Armadilhas técnicas que custaram retrabalho (HyperFrames)
- **Recorte congelado:** se o webm do recorte já começa no tempo do lettering, `data-media-start` = t0 − início real
  do webm (guardar em `inicio.json`), nunca t0 − início do bloco — o seek passa do fim e o quadro trava. Conferir
  medindo diferença de quadro no rosto (congelado ≈ 0; ok ≥ ~8).
- **Piscada/mancha na entrada do lettering:** stagger por índice da letra dentro de cada camada; blur no bloco inteiro.
- **Card/kit saindo em tempos diferentes** deixa o kit sozinho: cards e plano saem juntos.
- Vídeo maior que o plano em +0,1 s mostra **quadro vazio** no fim (split 33); b-roll que termina < 0,7 s antes da
  virada estica até ela.
- Render: `--workers 3` desde 31/10 (no MarcaK foi 1 worker, ~20 min por versão de 9 min); se texto sair vazio/piscando, volta para 1 e avisa o usuário; o shell pode cancelar (`render_cancelled_parent_exited`) — rodar
  desacoplado e conferir pelo arquivo final, não pelo processo. Antes de rodar as 7, conferir disco (cada master ~700 MB
  + bruto); apagar só temporário próprio.

## Fluxo de aprovação com o usuário
1. Prévia no HyperFrames (uma porta por versão: 3021–3027 = A–G). Nunca ferramenta de revisão.
2. Piloto do que é novo (ex.: lettering premium) antes de replicar nas 7.
3. usuário revê a timeline e aponta minuto a minuto; corrigir, **abrir a timeline de novo** antes de renderizar.
4. Só renderiza com o "pode dar render". Masters velhos → `entrega/_descartado/` com sufixo do defeito.
5. SFX reais (`real-sfx` + a sua biblioteca; o que faltar, `earshot`) só depois da imagem aprovada, mantendo −16 LUFS / TP −1,5.
6. Conferência dos masters (abaixo) e relatório com custo.

## Conferência obrigatória (com auxiliar)
Ver a seção "Conferente obrigatório" em `~/.claude/agents/samurai-upsell.md`. Checklist mínimo nos mp4:
duração e 25 fps · −16 LUFS e TP ≤ −1 · `blackdetect` 0 · recorte da expert se mexendo em cada lettering ·
nenhum vazamento de borda · nada cortado na borda · rótulo e contagem de frascos por versão · preço/CTA de cada versão.
