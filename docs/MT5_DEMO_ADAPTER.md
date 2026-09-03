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
- `reconciliation_snapshot(date_from, date_to)` — snapshot externo no formato consumido pelo reconciliador operacional.
- `submit(intent)` — executa somente após validação da conta demo, permissão de negociação, símbolo, `order_check` e `order_send` bem-sucedidos.

`cancel()` permanece bloqueado até que a semântica específica de cancelamento de ordens pendentes do ambiente Doto/MT5 seja validada.

## Validação DEMO end-to-end

O script `scripts/validate_mt5_demo.py` realiza uma conexão **somente de leitura** para capturar conta, posições, ordens abertas e execuções. Opcionalmente recebe um snapshot interno JSON e executa `OperationalReconciler` contra o estado observado.

Variáveis necessárias:

```text
DOTO_MT5_SERVER=<servidor DEMO>
DOTO_MT5_LOGIN=<login DEMO>
DOTO_MT5_PASSWORD=<senha DEMO>
```

Exemplo:

```bash
PYTHONPATH=backend python scripts/validate_mt5_demo.py
PYTHONPATH=backend python scripts/validate_mt5_demo.py --internal-snapshot internal_snapshot.json
```

O script nunca recebe senha por argumento de linha de comando e recusa um servidor cujo nome não identifique DEMO. A validação com `--internal-snapshot` retorna código diferente de zero quando a reconciliação estiver `blocked`.

## Segurança

Este componente não habilita live trading. Não há credenciais ou endpoint live no código. O adapter também não altera o sinal, o modelo, o sizing ou o risk gate.

O harness de validação é read-only: não envia nem cancela ordens. A próxima etapa operacional é executar essa validação em uma conta Doto/MT5 DEMO real, registrar o snapshot e validar as diferenças encontradas antes de conectar qualquer fluxo automático de autorização.
