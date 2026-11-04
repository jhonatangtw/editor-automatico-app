#!/usr/bin/env python3
"""
process_video.py — Prepara um vídeo para o workflow video-to-flow.

O que faz:
  1. Lê a duração e detecta se há trilha de áudio (ffprobe).
  2. Transcreve a fala com timestamps (Whisper local; vários backends).
  3. Agrupa a transcrição em BLOCOS SEMÂNTICOS de ~10s (corta em fim de frase,
     nunca no meio da palavra), com tolerância configurável.
  4. Corta o vídeo em um arquivo por bloco (re-encode para corte preciso).
  5. Extrai 1 frame representativo (meio do bloco) por bloco — para o Claude
     "ver" o que já está na tela e não sugerir B-roll redundante.
  6. Escreve blocos.json (máquina) e blocos.md (leitura humana).

Uso típico (no SEU terminal, onde ffmpeg + whisper estão disponíveis):
    python process_video.py /caminho/video.mp4 -o ./saida

Se você já tem a transcrição (copy/VSL), pule o Whisper:
    python process_video.py video.mp4 -o ./saida --transcript copy.srt

Backends de transcrição tentados, nesta ordem:
    1. openai-whisper (CLI `whisper` ou `import whisper`)
    2. faster-whisper (`from faster_whisper import WhisperModel`)
Se nenhum existir e não houver --transcript, o script avisa como instalar.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# ----------------------------- util ffmpeg -----------------------------------

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(bin_name):
    if shutil.which(bin_name) is None:
        sys.exit(f"[ERRO] '{bin_name}' não encontrado no PATH. Instale antes de continuar.")


def probe_duration(video):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit(f"[ERRO] não consegui ler a duração de {video}\n{r.stderr}")


def has_audio(video):
    r = run(["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=index", "-of", "csv=p=0", str(video)])
    return bool(r.stdout.strip())


def fmt_ts(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02d}:{s:02d}"


# --------------------------- transcrição --------------------------------------

def parse_srt(path):
    """Lê um .srt e devolve [{start,end,text}]."""
    txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"\n\s*\n", txt.strip())
    segs = []

    def to_sec(t):
        t = t.replace(",", ".")
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        time_line = next((l for l in lines if "-->" in l), None)
        if not time_line:
            continue
        a, _, c = time_line.partition("-->")
        text = " ".join(lines[lines.index(time_line) + 1:]).strip()
        segs.append({"start": to_sec(a.strip()), "end": to_sec(c.strip()), "text": text})
    return segs


def load_transcript_file(path):
    p = Path(path)
    if p.suffix.lower() == ".srt":
        return parse_srt(p)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        # aceita formato Whisper {"segments":[{start,end,text}]}
        if isinstance(data, dict) and "segments" in data:
            return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                    for s in data["segments"]]
        if isinstance(data, list):
            return data
    # .txt sem timestamps -> um único segmento (será dividido por tempo depois)
    return [{"start": None, "end": None, "text": p.read_text(encoding="utf-8").strip()}]


def transcribe(video, lang, model_size):
    """Tenta backends de Whisper. Devolve lista de segmentos com timestamps."""
    # backend 1: openai-whisper (python)
    try:
        import whisper  # type: ignore
        print(f"[info] transcrevendo com openai-whisper ({model_size})...", flush=True)
        model = whisper.load_model(model_size)
        res = model.transcribe(str(video), language=lang, verbose=False)
        return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                for s in res["segments"]]
    except ImportError:
        pass

    # backend 2: faster-whisper
    try:
        from faster_whisper import WhisperModel  # type: ignore
        print(f"[info] transcrevendo com faster-whisper ({model_size})...", flush=True)
        model = WhisperModel(model_size, compute_type="int8")
        segments, _ = model.transcribe(str(video), language=lang)
        return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
    except ImportError:
        pass

    # backend 3: whisper CLI
    if shutil.which("whisper"):
        print(f"[info] transcrevendo com whisper CLI ({model_size})...", flush=True)
        tmp = Path("_whisper_tmp")
        tmp.mkdir(exist_ok=True)
        cmd = ["whisper", str(video), "--model", model_size,
               "--output_format", "json", "--output_dir", str(tmp)]
        if lang:
            cmd += ["--language", lang]
        run(cmd)
        js = next(tmp.glob("*.json"), None)
        if js:
            segs = load_transcript_file(js)
            shutil.rmtree(tmp, ignore_errors=True)
            return segs
        shutil.rmtree(tmp, ignore_errors=True)

    sys.exit(
        "[ERRO] Nenhum backend de transcrição encontrado.\n"
        "  Opção A (recomendada):  pip install -U openai-whisper\n"
        "  Opção B (mais leve):    pip install faster-whisper\n"
        "  Opção C:                passe --transcript com a copy/SRT que você já tem."
    )


# --------------------------- blocagem -----------------------------------------

def build_semantic_blocks(segments, total_dur, target, lo, hi):
    """Agrupa segmentos em blocos de ~target s, quebrando em fim de segmento."""
    # sem timestamps -> divisão por tempo fixa
    if not segments or segments[0].get("start") is None:
        full_text = " ".join(s["text"] for s in segments) if segments else ""
        blocks, t = [], 0.0
        words = full_text.split()
        n_blocks = max(1, int(round(total_dur / target)))
        per = max(1, len(words) // n_blocks) if words else 0
        for i in range(n_blocks):
            start = i * (total_dur / n_blocks)
            end = min(total_dur, (i + 1) * (total_dur / n_blocks))
            chunk = " ".join(words[i * per:(i + 1) * per]) if words else ""
            blocks.append({"start": start, "end": end, "text": chunk})
        return blocks

    blocks = []
    cur = {"start": segments[0]["start"], "end": segments[0]["end"],
           "text": segments[0]["text"]}
    for seg in segments[1:]:
        dur = cur["end"] - cur["start"]
        ends_sentence = cur["text"].rstrip().endswith((".", "!", "?", "…"))
        # fecha o bloco se já passou do alvo (e idealmente terminou frase),
        # ou se estourou o teto rígido
        if (dur >= target and ends_sentence) or dur >= hi:
            blocks.append(cur)
            cur = {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
        else:
            cur["end"] = seg["end"]
            cur["text"] = (cur["text"] + " " + seg["text"]).strip()
    blocks.append(cur)

    # junta um último bloco curtíssimo ao anterior
    if len(blocks) > 1 and (blocks[-1]["end"] - blocks[-1]["start"]) < lo:
        blocks[-2]["end"] = blocks[-1]["end"]
        blocks[-2]["text"] = (blocks[-2]["text"] + " " + blocks[-1]["text"]).strip()
        blocks.pop()
    return blocks


# --------------------------- corte + frames -----------------------------------

def cut_block(video, start, end, out_path):
    run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
         "-i", str(video), "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-c:a", "aac", "-movflags", "+faststart",
         str(out_path)])


def grab_frame(video, t, out_path):
    run(["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(video),
         "-frames:v", "1", "-q:v", "2", str(out_path)])


# --------------------------------- main ---------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Prepara vídeo para o workflow video-to-flow.")
    ap.add_argument("video", help="caminho do vídeo de entrada")
    ap.add_argument("-o", "--out", default="./video_to_flow_out", help="pasta de saída")
    ap.add_argument("--target", type=float, default=10.0, help="duração-alvo do bloco (s)")
    ap.add_argument("--min", type=float, default=6.0, help="duração mínima do bloco (s)")
    ap.add_argument("--max", type=float, default=14.0, help="duração máxima do bloco (s)")
    ap.add_argument("--lang", default="pt", help="idioma da fala (ex.: pt, en)")
    ap.add_argument("--whisper-model", default="small",
                    help="tamanho do modelo Whisper (tiny/base/small/medium/large)")
    ap.add_argument("--transcript", help="usar transcrição pronta (.srt/.json/.txt) e pular o Whisper")
    ap.add_argument("--no-clips", action="store_true", help="não cortar os arquivos de vídeo (só frames+json)")
    args = ap.parse_args()

    need("ffmpeg")
    need("ffprobe")
    video = Path(args.video)
    if not video.exists():
        sys.exit(f"[ERRO] vídeo não encontrado: {video}")

    out = Path(args.out)
    clips_dir = out / "blocos"
    frames_dir = out / "frames"
    for d in (out, clips_dir, frames_dir):
        d.mkdir(parents=True, exist_ok=True)

    dur = probe_duration(video)
    audio = has_audio(video)
    print(f"[info] duração: {dur:.1f}s | áudio: {'sim' if audio else 'não'}")

    if args.transcript:
        print(f"[info] usando transcrição fornecida: {args.transcript}")
        segments = load_transcript_file(args.transcript)
    elif audio:
        segments = transcribe(video, args.lang, args.whisper_model)
    else:
        print("[aviso] sem áudio e sem --transcript: blocos serão por tempo fixo.")
        segments = []

    blocks = build_semantic_blocks(segments, dur, args.target, args.min, args.max)
    print(f"[info] {len(blocks)} blocos gerados.")

    manifest = {
        "source": str(video),
        "duration": round(dur, 2),
        "has_audio": audio,
        "n_blocks": len(blocks),
        "blocks": [],
    }

    md = ["# Índice de blocos\n",
          f"Fonte: `{video.name}` · duração {fmt_ts(dur)} · {len(blocks)} blocos\n"]

    for i, b in enumerate(blocks, 1):
        start, end = float(b["start"]), float(b["end"])
        mid = (start + end) / 2
        name = f"bloco_{i:02d}"
        clip = clips_dir / f"{name}.mp4"
        frame = frames_dir / f"{name}.jpg"

        if not args.no_clips:
            cut_block(video, start, end, clip)
        grab_frame(video, mid, frame)

        entry = {
            "n": i,
            "start": round(start, 2),
            "end": round(end, 2),
            "dur": round(end - start, 2),
            "ts": f"{fmt_ts(start)}-{fmt_ts(end)}",
            "text": b["text"].strip(),
            "clip": str(clip) if not args.no_clips else None,
            "frame": str(frame),
        }
        manifest["blocks"].append(entry)
        md.append(f"\n## Bloco {i:02d} · {entry['ts']} ({entry['dur']}s)")
        md.append(f"- vídeo: `{entry['clip']}`")
        md.append(f"- frame: `{entry['frame']}`")
        md.append(f"- fala: {entry['text'] or '(sem fala)'}")

    (out / "blocos.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    (out / "blocos.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\n[ok] saída em: {out.resolve()}")
    print(f"     - blocos.json  (manifesto para o Claude ler)")
    print(f"     - blocos.md    (índice legível)")
    print(f"     - blocos/      ({len(blocks)} clipes .mp4)")
    print(f"     - frames/      ({len(blocks)} frames .jpg)")


if __name__ == "__main__":
    main()
