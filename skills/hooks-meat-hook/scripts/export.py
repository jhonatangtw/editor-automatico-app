"""Renderiza os 30 entregaveis hook decupado + body. Uso: python3 export.py [ADxx ...]"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
J = os.environ.get("HOOKS_JOB") or os.getcwd()   # pasta do job: export HOOKS_JOB="..."
HK = os.path.join(J, "FOOTAGE/HOOKS/_DECUPADOS")
BODY = os.path.join(J, "FOOTAGE/BODY")
# AD -> (arquivo do body, inicio do body em s, fps de saida)
ADS = {"AD01": ("AD01_video-11-09-2026-09-22-01_h264.mp4", 0.0, "24000/1001"),   # empilhamento
       "AD02": ("AD02_video-09-09-2026-10-51-34_h264.mp4", 18.5333, "30"),       # 1o quadro preto antes do fade
       "AD03": ("AD03_video-11-09-2026-09-39-20_h264.mp4", 4.4667, "30")}        # logo apos "patients."

def job(ad, hk):
    bf, cut, fps = ADS[ad]
    n = int(hk[2:4])
    outdir = os.path.join(J, "EXPORT", ad); os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"[DDMMAA][OT] NNN_XX {ad} HK{n} [MarcaD] [Squad].mp4")
    V = f"scale=1080:1920:flags=lanczos:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps={fps},format=yuv420p"
    A = "aresample=48000,aformat=channel_layouts=stereo"
    fc = (f"[0:v]{V}[hv];[0:a]{A}[ha];"
          f"[1:v]trim=start={cut},setpts=PTS-STARTPTS,{V}[bv];[1:a]atrim=start={cut},asetpts=PTS-STARTPTS,{A}[ba];"
          f"[hv][ha][bv][ba]concat=n=2:v=1:a=1[v][a]")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(HK, hk), "-i", os.path.join(BODY, bf),
                        "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "h264_videotoolbox", "-b:v", "12M",
                        "-maxrate", "16M", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                        out], capture_output=True, text=True)
    return f"{'OK' if r.returncode == 0 else 'ERRO'} {os.path.basename(out)} {r.stderr[-200:]}"

if __name__ == "__main__":
    hooks = sorted(f for f in os.listdir(HK) if f.startswith("HK") and f.endswith(".mp4"))
    ads = sys.argv[1:] or list(ADS)
    with ThreadPoolExecutor(3) as ex:
        for res in ex.map(lambda a: job(*a), [(ad, hk) for ad in ads for hk in hooks]):
            print(res, flush=True)
