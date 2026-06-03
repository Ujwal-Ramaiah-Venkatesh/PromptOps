# Create PromptOps_Tracking.xlsx with all 8 sheets
Write-Host "Creating PromptOps_Tracking.xlsx..." -ForegroundColor Cyan

# Create Excel COM object
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

# Create new workbook
$workbook = $excel.Workbooks.Add()

# Remove default sheets except one
while ($workbook.Worksheets.Count -gt 1) {
    $workbook.Worksheets.Item(1).Delete()
}

# Define sheets
$sheets = @(
    @{Name="Daily Work Log"; File="tracking/01_daily_work_log.csv"},
    @{Name="Task Tracker"; File="tracking/02_task_tracker.csv"},
    @{Name="Deliverables"; File="tracking/03_deliverables_tracker.csv"},
    @{Name="Time Tracking"; File="tracking/04_time_tracking.csv"},
    @{Name="Issues & Blockers"; File="tracking/05_issues_blockers.csv"},
    @{Name="Weekly Summary"; File="tracking/06_weekly_summary.csv"},
    @{Name="Exit Criteria"; File="tracking/07_phase1_exit_criteria.csv"},
    @{Name="Team Roster"; File="tracking/08_team_roster.csv"}
)

$sheetIndex = 1

foreach ($sheet in $sheets) {
    Write-Host "Creating sheet: $($sheet.Name)" -ForegroundColor Yellow

    # Add new sheet or use existing
    if ($sheetIndex -eq 1) {
        $worksheet = $workbook.Worksheets.Item(1)
    } else {
        $worksheet = $workbook.Worksheets.Add([System.Reflection.Missing]::Value, $workbook.Worksheets.Item($workbook.Worksheets.Count))
    }

    $worksheet.Name = $sheet.Name

    # Read CSV file
    $csvPath = Join-Path (Get-Location) $sheet.File
    $csvData = Import-Csv -Path $csvPath

    # Get headers
    $headers = $csvData[0].PSObject.Properties.Name

    # Write headers
    $col = 1
    foreach ($header in $headers) {
        $worksheet.Cells.Item(1, $col) = $header
        $worksheet.Cells.Item(1, $col).Font.Bold = $true
        $worksheet.Cells.Item(1, $col).Interior.Color = 3430842  # Blue color
        $worksheet.Cells.Item(1, $col).Font.Color = 16777215    # White text
        $col++
    }

    # Write data
    $row = 2
    foreach ($record in $csvData) {
        $col = 1
        foreach ($header in $headers) {
            $worksheet.Cells.Item($row, $col) = $record.$header
            $col++
        }
        $row++
    }

    # Auto-fit columns
    $usedRange = $worksheet.UsedRange
    $usedRange.EntireColumn.AutoFit() | Out-Null

    # Freeze top row
    $worksheet.Application.ActiveWindow.SplitRow = 1
    $worksheet.Application.ActiveWindow.FreezePanes = $true

    $sheetIndex++
}

# Save workbook
$outputPath = Join-Path (Get-Location) "PromptOps_Tracking.xlsx"
$workbook.SaveAs($outputPath)
$workbook.Close()
$excel.Quit()

# Release COM objects
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($worksheet) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Host "`n✅ SUCCESS! Created: PromptOps_Tracking.xlsx" -ForegroundColor Green
Write-Host "Location: $outputPath" -ForegroundColor Green
Write-Host "Sheets: 8" -ForegroundColor Green
