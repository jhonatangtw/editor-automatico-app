#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o projeto HyperFrames inteiro a partir de roteiro.json + transcricao.json + marca.json.

    python3 scripts/premium/construir.py PASTA_DO_PROJETO [--sfx-auto]

Escreve compositions/*.html, index.html e (com --sfx-auto ou se não existir)
sfx-cues.json. NÃO edite os .html à mão: mude o roteiro e rode de novo.

Confere antes de escrever (e para com erro):
- toda âncora "palavra@tempo" existe na transcrição revisada;
- nada passa da duração do vídeo; no máximo 2 cenas ao mesmo tempo;
- lettering de 1–4 palavras por linha, que caiba na largura;
- tudo dentro da zona segura do Reels (topo 192 px, base 20 %, barra direita).
"""
import html
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from comum import TEMPLATES, duracao, gravar_json, ler_json, norm, resolver_tempo, sair  # noqa: E402

W, H = 1080, 1920
ZONA = {"topo": 192, "base": 1536, "trilho_x": 960}   # Reels: UI no alto, 20 % de baixo, barra de ações à direita
LETTER_TOP = 250
avisos = []


def avisar(m):
    avisos.append(m)
    print("! " + m)


# ------------------------------------------------------------------ marca
def hex_rgb(h):
    h = h.lstrip("#")
    return "%d, %d, %d" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def carregar_marca(proj):
    p = os.path.join(proj, "marca.json")
    base_dir = proj
    if not os.path.exists(p):
        p = os.path.join(TEMPLATES, "marca.json")
        base_dir = TEMPLATES
    m = ler_json(p)
    fontes_css, copiar = [], []
    for papel, f in m["fontes"].items():
        arq = f["arquivo"] if os.path.isabs(f["arquivo"]) else os.path.join(base_dir, f["arquivo"])
        if not os.path.exists(arq):
            sair("fonte '%s' não encontrada: %s" % (papel, arq))
        nome = os.path.basename(arq)
        copiar.append((arq, os.path.join(proj, "assets", "fonts", nome)))
        fmt = {"woff2": "woff2", "woff": "woff", "ttf": "truetype", "otf": "opentype"}.get(nome.rsplit(".", 1)[-1].lower(), "truetype")
        fontes_css.append('@font-face { font-family: "%s"; font-weight: 100 900; src: url("assets/fonts/%s") format("%s"); }' % (f["familia"], nome, fmt))
    c = m["cores"]
    tok = {
        "__FONTES__": "\n    ".join(sorted(set(fontes_css))),
        "__FUNDO__": c["fundo"], "__FUNDO_RGB__": hex_rgb(c["fundo"]), "__FUNDO2__": c.get("fundo2", c["fundo"]),
        "__TEXTO__": c["texto"], "__TEXTO_RGB__": hex_rgb(c["texto"]),
        "__DESTAQUE__": c["destaque"], "__DESTAQUE_RGB__": hex_rgb(c["destaque"]),
        "__DESTAQUE_CLARO__": c.get("destaque_claro", "#ffffff"), "__TINTA__": c.get("tinta_sobre_destaque", "#111111"),
        "__FONTE_TITULO__": m["fontes"]["titulo"]["familia"], "__PESO_TITULO__": str(m["fontes"]["titulo"].get("peso", 700)),
        "__FONTE_LEGENDA__": m["fontes"]["legenda"]["familia"], "__PESO_LEGENDA__": str(m["fontes"]["legenda"].get("peso", 800)),
        "__FONTE_MONO__": m["fontes"]["mono"]["familia"], "__PESO_MONO__": str(m["fontes"]["mono"].get("peso", 500)),
        "__CAIXA__": "text-transform: uppercase;" if m.get("lettering", {}).get("maiusculas", True) else "",
        "__TAM_LEGENDA__": str(m.get("legenda", {}).get("tamanho", 60)),
        "__COR_ATIVA__": c["destaque"] if m.get("legenda", {}).get("palavra_ativa_em_destaque", True) else c["texto"],
    }
    return m, tok, copiar


def aplicar(txt, tok):
    for k in sorted(tok, key=len, reverse=True):
        txt = txt.replace(k, tok[k])
    return txt


def tpl(nome):
    return open(os.path.join(TEMPLATES, "cenas", nome), encoding="utf-8").read()


# ------------------------------------------------------------------ medidas
def tam_que_cabe(texto, base, largura=990, fator=0.6):
    n = max(1, len(texto))
    return int(min(base, largura / (fator * n)))


def slug(s):
    s = norm(s).replace(" ", "-")
    return re.sub(r"-+", "-", s).strip("-") or "cena"


def marcar_destaque(texto):
    """'de *vocês.*' -> HTML com o trecho entre * em destaque."""
    partes = re.split(r"(\*[^*]+\*)", texto)
    out = []
    for p in partes:
        if p.startswith("*") and p.endswith("*"):
            out.append('<span class="x-gold">%s</span>' % html.escape(p[1:-1]))
        else:
            out.append(html.escape(p))
    return "".join(out), re.sub(r"\*", "", texto)


# ------------------------------------------------------------------ cenas
class Cena:
    def __init__(self, c, P, DUR, idx):
        self.id = slug(c.get("id") or "cena-%d" % idx)
        self.ini = resolver_tempo(c.get("ini", 0), P)
        self.fim = resolver_tempo(c.get("fim"), P) if c.get("fim") is not None else None
        self.c, self.P, self.DUR = c, P, DUR
        self.html, self.css, self.js = [], [], []
        self.n_video = 0
        self.sfx = []
        self.punch = []

    def t(self, x, campo="s"):
        v = resolver_tempo(x, self.P, campo)
        if v is not None and (v < -0.01 or v > self.DUR + 0.01):
            sair("cena '%s': tempo %.2f fora do vídeo (0–%.2f)" % (self.id, v, self.DUR))
        return v

    # --- lettering em batidas (1–4 palavras por linha)
    def beats(self):
        B = self.c.get("beats", [])
        tops = []
        for bi, b in enumerate(B):
            bid = "b%d" % bi
            linhas = b.get("linhas", [])
            if not linhas:
                continue
            ini_beat = None
            y = LETTER_TOP
            partes_html = []
            if b.get("kicker"):
                kid = "%s-k" % bid
                partes_html.append('<div id="%s-%s" class="x-kick" style="top:%dpx"><i></i><span>%s</span><i></i></div>' % (self.id, kid, 196, html.escape(b["kicker"])))
            for li, L in enumerate(linhas):
                lid = "%s-l%d" % (bid, li)
                if "partes" in L:
                    textos = [p["texto"] for p in L["partes"]]
                    plano = " ".join(re.sub(r"\*", "", x) for x in textos)
                else:
                    plano = re.sub(r"\*", "", L["texto"])
                pal = len(plano.split())
                if pal > 4:
                    avisar("cena %s: linha com %d palavras ('%s'). Lettering bom é 1–4 palavras: quebre em outra batida." % (self.id, pal, plano))
                gold = bool(L.get("destaque"))
                base = L.get("tamanho") or (130 if len(linhas) == 1 else (120 if gold else 104))
                fs = tam_que_cabe(plano, base)
                if fs < 64:
                    avisar("cena %s: '%s' só cabe com fonte %d px — texto longo demais para lettering." % (self.id, plano, fs))
                h = int(fs * 1.04)
                cls = "x-ln x-gold" if gold else "x-ln"
                if "partes" in L:
                    spans = []
                    for pi, p in enumerate(L["partes"]):
                        inner, _ = marcar_destaque(p["texto"])
                        g = ' class="x-gold"' if p.get("destaque") else ""
                        spans.append('<span id="%s-%s-p%d" style="display:inline-block"%s>%s</span>' % (self.id, lid, pi, g, inner))
                    inner = " ".join(spans)
                else:
                    inner, _ = marcar_destaque(L["texto"])
                partes_html.append('<div id="%s-%s" class="%s" style="top:%dpx;height:%dpx;font-size:%dpx">%s</div>' % (self.id, lid, cls, y, h, fs, inner))
                tops.append(y + h)
                # animação
                if "partes" in L:
                    for pi, p in enumerate(L["partes"]):
                        tt = self.t(p["em"])
                        ini_beat = tt if ini_beat is None else min(ini_beat, tt)
                        self.anim_linha("%s-p%d" % (lid, pi), tt, bool(p.get("destaque")))
                        self.punch.append((tt - 0.04, "forte" if p.get("destaque") else "leve"))
                else:
                    tt = self.t(L["em"])
                    ini_beat = tt if ini_beat is None else min(ini_beat, tt)
                    self.anim_linha(lid, tt, gold)
                    self.punch.append((tt - 0.04, "forte" if gold else "leve"))
                    if gold:
                        self.sfx.append([round(tt - 0.04, 2), "impact-soft", 0.32, 0])
                y += h + 8
            if b.get("kicker"):
                self.js.append('kick("%s-k", %.3f);' % (bid, self.t(b.get("kicker_em", ini_beat))))
            # fim da batida: 'ate' ou logo antes da próxima
            if b.get("ate") is not None:
                fim = self.t(b["ate"])
            elif bi + 1 < len(B):
                nxt = B[bi + 1]
                prims = [self.t(p["em"]) for L2 in nxt["linhas"] for p in (L2.get("partes") or [L2])]
                fim = min(prims) - 0.08
            else:
                fim = (self.fim or self.DUR) - 0.15
            vis = self.c.get("visual") or {}
            if vis.get("tipo") == "hit":          # o lettering sai antes do "hit" dourado entrar
                th = self.t(vis["em"])
                if ini_beat < th < fim + 0.12:
                    fim = th - 0.12
            self.html.append('      <div id="%s-%s" class="x-beat">\n        %s\n      </div>' % (self.id, bid, "\n        ".join(partes_html)))
            self.js.append('out("%s", %.3f, %s);' % (bid, fim, "0.14" if bi + 1 == len(B) else "0.12"))
            if bi > 0:
                self.sfx.append([round(ini_beat - 0.06, 2), "whoosh-soft", 0.14, 0])
        if tops and max(tops) > 1000:
            avisar("cena %s: lettering desce até y=%d (ideal < 700, acima do rosto)." % (self.id, max(tops)))

    def anim_linha(self, lid, t, gold):
        if t <= 0.05 and self.ini <= 0.01:
            self.js.append('settle("%s");' % lid)       # 1º quadro já com texto (gancho)
        else:
            self.js.append('pop("%s", %.3f, %s);' % (lid, t, "true" if gold else "false"))

    # --- visuais
    def visual(self, proj):
        v = self.c.get("visual")
        if not v:
            return
        tipo = v["tipo"]
        vi = self.t(v.get("ini", self.ini + 0.05))
        vf = self.t(v.get("fim", (self.fim or self.DUR) - 0.2))
        getattr(self, "v_" + tipo, lambda *a: sair("visual desconhecido: %s (use hit, telas, tela_unica, aprovacao, cta)" % tipo))(v, vi, vf, proj)

    def _midia(self, arq, proj, eid, ini_rel, dur):
        caminho = os.path.join(proj, arq)
        if not os.path.exists(caminho):
            sair("cena %s: arquivo %s não existe na pasta do projeto (as telas vêm da SUA pasta: novo_projeto.py --telas)." % (self.id, arq))
        if arq.lower().endswith((".mp4", ".mov", ".webm", ".m4v")):
            self.n_video += 1
            return ('<video id="%s" class="clip" src="%s" muted playsinline preload="auto" data-start="%.3f" data-duration="%.3f" '
                    'data-media-start="0" data-track-index="%d"></video>' % (eid, arq, max(0, ini_rel), dur, self.n_video))
        return '<img id="%s" src="%s" alt="">' % (eid, arq)

    def v_hit(self, v, vi, vf, proj):
        t1 = self.t(v["em"])
        t2 = self.t(v.get("em2", t1 + 0.22))
        l1, l2 = (v["linhas"] + [""])[:2]
        fs = min(tam_que_cabe(l1, 200, 1000, 0.62), tam_que_cabe(l2 or l1, 200, 1000, 0.62))
        top = 196
        big = lambda ident, y, txt: '<div %sclass="x-big" style="top:%dpx;height:%dpx;font-size:%dpx">%s</div>' % (
            ('id="%s-%s" ' % (self.id, ident)) if ident else "", y, fs, fs, html.escape(txt))
        self.html.append('''      <div id="%s-hflash" class="x-flash" data-layout-allow-overflow></div>
      <div id="%s-hit" style="position:absolute;left:0;right:0;top:%dpx;height:440px" data-layout-allow-overflow>
        %s
        %s
        <div id="%s-shine" class="x-shine" data-layout-allow-overflow><div id="%s-shinec" class="x-shine-copy">%s%s</div></div>
      </div>''' % (self.id, self.id, top, big("h1", 0, l1), big("h2", fs + 6, l2) if l2 else "", self.id, self.id,
                   big(None, 0, l1), big(None, fs + 6, l2) if l2 else ""))
        self.js += [
            'tl.fromTo($("hflash"), { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1.05, duration: 0.22, ease: "power2.out" }, at(%.3f));' % t1,
            'tl.fromTo($("hflash"), { opacity: 1 }, { opacity: 0.25, duration: 0.5, ease: "power2.inOut", immediateRender: false }, at(%.3f));' % (t1 + 0.22),
            'tl.fromTo($("h1"), { opacity: 0, scale: 1.45, filter: "blur(18px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.36, ease: "power4.out" }, at(%.3f));' % t1,
        ]
        if l2:
            self.js.append('tl.fromTo($("h2"), { opacity: 0, scale: 1.45, filter: "blur(18px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.36, ease: "power4.out" }, at(%.3f));' % t2)
        self.js += [
            'tl.fromTo($("shine"), { x: -340 }, { x: 1100, duration: 0.6, ease: "power2.inOut" }, at(%.3f));' % (t2 + 0.13),
            'tl.fromTo($("shinec"), { x: 340 }, { x: -1100, duration: 0.6, ease: "power2.inOut" }, at(%.3f));' % (t2 + 0.13),
            'out("hit", %.3f, 0.16); out("hflash", %.3f, 0.16);' % (vf, vf),
        ]
        self.punch.append((t1 - 0.04, "forte"))
        self.sfx += [[round(max(0, t1 - 1.7), 2), "riser", 0.22, 1.7], [round(t1 - 0.02, 2), "impact-soft", 0.55, 0], [round(t1, 2), "shimmer", 0.3, 0]]

    def v_telas(self, v, vi, vf, proj):
        itens = v["itens"]
        if v.get("passos", "auto") == "auto":
            n = len(itens) - 1
            a, b = vi + 0.9, vf - 0.7
            passos = [round(a + k * (b - a) / max(1, n), 3) for k in range(n)] if n > 0 else []
        else:
            passos = [self.t(x) for x in v["passos"]]
        plates = []
        for k, it in enumerate(itens):
            m = self._midia(it["arquivo"], proj, "%s-pm%d" % (self.id, k), vi - self.ini, vf - vi)
            plates.append('<div id="%s-pl%d" class="x-pl tl-pl" style="left:255px;top:1062px;width:570px;height:350px" data-layout-allow-overflow>'
                          '<div class="x-face">%s<div class="x-gloss"></div><div class="x-dimmer"></div><div class="x-rim"></div></div></div>' % (self.id, k, m))
        rot = [list(it.get("rotulo", ["", ""])) + [""] * 2 for it in itens]
        self.html.append('''      <div id="%s-rise" style="position:absolute;inset:0" data-layout-allow-overflow><div id="%s-cam" style="position:absolute;inset:0" data-layout-allow-overflow>
        %s
      </div></div>
      <div id="%s-labw" style="position:absolute;left:0;right:0;top:1002px;display:flex;justify-content:center"><div class="x-chip" style="position:relative"><span id="%s-lapp" class="x-sub"></span><span id="%s-lnom"></span></div></div>''' % (
            self.id, self.id, "\n        ".join(plates), self.id, self.id, self.id))
        self.js.append('''      (function () {
        const N = %d, STEPS = %s.map(at), SD = 0.36, ROT = %s;
        const ez = gsap.parseEase("power3.inOut");
        const els = []; for (let i = 0; i < N; i++) { const el = $("pl" + i); els.push({ el: el, dim: el.querySelector(".x-dimmer"), rim: el.querySelector(".x-rim") }); }
        const cam = $("cam"), app = $("lapp"), nom = $("lnom"), lab = $("labw");
        function pAt(t) { let p = 0; for (const s of STEPS) { if (t >= s + SD) p += 1; else if (t > s) p += ez((t - s) / SD); } return p; }
        function layout(t) {
          const p = pAt(t);
          els.forEach((o, i) => {
            const d = i - p, ad = Math.abs(d), s = d < 0 ? -1 : 1, c = Math.min(ad, 1), far = Math.max(0, ad - 1);
            o.el.style.transform = "translateX(" + (s * (c * 420 + far * 200)).toFixed(2) + "px) perspective(1500px) translateZ(" + (-c * 280 - far * 150).toFixed(2) + "px) rotateY(" + (-s * c * 48).toFixed(2) + "deg)";
            o.el.style.zIndex = String(100 - Math.round(ad * 10));
            o.el.style.opacity = String(Math.max(0, Math.min(1, 1 - (ad - 2.2) * 1.5)));
            o.dim.style.opacity = String(Math.min(0.62, c * 0.62 + far * 0.1));
            o.rim.style.opacity = String(Math.max(0, 1 - ad * 2.2) * 0.95);
          });
          const k = Math.min(N - 1, Math.round(p)), frac = Math.abs(p - k);
          app.textContent = ROT[k][0]; nom.textContent = ROT[k][1];
          lab.style.opacity = String(Math.max(0, 1 - frac * 3.2));
          cam.style.transform = "scale(" + (1 + t * 0.006).toFixed(4) + ")";
        }
        layout(0);
        const drv = { t: 0 };
        tl.fromTo(drv, { t: 0 }, { t: DUR, duration: DUR, ease: "none", onUpdate: () => layout(drv.t) }, 0);
      })();''' % (len(itens), json.dumps(passos), json.dumps(rot, ensure_ascii=False)))
        self.js += [
            'tl.fromTo($("rise"), { y: 520, opacity: 0, rotationX: 24, transformPerspective: 1500 }, { y: 0, opacity: 1, rotationX: 0, duration: 0.6, ease: "power3.out" }, at(%.3f));' % vi,
            'tl.fromTo($("labw"), { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power2.out" }, at(%.3f));' % (vi + 0.5),
            'tl.fromTo($("rise"), { opacity: 1, scale: 1, filter: "blur(0px)" }, { opacity: 0, scale: 1.12, filter: "blur(8px)", duration: 0.25, ease: "power2.in", immediateRender: false }, at(%.3f));' % vf,
            'out("labw", %.3f, 0.2);' % vf,
        ]
        self.sfx.append([round(vi, 2), "whoosh", 0.24, 0])
        self.sfx += [[round(p, 2), "tick", 0.18, 0.8] for p in passos]
        if not self._modo_ok("dividido", vi, vf):
            avisar("cena %s: 'telas' fica embaixo do rosto — ponha o layout em \"dividido\" de %.2f a %.2f." % (self.id, vi, vf))

    def v_tela_unica(self, v, vi, vf, proj):
        m = self._midia(v["arquivo"], proj, "%s-um" % self.id, vi - self.ini, vf - vi)
        chip = v.get("rotulo", "")
        self.html.append('''      <div id="%s-ustage" style="position:absolute;inset:0" data-layout-allow-overflow>
        <div id="%s-uplate" class="x-pl" style="left:160px;top:1030px;width:760px;height:390px"><div class="x-face">%s<div class="x-gloss"></div><div id="%s-usweep" style="position:absolute;top:-10%%;left:0;width:220px;height:120%%;transform:skewX(-20deg);background:linear-gradient(90deg,rgba(%s,0) 0%%,rgba(%s,0.22) 40%%,rgba(255,255,255,0.35) 50%%,rgba(%s,0.22) 60%%,rgba(%s,0) 100%%)"></div><div class="x-rim"></div></div></div>
        %s
      </div>''' % (self.id, self.id, m, self.id, "__DESTAQUE_RGB__", "__DESTAQUE_RGB__", "__DESTAQUE_RGB__", "__DESTAQUE_RGB__",
                   ('<div id="%s-uchipw" style="position:absolute;left:0;right:0;top:972px;display:flex;justify-content:center"><div class="x-chip" style="position:relative">%s</div></div>' % (self.id, html.escape(chip))) if chip else ""))
        self.js += [
            'tl.fromTo($("uplate"), { opacity: 0, y: 260, rotationX: 26, rotationY: 0, transformPerspective: 1500 }, { opacity: 1, y: 0, rotationX: 8, rotationY: -6, duration: 0.6, ease: "power3.out" }, at(%.3f));' % vi,
            'tl.fromTo($("uplate"), { scale: 1, rotationY: -6 }, { scale: 1.05, rotationY: 6, duration: %.3f, ease: "none", immediateRender: false }, at(%.3f));' % (max(0.2, vf - vi - 0.6), vi + 0.6),
            'tl.fromTo($("usweep"), { x: -260 }, { x: 980, duration: 0.9, ease: "power2.inOut" }, at(%.3f));' % (vi + 0.7),
            'tl.fromTo($("ustage"), { opacity: 1, scale: 1, filter: "blur(0px)" }, { opacity: 0, scale: 1.1, filter: "blur(8px)", duration: 0.25, ease: "power2.in", immediateRender: false }, at(%.3f));' % vf,
        ]
        if chip:
            self.js.append('fin("uchipw", %.3f); ' % (vi + 0.4))
        self.sfx.append([round(vi, 2), "whoosh", 0.22, 0])
        if not self._modo_ok("dividido", vi, vf):
            avisar("cena %s: 'tela_unica' fica embaixo do rosto — use layout \"dividido\" de %.2f a %.2f." % (self.id, vi, vf))

    def v_aprovacao(self, v, vi, vf, proj):
        tit = (v.get("titulo") or ["Você", "aprova"]) + [""]
        st = (v.get("status") or ["aguardando o seu ok…", "aprovado"]) + [""]
        tc = self.t(v["carimbo"])
        self.html.append('''      <div id="%s-card" style="position:absolute;left:170px;top:1080px;width:740px;height:300px;transform-origin:50%% 50%%">
        <div class="x-face" style="border-radius:26px;background:linear-gradient(160deg,__FUNDO2__ 0%%,__FUNDO__ 100%%)">
          <svg style="position:absolute;left:56px;top:60px" viewBox="0 0 180 180" width="180" height="180">
            <circle cx="90" cy="90" r="80" fill="none" stroke="rgba(__DESTAQUE_RGB__,0.25)" stroke-width="6" />
            <circle id="%s-arc" cx="90" cy="90" r="80" fill="none" stroke="__DESTAQUE__" stroke-width="6" stroke-linecap="round" stroke-dasharray="503" stroke-dashoffset="503" transform="rotate(-90 90 90)" />
            <circle id="%s-disc" cx="90" cy="90" r="66" fill="__DESTAQUE__" />
            <path id="%s-check" d="M58 92 L82 116 L124 68" fill="none" stroke="__TINTA__" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="110" stroke-dashoffset="110" />
          </svg>
          <div class="x-ln" style="left:280px;right:auto;text-align:left;top:62px;height:80px;font-size:%dpx">%s</div>
          <div class="x-ln x-gold" style="left:280px;right:auto;text-align:left;top:142px;height:82px;font-size:%dpx">%s</div>
          <div id="%s-st1" style="position:absolute;left:282px;top:238px;height:30px;white-space:nowrap;font-family:'__FONTE_MONO__',monospace;font-size:22px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(__TEXTO_RGB__,0.55)">%s</div>
          <div id="%s-st2" style="position:absolute;left:282px;top:238px;height:30px;white-space:nowrap;font-family:'__FONTE_MONO__',monospace;font-size:22px;letter-spacing:0.14em;text-transform:uppercase;color:__DESTAQUE__">%s</div>
          <div id="%s-rim" class="x-rim" style="border-radius:26px"></div>
        </div>
      </div>''' % (self.id, self.id, self.id, self.id, tam_que_cabe(tit[0], 78, 600), html.escape(tit[0]), tam_que_cabe(tit[1], 80, 600), html.escape(tit[1]),
                   self.id, html.escape(st[0]), self.id, html.escape(st[1]), self.id))
        self.js += [
            'tl.fromTo($("card"), { opacity: 0, y: 220, rotationX: 24, transformPerspective: 1500 }, { opacity: 1, y: 0, rotationX: 6, duration: 0.55, ease: "power3.out" }, at(%.3f));' % vi,
            'tl.fromTo($("card"), { scale: 1 }, { scale: 1.05, duration: %.3f, ease: "none", immediateRender: false }, at(%.3f));' % (max(0.2, vf - vi - 0.55), vi + 0.55),
            'tl.fromTo($("arc"), { strokeDashoffset: 503 }, { strokeDashoffset: 0, duration: %.3f, ease: "none" }, at(%.3f));' % (max(0.3, tc - vi - 0.55), vi + 0.55),
            'tl.fromTo($("disc"), { opacity: 0, scale: 0.6, transformOrigin: "50%% 50%%" }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2.2)" }, at(%.3f));' % (tc - 0.04),
            'tl.fromTo($("check"), { strokeDashoffset: 110 }, { strokeDashoffset: 0, duration: 0.28, ease: "power2.out" }, at(%.3f));' % (tc + 0.08),
            'tl.fromTo($("rim"), { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "power2.out" }, at(%.3f));' % tc,
            'out("st1", %.3f, 0.15);' % tc,
            'tl.fromTo($("st2"), { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power2.out" }, at(%.3f));' % (tc + 0.06),
            'tl.fromTo($("card"), { opacity: 1, filter: "blur(0px)" }, { opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power2.in", immediateRender: false }, at(%.3f));' % vf,
        ]
        self.punch.append((tc - 0.04, "forte"))
        self.sfx += [[round(vi, 2), "whoosh-soft", 0.16, 0], [round(tc, 2), "success-chime", 0.3, 0]]

    def v_cta(self, v, vi, vf, proj):
        l1, l2 = (v.get("linhas", ["Link", "na bio"]) + [""])[:2]
        url, pil, com, kk = v.get("url", ""), v.get("pilula", "Link na bio"), v.get("comentario", ""), v.get("kicker", "")
        f1, f2 = tam_que_cabe(l1, 112, 1000), tam_que_cabe(l2, 170, 1000, 0.62)
        self.html.append('''      <div id="%s-pip" style="position:absolute;left:310px;top:190px;width:460px;height:620px;border-radius:36px;box-shadow:inset 0 0 0 2px __DESTAQUE__,0 0 0 8px rgba(__FUNDO_RGB__,0.9),0 0 0 9px rgba(__DESTAQUE_RGB__,0.3),0 0 70px rgba(__DESTAQUE_RGB__,0.35)"></div>
      <div id="%s-end" style="position:absolute;inset:0;transform-origin:540px 900px" data-layout-allow-overflow>
        %s
        <div id="%s-l1" class="x-ln" style="top:900px;height:%dpx;font-size:%dpx">%s</div>
        <div id="%s-l2" class="x-ln x-gold" style="top:%dpx;height:%dpx;font-size:%dpx;letter-spacing:-0.045em">%s</div>
        %s
        <div id="%s-pill" style="position:absolute;left:0;right:0;top:1270px;margin:0 auto;width:420px;height:76px;border-radius:38px;background:__DESTAQUE__;box-shadow:0 14px 36px rgba(__DESTAQUE_RGB__,0.35);display:flex;justify-content:center;align-items:center;gap:14px;font-family:'__FONTE_TITULO__',sans-serif;font-weight:__PESO_TITULO__;font-size:34px;text-transform:uppercase;color:__TINTA__;white-space:nowrap"><span style="width:13px;height:13px;border-radius:50%%;background:__TINTA__;display:block"></span><span>%s</span></div>
        %s
      </div>''' % (self.id, self.id,
                   ('<div id="%s-kick" class="x-kick" style="top:846px"><i></i><span>%s</span><i></i></div>' % (self.id, html.escape(kk))) if kk else "",
                   self.id, int(f1 * 1.04), f1, html.escape(l1), self.id, 900 + int(f1 * 1.04) + 4, int(f2 * 1.02), f2, html.escape(l2),
                   ('<div id="%s-url" style="position:absolute;left:40px;right:40px;top:1196px;height:56px;text-align:center;white-space:nowrap;font-family:\'__FONTE_MONO__\',monospace;font-size:%dpx;letter-spacing:0.03em;color:__DESTAQUE__">%s</div>' % (self.id, tam_que_cabe(url, 42, 980, 0.62), html.escape(url))) if url else "",
                   self.id, html.escape(pil),
                   ('<div id="%s-com" style="position:absolute;left:0;right:0;top:1360px;margin:0 auto;width:600px;height:58px;border-radius:29px;box-shadow:inset 0 0 0 2px rgba(__DESTAQUE_RGB__,0.8);background:rgba(__DESTAQUE_RGB__,0.08);display:flex;justify-content:center;align-items:center;white-space:nowrap;font-family:\'__FONTE_MONO__\',monospace;font-size:24px;letter-spacing:0.1em;text-transform:uppercase;color:rgba(__TEXTO_RGB__,0.85)">%s</div>' % (self.id, html.escape(com))) if com else ""))
        self.js += [
            'fin("pip", %.3f, 0.35);' % (vi + 0.4),
            'tl.fromTo($("end"), { scale: 1 }, { scale: 1.03, duration: %.3f, ease: "none" }, at(%.3f));' % (max(0.2, vf - vi), vi),
        ]
        if kk:
            self.js.append('kick("kick", %.3f);' % (vi + 0.35))
        self.js += ['pop("l1", %.3f, false);' % (vi + 0.45), 'pop("l2", %.3f, true);' % (vi + 0.7)]
        if url:
            self.js.append('tl.fromTo($("url"), { opacity: 0, clipPath: "inset(0%% 50%% 0%% 50%%)" }, { opacity: 1, clipPath: "inset(0%% 0%% 0%% 0%%)", duration: 0.5, ease: "power3.out" }, at(%.3f));' % (vi + 0.95))
        self.js.append('tl.fromTo($("pill"), { opacity: 0, scale: 0.7, y: 16 }, { opacity: 1, scale: 1, y: 0, duration: 0.4, ease: "back.out(2.2)" }, at(%.3f));' % (vi + 0.92))
        if com:
            tcom = self.t(v["comentario_em"]) if v.get("comentario_em") is not None else vi + 1.6
            self.js.append('tl.fromTo($("com"), { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }, at(%.3f));' % tcom)
            self.sfx.append([round(tcom, 2), "tick", 0.18, 0.8])
        self.sfx += [[round(vi, 2), "whoosh", 0.28, 0], [round(vi + 0.7, 2), "impact-soft", 0.32, 0], [round(vi + 0.95, 2), "success-chime", 0.26, 0]]
        if not self._modo_ok("pip", vi + 0.3, vf):
            avisar("cena %s: 'cta' foi desenhado para o layout \"pip\" (o rosto vira cartão no alto) a partir de %.2f." % (self.id, vi))

    def _modo_ok(self, modo, a, b):
        L = self.layout
        ativos = [m for (t, m) in L if t <= a + 0.6]
        if not ativos or ativos[-1] != modo:
            return False
        return all(m == modo for (t, m) in L if a + 0.6 < t < b - 0.3)

    def gerar(self, tok):
        txt = tpl("cena.html")
        txt = txt.replace("__BASE__", tpl("base.css")).replace("__ESTILO__", "\n".join(self.css))
        txt = txt.replace("__VISUAL__", "\n".join(h for h in self.html if 'class="x-beat"' not in h))
        txt = txt.replace("__BEATS__", "\n".join(h for h in self.html if 'class="x-beat"' in h))
        txt = txt.replace("__ANIM__", "\n".join("      " + j if not j.startswith("      ") else j for j in self.js))
        txt = txt.replace("__ID__", self.id).replace("__O__", "%.3f" % self.ini).replace("__D__", "%.3f" % (self.fim - self.ini))
        return aplicar(txt, tok)


# ------------------------------------------------------------------ punch-in
def punch_auto(pontos, layout, DUR, marca):
    pi = marca.get("punch_in", {})
    forte, leve, maximo = pi.get("forte", 1.14), pi.get("leve", 1.05), pi.get("maximo", 1.16)

    def modo(t):
        m = layout[0][1]
        for (tt, mm) in layout:
            if tt <= t:
                m = mm
        return m
    pts = sorted((max(0.0, t), k) for t, k in pontos if 0 <= t < DUR)
    limpo = []
    for t, k in pts:
        if modo(t) == "pip":
            continue
        if limpo and t - limpo[-1][0] < 0.45:
            if k == "forte" and limpo[-1][1] != "forte":
                limpo[-1] = (t, "forte")      # a batida forte manda: o snap vai para ela
            continue
        limpo.append((t, k))
    P = []
    if not limpo or limpo[0][0] > 0.05:
        P.append([0.0, round(min(maximo, forte - 0.02), 3), round(min(maximo, forte - 0.04), 3), 0])
    alt = 0
    for t, k in limpo:
        dv = modo(t) == "dividido"
        if k == "forte":
            s = (min(1.09, leve + 0.04) if dv else forte) + (0.01 if alt % 2 else 0)
            snap = 0.15
        else:
            s = (leve - 0.02 if dv else leve) + (0.01 if alt % 2 else -0.01)
            snap = 0.4
        alt += 1
        s = round(min(maximo, max(1.0, s)), 3)
        P.append([round(t, 3), s, round(min(maximo, s + 0.01), 3), snap if t > 0.05 else 0])
    for (t, m) in layout:
        if m == "pip":
            P = [p for p in P if p[0] < t]
            P.append([round(t, 3), 1.0, 1.0, 0.6])
    P.sort(key=lambda p: p[0])
    return P


# ------------------------------------------------------------------ legendas
FRACAS = {"a", "o", "e", "de", "do", "da", "no", "na", "em", "um", "uma", "pra", "te", "que", "ou", "as", "os", "se", "eu", "e", "sua", "seu", "ter", "the", "com", "por"}


def legendas(P, DUR, marca, ocultar):
    W_ = [w for w in P if not w.get("inaudivel")]
    for seq in marca.get("legenda", {}).get("expressoes", []):
        alvo = seq.lower().split()
        n, out, i = len(alvo), [], 0
        while i < len(W_):
            if [norm(x["w"]) for x in W_[i:i + n]] == [norm(x) for x in alvo]:
                out.append({"w": " ".join(x["w"] for x in W_[i:i + n]), "s": W_[i]["s"], "e": W_[i + n - 1]["e"]}); i += n
            else:
                out.append(W_[i]); i += 1
        W_ = out
    W_ = [w for w in W_ if not any(a <= w["s"] < b for a, b in ocultar)]
    maxc = marca.get("legenda", {}).get("max_caracteres", 19)
    grupos, cur = [], []
    for i, w in enumerate(W_):
        cur.append(w)
        nxt = W_[i + 1] if i + 1 < len(W_) else None
        if nxt is None:
            grupos.append(cur); break
        txt = " ".join(x["w"] for x in cur)
        if w["w"][-1:] in ".,!?" or nxt["s"] - w["e"] > 0.28 or len(txt) + 1 + len(nxt["w"]) > maxc:
            grupos.append(cur); cur = []; continue
        if len(cur) >= 3 or (len(cur) == 2 and norm(nxt["w"]) in FRACAS and norm(w["w"]) not in FRACAS):
            grupos.append(cur); cur = []
    divs, js = [], []
    for gi, g in enumerate(grupos):
        s = round(max(0, g[0]["s"] - 0.04), 3)
        e = round(grupos[gi + 1][0]["s"] - 0.04, 3) if gi + 1 < len(grupos) else DUR
        e = min(e, round(g[-1]["e"] + 0.5, 3), DUR)
        if e - s < 0.15:
            e = s + 0.15
        spans = []
        for wi, w in enumerate(g):
            t = w["w"].rstrip(",.")
            spans.append('<span id="cw-%d-%d" class="cw">%s</span>' % (gi, wi, html.escape(t)))
            ws = w["s"]
            we = g[wi + 1]["s"] if wi + 1 < len(g) else w["e"]
            js.append('      word("#cw-%d-%d", %.3f, %.3f);' % (gi, wi, ws, max(we, ws + 0.12)))
        divs.append('      <div id="cg-%d" class="cg">%s</div>' % (gi, "".join(spans)))
        js.append('      group("#cg-%d", %.3f, %.3f);' % (gi, s, e))
    return "\n".join(divs), "\n".join(js), len(grupos)


# ------------------------------------------------------------------ main
def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    proj = os.path.abspath(sys.argv[1])
    sfx_auto = "--sfx-auto" in sys.argv
    R = ler_json(os.path.join(proj, "roteiro.json"))
    T = ler_json(os.path.join(proj, "transcricao.json"))
    P = T["palavras"]
    video = os.path.join(proj, "assets", "video", "fala.mp4")
    if not os.path.exists(video):
        sair("falta assets/video/fala.mp4 — rode novo_projeto.py antes")
    DUR = round(R.get("duracao") or duracao(video), 3)
    marca, tok, copiar = carregar_marca(proj)
    os.makedirs(os.path.join(proj, "assets", "fonts"), exist_ok=True)
    import shutil
    for a, b in copiar:
        if not os.path.exists(b):
            shutil.copy2(a, b)
    tok["__DUR__"] = "%.3f" % DUR

    layout = [[resolver_tempo(t, P), m] for t, m in (R.get("layout") or [[0, "cheio"]])]
    layout.sort(key=lambda x: x[0])
    if layout[0][0] > 0.01:
        layout.insert(0, [0.0, "cheio"])
    for t, m in layout:
        if m not in ("cheio", "dividido", "pip"):
            sair("layout '%s' não existe (use cheio, dividido, pip)" % m)

    cenas = []
    for i, c in enumerate(R["cenas"]):
        ce = Cena(c, P, DUR, i)
        ce.layout = layout
        cenas.append(ce)
    for i, ce in enumerate(cenas):   # fim padrão = início da próxima + 0,3 s de cruzamento
        if ce.fim is None:
            ce.fim = min(DUR, cenas[i + 1].ini + 0.3) if i + 1 < len(cenas) else DUR
        if ce.fim <= ce.ini:
            sair("cena %s termina antes de começar" % ce.id)
    ids = [c.id for c in cenas]
    if len(set(ids)) != len(ids):
        sair("ids de cena repetidos: %s" % ids)
    # no máximo 2 cenas ao mesmo tempo (trilhas 3 e 4 se alternam)
    for i in range(len(cenas) - 2):
        if cenas[i + 2].ini < cenas[i].fim:
            sair("3 cenas ao mesmo tempo (%s, %s, %s): encurte o fim de %s" % (cenas[i].id, cenas[i + 1].id, cenas[i + 2].id, cenas[i].id))

    comp = os.path.join(proj, "compositions")
    os.makedirs(comp, exist_ok=True)
    fixos = {"bg.html", "cam.html", "painel.html", "legendas.html"} | {c.id + ".html" for c in cenas}
    for f in os.listdir(comp):          # cena que saiu do roteiro não pode continuar no projeto
        if f.endswith(".html") and f not in fixos:
            os.remove(os.path.join(comp, f))
    pontos, cues = [], []
    for ce in cenas:
        ce.beats()
        ce.visual(proj)
        pontos += ce.punch
        cues += ce.sfx
        open(os.path.join(comp, ce.id + ".html"), "w", encoding="utf-8").write(ce.gerar(tok))

    PI = R.get("punch_ins", "auto")
    PI = punch_auto(pontos, layout, DUR, marca) if PI == "auto" else [[resolver_tempo(p[0], P)] + list(p[1:]) for p in PI]
    lay_js = json.dumps([[round(t, 3), m] for t, m in layout])
    for nome in ("bg", "cam", "painel"):
        txt = tpl(nome + ".html").replace("__PUNCH__", json.dumps(PI)).replace("__LAYOUT__", lay_js)
        open(os.path.join(comp, nome + ".html"), "w", encoding="utf-8").write(aplicar(txt, tok))

    oc = [[resolver_tempo(a, P), resolver_tempo(b, P)] for a, b in R.get("legenda", {}).get("ocultar", [])]
    if R.get("legenda", {}).get("ligada", True):
        g, j, ng = legendas(P, DUR, marca, oc)
        txt = tpl("legendas.html").replace("__GRUPOS__", g).replace("__PALAVRAS__", j)
        open(os.path.join(comp, "legendas.html"), "w", encoding="utf-8").write(aplicar(txt, tok))
    else:
        ng = 0

    # SFX: automáticos a partir das batidas (o aluno pode editar sfx-cues.json à mão depois)
    cues_p = os.path.join(proj, "sfx-cues.json")
    if sfx_auto or not os.path.exists(cues_p):
        cues = sorted([c for c in cues if 0 <= c[0] < DUR - 0.2], key=lambda c: c[0])
        dedup = []
        for c in cues:
            if dedup and c[1] == dedup[-1][1] and c[0] - dedup[-1][0] < 0.3:
                continue
            dedup.append(c)
        if not dedup or dedup[0][0] > 0.2:
            dedup.insert(0, [0.0, "whoosh-soft", 0.3, 0])
        dedup.append([round(max(0, DUR - 0.8), 2), "swell-out", 0.3, 0])
        gravar_json(cues_p, dedup)
    cues = ler_json(cues_p)
    faltam = sorted({c[1] for c in cues if not os.path.exists(os.path.join(proj, "assets", "sfx", c[1] + ".mp3"))})
    if faltam:
        avisar("SFX sem arquivo em assets/sfx: %s — rode gerar_kit_sfx.py ou ponha os seus (.mp3 com esse nome)." % ", ".join(faltam))
        cues = [c for c in cues if c[1] not in faltam]

    # index.html
    hosts = ['      <div id="el-bg" class="scene" data-composition-id="bg" data-composition-src="compositions/bg.html" data-start="0" data-duration="%.3f" data-track-index="0" data-width="1080" data-height="1920"></div>' % DUR,
             '      <div id="el-cam" class="scene" data-composition-id="cam" data-composition-src="compositions/cam.html" data-start="0" data-duration="%.3f" data-track-index="1" data-width="1080" data-height="1920"></div>' % DUR,
             '      <div id="el-painel" class="scene" data-composition-id="painel" data-composition-src="compositions/painel.html" data-start="0" data-duration="%.3f" data-track-index="2" data-width="1080" data-height="1920"></div>' % DUR]
    for i, ce in enumerate(cenas):
        hosts.append('      <div id="el-%s" class="scene" data-composition-id="%s" data-composition-src="compositions/%s.html" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-width="1080" data-height="1920"></div>'
                     % (ce.id, ce.id, ce.id, ce.ini, ce.fim - ce.ini, 3 + i % 2))
    if ng:
        hosts.append('      <div id="el-legendas" class="scene" data-composition-id="legendas" data-composition-src="compositions/legendas.html" data-start="0" data-duration="%.3f" data-track-index="6" data-track-kind="captions" data-width="1080" data-height="1920"></div>' % DUR)
    aud = ['      <audio id="a-voz" src="assets/audio/voz.wav" data-start="0" data-duration="%.3f" data-track-index="10" data-volume="1"></audio>' % DUR]
    mus = (R.get("musica") or {}).get("arquivo")
    if mus:
        if not os.path.exists(os.path.join(proj, mus)):
            sair("música %s não existe na pasta do projeto" % mus)
        aud.append('      <audio id="a-musica" src="%s" data-start="0" data-duration="%.3f" data-track-index="11" data-volume="0.07"></audio>' % (mus, DUR))
    for n, (t, nome, v, cap) in enumerate(cues):
        f = os.path.join(proj, "assets", "sfx", nome + ".mp3")
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout or 1)
        d = round(min(min(d, cap) if cap else d, DUR - t), 3)
        aud.append('      <audio id="sfx-%02d" src="assets/sfx/%s.mp3" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-volume="%s"></audio>' % (n, nome, t, d, 20 + n, v))
    fundo = marca["cores"]["fundo"]
    idx = '''<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 100%%; height: 100%%; overflow: hidden; background: %s; }
      #root { position: relative; width: 100%%; height: 100%%; overflow: hidden; background: %s; }
      .scene { position: absolute; inset: 0; width: 100%%; height: 100%%; }
    </style>
  </head>
  <body>
    <!-- gerado por construir.py — edite roteiro.json / marca.json / sfx-cues.json e rode de novo -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="%.3f" data-fps="30" data-width="1080" data-height="1920">
%s
%s
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({ paused: true });
      window.__timelines["main"].to({}, { duration: %.3f }, 0);
    </script>
  </body>
</html>
''' % (fundo, fundo, DUR, "\n".join(hosts), "\n".join(aud), DUR)
    open(os.path.join(proj, "index.html"), "w", encoding="utf-8").write(idx)
    print("ok: %d cenas, %d punch-ins, %d grupos de legenda, %d SFX, %.2f s" % (len(cenas), len(PI), ng, len(cues), DUR))
    if avisos:
        print("%d aviso(s) acima — leia antes de renderizar." % len(avisos))


if __name__ == "__main__":
    main()
