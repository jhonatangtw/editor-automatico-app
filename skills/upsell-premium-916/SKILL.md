---
name: upsell-premium-916
description: Edita um UPSELL DR 9:16 (vídeo pós-compra de nutra/saúde EUA, médico/especialista falando 8–10 min) no padrão premium aprovado pelo usuário no Upsell #2 MarcaK→MarcaN (NNN_XX, 28/10/2026) — avatar do especialista conduzindo, letterings de impacto sobre 3D anatômico que exemplifica a fala, cards/números em palco azul de marca com o especialista desfocado atrás, b-roll realista de dor e de produto, produto entrando quando o nome é falado, CTA pílula laranja + seta redonda + selo de garantia validado, motion blur em câmera 3D, light leak nas entradas, legenda pop. Use SEMPRE que pedirem "upsell 2", "edita esse upsell", "mesmo padrão do upsell do MarcaK/MarcaN", "upsell vertical premium", ou mandarem copy de upsell com expert falando para vídeo 9:16. Roda junto com a skill upsell-agente (pipeline de voz, avatar e mídia) e o agente IA Creator (Samurai) para storyboard e assets. NÃO é para upsell 4:3 com 3 preços e depoentes no estilo MarcaB (esse é a upsell-agente pura).
---

# Upsell premium 9:16

Padrão aprovado no **NNN_XX (MarcaK → MarcaN)**, depois de três rodadas de correção do usuário em 28/10/2026.
Projeto de referência (copiar e adaptar):
`Arquivo de Edição/01. Male Enhancement/MarcaK/OT/[281026][OT] NNN_XX [MarcaK] [Squad]/1 Projeto/upsell-MarcaN-NNNxx/`.
Os builds de jobs reais não acompanham o app: escreva o seu com a skill `hyperframes`, seguindo o padrão abaixo. Leia `references/PADRAO.md` (o padrão visual e de edição, medido) e
`references/REPROVADO.md` (o que o usuário reprovou — **ler antes de montar**).

## Pipeline (pasta do job no Drive: `1 Projeto/<slug>/`, `_SAMURAI/`, `5 Render/`)
1. **Ler tudo**: copy com comentários (Doc com abas: exportar a aba via Chrome logado
   `<link do documento>/export?format=txt&tab=<tab>` e gravar com receptor local; o `format=html` traz as
   imagens embutidas: rosto do expert, depoente, mockups), tópico do Slack (copy + task dos editores), upsell anterior do produto.
2. **Expert e voz**: rosto da imagem da copy (photorealism-prompts + GPT Image 2.5, mesma identidade, consultório) e voz
   clonada do upsell/VSL anterior do mesmo expert (ElevenLabs IVC sobre áudio isolado; medir semelhança ≥ 0,9 com
   VoiceEncoder). `eleven_v4`, stability .5 / similarity .85 / style .15, 192 kbps. Blocos de ~85 palavras, `_alin.json`.
3. **Avatar IV** (`or:heygen/avatar-iv`, 9:16 1080p) um clipe por bloco. Depoente em vídeo = selfie 9:16 + Avatar IV;
   depoimento citado em texto = **mensagem recebida no celular** (nome + idade inventados como na copy).
4. **Storyboard antes de montar** (agente IA Creator): tabela fala → cena (tipo D/T/F/M/B/R), asset, movimento, transição.
   Lista de assets novos com prompt pronto. Ver `references/STORYBOARD.md`.
