# Padrão de dinâmica + lettering Katana: estilo salvo pelo usuário (02/11/2026, MarcaO Up2 NNN_XX)

O usuário aprovou este estilo e pediu para salvar ("salve esse estilo"). Ele vale para todo upsell 9:16 daqui para a frente, por cima da base visual do MarcaE (b-roll orgânico, personagem da história ≠ expert, legenda por frase em caixa escura).


## 1. Regra de ritmo
- **Nenhum plano visualmente parado por mais de 2–3 s** (alvo 2,1 s; teto 2,6 s). Conta como mudança: corte, texto ou palavra entrando, punch no expert, batida de câmera.
- A batida cai na **palavra que abre uma ideia nova**. A ordem de prioridade é: início de frase, depois palavra-chave do texto, depois a palavra mais perto de 2,1 s. O mínimo entre batidas é 1,3 s.
- Medir antes e depois. Liste os trechos > 3 s com timecode. Só podem sobrar o preço (c076) e o card final.

## 2. Alternância de camadas
- **Expert** nos momentos de autoridade e explicação (mecanismo, prova, ingredientes). Punch-in alternando 1,0 ↔ 1,12 a cada ≥ 1,1 s.
- **B-roll** ilustrando exatamente o que é dito, sem repetir plano em sequência.
- **Lettering Katana** nas frases-chave e nos números. Entra em corte seco, com impacto.

## 3. Câmera da mídia (`.kbeat`)
A mídia de cada cena fica dentro de um `.kbeat` próprio, que é filho da camada de mídia e é plano. **O texto não escala** (nada corta na borda) e as regras flat do supervisor continuam intactas. Três tipos de batida, em ciclo:
- **corte seco** de enquadramento: scale 1,0 ↔ 1,10 (F: 1,07) e xPercent ±2,5. SFX: impacto 0,03.
- **chicote**: xPercent ±9 → 0 em 0,26 s expo.out, com **blur direcional só no eixo x** (filtro SVG feGaussianBlur `stdDeviation "30 0"` → 0 em 0,28 s). SFX: whoosh 0,04.
- **push 3D**: rotationY ±6, rotationX −2,5, scale +0,1 → 0 em 0,5 s expo.out, perspectiva 1400 e blur direcional 18. SFX: swish 0,035.

O ciclo depende da cena: em B/R é chicote → corte → push; em T é push → corte → chicote; em F é push → corte, mais leve e só no fundo. A direção alterna a cada batida.

- **Troca de camada** (expert → b-roll → lettering): a cena entra com chicote (xPercent ±7 → 0 em 0,3 s) e blur direcional 34.

## 4. Lettering Katana Dark-Glass
- **Palco** (`kstage`): vidro escuro, borda na cor de destaque, gloss diagonal e sombra funda. Entra com rotationX 18→0, y 56 e blur 14→0, em 0,5 s expo.out. Depois deriva y −10 / scale 1,025 até o fim. **Sem z** (z negativo esconde o palco atrás do fundo).
- **Kicker** em pílula, com ponto luminoso e caixa alta espaçada (.24em).
- **Headline**: as palavras saem da máscara (yPercent 118→0) sincronizadas à fala. A palavra única curta entra letra a letra (stagger 28–36 ms), com flash radial na cor e régua luminosa embaixo. Impacto 0,08.
- **Câmera 3D no lettering**: a cada batida o headline inclina (rotationY ±5, rotationX 4, x ±22 → 0 em 0,5 s), sempre sem escala.
- **Headline que fica muito tempo**: sai na primeira batida depois de 2,6 s no ar, se ainda sobrar ≥ 1,8 s de cena. A saída é blur 14 + y −80 + rotationX −26 em 0,3 s, e **a legenda volta** (ou lettering ou legenda).
- **B-roll longo sem texto** ganha `letra_em` com a frase-chave da fala. O lettering entra na palavra (≤ 0,15 s): o supervisor reprovou "THEN IT STOPPED" entrando 0,4 s antes.
- Preço riscado com laser (scaleX), selo ✓, troca de palavra (MONTHS rasga → WEEKS).
- Cores: amarelo #FFD23F (neutro), verde #2BD67B (benefício), vermelho #FF4B3E (dor).

## 5. SFX (sempre abaixo da voz, 0,03–0,045)
Whoosh no chicote, swish no push, hit leve no corte, pop no kicker e impacto no headline. Riser chegando nas telas-show (Ritual, presente, MONTHS→WEEKS). Master −16 LUFS / TP −1,5.

## 6. Fica de fora
Price reveal (c076), card final, barra de oferta, CTA e tarjas mantêm o padrão próprio.

## 7. Cuidados conhecidos
- `heavy_overlay` alto no check (133 no MarcaO): no render, confira se não há quadro preto.
- `line_unread` sobe quando a legenda volta depois do headline. Verifique o tempo de leitura.
- Se o lettering ficar 4–5 s, a fala fica esse tempo sem escrita. Isso é aceito pela regra "ou lettering ou legenda", mas avise o usuário.
- Conferir sempre por snapshot que nada some atrás do fundo (preserve-3d) e que nada corta na borda.
