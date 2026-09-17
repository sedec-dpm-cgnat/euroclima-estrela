param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputDocx,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]$OutputDir,
    [switch]$EmitPdf
)

# O LibreOffice está instalado neste caminho, mas não necessariamente no PATH
# de uma nova sessão do Codex. Centralizar a correção evita falhas intermitentes
# do renderizador DOCX.
$libreOfficeDir = 'C:\Program Files\LibreOffice\program'
$soffice = Join-Path $libreOfficeDir 'soffice.exe'
if (-not (Test-Path -LiteralPath $soffice)) {
    throw "LibreOffice não encontrado em $soffice"
}
$env:PATH = "$libreOfficeDir;" + $env:PATH

$python = 'C:\Users\cassi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$renderer = 'C:\Users\cassi\.codex\plugins\cache\openai-primary-runtime\documents\26.909.11814\skills\documents\render_docx.py'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python empacotado não encontrado em $python"
}
if (-not (Test-Path -LiteralPath $renderer)) {
    throw "Renderizador DOCX não encontrado em $renderer"
}

$arguments = @($renderer, $InputDocx, '--output_dir', $OutputDir)
if ($EmitPdf) { $arguments += '--emit_pdf' }
& $python @arguments
exit $LASTEXITCODE
