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
- `OpenBBMarketDataProvider.historical()` atualmente normaliza as colunas para minúsculas (`open`, `high`, `low`, `close`, `volume`).
- `technical.validate_ohlcv()` e `technical.indicators()` esperam as colunas canônicas capitalizadas `Open`, `High`, `Low`, `Close`, `Volume`.
- Portanto, existe atualmente uma quebra de contrato entre o adapter histórico e o pipeline de features.
- `data_quality.validate_market_data()` possui um quality gate mais completo que `OpenBBMarketDataProvider.quality()`, incluindo duplicidades, nulos, valores não finitos, timestamps não monotônicos, OHLC inválido e volume negativo.
- O quality gate trata grandes gaps de calendário como observabilidade, não como falha automática, porque feriados e eventos de mercado podem gerar gaps legítimos.
- `purged_walk_forward()` já possui uma purga de `horizon` entre train e test e não deve ser reescrito arquiteturalmente nesta tarefa sem evidência objetiva de defeito.
- `Backtester` já possui lógica própria de execução no próximo candle, comissão e slippage; esta tarefa não deve criar outro backtester nem alterar sua lógica econômica.

ACCEPTANCE_CRITERIA:
- `OpenBBMarketDataProvider` produz o formato OHLCV canônico utilizado internamente por `technical.indicators()`.
- Dados OHLCV válidos passam pelo quality gate completo.
- Dados com coluna ausente são rejeitados pelo quality gate.
- Dados com timestamp duplicado são rejeitados.
- Dados com timestamp não monotônico são rejeitados.
- Dados com valores nulos ou não numéricos nos campos obrigatórios são rejeitados.
- Dados com valores não finitos são rejeitados.
- Dados com OHLC inválido são rejeitados.
- Dados com volume negativo são rejeitados.
- Gaps de calendário são reportados, mas não rejeitam automaticamente os dados.
- O pipeline normalizado funciona diretamente com `technical.indicators()`.
- `build_features(..., horizon=5)` funciona sobre dados OHLCV normalizados.
- `purged_walk_forward(..., horizon=5)` preserva a separação temporal esperada.
- Nenhuma observação do intervalo de purga é utilizada no conjunto de teste.
- Os testes são determinísticos e não dependem de dados externos.
- Nenhum teste inicializa OpenBB, yfinance ou MT5.
- Nenhum teste chama `mt5.order_send()` ou qualquer operação financeira.
- Nenhuma credencial é utilizada.

TESTS:
- Criar testes unitários para `validate_market_data()` cobrindo dados válidos e inválidos.
- Criar testes para `OpenBBMarketDataProvider.normalize_symbol()`.
- Criar teste do adapter/normalização utilizando resultado sintético, sem importar ou inicializar OpenBB.
- Criar teste da integração quality gate -> `technical.indicators()` -> `build_features()`.
- Criar testes de `purged_walk_forward()` com dados sintéticos determinísticos.
- Criar teste explícito da purga de 5 barras.
- Executar a suíte completa `backend/tests`.
- Executar `compileall` em `backend/app` e `backend/tests`.
- Fazer scan estático dos arquivos alterados para referências a `MetaTrader5`, `mt5.order_send`, `order_send`, DOTO ou execução financeira.

DOCUMENTATION:
- Registrar a decisão e o comportamento no arquivo de tarefa.
- Atualizar `docs/PROJECT_CONTEXT.md` e `DEVELOPMENT_STATUS.md` somente se a implementação realmente for concluída e validada.
- Não marcar `Training workflow on real datasets` como concluído.
- Não marcar validação com dataset histórico real como concluída.
- Não marcar o item geral `End-to-end training/backtest test` como concluído apenas por esta tarefa.
- Não alterar `ROADMAP.md` ou criar ADR, salvo se uma mudança arquitetural real for demonstrada.

SAFETY_CONSTRAINTS:
- Tarefa exclusivamente offline/simulada.
- Nenhuma operação financeira real ou DEMO.
- Não chamar `mt5.order_send()`.
- Não criar, alterar, cancelar ou submeter ordens.
- Não conectar ao DOTO.
- Preservar `.runtime/`, `AGENTS.md` e `scripts/diagnose_first_demo_attempt.py`.
- Não usar `git reset --hard` ou `git clean -fd`.
- Não apagar ou sobrescrever arquivos locais não rastreados.

DO_NOT:
- Não baixar dados reais.
- Não conectar OpenBB.
- Não conectar yfinance.
- Não conectar MT5.
- Não executar operações financeiras.
- Não alterar o fluxo DEMO.
- Não alterar `.runtime/`.
- Não alterar `AGENTS.md`.
- Não alterar `scripts/diagnose_first_demo_attempt.py`.
- Não criar um novo backtester.
- Não alterar a lógica econômica de `Backtester` sem necessidade diretamente demonstrada pelos testes.
- Não transformar a tarefa em validação de performance de estratégia com dados reais.

EXPECTED_OUTPUT:
- Contrato OHLCV interno consistente entre adapter, quality gate, indicadores e features.
- Quality gate único e testado para o pipeline histórico.
- Testes determinísticos cobrindo dados válidos, inválidos, features e walk-forward.
- Explicação objetiva das fronteiras temporais e do horizonte utilizado.
- Resultados da suíte completa, compileall e scan de segurança.
- Riscos e pendências remanescentes, especialmente integração com dados históricos reais.
- Commit criado se houver alterações.
