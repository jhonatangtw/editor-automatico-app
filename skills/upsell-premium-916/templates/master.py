#!/usr/bin/env python3
"""Master de entrega do Upsell #2 (NNN_XX): loudnorm em 2 passadas (-16 LUFS, TP <= -1.5 dBTP), vídeo copiado.
    python3 edicao/master_up2.py <render.mp4> <pasta de saída>
"""
import json, os, re, subprocess, sys

src, pasta = sys.argv[1], sys.argv[2]
out = os.path.join(pasta, "[281026][OT] NNN_XX [MarcaK] [Squad].mp4")
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
m = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", af,
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1]
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate",
                               "-of", "json", out], capture_output=True, text=True).stdout)
print(json.dumps({"arquivo": out, "entrada_LUFS": m["input_i"], "saida_LUFS": I, "TP_dBTP": TP,
                  "duracao": p["format"]["duration"], "streams": p["streams"]}, ensure_ascii=False, indent=1))
