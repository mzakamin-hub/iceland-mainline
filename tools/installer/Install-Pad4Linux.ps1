#Requires -Version 5.1
# SPDX-License-Identifier: GPL-2.0-or-later
<#
.SYNOPSIS
    Guided install of Fedora 44 (iceland-mainline) on a OnePlus Pad 4 ("iceland", OPD2514): download, read-only
    backup, and exactly the two partition writes the project owner made on 13 Oct 2026, each one confirmed by you.

.DESCRIPTION
    Modelled on the owner's real procedure (iceland-mainline INSTALL-GUIDE, B149 edition, and the install record of
    13-14 Oct 2026):
      Preflight  PC checks: PowerShell, adb / fastboot (Google platform-tools), the release manifest, free disk space.
      Download   every file of the release manifest (URL + size + SHA-256), resumable, verified after download.
      Backup     READ ONLY. From Android (LineageOS on slot b, Developer options > "Rooted debugging" ON): the
                 identity, battery and lock state, then a copy of boot_b and the rest of the boot set of both slots
                 + misc (optionally every partition except userdata, -FullBackup), each checked by SHA-256 on the
                 tablet and on the PC; then the slot flags in the boot loader. The copy of boot_b is the undo file of
                 write 2. Recorded in a local backup-manifest.json that never leaves this PC.
      Flash      write 1: fastboot flash userdata <install image>    (erases ALL Android data)
                 three tethered RAM boots of U-Boot (fastboot boot, nothing written) to Fedora's desktop
                 write 2: fastboot flash boot_b <U-Boot with AVB footer>
                 Each write: a screen with partition, file, size and SHA-256, and you type the partition name.
      VerifySlot read the slot flags in the boot loader after Fedora's first boots (the slot-counter stop rule).
      UndoBootB  put the saved boot_b back (the documented undo of write 2).
      Inspect    print what this script reads from a local image file (boot header, AVB footer); PC only.

    DRY RUN BY DEFAULT: without -Execute nothing is downloaded and adb / fastboot are never started; every command
    is printed instead. Everything is logged to <WorkDir>\logs\.

    This script NEVER: unlocks or locks the boot loader (no "fastboot flashing ..."), erases or formats anything
    ("fastboot erase / format / -w"), switches slots ("set_active"), runs "flashall" / "update", writes any partition
    other than userdata and boot_b, or asks for the serial number. Every adb / fastboot command goes through a
    whitelist; anything else is refused before it is sent.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json
    (dry run of everything)

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Backup -Execute
#>
[CmdletBinding()]
param(
    [string]$Manifest = '',
    [ValidateSet('All', 'Preflight', 'Download', 'Backup', 'Flash', 'VerifySlot', 'UndoBootB', 'Inspect')]
    [string]$Phase = 'All',
    [switch]$Execute,
    [switch]$DryRun,
    [string]$WorkDir = '',
    [string]$PlatformTools = '',
    [string]$BackupDir = '',
    [switch]$FullBackup,
    [string]$Python = '',
    [string]$File = '',
    [int]$MinBatteryPercent = 60,
    [int]$MinBatteryMv = 3800
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

# ---------------------------------------------------------------------------------------------------------------------
# Fixed facts of the install procedure (INSTALL-GUIDE B149 edition, 13-14 Oct 2026). Every device value is
# re-read from the tablet before it is relied on.
$ScriptVersion   = '1.0 (2026-10-15)'
$ExpectedProduct = 'canoe'              # the tablet's own boot loader (ABL) fastboot
$UBootProduct    = 'oneplus-iceland'    # U-Boot's own fastboot: never written through
$WritableParts   = @('userdata', 'boot_b')
$BootBBytes      = 100663296            # 0x6000000
$FooterKeySha1   = '2597c218aae470a130f61162feaae70afd97f011'   # AOSP testkey_rsa4096 = the key LineageOS's vbmeta_b chains boot with
$RetryStop       = 3                    # INSTALL-GUIDE C0.6 / Part D: never boot slot b again at a retry count of 3 or less
$SparseMagic     = [Convert]::ToUInt32('ED26FF3A', 16)
$DataLossPhrase  = 'I understand my Android data is erased'
# Part A step 6 (parta-read.ps1): slot b's boot set, slot a's boot set, misc
$ReadParts = @('boot_b', 'vbmeta_b', 'init_boot_b', 'vendor_boot_b', 'dtbo_b', 'recovery_b', 'vbmeta_system_b',
               'vbmeta_vendor_b', 'boot_a', 'vbmeta_a', 'init_boot_a', 'vendor_boot_a', 'dtbo_a', 'misc')
$AllowedProps = @('ro.product.model', 'ro.product.device', 'ro.product.name', 'ro.build.fingerprint', 'ro.build.type',
                  'ro.boot.slot_suffix', 'ro.boot.verifiedbootstate', 'ro.boot.flash.locked',
                  'ro.boot.vbmeta.device_state', 'ro.gsid.image_running', 'service.adb.root', 'ro.build.version.release')
# the unit's own Bluetooth address: read ONCE, read only, in the backup phase - the property LineageOS's
# Bluetooth HAL keeps it in; saved as bdaddr.txt next to the backup
# manifest and handed to Fedora's first login as "sudo iceland-provision --bdaddr ..."; masked in every log line
$BdAddrProp = 'persist.vendor.service.bdroid.bdaddr'
$BdPlaceholders = @('00:00:00:00:00:00', 'FF:FF:FF:FF:FF:FF', 'AD:5A:00:00:00:25', '25:00:00:00:5A:AD', '00:00:00:00:5A:AD', 'AD:5A:00:00:00:00')
$AllowedVars = @('product', 'current-slot', 'unlocked', 'secure', 'slot-count', 'is-userspace', 'battery-voltage',
                 'max-download-size', 'partition-size:userdata', 'partition-size:boot_b',
                 'slot-successful:a', 'slot-successful:b', 'slot-unbootable:a', 'slot-unbootable:b',
                 'slot-retry-count:a', 'slot-retry-count:b')

if ($Execute -and $DryRun) { Write-Host 'Give either -Execute or -DryRun, not both.' -ForegroundColor Red; exit 1 }
$Live = [bool]$Execute
if (-not $WorkDir) { $WorkDir = Join-Path $env:USERPROFILE 'Pad4Linux' }
if (-not $Manifest -and $Phase -ne 'Inspect') { $Manifest = Join-Path $PSScriptRoot 'release-manifest.json' }
$DlDir      = Join-Path $WorkDir 'downloads'
$BackupRoot = Join-Path $WorkDir 'backups'
$ToolsDir   = Join-Path $WorkDir 'tools'
$LogDir     = Join-Path $WorkDir 'logs'

# ---------------------------------------------------------------------------------------------------------------------
# Output, log, masking
$script:stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
$script:logFile = $null
try {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $script:logFile = Join-Path $LogDir ('install-{0}-{1}-{2}.log' -f $script:stamp, $Phase.ToLower(), $(if ($Live) { 'execute' } else { 'dryrun' }))
} catch { $script:logFile = $null }

function Hide-Serial([string]$s) {
    if ($null -eq $s) { return '' }
    $s = [regex]::Replace($s, '(?m)^(\s*)\S+(\s+)(fastboot|device|recovery|unauthorized|sideload|bootloader|offline|no permissions.*)\s*$', '${1}<serial>${2}${3}')
    $s = [regex]::Replace($s, '(?im)^(\(bootloader\)\s*)?(serialno|serial)\s*:\s*\S+', '${1}${2}: <masked>')
    # MAC / Bluetooth addresses never reach the screen log or the log file (the hint line is written with Write-Host only)
    $s = [regex]::Replace($s, '(?i)(?<![0-9a-f:])([0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f:])', 'XX:XX:XX:XX:XX:XX')
    return $s
}
function Write-Log([string]$m, [string]$color = '') {
    $line = Hide-Serial $m
    if ($color) { Write-Host $line -ForegroundColor $color } else { Write-Host $line }
    if ($script:logFile) { try { Add-Content -LiteralPath $script:logFile -Value ('[{0}] {1}' -f (Get-Date).ToString('HH:mm:ss'), $line) } catch {} }
}
function Write-Step([string]$m) { Write-Log ''; Write-Log "==> $m" 'Cyan' }
function Write-Ok([string]$m)   { Write-Log "  [OK]   $m" 'Green' }
function Write-Warn([string]$m) { Write-Log "  [WARN] $m" 'Yellow' }
function Write-Dry([string]$m)  { Write-Log "  [DRY RUN] $m" 'Magenta' }
function Stop-Run([string]$m, [int]$code = 1) {
    Write-Log "STOP: $m" 'Red'
    Write-Log 'Nothing further was sent to the tablet by this run.' 'Red'
    if ($script:logFile) { Write-Host "Log: $script:logFile" }
    exit $code
}
function Read-Line {
    if ([Console]::IsInputRedirected) { $l = [Console]::In.ReadLine(); if ($null -eq $l) { return '' } }
    else { $l = Read-Host '>' }
    return ([string]$l).Trim([char]0xFEFF, ' ', "`t")
}
function Confirm-Typed([string]$what, [string]$phrase) {
    if (-not $Live) { Write-Dry ("would ask: {0} -> the user must type exactly: {1}" -f $what, $phrase); return }
    Write-Log ''
    Write-Log $what 'Yellow'
    Write-Log "Type exactly:  $phrase" 'Yellow'
    $a = Read-Line
    if ($a -cne $phrase) { Stop-Run "confirmation did not match (typed '$a', expected '$phrase'). Cancelled before this step." }
    Write-Log "  confirmed: $phrase"
}
function Confirm-YesNo([string]$question) {
    if (-not $Live) { Write-Dry "would ask: $question (yes / no)"; return $true }
    Write-Log ''
    Write-Log "$question  (type yes or no)" 'Yellow'
    $a = Read-Line
    Write-Log "  answer: $a"
    return ($a -ceq 'yes')
}
function Wait-Enter([string]$what) {
    if (-not $Live) { Write-Dry "would wait for Enter: $what"; return }
    Write-Log $what 'Yellow'
    [void](Read-Line)
}

# ---------------------------------------------------------------------------------------------------------------------
# Small helpers: files, hashes, bytes
function Get-Field($o, [string]$name) {
    if ($null -eq $o) { return $null }
    $p = $o.PSObject.Properties[$name]
    if ($null -eq $p) { return $null }
    return $p.Value
}
function Get-Long($v) { $r = 0L; if ($null -ne $v -and [long]::TryParse([string]$v, [ref]$r)) { return $r }; return 0L }
function Get-Sha([string]$p) { return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
function ConvertTo-Hex([byte[]]$b) { if ($null -eq $b) { return '' }; return (-join ($b | ForEach-Object { $_.ToString('x2') })) }
function ConvertFrom-Hex([string]$h) {
    $out = New-Object byte[] ($h.Length / 2)
    for ($i = 0; $i -lt $out.Length; $i++) { $out[$i] = [Convert]::ToByte($h.Substring(2 * $i, 2), 16) }
    return , $out
}
function Read-Bytes([string]$p, [long]$offset, [int]$n) {
    $fs = [IO.File]::OpenRead($p)
    try {
        if ($offset -lt 0 -or $offset + $n -gt $fs.Length) { return $null }
        [void]$fs.Seek($offset, 'Begin')
        $b = New-Object byte[] $n
        $got = 0
        while ($got -lt $n) { $r = $fs.Read($b, $got, $n - $got); if ($r -le 0) { break }; $got += $r }
        if ($got -ne $n) { return $null }
        return , $b
    } finally { $fs.Close() }
}
function Get-U32BE([byte[]]$b, [int]$o) { $t = New-Object byte[] 4; [Array]::Copy($b, $o, $t, 0, 4); [Array]::Reverse($t); return [BitConverter]::ToUInt32($t, 0) }
function Get-U64BE([byte[]]$b, [int]$o) { $t = New-Object byte[] 8; [Array]::Copy($b, $o, $t, 0, 8); [Array]::Reverse($t); return [BitConverter]::ToUInt64($t, 0) }
function Get-Ascii([byte[]]$b, [int]$o, [int]$n) { return [Text.Encoding]::ASCII.GetString($b, $o, $n).TrimEnd([char]0) }
function Format-Size([long]$n) { return ('{0:N0} bytes ({1:N2} GiB)' -f $n, ($n / 1GB)) }
function Get-FreeBytes([string]$path) {
    $root = [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($path))
    try { return [long](New-Object IO.DriveInfo($root)).AvailableFreeSpace } catch { return -1 }
}

# ---------------------------------------------------------------------------------------------------------------------
# Release manifest
function Test-Placeholder($v) {
    if ($null -eq $v) { return $true }
    $s = [string]$v
    return ($s -eq '' -or $s -match 'PLACEHOLDER')
}
function Test-SafeUrl([string]$url, [string[]]$hosts = @()) {
    # returns $null when the URL may be fetched, else the reason (https only, no local / private hosts, no file:)
    if (Test-Placeholder $url) { return 'URL is a placeholder (the file is not published yet)' }
    $u = $null
    if (-not [Uri]::TryCreate($url, [UriKind]::Absolute, [ref]$u)) { return "not an absolute URL: $url" }
    if ($u.Scheme -ne 'https') { return "only https URLs are accepted: $url" }
    $h = $u.Host.ToLower()
    if ($h -match '^(localhost|.*\.local|.*\.lan|.*\.home|.*\.internal)$' -or $h -match '^(127\.|10\.|192\.168\.|169\.254\.|172\.(1[6-9]|2[0-9]|3[01])\.)' -or $h -match '^\[?(::1|f[cd][0-9a-f]{2}:|fe80:)') {
        return "local / private host refused: $h"
    }
    if ($hosts.Count -gt 0 -and $hosts -notcontains $h) { return "host $h is not allowed here (allowed: $($hosts -join ', '))" }
    return $null
}
function Read-ReleaseManifest([string]$path) {
    if (-not $path) { Stop-Run 'no release manifest given (-Manifest <file>)' }
    if ($path -match '^https?://') {
        $why = Test-SafeUrl $path
        if ($why) { Stop-Run "manifest URL refused: $why" }
        $local = Join-Path $WorkDir 'release-manifest.json'
        if (-not $Live) { Write-Dry "would download the manifest $path -> $local" ; if (-not (Test-Path -LiteralPath $local)) { Stop-Run 'dry run: no local copy of the manifest yet; download it from the release page and pass the file' } }
        else {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
            (New-Object Net.WebClient).DownloadFile($path, $local)
        }
        $path = $local
    }
    if (-not (Test-Path -LiteralPath $path)) { Stop-Run "release manifest not found: $path" }
    try { $m = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json } catch { Stop-Run "release manifest is not valid JSON: $path" }
    if ((Get-Field $m 'schema') -ne 1) { Stop-Run 'release manifest: schema must be 1' }
    foreach ($k in 'device', 'image', 'uboot_plain') { if ($null -eq (Get-Field $m $k)) { Stop-Run "release manifest: '$k' missing" } }
    $script:manifestPath = $path
    $script:manifestSha = Get-Sha $path
    return $m
}
function Get-ArtifactPath($art) {
    $f = [string](Get-Field $art 'file')
    if ($f -notmatch '^[A-Za-z0-9._-]+$') { Stop-Run "manifest: bad file name '$f' (letters, digits, . _ - only)" }
    return (Join-Path $DlDir $f)
}
function Get-ArtifactBlockers($art, [string]$label) {
    $r = New-Object System.Collections.Generic.List[string]
    if ($null -eq $art) { $r.Add("${label}: missing in the manifest"); return , $r }
    if (-not ([string](Get-Field $art 'sha256') -match '^[0-9a-f]{64}$')) { $r.Add("${label}: no SHA-256 (placeholder)") }
    $enc = Get-Field $art 'encoding'
    if (-not $enc) { if (-not ((Get-Long (Get-Field $art 'size')) -gt 0)) { $r.Add("${label}: no size (placeholder)") } }
    $parts = Get-Field $art 'parts'
    if ($null -ne $parts) {
        $i = 0
        foreach ($p in @($parts)) {
            $i++
            $why = Test-SafeUrl ([string](Get-Field $p 'url'))
            if ($why) { $r.Add("${label} part ${i}: $why") }
            if (-not ([string](Get-Field $p 'sha256') -match '^[0-9a-f]{64}$')) { $r.Add("${label} part ${i}: no SHA-256") }
            if (-not ((Get-Long (Get-Field $p 'size')) -gt 0)) { $r.Add("${label} part ${i}: no size") }
        }
        if ($i -eq 0) { $r.Add("${label}: empty parts list") }
    } else {
        $why = Test-SafeUrl ([string](Get-Field $art 'url'))
        if ($why) { $r.Add("${label}: $why") }
    }
    return , $r
}
function Get-ReleaseBlockers($m) {
    # the reasons why this release may NOT be written to a tablet; empty = allowed
    $r = New-Object System.Collections.Generic.List[string]
    if ((Get-Field $m 'flash_allowed') -ne $true) { $r.Add('manifest flash_allowed is not true (the release is not cleared for other tablets)') }
    $img = Get-Field $m 'image'
    if ((Get-Field $img 'generic') -ne $true) { $r.Add('image.generic is not true: the image is not a generic release image') }
    if ((Get-Field $img 'contains_unit_data') -ne $false) { $r.Add('image.contains_unit_data is not false: the image carries ANOTHER tablet''s own data (sensor calibration, Bluetooth address); never write it to your tablet') }
    if ((Get-Field $m 'test_only') -eq $true) { $r.Add('manifest test_only is true (a test manifest for dry runs)') }
    foreach ($x in (Get-ArtifactBlockers $img 'image')) { $r.Add($x) }
    foreach ($x in (Get-ArtifactBlockers (Get-Field $m 'uboot_plain') 'uboot_plain')) { $r.Add($x) }
    if (-not ((Get-Long (Get-Field $img 'unpacked_size')) -gt 0)) { $r.Add('image.unpacked_size missing') }
    if ((Get-Field $img 'generic') -eq $true -and -not ((Get-Long (Get-Field $img 'min_userdata_bytes')) -gt 0)) { $r.Add('image.min_userdata_bytes missing (a generic image is small and grows into userdata)') }
    return , $r
}

# ---------------------------------------------------------------------------------------------------------------------
# Downloads (resumable, verified)
function Invoke-HttpRange([string]$url, [string]$dest, [long]$expect) {
    # appends to $dest from its current length (HTTP Range); returns the final length
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $have = 0L
    if (Test-Path -LiteralPath $dest) { $have = (Get-Item -LiteralPath $dest).Length }
    if ($expect -gt 0 -and $have -gt $expect) { Remove-Item -LiteralPath $dest -Force; $have = 0L }
    if ($expect -gt 0 -and $have -eq $expect) { return $have }
    $req = [Net.HttpWebRequest]::Create($url)
    $req.UserAgent = 'Install-Pad4Linux/1.0'
    $req.AllowAutoRedirect = $true
    $req.Timeout = 60000; $req.ReadWriteTimeout = 120000
    if ($have -gt 0) { $req.AddRange([long]$have) }
    $resp = $req.GetResponse()
    try {
        $code = [int]$resp.StatusCode
        $mode = 'Append'
        if ($have -gt 0 -and $code -ne 206) { Write-Warn 'the server did not resume (no HTTP 206): starting this file again'; $have = 0L; $mode = 'Create' }
        if ($have -eq 0) { $mode = 'Create' }
        $in = $resp.GetResponseStream()
        $out = New-Object IO.FileStream($dest, [IO.FileMode]$mode, [IO.FileAccess]::Write)
        try {
            $buf = New-Object byte[] (4MB); $n = 0; $next = $have + 256MB
            while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
                $out.Write($buf, 0, $n); $have += $n
                if ($have -ge $next) { Write-Log ('    {0:N0} MB{1}' -f ($have / 1MB), $(if ($expect -gt 0) { ' of {0:N0} MB' -f ($expect / 1MB) } else { '' })); $next += 256MB }
            }
        } finally { $out.Close(); $in.Close() }
    } finally { $resp.Close() }
    return $have
}
function Save-Artifact($art, [string]$label) {
    # downloads one manifest artifact (one URL or several parts), verifies size + SHA-256; returns the local path
    $dest = Get-ArtifactPath $art
    $want = ([string](Get-Field $art 'sha256')).ToLower()
    $size = (Get-Long (Get-Field $art 'size'))
    if ((Test-Path -LiteralPath $dest) -and ($size -le 0 -or (Get-Item -LiteralPath $dest).Length -eq $size)) {
        Write-Log "  $label already on disk, hashing $dest ..."
        if ((Get-Sha $dest) -eq $want) { Write-Ok "$label verified (SHA-256 $($want.Substring(0, 16))...)"; return $dest }
        Write-Warn "$label on disk has a different SHA-256: it is downloaded again"
        if ($Live) { Remove-Item -LiteralPath $dest -Force }
    }
    $blk = Get-ArtifactBlockers $art $label
    if ($blk.Count -gt 0) { foreach ($b in $blk) { Write-Warn "not downloadable: $b" }; return $null }
    $enc = Get-Field $art 'encoding'
    $parts = Get-Field $art 'parts'
    $list = @()
    if ($null -ne $parts) { $list = @($parts) } else { $list = @([pscustomobject]@{ url = (Get-Field $art 'url'); size = $(if ($enc) { 0L } else { $size }); sha256 = $want }) }
    if (-not $Live) {
        $i = 0
        foreach ($p in $list) { $i++; Write-Dry ("would download {0} part {1}/{2}: {3} ({4}) and check SHA-256 {5}" -f $label, $i, $list.Count, (Get-Field $p 'url'), $(if ((Get-Long (Get-Field $p 'size')) -gt 0) { Format-Size ((Get-Long (Get-Field $p 'size'))) } else { 'size given after decoding' }), (Get-Field $p 'sha256')) }
        Write-Dry ("would verify {0} = {1}, SHA-256 {2}" -f $label, $dest, $want)
        return $null
    }
    New-Item -ItemType Directory -Force -Path $DlDir | Out-Null
    $i = 0; $pieces = @()
    foreach ($p in $list) {
        $i++
        $pp = if ($list.Count -gt 1) { '{0}.part{1:D2}' -f $dest, $i } else { "$dest.partial" }
        $pw = ([string](Get-Field $p 'sha256')).ToLower(); $ps = (Get-Long (Get-Field $p 'size'))
        Write-Log ("  downloading {0} part {1}/{2} from {3}" -f $label, $i, $list.Count, (Get-Field $p 'url'))
        $ok = $false
        for ($try = 1; $try -le 5 -and -not $ok; $try++) {
            try { $len = Invoke-HttpRange ([string](Get-Field $p 'url')) $pp $ps } catch { Write-Warn "try ${try}: $($_.Exception.Message) (the download resumes)"; Start-Sleep -Seconds 5; continue }
            if ($ps -gt 0 -and $len -ne $ps) { Write-Warn "try ${try}: $len of $ps bytes"; continue }
            if ($enc) { $ok = $true; break }
            if ((Get-Sha $pp) -eq $pw) { $ok = $true } else { Write-Warn "try ${try}: SHA-256 differs, downloading the part again"; Remove-Item -LiteralPath $pp -Force }
        }
        if (-not $ok) { Stop-Run "$label part $i could not be downloaded and verified" }
        $pieces += $pp
    }
    if ($enc -eq 'base64') {
        # googlesource ?format=TEXT serves the file base64-encoded
        $txt = [IO.File]::ReadAllText($pieces[0])
        [IO.File]::WriteAllBytes("$dest.tmp", [Convert]::FromBase64String(($txt -replace '\s', '')))
        Remove-Item -LiteralPath $pieces[0] -Force
    } elseif ($enc) { Stop-Run "${label}: unknown encoding '$enc'" }
    elseif ($pieces.Count -eq 1) { Move-Item -LiteralPath $pieces[0] -Destination "$dest.tmp" -Force }
    else {
        Write-Log "  joining $($pieces.Count) parts into $dest"
        $out = [IO.File]::Create("$dest.tmp")
        try { foreach ($pp in $pieces) { $in = [IO.File]::OpenRead($pp); try { $in.CopyTo($out, 4MB) } finally { $in.Close() } } } finally { $out.Close() }
    }
    $got = Get-Sha "$dest.tmp"
    if ($got -ne $want) { Remove-Item -LiteralPath "$dest.tmp" -Force; Stop-Run "${label}: the joined / decoded file has SHA-256 $got, the manifest says $want" }
    if ($size -gt 0 -and (Get-Item -LiteralPath "$dest.tmp").Length -ne $size) { Stop-Run "${label}: size differs from the manifest" }
    Move-Item -LiteralPath "$dest.tmp" -Destination $dest -Force
    if ($pieces.Count -gt 1) { foreach ($pp in $pieces) { Remove-Item -LiteralPath $pp -Force -ErrorAction SilentlyContinue } }
    Write-Ok "$label downloaded and verified: $dest (SHA-256 $($got.Substring(0, 16))...)"
    return $dest
}
function Test-ArtifactLocal($art, [string]$label) {
    # returns the local path when the file is there with the manifest's SHA-256, else $null (no download)
    if ($null -eq $art) { return $null }
    $want = [string](Get-Field $art 'sha256')
    if ($want -notmatch '^[0-9a-f]{64}$') { Write-Warn "${label}: the manifest has no SHA-256 (placeholder)"; return $null }
    $dest = Get-ArtifactPath $art
    if (-not (Test-Path -LiteralPath $dest)) { Write-Warn "${label}: not downloaded yet ($dest)"; return $null }
    Write-Log "  hashing $label ($dest) ..."
    $got = Get-Sha $dest
    if ($got -ne $want.ToLower()) { Write-Warn "${label}: SHA-256 $got differs from the manifest $want"; return $null }
    Write-Ok "$label SHA-256 equals the manifest ($($got.Substring(0, 16))...)"
    return $dest
}

# ---------------------------------------------------------------------------------------------------------------------
# Tools and the only ways this script talks to the tablet
function Find-Tool([string]$name) {
    $c = @()
    if ($PlatformTools) { $c += (Join-Path $PlatformTools "$name.exe") }
    $c += (Join-Path $ToolsDir "platform-tools\$name.exe")
    $c += "C:\platform-tools\$name.exe"
    foreach ($x in $c) { if (Test-Path -LiteralPath $x) { return $x } }
    $cmd = Get-Command "$name.exe" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}
$script:adb = $null; $script:fastboot = $null
$script:armed = $null
$script:fbExit = 0; $script:adbExit = 0
$script:imagePath = $null; $script:ubootPlainPath = $null; $script:ubootWritePath = $null; $script:undoPath = $null

function Test-PartName([string]$p) { return ($p -match '^[a-z0-9_]+$' -and $p -ne 'userdata' -and $p -notmatch '^sd[a-z]$') }
function Invoke-Fb {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$A)
    $joined = $A -join ' '
    $free = ($A.Count -eq 1 -and @('devices', 'reboot') -contains $A[0]) -or
            ($A.Count -eq 2 -and $A[0] -eq 'getvar' -and $AllowedVars -contains $A[1]) -or
            ($A.Count -eq 2 -and $A[0] -eq 'boot' -and $null -ne $script:ubootPlainPath -and $A[1] -eq $script:ubootPlainPath)
    if (-not $free) {
        $isWrite = ($A.Count -eq 3 -and $A[0] -eq 'flash' -and $WritableParts -contains $A[1])
        if (-not $isWrite -or $null -eq $script:armed -or $script:armed -ne $joined) { Stop-Run "refusing fastboot command '$joined' (not on this script's list)" 2 }
        $script:armed = $null
    }
    if (-not $Live) { Write-Dry "fastboot $joined"; $script:fbExit = 0; return @() }
    $ErrorActionPreference = 'Continue'
    $stream = ($A[0] -eq 'flash' -or $A[0] -eq 'boot')
    $out = @(& $script:fastboot @A 2>&1 | ForEach-Object { $l = "$_"; if ($stream) { Write-Log "    $l" }; $l })
    $script:fbExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($script:logFile -and -not $stream) { Add-Content -LiteralPath $script:logFile -Value (Hide-Serial ("  > fastboot $joined (exit $($script:fbExit))`n" + (($out | ForEach-Object { "    $_" }) -join "`n"))) }
    return $out
}
function Invoke-AdbCmd {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$A)
    $ok = ($A.Count -eq 1 -and @('devices', 'get-state', 'root', 'unroot', 'wait-for-device') -contains $A[0]) -or
          ($A.Count -eq 2 -and $A[0] -eq 'reboot' -and $A[1] -eq 'bootloader') -or
          ($A.Count -eq 3 -and $A[0] -eq 'shell' -and $A[1] -eq 'getprop' -and $AllowedProps -contains $A[2]) -or
          ($A.Count -eq 3 -and $A[0] -eq 'shell' -and $A[1] -eq 'getprop' -and $A[2] -ceq $BdAddrProp) -or
          ($A.Count -eq 3 -and $A[0] -eq 'shell' -and $A[1] -eq 'id' -and $A[2] -eq '-u') -or
          ($A.Count -eq 3 -and $A[0] -eq 'shell' -and $A[1] -eq 'dumpsys' -and $A[2] -eq 'battery') -or
          ($A.Count -eq 3 -and $A[0] -eq 'shell' -and $A[1] -eq 'ls' -and $A[2] -eq '/dev/block/by-name') -or
          ($A.Count -eq 4 -and $A[0] -eq 'shell' -and $A[1] -eq 'blockdev' -and $A[2] -eq '--getsize64' -and $A[3] -match '^/dev/block/by-name/(.+)$' -and (Test-PartName $Matches[1])) -or
          ($A.Count -eq 3 -and $A[0] -eq 'shell' -and $A[1] -eq 'sha256sum' -and $A[2] -match '^/dev/block/by-name/(.+)$' -and (Test-PartName $Matches[1])) -or
          ($A.Count -eq 3 -and $A[0] -eq 'pull' -and $A[1] -match '^/dev/block/by-name/(.+)$' -and (Test-PartName $Matches[1]))
    if (-not $ok) { Stop-Run "refusing adb command '$($A -join ' ')' (not on this script's list)" 2 }
    if (-not $Live) { Write-Dry "adb $($A -join ' ')"; $script:adbExit = 0; return @() }
    $ErrorActionPreference = 'Continue'
    $out = @(& $script:adb @A 2>&1 | ForEach-Object { "$_" })
    $script:adbExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($script:logFile) { Add-Content -LiteralPath $script:logFile -Value (Hide-Serial ("  > adb $($A -join ' ') (exit $($script:adbExit))`n" + (($out | ForEach-Object { "    $_" }) -join "`n"))) }
    return $out
}
function Save-PartitionRaw([string]$part, [string]$outFile) {
    # adb exec-out "dd if=/dev/block/by-name/<part> bs=4194304" > file, byte-exact (a read on the tablet)
    if (-not (Test-PartName $part)) { Stop-Run "refusing to read '$part'" 2 }
    if (-not $Live) { Write-Dry "adb exec-out ""dd if=/dev/block/by-name/$part bs=4194304 2>/dev/null"" > $outFile"; return 0 }
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName = $script:adb
    $psi.Arguments = "exec-out ""dd if=/dev/block/by-name/$part bs=4194304 2>/dev/null"""
    $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.CreateNoWindow = $true
    $p = [Diagnostics.Process]::Start($psi)
    $fs = [IO.File]::Create($outFile)
    try { $p.StandardOutput.BaseStream.CopyTo($fs, 4MB) } finally { $fs.Close() }
    $p.WaitForExit()
    if ($script:logFile) { Add-Content -LiteralPath $script:logFile -Value "  > adb exec-out dd if=/dev/block/by-name/$part (exit $($p.ExitCode))" }
    return $p.ExitCode
}
function Get-Var([string]$n) {
    foreach ($l in (Invoke-Fb getvar $n)) {
        if ($l -match ('^(\(bootloader\)\s*)?' + [regex]::Escape($n) + ':\s*(.*)$')) { return $Matches[2].Trim() }
    }
    return ''
}
function Get-Prop([string]$n) { return ((@(Invoke-AdbCmd shell getprop $n)) -join ' ').Trim() }
function Wait-Fastboot([int]$seconds) {
    if (-not $Live) { Write-Dry "would wait up to $seconds s for exactly one device in fastboot"; return $true }
    $end = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $end) {
        if (@((Invoke-Fb devices) | Where-Object { $_ -match '^\S+\s+fastboot\s*$' }).Count -eq 1) { return $true }
        Start-Sleep -Seconds 3
    }
    return $false
}
function Assert-Tools([switch]$NeedAdb) {
    $script:fastboot = Find-Tool 'fastboot'
    $script:adb = Find-Tool 'adb'
    $miss = @()
    if (-not $script:fastboot) { $miss += 'fastboot.exe' }
    if ($NeedAdb -and -not $script:adb) { $miss += 'adb.exe' }
    if ($miss.Count -gt 0) {
        $msg = "not found: $($miss -join ', '). Get Google's SDK Platform-Tools for Windows from https://developer.android.com/tools/releases/platform-tools, unzip it (e.g. to C:\platform-tools) and pass -PlatformTools <folder>."
        if ($Live) { Stop-Run $msg } else { Write-Warn $msg; return }
    }
    if ($script:fastboot) { Write-Ok "fastboot: $script:fastboot" }
    if ($script:adb) { Write-Ok "adb: $script:adb" }
}

