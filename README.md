# OpenStoryline Standalone Pack

This repository is a standalone automation wrapper for FireRed-OpenStoryline.
It contains end-to-end setup, run, batch production, and GitHub release scripts so others can clone and use it directly.

## 1. Bootstrap Environment

```bash
bash scripts/bootstrap.sh /path/to/workspace storyline
```

What it does:
- Clone upstream repo (`https://github.com/FireRedTeam/FireRed-OpenStoryline.git` @ `main`)
- Create/activate conda env
- Install dependencies and resources

## 2. Start Service

```bash
bash scripts/start_service.sh start /path/to/workspace/FireRed-OpenStoryline storyline
```

Check status:

```bash
bash scripts/start_service.sh status /path/to/workspace/FireRed-OpenStoryline
```

## 3. Run Headless Workflow

```bash
bash scripts/run_workflow.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --media /path/a.mp4 /path/b.mp4 \
  --instruction "Create a 30s video, English female voiceover, no subtitles, no BGM."
```

## 4. Run Instruction Batch

```bash
bash scripts/run_batch.sh \
  /path/to/workspace/FireRed-OpenStoryline \
  --instruction "Create 10 product videos, English female voiceover, no subtitles, no BGM" \
  --count 10 \
  --duration 30
```

## 5. Publish to GitHub

```bash
bash scripts/publish_github.sh /path/to/this/repo your-org your-repo
```

If `gh` CLI is installed and authenticated, the script can create remote automatically.
