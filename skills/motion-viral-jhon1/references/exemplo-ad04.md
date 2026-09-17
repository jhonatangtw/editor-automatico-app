# Exemplo completo — AD04 LeafTide (10/09/2026)

Registro da demanda que originou a gramática podcast/dopaminérgica/editorial. Serve de **exemplo**
de briefing, decisões e números; nada daqui é regra fora deste contexto.

## Briefing recebido
- Pasta: `~/Documents/01_Producao/Demanda Setembro/AD04/` (`lip/` com 3 takes, `broll/` com 9 vídeos + 6 PNG).
- Copy: Doc "89_BM Leaftide - ADS" (`193cXF_zbYTSnwdbXhcNpvsP9wQbOnd-koFzdo7I4bjI`), seção "AD 04";
  37 threads de comentário (Breno 02/09 = inserts; Pedro 04/09 = copy, resolvidos; Mirella 09/09 = AD01).
- Referências: Pinterest `15551561209923797` (tipografia cinética, 17,9 s), `1142999580450072622`
  (editorial papel/luz, 17,2 s), `CRIATIVO PRONTO PARA SERVIR DE REFERENCIA.MP4` (era o próprio AD04
  montado por outra mão — virou o contrato de medidas).
- Projeto: `AD04.aep` aberto e vazio; comp criada `AD04_MAIN` 1080×1920 30 fps.

## Decisões e números
- Takes são segmentos: Rogan 0–9,60 (288 f) · "Yes, it's true" 0–1,567 (47 f) · body 0–122,97 (3689 f).
- Legenda: 229 blocos (1,7/s), caixa `#23500D` 103 px, Nunito ExtraBold 60 (escolhida por medição
  contra Poppins/Montserrat), centro 0,459 H no hook (depois 858 px) e 0,638 H no body.
- Reenquadramento medido (YuNet no take 720×1280): Rogan cx 348 / topo dos fones 200 → 156 %, pos
  (559,786) na fórmula, ajustado a (548,786) após remedir o render; Rhonda cx 359 / topo 95 → 150 %,
  (540,917.5). Olhos ficaram em 0,41–0,48 da metade — terço exato não alcançável sem cortar fones.
- Fundo sob cartão: 7 janelas na MAIN, 6 nas DOPA (cartões consecutivos fundidos).
- Higgsfield (autorizado): copo de matcha, balança, relógio — Nano Banana Pro, fundo `#8A8A8A`,
  "no digits/numerals". Reprovado: nenhuma nesta demanda (na demanda anterior, nota com "ONE DOLLAR").
- SFX da biblioteca local: `Fast_Swish.wav` (−12…−16 dB), `CARTOON_POP.mp3` (−10…−18 dB).
- Renders: `08_Exports/AD04_revisao_v4.mp4` (limpa), `_DOPA1_v6.mp4`, `_DOPA2_v3.mp4` — 134,133 s,
  4024 quadros, −26,9 dB médio.

## O que deu errado e virou regra
- Dois `aerender` no mesmo arquivo → MP4 sem moov → `lib/render.sh` com trava.
- Script de 458 camadas passou de 180 s e o runner desistiu → timeout 600 s + ping antes de concluir travamento.
- `set -o pipefail` + grep vazio matou o runner calado → `{ grep … || true; }`.
- Segundo grupo numa shape layer invalidou o primeiro → um grupo por camada.
- Emoji colorido não renderiza no AE → objeto 3D no lugar.
- API do Docs não liga thread à âncora `kix` → mapear por conteúdo + nome dos arquivos.

## Tempo
~2 h de sessão para as 3 versões, sendo ~1 h de render acumulado (3 comps × 3 rodadas).
