# MetaTrader 5 — workstation context

> Persistent operational reference for future InvestmentAI guidance. Source: user-provided MT5 screenshot analyzed on 2026-09-09.
>
> **Security rule:** this document intentionally excludes the account identifier shown in the window title and any credentials. Do not store passwords, access tokens, or full account identifiers in the public repository.

## Confirmed visual context

- Platform: MetaTrader 5.
- Interface language: Portuguese (Brazilian Portuguese UI labels are visible).
- Window title format visible: `DOTOGlobal-Real — Netting` preceded by an account identifier. The full identifier is intentionally not persisted here.
- The user has explicitly confirmed in the working conversation that the account shown is a **DEMO account**, despite the broker server display name containing `Real`. Future guidance must not infer account type from the server-name text alone.
- Account mode displayed: `Netting`.
- Main window contains the following visible areas:
  - `Observação do Mercado` (Market Watch) on the left.
  - `Navegador` (Navigator) below it.
  - Four chart panels in the main workspace.
- Visible Navigator sections:
  - MetaTrader 5
  - Contas
  - Indicadores
  - Consultor expert
  - Scripts
  - Serviços
  - Mercado
- Market Watch tabs visible at the bottom:
  - Ativos
  - Detalhes
  - Negociação
  - Ticks
- Market Watch visibly contains these instruments:
  - EURUSD
  - GBPUSD
  - USDCHF
  - USDJPY
  - USDCNH
  - AUDUSD
  - NZDUSD
  - USDCAD
  - USDSEK
  - SP500m
  - AMD
  - MSFT
  - INTC
  - NVDA
- The Market Watch counter visible near the bottom right is `14 / 10157`.
- The visible Market Watch columns include `Ativo`, `Bid`, `Venda` and a truncated change column (`Mudan...`).

## Visible chart workspace

Four H1 charts are open:

1. `EURUSD,H1`
   - Chart title identifies Euro vs US Dollar.
   - A red moving-average line is visible.
   - Visible historical x-axis spans approximately 9–21 Aug 2024.

2. `GBPUSD,H1`
   - Chart title identifies Pound Sterling vs US Dollar.
   - CCI indicator is visible below the price chart.
   - Indicator label/value visible: `CCI(14) 12.83`.
   - Visible historical x-axis spans approximately 15–21 Aug 2024.

3. `USDCHF,H1`
   - Chart title identifies US Dollar vs Swiss Franc.
   - A red moving-average line is visible.
   - Visible historical x-axis spans approximately 9–21 Aug 2024.

4. `USDJPY,H1`
   - Chart title identifies US Dollar vs Yen.
   - MACD indicator is visible below the price chart.
   - Indicator label/value visible: `MACD(12,26,9) -0.3582 -0.3739`.
   - Visible historical x-axis spans approximately 9–21 Aug 2024.

## Toolbar / UI context relevant to instructions

- Standard MT5 menus are visible: `Arquivo`, `Exibir`, `Inserir`, `Gráficos`, `Ferramentas`, `Janela`, `Ajuda`.
- The toolbar includes common chart/trading controls.
- `AlgoTrading` is visible on the toolbar.
- `Nova Ordem` is visible and appears disabled/greyed in the captured state.
- Timeframe buttons visible include: M1, M5, M15, M30, H1, H4, D1, W1, MN.
- H1 is selected in the captured state.
- The active chart tab at the bottom is `EURUSD,H1`; other visible chart tabs are `USDCHF,H1`, `GBPUSD,H1`, and `USDJPY,H1`.

## Operational interpretation for InvestmentAI

- Treat the screenshot as a **workstation/UI baseline**, not as proof of the current live state. Prices, indicator values, chart dates, connection state, and enabled/disabled controls can change after the screenshot.
- When guiding the user through MT5, use the Portuguese labels and the visible layout above as the default navigation context.
- The broker/server display string containing `Real` must **not** by itself be used to classify the account as real. Account type must be validated from MT5 account metadata / trade mode and the previously established DEMO context.
- The InvestmentAI integration remains DEMO-only. Never instruct the user to test the InvestmentAI broker path against a real-money account.
- For any future step involving a specific MT5 control whose current state is not established by this baseline, request a new screenshot rather than assuming the UI has remained unchanged.

## Security / persistence boundary

This file is deliberately a sanitized operational memory. The original screenshot contains an account identifier in the window title; that identifier is not copied into the public repository. Credentials must never be committed to GitHub. Environment variables or local configuration should be used for connection secrets.
