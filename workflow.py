"""科学动画工作流入口。prepare 配音与对时；render 绘制；build 完整制作。"""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
from motion.speech import synthesize
from motion.timeline import align

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','render','build'])
    parser.add_argument('--project',type=Path,default=ROOT/'examples/transformer')
    parser.add_argument('--output',type=Path,help='默认写入 build/项目目录名')
    args = parser.parse_args()
    project = args.project.resolve()
    output = (args.output or ROOT/'build'/project.name).resolve()
    config = json.loads((project/'project.json').read_text(encoding='utf-8'))
    lines = [s.strip() for s in (project/'narration.txt').read_text(encoding='utf-8').splitlines() if s.strip()]
    output.mkdir(parents=True,exist_ok=True)
    if args.command in ['prepare','build']:
        asyncio.run(synthesize(lines,config,output))
        align(lines,config,output)
    if args.command in ['render','build']:
        spec = importlib.util.spec_from_file_location('example_renderer',project/'render.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.render(output)


if __name__ == '__main__':
    main()