5. **Assets**: 3D = GPT Image 2.5 fundo preto (prompt "Premium 3D medical animation render … Isolated on a pure black
   background … Octane … No text") → Kling v3.0 Pro 5 s, `generate_audio:false`. Produto = Nano Banana Pro com o mockup
   oficial como referência (nunca colar PNG em cena realista). Cenas de pessoas = GPT Image com a mesma identidade do casal.
   QC por folha de contato (primeiro e último quadro): rótulo, mãos, anatomia sem genitália, pose estranha no fim do Kling.
6. **Montagem** HyperFrames (node@24): copiar `templates/kit/` para `assets/` e pôr em `assets/` a sua trilha, os seus SFX e os seus light leaks (o kit traz só fontes, grão e selo), escrever o build,
   `hyperframes check`, snapshots por cena (um `--at` por vez), preview `--background` na porta 3002.
7. **Revisão** (sincronia fala↔imagem, legibilidade, continuidade, áudio, repetição de footage) → corrigir → render
   (`--workers 3` (3 workers — se algum quadro sair com texto vazio/piscando, volte a 1 (corrida de worker com `document.fonts.ready`)), saída local fora do Drive) → `templates/master.py` (−16 LUFS, TP −1,5) → QC de quadros pretos → `5 Render/`.

## Regras que não mudam
- Nenhuma footage repete na timeline (o build imprime `footage repetida: nenhuma`).
- Nunca palco vazio: lettering de impacto vai **sobre** um 3D/b-roll que exemplifica a fala; o resto vai centralizado
  sobre o expert desfocado no palco azul de marca.
- Sem react/recorte do expert no canto e sem lettering atrás do recorte (reprovado).
- Produto entra (desliza da direita com brilho, 2,4 s) toda vez que o nome é falado com o expert em tela.
- B-roll de 5 s pode esticar até 6 s (B) / 8 s (R) com rate ≥ 0,55; nunca cortar no meio da frase.
- B-roll com texto próprio fica sem legenda; legenda nunca sob T/F.
- Selo de garantia = `templates/kit/selo_garantia_1year.png` (o validado). CTA = pílula laranja-amarela + seta redonda.
- Mídia gerada vai para a pasta do job, nunca importar do scratchpad.

## Ferramentas (scripts/)
  `avatar <blocos_dir> <imagem> <ids.tsv> <pasta> [prompt] --so S01,S02` · `gerar <lote.json> <ids.tsv> <pasta>` · `baixar <ids.tsv> <saida>`.
  Idempotency key por item; rodar de novo só gera o que falta.
- `receptor_local.py <pasta>` — servidor em 127.0.0.1:8765 que grava POST; com o Chrome logado no Doc:
  `fetch(".../export?format=txt&tab=<aba>")` → `fetch("http://127.0.0.1:8765/copy.txt",{method:"POST",body})` (format=html traz as imagens).
- `tts_lote.py` (ElevenLabs com timestamps) e `qc_tts.py` da skill upsell-agente.

## Armadilhas
- **Animação de saída com opacidade some a cena inteira**: o helper `em()` só pode zerar a opacidade no instante 0 quando o
  `de` parte de `opacity:0` (entrada). Já corrigido nos dois builds; não reintroduzir `if "opacity" in para`.
- Build montado a partir do storyboard: o 1º item de cada tela entra na abertura; os outros na palavra-chave, no máximo até 55 % da cena — senão a
  tela fica só com o expert desfocado.
- Produto com nome em duas palavras na fala ("MarcaD"): casar o bigrama.
- Render de 19 min ≈ 40 min com 1 worker; varrer quadros pretos com `blackdetect` no master.

## Rodada 29/10 (MarcaK v3 e MarcaD V2)
- **Trocar a voz do expert sem refazer lip sync:** ElevenLabs speech-to-speech (`scripts/voice_change_sts.py <job> <voice_id>`) mantém o tempo (±40 ms); troca só o áudio dentro do mp4 do avatar (vídeo copiado). Gerar 3–4 candidatas no 1º bloco e medir F0 (expert ~50 anos: 105–120 Hz).
- **Depoimento = avatar ultrarrealista** (pedido do usuário; mensagem no celular foi reprovada no 346): selfie 9:16 em casa real, voz idosa profissional diferente para cada um, tarja nome·idade·cidade (borda vermelha), legenda do alinhamento do próprio depoente.
  Encaixe: achar a citação “…” no `_alin.json` do expert → TTS do depoente → `atempo` para caber exatamente no trecho (+0,15 s antes, +0,25 s depois) → Avatar IV → silenciar a voz do expert no trecho. O resto do vídeo não muda de tempo.
- **Legenda:** usar o fim da última letra (`ea`), não o fim com a pausa da pontuação (o amarelo ficava 0,2–0,3 s a mais).
- **Lettering 0,15 s antes da palavra** (o usuário achou atrasado): o helper antecipa todas as entradas.
- usuário (29/10): tela que fica muito tempo cansa — card > 8 s vira card curto + b-roll do desfecho; números (50 %) precisam de gráfico que explique (anel), prazos viram linha do tempo, golpes (TOO LATE) com flash + tremor + rachadura; produto sempre no padrão da foto validada (marmore, luz dourada, caixa branca), nunca frasco de outra marca nem selo inventado.

## Rodada 30/10 (MarcaD CURTA)
- Vão < 0,7 s entre duas cenas faz o expert piscar entre b-rolls: o build estica a anterior até a próxima (vale para depoente) e imprime quantos havia.
- Cores: ver "Psicologia das cores" no PADRAO.md; título com cor escolhida no storyboard não é recolorido. Duas telas na mesma cena: a 2ª entra com fade (senão o vidro vazio aparece antes).

## Rodada 29/10 noite (MarcaK Upsell 01, NNN_XX)
- **Depoimento com duração natural:** quando a citação é um bloco à parte na copy, tirar a citação da fala do expert e abrir no mp3 do bloco um vão do tamanho do TTS do depoente (+0,15 s / +0,25 s), remapeando o `_alin.json` (citação vira linear no vão, o resto desloca). Evita o `atempo` de 1,2× quando o depoente fala mais devagar que o expert. Script de referência no job 362 (`edicao/` + `ia/depoentes/_citacoes.json`).
- `edicao/valida_storyboard.py` (job 362) confere frase única/ordem, tetos, cards > 10 s, assets repetidos e proporção por tipo, e preenche a coluna de tempo a partir do TTS real.

## Rodada 29/10 (MarcaK Upsell #1, 4:3 espelho do MarcaE)
- **Antes de gastar, conferir se há provedor com saldo**: o Studio local (8790) só gera com chave do OpenRouter (Ajustes › Chaves do OpenRouter; em 29/10 estava vazia), o Fal do usuário pode estar "Exhausted balance" e o HeyGen do CLI pode estar no plano free. Sem nenhum desses, o caminho é pedir ao usuário (chave, recarga ou liberar o da empresa). Não usar o da empresa por conta própria.
- **Prévia antes do crédito**: monte o build com a voz final (TTS da ElevenLabs), a Susan como o quadro parado do avatar + áudio, os depoentes como cartão nome·idade + áudio e os b-rolls novos como placeholder. Abra no Studio para o usuário aprovar estrutura, cores e tempos antes de gerar avatar e b-roll.
- Upsell 4:3 com espelho cena a cena: dá para extrair o mapa exato da referência importando o build da referência e chamando `achar()` em cada BROLL (`ref/mapa_ref_bruto.tsv`).
- Reuso 9:16 → 4:3: recortar 1080×810 na altura do rosto (`cy` por clipe) e ampliar 1,33×. Casal em pé precisa de `cy` ≈ 0,27–0,32, senão corta a cabeça.
- Legenda por frase (padrão MarcaB/MarcaE) + psicologia das cores: tingir só as palavras-chave (verde ganho / vermelho dor), com uma lista NEUTRA para negações ("not 100% satisfied", "no worrying", "didn't have to stop halfway") e prioridade da frase mais longa ("wasn't firm enough" vermelho vence "firm" verde).
- **Lettering atrás do avatar (30/10):** máscara de pessoa com o Vision da Apple (`scripts/mascara_pessoa.swift` do job MarcaK-up1, sem código externo) → recorte VP9 com alpha (`recorte_susan.py`) dentro do `#cam-in`, com o lettering entre o vídeo e o recorte. Usar coluna empilhada ao lado da cabeça (Archivo Narrow), opaca, sem encostar no cabelo. RVM pelo torch.hub é bloqueado pelo modo auto.

## Rodada 30/10 (NNN_XX MarcaG → MarcaM)
- **Nunca rodar dois builds ao mesmo tempo:** o que terminar por último sobrescreve o index.html com o storyboard antigo.
- **Frasco 100 % por composição** (`COMP` no build): cena vazia (Kling câmera travada ou still) + PNG oficial com sombra de contato, sombra longa na direção do sol, reflexo no mármore, desfoque leve na fileira de trás, recorte inclinado na borda da caixa; mão pegando o frasco = `remove-background` na própria imagem da mão (dedos por cima do PNG).
- **Tipo A (lettering atrás do expert):** `hyperframes remove-background bloco.mp4 -o bloco.webm --quality best` só nos blocos com A; palco A = expert desce 330 px e 0,88×; título 118–170 px conforme o comprimento.
- **Depoimento como bloco próprio** (D01/D02 na trilha do avatar) é mais simples que encaixar por cima da fala do expert.
- **3D curto em cena longa:** versão ida-e-volta `_pp.mp4` em vez de câmera lenta.

## Rodada 30/10 noite (NNN_XX, finalização)
- Antes do render, varrer o index: todo `<video>` com `data-duration × rate + media-start > duração da mídia` congela → criar `<nome>_pp.mp4` (o build já troca sozinho).
- Revisor independente (agente sem as notas do editor, 140+ quadros) achou 6 graves que a revisão do próprio editor não viu (leitura sobre fundo claro, colisão título×card, legenda atrás da CTA). Rodar sempre antes do master.
- Trabalhar e renderizar numa cópia local do projeto (rsync de hyperframes/, edicao/, ia/voz, _SAMURAI) e devolver ao Drive só os arquivos mudados: o build é determinístico (index idêntico).
