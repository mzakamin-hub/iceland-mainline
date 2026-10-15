# SPDX-License-Identifier: GPL-2.0-or-later
#
# OnePlus Pad 4 dual boot (PLAN v4 Phase 4-DB): put U-Boot into the CURRENT slot's recovery partition.
# Use it once when setting up dual boot (only after the user has approved 4-DB), and again after every Android
# OTA (an OTA switches slots, and the new slot's recovery is the stock one again).
#
# This script WRITES to the tablet, and only to recovery_a or recovery_b (the current slot). It refuses anything
# else, never switches slots, checks the image's sha256 and needs a typed confirmation.
# Rollback: flash the saved stock recovery image for that slot (from the 151-partition backup) the same way.
#
#   powershell -ExecutionPolicy Bypass -File .\reflash-recovery.ps1 -Image u-boot-iceland.img -Sha256 <hash>
param(
    [Parameter(Mandatory = $true)][string]$Image,
    [Parameter(Mandatory = $true)][string]$Sha256
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$fb = @((Join-Path $here 'fastboot.exe'), (Join-Path (Get-Location) 'fastboot.exe')) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $fb) { $c = Get-Command fastboot -ErrorAction SilentlyContinue; if ($c) { $fb = $c.Source } }
if (-not $fb) { Write-Host 'fastboot.exe not found'; exit 1 }
function Var([string]$n) { $o = & $fb getvar $n 2>&1 | ForEach-Object { "$_" }; foreach ($l in $o) { if ($l -match "^${n}:\s*(.*)$") { return $Matches[1].Trim() } }; return '' }

if (-not (Test-Path $Image)) { Write-Host "image not found: $Image"; exit 1 }
$h = (Get-FileHash -Algorithm SHA256 $Image).Hash.ToLower()
if ($h -ne $Sha256.ToLower()) { Write-Host "sha256 mismatch: $h"; exit 1 }
$b = [IO.File]::ReadAllBytes($Image)
if ([Text.Encoding]::ASCII.GetString($b, 0, 8) -ne 'ANDROID!') { Write-Host 'not an Android boot image'; exit 1 }
if ($b.Length -gt 100MB) { Write-Host 'image larger than the 100 MiB recovery partition'; exit 1 }

Write-Host 'Tablet must be in the bootloader (Power + Volume Down).'
$devs = @(& $fb devices 2>&1 | Where-Object { "$_" -match '\sfastboot$' })
if ($devs.Count -ne 1) { Write-Host 'need exactly one fastboot device'; exit 1 }
if ((Var 'product') -ne 'canoe') { Write-Host 'not the OnePlus Pad 4 bootloader (product canoe)'; exit 1 }
if ((Var 'unlocked') -ne 'yes') { Write-Host 'bootloader locked'; exit 1 }
$slot = (Var 'current-slot')
if ($slot -notin @('a', 'b')) { Write-Host "unknown current slot '$slot'"; exit 1 }
$part = "recovery_$slot"

Write-Host ''
Write-Host "This writes U-Boot into $part (current slot $slot). Android keeps booting normally;"
Write-Host 'Power + Volume Up (or adb reboot recovery) will start U-Boot -> Fedora.'
Write-Host "Type FLASH $part to continue:"
if ((Read-Host) -ne "FLASH $part") { Write-Host 'not confirmed, nothing written'; exit 1 }
& $fb flash $part $Image
if ($LASTEXITCODE -ne 0) { Write-Host 'flash failed'; exit 1 }
Write-Host "done: $part now holds U-Boot. Reboot with: fastboot reboot"
