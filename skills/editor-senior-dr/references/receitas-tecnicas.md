# Receitas técnicas (números de partida)

Valores que já funcionaram na operação, com a fonte entre colchetes. São **pontos de partida**, não leis: o critério final é ouvir e ver a emenda.

**Ordem de prioridade quando os valores conflitam:**
1. Padrão do projeto ou da peça de destino (skill dedicada, VSL em que o ML vai emendar, lote já entregue).
2. Limite técnico do material (avatar de IA: punch-in ≤ ~120%; resolução que não aguenta zoom).
3. Registro de acabamento escolhido (`matriz-decisao.md`).
4. Default das tabelas abaixo.

Exemplo: avatar no registro editorial dá punch-in de 105–115% (registro) dentro do teto de 120% (limite) — use 105–115%. ML no modo A dá loudness igual ao da VSL (projeto), mesmo que o registro diga −14.

## 1. Decupagem e cortes

| Material | Receita | Fonte |
|---|---|---|
| TTS (ElevenLabs) | Decupar pelo **silêncio real** (`silencedetect` em torno de −42 dB). Pausa > 0,42 s vira 0,32 s, com 0,15 s de borda. **Nunca** decupar pelo alinhamento de texto: mordeu fim de palavra | edicao-prosperidade-adhw |
| Hooks gerados | `silencedetect -40 dB / 0,3 s`, margem de 0,1 s, cauda de 0,3 s depois da última palavra; manter a cauda quando a demonstração termina depois da fala | hooks-meat-hook |
| Talking head real | "Corte suave": 0,40 s antes / 0,30 s depois, borda pela energia RMS da voz (o Whisper desloca até 0,5 s) | editor-de-reels-do-jhon |
| Aula / gravação longa | Receita aprovada da skill cortar-aula | cortar-aula |
| Body de avatar TTS/HeyGen | Normalmente não há silêncio para cortar; o ritmo vem de punch-in e inserts | editor-automatico-de-broll |
| Default editorial | Silêncio > 550 ms é **candidato** a corte, não remoção automática; 250–550 ms só com razão editorial; preserve pausa antes de revelação, reação e emoção | corte-viral |

**Nunca cortar palavra.** Confira a borda com `silencedetect=noise=-35dB:d=0.1` ao redor de cada emenda e ouça. Legenda nunca atravessa corte de take.

**Whisper:** passada longa alucina e engole frases. Use para localizar e reconfira janelas de ~20 s; palavra com duração > 1,5 s = trecho engolido; repetição no fim do áudio = alucinação. Regra: **timing do áudio, texto da copy** (corrija o texto contra a copy).

## 2. Punch-in, zoom e cobertura

| Registro | Valores |
|---|---|
| UGC cru | 110–116%, variando a escala (escala igual vira tique), corte seco para dentro e para fora |
| UGC dinâmico | Snap de ~0,16 s por frase, 1,0↔1,1–1,28; crash-zoom ~1,42 raro; deriva lenta em momento emocional |
| Premium DR | Punch seco de 112% (cópia do avatar na V2 com o mesmo inPoint); zoom 100↔107 em janelas ≥ 2 s, virando sempre num corte; hook com push-in de 100→110% nos 3 s iniciais |
| VSL 16:9 | ~1 punch a cada 25–30 s, no fim de frase |
| Default | 105–115%, duração mínima de ~1,2 s, só em número, confissão, reação ou prova. Nunca zoom "só para estimular" |

Avatar de IA: evite passar de ~120% (boca e dentes deformam).

**B-roll:** premium DR, 2–3,2 s por insert e cobertura de 30–40%; UGC alta densidade, cobertura de ~25% e 1 corte a cada 3–5 s; nenhum buraco < 0,6 s entre inserts na trilha de B-roll (o avatar "pisca"). Sem footage repetido na mesma timeline.

## 3. Legenda e lettering

- **Tamanho (em 1080 px de largura):** corpo da legenda entre ~54 e ~76 px. Na operação: 76 px no premium DR/WL (Montserrat ExtraBold), 54 px no MarcaB 1:1 (Helvetica Bold em pílula). Para público 50+, fique no topo da faixa e não passe de ~3–4 palavras por linha. Confira no celular: se for preciso apertar os olhos, está pequena.
- Texto **sempre** vindo da copy (diff palavra a palavra antes do render). SRT cru já produziu erro grave.
- Legenda some quando o lettering mostra a mesma palavra.
- Lettering na altura do peito (~47–55% da altura em 9:16), nunca a ~30%, que cobre o rosto.
- Só palavras da copy no lettering ("three days" não vira "3 days" se a copy diz por extenso).
- Lettering curto: 1–4 palavras.
- Estilos por registro: ver `matriz-decisao.md`.

## 4. Áudio

- **Loudness final:** −14 LUFS / TP ≤ −1 dBTP para redes (default); −16 no premium DR da operação; −15 no MarcaB. Use o do registro ou do projeto; seja consistente dentro de um lote.
- Trilha: bem abaixo da voz (no premium DR, voz −16 e trilha ~−34; com ducking, música ~−16 dB sob a voz, sidechain com release de ~400 ms).
- Hook e body normalizados para o mesmo nível **antes** de juntar.
- Voz: inglês americano nos criativos para os EUA; números por extenso no TTS; mesma voz entre clipes do mesmo personagem (STS para unificar).
- SFX: alinhados ao quadro do corte/entrada; whoosh em B-roll, pop/boom em lettering, riser antes de revelação/CTA. UGC cru: nenhum.

## 5. Técnica de imagem

- Sequência a 25 fps quando há HeyGen (23,976 derruba quadro na boca); HyperFrames a 30; Kling/Omni saem a 24.
- 4:5 a partir de 9:16: `crop=iw:iw*1.25:0:(ih-iw*1.25)/2`, mantendo o essencial nos 70% centrais. Leia as settings da sequência antes de gerar mídia.
- Flash em ffmpeg exige `blend=screen` em gbrp (em yuv420p fica roxo).
- Clipes do Kling: use a cópia sem áudio; o áudio do clipe apaga a voz na timeline.

## 6. Avatar e lip sync

- Persona de IA: HeyGen Avatar IV (Avatar V reprovado pelo usuário); fala nativa no Kling + STS venceu o wan3_0.
- Voz decupada **antes** do lip sync.
- QA de lip sync: um quadro no silêncio (boca fechada) e 3–4 nos picos de fala. **Não** confie em correlação automática (42 falsos em 68).
- Rótulo do produto deformado: recole o frasco do still em vez de regerar.
- Imagem não pode contradizer a fala (avatar de camisa social dizendo "de pijama").
