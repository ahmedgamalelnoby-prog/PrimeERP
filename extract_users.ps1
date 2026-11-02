param(
    [string]$File = ".\users_backup_check.sql",
    [string]$OutputCsv
)

$lines = Get-Content $File

$header = $lines |
    Where-Object { $_ -match '^COPY public\.users \(' -and $_ -notmatch '^\s*--' } |
    Select-Object -First 1

if (-not $header) {
    Write-Host "COPY HEADER NOT FOUND" -ForegroundColor Red
    return
}

$columns = [regex]::Match(
    $header,
    '^COPY public\.users \((.*)\) FROM stdin;$'
).Groups[1].Value -split ', '

$wanted = @(
    'id','tenant_id','username','email','role_id',
    'is_active','is_superuser','is_platform_admin','is_deleted','updated_at'
)

$indexes = @{}
foreach ($name in $wanted) {
    $indexes[$name] = [array]::IndexOf($columns, $name)
}

$missing = $indexes.GetEnumerator() | Where-Object { $_.Value -lt 0 }
if ($missing) {
    Write-Host "أعمدة مفقودة في الهيدر:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Yellow }
}

function ConvertFrom-PgCopyField {
    param([string]$Raw)
    if ($Raw -eq '\N') { return $null }
    return ($Raw -replace '\\\\', '\' -replace '\\t', "`t" -replace '\\n', "`n" -replace '\\r', "`r")
}

$start = [array]::IndexOf($lines, $header) + 1
$records = [System.Collections.Generic.List[object]]::new()

for ($i = $start; $i -lt $lines.Count -and $lines[$i] -ne '\.'; $i++) {
    $fields = $lines[$i] -split "`t"
    $record = [ordered]@{}

    foreach ($name in $wanted) {
        $idx = $indexes[$name]
        if ($idx -ge 0 -and $idx -lt $fields.Count) {
            $record[$name] = ConvertFrom-PgCopyField $fields[$idx]
        } else {
            $record[$name] = $null
        }
    }

    $records.Add([PSCustomObject]$record)
}

$deduped = $records |
    Sort-Object id, { if ($_.updated_at) { [datetime]$_.updated_at } else { [datetime]::MinValue } } |
    Group-Object id |
    ForEach-Object { $_.Group | Select-Object -Last 1 } |
    Sort-Object id

if ($OutputCsv) {
    $deduped | Export-Csv -Path $OutputCsv -NoTypeInformation -Encoding UTF8
    Write-Host "تم الحفظ في $OutputCsv" -ForegroundColor Green
} else {
    $deduped | Format-Table -AutoSize
}
