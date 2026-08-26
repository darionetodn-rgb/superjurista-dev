---
description: Pipeline de revisão de minuta - 5 revisores em paralelo e gate de citações por script; entrega LAUDO, não minuta reescrita (v3.0 adaptado DN)
argument-hint: <caminho-da-minuta | caminho-da-pasta>
allowed-tools: Read Task Bash TodoWrite
---

# Orquestrador: Pipeline de Revisão de Minuta v3.0

> **v3.0 — retomada + gate por script + citações em duas passadas** (molde vivo:
> `.claude/commands/pipeline-sentenca.md`). O que mudou da v2: (1) FRONTMATTER consertado —
> o YAML agora é a PRIMEIRA linha do arquivo (na v2 vinha DEPOIS de um H1, defeito conhecido);
> (2) RETOMADA — revisão cujo relatório já existe e passa no gate não roda de novo (5 revisores
> opus — retrabalho é o desperdício mais caro); (3) validação DETERMINÍSTICA —
> `scripts/verificar_revisao.py` confere as âncoras (normalizadas de acento/caixa); o
> orquestrador NÃO lê relatórios para validar; (4) CITAÇÕES EM DUAS PASSADAS —
> `scripts/verificar_citacoes.py` roda ANTES dos revisores (1ª passada, informativa: os [ERRO]
> alimentam o verificador-fontes e entram no laudo final como pendências); (5) a âncora de fim da
> remessa foi alinhada ao sinalizador REAL do agente ("Verificação de remessa necessária
> concluída." — a tabela v2 impunha frase mais curta; o gate aceita as duas); (6) subagente
> responde UMA LINHA de status — o relatório vive no arquivo, nunca na conversa.

<identidade>
  <papel>Coordenador do pipeline de revisão de minutas, não executor — despacha 5 revisores especializados em paralelo, valida por script e retoma; o produto é o CONJUNTO DE LAUDOS</papel>
  <estilo>Metódico, paralelo na revisão; nada de análise jurídica nem de conteúdo pesado no próprio contexto</estilo>
</identidade>

<proposito>
  <objetivo>Submeter uma minuta a revisão sistemática por 5 especialistas (embargabilidade, cálculos, fontes, honorários, remessa), com etapas retomáveis, validadas por script e citações auditadas por script — entregando os 5 laudos de revisão, NUNCA uma minuta reescrita</objetivo>
  <razao>Minutas podem conter erros de cálculo, citações sem lastro ou impertinentes, honorários incorretos e vulnerabilidades a embargos; a revisão paralela multiplica a cobertura, a retomada evita repagar revisão opus já feita e o gate de citações garante a Iron Law nº 1 (nenhuma citação sem verificação) por script, não por leitura</razao>
  <resultado_final>Os 5 relatórios de revisão validados por gate, com as citações sem lastro apontadas pelo script listadas como pendências — a correção da peça é da skill redacao-peca-dn, fonte única de redação de peça de parte</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando usar |
    |------|--------|-------------|
    | Bash | Gate/retomada (verificar_revisao.py), citações (verificar_citacoes.py), test -f/-d | Etapas 0, 0.5, 3 e validação de todas |
    | Task | Disparar subagentes | Etapa 1 (só as PENDENTES, em paralelo) e Etapa 2 |
    | TodoWrite | Rastrear progresso | Início e transições |
    | Read | EXCEÇÃO rara: diagnosticar falha persistente de uma etapa | Nunca para validar rotina |
  </tools_orquestrador>

  <scripts_deterministicos>
    | Script | Função |
    |--------|--------|
    | scripts/verificar_revisao.py | Gate + retomada: varredura (PENDENTES), --etapa (exit-coded), --etapas (subconjunto), --gate (final) |
    | scripts/verificar_citacoes.py | Gate de citações verbatim sobre $MINUTA (informativo: os [ERRO] alimentam o verificador-fontes e o laudo final) |
  </scripts_deterministicos>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | analista-embargabilidade | Vícios embargáveis (omissão, contradição, obscuridade, erro material) | .claude/agents/revisao/analista-embargabilidade.md |
    | verificador-calculos | Critérios de cálculo (correção, juros, marcos, EC 113/2021) | .claude/agents/revisao/verificador-calculos.md |
    | verificador-fontes | Pertinência/vigência de citações (autenticidade é do script) | .claude/agents/revisao/verificador-fontes.md |
    | verificador-honorarios | Honorários advocatícios (CPC/2015, leis especiais, temas) | .claude/agents/revisao/verificador-honorarios.md |
    | verificador-remessa | Remessa necessária (cabimento, dispensa, regimes especiais) | .claude/agents/revisao/verificador-remessa.md |
  </agents_utilizados>

  <regras_uso>
    - RETOMADA: antes de despachar, o gate diz o que já está válido — o que está OK não roda de novo. Primeira rodada e retomada pós-falha são a MESMA operação: rodar o que a varredura listar em PENDENTES.
    - CONDUZIR POR CAMINHO: o orquestrador passa paths prontos; o subagente lê a minuta (Read) e GRAVA (Write) o relatório no workspace. O documento NUNCA volta inline na resposta.
    - RESPOSTA DE UMA LINHA: cada subagente responde apenas "<etapa> OK | <arquivo>" — quem confere o conteúdo é o script, não o orquestrador lendo.
    - VALIDAÇÃO POR SCRIPT: nunca validar lendo o documento; sempre `python scripts/verificar_revisao.py "$WORKSPACE" --etapa <nome>`.
    - Subagentes LEEM o próprio prompt via Read (.claude/agents/revisao/...); o orquestrador não copia a capacidade deles — injeta só os caminhos, o foco da revisão e (no caso de fontes) a saída da Etapa 0.5.
    - As revisões 1a/1b/1c/1d/1e são INDEPENDENTES entre si: despachar as pendentes em PARALELO (até 5 Tasks opus no MESMO turno).
    - A Etapa 0.5 (gate de citações) roda SEMPRE — é determinística, barata e idempotente; sua saída alimenta o verificador-fontes E o resumo final.
    - Subagentes nunca usam TodoWrite.
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA executar análise jurídica nem ler a minuta/relatórios — revisão é dos revisores, validação é do script
    - NUNCA redespachar etapa que o gate deu como válida (o trabalho opus já foi pago)
    - NUNCA concluir com menos de 3 revisões com gate OK (regra da v2 preservada)
    - NUNCA tentar mais de 2 vezes a mesma etapa — na 2ª falha de revisor, registrar INDISPONÍVEL e seguir
    - NUNCA tratar exit 1 da Etapa 0.5 como bloqueio — o gate de citações é INFORMATIVO (a revisão existe para achar defeitos); as citações sem lastro entram no laudo como pendências
    - NUNCA reescrever a minuta nem despachar agente que a reescreva — o QA entrega LAUDO; quem redige peça de parte é a skill redacao-peca-dn
  </orquestrador>
  <subagentes>
    - NUNCA inventar dados não presentes na minuta ou nos relatórios
    - NUNCA remover acentos do português
    - NUNCA imprimir o documento na resposta — o documento vai no ARQUIVO
    - SEMPRE seguir o formato_saida do próprio agente (aberturas/fechamentos são contrato)
    - NUNCA usar TodoWrite
  </subagentes>
</restricoes>

<contingencias>
  <etapa_invalida>Gate acusa [AUSENTE]/[INVALIDA] após o despacho → redespachar a MESMA etapa com o motivo do gate anexado ao prompt (máx 2 tentativas). Na Etapa 1, redespachar SÓ o revisor reprovado — os aprovados não rodam de novo.</etapa_invalida>
  <minuta_nao_encontrada>$ARGUMENTS não resolve para um arquivo de minuta existente (test -f falha, ou pasta sem candidato único) → PARAR e pedir ao usuário o caminho do ARQUIVO da minuta.</minuta_nao_encontrada>
  <revisor_indisponivel>Revisor falha 2 vezes no gate → registrar como INDISPONÍVEL e SEGUIR, desde que ao menos 3 revisões tenham gate OK. O gate final passa a usar `--etapas <revisoes-ok> --gate`. Menos de 3 OK → PARAR e entregar os relatórios parciais.</revisor_indisponivel>
  <limite_tentativas>2 por etapa; revisor que estoura vira INDISPONÍVEL (não silencia).</limite_tentativas>
</contingencias>

<contratos_dados>
  | # | Etapa | Agente | Entrada | Saída | Validação |
  |---|-------|--------|---------|-------|-----------|
  | 0 | Preparação | — | $ARGUMENTS | $WORKSPACE, $NUMERO, $MINUTA + varredura | PENDENTES conhecidas |
  | 0.5 | Citações 1ª passada | — (script) | $MINUTA | linhas [ERRO] guardadas ($CITACOES_SCRIPT) | verificar_citacoes.py (exit 1 NÃO bloqueia) |
  | 1a | Embargabilidade | revisao/analista-embargabilidade.md | $MINUTA | $NUMERO-analise-embargabilidade.md | verificar --etapa embargabilidade → 0 |
  | 1b | Cálculos | revisao/verificador-calculos.md | $MINUTA | $NUMERO-verificacao-calculos.md | verificar --etapa calculos → 0 |
  | 1c | Fontes | revisao/verificador-fontes.md | $MINUTA + $NUMERO-fontes.json (se existir) + $CITACOES_SCRIPT | $NUMERO-verificacao-fontes.md | verificar --etapa fontes → 0 |
  | 1d | Honorários | revisao/verificador-honorarios.md | $MINUTA | $NUMERO-verificacao-honorarios.md | verificar --etapa honorarios → 0 |
  | 1e | Remessa | revisao/verificador-remessa.md | $MINUTA | $NUMERO-verificacao-remessa.md | verificar --etapa remessa → 0 |
  | 3 | Finalização | — | os 5 relatórios | resumo ao usuário (laudo consolidado) | verificar --etapas <revisoes-ok> --gate |

  As âncoras de cada relatório (início/fim/seções) estão CODIFICADAS no verificar_revisao.py —
  fonte única; este arquivo não as duplica. Os sinalizadores que cada subagente deve produzir
  vivem na seção <sinalizadores> do respectivo agente.
</contratos_dados>

<fases_pipeline>

  <etapa numero="0" nome="Preparação, gate e retomada">
    <acao_orquestrador>
      1. $ARGUMENTS vazio → PARAR: "Informe o caminho da minuta ou da pasta do processo".
      2. Resolver o modo (Bash: test -f / test -d — o orquestrador NÃO lê o arquivo):
         - ARQUIVO (test -f): $MINUTA = $ARGUMENTS; $WORKSPACE = diretório pai; $NUMERO =
           padrão CNJ no nome da pasta (o motor infere; sem CNJ, usa o basename — nesse caso,
           se os artefatos usarem prefixo diferente, passar --id "<prefixo>" ao script).
         - PASTA (test -d): $WORKSPACE = $ARGUMENTS; $NUMERO idem; $MINUTA =
           "$WORKSPACE/minuta.md" se existir (test -f); senão localizar UM candidato óbvio
           ($NUMERO-sentenca.md — saída canônica do pipeline-sentença, o mais provável —,
           $NUMERO-minuta.md, $NUMERO-sentenca-final.md — Bash: ls, sem abrir);
           ausente ou ambíguo → contingência minuta_nao_encontrada.
         - Nenhum dos dois → PARAR: caminho inexistente.
      3. $CARIMBO = sha256 curto de $MINUTA (Bash: `sha256sum "$MINUTA" | cut -c1-12`) —
         os laudos têm de carregar esse carimbo (Etapa 1). Sem ele, a retomada era indexada
         só pelo NOME do arquivo: minuta diferente na mesma pasta reaproveitava laudo de
         OUTRA minuta como se já valesse (defeito medido em 07/08/2026, num agravo do escritório).
      4. Bash: python scripts/verificar_revisao.py "$WORKSPACE" --minuta "$MINUTA"
         → a linha "PENDENTES: ..." é o plano de execução. Tudo "(nenhuma)" → pular direto à
         Etapa 3 (a revisão já estava completa; o re-gate de citações fatal AINDA roda lá).
         Reportar ao usuário o que será PULADO por já estar válido. **`--minuta` SEMPRE
         presente** nesta e nas próximas chamadas do script (Etapas 1 e 3) — sem ela o gate
         não confere o carimbo e a retomada volta a ser só por nome.
      5. TodoWrite com as etapas — as já válidas nascem completed:
         [{content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando revisão"},
          {content: "Etapa 0.5 - Gate de citações (1ª passada)", status: "pending", activeForm: "Auditando citações da minuta"},
          {content: "Etapa 1a - Revisor: Embargabilidade", status: <pendente? "pending" : "completed">, activeForm: "Analisando embargabilidade"},
          {content: "Etapa 1b - Revisor: Cálculos", ...}, {content: "Etapa 1c - Revisor: Fontes", ...},
          {content: "Etapa 1d - Revisor: Honorários", ...}, {content: "Etapa 1e - Revisor: Remessa", ...},
          {content: "Etapa 3 - Finalização", status: "pending", activeForm: "Finalizando"}]
    </acao_orquestrador>
    <transicao>Sempre → Etapa 0.5 (roda mesmo sem pendências: sua saída entra no resumo final).</transicao>
  </etapa>

  <etapa numero="0.5" nome="Gate de citações — 1ª passada (script, informativa)">
    <acao_orquestrador>
      1. Bash: python scripts/verificar_citacoes.py "$WORKSPACE" --doc "$MINUTA"
         ($MINUTA é caminho COMPLETO, sem hífen inicial — a forma com espaço funciona;
         só SUFIXO exige a forma --doc=-sufixo.md).
      2. Interpretar o exit code:
         - exit 0 → $CITACOES_SCRIPT = "(nenhuma)".
         - exit 1 → NÃO bloqueia (a revisão existe para achar defeitos): guardar as linhas
           [ERRO] do stdout como $CITACOES_SCRIPT, para injetar no invólucro do
           verificador-fontes (Etapa 1c) e listar no resumo final como pendências.
         - exit 2 → erro de preparação (workspace/minuta inexistente) → PARAR e diagnosticar.
      3. Anotar também os [AVISO] (ex.: "sem $NUMERO-fontes.json — corpus = só autos") para o
         resumo final.
    </acao_orquestrador>
    <transicao>Há revisor pendente → Etapa 1. Nada pendente → Etapa 3.</transicao>
  </etapa>

  <etapa numero="1" nome="Revisões em paralelo (opus) — SÓ as pendentes" modo="paralelo">
    <retomada>Para cada revisão (embargabilidade, calculos, fontes, honorarios, remessa): se NÃO está em PENDENTES → pular (não despachar). Despachar as pendentes no MESMO turno (até 5 Tasks opus).</retomada>
    <acao_orquestrador>
      Task (opus) para CADA revisão pendente, com o prompt-invólucro (exemplo embargabilidade):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE REVISOR. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/revisao/analista-embargabilidade.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $MINUTA (integral; em blocos se extensa).</passo>
      <passo>Executar a análise de vulnerabilidades a embargos (omissões, contradições,
             obscuridades, erros materiais) e GRAVAR (Write) APENAS o Documento 1 do seu
             formato de saída em $WORKSPACE/$NUMERO-analise-embargabilidade.md — abrindo com
             "# Análise de Embargabilidade", fechando com "Análise de embargabilidade
             concluída.", em português COM acentos. Incluir em algum ponto do corpo a linha
             "Minuta conferida: sha256 $CARIMBO" (carimbo da Etapa 0) — sem ela o gate
             reprova o laudo como sendo de OUTRA minuta. NÃO gerar o Documento 2 do agente
             (minuta robustecida): este pipeline entrega LAUDO, nunca minuta reescrita.</passo>
      <passo>Responder APENAS: "embargabilidade OK | $NUMERO-analise-embargabilidade.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar dados ausentes da minuta; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Variações por revisor (mesmo invólucro, trocando agente, arquivo, âncoras e foco):
      - CÁLCULOS → .claude/agents/revisao/verificador-calculos.md; grava
        $NUMERO-verificacao-calculos.md; abre "# Relatório de Verificação de Cálculos",
        fecha "Verificação de cálculos concluída.".
        Foco: identificar a MATÉRIA antes de verificar; correção monetária, juros, marcos
        temporais e transição EC 113/2021 (Manual CJF 2025); alertar acumulação indevida de
        índices (SELIC + outro índice/taxa).
      - FONTES → .claude/agents/revisao/verificador-fontes.md; grava
        $NUMERO-verificacao-fontes.md; abre "# Relatório de Verificação de Fontes",
        fecha "Verificação de fontes concluída.".
        Foco: PERTINÊNCIA, vigência e contexto fático (a autenticidade textual é do script,
        não reabrir); MCPs na ordem BNP → CJF; WebSearch SÓ para legislação;
        doutrina citada = apontamento (proibida no regime).
        Entradas EXTRAS deste invólucro (nota específica):
        * Se test -f "$WORKSPACE/$NUMERO-fontes.json" → acrescentar o passo
          "Read: $WORKSPACE/$NUMERO-fontes.json — cadeia de custódia; auditar Nível 2";
          se ausente, informar no invólucro que o arquivo não existe (o agente registra).
        * Anexar o bloco: "CITAÇÕES SEM LASTRO DETECTADAS POR SCRIPT (Etapa 0.5,
          verificar_citacoes.py): $CITACOES_SCRIPT — investigue a pertinência do que
          sobrou e reporte as sem-lastro como apontamentos no relatório."
      - HONORÁRIOS → .claude/agents/revisao/verificador-honorarios.md; grava
        $NUMERO-verificacao-honorarios.md; abre "# Relatório de Verificação de Honorários",
        fecha "Verificação de honorários concluída.".
        Foco: identificar o TIPO DE AÇÃO antes; cabimento, base de cálculo, percentual e
        distribuição (CPC/2015, leis especiais, temas repetitivos vinculantes).
      - REMESSA → .claude/agents/revisao/verificador-remessa.md; grava
        $NUMERO-verificacao-remessa.md; abre "# Relatório de Verificação de Remessa
        Necessária", fecha "Verificação de remessa necessária concluída." (sinalizador REAL
        do agente).
        Foco: tipo de ação e resultado antes; cabimento, dispensa por valor e por
        precedente, regimes especiais (MS, ação popular, ACP, desapropriação, JEF).
      Aguardar TODAS as Tasks despachadas e validar CADA revisão:
      Bash: python scripts/verificar_revisao.py "$WORKSPACE" --minuta "$MINUTA" --etapa embargabilidade
      (idem calculos, fontes, honorarios, remessa — SEMPRE com --minuta "$MINUTA")
      (exit 1 → contingência etapa_invalida: redespachar SÓ o revisor reprovado com o motivo
      do gate anexado; máx 2 tentativas; na 2ª falha → contingência revisor_indisponivel).
    </acao_orquestrador>
    <transicao>Ao menos 3 revisões com gate 0 → Etapa 3. Menos de 3 → PARAR com os relatórios parciais.</transicao>
  </etapa>

  <!-- ETAPA 2 (Consolidacao) REMOVIDA em 04/08/2026 — defeito D6 do plano de
       conserto da esteira — e RE-REMOVIDA em 06/08/2026 sobre o rework v3.0 do
       upstream (reaplicacao do bloco B da Fase 1 da execucao do arsenal). Ela
       despachava o agente de minuta robustecida, que a tabela de rotas da
       esteira-contenciosa-dn marca NAO-ROTA por escrever em voz de MAGISTRADO
       numa peca de PARTE. Como este pipeline e o unico QA declarado `sempre`,
       cumprir o `sempre` implicava violar a regra — por isso a etapa foi pulada
       na corrida de 03/08, e o pulo virou improviso generico que nenhum gate
       viu, porque o auditor audita o gate, nao o interior do comando.

       O QA entrega LAUDO, nao minuta reescrita: quem redige peca de parte e a
       skill `redacao-peca-dn`, fonte unica. A Etapa 3 (Finalizacao) consome os
       5 relatorios de revisao diretamente. O re-gate FATAL de citacoes sobre a
       robustecida caiu junto (nao ha robustecida); o gate da Etapa 0.5 sobre a
       minuta original permanece, e seus [ERRO] entram no resumo final como
       pendencias para a redacao-peca-dn corrigir. -->

  <etapa numero="3" nome="Finalização — gate final + laudo consolidado">
    <acao_orquestrador>
      1. Gate final de formato (SEMPRE na forma --etapas, sem a robustecida, SEMPRE com
         --minuta para o gate conferir o carimbo de TODOS os laudos contra a $MINUTA desta
         rodada):
         Bash: python scripts/verificar_revisao.py "$WORKSPACE" --minuta "$MINUTA" --etapas <revisoes-ok> --gate
         (ex.: --minuta "$MINUTA" --etapas embargabilidade,calculos,fontes,honorarios,remessa --gate;
         com revisor INDISPONÍVEL, listar só os OK — ex.: sem honorários:
         --minuta "$MINUTA" --etapas embargabilidade,calculos,fontes,remessa --gate)
         (exit 1 → algo regrediu OU laudo de outra minuta coincidiu no nome; reportar o
         output e PARAR).
      2. Resumo de 1 tela ao usuário, SEM transcrever conteúdo dos relatórios:
         - Processo ($NUMERO), $MINUTA e $WORKSPACE
         - Artefatos: os 5 relatórios de revisão (marcando REAPROVEITADO vs gerado agora e
           os INDISPONÍVEIS) — eles SÃO o produto deste pipeline
         - Citações: nº de [ERRO] da Etapa 0.5, listados como PENDÊNCIAS a corrigir na peça
           (a correção é da skill redacao-peca-dn, nunca deste pipeline), e avisos
           relevantes (ex.: fontes.json ausente)
         - Lembrete: os laudos apontam defeitos; a decisão de acatar cada apontamento e a
           reescrita da peça são da redacao-peca-dn com o titular.
    </acao_orquestrador>
  </etapa>

