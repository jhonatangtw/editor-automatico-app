# EXEMPLO REAL de montagem do clone no HyperFrames (1080x1920, 30 fps) — um AD de 29 s com
# 4 blocos: A tela dividida (b-roll reaproveitado em cima + personagem nova embaixo), flash branco,
# B tela dividida invertida (personagem na cozinha em cima + b-roll embaixo), desfoque, C tela cheia,
# vazamento de luz quente, D dois planos de "antes" refeitos lado a lado.
#
# NÃO rode como está: copie para <pasta do job>/hf/gerar_index.py e ADAPTE ao mapa de cenas da sua
# decupagem — tempos dos blocos, caixas (#cima/#baixo/...), arquivos em assets/media e os GRUPOS da
# legenda. O que vale levar para qualquer clone:
#   * os tempos vêm da DECUPAGEM do original (mesmos segundos, mesmas trocas);
#   * a legenda é gerada dos tempos de palavra da voz NOVA (voz/voz_clone.json do encaixar_voz.py),
#     por FRASE, na mesma altura medida no original (y da base da caixa);
#   * data-media-start de cada vídeo de lip sync = folga inicial do áudio enviado + offset_audio.py;
#   * todo elemento que anima depois começa escondido por tl.set(...) em t=0 e entra com
#     fromTo(..., {immediateRender:false}) — senão aparece pronto, some e entra ("tranco");
#   * movimento contínuo com ease "none" (sine.inOut por cena dá "lapso" antes do corte);
#   * nunca edite o index.html à mão: edite este gerador e rode de novo.
#
# Legenda por frase, em cima dos tempos de palavra da locução nova (voz/voz_clone.json).
import json, os, html
AQUI = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(AQUI, "..", "voz", "voz_clone.json")))["words"]
DUR = 29.08

GRUPOS = [  # (texto exibido, índice da 1ª palavra, índice da última)
    ("If you're", 0, 1), ("over 40", 2, 3), ("and your body just stopped", 4, 8),
    ("responding — it's not your fault.", 9, 13), ("It's a locked hormone.", 14, 17),
    ("And this gelatin is the only thing", 18, 24), ("that's gonna unlock it.", 25, 28),
    ("If you tried the gelatin trick", 29, 34), ("and it didn't work.", 35, 38),
    ("It's not the recipe.", 39, 42), ("It's the ratio of the ingredients.", 43, 48),
    ("Watch till the end", 49, 52), ("to find out", 53, 55), ("the right way to make it.", 56, 61),
    ("This was me before.", 62, 65), ("Bloated,", 66, 66),
    ("exhausted, and trapped in a body", 67, 72), ("that didn't feel like mine.", 73, 77),
]
assert len(W) == 78, "o numero de palavras mudou: refaca os GRUPOS"
leg = []
for k, (txt, a, z) in enumerate(GRUPOS):
    ini = W[a]["start"] - 0.04 if k else 0.0
    fim = (W[GRUPOS[k + 1][1]]["start"] - 0.04) if k + 1 < len(GRUPOS) else DUR
    y = 1062 if ini < 12.6 else 1438         # base da caixa, medida no original: A 0,55 H · B/C/D 0,75 H
    leg.append((k, txt, round(ini, 3), round(fim - ini, 3), y))

COZ_ATE = 24.70
clips_leg = "\n".join(
    f'<div id="lg{k}" class="clip leg" data-start="{i}" data-duration="{d}" data-track-index="20" style="top:{y-200}px">'
    f'<div id="lg{k}-in" class="leg-box">{html.escape(t)}</div></div>' for k, t, i, d, y in leg)

doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<!-- GERADO por gerar_index.py — edite o gerador, não este arquivo -->
<script src="assets/js/gsap.min.js"></script>
<style>
@font-face {{ font-family: 'Poppins'; font-weight: 700; font-display: block; src: url("assets/fonts/Poppins-Bold.ttf") format('truetype'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; background: #000; overflow: hidden; }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; font-family: 'Poppins', sans-serif; }}
.caixa {{ position: absolute; left: 0; width: 1080px; overflow: hidden; }}
.caixa video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
#cima {{ top: 0; height: 960px; }}
#cima video {{ height: 960px; }}
#baixo {{ top: 960px; height: 960px; }}
#baixo video {{ top: -230px; }}
#gel {{ top: 960px; height: 960px; }}
#gel video {{ height: 960px; }}
#coz {{ top: 0; height: 1920px; }}
#coz-in {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
#coz-in video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.painel {{ position: absolute; top: 0; width: 538px; height: 1920px; overflow: hidden; }}
.painel video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
#p1 {{ left: 0; }}
#p2 {{ left: 542px; }}
#p2-in {{ position: absolute; inset: 0; transform-origin: 50% 100%; }}
#sep {{ position: absolute; left: 538px; top: 0; width: 4px; height: 1920px; background: #f3efe9; }}
.leg {{ position: absolute; left: 0; width: 1080px; height: 200px; display: flex; justify-content: center; align-items: flex-end; }}
.leg-box {{ background: #fff; color: #000; font-weight: 700; font-size: 60px; line-height: 1.1; text-align: center;
  padding: 7px 22px 9px; border-radius: 14px; max-width: 780px; letter-spacing: -0.3px; }}
#flash {{ position: absolute; inset: 0; background: #fff; opacity: 0; }}
#leak {{ position: absolute; inset: 0; opacity: 0; mix-blend-mode: screen;
  background: radial-gradient(1200px 1500px at 85% 30%, rgba(255,190,110,0.95), rgba(255,140,60,0.55) 45%, rgba(255,120,40,0) 75%),
              linear-gradient(180deg, rgba(255,226,180,0.6), rgba(255,170,90,0.25)); }}
</style>
</head>
<body>
<div id="root" data-composition-id="clone" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">

<!-- A · 0–12,60: tela dividida — avião (reaproveitado) em cima, personagem nova em selfie embaixo -->
<div id="cima" class="caixa"><video id="v-aviao" class="clip" src="assets/media/broll_reuso_1.mp4" muted playsinline preload="auto" data-start="0" data-duration="12.62" data-media-start="0" data-track-index="1"></video></div>
<div id="baixo" class="caixa"><video id="v-selfie" class="clip" src="assets/media/lipsync_cenario1.mp4" muted playsinline preload="auto" data-start="0" data-duration="12.62" data-media-start="0.323" data-track-index="2"></video></div>

<!-- B/C · 12,60–24,70: cozinha (personagem nova). B: metade de cima + gelatina embaixo; C (17,40+): tela cheia -->
<div id="coz" class="caixa"><div id="coz-in"><video id="v-coz" class="clip" src="assets/media/lipsync_cenario2.mp4" muted playsinline preload="auto" data-start="12.60" data-duration="{COZ_ATE - 12.60:.2f}" data-media-start="0.283" data-track-index="3"></video></div></div>
<div id="gel" class="caixa"><video id="v-gel" class="clip" src="assets/media/broll_reuso_2.mp4" muted playsinline preload="auto" data-start="12.60" data-duration="4.80" data-media-start="0" data-track-index="4"></video></div>

<!-- D · 24,62–fim: planos de "antes" refeitos (GPT Image 2.5 + Kling 3.0 Turbo), lado a lado -->
<div id="p1" class="painel"><video id="v-a1" class="clip" src="assets/media/broll_refeito_1.mp4" muted playsinline preload="auto" data-start="24.62" data-duration="{DUR - 24.62:.2f}" data-media-start="0.3" data-track-index="5"></video></div>
<div id="p2" class="painel"><div id="p2-in"><video id="v-a2" class="clip" src="assets/media/broll_refeito_2.mp4" muted playsinline preload="auto" data-start="24.62" data-duration="{DUR - 24.62:.2f}" data-media-start="0.2" data-track-index="6"></video></div></div>
<div id="sep-c" class="clip" data-start="24.62" data-duration="{DUR - 24.62:.2f}" data-track-index="7"><div id="sep"></div></div>

<div id="fx" class="clip" data-start="0" data-duration="{DUR}" data-track-index="30" style="position:absolute;inset:0"><div id="leak"></div><div id="flash"></div></div>

{clips_leg}

<audio id="vo" src="assets/media/voz_clone.wav" data-start="0" data-duration="{DUR}" data-track-index="40" data-volume="1"></audio>
<audio id="sfx1" src="assets/sfx/whoosh-soft.mp3" data-start="12.42" data-duration="1.2" data-track-index="41" data-volume="0.22"></audio>
<audio id="sfx2" src="assets/sfx/whoosh.mp3" data-start="17.22" data-duration="1.0" data-track-index="42" data-volume="0.2"></audio>
<audio id="sfx3" src="assets/sfx/whoosh-soft.mp3" data-start="24.40" data-duration="1.2" data-track-index="43" data-volume="0.18"></audio>
<audio id="sfx4" src="assets/sfx/whoosh-soft.mp3" data-start="28.70" data-duration="0.38" data-track-index="44" data-volume="0.15"></audio>
</div>
<script>
(function () {{
  var tl = gsap.timeline({{ paused: true }});
  // cozinha: fase B mostra a faixa do rosto na metade de cima; fase C tela cheia
  tl.set("#flash", {{ opacity: 0 }}, 0); tl.set("#leak", {{ opacity: 0 }}, 0);
  tl.set("#coz-in", {{ filter: "blur(0px)", x: 0 }}, 0); tl.set("#gel", {{ filter: "blur(0px)" }}, 0);
  tl.set("#coz", {{ height: 960 }}, 0);
  tl.set("#coz-in", {{ y: -200 }}, 0);
  tl.set("#coz", {{ height: 1920 }}, 17.40);
  tl.set("#coz-in", {{ y: 0 }}, 17.40);
  tl.fromTo("#coz-in", {{ filter: "blur(0px)", x: 0 }}, {{ filter: "blur(26px)", x: -60, duration: 0.099, ease: "power2.in", immediateRender: false }}, 17.30);
  tl.fromTo("#coz-in", {{ filter: "blur(26px)", x: 60 }}, {{ filter: "blur(0px)", x: 0, duration: 0.12, ease: "power2.out", immediateRender: false }}, 17.401);
  tl.fromTo("#gel", {{ filter: "blur(0px)" }}, {{ filter: "blur(26px)", duration: 0.10, ease: "power2.in", immediateRender: false }}, 17.30);
  // painel 2: aproxima por baixo para o rosto ficar fora do quadro, como no original
  tl.set("#p2-in", {{ scale: 1.28 }}, 0);
  // flash branco 12,60
  tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.05, ease: "none", immediateRender: false }}, 12.55);
  tl.fromTo("#flash", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.08, ease: "none", immediateRender: false }}, 12.62);
  // vazamento de luz + branco 24,45–24,72
  tl.fromTo("#leak", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.14, ease: "power1.in", immediateRender: false }}, 24.44);
  tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.06, ease: "none", immediateRender: false }}, 24.56);
  tl.fromTo("#flash", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.10, ease: "none", immediateRender: false }}, 24.64);
  tl.fromTo("#leak", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.16, ease: "power1.out", immediateRender: false }}, 24.66);
  // fim: vazamento quente -> branco
  tl.fromTo("#leak", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.16, ease: "power1.in", immediateRender: false }}, 28.80);
  tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.10, ease: "none", immediateRender: false }}, 28.96);
  window.__timelines["clone"] = tl;
}})();
</script>
</body>
</html>
"""
open(os.path.join(AQUI, "index.html"), "w").write(doc)
for k, t, i, d, y in leg: print(f"{i:6.2f} +{d:5.2f}  {t}")
