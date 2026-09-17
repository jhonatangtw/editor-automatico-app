# Motion-Viral-Jhon1 — manual para a equipe

Skill do Claude Code que monta um Reels/AD vertical **dentro do After Effects**, por script, a partir de
takes de talking head + copy. Nada é posicionado "no olho": cada evento visual nasce de um transcript
palavra a palavra, e cada cena é provada por quadro exportado.

Versão 2.0 — 10/09/2026. Fluxo universal: começa por um questionário que só pergunta o que falta. Construída e validada em dois jobs reais: Reels "dois criativos idênticos" (Jhon)
e AD04 LeafTide (podcast Rogan + Dra. Rhonda), este em três versões (limpa, dopaminérgica, editorial).

## 1. O que ela entrega

| Entrada | Saída |
| --- | --- |
| pasta com takes (`lip/`), B-rolls (`broll/`), copy no Google Docs, 1–2 referências (Pinterest / MP4 pronto), projeto `.aep` **aberto** | comp principal editável (+ comps `_DOPA`), precomps nomeados pelo trecho da copy, pastas `01_Footage…08_Exports`, render de revisão, frames de conferência e provas de sincronia, relatório |

## 2. Instalação (5 min)

```bash
unzip motion-viral-jhon1.zip -d ~/.claude/skills/
cp ~/.claude/skills/motion-viral-jhon1/fontes/*.ttf ~/Library/Fonts/
pip install faster-whisper Pillow numpy opencv-python
python3 ~/.claude/skills/motion-viral-jhon1/verificar.py      # tudo verde = pronto
```

Precisa de: After Effects 2026, ffmpeg, Python 3.9+. Opcionais: `yt-dlp` (baixar referência),
`higgsfield` CLI (gerar objeto que falta), chave ElevenLabs em `~/.config/hw-creative/.env` (trocar voz).
Na primeira execução o macOS pede permissão de Automação (Terminal → After Effects).

## 3. Como pedir (no Claude Code)

A skill começa cruzando o que você disse com o que está no disco e pergunta, **numa mensagem só**, o que
ainda falta (pasta, take, referência, Doc, comentários, assets, Higgsfield, formato, projeto/comp, entregas,
regras). Quanto mais completo o pedido, menos perguntas.

Abra o projeto no AE e diga, por exemplo:

> Use a skill motion-viral-jhon1 para montar o AD04. Takes em `~/Demanda/AD04/lip`, B-rolls em `broll`,
> copy no doc <link>, referência de motion <pin>, referência prática `<arquivo>.mp4`.

Frases que acionam: *"monta esse reels"*, *"coloca motion nesses takes"*, *"constrói no After"*,
*"deixa mais dopaminérgico"*, *"legendas premium"*, *"troca a voz pela minha"*, *"reenquadra o locutor"*,
*"desfoca o fundo sob os cartões"*.

## 4. As oito etapas (cada uma tem uma trava)

1. **Medir a referência** — frames extraídos, não impressão. Registra ritmo, tipografia, paleta, transições.
2. **Decupar os takes** — Whisper por palavra + mapa de silêncio. Os arquivos da pasta são *segmentos*
   (hook, resposta, body), não alternativas. Corte sempre em silêncio medido.
3. **Plano de cenas** — cada frase tem cena *ou* motivo escrito de ficar fora. 25–40 % coberto; rosto
   sempre volta entre cenas.
4. **Assets** — só quando o quadro não resolve. B-roll com número no quadro tem que bater com a copy.
5. **Construir no AE** — `lib/rodar.sh` executa cada cena e devolve o log; `report()` + `frame()` provam.
6. **Voz** (opcional) — Voice Changer ElevenLabs; trava: desvio de palavra ≤ 100 ms.
7. **Legenda** — 1–2 palavras por bloco, ≤ 0,6 s, nunca atravessa corte; cala sob lettering.
8. **Render + revisão** — `lib/render.sh` (recusa render duplo, valida com ffprobe); folhas de contato
   do vídeo inteiro; prova de sincronia 4 f antes / 6 f depois de cada palavra-âncora.

## 5. As três gramáticas