# ---------------------------------------------------------------------------------------------------------------------
# Image parsing (PC only, read only): Android boot image header, U-Boot build kind, AVB footer / vbmeta
function Get-BootHeader([string]$p) {
    $b = Read-Bytes $p 0 4096
    if ($null -eq $b -or (Get-Ascii $b 0 8) -ne 'ANDROID!') { return $null }
    $hv = [BitConverter]::ToUInt32($b, 40)
    $osv = if ($hv -ge 3) { [BitConverter]::ToUInt32($b, 16) } else { [BitConverter]::ToUInt32($b, 44) }
    $ver = $osv -shr 11; $lvl = $osv -band 0x7ff
    return [pscustomobject]@{
        header      = [int]$hv
        os_version  = '{0}.{1}.{2}' -f ($ver -shr 14), (($ver -shr 7) -band 0x7f), ($ver -band 0x7f)
        patch_level = '{0}-{1:D2}' -f (2000 + ($lvl -shr 4)), ($lvl -band 0xf)
        kernel_size = [long][BitConverter]::ToUInt32($b, 8)
    }
}
function Get-UBootKind([string]$p) {
    # as check-header.py: the install build carries the install environment inside gzip(u-boot.bin)
    $h = Get-BootHeader $p
    if ($null -eq $h) { return 'not a boot image' }
    if ($h.header -lt 3) { return 'unknown (header < 3)' }
    $k = Read-Bytes $p 4096 ([int]$h.kernel_size)
    if ($null -eq $k) { return 'kernel truncated' }
    try {
        $ms = [IO.MemoryStream]::new($k)
        $gz = [IO.Compression.GZipStream]::new($ms, [IO.Compression.CompressionMode]::Decompress)
        $o = [IO.MemoryStream]::new()
        $gz.CopyTo($o); $gz.Close()
        $s = [Text.Encoding]::GetEncoding(28591).GetString($o.ToArray())
    } catch { return 'kernel is not gzip' }
    $install = $s.Contains('bootcmd=if run fedora_blkmap') -and $s.Contains('userdata_blkmap=')
    $rehearsal = $s.Contains("bootcmd=run fastboot_loop`0") -and -not $s.Contains('userdata_blkmap=')
    if ($install -and -not $rehearsal) { return 'install' }
    if ($rehearsal -and -not $install) { return 'rehearsal' }
    return 'unknown'
}
function Get-AvbInfo([string]$p) {
    # the AVB footer (last 64 bytes) and its vbmeta, or a bare vbmeta partition image ("AVB0" at 0)
    $len = (Get-Item -LiteralPath $p).Length
    if ($len -lt 320) { return $null }
    $tail = Read-Bytes $p ($len - 64) 64
    $footer = $false; $orig = 0L; $vbOff = 0L
    if ((Get-Ascii $tail 0 4) -eq 'AVBf') {
        $footer = $true
        $orig = [long](Get-U64BE $tail 12); $vbOff = [long](Get-U64BE $tail 20)
    }
    $h = Read-Bytes $p $vbOff 256
    if ($null -eq $h -or (Get-Ascii $h 0 4) -ne 'AVB0') { return $null }
    $auth = [long](Get-U64BE $h 12); $auxSize = [long](Get-U64BE $h 20)
    $alg = [int](Get-U32BE $h 28)
    $pkOff = [long](Get-U64BE $h 64); $pkSize = [long](Get-U64BE $h 72)
    $dOff = [long](Get-U64BE $h 96); $dSize = [long](Get-U64BE $h 104)
    $info = [ordered]@{
        file = $p; file_size = $len; has_footer = $footer; original_size = $orig; vbmeta_offset = $vbOff
        algorithm = $alg; rollback_index = [string](Get-U64BE $h 112); flags = [int](Get-U32BE $h 120)
        rollback_location = [int](Get-U32BE $h 124); key_sha1 = ''; props = @{}; hashes = @(); chains = @()
    }
    if ($auxSize -le 0 -or $auxSize -gt 1MB) { return [pscustomobject]$info }
    $aux = Read-Bytes $p ($vbOff + 256 + $auth) ([int]$auxSize)
    if ($null -eq $aux) { return $null }
    $sha1 = [Security.Cryptography.SHA1]::Create()
    if ($pkSize -gt 0) { $info.key_sha1 = ConvertTo-Hex ($sha1.ComputeHash($aux, [int]$pkOff, [int]$pkSize)) }
    $pos = [int]$dOff; $end = [int]($dOff + $dSize); $hashes = @(); $chains = @()
    while ($pos + 16 -le $end) {
        $tag = [long](Get-U64BE $aux $pos); $nb = [int](Get-U64BE $aux ($pos + 8)); $d = $pos + 16
        if ($tag -eq 0) {
            $kl = [int](Get-U64BE $aux $d); $vl = [int](Get-U64BE $aux ($d + 8))
            $info.props[(Get-Ascii $aux ($d + 16) $kl)] = Get-Ascii $aux ($d + 16 + $kl + 1) $vl
        } elseif ($tag -eq 2) {
            $nl = [int](Get-U32BE $aux ($d + 40)); $sl = [int](Get-U32BE $aux ($d + 44)); $dl = [int](Get-U32BE $aux ($d + 48))
            $q = $d + 116
            $salt = New-Object byte[] $sl; [Array]::Copy($aux, $q + $nl, $salt, 0, $sl)
            $dig = New-Object byte[] $dl; [Array]::Copy($aux, $q + $nl + $sl, $dig, 0, $dl)
            $hashes += [pscustomobject]@{ partition = (Get-Ascii $aux $q $nl); image_size = [long](Get-U64BE $aux $d); algorithm = (Get-Ascii $aux ($d + 8) 32); salt = (ConvertTo-Hex $salt); digest = (ConvertTo-Hex $dig) }
        } elseif ($tag -eq 4) {
            $loc = [int](Get-U32BE $aux $d); $nl = [int](Get-U32BE $aux ($d + 4)); $kl = [int](Get-U32BE $aux ($d + 8))
            $q = $d + 76
            $chains += [pscustomobject]@{ partition = (Get-Ascii $aux $q $nl); rollback_location = $loc; key_sha1 = (ConvertTo-Hex ($sha1.ComputeHash($aux, $q + $nl, $kl))) }
        }
        $pos = $d + $nb
    }
    $info.hashes = $hashes; $info.chains = $chains
    return [pscustomobject]$info
}
function Test-AvbHash([string]$p, $info) {
    # the hash descriptor's digest = sha256(salt || image[0 .. image_size]) (SHA-256 descriptors only)
    $hd = @($info.hashes | Where-Object { $_.partition -eq 'boot' })
    if ($hd.Count -ne 1 -or $hd[0].algorithm -ne 'sha256') { return $false }
    $sha = [Security.Cryptography.SHA256]::Create()
    $salt = ConvertFrom-Hex $hd[0].salt
    [void]$sha.TransformBlock($salt, 0, $salt.Length, $null, 0)
    $fs = [IO.File]::OpenRead($p)
    try {
        $rem = [long]$hd[0].image_size; $buf = New-Object byte[] (1MB)
        while ($rem -gt 0) { $n = $fs.Read($buf, 0, [int][Math]::Min([long]$buf.Length, $rem)); if ($n -le 0) { return $false }; [void]$sha.TransformBlock($buf, 0, $n, $null, 0); $rem -= $n }
    } finally { $fs.Close() }
    [void]$sha.TransformFinalBlock((New-Object byte[] 0), 0, 0)
    return ((ConvertTo-Hex $sha.Hash) -eq $hd[0].digest)
}
function Get-PrefixSha([string]$p, [long]$n) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $fs = [IO.File]::OpenRead($p)
    try {
        $rem = $n; $buf = New-Object byte[] (1MB)
        while ($rem -gt 0) { $r = $fs.Read($buf, 0, [int][Math]::Min([long]$buf.Length, $rem)); if ($r -le 0) { break }; [void]$sha.TransformBlock($buf, 0, $r, $null, 0); $rem -= $r }
    } finally { $fs.Close() }
    [void]$sha.TransformFinalBlock((New-Object byte[] 0), 0, 0)
    return (ConvertTo-Hex $sha.Hash)
}
function Get-SparseUnpacked([string]$p) {
    $h = Read-Bytes $p 0 28
    if ($null -eq $h -or [BitConverter]::ToUInt32($h, 0) -ne $SparseMagic) { return -1L }
    return [long][BitConverter]::ToUInt32($h, 12) * [long][BitConverter]::ToUInt32($h, 16)
}
function Get-MiscCommand([string]$p) {
    $b = Read-Bytes $p 0 32
    if ($null -eq $b) { return $null }
    $s = ''
    foreach ($c in $b) { if ($c -eq 0) { break }; if ($c -ge 32 -and $c -lt 127) { $s += [char]$c } else { $s += '.' } }
    return $s
}
function Write-AvbInfo($info) {
    if ($null -eq $info) { Write-Log '  no AVB data'; return }
    Write-Log ("  AVB: footer {0}, original image {1} bytes, algorithm {2}, rollback index {3} (location {4}), key sha1 {5}" -f $info.has_footer, $info.original_size, $info.algorithm, $info.rollback_index, $info.rollback_location, $info.key_sha1)
    foreach ($k in ($info.props.Keys | Sort-Object)) { Write-Log ("    prop {0} = {1}" -f $k, $info.props[$k]) }
    foreach ($x in $info.hashes) { Write-Log ("    hash descriptor {0}: {1} bytes, {2}" -f $x.partition, $x.image_size, $x.algorithm) }
    foreach ($x in $info.chains) { Write-Log ("    chain descriptor {0}: rollback location {1}, key sha1 {2}" -f $x.partition, $x.rollback_location, $x.key_sha1) }
}

