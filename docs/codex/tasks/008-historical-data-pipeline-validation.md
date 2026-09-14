# Tarefa Codex — InvestmentAI

TASK_ID: codex-20260914-008
OBJECTIVE: Padronizar e validar o contrato do pipeline histórico de mercado, garantindo que dados OHLCV provenientes de adapters sejam normalizados antes de passar pelo quality gate, technical indicators, feature engineering e walk-forward validation, sem introduzir dependência de dados externos nesta tarefa.

SCOPE:
- Inspecionar o contrato atual entre `OpenBBMarketDataProvider`, `data_quality.py`, `technical.py`, `features.py` e `walk_forward.py`.
- Corrigir a menor inconsistência necessária entre o formato OHLCV retornado pelo adapter e o formato canônico esperado por `technical.indicators()`.
- Utilizar `validate_market_data()` como quality gate completo para o pipeline histórico, sem duplicar desnecessariamente sua lógica de validação.
- Preservar a separação entre adapter externo e infraestrutura interna.
- Validar a integração `OHLCV -> quality gate -> indicators -> build_features()` usando somente DataFrames sintéticos determinísticos.
- Validar `purged_walk_forward()` com horizonte de 5 barras e dados sintéticos determinísticos.
- Validar explicitamente a separação temporal e a purga entre treino e teste.
- Criar testes para dados inválidos e para o contrato normalizado.
- Não baixar dados reais nem depender de Internet nesta tarefa.

CONTEXT:
- Task 006 validou o backtester determinístico com `MarketReplay` e `Backtester`.
- Task 007 implementou purge temporal explícito para o split de ML e validou o horizonte de 5 barras.
- `OpenBBMarketDataProvider.historical()` normalizava as colunas para minúsculas (`open`, `high`, `low`, `close`, `volume`).
- `technical.validate_ohlcv()` e `technical.indicators()` esperam as colunas canônicas capitalizadas `Open`, `High`, `Low`, `Close`, `Volume`.
- Portanto, existia uma quebra de contrato entre o adapter histórico e o pipeline de features.
- `data_quality.validate_market_data()` possui um quality gate mais completo que `OpenBBMarketDataProvider.quality()`, incluindo duplicidades, nulos, valores não finitos, timestamps não monotônicos, OHLC inválido e volume negativo.
- O quality gate trata grandes gaps de calendário como observabilidade, não como falha automática, porque feriados e eventos de mercado podem gerar gaps legítimos.
- `purged_walk_forward()` já possui uma purga de `horizon` entre train e test e não deve ser reescrito arquiteturalmente nesta tarefa sem evidência objetiva de defeito.
- `Backtester` já possui lógica própria de execução no próximo candle, comissão e slippage; esta tarefa não deve criar outro backtester nem alterar sua lógica econômica.

IMPLEMENTATION:
- `backend/app/services/data_quality.py` passou a usar `Open`, `High`, `Low`, `Close`, `Volume` como contrato OHLCV canônico e concentra a validação estrutural e numérica do pipeline histórico em `validate_market_data()`.
- `backend/app/services/openbb_market_data.py` passou a normalizar frames históricos na fronteira do provider, incluindo índice datetime, ordenação temporal e mapeamento case-insensitive das colunas OHLCV para o contrato canônico.
- `OpenBBMarketDataProvider.quality()` e `historical_with_quality()` utilizam o quality gate compartilhado, evitando duplicação da lógica de validação.
- `purged_walk_forward()` foi mantido arquiteturalmente intacto; os testes confirmam a separação temporal já implementada para `horizon=5`.
- A normalização e o quality gate permanecem independentes de execução financeira.

ACCEPTANCE_CRITERIA:
- [x] `OpenBBMarketDataProvider` produz o formato OHLCV canônico utilizado internamente por `technical.indicators()`.
- [x] Dados OHLCV válidos passam pelo quality gate completo.
- [x] Dados com coluna ausente são rejeitados pelo quality gate.
- [x] Dados com timestamp duplicado são rejeitados.
- [x] Dados com timestamp não monotônico são rejeitados.
- [x] Dados com valores nulos ou não numéricos nos campos obrigatórios são rejeitados.
- [x] Dados com valores não finitos são rejeitados.
- [x] Dados com OHLC inválido são rejeitados.
- [x] Dados com volume negativo são rejeitados.
- [x] Gaps de calendário são reportados, mas não rejeitam automaticamente os dados.
- [x] O pipeline normalizado funciona diretamente com `technical.indicators()`.
- [x] `build_features(..., horizon=5)` funciona sobre dados OHLCV normalizados.
- [x] `purged_walk_forward(..., horizon=5)` preserva a separação temporal esperada.
- [x] Nenhuma observação do intervalo de purga é utilizada no conjunto de teste.
- [x] Os testes são determinísticos e não dependem de dados externos.
- [x] Nenhum teste inicializa OpenBB, yfinance ou MT5.
- [x] Nenhum teste chama `mt5.order_send()` ou qualquer operação financeira.
- [x] Nenhuma credencial é utilizada.

TESTS:
- [x] Testes unitários para `validate_market_data()` cobrindo dados válidos e inválidos.
- [x] Testes para `OpenBBMarketDataProvider.normalize_symbol()`.
- [x] Teste do adapter/normalização utilizando resultado sintético, sem inicializar OpenBB.
- [x] Teste da integração quality gate -> `technical.indicators()` -> `build_features()`.
- [x] Testes de `purged_walk_forward()` com dados sintéticos determinísticos.
- [x] Teste explícito da purga de 5 barras.
- [x] Suíte completa `backend/tests` executada.
- [x] `compileall` executado em `backend`.
- [x] Scan estático executado para referências a `MetaTrader5`, `mt5.order_send`, `order_send`, DOTO ou execução financeira.

VALIDATION_RESULTS:
- Task 008 focused tests: **14 passed**.
- Complete `backend/tests` suite: **39 passed**.
- `compileall -q backend`: passed with no output/errors.
- Static scan: only pre-existing MT5/DOTO/execution references were found in unrelated backend components; no Task 008 execution dependency was introduced.
- No real market data, OpenBB initialization, yfinance connection, MT5 connection, DOTO connection or financial operation was used.

TEMPORAL_BOUNDARY:
For `horizon=5`, the walk-forward implementation trains on the observations immediately before the boundary, leaves the next five feature observations outside the test set, and begins the test set after that purge interval. The explicit test validates that the first test observation starts exactly after the five-observation purge and that train/test ranges remain temporally ordered and disjoint.

RISKS_AND_REMAINING_WORK:
- This task validates the historical pipeline contract and temporal behavior with deterministic synthetic data only.
- Real historical dataset ingestion remains pending.
- Real-provider historical validation remains pending.
- Training workflow on real datasets remains pending.
- The broader end-to-end training/backtest validation remains pending.
- Provider calibration against historical outcomes remains pending.

DOCUMENTATION:
- `DEVELOPMENT_STATUS.md` updated with the completed historical OHLCV normalization/quality-gate validation and explicit synthetic-data boundary.
- `docs/PROJECT_CONTEXT.md` updated with Task 008 implementation, validation results and remaining real-data limitations.
- No ROADMAP or ADR change was required because the fix was a contract correction within the existing architecture.

SAFETY:
- Offline/synthetic validation only.
- No DEMO or LIVE operation.
- No broker submission.
- No `mt5.order_send()`.
- No DOTO connection.
- Existing execution gates and financial safety boundaries were not modified.

STATUS: COMPLETED AND VALIDATED
