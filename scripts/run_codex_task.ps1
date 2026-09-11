[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TaskFile,

    [string]$OutputDirectory = ".runtime\codex"
)

$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Este script deve ser executado dentro do repositório InvestmentAI."
}

$taskPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $TaskFile))
if (-not (Test-Path -LiteralPath $taskPath -PathType Leaf)) {
    throw "Arquivo de tarefa não encontrado: $taskPath"
}

function Resolve-CodexExecutable {
    $command = Get-Command codex -ErrorAction SilentlyContinue
    if ($command -and $command.CommandType -eq "Application") {
        return $command.Source
    }

    $codexRoot = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"
    if (Test-Path -LiteralPath $codexRoot -PathType Container) {
        $candidate = Get-ChildItem -LiteralPath $codexRoot -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $exe = Join-Path $_.FullName "codex.exe"
                if (Test-Path -LiteralPath $exe -PathType Leaf) {
                    Get-Item -LiteralPath $exe
                }
            } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if ($candidate) {
            return $candidate.FullName
        }
    }

    throw "Codex CLI não encontrado. Nem 'codex' no PATH nem uma instalação do Codex App em '$codexRoot' foi localizada."
}

$codexPath = Resolve-CodexExecutable

$outputPath = Join-Path $repoRoot $OutputDirectory
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runDirectory = Join-Path $outputPath $stamp
New-Item -ItemType Directory -Force -Path $runDirectory | Out-Null

$schemaPath = Join-Path $repoRoot "docs\codex\handoff.schema.json"
if (-not (Test-Path -LiteralPath $schemaPath -PathType Leaf)) {
    throw "Schema de handoff não encontrado: $schemaPath"
}

$eventsPath = Join-Path $runDirectory "events.jsonl"
$resultPath = Join-Path $runDirectory "result.json"
$metadataPath = Join-Path $runDirectory "run.json"

$codexVersion = (& $codexPath --version 2>&1 | Out-String).Trim()
$metadata = [ordered]@{
    task_file = $taskPath
    started_at = (Get-Date).ToString("o")
    codex_command = $codexPath
    codex_version = $codexVersion
    repository = $repoRoot
    sandbox = "workspace-write"
    approval_policy = "on-request"
}
$metadata | ConvertTo-Json | Set-Content -LiteralPath $metadataPath -Encoding utf8

$prompt = @"
Você está executando uma tarefa do InvestmentAI recebida pelo protocolo ChatGPT ↔ Codex ↔ GitHub.

Leia e respeite integralmente o AGENTS.md e os documentos de arquitetura/decisão/status do projeto.

Regras desta execução:
- Execute a tarefa abaixo dentro do escopo solicitado.
- Inspecione o código existente antes de alterar arquivos.
- Faça as alterações necessárias, sem trabalho não relacionado.
- Execute os testes apropriados e registre resultados reais.
- Se encontrar ambiguidade de arquitetura, estado ou segurança, pare e reporte BLOCKED.
- Nunca execute operações financeiras, nunca chame mt5.order_send() e nunca crie uma nova ordem DEMO/LIVE.
- Não apague, redefina ou limpe .runtime/.
- Não use git reset --hard, git clean -fd ou ações destrutivas.
- Ao finalizar, responda SOMENTE com um objeto JSON compatível com o schema de handoff fornecido.

TAREFA:
$(Get-Content -LiteralPath $taskPath -Raw)
"@

$codexArgs = @(
    "exec",
    "--cd", $repoRoot,
    "--sandbox", "workspace-write",
    "--config", 'approval_policy="on-request"',
    "--json",
    "--output-schema", $schemaPath,
    "--output-last-message", $resultPath,
    "-"
)

Write-Host "InvestmentAI Codex Task Runner"
Write-Host "Task: $taskPath"
Write-Host "Run:  $runDirectory"
Write-Host "Codex: $codexVersion"
Write-Host "Path:  $codexPath"
Write-Host ""

$prompt | & $codexPath @codexArgs 2>&1 | Tee-Object -FilePath $eventsPath
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Error "Codex terminou com código $exitCode. Consulte: $eventsPath"
}

if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
    if ($exitCode -eq 0) {
        Write-Error "Codex terminou com sucesso, mas não produziu o handoff estruturado: $resultPath"
        $exitCode = 1
    }
} else {
    try {
        $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
        $required = @("task_id", "status", "changes", "tests", "results", "risks", "pending", "next_step", "commit")
        foreach ($field in $required) {
            if ($null -eq $result.PSObject.Properties[$field]) {
                throw "Campo obrigatório ausente no handoff: $field"
            }
        }
        if ($result.status -notin @("DONE", "BLOCKED", "PARTIAL")) {
            throw "Status de handoff inválido: $($result.status)"
        }
        Write-Host ""
        Write-Host "Handoff válido: $($result.status)"
        Write-Host "Resultado estruturado: $resultPath"
    } catch {
        Write-Error "Handoff inválido: $($_.Exception.Message)"
        $exitCode = 1
    }
}

exit $exitCode
