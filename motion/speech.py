"""整段微软在线配音与词级时间点；结果相同则复用已有声音。"""
import asyncio
import json


def speech_text(lines, replacements):
    text = ''.join(lines)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


async def synthesize(lines, config, output):
    text = speech_text(lines, config.get('pronunciation', {}))
    request = dict(text=text, voice=config.get('voice', 'zh-CN-XiaoxiaoNeural'),
                   rate=config.get('rate', '+0%'))
    audio_path, events_path = output/'narration.mp3', output/'speech.json'
    if audio_path.is_file() and events_path.is_file():
        previous = json.loads(events_path.read_text(encoding='utf-8'))
        if previous.get('request') == request and previous.get('word_events'):
            print('口播和音色未变，复用已有配音。', flush=True)
            return
    import edge_tts
    for attempt in range(3):
        audio, events = bytearray(), []
        try:
            stream = edge_tts.Communicate(text, request['voice'], rate=request['rate'], boundary='WordBoundary')
            async for chunk in stream.stream():
                if chunk['type'] == 'audio':
                    audio.extend(chunk['data'])
                elif chunk['type'] == 'WordBoundary':
                    events.append({key: chunk[key] for key in ('text', 'offset', 'duration')})
            if not audio or not events:
                raise RuntimeError('语音服务没有返回完整的声音或词级时间点。')
            output.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(audio)
            events_path.write_text(json.dumps(dict(request=request, word_events=events), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            print('整段配音及词级时间点已生成。', flush=True)
            return
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(2*(attempt+1))
