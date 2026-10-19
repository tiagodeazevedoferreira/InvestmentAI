# Contexto de continuidade — n8n / InvestmentAI

> **ESTADO ATUAL — 19/10/2026. Esta seção prevalece sobre instruções antigas abaixo que descrevem apenas o monitor de GitHub Actions.** O usuário mudou explicitamente a direção: o objetivo prioritário agora é criar um agente de desenvolvimento no n8n para ajudar a finalizar o projeto InvestmentAI. O workflow antigo de monitoramento deve ser preservado como referência e não deve ser desmontado.

## Objetivo atual

Construir um workflow n8n separado, inicialmente executado manualmente, que ajude a continuar e concluir o desenvolvimento de `tiagodeazevedoferreira/InvestmentAI`. A visão evolutiva é: ler o estado real do repositório e seus documentos, identificar a próxima tarefa técnica, planejar alterações, implementar de forma controlada, executar/consultar testes e GitHub Actions, diagnosticar falhas e iterar. Começar com etapas de leitura e análise, adicionando capacidade de escrita só depois de validada e com controles explícitos.

O usuário já aprendeu o básico do n8n e agora quer usá-lo como agente que participe da conclusão do próprio InvestmentAI. Não continuar priorizando o monitoramento de Actions como finalidade principal, a menos que o usuário peça.

## Estado exato do workflow novo

- Workflow novo criado na interface n8n, separado do workflow antigo.
- Nome combinado: `InvestmentAI - Agente de Desenvolvimento`.
- Nó inicial adicionado: `When clicking 'Execute workflow'` (Manual Trigger).
- Ainda não há outros nós confirmados nesse workflow.
- Última instrução dada: adicionar um nó GitHub, mas o usuário esclareceu que o editor exige selecionar uma ação ao adicionar o nó.
- **Próxima ação orientada:** adicionar o nó GitHub escolhendo a ação de leitura de arquivo (`Get a file` / `Get File`, conforme o rótulo da versão instalada), para começar lendo um arquivo de contexto do repositório. Se a interface não oferecer essa ação, pedir ao usuário os nomes exatos das opções exibidas antes de escolher uma alternativa.
- O nó GitHub ainda não foi confirmado como adicionado/configurado.
- Não executar o workflow ainda. Não clicar em `Publish`.

## Próximo passo para o usuário

No workflow `InvestmentAI - Agente de Desenvolvimento`, clique no `+` após `When clicking 'Execute workflow'`, pesquise `GitHub` e escolha a ação `Get a file` / `Get File` (leitura de arquivo). Não configure campos nem execute ainda. Se não aparecer essa ação, informar as opções disponíveis. A próxima configuração será definir repositório, caminho do arquivo e branch/ref depois de verificar as opções da interface.

## Separação dos workflows

### Workflow novo: `InvestmentAI - Agente de Desenvolvimento`
- Objetivo: agente que apoie o desenvolvimento do repositório.
- Execução inicial manual.
- Começar com leitura/inspeção, sem alterações remotas.
- Adicionar escrita, commits, PRs e automação de testes somente de forma progressiva, validada e com controles de aprovação.
- Não presumir que o agente pode modificar/mesclar código sem revisão.

### Workflow antigo: `Agente IA - Laboratório`
- Preservar intacto como referência e laboratório do monitoramento GitHub Actions.
- Não apagar nós, redesenhar, publicar ou ativar sem pedido explícito.
- As anotações técnicas mais abaixo sobre o workflow antigo continuam como histórico de referência, mas seus próximos passos não se sobrepõem ao objetivo atual do workflow novo.

## Segurança e critérios técnicos obrigatórios

- Não publicar/ativar nenhum workflow sem autorização explícita.
- Não criar issues reais durante testes.
- Não executar ações externas com efeito colateral sem explicar e obter confirmação explícita.
- Não habilitar operações financeiras reais.
- Manter a progressão do InvestmentAI: SIMULATION → PAPER → DEMO → LIVE; LIVE permanece bloqueado até validação quantitativa, operacional e de risco.
- Preservar os critérios de validação OOS/estatística/econômica. Não ajustar testes ou métricas apenas para fazer uma estratégia parecer aprovada.
- Usar a credencial GitHub já configurada no n8n, se estiver disponível; não pedir token novo sem necessidade.
- Ollama local disponível anteriormente em `http://127.0.0.1:11434`, modelo `llama3.2:1b`. Tratar como modelo experimental; não confiar nele isoladamente para decisões técnicas complexas.
- Uma etapa por vez; explicar exatamente o nó/campo e aguardar confirmação. Não presumir que o usuário fez algo que não confirmou.

## Regra permanente de continuidade

Sempre que houver mudança relevante de objetivo, estado do workflow, configuração, teste, decisão ou próximo passo, atualizar este arquivo no GitHub, na branch `docs/n8n-context-continuity`, no mesmo momento em que a mudança for registrada. O arquivo é a referência de continuidade para retomar o trabalho em qualquer novo chat. Informar ao usuário que a atualização foi feita e registrar o commit retornado. Não confundir esta branch/documentação de continuidade com a branch principal de desenvolvimento do InvestmentAI.

---

# Referência histórica — workflow antigo de monitoramento GitHub Actions

