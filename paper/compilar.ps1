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
    pdflatex -interaction=nonstopmode paper.tex | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFalló. Errores:" -ForegroundColor Red
        Select-String -Path paper.log -Pattern "^!" -Context 0, 3
        exit 1
    }
}

# Los auxiliares no aportan nada una vez que el PDF está hecho.
Remove-Item paper.aux, paper.log, paper.out, paper.toc -ErrorAction SilentlyContinue

$pdf = Get-Item paper.pdf
Write-Host ("`nListo: paper.pdf ({0:N1} MB)" -f ($pdf.Length / 1MB)) -ForegroundColor Green
Write-Host "Pesa lo que pesa porque los mapas son vectoriales y el de departamentos"
Write-Host "tiene más de 500 polígonos. Para una versión liviana, cambiá los"
Write-Host "\includegraphics de los dos mapas a la extensión .png."
