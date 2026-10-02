"""安装本仓库的完整 Skill，仅复制列明的通用文件，不联网或安装依赖。"""
import argparse
from pathlib import Path
import shutil
import tempfile

NAME = "science-motion-workflow"
ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/project-contract.md",
    "scripts/install_skill.py",
    "README.md",
    "LICENSE",
    ".gitignore",
    "requirements.txt",
    "workflow.py",
    "motion/__init__.py",
    "motion/fonts.py",
    "motion/encode.py",
    "motion/speech.py",
    "motion/timeline.py",
    "examples/transformer/narration.txt",
    "examples/transformer/project.json",
    "examples/transformer/render.py",
    "docs/workflow.md",
    "docs/privacy.md",
)


def install(parent):
    destination = parent.expanduser().resolve() / NAME
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("已有同名 Skill，未覆盖。请先移走旧版本或指定其他安装目录。")
    for relative in FILES:
        source = ROOT / relative
        if not source.is_file() or not source.resolve().is_relative_to(ROOT):
            raise ValueError(f"安装源文件缺失或位于仓库以外：{relative}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".motion-install-", dir=destination.parent) as temporary:
        bundle = Path(temporary) / NAME
        bundle.mkdir()
        for relative in FILES:
            target = bundle / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("安装位置已被占用，未覆盖。")
        bundle.rename(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest", type=Path, default=Path.home() / ".agents" / "skills",
        help="Skill 的父目录，默认 ~/.agents/skills；会在其下创建 science-motion-workflow",
    )
    args = parser.parse_args()
    try:
        destination = install(args.dest)
    except (OSError, ValueError) as error:
        parser.exit(1, f"安装未完成：{error}\n")
    print(f"已安装：{destination}")
    print("在 Codex 中使用 $science-motion-workflow；若未出现，请重启 Codex。")


if __name__ == "__main__":
    main()