O conteúdo abaixo documenta o workflow antigo `Agente IA - Laboratório`. Ele deve ser mantido como referência; não seguir os próximos passos antigos se conflitarem com o estado atual acima.

## Como identificar o projeto correto em um novo chat

O usuário mantém mais de um trabalho relacionado ao GitHub. Antes de agir, identificar o projeto pelo nome explícito no pedido:
- **Agente de desenvolvimento n8n:** workflow novo `InvestmentAI - Agente de Desenvolvimento`, para ajudar a finalizar o projeto.
- **Monitor n8n / GitHub Actions:** workflow antigo `Agente IA - Laboratório`.
- **Desenvolvimento direto do InvestmentAI:** trabalho de engenharia do próprio repositório — código, testes, branches, pull requests, Actions, diagnóstico OOS, dashboard e demais funcionalidades.

Se o usuário disser apenas “continue”, consultar este documento e o contexto da conversa mais recente. Se ainda houver ambiguidade sobre qual projeto quer continuar, perguntar antes de executar qualquer ação.

## Ambiente

- Windows 11.
- n8n v2.43.6, em `http://localhost:5678`.
- Node.js portátil v24.22.0 em `C:\Users\tiago.ferreira\apps\node`.
- Dados do n8n: `C:\Users\tiago.ferreira\.n8n`.
- Inicialização: `C:\Users\tiago.ferreira\apps\Iniciar-n8n.cmd`.
- Existe uma credencial GitHub funcional no n8n. Não solicitar token novo.
- O n8n faz autosave; não instruir o usuário a clicar em Save.

## Workflow antigo existente

Nome: `Agente IA - Laboratório`.

- `When clicking "Execute workflow"` → `Edit Fields manual` → `Merge (1)` Input 1.
- `Schedule Trigger` (a cada 15 minutos) → `Edit Fields manual`.
- Ramo de consulta: `GitHub - Validar Repositório` → `List workflows` → `HTTP Request` → `Code in JavaScript`.
- `Code in JavaScript` alimenta `Merge (1)` Input 2, `Resumo - Indicadores Oficiais` e `IF`.
- Ramo determinístico: `Resumo - Indicadores Oficiais` → `Análise Determinística` → `Consolidar Análise`.
- Ramo experimental de IA: `Merge (1)` → `Preparar Prompt IA` → `llama - Analisar Projeto` → `Extrair Análise IA`. Não usar a IA como autoridade para determinar se houve falha.
- Condição esperada de `IF`: `{{ $json.total_falha }}` is greater than `0`.
- A saída True do `IF` foi conectada a `GitHub - Consultar Issues Abertas`. A saída False foi inicialmente deixada sem conexão; qualquer mudança temporária de conexão precisa ser conferida no canvas antes de avançar.

## Estado histórico dos dados do monitor

A consulta original retorna as 10 execuções mais recentes. O código calcula contagens e percentuais e cria `falhas` com os campos de workflow, branch, data, mensagem do commit e URL. Em teste, as 10 execuções retornadas estavam concluídas com sucesso:
- `total_retornado: 10`
- `total_concluido: 10`
- `total_sucesso: 10`
- `total_falha: 0`
- `total_em_andamento: 0`
- `percentual_sucesso: 100`
- `falhas: []`

Para deduplicação, é preferível incluir e utilizar o identificador numérico estável `run.id`, em vez de depender apenas de comparação textual de URL.

## Consulta de issues abertas

Nó: `GitHub - Consultar Issues Abertas`.
- Method: GET.
- URL: `https://api.github.com/repos/tiagodeazevedoferreira/InvestmentAI/issues?state=open&per_page=100`.
- Authentication: Predefined Credential Type.
- Credential Type: GitHub API (ou opção GitHub equivalente disponível na instalação).
- Selecionar a credencial GitHub existente.
- Em Options → Response, `Include Response Headers and Status` estava ativado.
- Em Settings, `Always Output Data` estava desativado.
- Teste real: HTTP 200 OK, `body: []`; API funcionou e não havia issues abertas no momento do teste. Não é um erro.
- A opção `Always Output Data` foi ativada temporariamente para diagnóstico e depois desativada novamente. Não a ativar globalmente para mascarar ausência de dados.

## Nó Normalizar Issues Abertas

Conectado após `GitHub - Consultar Issues Abertas`. Mode: `Run Once for All Items`.

Código registrado:
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

Teste confirmado: `total_issues_abertas: 0`, `issues: []`.

## Nó Identificar Falhas Já Alertadas — estado histórico

- Nó Code criado.
- Mode: `Run Once for All Items`.
- Conexão confirmada: `Normalizar Issues Abertas` → `Identificar Falhas Já Alertadas`.
- Ainda sem código conforme o último estado conhecido.

O próximo passo antigo era criar `Combinar Falhas e Issues` em modo Append. Esse passo ficou pendente e não deve ser retomado automaticamente porque a prioridade mudou para o workflow novo de agente de desenvolvimento.

## Padrão operacional

- Responder em português do Brasil.
- Dar uma única ação por vez e aguardar confirmação.
- Não presumir que uma etapa foi concluída sem confirmação.
- Ser explícito sobre os nomes exatos dos nós e suas conexões.
- Não alterar nem publicar workflows sem autorização explícita.
- Se a intenção for ambígua entre os três trabalhos acima, perguntar qual deles continuar.
