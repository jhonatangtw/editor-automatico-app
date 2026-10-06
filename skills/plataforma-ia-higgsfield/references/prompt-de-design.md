# Prompt de design — a plataforma de IA do aluno

Preencha os colchetes e cole DEPOIS do setup prompt do Higgsfield, num chat novo (ou use como especificação no caminho B). Onde houver chave: `SUA_CHAVE_AQUI`.

---

Você é um designer de produto e desenvolvedor front-end sênior. Usando a documentação da API do Higgsfield que colei acima (o setup prompt), crie para mim uma **plataforma web de geração de imagem e vídeo com IA**, pronta para abrir no navegador.

### Minha marca
- Nome da plataforma: **[NOME DA SUA MARCA]**
- Cor de destaque: **[COR, ex.: #F2B33D]**
- Tom: **[ex.: premium, minimalista, criativo]**
- Logo: use um monograma simples com as iniciais do nome, desenhado em CSS ou SVG (sem imagens externas).

### Visual (estilo Apple)
- Interface limpa, muito espaço em branco, cantos arredondados generosos, sombras suaves e tipografia do sistema (`-apple-system`, `SF Pro`, `Inter` como alternativa).
- Hierarquia clara: um campo de prompt grande no topo, o botão "Gerar" com a cor de destaque, e os resultados logo abaixo.
- Microanimações discretas (hover, carregamento, entrada dos resultados). Nada piscando ou exagerado.
- Totalmente responsiva: tem que funcionar bem no celular.

### Modo claro e escuro
- Botão de alternância no topo (sol / lua).
- Respeite a preferência do sistema na primeira visita e lembre a escolha do usuário depois.
- As duas versões precisam ter bom contraste e a mesma identidade.

### Seletor de modelos
- Uma fileira de "chips" para escolher o modelo, separando **Imagem** e **Vídeo**.
- Inclua os modelos do Higgsfield que estiverem na documentação, como **Kling**, **Seedance** e **Soul**, e deixe fácil adicionar outros depois (uma lista de configuração no topo do código).
- Mostre opções relevantes para o modelo escolhido: proporção (1:1, 9:16, 16:9), duração do vídeo quando houver, e um campo opcional de imagem de referência.

### Geração e histórico
- Ao gerar, mostre o status do job (na fila, gerando, pronto, erro) com uma mensagem amigável em português.
- Galeria com os resultados em grade; vídeos com player; botões de baixar, copiar prompt e gerar de novo.
- **Histórico de criações** numa barra lateral (ou aba no celular): miniatura, prompt, modelo e data. Pesquisa por texto e botão para limpar o histórico. Guarde o histórico no próprio navegador.

### Segurança da chave (obrigatório)
- **Nunca coloque a minha chave de API dentro do código.** Nem como exemplo preenchido, nem em comentário.
- Na primeira vez que a plataforma abrir, mostre uma tela de configuração pedindo a chave, com o aviso: "Sua chave fica salva só neste navegador."
- Guarde a chave apenas no navegador do usuário (por exemplo, `localStorage`), com um botão "Trocar chave" e outro "Apagar chave".
- Nunca exiba a chave inteira na tela depois de salva: mostre só os 4 últimos caracteres.
- Onde o código ou o exemplo precisar de uma chave, escreva `SUA_CHAVE_AQUI`. Se eu colar uma chave de verdade neste chat por engano, me avise para apagá-la no Higgsfield e criar outra — e não a use no código.
- Inclua um aviso no topo do código e no README: **não publique este projeto com a chave dentro, não suba a chave para o GitHub e não compartilhe prints com a chave visível.**
- Se a API exigir chamadas feitas por servidor (por causa de CORS ou de segurança), me avise e me entregue também um pequeno servidor intermediário (proxy) que leia a chave de uma variável de ambiente — nunca do código.

### Entrega
- Primeiro, me mostre em poucas linhas a estrutura que você vai criar.
- Depois entregue o código completo, em arquivos separados (ou em um único `index.html` se for mais simples), sem partes faltando nem "complete aqui".
- No final, me dê um passo a passo curto em português de como abrir e testar no meu computador, e como publicar com segurança se eu quiser.
- Pagamento: a plataforma não tem assinatura — o custo é só o que eu gerar na minha conta do Higgsfield. Mostre o custo estimado antes de gerar, quando a API informar.
