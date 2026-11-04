import os, sys, json, subprocess, urllib.request, uuid
from concurrent.futures import ThreadPoolExecutor
C = sys.argv[1]; VOZ = sys.argv[2]
K = os.environ.get("ELEVENLABS_API_KEY") or ""
if not K:
    sys.exit("Defina ELEVENLABS_API_KEY (a mesma chave da aba Contas do Editor Automatico).")
SRC, OUT = f"{C}/ia/voz/blocos", f"{C}/ia/voz/blocos_sts_michael"; os.makedirs(OUT, exist_ok=True)
AV, AVO = f"{C}/hyperframes/up2-MarcaM/assets/avatar", f"{C}/ia/avatar"
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
def um(b):
    i = b["id"]
    if not i.startswith("S"): return f"{i} pulado"
    dst = f"{OUT}/{i}.mp3"
    if not os.path.exists(dst):
        bd = "----x" + uuid.uuid4().hex; aud = open(f"{SRC}/{i}.mp3", "rb").read()
        parts = [("model_id", "eleven_multilingual_sts_v2"), ("voice_settings", json.dumps({"stability":0.5,"similarity_boost":0.85,"style":0.1,"use_speaker_boost":True})), ("remove_background_noise","false")]
        body = b"".join(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in parts)
        body += f'--{bd}\r\nContent-Disposition: form-data; name="audio"; filename="{i}.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + aud + f"\r\n--{bd}--\r\n".encode()
        rq = urllib.request.Request(f"https://api.elevenlabs.io/v1/speech-to-speech/{VOZ}?output_format=mp3_44100_192", data=body, headers={"xi-api-key": K, "Content-Type": f"multipart/form-data; boundary={bd}"})
        open(dst, "wb").write(urllib.request.urlopen(rq, timeout=300).read())
    # troca o áudio do mp4 do avatar (vídeo copiado), mesma duração
    tmp = f"{AV}/{i}.tmp.mp4"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",f"{AVO}/{i}.mp4","-i",dst,"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","256k","-ar","48000","-t",str(dur(f"{AVO}/{i}.mp4")),tmp],check=True)
    os.replace(tmp, f"{AV}/{i}.mp4")
    return f"{i} mp3 {dur(dst):.2f}s / orig {dur(SRC+'/'+i+'.mp3'):.2f}s"
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(um, json.load(open(f"{C}/ia/voz/blocos.json"))): print(r, flush=True)
