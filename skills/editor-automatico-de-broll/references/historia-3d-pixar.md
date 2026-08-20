# Formato 2 — VSL narrada em 3D estilo Pixar

O outro formato da casa. Não tem avatar filmado, não tem plano fixo, não tem insert: **o anúncio inteiro é gerado**, cena a cena, sobre uma locução de 8 a 12 minutos.

Validado em produção nos **AD08, AD02 e AD04** do LinfaFlow — 134 cenas geradas e montadas.

A referência aprovada é `02. IA/AD07 - JONAS/Ad Experience Preview (1).mp4`: 720×1280, 30 fps, personagens 3D estilizados, legenda queimada no terço inferior, corte a cada 5–8 s.

---

## O que muda em relação ao formato UGC

| | UGC 9:16 (formato 1) | VSL 3D (formato 2) |
|---|---|---|
| Base | body de avatar, plano fixo | nada — tudo gerado |
| Duração | 40 s – 3 min | 8 – 12 min |
| Cenas | 4–5 inserts | 40–50 cenas |
| O que segura | insert casado na fala | a própria história |
| Risco central | insert que não casa | **o personagem mudar de rosto** |

---

## O que trava o personagem

**A imagem-âncora passada em `--image-references` em toda geração.** Não é o texto do prompt.

Descrever "mulher de 47 anos, cabelo castanho" em 51 prompts produz 51 mulheres diferentes. A âncora produz uma só.

```
higgsfield generate create nano_banana_pro --aspect_ratio 9:16 --resolution 2k \
  --image-references ./ancoras/sarah_fase1.png \
  --image-references ./estilo_sem_rosto.png \
  --prompt "<cena> Keep the character's face, hair, build and clothing EXACTLY identical to
            the reference character sheet. Modern Pixar / Disney 3D animated feature film style."
```

### A âncora de estilo é separada da de personagem

Para acertar o render da casa, passar **um frame do próprio anúncio de referência**. Descrever "estilo Pixar" em texto produz fotorrealismo tipo scan 3D — aconteceu na primeira âncora da Sarah e só foi resolvido com o frame.

### Estados "antes" e "depois" são duas âncoras

A história é sempre uma transformação. Gerar a fase 2 **a partir da folha da fase 1**, mudando só corpo, postura e roupa:

> *"The exact same woman from the reference — same face, same eye shape, same nose, same freckle,
> same earrings. She is now visibly lighter and rested: defined jawline, waist that shows again,
> upright confident posture."*

Sem isso a fase 2 vira outra atriz e a transformação perde o sentido. Se o guarda-roupa da âncora for marcante (um vestido vermelho, por exemplo), **gerar também uma variante casual** — senão a roupa vaza para cenas onde ela não deveria estar e rouba o impacto de onde deveria.

---

## O fluxo

### 1. Reconstruir o áudio como ele toca na timeline

Quando o anúncio já tem edição, a locução costuma estar **picotada em dezenas de pedaços com offsets diferentes**, às vezes em duas trilhas. Transcrever os arquivos originais dá timecode errado.

Ler `pr_timeline_listar`, e remontar com ffmpeg usando `inicio`, `duracao` e `entrada` de cada clipe:

```bash
python3 scripts/audio_da_timeline.py --timeline tl.json --midia "<pasta dos audios>" \
        --out timeline.wav --duracao-esperada 711.28
```

O script aborta se a duração não bater — é a trava que impede transcrever um áudio torto.

**Conferir que a duração bate com a da sequência** antes de transcrever. Bateu 711,29 contra 711,28 e 599,67 exato — se não bater, o mapa inteiro sai torto.

### 2. Mapear os vãos, não a linha toda

Nos três ADs a primeira metade já estava editada e a segunda estava vazia. Marcar só o que falta:

```bash
python3 scripts/mapear_vaos.py --timeline tl.json --duracao 711.28 \
        --transcricao timeline.json --esqueleto marcadores.json
```

O `--esqueleto` já corta em cenas de até 15 s casadas com a fala. Os nomes vêm como `(descrever)` de propósito: escrever cada um a partir da narração, senão o editor recebe 47 marcadores idênticos.

No AD02 eram **457 s (64%)**; no AD04, **380 s (63%)**. Descobrir isso antes evita prometer "alguns espaços vazios" e entregar meio anúncio.

### 3. Marcar sobre a fala

Segmentar cada vão em cenas de **no máximo 15 s** (teto do Seedance), quebrando nas viradas da narração. Convenção de nome e cor: ver `mcp-premiere.md`.

