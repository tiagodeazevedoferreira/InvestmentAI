# Tarefa Codex — InvestmentAI

TASK_ID: codex-20260914-007
OBJECTIVE: Tornar e validar o particionamento temporal do dataset de ML leakage-safe para o horizonte de previsão de 5 barras, sem alterar a política de execução e sem introduzir qualquer acesso a broker.

SCOPE:
- Inspecionar `backend/app/services/ml.py` e todos os usos de `chronological_split` encontrados no repositório.
- Demonstrar por teste o risco atual: `target_5d_up` usa `close.shift(-5)`, portanto as últimas linhas de um conjunto podem ter rótulos que dependem de barras pertencentes ao próximo conjunto temporal.
- Implementar a menor alteração necessária para permitir um purge temporal explícito entre conjuntos, compatível com o horizonte do target.
- Garantir que o treinamento/avaliação existente, quando usar horizonte de 5 barras, não mantenha no train ou validation amostras cujo rótulo dependa de dados posteriores ao limite do respectivo conjunto.
- Preservar a ordem cronológica e impedir mistura aleatória entre passado e futuro.
- Não implementar ainda treinamento com dataset real nem buscar dados externos nesta tarefa.

CONTEXT:
- Task 006 validou o backtester determinístico com MarketReplay e Backtester: 3/3 testes focados e 21/21 testes do backend passaram.
- O serviço `ml.py` já possui `make_features()` com `target_5d_up = (close.shift(-5) > close).astype(float)` e `chronological_split()` com divisão temporal simples.
- A divisão atual não considera explicitamente o horizonte do target ao definir as fronteiras. Isso precisa ser tratado antes de usar datasets históricos reais para treinamento/avaliação.
- Features atuais são baseadas em dados passados (retornos, volatilidade rolling, EMA, Bollinger, volume), mas o target possui dependência futura de 5 barras.
- A correção deve ser leakage-safe e determinística, sem alterar a lógica de execução do Paper Scheduler ou do broker.

ACCEPTANCE_CRITERIA:
- Existe teste reproduzível demonstrando que, com horizonte de 5 barras, amostras no final de train/validation não podem ter target calculado usando barras do conjunto temporal seguinte.
- Existe mecanismo explícito de purge/horizon na divisão temporal.
- O comportamento padrão existente não é quebrado sem necessidade; mudanças de API devem ser pequenas e documentadas.
- As fronteiras continuam cronológicas e determinísticas.
- Não há shuffle ou qualquer uso de dados futuros nas features de uma amostra.
- Os testes existentes relacionados a ML continuam passando.
- Nenhuma chamada de rede, OpenBB, yfinance, Firebase, MT5, broker ou `order_send` é necessária.

TESTS:
- Criar teste focado para o purge leakage-safe.
- Executar o teste focado.
- Executar `backend/tests` completo.
- Executar `compileall` em `backend/app` e `backend/tests`.
- Fazer scan estático dos arquivos alterados para referências a `MetaTrader5`, `mt5.order_send`, `order_send`, DOTO ou execução financeira.

DOCUMENTATION:
- Registrar a decisão e o comportamento no arquivo de tarefa.
- Atualizar `docs/PROJECT_CONTEXT.md` e `DEVELOPMENT_STATUS.md` somente se a implementação realmente for concluída e validada.
- Não marcar `Training workflow on real datasets` como concluído.
- Não marcar o item geral `End-to-end training/backtest test` como concluído apenas por esta tarefa.
- Não alterar `ROADMAP.md` ou criar ADR, salvo se uma mudança arquitetural real for demonstrada.

SAFETY_CONSTRAINTS:
- Tarefa exclusivamente offline/simulada.
- Nenhuma operação financeira real ou DEMO.
- Não chamar `mt5.order_send()`.
- Não criar, alterar, cancelar ou submeter ordens.
- Preservar `.runtime/`, `AGENTS.md` e `scripts/diagnose_first_demo_attempt.py`.
- Não usar `git reset --hard` ou `git clean -fd`.
- Não apagar ou sobrescrever arquivos locais não rastreados.

EXPECTED_OUTPUT:
- Implementação mínima de purge temporal leakage-safe, se o defeito for confirmado.
- Testes focados e resultados da suíte completa.
- Explicação objetiva das fronteiras temporais e do horizonte utilizado.
- Riscos e pendências remanescentes, especialmente treinamento com dataset real.
- Commit criado se houver alterações.
