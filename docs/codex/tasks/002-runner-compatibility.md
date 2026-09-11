# Codex Runner Compatibility

```text
TASK_ID: codex-20260911-002
OBJECTIVE: Validar a compatibilidade do runner local com a versão instalada do Codex CLI.

SCOPE:
- Inspecionar somente a CLI Codex e o estado do repositório.
- Não alterar arquivos do projeto.

CONTEXT:
- O runner chama `codex exec` com sandbox workspace-write, approval_policy on-request, JSON estruturado e output-schema.
- O runner resolve o executável do Codex por PATH ou pela instalação do Codex App e expõe o caminho resolvido em `CODEX_CLI_PATH`.
- A sessão do agente pode ter um PATH diferente da sessão PowerShell que iniciou o runner; por isso, a validação da CLI deve usar `CODEX_CLI_PATH` em vez de depender de `codex` no PATH.
- O objetivo é confirmar que esses argumentos são aceitos pela versão instalada localmente.

ACCEPTANCE_CRITERIA:
- Informar a versão exata do Codex CLI usando `& $env:CODEX_CLI_PATH --version`.
- Confirmar que `codex exec --help` expõe `--sandbox`, usando o executável em `CODEX_CLI_PATH`.
- Confirmar que `codex exec --help` expõe `--config`, usando o executável em `CODEX_CLI_PATH`.
- Confirmar que `codex exec --help` expõe `--json`, usando o executável em `CODEX_CLI_PATH`.
- Confirmar que `codex exec --help` expõe `--output-schema`, usando o executável em `CODEX_CLI_PATH`.
- Confirmar que `codex exec --help` expõe `--output-last-message`, usando o executável em `CODEX_CLI_PATH`.
- Informar branch, commit atual e estado Git.
- Não alterar arquivos.

TESTS:
- Executar apenas comandos de inspeção da CLI e Git.

DOCUMENTATION:
- Nenhuma.

SAFETY_CONSTRAINTS:
- Não executar operações financeiras.
- Não conectar ao MT5.
- Não modificar .runtime/.
- Não criar commits.

DO_NOT:
- Não editar arquivos.
- Não executar scripts de negócio.
- Não instalar ou atualizar dependências.

EXPECTED_OUTPUT:
- Handoff JSON com status DONE se todos os critérios forem confirmados; caso contrário BLOCKED ou PARTIAL com a incompatibilidade encontrada.
```