Um tipo de marcador que só existe neste formato: **REAPROVEITAR**, em amarelo, para o material que já foi gerado e está parado. Nos três ADs havia 9 clipes prontos que ninguém usava — não estavam nem importados no projeto, por isso ninguém conseguia arrastá-los.

### 4. Gerar imagem → conferir → só então animar

**Nunca animar sem olhar o frame.** Imagem custa 2 créditos; vídeo de 12 s custa 42. Nos três ADs o QA das imagens pegou 13 defeitos — 26 créditos para corrigir, contra ~550 se tivessem virado vídeo.

O que conferir, além do rosto:
- **o rótulo do produto está legível?** Some com facilidade (ver `armadilhas.md`)
- **vazou alguém que não deveria estar na cena?**
- **a roupa bate com a cena vizinha?** Festa e dia a dia se misturam
- **o personagem certo está no papel certo?** Com duas âncoras no prompt o modelo pega a errada

### 5. Montar nos marcadores

Cada clipe **no tempo do seu marcador**, aparado na duração dele. O material sobra (gerado em segundos inteiros), então o editor tem handle para esticar.

**Não encaixar em cascata.** Fechar buraco puxando cada clipe para onde o anterior termina parece elegante e quebra o casamento verbal-visual — chegou a adiantar cenas em 9 s, com a praia da semana três aparecendo antes da narração falar dela. Sincronia vale mais que timeline sem buraco. Antecipar só quando o vão é menor que ~1,5 s.

---

## Custo real

| | |
|---|---|
| Imagem `nano_banana_pro` 2k | **2 créditos** |
| Vídeo Seedance 720p `fast` | **3,5 créditos/segundo** (12 s = 42) |
| Vídeo Seedance 720p `std` | **4,5 créditos/segundo** (12 s = 54) |

`fast` é 22% mais barato e não perdeu nada no QA frame a frame. Usar `fast`.

Um AD de 10 min com ~45 cenas fica em torno de **2.000 créditos** completo.

---

## Ordem que funciona

1. Reconstruir o áudio da timeline e transcrever (sem forçar idioma)
2. Mapear os vãos
3. Marcar sobre a fala, ≤15 s por cena
4. Âncoras de personagem — inclusive as derivadas de "depois"
5. Imagens em lote → **QA** → refazer o que caiu
6. Vídeos em fila de 4 → **QA frame a frame** → refazer
7. Importar, montar nos marcadores, **ler de volta**

---

## Scripts

| | |
|---|---|
| `scripts/audio_da_timeline.py` | reconstrói o áudio como ele toca na timeline, e **aborta se a duração não bater** |
| `scripts/mapear_vaos.py` | mapeia o que falta de vídeo e gera o esqueleto de marcadores |
| `scripts/gerar_lote.py` | fila de geração no CLI do Higgsfield — imagens e vídeos, com retry e backoff |

O `gerar_lote.py` roda com **4 workers por padrão**: o teto da conta é 8 e é dividido com a equipe. Ele pula o que já está no índice, então **rodar de novo é seguro** — é assim que se recupera de falha sem regerar o que já saiu.

---

## Cobertura da timeline (AD04 Crowned)

Um take por marcador **não cobre nada**: no AD04 deu 31% da timeline. A conta é:

```
takes do marcador = ceil(duração / 5.03)     # Seedance entrega 5,04 s
```

10:54 de VO exigiram **151 takes** para cobertura total. Marcadores longos concentram o volume —
o de 59,7 s sozinho levou 12.

## As travas de prompt, em todo plano

```
ONE SINGLE continuous full-bleed vertical frame filling the whole image. NOT a collage, NOT
split-screen, no panels, no side-by-side, no stacked images, no borders, no letterbox bars,
no text, no subtitles, no captions, no watermark.

IMPORTANT: the camera is in PORTRAIT orientation. The subject stands or sits UPRIGHT and VERTICAL,
head toward the top edge and body toward the bottom edge. Do NOT rotate or tilt the composition.
```

## Animar

```
higgsfield generate create seedance_2_0 --prompt "<movimento>" \
  --start-image /caminho/plano.png --aspect_ratio 9:16 --resolution 720p \
  --duration 5 --generate_audio false --mode std --wait --json
```

`--generate_audio false` sempre — a trilha já existe. O prompt descreve **movimento**, não
aparência: a imagem já carrega o visual. 6 workers em paralelo.

## Enquadramentos espelhados

Escolha 2–3 pares que se repetem **idênticos** em momentos distantes. É a assinatura do filme e
entrega o antes/depois sem split-screen nem cartela:

```
abertura ↔ fecho     mesma janela, mesma roupa, mesmo movimento de câmera
o espelho            repetido idêntico depois da virada
o objeto do gancho   revisitado no fim, transformado
```
