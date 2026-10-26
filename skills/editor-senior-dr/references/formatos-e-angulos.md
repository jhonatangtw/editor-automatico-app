# Formatos, áreas seguras e ângulos

## 1. Formatos de tela

| Formato | Resolução de trabalho | Onde roda | O que muda na edição |
|---|---|---|---|
| 9:16 | 1080×1920 | Reels, Stories, TikTok, Shorts, posicionamentos verticais do Meta | Rosto no terço superior; legenda no meio-baixo, acima da interface; um elemento por vez |
| 4:5 | 1080×1350 | Feed do Meta (formato que mais ocupa o feed) | Respiro lateral maior; legenda pode ir mais baixo; cabe tela dividida em cima/baixo com folga |
| 1:1 | 1080×1080 | Feed, alguns posicionamentos de display | Enquadramento mais fechado no rosto; texto mais curto por linha |
| 16:9 | 1920×1080 | YouTube in-stream, VSL em página, desktop | Regra dos terços clássica; espaço lateral para gráficos ao lado do apresentador |

### Áreas seguras (aproximadas; confirme na plataforma, porque as interfaces mudam)
- **9:16:** reserve ~14% no topo (nome da conta, "Patrocinado") e ~20–25% embaixo (legenda do post, CTA da plataforma, botões). A coluna direita (~12%) recebe ícones de curtir/comentar no TikTok e no Reels. Texto essencial, rosto e produto ficam no retângulo central restante.
- **Medidas usadas na operação (9:16, 1080×1920):** Reels: nada importante em y < 192, y > 1536, nem em x > 960 na metade de baixo (editor-de-reels-do-jhon); default do harness de corte: margens L90 / R170 / T160 / B310, baseline da legenda em 1380–1500 (corte-viral). Hook Meat Hook: terço inferior livre para a legenda.
- **4:5 e 1:1:** interface quase toda fora do vídeo; mantenha 5% de margem nas bordas.
- **16:9:** margem de 5% (title safe); se a VSL vai ter player com barra de controle, nada essencial nos 10% de baixo.

### Master multiformato (quando a mesma peça sai em 9:16 e 4:5/1:1)
Planeje o master em 9:16 já com o recorte em mente, para não refazer a edição:
- **Zona comum:** o 4:5 recortado do 9:16 mantém a largura inteira e ~70% da altura central (1080×1350 dentro de 1080×1920, cortando ~285 px em cima e embaixo). Rosto, produto, lettering e qualquer texto essencial ficam nessa faixa central.
- **Legenda e CTA não são recortados**: são elementos de overlay renderizados por formato (no 9:16, mais baixo e acima da interface; no 4:5, dentro do quadro com 5% de margem). Por isso, mantenha legenda/lettering/CTA numa camada separada (overlay do HyperFrames ou trilha própria na timeline).
- B-roll gerado: peça a composição com o sujeito centralizado e "respiro" em cima e embaixo.
- Revise cada formato na sua área segura; o QA no 9:16 não aprova o 4:5.

### Converter um formato no outro
Não basta escalar. Para cada plano:
1. Identifique o que é essencial (rosto, olhos, produto, mão fazendo a ação, texto na cena).
2. Reenquadre para manter o essencial dentro da área segura do formato de destino; acompanhe com keyframe quando o sujeito se move.
3. Se o essencial não cabe (dois rostos lado a lado de 16:9 → 9:16), troque a solução: tela dividida, alternar entre rostos, ou fundo desfocado do próprio plano preenchendo as sobras.
4. Reposicione legenda e gráficos para a nova área segura; reduza texto por linha.
5. Confira resolução: um recorte de 16:9 para 9:16 usa ~32% da largura original. Um 1080p recortado fica abaixo de 1080 de largura; aceite a perda ou use material 4K.

## 2. Ângulo de comunicação (o que a peça argumenta)

