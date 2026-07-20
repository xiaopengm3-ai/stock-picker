# cc-toast-hook.ps1 — Claude Code hook 入口
# settings.json 中配置: powershell.exe ... -File cc-toast-hook.ps1 -Type permission|idle
# stdin 收到 CC 的 hook JSON（含 message/cwd），解析后分离启动 cc-toast.ps1，立即返回不阻塞 CC
param(
    [ValidateSet('permission','idle')][string]$Type = 'permission'
)

try {
    $raw = [Console]::In.ReadToEnd()
    $msg = ''; $cwd = ''
    if ($raw) {
        try {
            $data = $raw | ConvertFrom-Json
            if ($data.message) { $msg = [string]$data.message }
            if ($data.cwd)     { $cwd = [string]$data.cwd }
        } catch {}
    }

    # 顺父进程链回溯，找第一个有主窗口句柄的祖先作为宿主（不写死应用名，
    # 兼容 VS Code / Cursor / Windsurf / Trae / Windows Terminal 等）
    $hostProcId = 0
    try {
        $current = $PID
        for ($i = 0; $i -lt 15; $i++) {
            $wp = Get-CimInstance Win32_Process -Filter "ProcessId = $current" -ErrorAction SilentlyContinue
            if (-not $wp -or -not $wp.ParentProcessId) { break }
            $parentId = [int]$wp.ParentProcessId
            $pp = Get-Process -Id $parentId -ErrorAction SilentlyContinue
            if ($pp -and $pp.MainWindowHandle -ne [IntPtr]::Zero) { $hostProcId = $parentId; break }
            $current = $parentId
        }
    } catch {}

    function To-B64([string]$s) {
        if ([string]::IsNullOrEmpty($s)) { return '-' }
        return [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($s))
    }

    $toast = Join-Path $PSScriptRoot 'cc-toast.ps1'
    $argList = @(
        '-NoProfile','-ExecutionPolicy','Bypass','-STA','-WindowStyle','Hidden',
        '-File', "`"$toast`"",
        '-Type', $Type,
        '-MessageB64', (To-B64 $msg),
        '-CwdB64', (To-B64 $cwd),
        '-HostPid', $hostProcId
    )
    Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -WindowStyle Hidden
} catch {}
exit 0