# ---------------------------------------------------------------------------------------------------------------------
# The tablet in the boot loader (read only)
function Assert-Abl([switch]$AllowSlotA) {
    Write-Step 'Tablet in the boot loader (ABL) fastboot - read only'
    if (-not $Live) {
        Write-Dry 'fastboot devices: exactly one device'
        Write-Dry "fastboot getvar product = $ExpectedProduct (not U-Boot's '$UBootProduct'); getvar is-userspace = no (not fastbootd); getvar unlocked = yes; getvar current-slot = b; getvar battery-voltage >= $MinBatteryMv mV"
        return 'b'
    }
    $n = @((Invoke-Fb devices) | Where-Object { $_ -match '^\S+\s+fastboot\s*$' }).Count
    if ($n -ne 1) { Stop-Run "expected exactly one device in fastboot, found $n (switch the tablet off, hold Volume Down + Power until the boot loader shows, connect USB)" }
    $prod = Get-Var 'product'
    if ($prod -eq $UBootProduct) { Stop-Run "this is U-Boot's own fastboot ($UBootProduct). Hold Volume Down + Power (about 15 s) until the tablet's boot loader shows. U-Boot's fastboot is never written through." }
    if ($prod -ne $ExpectedProduct) { Stop-Run "fastboot product is '$prod', expected '$ExpectedProduct' (OnePlus Pad 4 boot loader)" }
    if ((Get-Var 'is-userspace') -eq 'yes') { Stop-Run 'this is fastbootd (Android userspace), not the boot loader. Use the boot loader: switch off, Volume Down + Power.' }
    $unl = Get-Var 'unlocked'
    if ($unl -ne 'yes') { Stop-Run "boot loader unlocked = '$unl'. This script never unlocks (unlocking erases the tablet and is your own decision, outside this script)." }
    $slot = Get-Var 'current-slot'
    if ($slot -ne 'b' -and -not $AllowSlotA) { Stop-Run "current-slot is '$slot', expected 'b'. Write nothing. The owner's procedure is proven only on slot b; this script never switches slots (no set_active)." }
    $mvText = Get-Var 'battery-voltage'
    $mv = 0; [void][int]::TryParse(($mvText -replace '[^0-9]', ''), [ref]$mv)
    if ($mv -gt 0 -and $mv -lt $MinBatteryMv) { Stop-Run "battery $mv mV is below $MinBatteryMv mV: charge to above $MinBatteryPercent % first" }
    if ($mv -eq 0) { Write-Warn "battery voltage not readable ('$mvText'): make sure the battery is above $MinBatteryPercent %" }
    Write-Ok "product $prod, boot loader (not fastbootd), unlocked, current-slot $slot, battery $mv mV"
    return $slot
}
function Assert-PartSize([string]$name, [long]$want) {
    if (-not $Live) { Write-Dry ("fastboot getvar partition-size:{0} must be 0x{1:X} ({1} bytes)" -f $name, $want); return }
    $txt = Get-Var "partition-size:$name"
    $got = -1L
    try { $got = [Convert]::ToInt64(($txt -replace '^\s*0x', ''), 16) } catch { $got = -1L }
    if ($got -ne $want) { Stop-Run ("partition-size:{0} reads '{1}', expected 0x{2:X} ({2} bytes). Not the tablet / storage size this release is made for." -f $name, $txt, $want) }
    Write-Ok ("partition-size:{0} = 0x{1:X} ({1} bytes)" -f $name, $got)
}
function Assert-UserdataSize($m) {
    # a generic image (image.min_userdata_bytes > 0) is small and grows into userdata at its first boot: userdata must be at
    # least that size; an image without the field (B149) must match device.userdata_bytes exactly
    $min = Get-Long (Get-Field (Get-Field $m 'image') 'min_userdata_bytes')
    if ($min -le 0) { Assert-PartSize 'userdata' (Get-Long (Get-Field (Get-Field $m 'device') 'userdata_bytes')); return }
    if (-not $Live) { Write-Dry ("fastboot getvar partition-size:userdata must be at least 0x{0:X} ({0} bytes: the image grows into the rest)" -f $min); return }
    $txt = Get-Var 'partition-size:userdata'
    $got = -1L
    try { $got = [Convert]::ToInt64(($txt -replace '^\s*0x', ''), 16) } catch { $got = -1L }
    if ($got -lt $min) { Stop-Run ("partition-size:userdata reads '{0}', smaller than this image's minimum 0x{1:X} ({1} bytes)" -f $txt, $min) }
    Write-Ok ("partition-size:userdata = 0x{0:X} ({0} bytes) >= the image's minimum {1} bytes; the root grows into the rest at the first boot" -f $got, $min)
}
function Test-BdAddr([string]$a) {
    return ($a -cmatch '^([0-9A-F]{2}:){5}[0-9A-F]{2}$') -and ($BdPlaceholders -notcontains $a)
}
function Show-BdAddrHint {
    # the one command for Fedora's first login; the address is shown on screen only (Write-Host), never in the log
    $bdir = Get-NewestBackup
    $f = if ($bdir) { Join-Path $bdir.FullName 'bdaddr.txt' } else { $null }
    if ($f -and (Test-Path -LiteralPath $f)) {
        $a = ((Get-Content -LiteralPath $f -TotalCount 1) -join '').Trim().ToUpper()
        if (Test-BdAddr $a) {
            Write-Log '  Bluetooth: after your FIRST login in Fedora, open a terminal and run this once (your tablet''s own address, read from Android in the backup):' 'Yellow'
            Write-Host "      sudo iceland-provision --bdaddr $a" -ForegroundColor Yellow
            if ($script:logFile) { try { Add-Content -LiteralPath $script:logFile -Value '      sudo iceland-provision --bdaddr <the address in the backup folder''s bdaddr.txt>' } catch {} }
            return
        }
    }
    Write-Log '  Bluetooth: no own address was saved from Android; Fedora uses the controller''s shared default address (iceland-provision warns once). With your address: sudo iceland-provision --bdaddr XX:XX:XX:XX:XX:XX' 'Yellow'
}
function Read-SlotFlags([string]$s) {
    if (-not $Live) { Write-Dry "fastboot getvar current-slot, slot-successful:$s, slot-unbootable:$s, slot-retry-count:$s"; return [pscustomobject]@{ current = 'b'; successful = 'yes'; unbootable = 'no'; retry = 6 } }
    $f = [pscustomobject]@{
        current    = (Get-Var 'current-slot')
        successful = (Get-Var "slot-successful:$s")
        unbootable = (Get-Var "slot-unbootable:$s")
        retry      = -1
    }
    $rc = -1; [void][int]::TryParse((Get-Var "slot-retry-count:$s"), [ref]$rc); $f.retry = $rc
    Write-Log ("  slot {0}: current-slot={1} successful={2} unbootable={3} retry-count={4}" -f $s, $f.current, $f.successful, $f.unbootable, $f.retry)
    return $f
}

