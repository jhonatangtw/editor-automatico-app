# Instalar

```bash
unzip motion-viral-jhon1.zip -d ~/.claude/skills/
cp ~/.claude/skills/motion-viral-jhon1/fontes/*.ttf ~/Library/Fonts/
python3 ~/.claude/skills/motion-viral-jhon1/verificar.py
```

Em projeto, vale `.claude/skills/motion-viral-jhon1/` na raiz do repositório.

## Dependências

| | Para quê | Como |
| --- | --- | --- |
| **After Effects 2026** | é onde a composição é construída | app da Adobe |
| `ffmpeg` + `ffprobe` | decupar, medir, extrair frame, converter áudio | `brew install ffmpeg` |
| `faster-whisper` | transcript palavra a palavra | `pip install faster-whisper` |
| `Pillow`, `numpy`, `opencv-python` | recorte de asset e conferência | `pip install Pillow numpy opencv-python` |
| `ELEVENLABS_API_KEY` | Voice Changer | `~/.config/hw-creative/.env` |
| `yt-dlp` | baixar vídeo de referência | opcional |
| `higgsfield` CLI | gerar asset que falta | opcional |

**As 10 fontes viajam com a skill** (todas OFL/Apache). Precisam estar instaladas em
`~/Library/Fonts` para o AE enxergar — o AE relê a lista sozinho, sem reiniciar.

## Permissão de automação

A skill fala com o AE por Apple Events. Na primeira vez o macOS pede autorização
(Privacidade e Segurança → Automação → Terminal/VS Code → Adobe After Effects).

## Fluxo mínimo

```bash
K=~/.claude/skills/motion-viral-jhon1
MVJ_COMP=REELS01_MAIN $K/lib/rodar.sh "<pasta-do-projeto>" cenas/01_setup.jsx
$K/lib/voz_jhon.sh 06_Audio/original 06_Audio/jhon
python3 $K/lib/conferir_voz.py 00_brief/transcripts 06_Audio/jhon
python3 $K/lib/conferir_render.py timbre saida.mp4 06_Audio/jhon/take1_jhon.wav 06_Audio/original/take1.wav
```

`rodar.sh` aceita: `MVJ_COMP` (comp principal) · `MVJ_FPS` · `MVJ_OUT` (padrão
`<projeto>/07_Exports/_ae`) · `MVJ_AE` (nome do app) · `MVJ_TIMEOUT`.
`voz_jhon.sh` aceita: `MVJ_VOICE` · `MVJ_STS_MODEL` · `MVJ_VOICE_SETTINGS` · `MVJ_ENV`.

## Se instalar em outro caminho

Nada a ajustar: `rodar.sh` resolve o próprio diretório e injeta os caminhos nos scripts.
Não há caminho absoluto de sessão dentro de `ae_lib.jsx` — o `verificar.py` confere isso.
