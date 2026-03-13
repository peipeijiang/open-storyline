# OpenStoryline Standalone Pack

中文 | [English](#english)

一个可直接复用的 FireRed-OpenStoryline 自动化封装仓库。  
目标：别人 clone 后按 3 步即可跑通。

当前仓库已内置官方主项目目录 `FireRed-OpenStoryline/`（默认优先使用，不再依赖在线拉取）。

## 3 步快速开始

### 1) 初始化环境（克隆主项目 + 安装依赖）

```bash
bash scripts/bootstrap.sh /path/to/workspace storyline
```

### 2) 启动服务（Web 7860 + MCP 8001）

```bash
bash scripts/start_service.sh start /path/to/workspace/FireRed-OpenStoryline storyline
```

可选检查：

```bash
bash scripts/start_service.sh status /path/to/workspace/FireRed-OpenStoryline
```

### 3) 直接生成视频

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

## 配置项（必须）

请在 `FireRed-OpenStoryline/config.toml` 配置：

- `[llm]`: `model`, `base_url`, `api_key`
- `[vlm]`: `model`, `base_url`, `api_key`
- `[generate_voiceover.providers.minimax]`: `base_url`, `api_key`

可选：

- `[search_media]`: `pexels_api_key`（在线搜素材时使用）

仓库内 `config.public.toml` 是脱敏示例，不含真实密钥。

## 发布到 GitHub

```bash
bash scripts/publish_github.sh /path/to/this/repo your-org your-repo
```

---

## English

This repository is a standalone automation wrapper for FireRed-OpenStoryline.
Goal: anyone can clone and run with only 3 steps.

### 3-Step Quickstart

1. Bootstrap:

```bash
bash scripts/bootstrap.sh /path/to/workspace storyline
```

2. Start services:

```bash
bash scripts/start_service.sh start /path/to/workspace/FireRed-OpenStoryline storyline
```

3. Produce videos:

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


This repo includes the official main project under `FireRed-OpenStoryline/` and `bootstrap.sh` will use it first.
