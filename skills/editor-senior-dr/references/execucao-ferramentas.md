# Execução: o que usar para cada etapa

Esta skill **decide e planeja**. Para executar, prefira a skill ou o agente especializado que já existe, porque eles carregam as armadilhas de cada ferramenta. Se a ferramenta não estiver disponível na sessão (MCP fora do ar, app fechado), entregue o plano de edição como instruções para um editor humano. Não finja que executou.

| Etapa | Use | Observação |
|---|---|---|
| Analisar uma referência/criativo pronto | skill `analise-criativo-ficha` (ficha + fluxo persuasivo) ou `analise-criativos-ponte` (nota PONTE) | Gera frames + transcrição; base honesta para uma ficha da biblioteca |
| Dissecar AD/VSL de terceiros | `dissecador-de-ads-atlas`, `dissecador-de-vsl-atlas` | |
| Decupar locução/body (plano de corte por silêncio) | agente `decupador` | Devolve JSON de trechos; não corta |
| Marcar timeline pela locução | `editor-broll:marcar-vsl` | Marcadores numerados e coloridos |
| Escrever no Premiere (sequência, clipes, marcadores, escala, nest, salvar) | agente `premiere-executor` (Tools PRO / ExtendScript) | Devolve o estado lido de volta |
| UGC de avatar → B-roll + punch-in + legenda | `editor-automatico-de-broll` | Gera B-roll de IA da mesma pessoa: só para avatar/persona de IA ou com consentimento da pessoa real. Com pessoa real sem autorização, peça inserts gravados por ela |
| ADs de prosperidade, doc de copy → render premium | `edicao-prosperidade-adhw` | Padrão premium DR completo |
| Clone de AD weight loss | `advalidado-weightloss` | |
| Clone de AD validado trocando personagem | `clone-ad-validado` | |
| Hooks novos Meat Hook + montagem hook/body | `hooks-meat-hook` | |
| Motion no After Effects (talking head + copy) | `motion-viral-jhon1`, `vsl-motion-ae` | |
| Overlays de oferta/lettering no Omni | `motion-omni-vsl` | |
| Acabamento (legenda, lettering, flash, CTA) por código | `hyperframes` (+ `hyperframes-core`) | Overlay ProRes 4444 ou montagem completa |
| Gerar B-roll/planos | agente `gerador-de-planos`; Kling (preferência do usuário) | Mostrar custo antes de gerar |
| Conferir lote de imagens/vídeos gerados | agente `qc-visual` | |
| Cortar silêncio de aula | `cortar-aula` | |
| Conferir AD exportado | `conferir-ads-por-frame` | |
| Auditar job no fim | agente `auditor-de-entrega` | Antes de dizer que acabou |

## Convenções da operação
- Mídia gerada vai para a pasta do job, nunca para o scratchpad nem para temp.
- Nome do entregável no padrão da casa (ex.: `[DDMMAA][OT] NNN_XX ADxx HKn [Produto] [Squad].mp4`); confira a memória "Nomenclatura de entregáveis".
- Arquivo com defeito vai para `_DESCARTADOS/` com o motivo no nome.
- Estime o custo e peça aprovação antes de gastar créditos de geração.
- Retorno de "sucesso" não prova resultado: leia de volta, rode `ffprobe` e olhe o quadro.
