# Voz do Jhon e legenda

## Voice Changer (speech-to-speech)

`POST /v1/speech-to-speech/{voice_id}`, multipart, `model_id=eleven_multilingual_sts_v2`.
Chave em `~/.config/hw-creative/.env` (`ELEVENLABS_API_KEY`).

| | |
| --- | --- |
| voz **Jhon 2** (padrão) | `JM55dOm3pyMwSBeLoAJt` |
| voz Jhon (antiga) | `s3UpYkNMHlMjPfwCUzdh` |
| formato | **`mp3_44100_128`** — `pcm_*` devolve 403 `output_format_not_allowed` (só plano Pro) |
| ajustes que funcionaram | `stability 0.6 · similarity_boost 0.85 · style 0.15 · use_speaker_boost true` |
| ruído | `remove_background_noise=false` — o take já é de estúdio, limpar demais tira o corpo da voz |

⚠ A chave é de **escopo restrito**: `/v1/user` devolve 401 `missing_permissions`. Isso **não**
quer dizer que a chave morreu — `/v2/voices`, STS e TTS funcionam. Não diagnostique por `/v1/user`.

### O que muda e o que não muda

O Voice Changer **preserva o tempo das palavras** — medido em 5 takes de 10 s, 89 palavras:
desvio médio ≤ 15 ms. O MP3 acrescenta ~26 ms de padding no fim, irrelevante para o corte.

Mas **confira sempre** antes de trocar o áudio sob um motion já sincronizado:

```bash
python3 lib/conferir_voz.py 00_brief/transcripts 06_Audio/jhon
```

**Como ler o resultado:** desvio grande só no **início** de uma palavra depois de pausa
(ex.: "É" +230 ms, "mexe" −340 ms) é **jitter do Whisper** marcando o ataque da vogal, não
deslocamento — o **fim** da mesma palavra bate em 0 ms. Deslocamento de verdade move as duas
pontas. O script já separa os dois casos na saída.

### Trocar no AE

Camada de áudio com o **mesmo `startTime`/`inPoint`/`outPoint` do take**, e no take original
`audioEnabled = false` (muta só o som; o vídeo continua). Guardar os originais em
`06_Audio/original/` — a troca precisa ser reversível.

### Provar que o render saiu com a voz certa

```bash
python3 lib/conferir_render.py timbre render.mp4 06_Audio/jhon/take1_jhon.wav 06_Audio/original/take1.wav
```

Correlação de forma de onda **não serve** (dá ~0 mesmo quando é a voz certa: o timbre muda a
fase). O que discrimina é o **espectro médio de longo prazo**, só nos quadros com voz:
esperado > 0,95 na voz certa e ≥ 0,05 abaixo na antiga. Medido: 0,997 × 0,820.

## Legenda

- Blocos **curtos**, uma ideia por bloco, centrados, centro em ~0,70 da altura.
- **Nunca atravessar um corte de take** — junta o fim de uma frase com o começo de outra e lê
  como erro de decupagem. Truncar o fim do bloco no início do próximo (nada de sobreposição:
  com blocos sobrepostos o render escolhe o primeiro que casa e o seguinte entra atrasado).
- **Cala sob cutaway que já tem tipografia própria.** Duas tipografias no mesmo quadro brigam.
- Janela livre menor que ~2 s fica de fora: legenda que pisca entre dois motions lê como defeito.
- O texto vem **da copy**, alinhado pelos tempos do Whisper — o texto cru do Whisper erra
  estrangeirismo ("hook" → "Hulk").

### Glow

```
dropShadow(l, 5, 7, 62, 90)          # a sombra vem primeiro: é ela que garante legibilidade
ADBE Glo2 → limiar 55 · raio 34 · intensidade 0,55
```

O glow é **destaque, não neon**: acima de ~0,8 de intensidade a letra engorda e perde a borda.
As propriedades de **cor** do `ADBE Glo2` recusam `[r,g,b,a]` (erro "Array não é um número") —
deixar no padrão e mexer só nos três números acima.
