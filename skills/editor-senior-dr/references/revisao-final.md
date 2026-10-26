# Revisão final

Rode na ordem. Cada item tem um jeito concreto de verificar; "parece certo" não conta.

## 1. Sentido e integridade
- [ ] Transcreva o render e compare com a copy/roteiro: nenhuma palavra cortada, nenhuma frase reordenada a ponto de mudar o sentido.
- [ ] Nenhum depoimento, resultado, número, credencial, endosso, estudo ou logo de mídia que não esteja no material fornecido.
- [ ] Ilustrações (IA, animação, stock) não estão apresentadas como evidência (sem "resultado real", "foto real", "comprovado" sobre imagem ilustrativa).
- [ ] Riscos de política sinalizados ao cliente (antes/depois de corpo, promessa de cura, figura pública, telejornal, atributos pessoais).

## 2. Sincronização e continuidade
- [ ] Emendas ouvidas uma a uma (5 s antes e depois): sem sílaba comida, sem respiração cortada pela metade, sem clique.
- [ ] Legenda bate com a fala (entra no início da palavra, sai antes da próxima frase) e com o texto da copy.
- [ ] Inserts entram na palavra que nomeiam.
- [ ] Avatar: boca fechada no silêncio, lip sync nos picos, sem loop de gesto visível, rótulo legível.
- [ ] Continuidade de figurino, luz e cenário entre planos que deveriam ser contínuos.
- [ ] Nenhum footage repetido na mesma timeline.

## 3. Compreensão
- [ ] Assista sem som: a mensagem e o CTA são entendidos só pela legenda e pelas imagens.
- [ ] Assista sem imagem: o áudio se sustenta (voz clara, trilha não cobre a fala).
- [ ] Os primeiros 3 s carregam o hook (sem logo, sem fade, sem contexto morto).

## 4. Enquadramento e formato
- [ ] Rosto, produto e texto essencial dentro da área segura do formato e da plataforma (ver `formatos-e-angulos.md`).
- [ ] Lettering não cobre o rosto; legenda não cobre boca nem produto.
- [ ] Reenquadramentos acompanham o sujeito; nada essencial cortado na borda.

## 5. Áudio
- [ ] Loudness integrado no alvo do registro (`ffmpeg -af ebur128` ou `loudnorm` em análise), true peak ≤ −1 dBTP.
- [ ] Hook e body no mesmo nível; blocos de VSL no mesmo nível.
- [ ] SFX no quadro certo e no volume do registro.

## 6. Exportação
- [ ] `ffprobe`: resolução, fps, codec e duração de vídeo = duração de áudio.
- [ ] `blackdetect` e `freezedetect` sem ocorrências não intencionais.
- [ ] Sem legenda duplicada (faixa de legenda nativa desligada quando a legenda já está queimada).
- [ ] Nome do arquivo e pasta no padrão; um arquivo por hook/variação.

## Formato do relatório de revisão
Liste só o que falhou ou o que precisa de decisão humana, com timecode e a correção proposta. O que passou cabe numa linha ("sincronia, formato e loudness ok").