# ---------------------------------------------------------------------------------------------------------------------
# Backups (local, private)
function Get-NewestBackup {
    if ($BackupDir) {
        if (-not (Test-Path -LiteralPath (Join-Path $BackupDir 'backup-manifest.json'))) { Stop-Run "no backup-manifest.json in $BackupDir" }
        return (Get-Item -LiteralPath $BackupDir)
    }
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return $null }
    return (Get-ChildItem -LiteralPath $BackupRoot -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'backup-manifest.json') } | Sort-Object Name -Descending | Select-Object -First 1)
}
function Read-BackupManifest($dir) {
    $bm = Get-Content -LiteralPath (Join-Path $dir.FullName 'backup-manifest.json') -Raw | ConvertFrom-Json
    return $bm
}
function Assert-UndoFile($dir, $bm) {
    $e = @($bm.files | Where-Object { $_.file -eq 'boot_b-before-install.img' })
    if ($e.Count -ne 1) { Stop-Run "the backup $($dir.FullName) has no boot_b-before-install.img entry" }
    $p = Join-Path $dir.FullName 'boot_b-before-install.img'
    if (-not (Test-Path -LiteralPath $p)) { Stop-Run "undo file missing: $p" }
    $len = (Get-Item -LiteralPath $p).Length
    if ($len -ne $BootBBytes) { Stop-Run "undo file is $len bytes, boot_b is $BootBBytes" }
    Write-Log "  hashing the undo file $p ..."
    $got = Get-Sha $p
    if ($got -ne $e[0].sha256_pc) { Stop-Run "undo file SHA-256 $got differs from the backup manifest $($e[0].sha256_pc)" }
    Write-Ok "undo file of write 2: $p, $len bytes, SHA-256 $got"
    return $p
}

