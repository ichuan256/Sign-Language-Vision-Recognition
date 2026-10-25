param([switch]$Apply)
# FROZEN HISTORICAL RECORD: retained only for provenance; the old plan must not run.
throw 'FROZEN HISTORICAL RECORD: do not run this script or use -Apply. Use the current documented workflow.'
# Original historical body follows unchanged.
$ErrorActionPreference = 'Stop'
$rootPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$rootPrefix = $rootPath.TrimEnd('\') + '\'
$evidencePath = Join-Path $rootPath 'analysis/materials/20261025_organization'
function WorkspacePath([string]$relative) {
    $absolute = [IO.Path]::GetFullPath((Join-Path $rootPath $relative))
    if (-not $absolute.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Path outside workspace: $relative" }
    return $absolute
}
function Digest([string]$path) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function SaveJson([string]$path, $value) {
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 15), [Text.UTF8Encoding]::new($false))
}
$copyPlan = @(Import-Csv -LiteralPath (WorkspacePath 'analysis/materials/20261025_111356/verified_relocation_plan.csv'))
if ($copyPlan.Count -ne 85) { throw 'Expected exactly 85 verified P08 copies' }
$moves = [Collections.Generic.List[object]]::new()
function PlanMove([string]$source, [string]$target) {
    $sourcePath = WorkspacePath $source
    $targetPath = WorkspacePath $target
    if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Missing source: $source" }
    $item = Get-Item -LiteralPath $sourcePath -Force
    if ($item.LinkType) { throw "Refuse moving a link as an operation root: $source" }
    if (Test-Path -LiteralPath $targetPath) { throw "Destination already exists: $target" }
    $moves.Add([pscustomobject]@{source=$source; target=$target; kind=if($item.PSIsContainer){'directory'}else{'file'}})
}
foreach ($row in $copyPlan) {
    $source = WorkspacePath $row.source
    $target = WorkspacePath $row.proposed_target
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing P08 source: $($row.source)" }
    if ((Digest $source) -ne $row.sha256) { throw "P08 source SHA mismatch: $($row.source)" }
    if (Test-Path -LiteralPath $target) { throw "P08 target exists: $($row.proposed_target)" }
}
$flatParents = @($copyPlan | ForEach-Object { (Split-Path $_.source -Parent).Replace('\','/') } | Sort-Object -Unique)
foreach ($relative in $flatParents) {
    $name = Split-Path $relative -Leaf
    PlanMove $relative "video/archive/import_P08_flat_20261025/$name"
}
PlanMove 'video/done/manifest_P08_reviewed_20261022.csv' 'video/archive/import_P08_flat_20261025/manifest_P08_reviewed_20261022.csv'
foreach ($file in @(Get-ChildItem -LiteralPath (WorkspacePath 'video') -File | Where-Object {$_.Name -like 'BV1Hs411E7aP*'})) {
    PlanMove "video/$($file.Name)" "video/raw/BV1Hs411E7aP/$($file.Name)"
}
$nlFiles = @(Get-ChildItem -LiteralPath (WorkspacePath 'video') -File | Where-Object {$_.Name -match '^P(?:10|[1-9])-.*\.mp4$'})
if ($nlFiles.Count -ne 10) { throw 'Expected 10 NL source videos' }
foreach ($file in $nlFiles) { PlanMove "video/$($file.Name)" "video/raw/NL_tutorial/$($file.Name)" }
PlanMove 'material_fullframe_20261021' 'video/archive/material_fullframe_20261021'
PlanMove 'material_fullframe_第二三课分类_20261023' 'video/inbox/lesson02_03_version_review_20261025'
PlanMove '训练视频' 'video/archive/work_batches_20261020'
PlanMove '_inspect' '_tmp/material_inspection_legacy_20261025'
PlanMove '工具/losslesscut' 'tools/portable/losslesscut'
PlanMove '剪裁方法' '_tmp/root_cache_archive_20261025/剪裁方法'
PlanMove '__pycache__' '_tmp/root_cache_archive_20261025/__pycache__'
if (-not $Apply) {
    [pscustomobject]@{mode='dry-run'; copies=$copyPlan.Count; moves=$moves.Count; evidence=$evidencePath} | ConvertTo-Json
    return
}
if (Test-Path -LiteralPath $evidencePath) { throw 'Evidence directory exists; inspect prior journal instead of rerunning' }
$null = New-Item -ItemType Directory -Path $evidencePath
$backup = WorkspacePath '_tmp/workspace_organization_backup_20261025'
if (Test-Path -LiteralPath $backup) { throw 'Backup already exists' }
$null = New-Item -ItemType Directory -Path $backup
$head = (& git -C $rootPath rev-parse HEAD).Trim()
$archive = Join-Path $backup 'tracked_HEAD.zip'
& git -C $rootPath archive --format=zip --output $archive HEAD
if ($LASTEXITCODE -ne 0) { throw 'Git control snapshot failed' }
foreach ($relative in @('video/sources.json','video/README.md','.git/info/exclude','.gitignore')) {
    $source = WorkspacePath $relative
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        $destination = Join-Path $backup ($relative.Replace('/','__').Replace('\','__'))
        Copy-Item -LiteralPath $source -Destination $destination
    }
}
SaveJson (Join-Path $evidencePath 'before_state.json') ([pscustomobject]@{head=$head; timestamp=(Get-Date -Format o); status=@(& git -C $rootPath status --short); backup=$backup})
SaveJson (Join-Path $evidencePath 'operations_plan.json') ([pscustomobject]@{copies=$copyPlan; moves=$moves})
$journal = Join-Path $evidencePath 'operations.jsonl'
function Journal($entry) { [IO.File]::AppendAllText($journal, (($entry | ConvertTo-Json -Depth 6 -Compress) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false)) }
foreach ($row in $copyPlan) {
    $source = WorkspacePath $row.source
    $target = WorkspacePath $row.proposed_target
    $null = [IO.Directory]::CreateDirectory((Split-Path $target -Parent))
    [IO.File]::Copy($source, $target, $false)
    if ((Digest $target) -ne $row.sha256) { throw "Copied file SHA mismatch: $($row.proposed_target)" }
    Journal ([pscustomobject]@{operation='copy'; source=$row.source; target=$row.proposed_target; sha256=$row.sha256; status='verified'})
}
foreach ($move in $moves) {
    $source = WorkspacePath $move.source
    $target = WorkspacePath $move.target
    if (Test-Path -LiteralPath $target) { throw "Destination appeared: $($move.target)" }
    $null = [IO.Directory]::CreateDirectory((Split-Path $target -Parent))
    if ($move.kind -eq 'directory') {
        try { [IO.Directory]::Move($source, $target) }
        catch {
            if ($move.source -ne '工具/losslesscut') { throw }
            # A running/package-managed resource can prevent rename. Preserve
            # the original and copy into the expected portable tool location.
            $null = [IO.Directory]::CreateDirectory($target)
            foreach ($file in @(Get-ChildItem -LiteralPath $source -File -Force -Recurse)) {
                $relative = [IO.Path]::GetRelativePath($source, $file.FullName)
                $destination = [IO.Path]::GetFullPath((Join-Path $target $relative))
                if (-not $destination.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Tool target outside workspace' }
                $null = [IO.Directory]::CreateDirectory((Split-Path $destination -Parent))
                [IO.File]::Copy($file.FullName, $destination, $false)
                if ((Digest $destination) -ne (Digest $file.FullName)) { throw 'Tool copy SHA mismatch' }
            }
            Journal ([pscustomobject]@{operation='copy_tree'; source=$move.source; target=$move.target; status='verified_original_preserved'})
            continue
        }
    } else { [IO.File]::Move($source, $target) }
    Journal ([pscustomobject]@{operation='move'; source=$move.source; target=$move.target; kind=$move.kind; status='moved'})
}
# Preserve the now-empty old tool container without deleting it.
$oldTool = WorkspacePath '工具'
if ((Test-Path -LiteralPath $oldTool) -and @(Get-ChildItem -LiteralPath $oldTool -Force).Count -eq 0) {
    $target = WorkspacePath '_tmp/root_cache_archive_20261025/工具'
    Move-Item -LiteralPath $oldTool -Destination $target
    Journal ([pscustomobject]@{operation='move'; source='工具'; target='_tmp/root_cache_archive_20261025/工具'; kind='empty_directory'; status='moved'})
}
# Update this live source index; preserve its original copy in the backup.
$sourceIndex = WorkspacePath 'video/sources.json'
$sources = @(Get-Content -LiteralPath $sourceIndex -Raw | ConvertFrom-Json)
foreach ($source in $sources) {
    $filename = Split-Path $source.file -Leaf
    $relative = "raw/BV1Hs411E7aP/$filename"
    $absolute = WorkspacePath "video/$relative"
    if ((Digest $absolute) -ne $source.sha256) { throw "Source index SHA mismatch: $filename" }
    $source.file = $relative
}
SaveJson $sourceIndex $sources
Journal ([pscustomobject]@{operation='update_index'; target='video/sources.json'; rows=$sources.Count; status='sha_verified'})
[pscustomobject]@{copies=$copyPlan.Count; moves=$moves.Count; source_index_rows=$sources.Count; evidence=$evidencePath; backup=$backup} | ConvertTo-Json
