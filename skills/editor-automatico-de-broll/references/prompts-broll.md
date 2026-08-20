# Prompts de B-roll

## Regra de ouro

O B-roll é **a mesma pessoa**, em **roupa diferente**, fazendo **o que a fala está descrevendo**. Nada além disso precisa ser inventado.

A troca de roupa não é enfeite: ela faz o espectador ler os inserts como *dias diferentes*, o que é a assinatura do UGC caseiro. Se todos os B-rolls tiverem a mesma roupa, vira sessão de fotos.

## Identidade

Sempre passar a imagem do avatar como referência — é mais confiável que descrever o rosto:

```
media_upload(filename)  →  curl PUT  →  media_confirm(type="image", media_id)
generate_image(params={
  model: "nano_banana_pro",          # roteia p/ nano_banana_2, normal
  aspect_ratio: "9:16",
  medias: [{role: "image", value: "<media_id>"}],
  prompt: "<ver template abaixo>"
})
```

Abrir o prompt com a âncora de identidade, sempre igual:

> `<TIPO DE PLANO> of the exact same woman from the reference image — same face, same <cabelo>, same skin tone.`

Para planos de mão/detalhe, ancorar em `same skin tone, same manicure` e **não mostrar o rosto** — some o risco de identidade escapar.

## Gramática do prompt

Seguir a skill `photorealism-prompts` (specs de câmera são exigência do usuário, não simplificar), **mas escolher specs de celular**, não de médio formato. Hasselblad entrega comercial de TV; o alvo aqui é vídeo de celular.

```
Shot on iPhone 15 Pro main camera, 24mm equivalent, f/1.78, ISO <200-500>, 1/<60-125>s.
```

Somar imperfeição deliberada: `slight handheld tilt`, `natural amateur framing`, `mild sensor noise in the shadows`, `ordinary home interior with real clutter`, `mirror slightly smudged`.

Fechar **sempre** com a frase obrigatória de pele, intocada, quando houver pessoa ou pele visível:

```
visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbushing, no smoothing filters
```

## Template

```
<PLANO> of the exact same woman from the reference image — same face, same <CABELO>, same skin tone.
<O QUE ELA FAZ, ancorado na fala do insert>.
She wears a different outfit than the reference: <ROUPA NOVA>.
Shot on iPhone 15 Pro main camera, 24mm equivalent, f/1.78, ISO <X>, 1/<Y>s.
<LUZ E AMBIENTE>. <IMPERFEIÇÃO DE ENQUADRAMENTO>.
visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbushing, no smoothing filters
```

## Animação

```
generate_video(params={
  model: "kling3_0_turbo",
  aspect_ratio: "9:16", resolution: "1080p",
  duration: <casar com o trecho de fala, 3-15>,
  medias: [{role: "start_image", value: "<job_id da imagem>"}],
  prompt: "<movimento sutil>"
})
```

Movimento **sutil e único**. Descrever um gesto, uma deriva de câmera, e a luz permanecendo constante. Fechar com `no scene change, no text on screen` — o Kling às vezes ignora o scene change e corta pra um macro, o que costuma ficar **melhor** que o pedido; conferir antes de descartar.

Se o servidor devolver `preset_recommendation`, recusar com `declined_preset_id` e regerar literal.

## O "antes" (foto de quando estava pior)

**Aviso de mídia, dar sempre:** a política do Meta proíbe imagem de **antes e depois** em anúncios de saúde e emagrecimento. Avisar o usuário uma vez, em uma frase, e seguir se ele confirmar — a decisão é dele.

Três regras que fazem ou quebram esse asset:

1. **Foto, não vídeo.** Ninguém tem vídeo produzido de quando estava mal. Foto parada lê como arquivo, e ainda elimina o risco de morphing de corpo, que é onde a IA mais falha. Animar com push-in lento no ffmpeg:
   ```bash
   ffmpeg -loop 1 -i antes.png -vf "scale=1080:1920:force_original_aspect_ratio=increase,\
   crop=1080:1920,zoompan=z='1+0.00055*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':\
   d=<frames>:s=1080x1920:fps=25,setsar=1" -frames:v <frames> -c:v libx264 -crf 16 -pix_fmt yuv420p antes.mp4
   ```

2. **Câmera PIOR.** Se sair na mesma qualidade do resto, denuncia na hora. Pedir: `older iPhone front camera`, `harsh direct on-camera flash`, `blown-out forehead`, `hard flat shadow on the wall`, `crooked framing`, `low contrast`, `visible digital noise`. Cenário bagunçado (corredor, sapatos no chão, casacos no gancho) e **expressão apática, sem pose**.

3. **O modelo resiste a engordar a referência.** A primeira tentativa costuma voltar quase igual, e às vezes **troca a cor do cabelo**. Reforçar em CAIXA ALTA o traço de identidade que não pode mudar (`keeping her pastel PINK hair`) e descrever o corpo de forma concreta e enumerada (rosto mais redondo, braços mais grossos, torso mais largo, barriga que estica a camiseta). Enquadrar `from the knees up` — meio corpo esconde justamente o que precisa aparecer.

Onde entra: no bloco de **dor/passado** da copy ("frustrada", "não cabia mais nas minhas roupas"), nunca perto do CTA.

## Custo

| | crédito |
|---|---|
| imagem `nano_banana_pro` 1k | ~2 |
| clipe `kling3_0_turbo` 5s 1080p | ~10 |

Um criativo de 2min com 4 inserts sai por ~50 créditos. Preflight com `get_cost:true` antes de lote grande.

## QA obrigatório

Baixar e olhar antes de montar:
```bash
ffmpeg -v error -i clip.mp4 -vf "fps=1,scale=200:-1,tile=8x1" -frames:v 1 qa.jpg
```
Procurar: morphing de rosto no meio do clipe, mão com dedo a mais, objeto que aparece do nada, mudança de luz. Regerar só o clipe que falhou.
