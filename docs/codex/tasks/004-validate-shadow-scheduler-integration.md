# Tarefa Codex — InvestmentAI

TASK_ID: codex-20260911-004
OBJECTIVE: Validar a integração do Shadow Decision Ledger com o paper scheduler em um cenário determinístico, garantindo que execuções repetidas do mesmo evento lógico produzam a mesma shadow decision e não criem registros duplicados, sem alterar o comportamento do Paper Decision Ledger.

SCOPE:
- Inspecionar `backend/app/services/paper_scheduler.py`, `backend/app/services/shadow_decision_ledger.py` e os testes existentes relacionados.
- Adicionar somente os testes e o menor ajuste de implementação necessário para validar a integração determinística do scheduler com o shadow ledger.
- Cobrir repetição do mesmo evento lógico, identidade determinística e ausência de duplicação no shadow ledger.
- Verificar que o Paper Decision Ledger continua com seu comportamento atual de claim/idempotência.
- Atualizar `DEVELOPMENT_STATUS.md` somente se a validação alterar materialmente o status real da entrega.

CONTEXT:
- Task 003 foi concluída no commit `698f3fd` e publicada em `main`.
- O Shadow Decision Ledger já existe, é broker-independent, usa identidade determinística e tem `execution_authority=none`.
- O `paper_scheduler` registra a shadow decision antes de processar o Paper Decision Ledger quando um shadow ledger é fornecido; por padrão ele instancia um ShadowDecisionLedger associado ao Firebase do scheduler.
- Task 004 deve validar a integração sem criar operações financeiras.
- Arquivos locais não relacionados (`.runtime/`, `AGENTS.md`, `scripts/diagnose_first_demo_attempt.py`) devem ser preservados.

ACCEPTANCE_CRITERIA:
- Existe teste determinístico da integração `paper_scheduler` -> Shadow Decision Ledger.
- Repetir o mesmo evento lógico não cria múltiplos shadow records equivalentes.
- O identificador da shadow decision permanece estável entre repetições do mesmo evento lógico.
- A integração não altera a semântica existente do Paper Decision Ledger; os testes relevantes continuam passando.
- O teste demonstra que o caminho shadow não possui autoridade de execução e não depende de MT5/broker.
- Não são criados `OrderIntent` executáveis nem chamadas a `mt5.order_send()`.
- Nenhuma operação DEMO/LIVE é criada, modificada, cancelada ou submetida.
- Testes relacionados e suíte relevante do backend passam.

TESTS:
- Executar testes diretamente relacionados ao `paper_scheduler` e Shadow Decision Ledger.
- Executar suíte relevante do backend.
- Executar compileall nos arquivos alterados quando aplicável.
- Fazer busca estática no escopo alterado para garantir ausência de `mt5.order_send`, `MetaTrader5`, `OrderIntent` executável ou integração de broker.

DOCUMENTATION:
- Atualizar `DEVELOPMENT_STATUS.md` apenas se necessário para refletir a validação efetivamente concluída.
- Não alterar `ROADMAP.md` ou criar ADR se não houver mudança arquitetural material.

SAFETY_CONSTRAINTS:
- Preservar todos os gates existentes.
- Nenhuma operação financeira.
- DEMO/LIVE intocados.
- Fail-closed em ambiguidades ou erros relevantes.
- Não usar credenciais nem depender de terminal MT5.
- Não criar promoção automática ou caminho scheduler -> broker.

DO_NOT:
- Não chamar `mt5.order_send()`.
- Não criar/alterar/cancelar/submeter ordens DEMO/LIVE.
- Não conectar o Shadow Decision Ledger a qualquer executor de broker.
- Não habilitar scheduler -> DEMO broker integration.
- Não apagar testes, estado operacional ou controles de segurança.
- Não usar `git reset --hard`, `git clean -fd` ou apagar alterações locais não relacionadas.
- Não modificar arquivos fora do escopo sem justificativa explícita no handoff.

EXPECTED_OUTPUT:
- Implementação/testes concluídos ou bloqueados com justificativa objetiva.
- Lista de arquivos alterados.
- Testes executados e resultados.
- Riscos e pendências.
- Commit criado se houver alterações.
- Handoff estruturado conforme contrato do runner.
