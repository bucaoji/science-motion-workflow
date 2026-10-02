"""使用本机字体或显式配置的字体，不下载、不分发字体文件。"""
from functools import lru_cache
from pathlib import Path
import os
from PIL import ImageFont


def choose_font(env, candidates):
    configured = os.environ.get(env)
    if configured:
        file = Path(configured).expanduser()
        if not file.is_file():
            raise RuntimeError(f'{env} 指定的字体文件不存在。')
        return file
    for candidate in candidates:
        file = Path(candidate)
        if file.is_file():
            return file
    return None


@lru_cache(None)
def paths():
    root = Path(__file__).resolve().parents[1]
    windows_fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    regular = choose_font('SCIENCE_MOTION_FONT', [
        root / 'fonts/NotoSansCJKsc-Regular.otf',
        root / 'fonts/NotoSansSC-Regular.ttf',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        windows_fonts / 'msyh.ttc',
    ])
    if regular is None:
        raise RuntimeError('找不到中文字体。请安装 Noto Sans CJK，或设置 SCIENCE_MOTION_FONT。')
    bold = choose_font('SCIENCE_MOTION_FONT_BOLD', [
        root / 'fonts/NotoSansCJKsc-Bold.otf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
        windows_fonts / 'msyhbd.ttc',
    ])
    latin = choose_font('SCIENCE_MOTION_LATIN_FONT', [
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        windows_fonts / 'arial.ttf',
    ])
    latin_bold = choose_font('SCIENCE_MOTION_LATIN_BOLD_FONT', [
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        windows_fonts / 'arialbd.ttf',
    ])
    return regular, bold, latin, latin_bold


@lru_cache(None)
def font(size, bold=False, latin=False):
    regular, heavy, latin_regular, latin_heavy = paths()
    file = (latin_heavy if bold else latin_regular) if latin else None
    file = file or (heavy if bold else regular) or regular
    # Noto 的 TTC 中简体中文为第 2 个索引；Hiragino 粗体为第 1 个索引。
    index = 2 if file.name.startswith('NotoSansCJK') and file.suffix.lower() == '.ttc' else 0
    if bold and file.name == 'Hiragino Sans GB.ttc':
        index = 1
    return ImageFont.truetype(str(file), size, index=index)

