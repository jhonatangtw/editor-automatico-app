# Instalação — decupar-vsl-por-frame

## macOS
```bash
brew install ffmpeg tesseract tesseract-lang yt-dlp
python3 -m pip install --user pillow numpy faster-whisper
```

## Windows (PowerShell)
```powershell
winget install -e --id Gyan.FFmpeg
winget install -e --id UB-Mannheim.TesseractOCR
winget install -e --id yt-dlp.yt-dlp
py -m pip install --user pillow numpy faster-whisper
```
Feche e reabra o terminal depois do `winget` (o PATH só atualiza numa sessão nova).

## Conferir
```bash
ffmpeg -version | head -1
tesseract --version | head -1
yt-dlp --version
python3 -c "import PIL, numpy; print('ok')"
```

## O que é obrigatório
| Dependência | Sem ela |
|---|---|
| ffmpeg / ffprobe | não roda |
| pillow | folhas saem sem timecode escrito |
| numpy | detecção de corte fica ~10× mais lenta |
| tesseract | `--ocr` é pulado |
| yt-dlp | não aceita link, só arquivo |
| faster-whisper | `--transcrever` é pulado (use `--legenda`) |

Na primeira vez, o `faster-whisper` baixa o modelo (~500 MB no `small`).
