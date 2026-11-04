# Caminho sem Premiere (só ffmpeg)

Para quem não tem o pacote Adobe. Pula as fases 2–4.

```
python3 "$SK/scripts/transcrever.py" BRUTO --saida decupagem/transcricao.json --termos "..."
python3 "$SK/scripts/decupar.py" --video BRUTO --transcricao decupagem/transcricao.json --roteiro roteiro.txt --saida decupagem/
python3 "$SK/scripts/previa_corte.py" --video BRUTO --plano decupagem/plano-corte.json --saida decupagem/previa-corte.mp4
#   (o aluno ouve a prévia e escolhe os takes — checkpoint 1)
python3 "$SK/scripts/previa_corte.py" --video BRUTO --plano decupagem/plano-corte.json --saida Render/corte.mp4 --alta
```

Depois siga da fase 5 com `--corte Render/corte.mp4`.

Limite honesto: se o bruto é HDR (iPhone em HLG), a conversão do ffmpeg aqui é só
uma aproximação de cor (`eq`), porque este ffmpeg não tem tone map de verdade.
Para cor fiel, grave o celular em SDR (no iPhone: Ajustes › Câmera › Gravar
vídeo › desligar "Vídeo HDR") ou use o Premiere.
