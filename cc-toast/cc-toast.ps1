# cc-toast.ps1 — Claude Code 右下角置顶提醒 toast
# 用法: powershell -STA -File cc-toast.ps1 -Type permission -MessageB64 <b64> -CwdB64 <b64> -HostPid <pid>
param(
    [ValidateSet('permission','idle')][string]$Type = 'permission',
    [string]$MessageB64 = '-',
    [string]$CwdB64 = '-',
    [int]$HostPid = 0
)

$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    Add-Type -ReferencedAssemblies System.Windows.Forms -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class CCToastNative
{
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    // 数当前已有几个 toast（按窗口标题精确匹配），用于向上堆叠
    public static int CountWindowsTitled(string title)
    {
        int count = 0;
        EnumWindows(delegate(IntPtr h, IntPtr l) {
            if (!IsWindowVisible(h)) return true;
            StringBuilder sb = new StringBuilder(256);
            GetWindowText(h, sb, 256);
            if (sb.ToString() == title) count++;
            return true;
        }, IntPtr.Zero);
        return count;
    }

    // 兜底：按标题片段找可见顶层窗口
    public static IntPtr FindVisibleWindowContaining(string fragment)
    {
        IntPtr found = IntPtr.Zero;
        EnumWindows(delegate(IntPtr h, IntPtr l) {
            if (!IsWindowVisible(h)) return true;
            StringBuilder sb = new StringBuilder(512);
            GetWindowText(h, sb, 512);
            if (sb.Length > 0 && sb.ToString().IndexOf(fragment, StringComparison.OrdinalIgnoreCase) >= 0)
            {
                found = h;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    // 激活宿主窗口：空按键(Alt)解除前台锁定 -> 最小化则还原 -> 置前 -> 提升Z序
    public static void Activate(IntPtr hWnd)
    {
        keybd_event(0x12, 0, 0, UIntPtr.Zero); // Alt down
        keybd_event(0x12, 0, 2, UIntPtr.Zero); // Alt up (KEYEVENTF_KEYUP)
        if (IsIconic(hWnd)) ShowWindow(hWnd, 9); // SW_RESTORE
        SetForegroundWindow(hWnd);
        BringWindowToTop(hWnd);
    }
}

// 不抢焦点窗体：ShowWithoutActivation(Show时不激活) + WS_EX_NOACTIVATE(点击也不夺焦点)
public class NoActivateForm : System.Windows.Forms.Form
{
    protected override bool ShowWithoutActivation { get { return true; } }
    protected override System.Windows.Forms.CreateParams CreateParams
    {
        get
        {
            System.Windows.Forms.CreateParams cp = base.CreateParams;
            cp.ExStyle |= 0x08000000; // WS_EX_NOACTIVATE
            return cp;
        }
    }
}
'@

    function ConvertFrom-B64([string]$s) {
        if ([string]::IsNullOrEmpty($s) -or $s -eq '-') { return '' }
        try { return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s)) } catch { return '' }
    }
    $Message = ConvertFrom-B64 $MessageB64
    $Cwd     = ConvertFrom-B64 $CwdB64
    $proj = ''
    if ($Cwd) { $proj = Split-Path $Cwd -Leaf }

    if ($Type -eq 'permission') {
        $accent = [System.Drawing.Color]::FromArgb(230,126,34)   # 橙
        $titleText = 'Claude Code · 权限请求'
        if (-not $Message) { $Message = '有权限请求等待确认' }
        $lifeMs = 15000
    } else {
        $accent = [System.Drawing.Color]::FromArgb(46,204,113)   # 绿
        $titleText = 'Claude Code · 已完成'
        if (-not $Message) {
            if ($proj) { $Message = "$proj — 回复完成，等待输入" }
            else       { $Message = '回复完成，等待输入' }
        }
        $lifeMs = 6000
    }

    # 布局：主屏工作区右下角，已有 toast 时向上堆叠
    $w = 360; $h = 92; $margin = 12; $gap = 8
    $stackIndex = [CCToastNative]::CountWindowsTitled('CCToast')
    $wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    $x = $wa.Right  - $w - $margin
    $y = $wa.Bottom - $h - $margin - ($stackIndex * ($h + $gap))

    $form = New-Object NoActivateForm
    $form.Text            = 'CCToast'
    $form.FormBorderStyle = 'None'
    $form.StartPosition   = 'Manual'
    $form.ShowInTaskbar   = $false
    $form.TopMost         = $true
    $form.Size            = New-Object System.Drawing.Size($w, $h)
    $form.Location        = New-Object System.Drawing.Point($x, $y)
    $form.BackColor       = [System.Drawing.Color]::FromArgb(30,30,30)

    $bar = New-Object System.Windows.Forms.Panel
    $bar.BackColor = $accent
    $bar.Size      = New-Object System.Drawing.Size(4, $h)
    $bar.Location  = New-Object System.Drawing.Point(0, 0)
    $form.Controls.Add($bar)

    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Text      = $titleText
    $lblTitle.Font      = New-Object System.Drawing.Font('Microsoft YaHei UI', 10, [System.Drawing.FontStyle]::Bold)
    $lblTitle.ForeColor = [System.Drawing.Color]::White
    $lblTitle.Location  = New-Object System.Drawing.Point(16, 12)
    $lblTitle.Size      = New-Object System.Drawing.Size(($w - 28), 24)
    $form.Controls.Add($lblTitle)

    $lblMsg = New-Object System.Windows.Forms.Label
    $lblMsg.Text         = $Message
    $lblMsg.Font         = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
    $lblMsg.ForeColor    = [System.Drawing.Color]::FromArgb(190,190,190)
    $lblMsg.Location     = New-Object System.Drawing.Point(16, 40)
    $lblMsg.Size         = New-Object System.Drawing.Size(($w - 28), ($h - 52))
    $lblMsg.AutoEllipsis = $true
    $form.Controls.Add($lblMsg)

    # 点击：激活宿主窗口（PID -> 标题含项目名兜底 -> 放弃），然后关闭自己
    $script:form = $form
    $activate = {
        try {
            $hwnd = [IntPtr]::Zero
            if ($HostPid -gt 0) {
                $hp = Get-Process -Id $HostPid -ErrorAction SilentlyContinue
                if ($hp -and $hp.MainWindowHandle -ne [IntPtr]::Zero) { $hwnd = $hp.MainWindowHandle }
            }
            if ($hwnd -eq [IntPtr]::Zero -and $proj) {
                $hwnd = [CCToastNative]::FindVisibleWindowContaining($proj)
            }
            if ($hwnd -ne [IntPtr]::Zero) { [CCToastNative]::Activate($hwnd) }
        } catch {}
        $script:form.Close()
    }
    $form.Add_Click($activate)
    $lblTitle.Add_Click($activate)
    $lblMsg.Add_Click($activate)

    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = $lifeMs
    $script:timer = $timer
    $timer.Add_Tick({ $script:timer.Stop(); $script:form.Close() })
    $timer.Start()

    [System.Windows.Forms.Application]::Run($form)
    exit 0
} catch {
    exit 0   # 任何异常静默退出，绝不反向干扰 CC
}