| Ângulo | Pergunta que responde | Hook típico | Seleção de cenas | Edição |
|---|---|---|---|---|
| Dor | "Isso é comigo?" | Descrição vívida do problema | Situações do problema, rosto preocupado, o momento constrangedor | Ritmo mais lento, ficar no rosto, trilha tensa; não exagerar o sofrimento a ponto de virar sensacionalismo |
| Desejo | "Como seria se…?" | Cena do resultado desejado | Vida depois, liberdade, prazer | Luz mais quente, movimento, trilha que sobe |
| Curiosidade | "O que é isso?" | Afirmação incompleta ou estranha | Objeto inesperado, gesto estranho, imagem fora de contexto | Segurar a revelação; não mostrar a resposta no hook |
| Mecanismo | "Por que isso funciona quando o resto falhou?" | Nome do mecanismo ou contradição de crença | Animação, diagrama, especialista | Clareza acima de velocidade; cada passo do mecanismo com seu visual |
| Demonstração | "Funciona mesmo?" | O resultado acontecendo | Produto em uso, antes/depois real | Close, tempo real nos momentos críticos |
| Prova | "Quem garante?" | Número, depoimento ou fonte | Depoimentos, estudos, prints reais | Fonte visível; sóbrio |
| Objeção | "Mas e se…?" | A objeção dita em voz alta | Pessoa cética, comparação | Pergunta → pausa → resposta; tom calmo |
| Comparação | "Por que esse e não o outro?" | Lado a lado | Alternativas comuns vs. o produto | Tela dividida, mesmas condições de captura; não difamar concorrente nomeado |
| Oportunidade | "Por que agora?" | Novidade, janela, mudança | Notícia, tendência, evento | Ritmo mais rápido, estética de notícia; urgência real, não inventada |

## 3. Ângulo de câmera (como o plano foi gravado ou reenquadrado)

| Plano | Efeito | Use quando |
|---|---|---|
| Frontal | Conversa direta, honestidade | Frases dirigidas ao "você", CTA, confissão |
| Três quartos | Mais natural e menos confrontador; parece entrevista | Explicação longa, storytelling |
| Lateral (perfil) | Observação, documentário, "bastidor" | Quebrar bloco longo, reação, momento reflexivo |
| Close (rosto) | Emoção, intimidade, ênfase | Hook, revelação, dor, resultado |
| Plano médio (cintura para cima) | Explicação com gestos | Mecanismo, listas, demonstração com as mãos |
| Plano aberto | Contexto e ambiente | Situar a história, mostrar casa/consultório/lugar |

Com uma única câmera, o punch-in digital simula a passagem plano médio → close. Com duas câmeras, alterne por função (frontal para o espectador, lateral para reflexão), não por relógio.

## 4. Variações sem perder coerência

Uma variação muda **uma variável principal** em relação à peça de controle, para o teste dizer algo. Para cada variação, registre:

- **O que muda no hook:** ângulo de comunicação, primeira frase, primeiro visual.
- **O que muda na seleção de cenas:** quais planos entram para servir ao novo ângulo (dor puxa cenas do problema; prova puxa depoimento).
- **O que muda na edição:** ritmo, trilha, legenda, intensidade dos efeitos.
- **O que fica igual:** body, oferta, CTA, promessa central, identidade visual.

Se a variação precisa de uma promessa diferente para fazer sentido, ela é outra peça, não uma variação.

### Variar hook sem copy nova
Esta skill não escreve copy. Quando pedirem hooks de variação e não houver copy de hook:
1. **Reordenar uma frase real do body para a abertura** (a frase de maior tensão: número, confissão, resultado). O sentido não pode mudar, e a repetição precisa de aprovação do copywriter.
2. **Mudar só a abertura visual** com a mesma fala: começar na ação (demonstração), num close ou num insert forte. É uma variação de edição, não de copy.
3. **Propor ângulos** (dor, curiosidade, prova…) para o copywriter escrever e a pessoa gravar ou o avatar gerar.

Nunca crie fala nova na boca de uma pessoa real, nem por montagem nem por voz sintética.
