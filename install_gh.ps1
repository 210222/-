$repo = 'cli/cli'
$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/cli/cli/releases/latest'
$msi = $release.assets | Where-Object { $_.name -match 'gh_.*_windows_amd64\.msi$' } | Select-Object -First 1
if (-not $msi) {
    Write-Error 'MSI asset not found in latest release'
    exit 1
}
$url = $msi.browser_download_url
$file = Join-Path $env:TEMP $msi.name
Write-Host "Downloading $($msi.name) ..."
Invoke-WebRequest -Uri $url -OutFile $file
Write-Host 'Installing ...'
Start-Process msiexec.exe -ArgumentList "/i `"$file`" /quiet /norestart" -Wait
Write-Host 'Done. Cleaning up.'
Remove-Item $file -Force
