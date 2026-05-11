Set-Location -LiteralPath "$PSScriptRoot\frontend"
..\backend\venv\Scripts\python.exe -m http.server 3000 --bind 127.0.0.1
