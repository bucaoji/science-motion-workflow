# 科学精神 · 动画视频工作流

把科学讲解写成可运行的动画：口播 → 配音与词级时间点 → 字幕和场景时间轴 → 逐帧绘图 → 竖屏视频。

这里提供一套可复用的制作方法、一个可安装的 **Codex Skill**，以及一个完整的 **Transformer** 示例。示例使用 Python 绘制词块、连线、权重和生成过程，使用微软“晓晓”配音，最终导出 1080×1920、30fps、H.264＋AAC 的 MP4。

每个新选题仍需要设计自己的场景。当前示例的画面和部分布局文字围绕 Transformer 编写；更换口播时，要同步修改相应场景。

## 实际工具

| 环节 | 工具与作用 |
|---|---|
| 内容与动画代码 | 可以与 AI 编程助手协作，确定要解释的关系并编写场景 |
| 配音 | 社区项目 `edge-tts` 调用微软 Edge 在线语音服务 |
| 字幕与时间轴 | 从语音服务返回的词级时间点对齐口播、场景和关键词 |
| 画面 | Pillow 绘制每一帧，NumPy 辅助计算坐标与背景 |
| 合成 | FFmpeg 合并画面和声音，统一音量，输出 MP4 |

配音需要联网，会把口播文本发送给微软在线语音服务。绘图和视频合成在本机运行。本仓库没有 AI 账号、公众号、邮件或平台发布接口。

## 作为 Skill 使用

Skill 名称是 `science-motion-workflow`。根目录的 [SKILL.md](SKILL.md) 告诉 AI 怎样写口播、设计新主题的场景、调用制作程序并交付视频。它带有完整运行代码，无需 MCP 服务。

取得本仓库后，在仓库根目录运行：

```sh
python3 scripts/install_skill.py
```

Windows 可将 `python3` 换成 `python`。安装器只使用 Python 标准库，默认安装到 `~/.agents/skills/science-motion-workflow`；它仅复制明确列出的 Skill、代码、文档和示例，不复制 `.git`、本机环境、字体、成片或额外文件，也不联网。已存在同名 Skill 时会停止，不覆盖旧版本。

安装后，在 Codex 中输入：

```text
请使用 $science-motion-workflow，解释“缓存为什么能加速”。
先写约 60 秒的口播给我审阅，暂时不要制作视频。
```

口播满意后继续：

```text
按这版口播制作 1080×1920 的连续动画视频，使用微软晓晓配音。
交付 MP4、字幕和可编辑源文件。
```

也可以直接要求制作完整视频。Skill 会在当前任务目录建立新项目，为新主题编写画面，再调用本仓库的配音和合成程序。安装 Skill 不等于安装运行依赖：首次生成视频仍需要下文的 Python 包、FFmpeg 和中文字体，可让 Codex 根据 README 帮你准备。

如果只想在某个项目中使用，从那个项目的根目录运行 `python /path/to/science-motion-workflow/scripts/install_skill.py --dest .agents/skills`，将示例路径换成实际下载位置。Codex 的本地 Skill 目录与发现方式见 [官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)；安装后未出现时，重启 Codex。

仓库保持私有时，只有获得访问权限的人才能从 GitHub 下载。无需提供作者的账号、语音密钥或任何平台登录信息。不要把访问令牌写入安装提示词。

## 直接运行项目

需要 Python 3.12 或更新版本、包含 `ffmpeg` 和 `ffprobe` 的 FFmpeg 安装，以及一款支持中文的字体。

FFmpeg 下载及平台安装入口：https://ffmpeg.org/download.html

在仓库根目录创建 Python 环境并安装依赖：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows 使用 `python -m venv .venv`，随后在 PowerShell 运行 `.venv\Scripts\Activate.ps1`。

直接制作 Transformer 示例：

```sh
python workflow.py build
```

输出位于 `build/transformer/`：

- `transformer.mp4`：最终竖屏视频，字幕已绘制在画面内。
- `narration.mp3`：配音。
- `speech.json`：配音参数、实际送读文本及词级时间点，用于复用声音和对时。
- `timeline.json`：场景、关键词和字幕的时间轴。
- `subtitles.srt`：可单独导入剪辑工具的字幕。

`build/` 已加入忽略规则，不随代码提交。

## 分步制作

```sh
# 生成配音、字幕和时间轴；口播及音色未变时复用已有声音。
python workflow.py prepare

# 只重新绘制动画，使用现有声音和时间轴。
python workflow.py render

# 指定另一个示例或输出位置。
python workflow.py build --project examples/transformer --output build/my-video
```

`render` 用于只改画面的情况。修改口播、音色或关键词锚点后，先运行 `prepare`，或直接运行 `build`。

## 字体

程序会尝试使用本机常见中文字体。也可自行取得 [Noto Sans CJK](https://github.com/notofonts/noto-cjk) 字体，在本机 `fonts/` 下放置 `NotoSansCJKsc-Regular.otf` 和 `NotoSansCJKsc-Bold.otf`。

自定义字体通过环境变量指定：

```sh
export SCIENCE_MOTION_FONT="./fonts/NotoSansCJKsc-Regular.otf"
export SCIENCE_MOTION_FONT_BOLD="./fonts/NotoSansCJKsc-Bold.otf"
```

PowerShell 示例：`$env:SCIENCE_MOTION_FONT = ".\fonts\NotoSansCJKsc-Regular.otf"`。

可选变量：`SCIENCE_MOTION_LATIN_FONT`、`SCIENCE_MOTION_LATIN_BOLD_FONT`。本仓库不分发系统字体；不同字体的字宽可能影响布局，换字体时应在设计中留出空间。

## 文件结构

```text
SKILL.md                    AI 制作指引与适用范围
agents/openai.yaml          Skill 的显示名称与默认提示词
references/project-contract.md  新主题项目与绘图接口
scripts/install_skill.py    仅复制指定文件的本地安装器
workflow.py                 制作入口
motion/
  speech.py                 整段配音与声音复用
  timeline.py               词级对齐、场景时间轴与 SRT
  fonts.py                  本机字体选择
  encode.py                 FFmpeg 合成
examples/transformer/
  narration.txt             一行对应一个场景的口播
  project.json              音色、读法、场景及关键词
  render.py                 本篇动画的具体画面
docs/
  workflow.md               怎样把一句解释变成一个画面动作
  privacy.md                运行与分享时的数据边界
```

继续阅读：[制作方法](docs/workflow.md) · [隐私与分享范围](docs/privacy.md)。

## 示例的解释边界

“只靠注意力”描述跨位置的信息交互方式；Transformer 还包含前馈网络、位置表示等模块。双向自注意力的全连接示意不代表自回归解码器可以读取未来词。权重、分词和连线都是讲解示意，不是对某个模型的实测可视化。生成部分描述标准自回归过程。

原论文：Vaswani et al., *Attention Is All You Need*, 2017。
https://arxiv.org/abs/1706.03762v7

语音工具：https://github.com/rany2/edge-tts

## 许可

沿用本仓库的 [Apache-2.0 许可证](LICENSE)。外部依赖、语音服务和自行安装的字体，遵循各自的许可或使用条件。
