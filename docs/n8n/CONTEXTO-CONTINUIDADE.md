# Contexto de continuidade — n8n / GitHub Actions

> **Este documento é exclusivamente sobre o workflow local do n8n.** Não é documentação de desenvolvimento do InvestmentAI, não define tarefas de código/testes do repositório e não autoriza alterações no projeto principal. O repositório InvestmentAI está sendo usado apenas como local para guardar esta nota de continuidade.

## Como identificar o projeto correto em um novo chat

O usuário mantém mais de um trabalho relacionado ao GitHub. Antes de agir, identificar o projeto pelo nome explícito no pedido:

- **Projeto n8n / monitoramento GitHub Actions:** configurar o n8n local no Windows para monitorar o repositório `tiagodeazevedoferreira/InvestmentAI`. O foco é o workflow `Agente IA - Laboratório`, os nós do n8n e a deduplicação de alertas. Não modificar código do InvestmentAI.
- **Projeto InvestmentAI (desenvolvimento):** trabalho de engenharia do próprio repositório — código, testes, branches, pull requests, GitHub Actions, diagnóstico OOS, dashboard e demais funcionalidades. Não continuar a configuração do n8n, a menos que o usuário peça explicitamente.

Se o usuário disser apenas “continue”, consultar este documento e o contexto da conversa mais recente. Se ainda houver ambiguidade sobre qual projeto ele quer continuar, perguntar antes de executar qualquer ação.

## Objetivo do projeto n8n

Construir um workflow local que consulta periodicamente as execuções do GitHub Actions do repositório `tiagodeazevedoferreira/InvestmentAI`, identifica falhas e cria issues de alerta somente quando ainda não houver um alerta correspondente.

Requisitos:
- Consulta agendada a cada 15 minutos.
- Distinguir falhas reais de execuções bem-sucedidas.
- Consultar issues abertas antes de criar alertas.
- Evitar duplicidades usando um identificador estável da execução do Actions.
- Manter a análise determinística como fonte de verdade; o ramo de IA é experimental.
- Não publicar/ativar o workflow antes de completar e validar os testes.
- Durante os testes, não criar issues reais sem confirmação explícita.

## Ambiente

- Windows 11.
- n8n v2.43.6, em `http://localhost:5678`.
- Node.js portátil v24.22.0 em `C:\Users\tiago.ferreira\apps\node`.
- Dados do n8n: `C:\Users\tiago.ferreira\.n8n`.
- Inicialização: `C:\Users\tiago.ferreira\apps\Iniciar-n8n.cmd`.
- Existe uma credencial GitHub funcional no n8n. Não solicitar token novo.
- O n8n faz autosave; não instruir o usuário a clicar em Save.

## Workflow existente

Nome: `Agente IA - Laboratório`.

- `When clicking "Execute workflow"` → `Edit Fields manual` → `Merge (1)` Input 1.
- `Schedule Trigger` (a cada 15 minutos) → `Edit Fields manual`.
- Ramo de consulta: `GitHub - Validar Repositório` → `List workflows` → `HTTP Request` → `Code in JavaScript`.
- `Code in JavaScript` alimenta `Merge (1)` Input 2, `Resumo - Indicadores Oficiais` e `IF`.
- Ramo determinístico: `Resumo - Indicadores Oficiais` → `Análise Determinística` → `Consolidar Análise`.
- Ramo experimental de IA: `Merge (1)` → `Preparar Prompt IA` → `llama - Analisar Projeto` → `Extrair Análise IA`. Não usar a IA como autoridade para determinar se houve falha.
- Condição esperada de `IF`: `{{ $json.total_falha }}` is greater than `0`.
- A saída True do `IF` foi conectada a `GitHub - Consultar Issues Abertas`. A saída False foi inicialmente deixada sem conexão; qualquer mudança temporária de conexão precisa ser conferida no canvas antes de avançar.

## Nó Code in JavaScript — situação dos dados

