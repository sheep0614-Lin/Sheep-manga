#!/usr/bin/env python3
from pathlib import Path
import shutil
import re

root = Path("upstream")
src = root / "src/zh/happymh"
dst = root / "src/zh/hipmh"

if not src.exists():
    raise SystemExit("找不到 upstream Happymh module")

if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)

for p in dst.rglob("*"):
    if not p.is_file():
        continue
    if p.suffix not in {".kt", ".java", ".xml", ".gradle", ".kts"}:
        continue
    text = p.read_text(encoding="utf-8")
    text = text.replace("eu.kanade.tachiyomi.extension.zh.happymh",
                        "eu.kanade.tachiyomi.extension.zh.hipmh")
    text = text.replace("class Happymh", "class Hipmh")
    text = text.replace(".Happymh", ".Hipmh")
    text = text.replace("Happymh", "Hipmh")
    text = text.replace("嗨皮漫画", "嘻皮漫畫")
    text = text.replace("https://m.happymh.com", "https://m.hipmh.com")
    p.write_text(text, encoding="utf-8")

# rename main class file if present
old = dst / "src/eu/kanade/tachiyomi/extension/zh/happymh/Happymh.kt"
newdir = dst / "src/eu/kanade/tachiyomi/extension/zh/hipmh"
if old.exists():
    newdir.mkdir(parents=True, exist_ok=True)
    new = newdir / "Hipmh.kt"
    shutil.move(str(old), str(new))
    old_parent = old.parent
    try:
        old_parent.rmdir()
    except OSError:
        pass

# move any remaining package directory
oldpkg = dst / "src/eu/kanade/tachiyomi/extension/zh/happymh"
if oldpkg.exists():
    newdir.mkdir(parents=True, exist_ok=True)
    for f in oldpkg.iterdir():
        shutil.move(str(f), str(newdir / f.name))
    oldpkg.rmdir()

# ensure build.gradle ext class/name
bg = dst / "build.gradle"
if bg.exists():
    t = bg.read_text(encoding="utf-8")
    t = re.sub(r"extName\s*=\s*'[^']+'", "extName = 'Hipmh'", t)
    t = re.sub(r"extClass\s*=\s*'[^']+'", "extClass = '.Hipmh'", t)
    bg.write_text(t, encoding="utf-8")

print("Hipmh module prepared at", dst)