# ---------------------------------------------------------------------------------------------------------------------
# The U-Boot file for boot_b: the release's footered file when it matches this tablet, else a local footer
function Get-PythonCmd {
    if ($Python) { if (Test-Path -LiteralPath $Python) { return @($Python) }; Stop-Run "python not found: $Python" }
    $c = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($c -and $c.Source -notmatch 'WindowsApps') { return @($c.Source) }
    $c = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($c) { return @($c.Source, '-3') }
    return $null
}
function Find-OpenSsl {
    $c = Get-Command 'openssl.exe' -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($x in @("$env:ProgramFiles\Git\usr\bin\openssl.exe", "${env:ProgramFiles(x86)}\Git\usr\bin\openssl.exe")) { if ($x -and (Test-Path -LiteralPath $x)) { return $x } }
    return $null
}
function Test-FooterFor([string]$path, [string]$plainSha, $want, [string]$label) {
    # the footered U-Boot must: be exactly boot_b's size, carry the plain install U-Boot unchanged, have a valid hash
    # descriptor "boot", be signed with the key vbmeta_b chains boot with, and carry this tablet's rollback index,
    # os_version and security_patch (exactly what mk-footer.sh copies from today's boot_b)
    $bad = @()
    $len = (Get-Item -LiteralPath $path).Length
    if ($len -ne $BootBBytes) { $bad += "size $len, boot_b is $BootBBytes" }
    $i = Get-AvbInfo $path
    if ($null -eq $i -or -not $i.has_footer) { $bad += 'no AVB footer'; return , $bad }
    if ((Get-PrefixSha $path $i.original_size) -ne $plainSha) { $bad += 'the image inside the footer is not the plain install U-Boot of the manifest' }
    if (-not (Test-AvbHash $path $i)) { $bad += 'the hash descriptor does not match the image (damaged file)' }
    if ($i.key_sha1 -ne $want.key_sha1) { $bad += "signing key sha1 $($i.key_sha1), the chain needs $($want.key_sha1)" }
    if ($i.rollback_index -ne $want.rollback_index) { $bad += "rollback index $($i.rollback_index), this tablet's boot_b has $($want.rollback_index)" }
    foreach ($k in 'com.android.build.boot.os_version', 'com.android.build.boot.security_patch') {
        $a = $null; $b = $null
        if ($i.props.ContainsKey($k)) { $a = $i.props[$k] }
        if ($want.props.ContainsKey($k)) { $b = $want.props[$k] }
        if ($a -ne $b) { $bad += "$k is '$a', this tablet's boot_b has '$b'" }
    }
    if ($bad.Count -eq 0) { Write-Ok "${label}: footer matches this tablet (rollback $($i.rollback_index), os $($i.props['com.android.build.boot.os_version']), patch $($i.props['com.android.build.boot.security_patch']), key $($i.key_sha1.Substring(0, 8))...), hash descriptor valid" }
    return , $bad
}
function New-LocalFooter([string]$plain, [string]$plainSha, $want, $m) {
    # the owner's mk-footer.sh, unchanged in its parameters, with AOSP avbtool (pinned) on this PC
    $out = Join-Path $WorkDir 'u-boot-iceland-footered-local.img'
    $py = Get-PythonCmd
    $ossl = Find-OpenSsl
    $avb = Test-ArtifactLocal (Get-Field $m 'avbtool') 'avbtool'
    $key = Test-ArtifactLocal (Get-Field $m 'avb_testkey') 'avb_testkey'
    $osv = ''; $spl = ''
    if ($want.props.ContainsKey('com.android.build.boot.os_version')) { $osv = $want.props['com.android.build.boot.os_version'] }
    if ($want.props.ContainsKey('com.android.build.boot.security_patch')) { $spl = $want.props['com.android.build.boot.security_patch'] }
    $args2 = @('add_hash_footer', '--image', $out, '--partition_name', 'boot', '--partition_size', "$BootBBytes",
               '--algorithm', 'SHA256_RSA4096', '--key', "$key", '--rollback_index', "$($want.rollback_index)", '--salt', $plainSha,
               '--prop', "com.android.build.boot.os_version:$osv", '--prop', "com.android.build.boot.security_patch:$spl",
               '--prop', 'iceland.image:u-boot-iceland')
    if (-not $osv -or -not $spl) { Stop-Run "this tablet's boot_b has no os_version / security_patch props in its AVB footer: not the owner's case (mk-footer.sh refuses too)" }
    if (-not $Live) { Write-Dry ("would copy {0} to {1} and run: python avbtool.py {2}" -f $plain, $out, ($args2 -join ' ')); return $null }
    if (-not $py) { Stop-Run 'the footer for this tablet must be made locally and needs Python 3 (https://www.python.org/) - or ask for a release whose footered U-Boot matches your boot_b' }
    if (-not $ossl) { Stop-Run 'avbtool signs with openssl.exe: install Git for Windows (it brings usr\bin\openssl.exe) or put openssl.exe on PATH' }
    if (-not $avb -or -not $key) { Stop-Run 'avbtool.py / testkey_rsa4096.pem not downloaded and verified: run -Phase Download -Execute first' }
    Copy-Item -LiteralPath $plain -Destination $out -Force
    $oldPath = $env:PATH
    $env:PATH = (Split-Path -Parent $ossl) + ';' + $env:PATH
    try {
        $ErrorActionPreference = 'Continue'
        $pyArgs = @(); if ($py.Count -gt 1) { $pyArgs = $py[1..($py.Count - 1)] }
        $o = @(& $py[0] @pyArgs $avb @args2 2>&1 | ForEach-Object { "$_" })
        $rc = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
    } finally { $env:PATH = $oldPath }
    foreach ($l in $o) { Write-Log "    $l" }
    if ($rc -ne 0) { Stop-Run "avbtool add_hash_footer failed (exit $rc)" }
    return $out
}
function Select-BootBImage($m, [string]$plain, [string]$plainSha, $want) {
    $pre = Get-Field $m 'uboot_footered'
    $prePath = $null
    if ($null -ne $pre) { $prePath = Test-ArtifactLocal $pre 'uboot_footered' }
    if ($prePath) {
        $bad = Test-FooterFor $prePath $plainSha $want 'release footered U-Boot'
        if ($bad.Count -eq 0) { return $prePath }
        foreach ($x in $bad) { Write-Warn "release footered U-Boot does not fit this tablet: $x" }
        Write-Log '  -> making the footer for THIS tablet locally (the owner''s mk-footer.sh parameters)'
    } else { Write-Log '  no release footered U-Boot on disk -> the footer is made locally for this tablet' }
    $loc = New-LocalFooter $plain $plainSha $want $m
    if ($null -eq $loc) { return $null }
    $bad = Test-FooterFor $loc $plainSha $want 'locally footered U-Boot'
    if ($bad.Count -gt 0) { Stop-Run ("the locally made footer is wrong: " + ($bad -join '; ')) }
    return $loc
}

