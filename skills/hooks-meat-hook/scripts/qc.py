"""QC dos clipes animados: fala x copy, 1a palavra, repeticao, e tira de quadros."""
import json, os, re, subprocess, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import C, folder
S = os.path.dirname(os.path.abspath(__file__))
os.makedirs(f"{S}/qc", exist_ok=True)

def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower().replace("-", " ")).split()

rows = []
for clip in (sys.argv[1:] or list(C)):
    f = os.path.join(folder(clip), clip + ".mp4")
    if not os.path.exists(f):
        rows.append((clip, "SEM ARQUIVO")); continue
    wav = f"{S}/qc/{clip}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f, "-ar", "16000", "-ac", "1", wav], check=True)
    subprocess.run(["whisper", wav, "--model", "small", "--language", "en", "--word_timestamps", "True",
                    "--output_format", "json", "--output_dir", f"{S}/qc"], capture_output=True)
    d = json.load(open(f"{S}/qc/{clip}.json"))
    words = [w for s in d["segments"] for w in s.get("words", [])]
    said = " ".join(s["text"].strip() for s in d["segments"])
    a, b = norm(C[clip]["line"]), norm(said)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    first = words[0]["start"] if words else None
    last = words[-1]["end"] if words else None
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                               capture_output=True, text=True).stdout)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f, "-vf", f"fps={8/dur},scale=180:-2,tile=8x1",
                    "-frames:v", "1", f"{S}/qc/{clip}.jpg"])
    flag = []
    if ratio < 0.9: flag.append(f"fala difere ({ratio:.2f})")
    if len(b) > len(a) * 1.3: flag.append("possivel repeticao")
    if first is not None and first < 0.1: flag.append(f"1a palavra em {first:.2f}s")
    rows.append((clip, f"{dur:.1f}s | fala {first}-{last} | match {ratio:.2f} | {'; '.join(flag) or 'ok'} | \"{said}\""))
for r in rows: print(" · ".join(r))
