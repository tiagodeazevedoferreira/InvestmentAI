# Doto/MT5 Demo Adapter

## Objetivo

O `MT5DemoBroker` fornece a primeira fronteira de integração com uma conta MetaTrader 5 de demonstração, mantendo o domínio InvestmentAI independente do SDK do MT5.

A implementação é deliberadamente **demo-only**. Ela recusa servidores cujo nome não contenha `demo` e também recusa modos de negociação explicitamente identificados como `real`/`live`.

## Arquitetura

```text
InvestmentAI
    |
    +-- OrderIntent
    |
    +-- MT5DemoBroker
             |
             +-- MT5Gateway (injeção/teste)
             |
             +-- MetaTrader5DemoGateway (SDK lazy)
             |
             +-- Doto MT5 Demo Terminal
```

O SDK `MetaTrader5` é carregado somente quando o gateway concreto é utilizado. Assim, os testes de CI não dependem do terminal MT5 nem de credenciais.

## Operações disponíveis

- `account()` — snapshot normalizado de login, servidor, saldo, equity, moeda e permissão de negociação.
- `positions()` — posições abertas normalizadas.
- `open_orders()` — ordens pendentes normalizadas.
- `executions(date_from, date_to)` — negócios executados normalizados.
- `submit(intent)` — executa somente após validação da conta demo, permissão de negociação, símbolo, `order_check` e `order_send` bem-sucedidos.

`cancel()` permanece bloqueado até que a semântica específica de cancelamento de ordens pendentes do ambiente Doto/MT5 seja validada.

## Segurança

Este componente não habilita live trading. Não há credenciais, servidor ou endpoint live no código. O adapter também não altera o sinal, o modelo, o sizing ou o risk gate.

A próxima etapa é conectar esse adapter a um fluxo **end-to-end de demo**, incluindo reconciliação de conta, posições, ordens e execuções contra o estado interno, com kill switch ativo na fronteira de autorização.