| | Quando usar | Marcas |
| --- | --- | --- |
| **STUDIO** | talking head do próprio Jhon | estúdio cinza-claro, Inter Itálica + Playfair, numeral fantasma, fita âmbar, silhueta desfocada |
| **PODCAST + split** | ad com avatar em podcast | hook em tela dividida (costura 0,49 H), caixa verde `#23500D` Nunito ExtraBold 60, cartão com borda branca e blur-in, prova em tela cheia |
| **EDITORIAL** | versão "premium calma" | papel creme + luz de janela, fantasma Anton, Fraunces + Montserrat Bold com reveal letra a letra, ✦✦✦, flash/anel |

**Camada dopaminérgica** (sempre em comp duplicada `*_DOPA`): cena de lettering creme/preto com
vermelho `#E0212A`, câmera 3D, objeto 3D pousando na palavra, zoom alternado por frase, pop por palavra.
**Legenda premium**: pílula fosca + Montserrat Bold + acento Playfair dourada com glow.
**Fundo sob cartão**: blur 22 px + preto 40 %, rampa 8 f, só enquanto há imagem sobre a locutora.

## 6. Regras que não se negociam

- **Só palavras da copy** na tela. "three days" não vira "3 days".
- **Nunca timecode estimado.** Toda âncora vem do transcript; a legenda vem da copy alinhada pelos tempos.
- **Quem cria e abre o projeto é a pessoa.** A skill escreve no `.aep` aberto e nunca apaga original.
- **Prova por quadro.** Retorno de ferramenta não é prova — PNG exportado é.
- **Um render por vez.** Dois `aerender` no mesmo arquivo produzem MP4 corrompido.
- **Não rodar `ae_organizar` do Tools PRO** — desmonta a árvore de pastas da demanda.

## 7. Estrutura entregue

```
<demanda>/
  00_brief/   ANALISE_REFERENCIAS.md · PLANO_MOTION.md · COMENTARIOS_APLICADOS.md · transcripts/
  01_Footage  02_Audio (legendas .srt/.json)  03_Broll  04_Imagens  05_Assets_IA  06_Precomps  07_SFX
  08_Exports/ <nome>_revisao_vN.mp4 · frames_conferencia/ (+ sync/)
No AE: <MAIN> · <MAIN>_DOPA · <MAIN>_DOPA2 · 06_Precomps/PC_* nomeados pelo trecho da copy
```

## 8. Onde está o quê na skill

| Arquivo | Conteúdo |
| --- | --- |
| `SKILL.md` | o método: questionário, 9 etapas com trava, gramáticas |
| `references/questionario.md` | as 13 perguntas do briefing, como verificar cada uma sozinho e o que assumir se faltar |
| `references/fluxo-detalhado.md` | as 9 etapas por extenso, com a trava de cada uma |
| `references/mapa-de-inserts.md` | modelo do mapa trecho → timecode → insert → asset → status, com exemplo real |
| `references/exemplo-ad04.md` | uma demanda completa como exemplo (briefing, números, o que deu errado) |
| `IDENTIDADE.md` | identidade STUDIO (paleta, fontes, movimento, sombras) |
| `references/formato-podcast-split.md` | gramática podcast, dopaminérgica, editorial, legenda premium, fundo sob cartão, reenquadramento |
| `references/armadilhas-extendscript.md` | 13 armadilhas do AE por script + render + Tools PRO |
| `references/voz-e-legenda.md` | Voice Changer, limites da conta, regras de legenda |
| `references/prompts-asset.md` | prompts de objeto (Nano Banana Pro) e recorte |
| `lib/ae_lib.jsx` · `lib/ae_podcast.jsx` | 62 + 36 funções de composição |
| `lib/rodar.sh` · `lib/render.sh` · `lib/toolspro.sh` | executar cena no AE / renderizar com trava / falar com o Tools PRO |
| `lib/conferir_render.py` · `lib/conferir_voz.py` | provas de sincronia, timbre e frames |
| `exemplo/01–04` | setup, cena STUDIO, body podcast, lettering dopa/editorial |
| `verificar.py` | checagem de instalação |

## 9. Tempo de referência

Reels de 38 s (STUDIO, 8 cenas, voz trocada): ~45 min. AD de 134 s (podcast, 3 versões, 3 objetos IA,
2 rodadas de ajuste): ~2 h de sessão, sendo ~1 h de render acumulado.
