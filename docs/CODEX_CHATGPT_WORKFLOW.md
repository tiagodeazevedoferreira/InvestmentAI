# Workflow ChatGPT ↔ Codex ↔ GitHub

## Objetivo

Estabelecer um fluxo de desenvolvimento para o InvestmentAI em que:

- **ChatGPT** atua como arquiteto, planejador, analista e revisor;
- **Codex local** atua como executor no workspace Windows, podendo inspecionar arquivos, editar código e executar testes;
- **GitHub** atua como estado compartilhado, histórico e contrato assíncrono entre os dois agentes.

O objetivo é reduzir o copy/paste manual sem transformar o scheduler, o broker DEMO ou o LIVE em mecanismos de execução automática.

## Princípio de integração

A integração deve evoluir em três níveis:

### Nível 1 — protocolo persistente

Toda tarefa relevante deve possuir:

1. objetivo;
2. contexto e arquivos relevantes;
3. critérios de aceite;
4. restrições de segurança;
5. testes esperados;
6. resultado;
7. pendências e próximo passo.

`AGENTS.md` permanece como contrato operacional do Codex. Os documentos de arquitetura, decisões, status e roadmap permanecem como fonte de verdade do projeto.

### Nível 2 — handoff automatizado local

O workspace local poderá iniciar o Codex de forma programática, preferencialmente por uma interface suportada pelo próprio Codex.

As opções avaliadas são:

- `codex exec` para tarefas pontuais e pipelines;
- Codex App Server para integração bidirecional, persistência de threads, eventos e aprovações;
- `codex mcp-server` quando uma integração MCP for mais adequada.

A escolha preferencial para uma integração rica e durável é o **Codex App Server**. `codex exec` é preferível para o primeiro MVP porque reduz a complexidade operacional.

### Nível 3 — ciclo de desenvolvimento assistido

Fluxo-alvo:

```text
Solicitação humana
        ↓
     ChatGPT
        ↓
Plano + critérios de aceite
        ↓
     GitHub
        ↓
 Codex local
        ↓
Implementação + testes
        ↓
     GitHub
        ↓
 ChatGPT / revisão
        ↓
Aprovação ou correção
        ↓
     GitHub
```

O ciclo deve ser idempotente: se uma execução for interrompida, o estado existente deve permitir retomada sem duplicar alterações ou operações.

## Contrato de handoff

Uma tarefa encaminhada ao Codex deve conter, no mínimo:

```text
TASK_ID:
OBJECTIVE:
SCOPE:
CONTEXT:
ACCEPTANCE_CRITERIA:
TESTS:
DOCUMENTATION:
SAFETY_CONSTRAINTS:
DO_NOT:
EXPECTED_OUTPUT:
```

O Codex deve devolver:

```text
TASK_ID:
STATUS: DONE | BLOCKED | PARTIAL
CHANGES:
TESTS:
RESULTS:
RISKS:
PENDING:
NEXT_STEP:
COMMIT:
```

## Regras de segurança

1. Nenhum mecanismo de handoff pode chamar `mt5.order_send()` automaticamente.
2. Nenhuma tarefa de desenvolvimento concede autorização para operação financeira.
3. O scheduler não recebe autoridade de execução.
4. `DEMO` e `LIVE` continuam separados.
5. Uma execução DEMO ambígua permanece recuperável e não pode ser reenviada automaticamente.
6. Segredos permanecem exclusivamente em ambiente/configuração segura.
7. A automação deve parar diante de identidade de conta, reconciliação ou estado operacional ambíguo.

## Estratégia de implementação

### Fase A — contrato

- manter `AGENTS.md` como contrato do Codex;
- manter este documento como descrição do fluxo ChatGPT/Codex;
- usar GitHub como fonte compartilhada de tarefas, commits e evidências.

### Fase B — executor local

Criar um pequeno launcher local para iniciar uma tarefa do Codex a partir de um artefato de tarefa, sem exigir que o usuário copie manualmente o prompt inteiro.

O launcher não deve conter lógica de negócio do InvestmentAI. Sua responsabilidade é apenas:

1. localizar o workspace;
2. carregar a tarefa;
3. iniciar o Codex;
4. capturar saída e código de retorno;
5. registrar o resultado.

### Fase C — integração rica

Se o MVP com `codex exec` atingir o objetivo, avaliar a migração para Codex App Server para obter:

- threads persistentes;
- eventos de progresso;
- pedidos de aprovação;
- controle bidirecional;
- reconexão;
- múltiplas tarefas/agentes.

## O que não faz parte desta automação

A integração ChatGPT/Codex é uma infraestrutura de desenvolvimento. Ela não deve ser usada para transformar o InvestmentAI em um agente financeiro autônomo.

Em particular, não será criada uma ponte implícita:

```text
scheduler → Codex → MT5 → order_send
```

Qualquer caminho de execução financeira continuará submetido aos gates existentes e à autorização humana específica.

## Estado inicial

Em 2026-09-11, o repositório possui o boundary fail-closed Scheduler → DEMO e a camada explícita `SchedulerDemoExecutionAdapter`, mas a integração de execução automática do scheduler com o broker permanece deliberadamente desconectada.

O próximo passo desta iniciativa é implementar e validar o **MVP do executor local baseado em `codex exec`**, sem alterar a lógica financeira do InvestmentAI.
