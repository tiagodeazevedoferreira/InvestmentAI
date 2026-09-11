# Tarefa Codex — InvestmentAI

```text
TASK_ID: codex-YYYYMMDD-NNN
OBJECTIVE: Descreva o resultado esperado.

SCOPE:
- Arquivos/módulos permitidos.
- Limites da alteração.

CONTEXT:
- Contexto técnico necessário.
- Decisões/ADRs relevantes.

ACCEPTANCE_CRITERIA:
- Critério verificável 1.
- Critério verificável 2.

TESTS:
- Testes unitários/integrados esperados.
- Comandos de validação, quando conhecidos.

DOCUMENTATION:
- Documentos que precisam ser atualizados, se aplicável.

SAFETY_CONSTRAINTS:
- Preservar gates existentes.
- Não executar operações financeiras.

DO_NOT:
- Não modificar componentes fora do escopo.
- Não apagar estado operacional.

EXPECTED_OUTPUT:
- Alterações realizadas.
- Testes e resultados.
- Riscos e pendências.
```

## Como usar

1. Salve uma tarefa baseada neste template.
2. Execute `scripts/run_codex_task.ps1 -TaskFile <arquivo>` dentro do workspace.
3. O runner cria uma execução em `.runtime/codex/<timestamp>/`.
4. `events.jsonl` contém os eventos da execução.
5. `result.json` contém o handoff estruturado para o ChatGPT.

O runner usa `codex exec` com `workspace-write` e política de aprovação `on-request`. Ele não usa o modo de bypass de aprovações/sandbox.
