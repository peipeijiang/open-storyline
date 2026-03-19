# Open Storyline

中文 | [English](#english)

一个面向 OpenStoryline 工作流的可发布 macOS 桌面应用与独立运行仓库。

你可以按两种方式使用它：

- 桌面 App：直接下载 `.dmg` / `.zip`，安装后用图形界面导入素材、填写提示词、生成视频。
- 脚本模式：clone 仓库后，用内置脚本启动 FireRed-OpenStoryline 服务并批量跑工作流。

## 下载桌面 App

Release 页面：

- [OpenStoryline Studio Releases](https://github.com/peipeijiang/open-storyline/releases)

当前提供的 macOS Apple Silicon 安装包：

- `OpenStoryline-Studio-*-arm64.dmg`
- `OpenStoryline-Studio-*-arm64.zip`

说明：

- 当前发布包面向 macOS arm64。
- App 已内置 `FireRed-OpenStoryline/` 后端目录，不需要你再单独下载主项目。
- 首次启动如果被 macOS 拦截，请在“系统设置 -> 隐私与安全性”中允许打开。

## App 能做什么

- 导入图片和视频素材
- 用自然语言提示词驱动完整工作流
- 自动执行镜头理解、筛选、分组、文案、配音、时间线规划、渲染
- 输出单条或多条成片
- 在界面中查看执行轨迹、失败原因和导出路径

适合的提示词示例：

```text
生产5个25s视频，要求无背景音和字幕，配音为英文可爱女生，风格为tiktok带货风格
```

```text
Create 3 product videos, 20 seconds each, no subtitles, no BGM, cute English female voice, TikTok commerce style.
```

## App 使用方式

### 1. 下载并安装

从 Releases 页面下载最新的：

- `.dmg`：适合普通安装
- `.zip`：适合直接解压运行

### 2. 启动 App

打开 `OpenStoryline Studio.app`。

首次运行时，App 会自动尝试启动内置后端。

### 3. 配置模型与服务

在 App 左侧配置区填写：

- `LLM`：`model`、`base_url`、`api_key`
- `VLM`：`model`、`base_url`、`api_key`
- `TTS`：当前主要使用 `MiniMax`
- `Pexels API Key`：只有在需要在线搜素材时才需要

至少需要：

- 一个可用的 LLM
- 一个可用的 VLM
- 一个可用的 TTS 配置

### 4. 导入素材并执行

- 点击添加素材
- 输入提示词
- 直接执行

App 会通过 WebSocket 持续回传：

- 当前执行节点
- 工具进度
- 错误信息
- 导出视频路径

## 当前这个版本的重点修复

本仓库当前 Release 对以下问题做了增强：

- 更准确识别类似 `无背景音和字幕` 的提示词，不再漏判“无字幕”
- 更准确识别类似 `英文可爱女生` 的提示词，不再要求必须写成“英文女声”
- 对 `无字幕` 和 `无 BGM` 使用更强的时间线与渲染约束
- 配音时长更贴近最终画面时长，减少口播提前结束导致的长尾空镜
- 后端会把 `ExceptionGroup` 展开为更可读的真实错误信息

## App 常见问题

### 1. 打开后端失败

先检查本机环境是否满足：

- `python3`
- 可用的运行环境
- 模型接口地址和密钥填写正确

如果 App 启动后端失败，可查看：

- `~/Library/Logs/OpenStoryline Studio/backend.log`

### 2. 提示词写了“无字幕”，结果还有字幕

请先确认你使用的是最新 Release。旧版本对并列说法的识别较弱，比如：

- `无背景音和字幕`
- `不要背景音和字幕`

最新版本已经专门补过这类识别。

### 3. WebSocket 断开或会话过期

如果出现以下问题：

- `WebSocket 连接关闭(1006)`
- `会话已过期`
- `ExceptionGroup: unhandled errors in a TaskGroup`

请先升级到最新 Release。当前版本已经对这些错误提示做了更清晰的归因和更友好的前端展示。

## 仓库结构

```text
.
├── FireRed-OpenStoryline/   # 内置主项目后端
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

### 3. 直接跑工作流

单条生成：

```bash
bash scripts/run_workflow.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --media /path/a.mp4 /path/b.mp4 \
  --instruction "Create a 30s video, English female voiceover, no subtitles, no BGM."
```

批量生成：

```bash
bash scripts/run_batch.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --instruction "Create 10 product videos, English female voiceover, no subtitles, no BGM" \
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

仓库中的 `config.public.toml` 是脱敏示例，不包含真实密钥。

## 发布这个仓库到你自己的 GitHub

```bash
bash scripts/publish_github.sh /path/to/this/repo your-org your-repo
```

---

# English

Open Storyline is a standalone distribution repo for an OpenStoryline-based workflow, with a packaged macOS desktop app and script-based automation.

You can use it in two ways:

- Desktop App: download the release asset and run the GUI directly
- Script Mode: clone the repo and run the built-in FireRed-OpenStoryline workflow from shell scripts

## Download The Desktop App

Releases page:

- [OpenStoryline Studio Releases](https://github.com/peipeijiang/open-storyline/releases)

Current release assets:

- `OpenStoryline-Studio-*-arm64.dmg`
- `OpenStoryline-Studio-*-arm64.zip`

Notes:

- Current builds target macOS Apple Silicon.
- The packaged app already includes the `FireRed-OpenStoryline/` backend.
- If macOS blocks first launch, allow it in System Settings -> Privacy & Security.

## What The App Does

- Import image and video assets
- Drive the full workflow with natural-language prompts
- Run clip understanding, filtering, grouping, script generation, voiceover, timeline planning, and rendering
- Produce one or multiple final videos
- Show tool progress, failures, and output paths in the GUI

Example prompts:

```text
Create 3 product videos, 20 seconds each, no subtitles, no BGM, cute English female voice, TikTok commerce style.
```

## How To Use The App

### 1. Download And Install

From Releases, download either:

- `.dmg` for normal installation
- `.zip` for direct extraction and launch

### 2. Launch The App

Open `OpenStoryline Studio.app`.

The app will try to start its bundled backend automatically on first run.

### 3. Configure Models And Services

Fill these in the left configuration panel:

- `LLM`: `model`, `base_url`, `api_key`
- `VLM`: `model`, `base_url`, `api_key`
- `TTS`: currently mainly MiniMax
- `Pexels API Key`: only needed when searching remote media

At minimum you need:

- one working LLM
- one working VLM
- one working TTS provider

### 4. Import Assets And Run

- add media
- type your prompt
- run the workflow

The app streams back:

- active workflow node
- tool progress
- error messages
- exported video paths

## Key Fixes In Current Release

- better prompt parsing for phrases like `no background music and subtitles`
- better detection of prompts like `cute English girl voice`
- stronger subtitle-off and BGM-off enforcement
- voiceover duration fits the planned visual timeline more closely
- backend unwraps `ExceptionGroup` errors into clearer user-facing messages

## Common Issues

### Backend fails to start

Check your local environment and model configuration first.

Backend log path:

- `~/Library/Logs/OpenStoryline Studio/backend.log`

### Prompt says “no subtitles” but output still contains subtitles

Please update to the latest release first. Older builds were weaker at parsing combined phrases such as:

- `no background music and subtitles`
- `without BGM and subtitles`

### WebSocket closed or session expired

If you see errors such as:

- `WebSocket 1006`
- `session expired`
- `ExceptionGroup: unhandled errors in a TaskGroup`

please upgrade to the latest release first. Recent builds improve both recovery and user-facing error clarity.

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

### 3. Run workflow

```bash
bash scripts/run_workflow.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --media /path/a.mp4 /path/b.mp4 \
  --instruction "Create a 30s video, English female voiceover, no subtitles, no BGM."
```

Batch mode:

```bash
bash scripts/run_batch.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --instruction "Create 10 product videos, English female voiceover, no subtitles, no BGM" \
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
