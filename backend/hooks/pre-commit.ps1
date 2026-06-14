Param()
try {
    $repo = git rev-parse --show-toplevel 2>$null
    if (-not $repo) {
        Write-Host "Not a git repository; skipping AI pre-commit review."
        exit 0
    }

    $url = 'http://127.0.0.1:8765/analyze/hook'
    $body = @{ repoPath = $repo } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType 'application/json' -ErrorAction Stop

    $risk = $response.riskScore
    if ($null -eq $risk) { $risk = 0 }
    $threshold = 8.0
    if ([double]$risk -ge $threshold) {
        Write-Host "AI pre-commit review blocked commit: riskScore=$risk >= $threshold"
        exit 1
    }
    else {
        Write-Host "AI pre-commit review passed: riskScore=$risk < $threshold"
        exit 0
    }
} catch {
    Write-Host "AI pre-commit review error: $_"
    exit 1
}
