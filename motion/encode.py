"""把 RGB 帧和配音交给 FFmpeg；临时文件成功后才替换交付文件。"""
from pathlib import Path
import math
import shutil
import subprocess


def encode(frame, audio, destination, duration, fps=30, width=1080, height=1920):
    if shutil.which('ffmpeg') is None:
        raise RuntimeError('找不到 ffmpeg，请先安装并加入 PATH。')
    audio, destination = Path(audio), Path(destination)
    if not audio.is_file():
        raise RuntimeError('缺少配音文件，请先运行 prepare。')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.stem + '.partial.mp4')
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{width}x{height}', '-r', str(fps), '-i', 'pipe:0', '-i', str(audio),
           '-map', '0:v:0', '-map', '1:a:0', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9,apad',
           '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-threads', '6',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
           '-t', str(duration), '-movflags', '+faststart', str(temporary)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(math.ceil(duration*fps)):
            proc.stdin.write(frame(i/fps).tobytes())
            if i % (fps*10) == 0:
                print(f'动画合成 {i/fps:.0f} / {duration:.1f} 秒', flush=True)
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('FFmpeg 合成失败。')
        temporary.replace(destination)
    except BaseException:
        try:
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        if proc.poll() is None:
            proc.terminate()
        proc.wait()
        temporary.unlink(missing_ok=True)
        raise
    print(f'已生成 {duration:.1f} 秒视频：{destination.name}', flush=True)

