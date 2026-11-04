# -*- coding: utf-8 -*-
"""Funções compartilhadas pelos scripts do Editor de Reels.

Nada aqui tem caminho fixo de máquina: tudo vem do argumento, da pasta do
projeto ou do ambiente do aluno.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
TEMPLATES = os.path.join(SKILL, "templates")


def sair(msg, codigo=1):
    print("x " + msg, file=sys.stderr)
    sys.exit(codigo)


def exigir(binario):
    if not shutil.which(binario):
        sair("não achei o comando '%s'. Rode scripts/requisitos.sh e instale o que faltar." % binario)


def ffprobe_json(caminho):
    exigir("ffprobe")
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", caminho],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sair("ffprobe não conseguiu ler %s: %s" % (caminho, r.stderr.strip()[:300]))
    return json.loads(r.stdout)


def duracao(caminho):
    d = ffprobe_json(caminho)
    return float(d["format"].get("duration") or 0)


def info_video(caminho):
    """Resumo do vídeo: tamanho, fps, rotação, cor (HDR?), duração."""
    d = ffprobe_json(caminho)
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in d["streams"] if s.get("codec_type") == "audio"), None)
    if not v:
        sair("%s não tem trilha de vídeo" % caminho)
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if "rotate" in (v.get("tags") or {}):
        rot = int(v["tags"]["rotate"])
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1)
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) in (90, 270):
        w, h = h, w
    trc = v.get("color_transfer") or ""
    hdr = "hlg" if trc == "arib-std-b67" else ("pq" if trc == "smpte2084" else "")
    return {
        "arquivo": caminho, "codec": v.get("codec_name"), "largura": w, "altura": h, "fps": round(fps, 3),
        "rotacao": rot, "pix_fmt": v.get("pix_fmt"), "transfer": trc, "primaries": v.get("color_primaries") or "",
        "hdr": hdr, "duracao": float(d["format"].get("duration") or 0),
        "audio": bool(a), "audio_hz": int(a["sample_rate"]) if a else 0,
        "bitrate_mbps": round(float(d["format"].get("bit_rate") or 0) / 1e6, 1),
    }


def ler_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def gravar_json(caminho, dado):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dado, f, ensure_ascii=False, indent=1)


def norm(txt):
    """minúsculo, sem acento, sem pontuação — para comparar palavras."""
    t = unicodedata.normalize("NFD", txt.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def tokens(txt):
    return [x for x in norm(txt).split() if x]


# ------------------------------------------------------------------ áudio
def pcm16k(caminho, ini=None, fim=None):
    """Áudio mono 16 kHz float32 (numpy) — o mesmo formato que o Whisper usa."""
    import numpy as np
    exigir("ffmpeg")
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if ini is not None:
        cmd += ["-ss", "%.3f" % ini]
    if fim is not None:
        cmd += ["-to", "%.3f" % fim] if ini is None else ["-t", "%.3f" % (fim - ini)]
    cmd += ["-i", caminho, "-map", "0:a:0", "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def rms_db(y, passo=160):
    """RMS em dBFS a cada 10 ms (160 amostras a 16 kHz)."""
    import numpy as np
    n = len(y) // passo
    if n == 0:
        return np.zeros(0)
    return 20 * np.log10(np.sqrt((y[:n * passo].reshape(n, passo) ** 2).mean(1)) + 1e-9)


def limiar_auto(r):
    """Limiar da fala RELATIVO À VOZ: nível forte da voz (percentil 90) - 24 dB, preso entre -52 e -34 dBFS.

    Não usa o piso de ruído: celular costuma ter noise gate (silêncio digital de -180 dB),
    o que torna qualquer percentil de "piso" sem sentido. Num bruto real de iPhone isto deu
    -45 dB, o mesmo valor que acertou as bordas de todos os takes conferidos de ouvido.
    """
    import numpy as np
    w = r[r > -100] if len(r) else r
    if len(w) < 50:
        return -46.0
    voz = float(np.percentile(w, 90))
    return max(-52.0, min(-34.0, voz - 24.0))


def nivel_voz(r, a, b, limiar):
    """Nível médio da voz (só quadros acima do limiar) e fração do trecho com voz."""
    import numpy as np
    seg = r[int(a * 100):int(b * 100)]
    if not seg.size:
        return -99.0, 0.0
    v = seg[seg > limiar]
    return (round(float(v.mean()), 1) if v.size else -99.0), round(v.size / float(seg.size), 2)


def trechos_de_fala(r, limiar, juntar=0.25, minimo=0.08, offset=0.0):
    """Trechos [ini, fim] em segundos com energia acima do limiar (borda por energia)."""
    out, s = [], None
    for i, v in enumerate(r > limiar):
        if v and s is None:
            s = i
        if not v and s is not None:
            out.append([s / 100.0, i / 100.0]); s = None
    if s is not None:
        out.append([s / 100.0, len(r) / 100.0])
    m = []
    for x in out:
        if m and x[0] - m[-1][1] < juntar:
            m[-1][1] = x[1]
        else:
            m.append(x)
    return [(round(a + offset, 2), round(b + offset, 2)) for a, b in m if b - a > minimo]


# ------------------------------------------------------------------ tempo por palavra
def resolver_tempo(x, palavras, campo="s"):
    """Âncora de tempo do roteiro.

    - número          -> segundos no vídeo
    - "palavra@12.3"  -> início da ocorrência de 'palavra' mais perto de 12,3 s
    - "palavra@12.3>" -> FIM dessa palavra
    - "palavra"       -> primeira ocorrência
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    try:
        return float(s.replace(",", "."))
    except ValueError:
        pass
    fim = s.endswith(">")
    s = s.rstrip(">")
    alvo, _, perto = s.partition("@")
    alvo_n = norm(alvo)
    cands = [w for w in palavras if norm(w["w"]) == alvo_n]
    if not cands:
        cands = [w for w in palavras if alvo_n and alvo_n in norm(w["w"])]
    if not cands:
        sair("âncora '%s': a palavra '%s' não aparece na transcricao.json (confira a grafia revisada)." % (x, alvo))
    if perto:
        p = float(perto.replace(",", "."))
        w = min(cands, key=lambda c: abs(c["s"] - p))
        if abs(w["s"] - p) > 3.0:
            print("! âncora '%s' casou com '%s' em %.2f s (longe de %.2f s)" % (x, w["w"], w["s"], p))
    else:
        w = cands[0]
    return float(w["e"] if (fim or campo == "e") else w["s"])
