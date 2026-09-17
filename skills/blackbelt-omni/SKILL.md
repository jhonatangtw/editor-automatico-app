---
name: blackbelt-omni
description: Gera prompts de vídeo prontos pro Google Flow / Omni Flash no estilo de motion "Black Belt" — talking head num estúdio escuro com cards de vidro flutuantes de contorno dourado, gráficos off-white, legenda karaokê e fala em português brasileiro. Cada clipe é standalone de 10 segundos com a edição já embutida. Use SEMPRE que pedirem "prompt pro Omni Flash", "prompt pro Google Flow", "clipe no estilo Black Belt", "vídeo com motion graphics", "criativo com cards flutuantes", "transformar essa copy em clipes", "fatiar esse roteiro em vídeos de 10s", "vídeo falando com overlay", ou mandarem uma copy dizendo que quer virar vídeo no Omni. Acione também para corrigir clipe que saiu errado (legenda queimada, fala corrida, grafia errada, voz duplicada, sem respiro) e para adaptar paleta ou duração. NÃO use para talking head sem overlay nem para engenharia reversa de vídeo de referência.
---

# Black Belt Omni

Prompts de geração de vídeo para o **Omni Flash** (Google Flow) na linguagem visual Black Belt: preto profundo, dourado como marcador de beat, off-white para conteúdo. O resultado é um clipe de 10 segundos que já vem editado — pessoa falando, cards entrando, respiro e frame final — em vez de material bruto pra montar depois.

## O que o Omni Flash aguenta

- **10 segundos por geração.** Não existe clipe de 15s. Roteiro maior vira N clipes.
- **Uma imagem de Ingredient** por geração, que carrega a identidade da pessoa.
- **Áudio gerado junto**, incluindo fala com lip sync.
- **Texto renderizado é o ponto fraco.** Quanto menos string, menor a chance de erro.

Por isso a arquitetura é sempre a mesma: um clipe = um beat do roteiro = uma frase falada + dois ou três cards + um frame final.

## O DNA visual

| Camada | O que é |
|---|---|
| Base | Pessoa sentada num estúdio escuro, luz prática quente atrás, fundo em bokeh preto-azulado, key suave pela esquerda |
| Cards | Retângulos de vidro de cantos arredondados, **contorno dourado com bloom real**, flutuando no terço inferior |
| Conteúdo dos cards | Gráficos, grids e silhuetas em **off-white**, nunca em dourado |
| Marcador de beat | O contorno dourado **acende** quando o card pousa. É o único uso do dourado |
| Faixa central | Reservada, sempre vazia — é onde a legenda entra na edição |
| Frame final | Congela, dessatura um passo, uma barra dourada se desenha e para |

**Paleta padrão:** preto #0B0B0C · dourado #C9A227 · off-white #F6F3EC.
Se o usuário pedir outra, troque o dourado pelo acento dele e mantenha a regra: um acento só, usado apenas como marcador de beat.

## Estrutura obrigatória do prompt

O prompt é um bloco único de texto corrido, em **inglês**, com estes componentes nesta ordem. Falta de qualquer um deles é o que faz o Omni improvisar.

1. **CRITICAL RULES** — política de texto (ver abaixo), likeness, obra original, caption safe zone
2. **STYLE** — uma frase densa descrevendo o mundo visual
3. **TECHNICAL** — 1080x1920, 9:16, 25 fps, 10 seconds, single continuous piece
4. **TYPOGRAPHY** — só quando existir texto renderizado
5. **PALETTE** — fundo, tipografia, acento e onde cada um pode aparecer
6. **VOICE & DIALOGUE** — travas de voz + a fala exata
7. **TIMELINE** — os seis beats com timecodes
8. **CAMERA** — como as coisas entram, saem e descansam
9. **SOUND** — trilha, efeitos e o silêncio final
10. **DO NOT** — a lista de negações

## Os seis beats de 10 segundos

Sempre esta cadência. É ela que cria a sensação de "já editado":

```
0.0–1.5s   HOOK       Pessoa falando, sem gráfico nenhum, push-in lento
1.5–3.5s   CARD A     Primeiro card sobe, contorno dourado acende
3.5–5.5s   CARD B     Segundo card entra pelo lado, acende um beat depois
5.5–7.5s   BURST      Pico de densidade: pulso, conexão, chips, tags
7.5–8.8s   RESOLVE    Últimas palavras. Cards encolhem, desfocam e saem
8.8–10.0s  HERO FRAME Silêncio. Congela, dessatura, barra dourada, fim
```

Dois princípios que sustentam isso:

**O respiro é parte do design.** Se algo se move em todos os frames, o olho não descansa e o clipe parece amador. O beat RESOLVE e o HERO FRAME existem pra isso.