A consulta original retorna as 10 execuções mais recentes. O código calcula contagens e percentuais e cria `falhas` com os campos de workflow, branch, data, mensagem do commit e URL.

No teste mais recente, as 10 execuções retornadas estavam concluídas com sucesso:
- `total_retornado: 10`
- `total_concluido: 10`
- `total_sucesso: 10`
- `total_falha: 0`
- `total_em_andamento: 0`
- `percentual_sucesso: 100`
- `falhas: []`

O campo `url` existe nos objetos de execução e nas falhas. Para deduplicação, é preferível incluir e utilizar o identificador numérico estável `run.id` na estrutura de falhas, em vez de depender apenas de comparação textual de URL.

## Consulta de issues abertas

Nó: `GitHub - Consultar Issues Abertas`.

- Method: GET.
- URL: `https://api.github.com/repos/tiagodeazevedoferreira/InvestmentAI/issues?state=open&per_page=100`.
- Authentication: Predefined Credential Type.
- Credential Type: GitHub API (ou opção GitHub equivalente disponível na instalação).
- Selecionar a credencial GitHub existente.
- Em Options → Response, `Include Response Headers and Status` está ativado.
- Em Settings, `Always Output Data` está desativado.

Teste real:
- HTTP 200 OK.
- `body: []`.
- Interpretação: a API funcionou e não havia issues abertas no momento do teste. Não é um erro.

A opção `Always Output Data` foi ativada temporariamente para diagnóstico e depois desativada novamente. Não a ativar globalmente para mascarar ausência de dados.

## Nó Normalizar Issues Abertas

Conectado após `GitHub - Consultar Issues Abertas`. Mode: `Run Once for All Items`.

Código atual:

```javascript
const response = $input.first().json;

const issues = Array.isArray(response.body)
  ? response.body
  : Array.isArray(response)
    ? response
    : [];

return [{
  json: {
    total_issues_abertas: issues.length,
    issues: issues.map(issue => ({
      numero: issue.number,
      titulo: issue.title,
      estado: issue.state,
      url: issue.html_url,
      criado_em: issue.created_at
    }))
  }
}];
```

Teste confirmado:
```json
[
  {
    "total_issues_abertas": 0,
    "issues": []
  }
]
```

## Nó Identificar Falhas Já Alertadas

- Foi criado um nó Code com esse nome.
- Mode: `Run Once for All Items`.
- Conexão confirmada: `Normalizar Issues Abertas` → `Identificar Falhas Já Alertadas`.
- Ainda sem código, conforme o último estado conhecido.

## Ponto exato de continuidade

A orientação imediatamente anterior foi criar um nó Merge chamado `Combinar Falhas e Issues`, configurá-lo como `Append` e não o conectar ainda. O usuário interrompeu antes de confirmar que executou essa ação, para pedir este documento.

Portanto:
1. Não presumir que `Combinar Falhas e Issues` já foi criado.
2. Perguntar ao usuário se esse nó já foi criado.
3. Não alterar o nó existente `Merge (1)`.
4. Depois de confirmar o estado real do canvas, planejar como reunir os dados de falhas e issues. Um Merge em Append, sozinho, não faz deduplicação; o código seguinte precisa distinguir explicitamente os dois conjuntos de dados.
5. Testar lista vazia, falha já alertada e falha sem alerta, sem criar issues reais durante os testes.
6. Só depois implementar a criação de issue e testar com segurança.

## Como conduzir o trabalho

- Responder em português do Brasil.
- Dar uma única ação por vez e aguardar confirmação.
- Não presumir que uma etapa foi concluída sem confirmação.
- Ser explícito sobre os nomes exatos dos nós e suas conexões.
- Não alterar nem publicar workflows do InvestmentAI.
- Não ativar o workflow n8n até finalizar os testes.
- Se a intenção do usuário for ambígua entre n8n e desenvolvimento do InvestmentAI, perguntar qual dos dois quer continuar.