# =====================================================================================================================
# Phases
function Invoke-Preflight($m) {
    Write-Step 'Preflight (PC only)'
    Write-Ok ("PowerShell {0} ({1}); Install-Pad4Linux {2}; {3}" -f $PSVersionTable.PSVersion, $PSVersionTable.PSEdition, $ScriptVersion, $(if ($Live) { 'EXECUTE' } else { 'DRY RUN: nothing is downloaded, adb / fastboot are never started' }))
    Assert-Tools -NeedAdb
    if ($script:fastboot -and $Live) {
        $ErrorActionPreference = 'Continue'; $v = @(& $script:fastboot --version 2>&1 | ForEach-Object { "$_" }); $ErrorActionPreference = 'Stop'
        Write-Log "  $($v -join ' | ')"
    }
    Write-Log ("  release manifest: {0} (SHA-256 {1}) - compare this hash with the release page" -f $script:manifestPath, $script:manifestSha)
    Write-Log ("  release: {0}" -f (Get-Field $m 'release'))
    $img = Get-Field $m 'image'
    Write-Log ("  image: {0}, {1}, unpacked {2}" -f (Get-Field $img 'file'), $(if ((Get-Long (Get-Field $img 'size')) -gt 0) { Format-Size ((Get-Long (Get-Field $img 'size'))) } else { 'size: placeholder' }), (Get-Field $img 'unpacked_size'))
    $blk = Get-ReleaseBlockers $m
    if ($blk.Count -gt 0) {
        Write-Warn 'this release can NOT be written to a tablet (the script will refuse write 1 and write 2):'
        foreach ($b in $blk) { Write-Log "         - $b" 'Yellow' }
        Write-Log '         Backups (read only) still work.' 'Yellow'
    } else { Write-Ok 'release manifest: cleared for flashing (generic image, all files published with SHA-256)' }
    # free space: downloads not yet on disk + the read-only backup + margin
    $need = 2GB + 800MB
    foreach ($k in 'image', 'uboot_plain', 'uboot_footered') {
        $a = Get-Field $m $k
        if ($null -eq $a) { continue }
        $f = [string](Get-Field $a 'file')
        $sz = (Get-Long (Get-Field $a 'size'))
        if ($f -match '^[A-Za-z0-9._-]+$' -and -not (Test-Path -LiteralPath (Join-Path $DlDir $f))) { $need += [Math]::Max($sz, 0L) * $(if ($k -eq 'image') { 2 } else { 1 }) }
    }
    if ($FullBackup) { $need += 18GB }
    $free = Get-FreeBytes $WorkDir
    if ($free -ge 0 -and $free -lt $need) { $msg = ("only {0:N1} GB free on the drive of {1}; this run needs about {2:N1} GB (downloads, joining parts, backup, margin)" -f ($free / 1GB), $WorkDir, ($need / 1GB)); if ($Live) { Stop-Run $msg } else { Write-Warn $msg } }
    else { Write-Ok ("{0:N1} GB free on the drive of {1} (about {2:N1} GB needed)" -f ($free / 1GB), $WorkDir, ($need / 1GB)) }
    if (-not (Get-PythonCmd)) { Write-Log '  Python 3 not found: only needed if the release''s footered U-Boot does not match your boot_b (then the footer is made locally).' }
}
function Invoke-Download($m) {
    Write-Step 'Download (every file verified by SHA-256; an interrupted download resumes)'
    foreach ($k in 'image', 'uboot_plain', 'uboot_footered', 'avbtool', 'avb_testkey') {
        $a = Get-Field $m $k
        if ($null -eq $a) { Write-Log "  ${k}: not in this manifest"; continue }
        if ($k -eq 'avbtool' -or $k -eq 'avb_testkey') {
            $why = Test-SafeUrl ([string](Get-Field $a 'url')) @('android.googlesource.com')
            if ($why) { Write-Warn "${k}: $why"; continue }
        }
        [void](Save-Artifact $a $k)
    }
    $pt = Get-Field $m 'platform_tools'
    if ($null -ne $pt -and -not (Find-Tool 'fastboot')) {
        $why = Test-SafeUrl ([string](Get-Field $pt 'url')) @('dl.google.com')
        if ($why -or ([string](Get-Field $pt 'sha256')) -notmatch '^[0-9a-f]{64}$') { Write-Warn "platform-tools: no pinned Google download in this manifest ($why). Download them yourself from https://developer.android.com/tools/releases/platform-tools" }
        else {
            $zip = Save-Artifact $pt 'platform_tools'
            if ($zip) { Expand-Archive -LiteralPath $zip -DestinationPath $ToolsDir -Force; Write-Ok "platform-tools unpacked to $ToolsDir\platform-tools" }
        }
    }
}
function Invoke-Backup($m, [switch]$StayInFastboot) {
    Write-Step 'Backup - READ ONLY (Android: LineageOS on slot b, USB debugging and Developer options > "Rooted debugging" ON)'
    Assert-Tools -NeedAdb
    $dev = Get-Field $m 'device'
    $dir = Join-Path $BackupRoot ('backup-' + $script:stamp)
    if ($Live) {
        $st = @((Invoke-AdbCmd devices) | Where-Object { $_ -match '^\S+\s+device\s*$' }).Count
        if ($st -ne 1) { Stop-Run "expected exactly one tablet in Android with USB debugging allowed, found $st" }
    } else { Write-Dry 'adb devices: exactly one tablet in Android' }
    # identity, lock state, slot, root, battery
    $facts = [ordered]@{}
    foreach ($p in $AllowedProps) { $facts[$p] = Get-Prop $p }
    if ($Live) {
        $models = @(Get-Field $dev 'android_model'); $devices = @(Get-Field $dev 'android_device')
        $idOk = ($models -contains $facts['ro.product.model']) -or ($devices -contains $facts['ro.product.device']) -or ($facts['ro.build.fingerprint'] -match ('/(' + (($models | ForEach-Object { [regex]::Escape($_) }) -join '|') + ')/'))
        if (-not $idOk) { Stop-Run ("this is not a OnePlus Pad 4: model '{0}', device '{1}'" -f $facts['ro.product.model'], $facts['ro.product.device']) }
        Write-Ok ("OnePlus Pad 4: model {0}, device {1}, Android {2}, build type {3}" -f $facts['ro.product.model'], $facts['ro.product.device'], $facts['ro.build.version.release'], $facts['ro.build.type'])
        if ($facts['ro.boot.vbmeta.device_state'] -ne 'unlocked' -and $facts['ro.boot.flash.locked'] -ne '0') { Stop-Run 'the boot loader is LOCKED. This script never unlocks it. Unlocking (fastboot flashing unlock) erases the tablet and is your own decision; the owner did it before this procedure. Come back when it is unlocked and LineageOS runs on slot b.' }
        if ($facts['ro.boot.slot_suffix'] -ne '_b') { Stop-Run "the active slot is '$($facts['ro.boot.slot_suffix'])', not _b. The owner's procedure writes boot_b and is proven only with LineageOS running on slot b; this script never switches slots." }
        if ($facts['ro.build.type'] -ne 'userdebug' -and $facts['ro.gsid.image_running'] -ne '1') { Stop-Run "build type '$($facts['ro.build.type'])': reading the partitions needs adb root, which only a userdebug build (LineageOS: Developer options > Rooted debugging) or a DSU image gives. The owner's starting point was LineageOS on slot b." }
        $bat = (@(Invoke-AdbCmd shell dumpsys battery) | Where-Object { $_ -match '^\s*level:\s*(\d+)' } | Select-Object -First 1)
        $lvl = -1; if ($bat -and $bat -match 'level:\s*(\d+)') { $lvl = [int]$Matches[1] }
        if ($lvl -lt $MinBatteryPercent) { Stop-Run "battery $lvl %: charge to at least $MinBatteryPercent % first (the PC's own USB port and cable, the PC on mains, no sleep)" }
        Write-Ok "battery $lvl %"
        Invoke-AdbCmd root | Out-Null; Start-Sleep -Seconds 3; Invoke-AdbCmd wait-for-device | Out-Null
        $uid = ((@(Invoke-AdbCmd shell id -u)) -join '').Trim()
        if ($uid -ne '0') { Stop-Run "adb is not root (id -u = '$uid'): turn on Developer options > Rooted debugging, then run again" }
        Write-Ok 'adb shell is root (reads only)'
    } else {
        Write-Dry ("would require: model in {0} or device in {1}; vbmeta.device_state unlocked; slot_suffix _b; build type userdebug (or DSU); battery >= {2} %; adb root (id -u = 0)" -f ((@(Get-Field $dev 'android_model')) -join '/'), ((@(Get-Field $dev 'android_device')) -join '/'), $MinBatteryPercent)
        Invoke-AdbCmd shell dumpsys battery | Out-Null
        Invoke-AdbCmd root | Out-Null; Invoke-AdbCmd wait-for-device | Out-Null; Invoke-AdbCmd shell id -u | Out-Null
    }
    # the partitions
    $parts = @($ReadParts)
    if ($FullBackup) {
        if ($Live) {
            $names = @((Invoke-AdbCmd shell ls /dev/block/by-name) | ForEach-Object { $_.Trim() } | Where-Object { $_ -and (Test-PartName $_) })
            $first = @('persist', 'oplusreserve1', 'oplusreserve2', 'modemst1', 'modemst2', 'fsg', 'fsc', 'frp', 'devinfo')
            $parts = @($parts) + @($first | Where-Object { $names -contains $_ -and $parts -notcontains $_ }) + @($names | Where-Object { $first -notcontains $_ -and $parts -notcontains $_ -and $_ -ne 'super' } | Sort-Object)
            if ($names -contains 'super') { $parts += 'super' }
        } else { Invoke-AdbCmd shell ls /dev/block/by-name | Out-Null; Write-Dry 'would add every partition in /dev/block/by-name except userdata and the whole-LUN nodes (persist and the other calibration partitions first, super last: about 17 GB)' }
    }
    if ($Live) { New-Item -ItemType Directory -Force -Path $dir | Out-Null; Set-Content -LiteralPath (Join-Path $dir 'PRIVATE-README.txt') -Value 'PRIVATE: partition copies of ONE tablet (boot images, misc; with -FullBackup also calibration, persist, modem data). Never upload or share. Keep a second copy on another disk.' }
    else { Write-Dry "would create the private backup folder $dir" }
    $rows = @()
    foreach ($p in $parts) {
        $out = Join-Path $dir "$p.img"
        $dpath = "/dev/block/by-name/$p"
        if (-not $Live) { Invoke-AdbCmd shell blockdev --getsize64 $dpath | Out-Null; Invoke-AdbCmd shell sha256sum $dpath | Out-Null; Invoke-AdbCmd pull $dpath $out | Out-Null; continue }
        $size = ((@(Invoke-AdbCmd shell blockdev --getsize64 $dpath)) -join '').Trim()
        if ($size -notmatch '^\d+$') { Stop-Run "cannot read the size of ${p}: '$size'" }
        $want = (((@(Invoke-AdbCmd shell sha256sum $dpath)) -join ' ').Trim() -split '\s+')[0].ToLower()
        if ($want -notmatch '^[0-9a-f]{64}$') { Stop-Run "the tablet did not give a SHA-256 for ${p}: '$want'" }
        $ok = $false; $got = ''
        for ($try = 1; $try -le 3 -and -not $ok; $try++) {
            if (Test-Path -LiteralPath $out) { Set-ItemProperty -LiteralPath $out -Name IsReadOnly -Value $false; Remove-Item -LiteralPath $out -Force }
            Invoke-AdbCmd pull $dpath $out | Out-Null
            $len = if (Test-Path -LiteralPath $out) { (Get-Item -LiteralPath $out).Length } else { -1 }
            if ("$len" -ne $size) { Write-Log "  ${p}: adb pull gave $len of $size bytes - reading it with exec-out dd"; if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }; [void](Save-PartitionRaw $p $out); $len = if (Test-Path -LiteralPath $out) { (Get-Item -LiteralPath $out).Length } else { -1 } }
            if ("$len" -ne $size) { Write-Warn "try ${try}: $p read $len of $size bytes"; continue }
            $got = Get-Sha $out
            if ($got -eq $want) { $ok = $true } else { Write-Warn "try ${try}: $p SHA-256 differs from the tablet's" }
        }
        if (-not $ok) { Stop-Run "$p could not be copied reliably (cable / port): nothing is written until the backup is complete" }
        Set-ItemProperty -LiteralPath $out -Name IsReadOnly -Value $true
        Write-Ok ("{0}: {1:N0} bytes, SHA-256 {2} (tablet = PC)" -f $p, [long]$size, $got)
        $rows += [pscustomobject]@{ partition = $p; file = "$p.img"; bytes = [long]$size; sha256_device = $want; sha256_pc = $got }
    }
    $undo = Join-Path $dir 'boot_b-before-install.img'
    if (-not $Live) { Write-Dry "would copy boot_b.img to $undo (the undo file of write 2) and check both SHA-256 equal" }
    else {
        Copy-Item -LiteralPath (Join-Path $dir 'boot_b.img') -Destination $undo
        $u = Get-Sha $undo
        $b = @($rows | Where-Object { $_.partition -eq 'boot_b' })[0]
        if ($u -ne $b.sha256_pc) { Stop-Run 'the undo copy of boot_b differs from boot_b.img' }
        Set-ItemProperty -LiteralPath $undo -Name IsReadOnly -Value $true
        $rows += [pscustomobject]@{ partition = 'boot_b'; file = 'boot_b-before-install.img'; bytes = $b.bytes; sha256_device = $b.sha256_device; sha256_pc = $u }
        Write-Ok "undo file of write 2: $undo (SHA-256 $u)"
    }
    # the tablet's own Bluetooth address: one read-only getprop, saved next to the backup manifest
    # (private, like the backup), never logged; Fedora gets it at the first login (Show-BdAddrHint). Missing: a warning only
    $bdSaved = $false
    if ($Live) {
        $bd = ((Get-Prop $BdAddrProp) -replace '\s', '').ToUpper()
        if (Test-BdAddr $bd) {
            $bf = Join-Path $dir 'bdaddr.txt'
            Set-Content -LiteralPath $bf -Value $bd -Encoding ASCII; Set-ItemProperty -LiteralPath $bf -Name IsReadOnly -Value $true
            $bdSaved = $true; Write-Ok 'Bluetooth address: read from Android and saved as bdaddr.txt in the backup folder (private; masked in the log)'
        } else { Write-Warn "Android's $BdAddrProp holds no usable Bluetooth address: Fedora will use the controller's shared default address until you set yours (README section 7)" }
    } else { Invoke-AdbCmd shell getprop $BdAddrProp | Out-Null; Write-Dry 'would save the Bluetooth address as <backup>\bdaddr.txt (private, never logged)' }
    Invoke-AdbCmd unroot | Out-Null
    # the PC checks of parta-check.sh on today's images
    $an = [ordered]@{}
    $checks = 0
    if ($Live) {
        $cmd = Get-MiscCommand (Join-Path $dir 'misc.img')
        if ($cmd -eq '' -or $cmd -eq 'bootonce-bootloader') { Write-Ok "misc: boot command '$cmd' (ABL acts only on boot-recovery / boot-fastboot)" }
        else { Write-Warn "misc holds '$cmd': ABL would start recovery instead of boot_b. Boot LineageOS recovery, choose 'Reboot system now', then run the backup again."; $checks++ }
        $an['misc_command'] = $cmd
        $vb = Get-AvbInfo (Join-Path $dir 'vbmeta_b.img')
        $ch = @(); if ($vb) { $ch = @($vb.chains | Where-Object { $_.partition -eq 'boot' }) }
        if ($ch.Count -eq 1 -and $ch[0].key_sha1 -eq $FooterKeySha1) { Write-Ok "vbmeta_b chains boot with key sha1 $($ch[0].key_sha1) (LineageOS test keys: the owner's case)" }
        else { Write-Warn ("vbmeta_b does not chain boot with the AOSP test key (found: {0}). Not the owner's proven case (LineageOS); write 2 will be refused." -f $(if ($ch.Count) { $ch[0].key_sha1 } else { 'no chain for boot' })); $checks++ }
        $bi = Get-AvbInfo (Join-Path $dir 'boot_b.img')
        if ($null -eq $bi -or -not $bi.has_footer) { Write-Warn "today's boot_b has no AVB footer: not the owner's case"; $checks++ }
        else { Write-Ok ("boot_b footer: rollback index {0}, os_version {1}, security_patch {2}, key sha1 {3}" -f $bi.rollback_index, $bi.props['com.android.build.boot.os_version'], $bi.props['com.android.build.boot.security_patch'], $bi.key_sha1) }
        $bh = Get-BootHeader (Join-Path $dir 'boot_b.img')
        $an['boot_b_header'] = $bh; $an['boot_b_avb'] = $bi; $an['vbmeta_b_chain_boot'] = $ch
    } else { Write-Dry "would check (PC): misc's boot command, vbmeta_b chains boot with key sha1 $FooterKeySha1, boot_b's AVB footer (rollback index, os_version, security_patch) and boot header" }
    # the boot loader: flags and sizes (read only)
    Write-Step 'Slot flags in the boot loader (adb reboot bootloader; fastboot getvar; read only)'
    Invoke-AdbCmd reboot bootloader | Out-Null
    if (-not (Wait-Fastboot 120)) { Stop-Run 'the boot loader''s fastboot did not appear within 2 minutes (if the tablet shows it: check the cable / driver)' }
    [void](Assert-Abl)
    Assert-PartSize 'boot_b' $BootBBytes
    Assert-UserdataSize $m
    $fa = Read-SlotFlags 'a'; $fb = Read-SlotFlags 'b'
    if ($Live) {
        if ($fb.successful -ne 'yes') { Write-Warn "slot-successful:b is '$($fb.successful)': boot LineageOS once fully, then run the backup again"; $checks++ }
        if ($fb.unbootable -ne 'no') { Write-Warn "slot-unbootable:b is '$($fb.unbootable)'"; $checks++ }
    } else { Write-Dry 'would require slot-successful:b = yes and slot-unbootable:b = no' }
    if ($Live) {
        $bm = [ordered]@{
            WARNING = 'PRIVATE. Partition copies of one tablet. Never upload or share this folder.'
            created = (Get-Date -Format s); script = "Install-Pad4Linux $ScriptVersion"; folder = $dir
            full_backup = [bool]$FullBackup; identity_ok = $true; checks_failed = $checks; bdaddr_saved = $bdSaved
            facts = $facts; abl = [ordered]@{ slot_a = $fa; slot_b = $fb }; analysis = $an; files = $rows
        }
        $bm | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $dir 'backup-manifest.json') -Encoding UTF8
        ($rows | ForEach-Object { '{0}  {1}' -f $_.sha256_pc, $_.file }) | Set-Content -LiteralPath (Join-Path $dir 'SHA256SUMS.txt') -Encoding ASCII
        Write-Ok "backup manifest: $(Join-Path $dir 'backup-manifest.json') (stays on this PC)"
    } else { Write-Dry "would write $dir\backup-manifest.json and SHA256SUMS.txt (local only)" }
    if (-not $StayInFastboot -or $checks -gt 0) { Invoke-Fb reboot | Out-Null; if ($Live) { Write-Ok 'fastboot reboot sent: back to Android' } }
    if ($checks -gt 0) { Stop-Run "$checks backup check(s) need attention (see WARN lines). Fix them and run the backup again; nothing was written." }
    Write-Ok 'BACKUP done: read only, nothing was written to the tablet. Copy the backup folder to a second disk now.'
}
function Get-BootBWant($bm) {
    $avb = Get-Field (Get-Field $bm 'analysis') 'boot_b_avb'
    $props = @{}
    $pp = Get-Field $avb 'props'
    if ($null -ne $pp) { foreach ($pr in $pp.PSObject.Properties) { $props[$pr.Name] = [string]$pr.Value } }
    return [pscustomobject]@{ rollback_index = [string](Get-Field $avb 'rollback_index'); props = $props; key_sha1 = $FooterKeySha1 }
}
function Invoke-Flash($m) {
    Write-Step 'Flash: the owner''s two writes - write 1 userdata, write 2 boot_b (each confirmed by you)'
    $dev = Get-Field $m 'device'
    $img = Get-Field $m 'image'
    $userdataBytes = (Get-Long (Get-Field $dev 'userdata_bytes'))
    # 1. the release may be written at all
    $blk = Get-ReleaseBlockers $m
    if ($blk.Count -gt 0) {
        foreach ($b in $blk) { Write-Log "  BLOCKED: $b" 'Red' }
        if ($Live) { Stop-Run 'this release is not cleared for flashing (see BLOCKED lines). Nothing was written.' 2 }
        Write-Dry 'a real run stops here; the steps below are shown for review only'
    }
    Assert-Tools
    # 2. today's backup with the undo file
    $bdir = Get-NewestBackup
    $bm = $null; $want = $null
    if ($null -eq $bdir) {
        if ($Live) { Stop-Run 'no backup found: run -Phase Backup -Execute first (it makes the undo file of write 2)' }
        Write-Dry "no backup in $BackupRoot yet: a real run needs today's -Phase Backup"
    } else {
        $bm = Read-BackupManifest $bdir
        Write-Ok "backup: $($bdir.FullName) (created $($bm.created))"
        if ([datetime]::Parse([string]$bm.created).Date -ne (Get-Date).Date) {
            $msg = 'the backup is not from today. Run -Phase Backup again today, just before write 1: it is the last time Android can be read.'
            if ($Live) { Stop-Run $msg } else { Write-Warn $msg }
        }
        if ([int]$bm.checks_failed -ne 0) { Stop-Run 'the backup recorded failed checks; run it again' }
        $script:undoPath = Assert-UndoFile $bdir $bm
        $want = Get-BootBWant $bm
    }
    # 3. the files
    Write-Step 'Files (SHA-256 checked right before use)'
    $script:imagePath = Test-ArtifactLocal $img 'image'
    if ($script:imagePath) {
        $unp = Get-SparseUnpacked $script:imagePath
        if ($unp -lt 0) { Stop-Run 'the image is not an Android sparse image' }
        $minU = Get-Long (Get-Field $img 'min_userdata_bytes')
        if ($minU -gt 0) {
            if ($unp -ne (Get-Long (Get-Field $img 'unpacked_size')) -or $unp -gt $minU) { Stop-Run ("the image unpacks to {0} bytes; manifest unpacked_size {1}, min_userdata_bytes {2}" -f $unp, (Get-Field $img 'unpacked_size'), $minU) }
            Write-Ok "sparse image unpacks to $unp bytes (a small generic image: it grows into userdata at the first boot)"
        } else {
            if ($unp -ne (Get-Long (Get-Field $img 'unpacked_size')) -or $unp -ne $userdataBytes) { Stop-Run ("the image unpacks to {0} bytes; manifest unpacked_size {1}, userdata {2}" -f $unp, (Get-Field $img 'unpacked_size'), $userdataBytes) }
            Write-Ok "sparse image unpacks to exactly the size of userdata ($unp bytes)"
        }
    } elseif ($Live) { Stop-Run 'the install image is not on disk with the manifest''s SHA-256: run -Phase Download -Execute' }
    $script:ubootPlainPath = Test-ArtifactLocal (Get-Field $m 'uboot_plain') 'uboot_plain'
    $plainSha = ''
    if ($script:ubootPlainPath) {
        $plainSha = Get-Sha $script:ubootPlainPath
        $kind = Get-UBootKind $script:ubootPlainPath
        if ($kind -ne 'install') { Stop-Run "uboot_plain is the '$kind' build; only the install build of U-Boot may be booted from / written to boot_b" }
        $uh = Get-BootHeader $script:ubootPlainPath
        Write-Ok ("uboot_plain: install build, header v{0}, os_version {1}, patch {2}" -f $uh.header, $uh.os_version, $uh.patch_level)
        if ($null -ne $bm) {
            $sh = Get-Field (Get-Field $bm 'analysis') 'boot_b_header'
            if ($null -ne $sh -and -not ($sh.os_version -eq '0.0.0' -and $sh.patch_level -eq '2000-00')) {
                if ($uh.header -ne $sh.header -or $uh.os_version -ne $sh.os_version -or $uh.patch_level -ne $sh.patch_level) { Stop-Run ("U-Boot header v{0} {1} {2} differs from this tablet's boot_b v{3} {4} {5}: a U-Boot built with your values is needed (check-header.py rule). Nothing was written." -f $uh.header, $uh.os_version, $uh.patch_level, $sh.header, $sh.os_version, $sh.patch_level) }
                Write-Ok 'boot header version, OS version and patch level match this tablet''s boot_b'
            }
        }
    } elseif ($Live) { Stop-Run 'uboot_plain not on disk with the manifest''s SHA-256: run -Phase Download -Execute' }
    else { $script:ubootPlainPath = Get-ArtifactPath (Get-Field $m 'uboot_plain'); Write-Dry "uboot_plain would be $script:ubootPlainPath" }
    if ($null -ne $bm) {
        $ch = @((Get-Field (Get-Field $bm 'analysis') 'vbmeta_b_chain_boot'))
        if ($ch.Count -ne 1 -or $ch[0].key_sha1 -ne $FooterKeySha1) { Stop-Run "vbmeta_b of this tablet does not chain boot with the AOSP test key: not the owner's proven case. Write 2 would leave ABL to refuse boot_b. Nothing was written." }
    }
    if ($script:ubootPlainPath -and $null -ne $want) { $script:ubootWritePath = Select-BootBImage $m $script:ubootPlainPath $plainSha $want }
    else { Write-Dry 'would choose the boot_b file: the release''s footered U-Boot if its footer matches this tablet''s boot_b (rollback index, os_version, security_patch, key), else a local footer with avbtool (the owner''s mk-footer.sh parameters)' }
    if ($Live -and -not $script:ubootWritePath) { Stop-Run 'no boot_b file for this tablet' }
    # 4. the tablet in the boot loader
    if ($Live) {
        Write-Log 'Put the tablet into the boot loader: switch it off, hold Volume Down + Power until the boot loader''s fastboot screen shows, connect USB to the PC''s own port.' 'Cyan'
        if (-not (Wait-Fastboot 300)) { Stop-Run 'no fastboot device within 5 minutes' }
    }
    [void](Assert-Abl)
    Assert-UserdataSize $m
    Assert-PartSize 'boot_b' $BootBBytes
    $f0 = Read-SlotFlags 'b'
    if ($Live -and ($f0.successful -ne 'yes' -or $f0.unbootable -ne 'no')) { Stop-Run "slot b must read successful=yes and unbootable=no before write 1 (found $($f0.successful) / $($f0.unbootable))" }
    # 5. WRITE 1
    Write-Step 'WRITE 1 of 2: the Fedora image into userdata'
    $isz = if ($script:imagePath) { (Get-Item -LiteralPath $script:imagePath).Length } else { (Get-Long (Get-Field $img 'size')) }
    $ish = ([string](Get-Field $img 'sha256')).ToLower()   # equal to the file's own hash when imagePath is set (Test-ArtifactLocal)
    Write-Log  '  +-----------------------------------------------------------------------------------------+' 'Yellow'
    Write-Log  '  | partition : userdata  (the ONLY partition of this write)' 'Yellow'
    Write-Log ("  | file      : {0}" -f $(if ($script:imagePath) { $script:imagePath } else { Join-Path $DlDir (Get-Field $img 'file') })) 'Yellow'
    Write-Log ("  | size      : {0} (sparse); unpacks to {1}" -f (Format-Size $isz), (Format-Size (Get-Long (Get-Field $img 'unpacked_size')))) 'Yellow'
    Write-Log ("  | SHA-256   : {0}" -f $ish) 'Yellow'
    Write-Log  '  | effect    : ERASES ALL ANDROID DATA (apps, photos, accounts). Android data cannot be backed up' 'Yellow'
    Write-Log  '  |             by this script: it is encrypted on the tablet. Copy your own files off first.' 'Yellow'
    Write-Log  '  +-----------------------------------------------------------------------------------------+' 'Yellow'
    Confirm-Typed 'Write 1 erases every Android file on the tablet.' $DataLossPhrase
    Confirm-Typed 'Confirm the partition of write 1 by typing its name.' 'userdata'
    if ($script:imagePath -and $Live) { if ((Get-Sha $script:imagePath) -ne $ish) { Stop-Run 'the image changed since it was checked' } }
    $imgArg = if ($script:imagePath) { $script:imagePath } else { Join-Path $DlDir (Get-Field $img 'file') }
    $script:armed = "flash userdata $imgArg"
    $out = Invoke-Fb flash userdata $imgArg
    if ($Live) {
        $j = $out -join ' | '
        if ($script:fbExit -ne 0 -or $j -match 'FAILED' -or $j -notmatch 'Finished') { Stop-Run 'write 1 did not finish. The boot loader is unaffected: stay in (or re-enter) fastboot and run -Phase Flash again (the same command from the start). Do nothing else.' }
        Write-Ok "write 1 done: $(@($out | Where-Object { $_ -match 'Finished' }) -join ' ')"
        Write-Log '  From now on: if Android starts and offers a factory reset, choose "Try again" or power off - NEVER the reset.' 'Yellow'
    }
    # 6. three tethered cold boots (RAM only)
    Write-Step 'Tethered boots: U-Boot from RAM (fastboot boot, nothing written) -> GRUB -> Fedora; three cold boots to the desktop'
    for ($i = 1; $i -le 3; $i++) {
        if ($i -gt 1) {
            Wait-Enter "Cold boot $i of 3: switch the tablet off (Fedora: power off), hold Volume Down + Power until the boot loader shows, connect USB, then press Enter."
            if ($Live -and -not (Wait-Fastboot 300)) { Stop-Run 'no fastboot device within 5 minutes' }
            [void](Assert-Abl)
            [void](Read-SlotFlags 'b')
        }
        $o = Invoke-Fb boot $script:ubootPlainPath
        if ($Live -and ($script:fbExit -ne 0 -or ($o -join ' ') -match 'FAILED')) { Stop-Run "the boot loader refused the RAM boot: $($o -join ' | '). Do not do write 2." }
        if ($i -eq 1) { Write-Log '  Expected: U-Boot''s text, GRUB''s menu (3 s), then Fedora''s first-boot setup. Create your user and password there (the image has no preset user).' 'Cyan' }
        if (-not (Confirm-YesNo "Cold boot ${i}: did Fedora reach the desktop?")) { Stop-Run 'Fedora did not reach the desktop: do NOT do write 2. Way back: README "Undo and return to stock".' }
    }
    # 7. WRITE 2
    Write-Step 'WRITE 2 of 2: U-Boot with its AVB footer into boot_b'
    Wait-Enter 'Switch the tablet off, hold Volume Down + Power until the boot loader shows, connect USB, then press Enter.'
    if ($Live -and -not (Wait-Fastboot 300)) { Stop-Run 'no fastboot device within 5 minutes' }
    [void](Assert-Abl)
    Assert-PartSize 'boot_b' $BootBBytes
    $f1 = Read-SlotFlags 'b'
    if ($Live -and ($f1.successful -ne 'yes' -or $f1.unbootable -ne 'no')) { Stop-Run "slot b must read successful=yes and unbootable=no before write 2 (found $($f1.successful) / $($f1.unbootable))" }
    $wsz = if ($script:ubootWritePath) { (Get-Item -LiteralPath $script:ubootWritePath).Length } else { $BootBBytes }
    $wsh = if ($script:ubootWritePath) { Get-Sha $script:ubootWritePath } else { '(chosen at run time)' }
    Write-Log  '  +-----------------------------------------------------------------------------------------+' 'Yellow'
    Write-Log  '  | partition : boot_b  (the ONLY partition of this write)' 'Yellow'
    Write-Log ("  | file      : {0}" -f $(if ($script:ubootWritePath) { $script:ubootWritePath } else { '<footered U-Boot for this tablet>' })) 'Yellow'
    Write-Log ("  | size      : {0}" -f (Format-Size $wsz)) 'Yellow'
    Write-Log ("  | SHA-256   : {0}" -f $wsh) 'Yellow'
    Write-Log ("  | undo file : {0}" -f $(if ($script:undoPath) { $script:undoPath } else { '<backup>\boot_b-before-install.img' })) 'Yellow'
    Write-Log  '  +-----------------------------------------------------------------------------------------+' 'Yellow'
    Confirm-Typed 'Confirm the partition of write 2 by typing its name.' 'boot_b'
    if ($script:ubootWritePath -and $Live) { if ((Get-Sha $script:ubootWritePath) -ne $wsh) { Stop-Run 'the boot_b file changed since it was checked' } }
    $wArg = if ($script:ubootWritePath) { $script:ubootWritePath } else { '<footered-u-boot>' }
    $script:armed = "flash boot_b $wArg"
    $out = Invoke-Fb flash boot_b $wArg
    if ($Live) {
        $j = $out -join ' | '
        if ($script:fbExit -ne 0 -or $j -match 'FAILED') { Stop-Run 'write 2 failed: stay in fastboot. Run -Phase UndoBootB (puts the saved boot_b back), or run -Phase Flash again later.' }
        Write-Ok 'write 2 done'
    }
    Write-Log '  The flags right after the flash, before any boot (expected: current b, successful no, unbootable no, retry count at its maximum, 7 on the owner''s tablet):'
    $f2 = Read-SlotFlags 'b'
    if ($Live -and ($f2.current -ne 'b' -or $f2.unbootable -eq 'yes')) { Write-Log 'UNDO NOW: current-slot is not b or slot b is unbootable. Run -Phase UndoBootB -Execute. No set_active.' 'Red'; exit 3 }
    if ($Live) {
        $rec = [ordered]@{ date = (Get-Date -Format s); release = (Get-Field $m 'release'); manifest_sha256 = $script:manifestSha; image_sha256 = $ish; boot_b_sha256 = $wsh; undo_file = $script:undoPath; flags_after_write2 = $f2 }
        $rec | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $WorkDir ('install-record-{0}.json' -f $script:stamp)) -Encoding UTF8
    }
    Wait-Enter 'Press Enter to restart the tablet (fastboot reboot).'
    Invoke-Fb reboot | Out-Null
    Write-Step 'After the install - read this now'
    Write-Log '  Every normal power-on of slot b counts down one try until slot b is marked "successful" (the owner''s tablet: 7 tries).' 'Yellow'
    if ((Get-Field $img 'slot_mark_automatic') -eq $true) {
        Write-Log '  This image marks the slot itself after the first good boot (iceland-slot-mark). Check it: Fedora terminal: journalctl -u iceland-slot-mark' 'Yellow'
    } else {
        Write-Log '  This image does NOT mark the slot by itself (the owner''s B149 image: iceland-slot-mark skips the loop root). At the FIRST Fedora boot,' 'Yellow'
        Write-Log '  open a terminal and run the owner''s manual mark of 14 Oct 2026 (README section 7):' 'Yellow'
        Write-Log '      B=$(readlink -f /dev/disk/by-partlabel/boot_b); L=/dev/$(lsblk -no PKNAME "$B")'
        Write-Log '      sudo dd if="$L" of=$HOME/boot-lun-gpt-head.bin bs=4096 count=6     # a read: copy of that LUN''s partition table'
        Write-Log '      sudo blockdev --setrw "$L"; sudo qbootctl -m; sudo blockdev --setro "$L"; sudo qbootctl'
    }
    Write-Log '  Then: power off, Volume Down + Power, connect USB and run:  -Phase VerifySlot -Execute   (slot-successful:b must read yes).' 'Yellow'
    Write-Log '  Undo of write 2 (two minutes, Fedora stays in userdata): -Phase UndoBootB -Execute' 'Yellow'
    Show-BdAddrHint
}
function Invoke-VerifySlot($m) {
    Write-Step 'Verify the slot flags after Fedora''s first boots (read only; INSTALL-GUIDE Part D step 3)'
    Assert-Tools
    $slot = Assert-Abl -AllowSlotA
    $f = Read-SlotFlags 'b'
    [void](Read-SlotFlags 'a')
    if (-not $Live) { Write-Dry "would apply the stop rule: current-slot a, unbootable yes or retry count <= $RetryStop with successful no -> UNDO NOW (-Phase UndoBootB)"; return }
    if ($f.successful -eq 'yes' -and $f.current -eq 'b' -and $f.unbootable -eq 'no') { Write-Ok 'slot b is marked successful: the boot loader no longer counts its boots. Install complete.'; Show-BdAddrHint; Invoke-Fb reboot | Out-Null; return }
    if ($slot -ne 'b' -or $f.unbootable -eq 'yes' -or $f.retry -le $RetryStop) {
        Write-Log ("UNDO NOW: current-slot {0}, unbootable {1}, retry-count {2}, successful {3} (stop rule: <= {4}). Run -Phase UndoBootB -Execute; no further boot, no set_active." -f $f.current, $f.unbootable, $f.retry, $f.successful, $RetryStop) 'Red'
        exit 3
    }
    Write-Warn ("slot b is NOT marked yet (retry count {0}). Boot Fedora and mark it (README section 7) before any other power cycle; a tethered RAM boot costs no try: -Phase Flash is not needed, use: fastboot boot <uboot_plain>." -f $f.retry)
    exit 3
}
function Invoke-UndoBootB($m) {
    Write-Step 'Undo of write 2: the saved boot_b back into boot_b (Fedora stays in userdata)'
    Assert-Tools
    $bdir = Get-NewestBackup
    if ($null -eq $bdir) { if ($Live) { Stop-Run 'no backup with boot_b-before-install.img found (-BackupDir <folder>)' }; Write-Dry "no backup in $BackupRoot"; $script:undoPath = '<backup>\boot_b-before-install.img' }
    else { $bm = Read-BackupManifest $bdir; $script:undoPath = Assert-UndoFile $bdir $bm }
    $slot = Assert-Abl -AllowSlotA
    if ($slot -ne 'b') { Write-Warn "current-slot reads '$slot': the flash still goes to boot_b (slot b's partition). Afterwards STOP and ask; no set_active." }
    Assert-PartSize 'boot_b' $BootBBytes
    $ush = if ($Live -or (Test-Path -LiteralPath $script:undoPath)) { Get-Sha $script:undoPath } else { '(from the backup)' }
    Write-Log  '  +-----------------------------------------------------------------------------------------+' 'Yellow'
    Write-Log  '  | partition : boot_b' 'Yellow'
    Write-Log ("  | file      : {0}" -f $script:undoPath) 'Yellow'
    Write-Log ("  | size      : {0}" -f (Format-Size $BootBBytes)) 'Yellow'
    Write-Log ("  | SHA-256   : {0}" -f $ush) 'Yellow'
    Write-Log  '  +-----------------------------------------------------------------------------------------+' 'Yellow'
    Confirm-Typed 'Confirm the partition of the undo by typing its name.' 'boot_b'
    $script:armed = "flash boot_b $($script:undoPath)"
    $out = Invoke-Fb flash boot_b $script:undoPath
    if ($Live -and ($script:fbExit -ne 0 -or ($out -join ' ') -match 'FAILED')) { Stop-Run 'the undo write failed: stay in fastboot, check cable and port, run -Phase UndoBootB again' }
    [void](Read-SlotFlags 'b')
    if ($Live -and $slot -ne 'b') { Stop-Run "boot_b restored, but current-slot was '$slot': do not reboot into anything else; ask for help (no set_active)" }
    Invoke-Fb reboot | Out-Null
    Write-Ok 'boot_b restored. Android starts (after write 1 without its data; never confirm a factory reset if you want to keep Fedora). Fedora can still be started tethered with fastboot boot <uboot_plain>.'
}
function Invoke-Inspect {
    if (-not $File -or -not (Test-Path -LiteralPath $File)) { Stop-Run '-Phase Inspect needs -File <local image file>' }
    Write-Step "Inspect $File (PC only, read only)"
    Write-Log ("  size {0}, SHA-256 {1}" -f (Get-Item -LiteralPath $File).Length, (Get-Sha $File))
    $h = Get-BootHeader $File
    if ($h) { Write-Log ("  boot image header v{0}, os_version {1}, patch level {2}, kernel {3} bytes; U-Boot build: {4}" -f $h.header, $h.os_version, $h.patch_level, $h.kernel_size, (Get-UBootKind $File)) }
    $u = Get-SparseUnpacked $File
    if ($u -ge 0) { Write-Log "  Android sparse image, unpacks to $u bytes" }
    $mc = Get-MiscCommand $File
    if ((Get-Item -LiteralPath $File).Length -eq 1048576) { Write-Log "  (as misc) boot command: '$mc'" }
    $i = Get-AvbInfo $File
    Write-AvbInfo $i
    if ($i -and $i.has_footer) { Write-Log ("  hash descriptor valid: {0}" -f (Test-AvbHash $File $i)) }
}

