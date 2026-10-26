# Lições do Upsell #1 MarcaE (22–23/10/2026) — o que custou retrabalho

## Frasco do produto (3 rodadas reprovadas, ≈ US$ 14)
- GPT Image 2.5 gera o frasco **gigante** (maior que caneca/mão) e **afina** o frasco mesmo com a proporção escrita no
  prompt (2,0–2,4 contra 1,79 do mockup). "uns gordinhos e outros magros".
- Colar o mockup PNG por cima de fundo sem frasco, mesmo medindo escala pela caneca/mão e com sombra: "bem fake". Não usar.
- Girar o PNG para frasco deitado = "rótulo deitado" falso; e compor sobre vídeo que já tinha frasco = frasco duplicado.
- O que passou: **Nano Banana Pro** (`or:google/gemini-3-pro-image`) com o mockup como 1ª referência + still da cena
  como 2ª; escala real escrita (frasco 30 cáps ≈ 11 cm; caneca 9,5; mão 18,5; copo 14); medir altura/largura do frasco
  mais frontal no still (±8% do mockup) antes de animar.
- Kling v3.0 Pro: usar só os 2–3 s iniciais (gira o frasco/derrete rótulo depois); com 9 frascos muda a contagem →
  kit do preço fica still com push. Fila do Kling no Studio pode prender >1 h: use o still e troque depois; nunca reenviar.
- Estoque ("almost sold out"): poucos frascos restantes numa estante de galpão real, rótulo legível nos da frente.

## Avatar IV
- Ignora gesto pedido (aceno): mantém a pose da foto. Não prometa gesto; o pose vem do start frame.
- Sai 1080p 16:9 25 fps → recorte central 1440×1080 sem ampliar (start frame com a pessoa nos 75 % centrais).
- Seedance recusa referência com rosto que parece real ("persona criada por IA" só).
- Bloco de ~30–40 s por clipe; frase de preço como clipe próprio por versão (A/B/C).

## Voz
- ElevenLabs `eleven_v4`; checar cada áudio com Whisper. "-ed" que some antes de "t" (stopped taking) é pronúncia
  natural — 3 refações não mudam; aceitar.
- Voz de idoso: catálogo soa jovem; escolher por rótulo de idade + ouvido; o usuário decide (ou delega).

## Edição
- Música: "muito alta" com −20 dB → foi a −30 dB e "faltou fundo musical". O certo foi ~20 dB abaixo da voz COM o bed
  medido (o arquivo já é −34,6 LUFS).
- Legenda: "sem quebra de frase" → cortar só em pontuação (aceitando aspas de fechamento), oração > 80 caracteres em
  2 linhas dividindo antes de conectivo forte, travessão fica com a palavra de antes, oração de ≤ 3 palavras cola na
  seguinte, juntar orações da mesma frase enquanto couber; `text-wrap: balance`.
- Legenda de 2 linhas cobre gráfico que está no rodapé: botões a `top:690px`, contato a `top:580px`.
- Sem legenda sob o card de garantia e sob a CTA fixa (filtrar pelo MEIO da legenda dentro da janela, senão apaga a
  frase seguinte).
- Transições que "bugam" (salto de pose entre blocos do Avatar IV, fantasma de crossfade): corte seco + light leak.
- `<img>` de gráfico sem width/height explícito saiu esticado numa das versões → sempre width/height no HTML.
- `npx hyperframes` pode instalar versão nova na hora (0.8.188 em 23/10): conferir snapshot depois de update.

## Processo
- Não renderizar antes do usuário ver o preview (pedido explícito). Render das 3 ≈ 45 min; mudança de imagem = render de novo.
- Subagente que cai com a sessão não termina o render: conferir `entrega/` pela data antes de dizer que saiu.
- MCP do Drive/Chrome pode cair no meio: o caminho local do Drive (CloudStorage) continua funcionando.

## Correções do copywriter (revisão de 23/10) — já fazer assim de primeira
- Tarja nome+idade NUNCA na altura da legenda de 2 linhas (`top:676px` em 4:3).
- "Fazer igual MarcaB" nos trechos de oferta = planos COM o produto/kit: estoque (caixas de acrílico + etiqueta
  da marca + mão de luva), avental pondo a caixa do kit na caixa de envio e fechando, entregador com caixas da marca
  (sem logo de transportadora), cliente abrindo o kit em casa. Nada de caixa genérica do TikTok nesses pontos.
- Revelação do preço = imagem do kit fornecida pelo copy (push → mão pega um frasco) + card claro no canto inferior
  esquerdo "$15/bottle · $139 total" (padrão MarcaB), sem selo de nome do kit.
- "click the button below" do meio = seta para baixo (não botão).
- Fábrica: o copy pode mandar vídeo do YouTube — recortar só planos de máquina/cápsula, sem apresentador nem logo.
- Frasco no plano de "pessoas no protocolo" em primeiro plano, grande ("pote tá minúsculo").
- Luz (light leak) em toda virada de bloco; SFX de transição quase nenhum ("tem muito SFX nas transições").
