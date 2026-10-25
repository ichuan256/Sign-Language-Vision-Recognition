param([switch]$Apply)
# FROZEN HISTORICAL RECORD: retained only for provenance; the old plan must not run.
throw 'FROZEN HISTORICAL RECORD: do not run this script or use -Apply. Use the current documented workflow.'
# Original historical body follows unchanged.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$prefix = $root.TrimEnd('\') + '\'
$evidence = Join-Path $root 'analysis/materials/20261025_cleanup'
$rows = @(Import-Csv -LiteralPath (Join-Path $evidence 'delete_plan.csv'))
$fixture = Join-Path $root 'data/legacy/material/你好/01_你好_示范01.mp4'
$allowedPrefixes = @('data/legacy/material/', 'video/.sd_cache/', 'video/inbox/lesson02_03_version_review_20261025/')
$allowedFiles = @('video/raw/BV1Hs411E7aP/BV1Hs411E7aP_p01_greetings.mp4', 'video/raw/BV1Hs411E7aP/BV1Hs411E7aP_p01_greetings.info.json', 'video/raw/BV1Hs411E7aP/BV1Hs411E7aP_p01_greetings-proj.llc')
if ($rows.Count -ne 317) { throw 'Unexpected plan size; this is a single approved cleanup batch' }
foreach ($row in $rows) {
    $relative = $row.path.Replace('\','/')
    $absolute = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $absolute.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or $absolute -eq $fixture -or $absolute -ne $row.absolute_path) { throw 'Unsafe or changed target path' }
    $allowed = $allowedFiles -contains $relative
    foreach ($candidate in $allowedPrefixes) { if ($relative.StartsWith($candidate, [StringComparison]::OrdinalIgnoreCase)) { $allowed = $true } }
    if (-not $allowed) { throw 'Target is not in this cleanup allowlist' }
    $item = Get-Item -LiteralPath $absolute -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Only regular files may be recycled' }
    $parent = $item.Directory
    while ($parent.FullName -ne $root) {
        if ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'A target parent is a link' }
        $parent = $parent.Parent
    }
    $digest = (Get-FileHash -LiteralPath $absolute -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -ne [long]$row.bytes -or $digest -ne $row.sha256) { throw 'Target changed since the plan was recorded' }
}
if (-not $Apply) { [pscustomobject]@{mode='dry-run'; files=$rows.Count; videos=315; bytes=286094154; destination='Windows Recycle Bin'} | ConvertTo-Json; return }
$journal = Join-Path $evidence 'recycled_files.jsonl'
if (Test-Path -LiteralPath $journal) { throw 'A journal already exists; inspect it rather than repeating operations' }
Add-Type -AssemblyName Microsoft.VisualBasic.Core
$parents = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$count = 0
foreach ($row in $rows) {
    # This is explicitly recoverable shell recycling, never permanent deletion.
    [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($row.absolute_path, [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin, [Microsoft.VisualBasic.FileIO.UICancelOption]::ThrowException)
    [IO.File]::AppendAllText($journal, (([pscustomobject]@{path=$row.path; bytes=[long]$row.bytes; sha256=$row.sha256; reason=$row.reason; status='sent_to_recycle_bin'} | ConvertTo-Json -Compress) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
    $parent = Split-Path $row.absolute_path -Parent
    foreach ($relativeBase in @('data/legacy/material','video/.sd_cache','video/inbox/lesson02_03_version_review_20261025')) {
        $boundary = [IO.Path]::GetFullPath((Join-Path $root $relativeBase))
        if ($parent -eq $boundary -or $parent.StartsWith($boundary+'\', [StringComparison]::OrdinalIgnoreCase)) {
            while ($parent -eq $boundary -or $parent.StartsWith($boundary+'\', [StringComparison]::OrdinalIgnoreCase)) {
                $null = $parents.Add($parent)
                if ($parent -eq $boundary) { break }
                $parent = Split-Path $parent -Parent
            }
            break
        }
    }
    $count++
    if ($count % 50 -eq 0) { Write-Output "Recycled $count/$($rows.Count) files" }
}
$directoryCount = 0
foreach ($directory in @($parents | Sort-Object Length -Descending)) {
    if (-not $directory.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe empty-directory path' }
    if ((Test-Path -LiteralPath $directory -PathType Container) -and @(Get-ChildItem -LiteralPath $directory -Force).Count -eq 0) {
        $item = Get-Item -LiteralPath $directory -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse recycling a linked directory' }
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($directory, [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin, [Microsoft.VisualBasic.FileIO.UICancelOption]::ThrowException)
        $directoryCount++
    }
}
[pscustomobject]@{recycled_files=$count; recycled_videos=315; bytes_removed_from_workspace=286094154; empty_directories_recycled=$directoryCount; recycle_bin_emptied=$false} | ConvertTo-Json