# =====================================================================================================================
# Main
Write-Log ("Install-Pad4Linux {0} - phase {1} - {2}" -f $ScriptVersion, $Phase, $(if ($Live) { 'EXECUTE' } else { 'DRY RUN (nothing is downloaded or sent to a tablet; add -Execute to run)' }))
Write-Log "work folder: $WorkDir   log: $script:logFile"
if ($Phase -eq 'Inspect') { Invoke-Inspect; exit 0 }
$m = Read-ReleaseManifest $Manifest
switch ($Phase) {
    'Preflight'  { Invoke-Preflight $m }
    'Download'   { Invoke-Download $m }
    'Backup'     { Invoke-Backup $m }
    'Flash'      { Invoke-Flash $m }
    'VerifySlot' { Invoke-VerifySlot $m }
    'UndoBootB'  { Invoke-UndoBootB $m }
    'All' {
        Invoke-Preflight $m
        Invoke-Download $m
        $blk = Get-ReleaseBlockers $m
        Invoke-Backup $m -StayInFastboot:($blk.Count -eq 0)
        if ($Live -and $blk.Count -gt 0) { Stop-Run 'backup done; this release is not cleared for flashing (Preflight lists why). Nothing was written.' 2 }
        Invoke-Flash $m
    }
}
Write-Log ''
Write-Log ("Done ({0}). Log: {1}" -f $(if ($Live) { 'executed' } else { 'dry run - nothing was downloaded or sent to a tablet' }), $script:logFile) 'Green'
exit 0
