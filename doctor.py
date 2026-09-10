# -*- coding: utf-8 -*-
"""环境自检:缺什么、怎么装,直接打印可复制的命令。

agent 起手先跑这个;输出为纯 ASCII 状态行,便于解析。
退出码 0=READY。
"""
import importlib.util
import platform
import shutil
import subprocess
import sys


def _has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def main() -> bool:
    osname = platform.system()
    print(f"平台: {osname} | Python {sys.version.split()[0]}")
    ok = True

    if sys.version_info < (3, 9):
        print("[FAIL] 需要 Python >= 3.9")
        ok = False
    else:
        print("[OK] Python 版本")

    for mod in ("graphviz", "jsonschema"):
        if _has(mod):
            print(f"[OK] python 包 {mod}")
        else:
            print(f"[FAIL] 缺 python 包 {mod} —— 运行: pip install -r requirements.txt")
            ok = False

    if shutil.which("dot"):
        print("[OK] graphviz 可执行 dot")
    else:
        ok = False
        print("[FAIL] 缺 graphviz(dot)—— 按平台安装其一:")
        for plat, cmd in (("Linux", "sudo apt-get install -y graphviz"),
                          ("Windows", "winget install Graphviz.Graphviz"),
                          ("macOS", "brew install graphviz")):
            print(f"        {plat}: {cmd}")

    if osname == "Linux":
        try:
            out = subprocess.run(["fc-list"], capture_output=True, text=True,
                                 timeout=15).stdout
            if "CJK" in out:
                print("[OK] 中文字体(CJK)")
            else:
                print("[FAIL] 无 CJK 字体(中文会显示成方框)—— "
                      "运行: sudo apt-get install -y fonts-noto-cjk")
                ok = False
        except Exception:
            print("[WARN] 无法执行 fc-list,跳过字体检查")
    else:
        print("[INFO] 非 Linux,跳过字体检查(Windows/macOS 自带中文字体)")

    print("\nRESULT:", "READY" if ok else "NOT READY")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
