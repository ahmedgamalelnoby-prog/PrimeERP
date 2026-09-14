param(
    [string]$BaseUrl = "http://localhost:3000/api/v1",
    [string]$Login = $env:PRIMEERP_ADMIN_LOGIN,
    [string]$Password = $env:PRIMEERP_ADMIN_PASSWORD,
    [int]$TenantId = [int]$env:PRIMEERP_TENANT_ID
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Login) -or [string]::IsNullOrWhiteSpace($Password)) {
    throw "Set PRIMEERP_ADMIN_LOGIN and PRIMEERP_ADMIN_PASSWORD before running this smoke test."
}
if ($TenantId -le 0) {
    throw "Set PRIMEERP_TENANT_ID to the tenant that the platform admin should operate on."
}

function Assert-Ok([string]$Name, [scriptblock]$Action) {
    try {
        $value = & $Action
        Write-Host ("PASS  {0}" -f $Name) -ForegroundColor Green
        return $value
    } catch {
        Write-Host ("FAIL  {0}: {1}" -f $Name, $_.Exception.Message) -ForegroundColor Red
        throw
    }
}

$loginPayload = @{ login = $Login; password = $Password } | ConvertTo-Json
$login = Assert-Ok "Platform admin login" {
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/identity/login" -ContentType "application/json" -Body $loginPayload
}

$headers = @{ Authorization = "Bearer $($login.access_token)" }
$tenantHeaders = @{ Authorization = "Bearer $($login.access_token)"; "X-Tenant-ID" = "$TenantId" }

$me = Assert-Ok "Platform admin /me without context" {
    Invoke-RestMethod -Method Get -Uri "$BaseUrl/identity/me" -Headers $headers
}
if (-not $me.is_platform_admin) { throw "Login principal is not a platform administrator." }

$meContext = Assert-Ok "Platform admin /me with tenant context" {
    Invoke-RestMethod -Method Get -Uri "$BaseUrl/identity/me" -Headers $tenantHeaders
}
if ([int]$meContext.tenant_id -ne $TenantId) { throw "/me did not expose the selected tenant context." }

$tenant = Assert-Ok "Tenant details" {
    Invoke-RestMethod -Method Get -Uri "$BaseUrl/platform/tenants/$TenantId" -Headers $headers
}
if ([int]$tenant.id -ne $TenantId) { throw "Tenant detail returned an unexpected tenant." }

$subscriptions = Assert-Ok "Tenant subscriptions" {
    Invoke-RestMethod -Method Get -Uri "$BaseUrl/subscriptions/tenant/$TenantId" -Headers $headers
}
if ([int]$subscriptions.Count -lt 1) { throw "Tenant has no subscription." }

$companies = Assert-Ok "Tenant-scoped companies" {
    Invoke-RestMethod -Method Get -Uri "$BaseUrl/companies" -Headers $tenantHeaders
}
if ($null -eq $companies) { throw "Companies endpoint returned no response." }

Write-Host "Tenant context smoke test completed successfully for tenant $TenantId." -ForegroundColor Cyan
