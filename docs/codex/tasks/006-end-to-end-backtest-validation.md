# Tarefa Codex — InvestmentAI

TASK_ID: codex-20260911-006
OBJECTIVE: Validar de ponta a ponta o backtester determinístico existente usando MarketReplay e dados OHLCV sintéticos, cobrindo execução no candle seguinte, custos, liquidação final e rejeição de sinais inválidos.

SCOPE:
- Inspecionar `backend/app/services/market_replay.py` e `backend/app/services/backtesting.py`.
- Adicionar testes determinísticos para o fluxo MarketReplay -> Backtester -> BacktestResult.
- Validar que o sinal do candle t só é executado na abertura do candle t+1.
- Validar comissão, slippage, contagem de trades e liquidação final.
- Validar que sinais fora de {-1, 0, 1} falham de forma explícita.
- Não alterar a implementação salvo se um defeito mínimo e claramente demonstrável for encontrado.

CONTEXT:
- Task 005 validou a integração do Paper Scheduler com provider mock.
- O repositório possui um backtester mais completo em `backtesting.py`, separado do backtest legado em `backtest.py`.
- O backtester documenta explicitamente a regra anti-look-ahead: sinal em t é executado na abertura de t+1.
- A validação deve ser totalmente offline, sem OpenBB, yfinance, Firebase, MT5 ou broker.

ACCEPTANCE_CRITERIA:
- Existe teste cobrindo sinal BUY em um candle e execução somente no open do candle seguinte.
- Existe teste cobrindo comissão e slippage determinísticos.
- A liquidação final deixa `final_position == 0` e torna `final_cash` economicamente realizável.
- O resultado contém equity cronológica e contagem determinística de trades.
- Sinal inválido gera `ValueError`.
- Nenhuma autoridade de execução financeira externa é introduzida.

TESTS:
- Executar o novo teste diretamente.
- Executar `backend/tests` completo.
- Executar `compileall` em `backend/app` e `backend/tests`.
- Fazer busca estática no novo teste para garantir ausência de MT5/order_send/OrderIntent/DOTO.

DOCUMENTATION:
- Não marcar automaticamente a pendência geral de `End-to-end training/backtest test`, pois esta tarefa valida somente o backtest e não implementa um pipeline de treinamento.
- Não alterar `ROADMAP.md` ou criar ADR.

SAFETY_CONSTRAINTS:
- Operação exclusivamente offline e determinística.
- Nenhuma operação financeira real ou DEMO.
- Não chamar `mt5.order_send()`.
- Não criar/alterar/cancelar/submeter ordens.
- Preservar `.runtime/`, `AGENTS.md` e `scripts/diagnose_first_demo_attempt.py`.
- Não usar `git reset --hard` ou `git clean -fd`.

EXPECTED_OUTPUT:
- Testes de integração do backtester criados.
- Resultados dos testes e validações.
- Riscos e pendências remanescentes.
- Commit criado se houver alterações.
