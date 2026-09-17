# Questionário inicial — só o que ainda falta

Antes de qualquer demanda, cruze o que o usuário já disse com o que dá para **verificar nos arquivos**
(`ls` na pasta, `ffprobe` nos vídeos, metadados do Doc, projeto aberto no AE). Faça, **numa única
mensagem**, apenas as perguntas cujas respostas não estão nem no pedido nem no disco.

| # | Pergunta | Como verificar sozinho antes de perguntar | Se faltar |
| --- | --- | --- | --- |
| 1 | Nome ou código da demanda | nome da pasta / do `.aep` | **essencial** |
| 2 | Caminho completo da pasta com takes e materiais | — | **essencial** |
| 3 | Qual take usar; posso escolher o melhor? | se só há um take, não perguntar; se há vários, perguntar autorização | assumir "posso escolher" e registrar |
| 4 | Link da referência principal de motion | — | seguir com a referência prática ou a gramática padrão; registrar |
| 5 | Vídeo local de referência (nome/caminho) | `find <pasta> -iname "*referenc*"` | idem |
| 6 | Link do Google Docs com a copy | `.txt`/`.md` de copy na pasta conta | **essencial** (copy é insumo) |
| 7 | Ler também comentários/sugestões/inserts do copywriter? | — | assumir **sim** e registrar |
| 8 | B-rolls, imagens, logos, fontes prontos — em qual pasta? | listar `broll/`, `assets/`, PNG/MP4 soltos | assumir "o que está na pasta" |
| 9 | Higgsfield pode gerar o que faltar? | — | assumir **não** até autorizar; listar o que faltaria |
| 10 | Formato final: proporção, resolução, fps, duração | `ffprobe` do take principal | assumir o do take principal |
| 11 | Projeto certo aberto no AE? Nome da comp principal? | `lib/rodar.sh` com um script de estado lê `app.project.file` | assumir o `.aep` da pasta; comp = `<CODIGO>_MAIN` |
| 12 | Legendas, trilha, SFX, versão limpa, outras entregas? | — | assumir legendas + SFX pontuais + 1 render de revisão |
| 13 | Regra visual, elemento obrigatório, o que não pode mudar? | "Instruções gerais" do Doc | assumir "só a copy, nada de texto novo" |

**Pare somente** se faltar pasta, copy ou material principal. Para o resto, avance com a suposição
razoável e escreva a decisão no `00_brief/PLANO_MOTION.md` — o usuário corrige depois se quiser.

## Modelo da mensagem

> Para começar a **<demanda>** já tenho: pasta, copy, take (vou escolher o melhor), referência do Pinterest.
> Falta só:
> 1. Posso usar o Higgsfield se faltar algum objeto?
> 2. O projeto `<X>.aep` está aberto? Qual o nome da comp principal (ou crio `<CODIGO>_MAIN`)?
> 3. Além das legendas, precisa de trilha ou versão limpa?
> Vou assumir 9:16 a 30 fps (formato do take) e ler os comentários do Doc como parte do briefing.
