"""Decupagem de silencio dos hooks + normalizacao de loudness.
Junta os clipes de cada hook (H01-1, H01-2...) cortando respiro inicial, pausas > MIN_SIL e cauda,
e renderiza FOOTAGE/HOOKS/_DECUPADOS/HKnn_Estrutura_Prop.mp4 em 1080x1920 (preenche, corta 8 px de lado)."""
import os, re, subprocess, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import C, folder, OUTROOT

OUT = os.path.join(OUTROOT, "_DECUPADOS"); os.makedirs(OUT, exist_ok=True)
THR, MIN_SIL, PAD, TAIL = "-40dB", 0.30, 0.10, 0.20
TARGET_LUFS = -14.3
KEEP_TAIL = {"H04-2_Demonstracao_Coracao"}   # payoff visual depois da fala
NO_DROP = {"H07-2_Comando_Padre"}   # Whisper marca o "Please" fora do lugar; nao descartar trecho curto

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)

def silences(p):
    e = subprocess.run(["ffmpeg", "-v", "info", "-i", p, "-af", f"silencedetect=noise={THR}:d={MIN_SIL}", "-f", "null",
                        "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", e)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    D = dur(p)
    if len(en) < len(st): en.append(D)
    return list(zip(st, en)), D

def keep_segments(clip):
    p = os.path.join(folder(clip), clip + ".mp4")
    sil, D = silences(p)
    segs, cur = [], 0.0
    for s, e in sil:
        s = max(0.0, s)
        if s <= 0.05:                     # silencio inicial: comeca PAD antes da voz
            cur = max(0.0, e - PAD); continue
        if e >= D - 0.05:                 # silencio final
            end = D if clip in KEEP_TAIL else min(D, s + TAIL)
            segs.append((cur, end)); cur = None; break
        segs.append((cur, s + PAD)); cur = e - PAD
    if cur is not None: segs.append((cur, D))
    # cruza com as palavras do Whisper (qc/<clip>.json): tira trecho curto sem fala e limita cauda/respiro
    wj = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qc", clip + ".json")
    words = [w for s in json.load(open(wj))["segments"] for w in s.get("words", [])]
    first, last = words[0]["start"], words[-1]["end"]
    out = []
    for a, b in segs:
        has = any(a - 0.05 <= (w["start"] + w["end"]) / 2 <= b + 0.05 for w in words)
        if not has and b - a < 0.8 and clip not in NO_DROP: continue            # ruido/respiro solto
        if clip not in KEEP_TAIL: b = min(b, last + 0.30)
        if first > 0.2: a = max(a, first - 0.15)
        if b - a > 0.05: out.append((a, b))
    return p, [(round(a, 3), round(b, 3)) for a, b in out], D

def render(hk, clips):
    name = clips[0].split("_", 1)[1]
    out = os.path.join(OUT, f"HK{int(hk[1:]):02d}_{name}.mp4")
    inputs, fc, n, log = [], "", 0, []
    for i, c in enumerate(clips):
        p, segs, D = keep_segments(c)
        inputs += ["-i", p]
        log.append((c, round(D, 2), segs, round(sum(b - a for a, b in segs), 2)))
        for a, b in segs:
            fc += (f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,"
                   f"crop=1080:1920,setsar=1,fps=24[v{n}];[{i}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,"
                   f"aresample=48000,afade=t=in:d=0.01,afade=t=out:st={max(0, b - a - 0.012):.3f}:d=0.012[a{n}];")
            n += 1
    fc += "".join(f"[v{k}][a{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=1[v][a0]"
    # 1a passada: loudness
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a0]",
                    "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le",
                    tmp.replace(".mp4", ".mov")], check=True)
    tmp = tmp.replace(".mp4", ".mov")
    m = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    ln = (f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-c:v", "copy", "-af", ln + ",aresample=48000", "-c:a", "aac",
                    "-b:a", "256k", "-ar", "48000", out], check=True)
    os.remove(tmp)
    return out, log

if __name__ == "__main__":
    hooks = {}
    for c in C: hooks.setdefault(c[:3], []).append(c)
    sel = sys.argv[1:] or sorted(hooks)
    report = {}
    for hk in sel:
        out, log = render(hk, sorted(hooks[hk]))
        report[hk] = {"arquivo": out, "clipes": log, "duracao": round(dur(out), 2)}
        orig = sum(l[1] for l in log)
        print(f"{hk}: {orig:.1f}s -> {dur(out):.1f}s  {os.path.basename(out)}", flush=True)
        for l in log: print("    ", l[0], "segmentos:", l[2])
    json.dump(report, open(os.path.join(OUT, "_decupagem.json"), "w"), indent=1, ensure_ascii=False)