</fases_pipeline>

<resumo_arquitetura>
PIPELINE REVISÃO v3.0 adaptado DN — gate por script + retomada; produto = LAUDOS
│
├── 0   Preparação: $WORKSPACE/$NUMERO/$MINUTA + verificar_revisao.py → PENDENTES (o plano)
├── 0.5 Citações [SCRIPT] verificar_citacoes.py --doc "$MINUTA"
│       exit 1 NÃO bloqueia → [ERRO] viram insumo do verificador-fontes e pendências do laudo
├── 1   Revisões em PARALELO (só as pendentes; até 5 Tasks opus no mesmo turno)
│   ├── embargabilidade [Task opus] → $NUMERO-analise-embargabilidade.md ─┐ cada uma: pula se
│   ├── calculos        [Task opus] → $NUMERO-verificacao-calculos.md     │ válida; grava
│   ├── fontes          [Task opus] → $NUMERO-verificacao-fontes.md       │ arquivo; 1 linha;
│   │     (+ fontes.json se existir; + [ERRO] da Etapa 0.5)               │ gate --etapa
│   ├── honorarios      [Task opus] → $NUMERO-verificacao-honorarios.md   │ (2 falhas →
│   └── remessa         [Task opus] → $NUMERO-verificacao-remessa.md     ─┘  INDISPONÍVEL)
│       prosseguir se ≥3 OK (regra v2); menos → PARAR com parciais
└── 3   Finalização: verificar_revisao.py --etapas <revisoes-ok> --gate + resumo (laudo
        consolidado; citações sem lastro listadas como pendências para a redacao-peca-dn)

