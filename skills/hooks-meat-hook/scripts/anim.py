"""Animacao dos hooks MarcaD NNN_XX — MiniMax H3 Max via CLI Higgsfield.
Uso: python3 anim.py run <clip> [<clip>...] | python3 anim.py run all
Saida: FOOTAGE/HOOKS/<Hxx_Estrutura_Prop>/<Hxx-n_Estrutura_Prop>.mp4"""
import json, os, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import PROJ, HF, load as load_frames

OUTROOT = os.path.join(PROJ, "FOOTAGE", "HOOKS")
JOBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anim_jobs.json")

LOCK = ("Animate this exact photo. Same faces, same room, same lighting, same vertical phone-shot look, "
        "raw handheld iPhone footage, not cinematic.")
TAIL = ("Camera: one continuous handheld take, subtle organic drift, slow 3% push-in, no cuts. "
        "Audio: {voice} only, natural American English accent, quiet room tone, no music, no second voice, no narrator. "
        "The line is spoken exactly once, no repetition, no loop. Speech occupies roughly {w0}s to {w1}s, then silence "
        "while holding the lens. Mouth movement contained and natural, lips closing fully on the m and b sounds, no "
        "exaggerated jaw. Numbers are spoken as words exactly as written. No on-screen text, no subtitles, no captions, "
        "no watermark, no logo. No face morphing. No extra people appearing.")

M_GRAVE = "one male voice, a 60-something American man, slightly raspy, sincere"
DOC_V = "one male voice, a 68-year-old American doctor, calm and authoritative"
DOC2_V = "one male voice, a 46-year-old American doctor, warm and serious"
DAU_V = "one female voice, a 42-year-old American woman, emotional"
PRI_V = "one male voice, a 66-year-old American priest, soft, fatherly and grave"
JAP_V = "one female voice, a 62-year-old Japanese-American woman with a light Japanese accent in her English, confiding"
FAR_V = "one male voice, a 64-year-old rural American farmer, Midwestern drawl, breathless then relaxed"
BUT_V = "one male voice, a 54-year-old American butcher, gruff and direct"

# clip -> (pasta, start_frame, end_frame|None, duracao, voz, acao, fala, janela)
C = {}
def add(clip, start, end, dur, voice, action, line, w0=0.4, w1=None):
    C[clip] = dict(start=start, end=end, dur=dur, voice=voice, action=action, line=line, w0=w0, w1=w1 or dur - 0.8)

add("H01-1_Demonstracao_Cilindro", "H01-A_Demonstracao_Cilindro", None, 6, M_GRAVE,
    "He holds the clogged clear tube steady against the lens, tilts it slightly so the yellow waxy buildup catches the "
    "light, eyebrows raised, serious.",
    "If you have high blood pressure, this is what's happening inside your arteries right now.")
add("H01-2_Demonstracao_Cilindro", "H01-B_Demonstracao_Cilindro", "H01-C_Demonstracao_Cilindro", 7, M_GRAVE,
    "He keeps pouring the golden honey mixture into the tube; the yellow waxy buildup slowly softens and slides down, "
    "dripping out of the bottom in soft globs onto his jeans; he looks amazed.",
    "And this is what the Arterial Flush Ritual does to that blockage.")
add("H02-1_Confissao_Parque", "H02-A_Confissao_Parque", None, 13, DAU_V,
    "She holds the blood pressure monitor close to the lens, emotional, talking to the camera. Far behind her, her "
    "74-year-old father runs FORWARD along the path TOWARD the camera, facing the direction he is running, happy and "
    "grinning, slowly getting closer; the two grandkids run behind him, tired. He never moves backwards.",
    "My dad is seventy-four years old. Two weeks ago his blood pressure was one seventy-two over ninety-eight. "
    "Almost having a heart attack. He did the Arterial Flush Ritual. And look at him now.")
add("H03-1_Demonstracao_Pescoco", "H03-A_Demonstracao_Pescoco", None, 7, M_GRAVE,
    "He points at the raised vein throbbing on the side of his neck, then pushes the blood pressure monitor toward "
    "the lens, worried.",
    "See this vein in my neck pulsing like that? My pressure's been sitting at one seventy-two over ninety-eight.")
add("H03-2_Demonstracao_Pescoco", "H03-B_Demonstracao_Pescoco", None, 6, M_GRAVE,
    "He keeps pouring the golden honey mixture slowly over the vein on his neck, then lowers the jar and looks into the "
    "lens, speaking clearly with his face toward the camera.",
    "Eight days of the Arterial Flush Ritual. Look at the difference.", w0=0.5, w1=4.5)
add("H03-3_Demonstracao_Pescoco", "H03-C_Demonstracao_Pescoco", None, 6, M_GRAVE,
    "He holds the blood pressure monitor near the lens, low enough that his whole face stays visible, relieved, small "
    "smile.",
    "Went all the way down to one twelve over seventy-four.", w0=0.5, w1=4.0)
