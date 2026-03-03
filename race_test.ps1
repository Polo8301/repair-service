# race_test.ps1 - Race Condition Test
# Run: .\race_test.ps1

Write-Host ""
Write-Host "RACE CONDITION TEST" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

$REQUEST_ID = Read-Host "Enter request ID (must be in 'assigned' status)"
$BASE_URL = "http://localhost:8001"

Write-Host ""
Write-Host "Request ID: $REQUEST_ID" -ForegroundColor Yellow
Write-Host "URL: $BASE_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting two simultaneous requests..." -ForegroundColor Green
Write-Host ""

$job1 = Start-Job -ScriptBlock {
    param($url, $id)
    try {
        $response = Invoke-RestMethod -Uri "$url/requests/$id/take" -Method POST -UseBasicParsing
        return @{ Status="SUCCESS"; Code=200; Message="Request taken" }
    } catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            return @{ Status="CONFLICT"; Code=409; Message="Already taken by another master" }
        } else {
            return @{ Status="ERROR"; Code=$_.Exception.Response.StatusCode; Message=$_.Exception.Message }
        }
    }
} -ArgumentList $BASE_URL, $REQUEST_ID

$job2 = Start-Job -ScriptBlock {
    param($url, $id)
    Start-Sleep -Milliseconds 100
    try {
        $response = Invoke-RestMethod -Uri "$url/requests/$id/take" -Method POST -UseBasicParsing
        return @{ Status="SUCCESS"; Code=200; Message="Request taken" }
    } catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            return @{ Status="CONFLICT"; Code=409; Message="Already taken by another master" }
        } else {
            return @{ Status="ERROR"; Code=$_.Exception.Response.StatusCode; Message=$_.Exception.Message }
        }
    }
} -ArgumentList $BASE_URL, $REQUEST_ID

$result1 = $job1 | Wait-Job | Receive-Job
$result2 = $job2 | Wait-Job | Receive-Job

Remove-Job $job1
Remove-Job $job2

Write-Host ""
Write-Host "RESULTS:" -ForegroundColor Cyan
Write-Host "========" -ForegroundColor Cyan
Write-Host ""
Write-Host "Request 1: $($result1.Status) - $($result1.Message)" -ForegroundColor $(if ($result1.Code -eq 200) { "Green" } else { "Yellow" })
Write-Host "Request 2: $($result2.Status) - $($result2.Message)" -ForegroundColor $(if ($result2.Code -eq 200) { "Green" } else { "Yellow" })
Write-Host ""

if (($result1.Code -eq 200 -and $result2.Code -eq 409) -or ($result1.Code -eq 409 -and $result2.Code -eq 200)) {
    Write-Host "SUCCESS! Race condition protection works!" -ForegroundColor Green
    Write-Host "One request succeeded, second got 409 Conflict" -ForegroundColor Green
} elseif ($result1.Code -eq 200 -and $result2.Code -eq 200) {
    Write-Host "ERROR! Both requests succeeded - race condition NOT protected!" -ForegroundColor Red
} else {
    Write-Host "UNEXPECTED RESULT" -ForegroundColor Yellow
    Write-Host "Check that request exists and is in 'assigned' status" -ForegroundColor Yellow
}

Write-Host ""