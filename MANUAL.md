# Editor Automático — manual

## Instalar

1. Abra o `.dmg` e arraste o **Editor Automático** para Aplicativos — ou dê dois cliques no `.pkg`.
2. Na primeira abertura o macOS vai reclamar que o app não é de desenvolvedor identificado.
   **Botão direito no app → Abrir → Abrir.** Só na primeira vez.
3. Entre com a **mesma conta do Tools PRO**. Se ainda não tem, crie por dentro do app —
   o acesso passa por aprovação.

O app **não pede senha de administrador** para instalar.

## O que precisa estar na máquina

| Ferramenta | Para quê | Sem ela |
|---|---|---|
| `ffmpeg` / `ffprobe` | ler e montar vídeo | o app planeja mas não monta |
| `whisper` | decupar a fala | não dá para decupar |
| `higgsfield` | gerar b-roll | não dá para gerar |
| `ant` (opcional) | entrar com a conta Claude sem chave | use chave de API |

O app mostra na tela o que está faltando em vez de quebrar no meio.

## Conectar as contas

Aba **Contas**. Cada um usa a própria conta — nada passa pelo nosso servidor,
nada sai da sua máquina. As credenciais ficam no Chaveiro do sistema.

- **Claude** — entra com a conta (`ant auth login`) ou chave de API.
  É quem decide onde entra o insert.
- **Higgsfield** — entra com a conta, sem copiar segredo.
- **HeyGen, ElevenLabs, MiniMax** — chave de API.

⚠️ Se você exportou uma `ANTHROPIC_API_KEY` no terminal, é **ela** que vale,
mesmo que você entre com outra conta no app. O app avisa quando isso acontece.

## O fluxo — 12 etapas, com portão entre cada uma

Nenhuma etapa avança sozinha. Nenhuma gasta crédito sem você aprovar a anterior.
O app para em **aguardando aprovação** e espera — quem conclui é sempre você.

| # | Etapa | |
|---|---|---|
| 1 | Análise inicial | projeto, sequência, arquivos, formato e copy |
| 2 | Verificação da copy | copy × fala real: divergências, pronúncia, ausentes, repetições |
| 3 | Marcação da timeline | vermelho b-roll · azul lettering · roxo decisão |
| 4 | **Aprovação do planejamento** | portão — a geração visual só começa aqui |
| 5 | Criação dos avatares | 💳 personagem, aparência, figurino, identidade |
| 6 | Imagens de B-roll | 💳 só estáticas, com consistência de personagem e cenário |
| 7 | **Aprovação das imagens** | portão — aprovar, rejeitar ou regerar uma a uma |
| 8 | Animação dos B-rolls | 💳 só as aprovadas viram vídeo |
| 9 | **Aprovação dos vídeos** | portão |
| 10 | Letterings, voz e legendas | 💳 só depois do visual aprovado |
| 11 | Montagem no Premiere | Tools PRO: posiciona, muda áudio do b-roll, punch-in, trilhas |
| 12 | **Controle de qualidade** | quadro a quadro; a exportação libera só na aprovação final |

💳 = consome crédito das **suas** contas.

**Status de cada etapa:** pendente · em geração · aguardando aprovação · aprovado ·
rejeitado · concluído.

**Retomar de onde parou.** O progresso fica no projeto. Feche o app no meio da etapa 7
e ele reabre exatamente ali, com as imagens já julgadas.

**Reabrir derruba o que veio depois.** Se você voltar na marcação com b-roll já gerado,
o app invalida as etapas seguintes e avisa quantas. É de propósito: mudar o plano sem
derrubar deixaria imagem aprovada que não corresponde mais — caro e silencioso.

**Todo julgamento fica registrado** — quem aprovou, quando e a observação.

## Estilo é um botão, não um arquivo reescrito

`alta-densidade` — 1 corte a cada 3–5s, cobertura ~25%, punch nos vãos. O padrão da casa.
`talking-head-puro` — plano fixo, zero insert. O AD mais longo do acervo valida assim.

Trocar o ritmo do criativo é trocar o seletor. O plano roda em qualquer estilo,
porque nada de acabamento mora no plano e nada de conteúdo mora no estilo.

## Onde ficam seus arquivos

`~/Documents/Editor Automático/Projetos/<projeto>/`
— `plano.json` (seu plano), `transcricao.json`, `broll/`, `saida/`.

Tudo legível, tudo seu, tudo nesta máquina.