add("H04-1_Demonstracao_Coracao", "H04-A_Demonstracao_Coracao", None, 11, DOC_V,
    "The doctor holds the heart model on its stand close to the lens and slowly turns it so the yellow waxy buildup on "
    "the vessels is clearly seen, grave expression.",
    "See this yellow cement clogging up the arteries of this heart? That's exactly what's happening inside your "
    "arteries right now, with your pressure sitting at one eighty over one ten.")
add("H04-2_Demonstracao_Coracao", "H04-B_Demonstracao_Coracao", "H04-C_Demonstracao_Coracao", 8, DOC_V,
    "He looks into the lens and starts speaking right away with the words 'Now watch', then pours the golden honey "
    "mixture over the heart; the yellow wax softens and slides off, dripping in long thick "
    "strands and falling onto his khaki thigh; he points down at his leg, amazed.",
    "Now watch what happens when I pour the Arterial Flush Ritual right here.", w0=0.6, w1=5.0)
add("H05-1_Confissao_Escada", "H05-A_Confissao_Escada", None, 11, DAU_V,
    "She stands at the top of the stairs, worried, talking to the lens. Below her, her father in the burgundy cardigan "
    "climbs UP the stairs toward her, facing the camera, in THREE clearly separated struggles. BEAT 1 (0 to 1.5s): he "
    "climbs two steps. STOP 1 (1.5 to 3s): he STOPS COMPLETELY, frozen on the step, doubled over, clutching his chest "
    "in pain, grimacing. BEAT 2 (3 to 4.5s): he climbs two more steps. STOP 2 (4.5 to 6.5s): he STOPS COMPLETELY "
    "again, both hands pressed to his chest, wincing, gasping. BEAT 3 (6.5 to 8s): two more steps. STOP 3 (8 to 11s): "
    "he STOPS COMPLETELY a third time, leaning on the rail, hand on his chest, in pain, and stays stopped until the "
    "end. During each stop his feet do not move at all. He always moves up toward the camera, never backwards.",
    "This was my dad climbing these stairs. He stopped six times just to make it to the top. Heart pounding out of "
    "his chest. Pressure at one ninety-six over one eighteen.")
add("H05-2_Confissao_Escada", "H05-B_Confissao_Escada", None, 8, DAU_V,
    "She stands at the top of the stairs. Below her, her father climbs UP the stairs toward her, facing the camera, "
    "fast and happy, two steps at a time, getting closer and reaching the landing; he never moves backwards. She keeps "
    "pouring the golden honey mixture in one continuous stream onto the landing floor, amazed, talking to the lens.",
    "This is my dad eight days after the Arterial Flush Ritual, with his pressure down to one twelve over seventy-four.")
add("H06-1_Omissao_Quarto", "H06-A_Omissao_Quarto", None, 8, DOC2_V,
    "The doctor holds the blood pressure monitor toward the lens; behind him the old man in bed gasps for air, chest "
    "heaving. Only the doctor speaks; the old man does not talk.",
    "No cardiologist will ever show you this. His blood pressure is one ninety-two over one eighteen. Struggling to "
    "breathe.")
add("H06-2_Omissao_Quarto", "H06-B_Omissao_Quarto", None, 6, DOC2_V,
    "The doctor slowly pours the golden honey mixture onto the old man's chest and rubs it in gently with his palm; "
    "the old man's breathing slows down. Only the doctor speaks, glancing at the lens.",
    "Today marks four days pouring the Arterial Flush Ritual directly on his chest.")
add("H06-3_Omissao_Quarto", "H06-C_Omissao_Quarto", None, 6, DOC2_V,
    "The old man sits up in bed smiling; the doctor holds up the jar and smiles at the lens. Only the doctor speaks; "
    "the old man just smiles and nods.",
    "He woke up this morning at one fourteen over seventy-four. No losartan.")
add("H07-1_Comando_Padre", "H07-A_Comando_Padre", None, 8, PRI_V,
    "The priest leans toward the lens, hands clasped, kind worried eyes, small pauses between phrases.",
    "My child, I need to tell you something. I lost three members of my parish to heart attacks this past year.")
add("H07-2_Comando_Padre", "H07-B_Comando_Padre", "H07-C_Comando_Padre", 10, PRI_V,
    "He pours the golden honey mixture into the cut-open artery; the yellow wax slowly dissolves and slides out onto "
    "the desk while he looks up into the lens and speaks slowly and clearly, with fatherly warmth.",
    "Please. If your pressure's running above one sixty, do the Arterial Flush Ritual. Your family needs you alive.",
    w0=1.0, w1=8.5)
add("H08-1_Omissao_Tornozelo", "H08-A_Omissao_Tornozelo", None, 7, JAP_V,
    "She points at her swollen ankle, then leans toward the lens as if sharing a secret.",
    "Do you have high blood pressure? Don't let your doctor find out about this Japanese trick.")
