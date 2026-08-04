# Compila paper.tex -> paper.pdf
#
# MiKTeX no quedó en el PATH del sistema en esta máquina, así que el script lo
# agrega para la sesión en vez de depender de que esté. Si lo instalaste en otro
# lado, cambiá $miktex.
#
# Dos pasadas: la primera resuelve el texto y escribe paper.aux, la segunda
# rellena los números de figura y las citas. Con una sola pasada las referencias
# salen como «??».
#
# Uso:  .\compilar.ps1

$ErrorActionPreference = "Stop"
$miktex = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64"

if (-not (Test-Path "$miktex\pdflatex.exe")) {
    throw "No encuentro pdflatex en $miktex. Corregí la variable `$miktex."
}
$env:PATH = "$miktex;$env:PATH"
Set-Location $PSScriptRoot

foreach ($pasada in 1, 2) {
    Write-Host "pasada $pasada de 2..."
    # MiKTeX escribe a stderr un aviso sobre actualizaciones aunque la
    # compilación salga bien. En PowerShell 5.1 cada línea de stderr de un
    # ejecutable nativo se envuelve en un ErrorRecord: con
    # $ErrorActionPreference = "Stop" aborta el script sin que haya fallado nada,
    # y con "Continue" igual ensucia la consola con NativeCommandError.
    #
    # Se invoca a través de cmd para que stderr nunca llegue al stream de errores
    # de PowerShell. La señal real de éxito es $LASTEXITCODE, no stderr: pdflatex
    # escribe avisos ahí de rutina.
    cmd /c "pdflatex -interaction=nonstopmode paper.tex > nul 2>&1"
    $codigo = $LASTEXITCODE

    if ($codigo -ne 0) {
        Write-Host "`nFalló en la pasada $pasada. Errores de LaTeX:" -ForegroundColor Red
        Select-String -Path paper.log -Pattern "^!" -Context 0, 3
        exit 1
    }
}

# Una referencia sin resolver sale como «??» en el PDF y no es un error de
# compilación: hay que buscarla explícitamente.
$sueltas = Select-String -Path paper.log -Pattern "Reference .* undefined|Citation .* undefined"
if ($sueltas) {
    Write-Host "`nReferencias sin resolver (van a salir como ?? en el PDF):" -ForegroundColor Yellow
    $sueltas | ForEach-Object { "  " + $_.Line.Trim() }
}

# Los auxiliares no aportan nada una vez que el PDF está hecho.
Remove-Item paper.aux, paper.log, paper.out, paper.toc -ErrorAction SilentlyContinue

$pdf = Get-Item paper.pdf
Write-Host ("`nListo: paper.pdf ({0:N1} MB)" -f ($pdf.Length / 1MB)) -ForegroundColor Green
Write-Host "Pesa lo que pesa porque los mapas son vectoriales y el de departamentos"
Write-Host "tiene más de 500 polígonos. Para una versión liviana, cambiá los"
Write-Host "\includegraphics de los dos mapas a la extensión .png."
