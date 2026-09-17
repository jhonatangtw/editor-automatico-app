---
name: motion-viral-jhon1
description: Inicia, planeja e executa demandas de motion no Adobe After Effects a partir de takes de talking head + copy, construindo tudo dentro do projeto aberto via ExtendScript e Tools PRO (MCP) — questionário de briefing, leitura da copy com comentários e pedidos de insert do copywriter, análise de referências (Pinterest / vídeo pronto), transcrição por palavra, mapa de inserts, cartões, splits, lettering, legendas, fundo desfocado, render e QA por quadro. Use SEMPRE que o usuário pedir para iniciar uma demanda de motion, editar ou montar um criativo/AD/Reels no After Effects, aplicar uma referência de motion, ler uma copy com comentários e inserts, usar o Tools PRO para construir animações, organizar um projeto de motion, deixar um vídeo "mais dopaminérgico", trocar legendas por premium, reenquadrar tela dividida ou desfocar o fundo sob B-roll — mesmo que ele não diga "skill" nem "After Effects" explicitamente. NÃO é para conferir criativo pronto (QA) nem para gerar vídeo por IA.
---

# Demanda de motion no After Effects

Takes + copy → composição editável no `.aep` que está aberto, com cada elemento ancorado na palavra
falada e provado por quadro exportado. Regra-mãe: **a fala manda no motion, e o motion se prova por
PNG** — retorno de ferramenta não é prova.

## 0. Briefing: perguntar só o que falta

Cruze o pedido com o que dá para verificar no disco e faça, **numa única mensagem**, apenas as
perguntas ainda abertas do questionário em `references/questionario.md` (13 itens: demanda, pasta,
take, referência, vídeo local, Doc da copy, comentários, assets, Higgsfield, formato, projeto/comp,
entregas, regras). Falta secundária → suposição razoável, registrada no plano. Pare **somente** sem
pasta, copy ou material principal.

## 1–9. O fluxo (detalhe em `references/fluxo-detalhado.md`)

| # | Etapa | Trava para avançar |
| --- | --- | --- |
| 1 | **Validar** — caminhos existem, `ffprobe` em tudo, originais intactos | inventário com veredito por arquivo |
| 2 | **Copy + comentários** — Doc inteiro, threads abertos e resolvidos, cada comentário ligado ao trecho; conflito → o mais recente, sinalizado | `COMENTARIOS_APLICADOS.md` + mapa de inserts (`references/mapa-de-inserts.md`) |
| 3 | **Referências** — link e vídeo local medidos (ritmo, tipografia, paleta, composição, transições, câmera, B-roll, legenda, SFX); acervo local em `references/acervo-motion.md` cobre o que a referência do cliente não cobrir; adaptar, não copiar | `ANALISE_REFERENCIAS.md` + gramática escolhida |
| 4 | **Takes** — áudio/enquadramento/performance; Whisper por palavra; copy alinhada à fala | transcript + âncoras; **nunca timecode estimado** |
| 5 | **Materiais** — o que está na pasta primeiro; Higgsfield só autorizado e só para o que falta; conferir antes de importar | todo asset visto e gravado na pasta da demanda |
| 6 | **Organizar** — `01_Footage … 08_Exports` na pasta e no projeto; nomes pelo trecho da copy | árvore criada, nada movido |
| 7 | **Executar no AE** — `lib/toolspro.sh tools/list` confirma a conexão; construção por `lib/rodar.sh` cena a cena com `report()` + `frame()` | frames de cada cena revisados |
| 8 | **QA** — finalização pelo Tools PRO, frames dos momentos-chave, janelas, sincronia, save, `lib/render.sh`, integridade | render válido no ffprobe |
| 9 | **Relatório** — demanda, take, referências, comentários aplicados, inserts, assets, animações, caminhos, pendências | — |

Se o Tools PRO/AE não responder: dizer **exatamente** o que falhou e entregar tudo que não depende
dele (análise, transcrição, mapa, assets, plano).

