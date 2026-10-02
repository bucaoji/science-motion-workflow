"""把口播与词级事件对齐，生成场景、关键词锚点及 SRT 字幕。"""
from difflib import SequenceMatcher
import json
import math
import re
import shutil
import subprocess
import unicodedata
from .speech import speech_text


def normalized(s):
    return ''.join(c for c in s.lower() if not c.isspace() and unicodedata.category(c)[0] not in 'PS')


def timecode(t):
    value = round(t*1000)
    return f'{value//3600000:02}:{value//60000%60:02}:{value//1000%60:02},{value%1000:03}'


def align(lines, config, output):
    if shutil.which('ffprobe') is None:
        raise RuntimeError('找不到 ffprobe，请安装完整 FFmpeg。')
    record = json.loads((output/'speech.json').read_text(encoding='utf-8'))
    expected = speech_text(lines, config.get('pronunciation', {}))
    if record['request']['text'] != expected:
        raise RuntimeError('口播已经变化，请重新运行 prepare 生成对应配音。')
    if len(lines) != len(config['scenes']):
        raise RuntimeError('每行口播必须对应 project.json 中的一个场景。')
    chars = []
    for word in record['word_events']:
        value = normalized(word['text'])
        start, duration = word['offset']/1e7, word['duration']/1e7
        for i, c in enumerate(value):
            chars.append((c, start+duration*i/len(value), start+duration*(i+1)/len(value)))
    if not chars:
        raise RuntimeError('词级事件为空，无法生成时间轴。')
    wanted = ''.join(normalized(line) for line in lines)
    heard = ''.join(c[0] for c in chars)
    starts, ends = [None]*len(wanted), [None]*len(wanted)
    for kind,i1,i2,j1,j2 in SequenceMatcher(None,wanted,heard,autojunk=False).get_opcodes():
        if kind == 'equal':
            for k in range(i2-i1):
                starts[i1+k],ends[i1+k] = chars[j1+k][1:]
        elif i2 > i1:
            a = chars[j1][1] if j1<len(chars) else chars[-1][2]
            b = chars[j2-1][2] if j2>j1 else a
            for k in range(i2-i1):
                starts[i1+k] = a+(b-a)*k/(i2-i1)
                ends[i1+k] = a+(b-a)*(k+1)/(i2-i1)
    audio_duration = float(subprocess.check_output([
        'ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(output/'narration.mp3')], text=True))
    total = math.ceil((audio_duration+.9)*30)/30
    cues, subtitles, pos = [], [], 0
    for i,(line,scene) in enumerate(zip(lines,config['scenes'])):
        length = len(normalized(line))
        if not length:
            raise RuntimeError('场景口播不能为空或只有标点。')
        cue = dict(id=i,scene=scene['id'],text=line,start=starts[pos] if i else 0,anchors={})
        for term in scene.get('anchors', []):
            at = normalized(line).find(normalized(term))
            if at < 0:
                raise RuntimeError(f'场景 {scene["id"]} 的锚点不在对应口播中：{term}')
            cue['anchors'][term] = starts[pos+at]
        for part in re.findall(r'[^，。；？！：]+[，。；？！：]?',line):
            n = len(normalized(part))
            if n:
                subtitles.append(dict(text=part,start=starts[pos],end=ends[pos+n-1]+.15))
                pos += n
        cues.append(cue)
    for i,cue in enumerate(cues):
        cue['end'] = cues[i+1]['start'] if i+1<len(cues) else total
    for i,sub in enumerate(subtitles):
        sub['end'] = max(sub['start']+.06,min(sub['end'],subtitles[i+1]['start'] if i+1<len(subtitles) else audio_duration))
    data = dict(cues=cues,subtitles=subtitles,duration=total,audio_duration=audio_duration)
    (output/'timeline.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'subtitles.srt').write_text('\n\n'.join(
        f"{i+1}\n{timecode(s['start'])} --> {timecode(s['end'])}\n{s['text']}" for i,s in enumerate(subtitles))+'\n',encoding='utf-8')
    print(f'时间轴与字幕已生成，预计时长 {total:.1f} 秒。',flush=True)

