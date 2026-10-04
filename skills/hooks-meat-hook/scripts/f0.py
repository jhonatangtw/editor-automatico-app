"""F0 mediano por autocorrelacao (quadros vozeados). Uso: f0.py a.mp4 b.mp4 ..."""
import sys, subprocess, numpy as np
def f0(p, sr=16000):
    y = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",p,"-ac","1","-ar",str(sr),"-f","f32le","-"],
                                     capture_output=True).stdout, dtype=np.float32)
    n, hop, out = 640, 160, []
    for i in range(0, len(y) - n, hop):
        fr = y[i:i+n] * np.hanning(n)
        if np.sqrt(np.mean(fr**2)) < 0.02: continue
        ac = np.correlate(fr, fr, "full")[n-1:]
        lo, hi = sr // 300, sr // 60
        k = lo + np.argmax(ac[lo:hi])
        if ac[k] > 0.4 * ac[0]: out.append(sr / k)
    return np.median(out) if out else float("nan")
for p in sys.argv[1:]:
    print("%.0f Hz  %s" % (f0(p), p.split("/")[-1]))
