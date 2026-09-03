# DEMO Authorization Gate

## Objetivo

O `DemoAuthorizationGate` é a fronteira explícita de autorização operacional para o ambiente DEMO. Ele decide se uma ordem pode prosseguir até o broker, mas **não envia ordens**.

## Condições obrigatórias

A autorização somente é concedida quando todas as condições são verdadeiras:

1. `environment` é exatamente `demo`;
2. o `OperationalKillSwitch` está liberado;
3. existe evidência externa suficiente para reconciliação;
4. a evidência não está stale;
5. caixa/saldo está dentro da tolerância;
6. posições coincidem;
7. ordens abertas coincidem;
8. execuções coincidem nos dois sentidos.

Qualquer divergência resulta em `allowed=False` e o fluxo deve parar.

## Fluxo

```text
Signal
  |
RiskGate / sizing
  |
OrderIntent
  |
DEMO Authorization Gate
  |---- kill switch
  |---- reconciliation
  |---- environment check
  |
MT5DemoBroker
  |
order_check
  |
order_send
  |
new external snapshot
  |
reconciliation
```

A documentação do MetaTrader confirma que `order_check` valida a solicitação, mas uma checagem bem-sucedida não garante que a operação será executada. Por isso, a reconciliação posterior continua obrigatória. citehttps://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_pyhttps://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py

## Limites

- Não existe caminho live.
- O gate não promove política, modelo ou estratégia.
- O gate não altera sinal, risco ou sizing.
- O kill switch não envia/cancela ordens.
- A autorização é fail-closed.

## Próxima validação

Depois dos testes unitários, o próximo passo é executar a sequência em uma conta Doto/MT5 DEMO controlada, inicialmente com operações manuais e snapshots read-only, antes de qualquer scheduler automático.
