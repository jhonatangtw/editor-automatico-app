"""Unifica a voz de cada personagem: clona a voz do clipe de referencia (ElevenLabs IVC, vaga unica),
converte todos os clipes do personagem por speech-to-speech, troca o audio no mp4 e apaga o clone temporario.
Uso: python3 voz.py <PERSONAGEM> [...] | all"""
import os, shutil, subprocess, sys, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import folder

S = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get("ELEVENLABS_API_KEY") or ""   # export ELEVENLABS_API_KEY="..." antes de rodar
if not KEY:
    sys.exit("Defina ELEVENLABS_API_KEY (a mesma chave da aba Contas do Editor Automatico).")
TMP = f"{S}/voz"; os.makedirs(TMP, exist_ok=True)

P = {  # personagem -> (clipe de referencia, clipes)
    "PACIENTE": ("H01-1_Demonstracao_Cilindro", ["H01-1_Demonstracao_Cilindro", "H01-2_Demonstracao_Cilindro",
                 "H03-1_Demonstracao_Pescoco", "H03-2_Demonstracao_Pescoco", "H03-3_Demonstracao_Pescoco"]),
    "MEDICO": ("H04-1_Demonstracao_Coracao", ["H04-1_Demonstracao_Coracao", "H04-2_Demonstracao_Coracao"]),
    "FILHA": ("H05-1_Confissao_Escada", ["H05-1_Confissao_Escada"]),
    "MEDICO2": ("H06-1_Omissao_Quarto", ["H06-1_Omissao_Quarto", "H06-2_Omissao_Quarto", "H06-3_Omissao_Quarto"]),
    "PADRE": ("H07-1_Comando_Padre", ["H07-1_Comando_Padre", "H07-2_Comando_Padre"]),
    "JAPONESA": ("H08-1_Omissao_Tornozelo", ["H08-1_Omissao_Tornozelo", "H08-2_Omissao_Tornozelo"]),
    "FAZENDEIRO": ("H09-1_Omissao_Fazenda", ["H09-1_Omissao_Fazenda", "H09-2_Omissao_Fazenda"]),
    "ACOUGUEIRO": ("H10-1_Omissao_Acougue", ["H10-1_Omissao_Acougue", "H10-2_Omissao_Acougue"]),
}

REF_PATH = {"FILHA": os.path.join(os.path.dirname(folder("H05-1_x_y")), "_REPROVADOS", "FILHA_voz_referencia.mp4")}
def mp4(c): return os.path.join(folder(c), c + ".mp4")
def orig(c): return os.path.join(os.path.dirname(folder(c)), "_REPROVADOS", c + "_voz_original.mp4")
def run(*a): subprocess.run(a, check=True, capture_output=True)

def curl(*a):
    r = subprocess.run(["curl", "-sS", "-H", f"xi-api-key: {KEY}", *a], capture_output=True)
    return r.stdout

for name in (list(P) if sys.argv[1:] == ["all"] else sys.argv[1:]):
    ref, clips = P[name]
    src = lambda c: orig(c) if os.path.exists(orig(c)) else mp4(c)   # sempre parte do audio original
    refsrc = REF_PATH.get(name, src(ref))
    run("ffmpeg", "-y", "-v", "error", "-i", refsrc, "-vn", "-ac", "1", "-ar", "44100", f"{TMP}/{name}_ref.wav")
    out = json.loads(curl("-X", "POST", "https://api.elevenlabs.io/v1/voices/add", "-F", f"name=TMP_NNNXX_{name}",
                          "-F", f"files=@{TMP}/{name}_ref.wav", "-F", "remove_background_noise=false"))
    vid = out.get("voice_id")
    if not vid:
        print("CLONE_FAIL", name, out); continue
    print("CLONE", name, vid, flush=True)
    try:
        for c in clips:
            s = src(c)
            run("ffmpeg", "-y", "-v", "error", "-i", s, "-vn", "-ac", "1", "-ar", "44100", f"{TMP}/{c}_in.wav")
            mp3 = f"{TMP}/{c}_out.mp3"
            raw = curl("-X", "POST", f"https://api.elevenlabs.io/v1/speech-to-speech/{vid}?output_format=mp3_44100_128",
                       "-F", "model_id=eleven_multilingual_sts_v2", "-F", f"audio=@{TMP}/{c}_in.wav",
                       "-F", "remove_background_noise=false")
            if raw[:1] == b"{":
                print("STS_FAIL", c, raw[:300]); continue
            open(mp3, "wb").write(raw)
            if not os.path.exists(orig(c)):
                shutil.copy2(mp4(c), orig(c))
            tmpv = f"{TMP}/{c}.mp4"
            run("ffmpeg", "-y", "-v", "error", "-i", orig(c), "-i", mp3, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-t", str(float(subprocess.run(["ffprobe", "-v", "error",
                "-show_entries", "format=duration", "-of", "csv=p=0", orig(c)], capture_output=True, text=True).stdout)),
                tmpv)
            shutil.copy2(tmpv, mp4(c))
            print("VOZ", c, flush=True)
    finally:
        curl("-X", "DELETE", f"https://api.elevenlabs.io/v1/voices/{vid}")
        print("DELETE", name, vid, flush=True)