## Gramáticas disponíveis

| | Quando | Onde |
| --- | --- | --- |
| **STUDIO** | talking head do próprio Jhon, motion tipográfico premium | `IDENTIDADE.md` |
| **PODCAST + split + caixa** | avatar em podcast, hook em tela dividida, B-roll de prova | `references/formato-podcast-split.md` |
| **EDITORIAL** | papel + luz de janela, fantasma condensado, reveal letra a letra | mesma referência, seção *Gramática EDITORIAL* |

## Acervo local de referências

15 referências classificadas (produto+vidro, oferta/preço/CTA, prova científica, lettering/legenda,
editorial-documentário, colagem dopaminérgica, carrossel de cartão). Mídia em
`~/Documents/Referencias de Motion/` + mosaico de 9 quadros por peça em `_mosaicos/`; catálogo por
arquivo em `~/Documents/Referencias de Motion/INDICE.md`. **Tabela "cena da copy → referência →
função" em `references/acervo-motion.md`** — consultar na etapa 3, antes de pedir referência nova.

A referência do cliente decide a gramática. **Camada dopaminérgica** (lettering creme/preto,
câmera 3D, objeto na palavra, zoom por frase, pop por palavra), **legenda premium** e **fundo sob
cartão** entram por cima de qualquer uma — sempre numa comp duplicada (`*_DOPA`) para a versão
limpa sobreviver. Versões: `<CODIGO>_MAIN`, `<CODIGO>_DOPA`, `<CODIGO>_DOPA2`.

## Construir no AE

```bash
MVJ_COMP=<CODIGO>_MAIN MVJ_FPS=30 lib/rodar.sh "<pasta-da-demanda>" cenas/01_setup.jsx
```

O runner injeta caminhos, concatena `lib/ae_lib.jsx` (base, 62 fn) + `lib/ae_podcast.jsx`
(podcast/dopa/editorial, 36 fn), fecha em try/catch e devolve o log. Vocabulário principal:
`talkingHead` `cardPhoto` `cutFull` `split` `reenquadrar` `punch` `zoomPorFrase` `chevron`
`legendasCaixa` `legendasPremium` `legendasPop` `calar` `fundoSobCartao` `camera3D` `camMove`
`cenaDopa` `palavraDopa` `objeto3D` `cenaEditorial` `chave` `serifa` `revelaLetras` `flashBranco`
`anel` · base: `precomp` `text` `pill` `dashedCircle` `line` `drawIn` `blockIn` `popIn` `slideOut`
`sweep` `placeInMain` `report` `frame`. Modelos em `exemplo/01–04`.

Regras dentro do AE: safe margins (100 px topo, 260 px rodapé); legenda longe de olhos, boca e
costura; entrada + permanência + saída para tudo; imagem sobre a locutora → `fundoSobCartao()`
(blur 22 px + preto 40 %, rampa 8 f, só na janela); tela dividida → medir o rosto (YuNet) e
`reenquadrar()` sem cortar cabeça, fones ou queixo; **só palavras da copy** na tela.

## Legenda, voz, assets, render

- Legenda: blocos de 1–2 palavras (≤ 0,6 s), da copy alinhada pelos tempos do Whisper, nunca
  atravessa corte, cala sob lettering. Caixa (`legendasCaixa`) ou premium (`legendasPremium`).
  Detalhes e Voice Changer: `references/voz-e-legenda.md`.
- Assets de IA: `references/prompts-asset.md` + `lib/recortar_gradiente.py`.
- Render/QA: `lib/render.sh` · `lib/conferir_render.py frames|sync|timbre` · `lib/conferir_voz.py`.
- Antes de culpar o projeto: `references/armadilhas-extendscript.md` (13 armadilhas do AE por
  script, render e Tools PRO).

## Exemplo real

`references/exemplo-ad04.md` — briefing, decisões, números e o que deu errado numa demanda
completa (3 versões). Use como referência de formato, não como valores fixos.
