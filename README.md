# Open Storyline

中文 | [English](#english)

Open Storyline 是一个面向视频生成工作流的可发布 macOS 桌面应用仓库。你可以直接下载安装 App，也可以用仓库里的脚本模式启动内置工作流。

## 下载

最新桌面版 Release：

- [OpenStoryline Studio v0.1.0](https://github.com/peipeijiang/open-storyline/releases/tag/v0.1.0)

当前已发布的 macOS Apple Silicon 安装包：

- `OpenStoryline-Studio-0.1.0-arm64.dmg`，`704,035,219` 字节
- `OpenStoryline-Studio-0.1.0-arm64.zip`，`693,827,018` 字节

说明：

- 当前安装包面向 macOS arm64。
- App 内已经包含 `FireRed-OpenStoryline` 后端运行目录，不需要再单独下载主项目。
- 如果首次启动被 macOS 拦截，请到“系统设置 -> 隐私与安全性”中允许打开。

## App 能做什么

- 导入本地图片和视频素材
- 用自然语言提示词驱动完整工作流
- 自动执行镜头理解、筛选、分组、文案、配音、时间线规划和渲染
- 输出单条或多条成片
- 在界面中查看执行进度、报错信息和导出路径

适合的提示词示例：

```text
生产3个25s视频，要求无背景音和字幕，配音为英文可爱女生，风格为tiktok带货风格
```

```text
Create 3 product videos, 25 seconds each, no subtitles, no background music, cute English female voice, TikTok commerce style.
```

## 快速开始

### 1. 下载并安装

从 Release 页面下载：

- `.dmg`：适合普通安装
- `.zip`：适合直接解压运行

### 2. 启动 App

打开 `OpenStoryline Studio.app`。

首次运行时，App 会自动尝试启动内置后端。

### 3. 配置模型

在左侧配置区填写：

- `LLM`：`model`、`base_url`、`api_key`
- `VLM`：`model`、`base_url`、`api_key`
- `TTS`：当前主要使用 `MiniMax`
- `Pexels API Key`：只有需要联网搜素材时才需要

至少需要：

- 一个可用的 LLM
- 一个可用的 VLM
- 一个可用的 TTS 配置

### 4. 添加素材并执行

- 点击右上角添加素材
- 输入提示词
- 直接执行工作流

App 会持续显示：

- 当前执行节点
- 工具进度
- 错误信息
- 导出视频路径

## v0.1.0 重点修复

2026 年 3 月 20 日同步的 `v0.1.0` 桌面版包含以下修复：

- 同一会话里重复上传素材时，新素材会替换旧素材，不再持续累计重复素材
- 右上角素材数量标记支持悬停查看当前素材列表
- App 重启后恢复会话时，不再复用已过期的远端附件绑定
- `generate_script` 默认回退路径不再返回空结果
- 脚本时长校验改为尽量继续执行，避免因为拟合不够严而直接中断整条流程
- 英文配音更贴近镜头时长，减少最后一句没有说完或明显留白的情况

## 常见问题

### 1. 打开 App 后是空白页

请优先升级到最新 Release。旧版本在前端初始化和会话恢复失败时，空白页问题更明显。

### 2. 新建会话后提示“会话已过期”

请优先升级到最新 Release。当前版本已经避免在会话恢复时继续引用过期附件。

### 3. 明明写了“无字幕”，结果还是出了字幕

请尽量把约束直接写在同一句提示词里，例如：

```text
生产3个25s视频，要求无背景音和字幕，配音为英文可爱女生，风格为tiktok带货风格
```

如果仍然出现偏差，请先确认你使用的是最新 Release。

### 4. WebSocket 断开或报 `1006`

这类错误通常和后端异常、配置错误或网络中断有关。请先检查模型配置，再查看后端日志：

- `~/Library/Logs/openstoryline-app/OpenStoryline Studio/backend.log`

### 5. 提示“创建会话失败: 500”

这通常和模型配置、后端启动状态或节点异常有关。先检查：

- `LLM` / `VLM` / `TTS` 的 `base_url`、`model`、`api_key`
- 后端是否已经成功启动
- 后端日志里是否有真实报错堆栈

## 仓库结构

```text
.
├── FireRed-OpenStoryline/   # 内置后端项目
├── scripts/                 # 启动、发布、运行脚本
├── tools/                   # 工作流辅助脚本
├── config.public.toml       # 脱敏配置示例
└── README.md
```

## 脚本模式

如果你不想使用桌面 App，也可以直接用脚本模式。

### 1. 初始化环境

```bash
bash scripts/bootstrap.sh /path/to/workspace storyline
```

### 2. 启动服务

```bash
bash scripts/start_service.sh start /path/to/workspace/FireRed-OpenStoryline storyline
```

可选检查：

```bash
bash scripts/start_service.sh status /path/to/workspace/FireRed-OpenStoryline
```

### 3. 跑工作流

单条生成：

```bash
bash scripts/run_workflow.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --media /path/a.mp4 /path/b.mp4 \
  --instruction "Create a 30s video, English female voiceover, no subtitles, no background music."
```

批量生成：

```bash
bash scripts/run_batch.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --instruction "Create 10 product videos, English female voiceover, no subtitles, no background music" \
  --count 10 \
  --duration 30
```

## 配置说明

请在 `FireRed-OpenStoryline/config.toml` 中配置真实参数：

- `[llm]`: `model`, `base_url`, `api_key`
- `[vlm]`: `model`, `base_url`, `api_key`
- `[generate_voiceover.providers.minimax]`: `base_url`, `api_key`

可选：

- `[search_media]`: `pexels_api_key`

`config.public.toml` 是脱敏示例，不包含真实密钥。

---

# English

Open Storyline is a distributable macOS desktop app repo for an OpenStoryline-based video workflow. You can either download the packaged app or run the built-in scripts directly.

## Download

Latest desktop release:

- [OpenStoryline Studio v0.1.0](https://github.com/peipeijiang/open-storyline/releases/tag/v0.1.0)

Current macOS Apple Silicon assets:

- `OpenStoryline-Studio-0.1.0-arm64.dmg`, `704,035,219` bytes
- `OpenStoryline-Studio-0.1.0-arm64.zip`, `693,827,018` bytes

Notes:

- Current builds target macOS arm64.
- The packaged app already includes the `FireRed-OpenStoryline` backend runtime.
- If macOS blocks first launch, allow it in System Settings -> Privacy & Security.

## What The App Does

- Import local image and video assets
- Run the workflow through natural-language prompts
- Execute clip understanding, filtering, grouping, script generation, voiceover, timeline planning, and rendering
- Produce one or multiple final videos
- Show progress, errors, and export paths in the GUI

Example prompts:

```text
Create 3 product videos, 25 seconds each, no subtitles, no background music, cute English female voice, TikTok commerce style.
```

## Quick Start

### 1. Download and install

From the release page, download either:

- `.dmg` for standard installation
- `.zip` for direct extraction and launch

### 2. Launch the app

Open `OpenStoryline Studio.app`.

On first launch, the app will try to start its bundled backend automatically.

### 3. Configure models

Fill these in on the left configuration panel:

- `LLM`: `model`, `base_url`, `api_key`
- `VLM`: `model`, `base_url`, `api_key`
- `TTS`: currently mainly `MiniMax`
- `Pexels API Key`: only needed for remote media search

At minimum you need:

- one working LLM
- one working VLM
- one working TTS provider

### 4. Add media and run

- add media from the top right
- type your prompt
- run the workflow

The app continuously reports:

- active workflow node
- tool progress
- error details
- exported video paths

## Key Fixes In v0.1.0

The desktop build synced on March 20, 2026 includes:

- re-uploading materials in the same conversation now replaces old materials instead of accumulating duplicates
- the top-right material count badge now shows the current material list on hover
- session restore no longer reuses expired remote attachment bindings after restart
- the `generate_script` default fallback no longer returns empty output
- script timing validation now prefers best-effort continuation instead of failing the whole run
- English voiceover fitting is closer to the planned visual duration, reducing unfinished last lines and long silent tails

## Common Issues

### Blank page after launch

Please update to the latest release first. Older builds were more fragile during app initialization and session restore.

### Session expired on a new conversation

Please update to the latest release first. Recent builds avoid reusing expired attachment bindings during restore.

### Prompt says “no subtitles” but subtitles still appear

Keep the constraints explicit in a single prompt, for example:

```text
Create 3 product videos, 25 seconds each, no subtitles, no background music, cute English female voice, TikTok commerce style.
```

If the result still drifts, make sure you are on the latest release.

### WebSocket closed with `1006`

This is usually caused by backend exceptions, invalid model settings, or transient connectivity issues. Check backend logs first:

- `~/Library/Logs/openstoryline-app/OpenStoryline Studio/backend.log`

### `500` when creating a session

This is usually related to model config, backend startup failure, or a workflow node crash. Check:

- `base_url`, `model`, and `api_key` for `LLM`, `VLM`, and `TTS`
- whether the backend started successfully
- the backend log for the real stack trace

## Repository Layout

```text
.
├── FireRed-OpenStoryline/
├── scripts/
├── tools/
├── config.public.toml
└── README.md
```

## Script Mode

### 1. Bootstrap

```bash
bash scripts/bootstrap.sh /path/to/workspace storyline
```

### 2. Start services

```bash
bash scripts/start_service.sh start /path/to/workspace/FireRed-OpenStoryline storyline
```

Optional status check:

```bash
bash scripts/start_service.sh status /path/to/workspace/FireRed-OpenStoryline
```

### 3. Run workflow

```bash
bash scripts/run_workflow.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --media /path/a.mp4 /path/b.mp4 \
  --instruction "Create a 30s video, English female voiceover, no subtitles, no background music."
```

Batch mode:

```bash
bash scripts/run_batch.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --instruction "Create 10 product videos, English female voiceover, no subtitles, no background music" \
  --count 10 \
  --duration 30
```

## Configuration

Set real values in `FireRed-OpenStoryline/config.toml`:

- `[llm]`: `model`, `base_url`, `api_key`
- `[vlm]`: `model`, `base_url`, `api_key`
- `[generate_voiceover.providers.minimax]`: `base_url`, `api_key`

Optional:

- `[search_media]`: `pexels_api_key`

`config.public.toml` is sanitized and contains no real secrets.