**Nada se move linearmente.** Tudo desacelera até parar, como se assentasse pelo próprio peso. Elementos que saem encolhem e desfocam, nunca somem de uma vez.

## Política de texto — escolha um dos três modos

Renderizar texto é onde o Omni mais erra. Pergunte ao usuário qual modo, ou escolha pelo contexto.

**Modo A — zero texto (padrão, mais seguro).** O usuário coloca a legenda na edição.
> `CRITICAL RULE — NO TEXT ON SCREEN: This video must contain absolutely no readable text, letters, numbers, captions, subtitles, watermarks or UI copy of any kind. The dialogue is spoken audio only — it must NEVER appear as burned-in subtitles. Panels and cards are blank or filled with abstract shapes only. Never render pixel sizes, font names, color codes, easing names, durations or frame rates as visible text.`

**Modo B — uma exceção controlada.** Uma string única, curta e em caixa alta, tipicamente o CTA.
> `CRITICAL RULE — ONE TEXT EXCEPTION: The ONLY text allowed anywhere in this video is the exact string "XXXX". It must be spelled exactly like that, letter for letter. Absolutely no other readable text, letters, numbers, subtitles, captions or UI copy may appear — every other panel and surface stays blank. The spoken dialogue must NEVER appear as burned-in subtitles.`

**Modo C — legenda karaokê queimada.** Só quando o usuário pedir explicitamente. Exige o bloco TYPOGRAPHY e aumenta muito o risco de erro de grafia.

Em qualquer modo, avise: se sair grafia errada, regerar o mesmo prompt costuma resolver — é falha do renderizador, não do texto do prompt.

## Fala em português

O Omni gera o áudio. As travas que evitam os bugs conhecidos:

```
VOICE & DIALOGUE: The person speaks directly to camera in natural Brazilian
Portuguese with a neutral São Paulo accent — never European Portuguese, never
Spanish, never English. Confident conversational creator tone, mid-tempo, warm
and grounded. Natural mouth movement synced to the words, restrained lip
articulation, no exaggerated jaw. Speaks continuously from the first frame with
no silent lead-in. Small natural hand gestures near chest height. Single voice
only — no narrator, no voice-over, no echo, no second speaker. The line is
spoken once, exactly as written, and is not repeated or looped. Numbers are
spoken as full words.

DIALOGUE (Brazilian Portuguese, spoken aloud, never shown as subtitles): "..."
```

**Limite duro: 24 palavras por clipe.** É o teto para 10 segundos em português. Acima disso o Omni acelera a fala ou repete o final. Conte as palavras antes de entregar e informe a contagem ao usuário.

Siglas saem soletradas. Escreva "inteligência artificial" em vez de "IA", "três" em vez de "3".

## Como fatiar um roteiro

Quando o usuário manda uma copy inteira:

1. Corte em beats de sentido completo — cada clipe precisa fazer sentido sozinho, porque cada geração é independente.
2. Reduza cada beat a no máximo 24 palavras, preservando a voz do usuário.
3. Dê a cada clipe um papel: HOOK, PROVA, MECANISMO, CTA. Isso define quais cards entram.
4. Mantenha STYLE, PALETTE, CAMERA e SOUND **idênticos** entre os clipes — é o que faz a emenda funcionar na edição.
5. Varie só o TIMELINE e a fala.

Instrua o usuário a gerar todos na **mesma sessão com o mesmo Ingredient**, senão a paleta e o grain mudam entre clipes.

## Formato de entrega

Um bloco de código por clipe, com um título curto antes. Nada de comentário dentro do bloco — o usuário copia e cola inteiro.

Depois dos blocos, no máximo três linhas de nota prática: contagem de palavras, config do Flow (`Video | Ingredients | Omni Flash | 10s`), e o risco específico daquele lote.

## Antes de entregar, confira

- Cada clipe fecha em 10.0s e tem os seis beats
- A fala tem no máximo 24 palavras e nenhuma sigla
- A política de texto está declarada e é coerente com o TIMELINE
- A faixa central está reservada quando a legenda vier depois
- STYLE, PALETTE, CAMERA e SOUND são idênticos entre os clipes do mesmo lote
- O dourado aparece só como marcador de beat, nunca preenchendo texto ou forma
- Existe pelo menos um beat sem movimento nenhum

## Referências

- `references/prompt-template.md` — o esqueleto completo preenchível e um exemplo pronto de cada papel de clipe (HOOK, PROVA, MECANISMO, CTA)
- `references/troubleshooting.md` — os bugs conhecidos do Omni Flash e a correção de cada um. Leia quando o usuário disser que um clipe saiu errado.
