# CC Toast — Claude Code 权限/空闲提醒弹窗 设计文档

日期：2026-07-20

## 目标

Claude Code 弹出权限请求、或回复完成等待输入时，在 Windows 屏幕右下角显示一个置顶（所有应用最上层）的 toast 提醒，点击可跳回 CC 所在窗口。纯提醒，不做批准/拒绝交互。

## 架构

**Hook 触发即弃脚本**：CC hook 事件触发时 `Start-Process` 启动一个 PowerShell + WinForms 弹窗脚本，显示后自动消失。零常驻进程、零状态。

```
Claude Code
  ├─ Notification hook (权限请求) ──┐
  └─ Stop hook (回复完成/空闲)  ────┤
                                    ▼
              powershell -WindowStyle Hidden -File cc-toast.ps1
                                    ▼
                    右下角置顶 toast（自动消失）
                       点击 → 激活 CC 宿主窗口
```

## 组件

### 1. 触发层 — hooks 配置

位置：`C:\Users\Administrator\.claude\settings.json`（合并到现有配置，不动 env/permissions/model 等已有字段）。

- `Notification` 事件：权限请求提醒（type=permission）
- `Stop` 事件：空闲/完成提醒（type=idle）

Hook stdin 收到 JSON（含 `message`、`cwd`、`session_id`），由包装命令读入并传给弹窗脚本。Hook timeout 5s；脚本用 `Start-Process` 分离启动弹窗后立即返回，不阻塞 CC。

### 2. 展示层 — cc-toast.ps1

位置：`e:\claude code files\cc-toast\cc-toast.ps1`（不占 C 盘），单文件，仅依赖 Windows 自带 .NET WinForms。

- 无边框窗口，`TopMost = $true`
- 位置：主屏 `WorkingArea` 右下角，边距 12px；已有 toast 时向上堆叠（按现存 toast 窗口数偏移 Y）
- 不抢焦点（双保险）：重写 `ShowWithoutActivation`（Show 时不激活）+ `CreateParams` 加 `WS_EX_NOACTIVATE` 扩展样式（点击时也不夺焦点——焦点只该给宿主窗口，toast 永远不拿）
- 样式：深色背景，左侧彩色竖条 — 权限=橙色，空闲=绿色；标题 "Claude Code"，正文 = 权限内容 / 项目目录名
- 自动消失：权限类 15s，空闲类 6s
- 参数：`-Type permission|idle -Message <文本> -Cwd <项目路径> -HostPid <宿主进程PID>`

### 3. 跳转层 — 点击行为

点击 toast → 关闭自身 + 激活 CC 宿主窗口：

1. **宿主识别**：hook 触发时顺父进程链回溯，取第一个 `MainWindowHandle != 0` 的祖先进程为宿主。不写死任何应用名，天然兼容 VS Code、Cursor、Windsurf、Trae、Windows Terminal 等
2. **激活序列**：`ShowWindow(SW_RESTORE)` → `SetForegroundWindow` → `BringWindowToTop`。为绕过 Windows 前台锁定（后台进程调用 `SetForegroundWindow` 可能只闪任务栏不置前），置前前先发一个空按键（`keybd_event` 模拟 Alt）解锁
3. **兜底**：PID/句柄失效时，遍历可见顶层窗口找标题含项目目录名（取自 `-Cwd`）的窗口；再失败则仅关闭 toast

## 错误处理

- 脚本整体 try/catch，任何异常静默退出，绝不反向干扰 CC
- Hook 配 timeout，防止脚本挂死阻塞会话
- 多显示器：只用主屏 WorkingArea（简单可预期）

## 测试

1. 手动：`powershell -File cc-toast.ps1 -Type permission -Message "test"` — 验证位置/置顶/样式/自动消失
2. 堆叠：连开 3 个验证向上堆叠不重叠
3. 点击跳转：分别从 VS Code、Windows Terminal 启动，验证点击后宿主窗口置前（含最小化状态恢复）
4. 端到端：配置 hooks 后触发真实权限请求与 Stop 事件

## 非目标（YAGNI）

- 不做弹窗内批准/拒绝（不碰 PreToolUse 决策流）
- 不做常驻托盘、消息队列、历史记录
- 不做多显示器智能定位、勿扰时段