add("H08-2_Omissao_Tornozelo", "H08-B_Omissao_Tornozelo", "H08-C_Omissao_Tornozelo", 9, JAP_V,
    "She pours the golden honey mixture over her ankle; the swelling slowly goes down until the ankle looks slim; she "
    "points at it, relieved, and smiles at the lens.",
    "After just four days doing the Arterial Flush Ritual, my ankles went down and my blood pressure dropped to one "
    "twelve over seventy.")
add("H09-1_Omissao_Fazenda", "H09-A_Omissao_Fazenda", None, 11, FAR_V,
    "Out of breath, struggling to talk, he holds the monitor to the lens, then sets it down, grabs the jar from the "
    "railing and pours the golden mixture onto the chest of his plaid shirt.",
    "Your city cardiologist is hiding this from you. My blood pressure is one seventy-two over ninety-eight. I'm "
    "pouring the Arterial Flush Ritual directly on my chest right now.")
add("H09-2_Omissao_Fazenda", "H09-B_Omissao_Fazenda", None, 8, FAR_V,
    "Healthy and relaxed, breathing easy, he holds the jar up to the lens with a small confident smile.",
    "This is me five days later using the ritual. My blood pressure is one twelve over seventy-four. Simple as that.")
add("H10-1_Omissao_Acougue", "H10-A_Omissao_Acougue", None, 9, BUT_V,
    "The butcher holds the split artery toward the lens and turns it so the yellow waxy buildup is clearly seen, "
    "matter-of-fact.",
    "I cut open clogged arteries every single morning. If you suffer from high blood pressure, yours looks exactly "
    "like this right now.")
add("H10-2_Omissao_Acougue", "H10-B_Omissao_Acougue", "H10-C_Omissao_Acougue", 10, BUT_V,
    "He pours the golden honey mixture into the artery on the block; the yellow waxy lining slowly melts and slides "
    "out into a soft puddle on the wood, leaving the artery clean; he looks into the lens.",
    "Watch what the Arterial Flush Ritual does inside here. Don't let your cardiologist know I showed you this secret.")


def prompt(c):
    return " ".join([LOCK, c["action"], "The speaker inhales slightly before the first word so the audio starts a beat "
                     "after the first frame, then says, exactly once:", f'"{c["line"]}"',
                     TAIL.format(voice=c["voice"], w0=c["w0"], w1=c["w1"])])

def folder(clip):
    h, rest = clip.split("-", 1)
    return os.path.join(OUTROOT, h + "_" + rest.split("_", 1)[1])

def load():
    return json.load(open(JOBS)) if os.path.exists(JOBS) else {}

def save(j):
    json.dump(j, open(JOBS, "w"), indent=1)

def submit(clip, jobs, fj):
    c = C[clip]
    cmd = [HF, "generate", "create", "minimax_h3_max", "--prompt", prompt(c), "--start-image", fj[c["start"]],
           "--duration", str(c["dur"]), "--resolution", "768p", "--aspect_ratio", "9:16", "--json"]
    if c["end"]:
        cmd += ["--end-image", fj[c["end"]]]
    out = subprocess.run(cmd, capture_output=True, text=True)
    ids = [t for t in out.stdout.replace('"', " ").replace("[", " ").replace("]", " ").replace(",", " ").split() if len(t) > 20]
    if not ids:
        print("SUBMIT_FAIL", clip, out.stdout[-400:], out.stderr[-400:], flush=True); return
    jobs[clip] = ids[0]; save(jobs); print("SUBMIT", clip, ids[0], flush=True)

def get(job):
    raw = subprocess.run([HF, "generate", "get", job, "--json"], capture_output=True, text=True).stdout
    return json.JSONDecoder().raw_decode(raw[raw.find("{"):])[0]

def wait_all(clips, jobs):
    pend = [c for c in clips if c in jobs and not os.path.exists(os.path.join(folder(c), c + ".mp4"))]
    t0 = time.time()
    while pend and time.time() - t0 < 3600:
        for c in list(pend):
            try: g = get(jobs[c])
            except Exception: continue
            st = g.get("status")
            if st == "completed" and g.get("result_url"):
                os.makedirs(folder(c), exist_ok=True)
                urllib.request.urlretrieve(g["result_url"], os.path.join(folder(c), c + ".mp4"))
                print("DONE", c, flush=True); pend.remove(c)
            elif st in ("failed", "nsfw", "canceled", "cancelled"):
                print("FAILED", c, st, flush=True); pend.remove(c)
        if pend: time.sleep(20)
    for c in pend: print("TIMEOUT", c, flush=True)

if __name__ == "__main__":
    jobs, fj = load(), load_frames()
    clips = list(C) if sys.argv[2:] == ["all"] else sys.argv[2:]
    if sys.argv[1] == "run":
        for c in clips:
            if c not in jobs: submit(c, jobs, fj)
        wait_all(clips, jobs)
    elif sys.argv[1] == "prompt":
        for c in clips: print(c, "\n", prompt(C[c]), "\n")
