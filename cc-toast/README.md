# CC Toast

Claude Code 权限请求 / 回复完成时，在 Windows 屏幕右下角弹出置顶、不抢焦点的 toast 提醒，点击跳回 CC 宿主窗口。纯 PowerShell + WinForms，零依赖安装。

## 组成

- `cc-toast.ps1` — 展示层：右下角置顶 toast 窗口（`ShowWithoutActivation` + `WS_EX_NOACTIVATE` 双保险不抢焦点），多个时向上堆叠，权限类 15s / 空闲类 6s 后自动消失。点击激活 CC 宿主窗口。
- `cc-toast-hook.ps1` — 触发层：作为 CC hook 入口，读 stdin JSON（UTF-8）、顺父进程链回溯找宿主窗口 PID、Base64 编码参数后分离启动展示层，立即返回不阻塞 CC。

## 安装

hook 配置在 `C:\Users\Administrator\.claude\settings.json`（在 git 仓库之外），在顶层 JSON 中加入 `hooks` 键（与 `env`、`permissions` 平级）：

```json
"hooks": {
  "Notification": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"e:\\claude code files\\cc-toast\\cc-toast-hook.ps1\" -Type permission",
          "timeout": 10
        }
      ]
    }
  ],
  "Stop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"e:\\claude code files\\cc-toast\\cc-toast-hook.ps1\" -Type idle",
          "timeout": 10
        }
      ]
    }
  ]
}
```

改完 `settings.json` 后需**重启 Claude Code 会话**才生效（hooks 在会话启动时快照）。

- `Notification` 事件：权限请求，以及 CC 空闲 60s 的等待输入提醒 → 橙色 toast。
- `Stop` 事件：回复完成 → 绿色 toast。

## 手动测试

```powershell
# 权限样式（橙，15s）
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("Claude 请求执行 Bash 命令"))
Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-STA','-File','"e:\claude code files\cc-toast\cc-toast.ps1"','-Type','permission','-MessageB64',$b64)

# 空闲样式（绿，6s）+ 堆叠
1..3 | ForEach-Object { Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-STA','-File','"e:\claude code files\cc-toast\cc-toast.ps1"','-Type','idle'); Start-Sleep -Milliseconds 800 }
```

模拟 hook 输入（端到端）：

```powershell
'{"cwd":"e:\\claude code files","message":"Claude needs your permission to use Bash"}' | powershell.exe -NoProfile -ExecutionPolicy Bypass -File "e:\claude code files\cc-toast\cc-toast-hook.ps1" -Type permission
```

## 注意

- `.ps1` 文件含中文，必须保存为 **UTF-8 with BOM**，否则 Windows PowerShell 5.1 解析器会因编码报错。
- 宿主窗口识别不写死应用名，回溯父进程链取第一个有主窗口的祖先，兼容 VS Code / Cursor / Windsurf / Trae / Windows Terminal 等。
