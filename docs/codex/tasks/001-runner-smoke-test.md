# Codex Runner Smoke Test

```text
TASK_ID: codex-20260911-001
OBJECTIVE: Validar o executor local ChatGPT ↔ Codex do InvestmentAI.

SCOPE:
- Somente inspeção do estado do repositório.
- Não alterar nenhum arquivo.

CONTEXT:
- O runner deve iniciar o Codex em modo não interativo.
- O objetivo é validar recebimento da tarefa e retorno estruturado.

ACCEPTANCE_CRITERIA:
- Informar a branch atual.
- Informar o último commit.
- Informar se existem alterações locais ou arquivos não rastreados.
- Não alterar arquivos.

TESTS:
- Executar apenas comandos de inspeção Git necessários.

DOCUMENTATION:
- Nenhuma.

SAFETY_CONSTRAINTS:
- Não executar operações financeiras.
- Não conectar ao MT5.
- Não modificar .runtime/.

DO_NOT:
- Não editar arquivos.
- Não criar commits.
- Não executar scripts de negócio.

EXPECTED_OUTPUT:
- Handoff JSON com status DONE, mudanças vazias, testes/resultados, riscos e próximo passo.
```
