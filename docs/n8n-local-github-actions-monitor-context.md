# Contexto de continuidade — n8n local / GitHub Actions

Atualizado em: 2026-10-16

## Objetivo
Workflow local do n8n para monitorar as execuções de GitHub Actions do repositório `tiagodeazevedoferreira/InvestmentAI`, detectar falhas confirmadas pelo ramo determinístico e preparar alertas em Issues sem duplicidade.

**Importante:** este arquivo registra o estado do trabalho local; ele não contém o workflow exportado do n8n. O workflow ainda não foi ativado/publicado e nenhuma issue real foi criada durante os testes.

## Ambiente
- Windows 11.
- n8n v2.43.6 em `http://localhost:5678`.
- Node portable v24.22.0 em `C:\Users\tiago.ferreira\apps\node`.
- Dados n8n em `C:\Users\tiago.ferreira\.n8n`.
- Inicializador: `C:\Users\tiago.ferreira\apps\Iniciar-n8n.cmd`.
- Credencial GitHub já existente no n8n; não solicitar novo token.
- Workflow: `Agente IA - Laboratório`.

## Arquitetura e validações já realizadas
- Consulta GitHub Actions: `GET https://api.github.com/repos/tiagodeazevedoferreira/InvestmentAI/actions/runs?per_page=10`.
- A última amostra consultada tinha 10 execuções concluídas, 10 sucessos e nenhuma falha.
- Ramo determinístico é a fonte de verdade; ramo Ollama/IA é experimental e não autoritativo.
- Consulta issues abertas: `GET https://api.github.com/repos/tiagodeazevedoferreira/InvestmentAI/issues?state=open&per_page=100`; o teste retornou HTTP 200 e lista vazia.
- `Normalizar Issues Abertas` normaliza os dados para `{ total_issues_abertas, issues }`.
- `Combinar Falhas e Issues` usa modo Append.
- `Identificar Falhas Já Alertadas` compara URL da execução com título/corpo/URL de issues abertas; teste sintético validou os casos já alertada e falha nova.
- `IF` avalia `{{ $json.total_falhas_novas }}` maior que `0`; os testes sintéticos de verdadeiro/falso passaram.
- `Preparar Alerta GitHub` cria título e corpo de alerta; teste sintético passou.
- `Separar Alertas para Issues` transforma o array de alertas em itens independentes; teste com dois alertas sintéticos passou.
- `IF - Autorizar Criação Real` avalia `{{ $json.autorizar_criacao === true }}`; teste com `false` confirmou que o item deve seguir pela saída false.
- Nenhuma issue real foi criada; os testes utilizaram URLs e dados fictícios.

## Conexões esperadas do trecho de alertas
`Identificar Falhas Já Alertadas` → `IF` (falhas novas > 0) → saída true → `Preparar Alerta GitHub` → `Separar Alertas para Issues` → `IF - Autorizar Criação Real` → saída true → `GitHub - Criar Issue de Alerta`.

A saída false do primeiro IF está desconectada. A saída false do IF de autorização está desconectada. Não há nós de teste temporário que devam permanecer no canvas.

## Configuração do nó HTTP de criação
Nó: `GitHub - Criar Issue de Alerta`. Deve permanecer desconectado até concluir revisão/testes e não deve ser executado sem autorização explícita.

- Method: POST
- URL: `https://api.github.com/repos/tiagodeazevedoferreira/InvestmentAI/issues`
- Authentication: Predefined Credential Type, usando a credencial GitHub existente
- Send Body: ON
- Body Content Type: JSON
- Specify Body: Using JSON
- Body (Expression):
  ```javascript
  ={{ { title: $json.titulo, body: $json.corpo } }}
  ```
- Em Options → Add option → Response, o usuário encontrou a opção Response, mas **ainda não concluiu** a ativação de `Include Response Headers and Status`. Response Format deve ser JSON se essa opção estiver disponível.

## Estado atual e próximo passo
O usuário precisou interromper antes de concluir o passo 28. A próxima ação é abrir `GitHub - Criar Issue de Alerta` → Options → Response e ativar `Include Response Headers and Status`, se disponível. Não executar o nó HTTP.

Depois:
1. Revisar todos os campos do HTTP Request e a expressão do corpo.
2. Confirmar conexões e manter `autorizar_criacao: false` no código de `Separar Alertas para Issues`.
3. Não executar o workflow completo, não ativar/publicar o workflow e não criar issues reais sem consentimento explícito.
4. Antes de liberar alertas reais, revisar a estrutura real de `falhas_confirmadas` em cenário controlado e confirmar que o identificador/URL estável de cada execução está preservado. Até agora não houve falha real para validar esse caminho.

## Observações
- O nó `Separar Alertas para Issues` deve continuar em `Run Once for All Items` e adicionar `autorizar_criacao: false` a cada item.
- A trava é uma proteção adicional; a autorização falsa por padrão é intencional neste estágio.
- Não confundir este projeto de n8n local com o desenvolvimento do código do repositório InvestmentAI.
