# Setup de dependências (uma vez)

A CLI `scripts/conferir.py` precisa de:

| Dependência | Obrigatória? | Para quê |
|-------------|--------------|----------|
| `ffmpeg` / `ffprobe` | sim | ler metadados, extrair frames, detectar preto/congelado/silêncio |
| `tesseract` + idioma | só com `--ocr` | ler a legenda queimada na tela |
| `pillow` (Python) | sim | montar o mosaico com timecode |
| `faster-whisper` (Python) | só com `--transcrever` | transcrever a fala |

## macOS (Homebrew)
```bash
brew install ffmpeg tesseract tesseract-lang     # tesseract-lang traz o português (por)
pip3 install pillow
# opcional, para --transcrever:
pip3 install faster-whisper
```

## Linux (apt)
```bash
sudo apt update
sudo apt install -y ffmpeg tesseract-ocr tesseract-ocr-por
pip3 install pillow --break-system-packages
pip3 install faster-whisper --break-system-packages   # opcional
```

## Verificar
```bash
ffmpeg -version | head -1
tesseract --list-langs        # deve listar 'por' se for usar OCR em PT
python3 -c "import PIL; print('pillow ok')"
```

Se `tesseract` não tiver o idioma `por`, a CLI cai pra `eng` automaticamente e avisa.
