# O que o aluno pode pedir (e o que você faz)

Pedidos prontos — o aluno troca o que está entre colchetes.

| Fase | Pedido | Você faz |
|---|---|---|
| 0 | "Quero editar meu Reels. O bruto está em [pasta/arquivo] e o roteiro em [arquivo]." | requisitos.sh + sondar.py, conta o que o vídeo é e as decisões que virão |
| 1 | "Decupa meus takes e me mostra o melhor de cada frase." | transcrever + decupar + prévia; mostra o mapa e pergunta os empates |
| 1 | "Na frase [N] quero o take [X] e tira a frase [M]." | decupar --escolha "N:X" --sem "M"; nova prévia |
| 1 | "Acho que no take [X] eu tropecei no começo, confere." | transcrever --ini/--fim na janela; responde com o que ouviu |
| 2 | "Monta o corte no Premiere com todos os takes por frase." | montar.py diagnostico/importar/corte/takes/subclipes + leitura de volta |
| 3 | "Meu vídeo ficou claro/lavado, corrige a cor." | montar.py cor (Rec.709 + tone map + look) e pede para ele olhar |
| 3 | "Deixa a cor mais [quente/contrastada/saturada]." | montar.py cor --look "temperatura=..,contraste=..,sat=.." |
| 4 | (o aluno exporta) "Exportei em [Render/arquivo.mp4]." | sondar.py confirma SDR/vertical/áudio |
| 5 | "Faz a edição premium do meu corte. Minhas telas estão em [pasta]." | novo_projeto + transcrever + revisar + rascunho + construir + rascunho de render |
| 5 | "No [momento/frase], coloca [a tela X / um cartão de aprovação / o 'hit' dourado]." | edita roteiro.json (cena/visual) e reconstrói |
| 5 | "Usa as cores da minha marca: [cores] e a fonte [fonte]." | marca.json na pasta do projeto |
| 5 | "O CTA é: [texto], site [site], comentar [palavra]." | visual cta no roteiro |
| 6 | "Renderiza com música [arquivo] / sem música." | renderizar.sh [--sem-musica] + QC + folha de quadros |
| 7 | "Acelera para [1,15x] e me entrega as duas versões." | acelerar.py + qc.py; entrega caminhos, duração, LUFS |

Sempre: mostre o que vai fazer antes de escrever no Premiere, e devolva o que
LEU de volta (não o que "deveria" ter acontecido).
