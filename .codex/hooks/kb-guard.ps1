$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$kbPattern = '(?:D-TRI|A-SUS|M-MOT|M-TRK|C-KTZ|C-FI|C-AJS|L-CT|L-SCN|L-LOW|L-3PT|COL-PRI|VS-TONE|D-DUO|D-DIA|D-POV|D-MOT|D-VLM|D-TRI-3|A-CHS|A-GEN|A-ACT|E-PCE)-\d+|\bKB:\s'
$chineseVideoPrompt = -join (0x89C6, 0x9891, 0x63D0, 0x793A, 0x8BCD | ForEach-Object { [char]$_ })

try {
    $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $toolInput = $payload.tool_input
    $filePath = [string]$toolInput.file_path
    $content = [string]$toolInput.content
    if ([string]::IsNullOrEmpty($content)) {
        $content = [string]$toolInput.new_string
    }

    $name = [System.IO.Path]::GetFileName($filePath)
    $upper = $name.ToUpperInvariant()
    $guarded = (
        $upper -eq "STORYBOARD.MD" -or
        $upper -eq "VIDEO_PROMPT.MD" -or
        $upper.StartsWith("STORYBOARD_") -or
        $name.Contains($chineseVideoPrompt)
    )

    if ($guarded -and $content -match $kbPattern) {
        @{
            continue = $false
            systemMessage = "KB leak: remove all internal KB rule IDs and retry."
            stopReason = "Storyboard or video prompt contains an internal rule ID; keep the natural-language design and remove the rule number."
        } | ConvertTo-Json -Compress
    }
    else {
        @{ continue = $true } | ConvertTo-Json -Compress
    }
}
catch {
    # Content parsing is fail-open; a missing hook script is handled by the caller.
    @{ continue = $true } | ConvertTo-Json -Compress
}
