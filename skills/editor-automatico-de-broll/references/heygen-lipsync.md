# Gerar o BRUTO com lipsync (HeyGen) — quando não existe body pronto

A skill principal começa no bruto. Este arquivo cobre o passo anterior: **copy → áudio → lipsync → bruto**, para quando o body ainda não existe.

Chaves: as que você conectou na aba Contas do Editor Automático (ou variáveis de ambiente). Validado em 27/07/2026.

---

## Endpoint atual

**`POST https://api.heygen.com/v3/videos`**. Os endpoints v2 ainda respondem mas **serão removidos em 31/10/2026** — o próprio retorno avisa.

Campos descobertos por teste, porque a documentação não os traz juntos:

| Campo | Regra |
|---|---|
| `audio_asset_id` | **Nível raiz.** Não é `audio.asset_id` nem `voice.audio`. A mensagem de erro lista as três opções válidas: `(script + voice_id)`, `audio_url`, `audio_asset_id`. |
| `aspect_ratio: "9:16"` | **Obrigatório para vertical.** Só `resolution: "1080p"` devolve 1920x1080 DEITADO. Não existe `dimension` nem `orientation` no v3. |
| `engine` | `{"type": "avatar_v"}` ou `{"type": "avatar_iv"}` |
| `motion_prompt` | Linguagem natural para gesto. **Funciona de verdade** — pedir "pequenos movimentos de mão perto da mesa" faz a avatar gesticular. |

---

## Avatar V exige grupo TREINADO

Foto solta é recusada: *"No cross-reference candidate available for Avatar V. This photo avatar's group has no eligible instant avatar look."*
O **Avatar IV aceita a foto direto**, sem preparo.

Fluxo do treino — **uma vez por persona, ~9 minutos**, não por criativo:

```
POST upload.heygen.com/v1/talking_photo   (binário, Content-Type: image/jpeg)  -> talking_photo_id
POST /v2/photo_avatar/train  {"group_id": "<id>"}                              -> flow_id
GET  /v2/photo_avatar/train/status/<group_id>                                  -> pending ... ready
```

Depois disso o mesmo id serve como `avatar_id` com `engine: avatar_v`.

**Áudio:** `POST upload.heygen.com/v1/asset` (Content-Type: audio/mpeg) → `asset_id`.

---

## Qualidade dos motores (testado no mesmo áudio)

**Avatar V > Avatar IV > talking photo padrão.** O V gesticula — mão levantada, palma aberta, dedo apontando. O IV é mais expressivo que o padrão mas gesticula pouco. Todos os três seguram a identidade e **travam o enquadramento**.

---

## Voz: clonar do próprio body

Se os hooks forem aberturas alternativas de um body que já existe, **clonar a voz do body** em vez de escolher de catálogo. Voz diferente entre hook e body faz o corte soar como duas pessoas e mata o criativo no primeiro segundo.

```
POST https://api.elevenlabs.io/v1/voices/add   (multipart: name, description, files=@amostra.mp3)
POST https://api.elevenlabs.io/v1/text-to-speech/<voice_id>
     {"model_id":"eleven_multilingual_v2",
      "voice_settings":{"stability":0.45,"similarity_boost":0.85,"style":0.35,"speed":1.0}}
```

**Ritmo importa.** Medir sempre palavras por segundo contra o body de referência. TTS lento entrega fala arrastada e derruba o hook. Referência medida: body ≈ 2,95 pal/s; hook pode e deve ser mais seco (3,2–3,5).

**O `text2speech_v2` do Higgsfield NÃO expõe velocidade** — só engine, tipo e id de voz. Para controlar ritmo, entonação ou stability é preciso a API direta do ElevenLabs.

---

## O caminho Higgsfield (quando o HeyGen recusa)

`wan2_7` aceita `start_image` + `audio_references`. Mas:

- **Teto de 15 segundos.** Um body de 2 minutos vira ~10 segmentos.
- **O enquadramento NÃO trava** — deriva 15-20% ao longo do clipe. Cada segmento começa aberto e termina fechado, então emendar dois seguidos dá salto visível. Repetido dez vezes, vira serrote de zoom e denuncia a costura.
- Consequência de projeto: **nesse caminho o B-roll não é enfeite, é o que esconde a emenda.** Cada seam precisa de insert em cima, e a segmentação da copy tem que cair onde exista gancho visual.

`sync_so` (Sync Lipsync 3) **não serve para criar** — pede `input_video`, não imagem. É para re-sincronizar vídeo existente.

---

## Antes de gerar, conferir a imagem

O HeyGen anima exatamente o que está no quadro e **não reenquadra**. A foto precisa ter o enquadramento final desejado, rosto único e nítido, sem óculos escuros, vertical.

E conferir se a imagem contradiz a copy: num caso real o hook dizia *"I'm here in my pajamas"* e a avatar estava de camisa social — a fala desmentia a imagem no primeiro segundo.

---

## Atualização — o que mudou depois deste guia

- **Persona gerada por IA: Avatar IV com foto + áudio.** O CLI oficial (`heygen`) faz direto, sem treinar avatar:
  ```
  heygen asset create --file persona.jpg        # imagem: o retorno traz "id"
  heygen asset create --file fala.wav           # áudio: o retorno traz "asset_id"
  heygen video create -d '{"type":"image","image":{"type":"asset_id","asset_id":"<ID_IMG>"},
    "audio_asset_id":"<ID_AUD>","aspect_ratio":"9:16","resolution":"1080p","fit":"cover",
    "expressiveness":"medium","motion_prompt":"<arco da fala>","output_format":"mp4"}'
  heygen video get <VIDEO_ID>   ->   heygen video download <VIDEO_ID> --output-path avatar.mp4
  ```
  No Avatar V a persona sintética fica sem `expressiveness` e sem `motion_prompt` (exigem filmagem real do mesmo grupo); o IV dá microexpressão e piscada mais naturais.
- **Dois bolsos de crédito**: a chave de API tem uma carteira; o login do CLI (OAuth) usa os créditos da assinatura. Confira o saldo com `heygen auth status` antes de concluir que "não dá pra gerar". Referência: ~4 créditos premium por segundo de vídeo de foto.
- **Copy inteira numa geração** (até ~5 min), com um `motion_prompt` que descreve o arco (ordem das intenções, ênfases, trocas de expressão). Segmentar só para refazer um trecho.
- **25 fps.** A HeyGen entrega 25; sequência em 23,976 derruba quadro justo na boca. Case a sequência com a fonte (`t.ticks="10160640000"` como texto já calculado, ou `t.seconds = 1/25`).
- **Rótulo do produto** degrada no IV e no V: recolar o frasco do still aprovado por cima (rastreio por `cv2.matchTemplate`) resolve sem gastar crédito. Regerar só por rosto, boca ou pose.
- **Arquivo até 32 MB** no upload: áudio longo em mp3.
