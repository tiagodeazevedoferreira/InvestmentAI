# Tarefa Codex — InvestmentAI

TASK_ID: codex-20260911-005
OBJECTIVE: Validar a integração do paper scheduler com a fronteira de MarketDataProvider usando um provider mock determinístico, sem rede externa e sem qualquer autoridade de execução financeira.

SCOPE:
- Inspecionar `backend/app/services/providers.py` e `backend/app/services/paper_scheduler.py`.
- Adicionar teste de integração em memória cobrindo `get_provider("openbb")` -> `OpenBBProvider.history()` mockado -> `run_symbol()`.
- Validar normalização do símbolo B3, passagem do período e consumo do DataFrame pelo scheduler.
- Preservar a semântica existente do Paper Decision Ledger e Shadow Decision Ledger.
- Não alterar a implementação de provider ou scheduler salvo se o teste revelar um defeito mínimo e claramente demonstrável.

CONTEXT:
- Task 004 validou a integração determinística do scheduler com o Shadow Decision Ledger.
- `DEVELOPMENT_STATUS.md` mantém como pendência a suíte de integração contra provider mocks.
- O scheduler usa a abstração `MarketDataProvider` e, por padrão, `get_provider("openbb")`.
- O teste deve substituir somente a chamada de dados por um DataFrame determinístico; não deve acessar OpenBB, yfinance, internet, Firebase real ou MT5.

ACCEPTANCE_CRITERIA:
- Existe teste que instancia o provider pela fábrica `get_provider("openbb")`.
- A chamada `history()` é mockada e recebe o símbolo B3 normalizado com `.SA` e o período solicitado.
- O scheduler consome os dados mockados e produz uma decisão determinística.
- O caminho continua broker-independent e não cria ordens quando `execute=False`.
- O Paper Decision Ledger mantém idempotência e o Shadow Decision Ledger permanece observacional.
- Nenhuma chamada de rede, MT5, `OrderIntent` executável ou `mt5.order_send()` é introduzida.

TESTS:
- Executar o novo teste diretamente.
- Executar `backend/tests` completo.
- Executar `compileall` em `backend/app` e `backend/tests`.
- Fazer busca estática no novo teste para garantir ausência de execução financeira.

DOCUMENTATION:
- Atualizar `DEVELOPMENT_STATUS.md` somente se esta validação permitir marcar materialmente a pendência de integração contra provider mocks como concluída.
- Não alterar `ROADMAP.md` ou criar ADR se não houver mudança arquitetural.

SAFETY_CONSTRAINTS:
- Preservar todos os gates existentes.
- Nenhuma operação financeira.
- DEMO/LIVE intocados.
- Fail-closed em ambiguidades.
- Não usar credenciais, terminal MT5 ou serviços externos.
- Não promover scheduler para broker.

DO_NOT:
- Não chamar `mt5.order_send()`.
- Não criar/alterar/cancelar/submeter ordens DEMO/LIVE.
- Não habilitar scheduler -> DEMO broker integration.
- Não apagar `.runtime/`, `AGENTS.md` ou `scripts/diagnose_first_demo_attempt.py`.
- Não usar `git reset --hard` ou `git clean -fd`.

EXPECTED_OUTPUT:
- Teste de integração determinístico criado.
- Resultados dos testes e validações.
- Riscos e pendências remanescentes.
- Commit criado se houver alterações.
