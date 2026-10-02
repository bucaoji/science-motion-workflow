# 项目与绘图接口

所有程序均包含在 Skill 根目录。制作新主题时，在用户任务目录创建独立项目，通过根目录的 `workflow.py` 加载；无需修改或复制 `motion/`。

## 口播和场景配置

`narration.txt` 使用 UTF-8，一行对应一个场景，不空行占位。例如：

```text
缓存会保留一份已经取得的数据。
再次访问时，如果命中缓存，就能直接取出这份数据。
```

对应 `project.json`：

```json
{
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "pronunciation": {},
  "scenes": [
    {"id": "store", "anchors": ["保留"]},
    {"id": "reuse", "anchors": ["命中缓存", "直接取出"]}
  ]
}
```

`scenes` 与非空口播行数、顺序一一对应。`id` 使用各不相同的简短名称。`anchors` 中的词应直接出现在对应口播行中；对齐时忽略大小写、标点与空白，并取第一次出现的位置。需要两个不同时间点时，选用不重复的完整词组。

`pronunciation` 为送读时的全局字符串替换，例如 `{"GPU": "G P U"}`。画面字幕仍使用原口播。程序将服务返回的时间点映射回原文，替换段中的细分时间可能是插值。替换应简短，避免互相覆盖。

## prepare 产生的数据

输出目录由 `--output` 指定，包含：

- `narration.mp3`：实际配音。
- `speech.json`：语音请求参数及服务返回的词级事件；相同请求可以复用。
- `timeline.json`：绘图使用的秒级时间轴。
- `subtitles.srt`：与配音对齐的字幕。

`timeline.json` 结构示意如下，数值只是说明字段：

```json
{
  "cues": [
    {
      "id": 0,
      "scene": "store",
      "text": "缓存会保留一份已经取得的数据。",
      "start": 0.0,
      "end": 3.2,
      "anchors": {"保留": 0.8}
    }
  ],
  "subtitles": [
    {"text": "缓存会保留一份已经取得的数据。", "start": 0.2, "end": 3.0}
  ],
  "duration": 7.0,
  "audio_duration": 6.1
}
```

`start`、`end` 和锚点均为全片绝对秒数。首场从 0 开始，各场衔接；末场包含短暂声音尾留白。渲染用 `duration`，不要自行再加一遍尾留白。

## render.py 接口

实现 `render(output)`，其中 `output` 是包含上述结果的 `pathlib.Path`。不要在模块导入时开始渲染。将自己的素材相对于 `Path(__file__).resolve().parent` 定位。

可用公共组件：

```python
from motion.fonts import font
from motion.encode import encode

title_font = font(64, bold=True)
subtitle_font = font(52)
latin_font = font(48, latin=True)
```

制作入口会提供这些导入路径。运行 `workflow.py render --project ... --output ...`，不要要求用户直接运行自定义 `render.py`。

绘图接口如下；`draw_scene` 与 `draw_subtitles` 需要在本篇项目中实际实现：

```python
import json
from PIL import Image, ImageDraw
from motion.encode import encode

def render(output):
    timeline = json.loads((output / "timeline.json").read_text(encoding="utf-8"))

    def frame(t):
        canvas = Image.new("RGB", (1080, 1920), "#101725")
        draw = ImageDraw.Draw(canvas)
        cue = next(
            (c for c in timeline["cues"] if c["start"] <= t < c["end"]),
            timeline["cues"][-1],
        )
        draw_scene(canvas, draw, cue, t)
        active = [s for s in timeline["subtitles"] if s["start"] <= t < s["end"]]
        draw_subtitles(draw, active)
        return canvas

    encode(frame, output / "narration.mp3", output / "video.mp4", timeline["duration"])
```

`frame(t)` 必须返回 1080×1920 的 RGB Pillow Image。RGBA 素材先合成到 RGB 画布。`encode` 流式接收帧，输出 H.264、AAC、yuv420p 与 faststart MP4；不需要保存所有帧到磁盘。

`draw_scene` 按 `cue["scene"]` 分发到不同场景。使用 `t - cue["start"]` 计算场景内进度；需要口播同步的变化使用 `t - cue["anchors"][关键词]`。将进度限制在 0–1，再用缓动改变位置、连接、比例或透明度。对象应保持可追踪，不能只让文字淡入淡出。

`draw_subtitles` 根据字体实际宽度换行，通常居中放在底部操作区上方，使用高对比文字或底板。不要把 SRT 当作已经烧录进画面的字幕；最终帧里必须绘制它们。

## 调用示意

以实际 Python 环境替换 `python`，以绝对路径替换以下占位符：

```text
python <SKILL_DIR>/workflow.py build --project <PROJECT_DIR> --output <OUTPUT_DIR>
```

始终显式提供 `--project` 和 `--output`，避免误渲染默认 Transformer 示例或把成片写入安装目录。

只改场景代码用 `render`。改动了口播、声音参数或场景锚点用 `prepare` 再 `render`，或直接 `build`。配音缓存由实际送读文本、音色和语速决定；仅修改锚点不会强制重新请求相同声音。