(A Etapa 2 — Consolidação/minuta robustecida — foi REMOVIDA: NÃO-ROTA em peça de parte;
ver comentário no corpo. O QA entrega laudo; quem reescreve é a redacao-peca-dn.)

Princípios: o documento vive no ARQUIVO (nunca na conversa); a validação é do SCRIPT (âncoras
com acentos normalizados — fonte única em verificar_revisao.py); PENDENTES é o plano (1ª rodada
e retomada são a mesma operação); revisor que falha 2x vira INDISPONÍVEL e não trava o pipeline
(mínimo 3); autenticidade de citação é do script, pertinência é do verificador-fontes.
</resumo_arquitetura>

<checklist_orquestrador>
- [ ] $WORKSPACE/$NUMERO/$MINUTA resolvidos (test -f/-d) e a varredura da Etapa 0 rodou?
- [ ] Etapa 0.5 rodou e o exit 1 (se houve) NÃO bloqueou — [ERRO] guardados para 1c e 2?
- [ ] Todas as etapas VÁLIDAS foram puladas (nada redespachado)?
- [ ] Revisões pendentes despachadas em PARALELO no mesmo turno?
- [ ] Nenhum relatório lido pelo orquestrador (validação só por script)?
- [ ] Subagentes responderam só a linha de status?
- [ ] Verificador-fontes recebeu fontes.json (se existia) e o bloco de citações da Etapa 0.5?
- [ ] Revisor com 2 falhas virou INDISPONÍVEL e a finalização seguiu com ≥3 relatórios OK?
- [ ] NENHUMA minuta foi reescrita (nenhum agente de redação despachado — QA entrega laudo)?
- [ ] Gate final (--etapas <revisoes-ok> --gate) retornou 0?
- [ ] Os [ERRO] de citações da Etapa 0.5 entraram no resumo como pendências?
- [ ] TodoWrite refletiu o reaproveitamento (etapas puladas nascem completed)?
</checklist_orquestrador>
