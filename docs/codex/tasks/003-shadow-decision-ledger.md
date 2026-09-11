# Tarefa Codex — InvestmentAI

```text
TASK_ID: codex-20260911-003
OBJECTIVE: Implementar a capacidade de registrar decisões de trading em um shadow decision ledger, separada da execução paper/demo/live, para permitir observabilidade e comparação futura entre decisões teóricas e resultados sem qualquer autoridade de execução.

SCOPE:
- Inspecionar a implementação atual de paper scheduler, decision ledger, outcome attribution e persistência operacional para reutilizar abstrações existentes.
- Implementar somente o menor incremento necessário para suportar um shadow decision ledger determinístico, idempotente e broker-independent.
- Adicionar testes unitários cobrindo criação, chave determinística, idempotência, leitura e comportamento de estado/erro relevante.
- Atualizar DEVELOPMENT_STATUS.md e, se necessário, ROADMAP.md com o estado real da entrega.
- Não alterar o comportamento existente do paper scheduler/ledger além da integração explícita e segura necessária ao shadow ledger.

CONTEXT:
- O DEVELOPMENT_STATUS.md registra o item "Shadow decision ledger" como pendente.
- O paper path já possui scheduler, idempotent decision ledger, outcomes persistidos, calibração e reconciliação.
- A arquitetura separa simulation -> paper -> demo -> live e exige fail-closed behavior.
- O scheduler não possui autoridade de execução de broker.
- O shadow ledger deve representar uma decisão teórica/observacional e nunca uma ordem submetível.
- O estado atual do Doto/MT5 DEMO já foi validado com uma única transação explicitamente autorizada; não criar outra transação para esta tarefa.

ACCEPTANCE_CRITERIA:
- Existe uma abstração clara para shadow decision records, reutilizando os padrões existentes quando apropriado.
- Cada shadow decision possui identidade/chave determinística suficiente para impedir duplicação do mesmo evento lógico.
- Repetir a gravação do mesmo evento lógico é idempotente e não cria múltiplos registros equivalentes.
- O registro preserva pelo menos timestamp/evento, símbolo, direção/decisão, quantidade ou sizing quando aplicável, referência/preço quando aplicável, origem/política e resultado de risco/sinal disponível no contexto.
- O shadow ledger não chama broker, não chama MT5, não chama order_send e não cria OrderIntent executável.
- A implementação permanece independente de DEMO/LIVE e não cria qualquer caminho de promoção automática.
- Testes novos cobrem os invariantes de idempotência e isolamento de execução.
- A documentação de status/roadmap é atualizada somente com o que foi efetivamente implementado.

TESTS:
- Executar os testes unitários diretamente relacionados ao novo ledger e integrações alteradas.
- Executar a suíte relevante existente de paper scheduler/decision ledger/outcome attribution.
- Executar a suíte completa de backend quando viável.
- Validar que nenhum teste ou código novo chama mt5.order_send() ou qualquer executor de broker.

DOCUMENTATION:
- Atualizar DEVELOPMENT_STATUS.md para marcar "Shadow decision ledger" como concluído somente se todos os critérios forem atendidos.
- Atualizar ROADMAP.md somente se a entrega alterar materialmente o estado do roadmap.
- Se uma decisão arquitetural nova for necessária, registrar em DECISIONS.md; não criar ADR apenas por conveniência.

SAFETY_CONSTRAINTS:
- Preservar todos os gates existentes.
- Nenhuma operação financeira.
- DEMO/LIVE permanecem intocados.
- Fail-closed em caso de ambiguidade ou erro de persistência relevante.
- Não usar credenciais nem depender de terminal MT5.
- Não criar mecanismos de auto-promoção ou auto-execução.

DO_NOT:
- Não chamar mt5.order_send().
- Não criar, alterar, cancelar ou submeter ordens DEMO/LIVE.
- Não conectar o shadow ledger ao broker.
- Não habilitar scheduler -> DEMO broker integration.
- Não remover testes, estado operacional ou controles de segurança.
- Não executar git reset --hard, git clean -fd ou apagar alterações locais não relacionadas.
- Não modificar arquivos fora do escopo sem justificativa explícita no handoff.

EXPECTED_OUTPUT:
- Implementação concluída ou bloqueada com justificativa objetiva.
- Lista de arquivos alterados.
- Testes executados e resultados.
- Riscos e pendências.
- Commit criado se houver alterações.
- Handoff estruturado conforme o contrato do runner.
```
