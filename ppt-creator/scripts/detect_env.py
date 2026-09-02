#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPT Creator 环境检测脚本

检测技能目录路径、Python 环境和 python-pptx 可用性，
输出 JSON 格式结果供 LLM 决策路线选择。

用法：
    python detect_env.py
    python detect_env.py --skill-dir "C:\\path\\to\\ppt-creator"

输出示例：
    {
        "skill_dir": "C:\\Users\\xxx\\.useio\\skills\\ppt-creator",
        "system_python": {
            "available": true,
            "version": "3.12.0",
            "executable": "C:\\Python312\\python.exe",
            "is_store_stub": false
        },
        "system_pptx_available": false,
        "system_pptx_version": null,
        "embed_python_available": true,
        "embed_python_path": "C:\\Users\\xxx\\.useio\\skills\\ppt-creator\\vendor\\python\\python.exe",
        "embed_python_test": "Python 3.12.0",
        "embed_pptx_available": true,
        "libs_available": true,
        "libs_path": "C:\\Users\\xxx\\.useio\\skills\\ppt-creator\\vendor\\libs",
        "ppt_templates": {
            "available": true,
            "dir": "C:\\Users\\xxx\\.useio\\data\\ppt-templates",
            "templates": [{"name": "report.pptx", "path": "C:\\...\\report.pptx", "size": 102400}]
        },
        "recommended_route": "B"
    }
"""

import os
import sys
import json
import argparse
import subprocess


def get_skill_dir(arg_skill_dir=None):
    """获取技能目录绝对路径

    优先使用命令行 --skill-dir 参数，其次通过 __file__ 自探测。
    """
    if arg_skill_dir:
        return os.path.abspath(arg_skill_dir)
    # 脚本位于 scripts/detect_env.py，技能目录为上一级
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    return skill_dir


def get_app_root(skill_dir):
    """从 skill_dir 推算 app_root

    skill_dir = {appRoot}/skills/ppt-creator
    app_root = skill_dir 向上两级
    """
    # skills/ppt-creator -> skills -> app_root
    return os.path.dirname(os.path.dirname(skill_dir))


def _get_python_version(exe_path):
    """通过子进程获取指定 Python 可执行文件的版本"""
    try:
        result = subprocess.run(
            [exe_path, "--version"],
            capture_output=True, text=True, timeout=10
        )
        # Python 3.x 输出 "Python 3.12.0" 到 stdout
        output = (result.stdout or result.stderr or "").strip()
        return output.replace("Python ", "") if output else "unknown"
    except Exception:
        return "unknown"


def check_system_python(skill_dir):
    """检测系统 Python 环境（排除嵌入式 Python 和 Windows Store 桩）

    判断逻辑：当前运行的 Python 可执行文件路径是否在技能目录内。
    若在技能目录内，说明是嵌入式 Python，不算系统 Python。
    """
    embed_python_path = os.path.join(skill_dir, "vendor", "python", "python.exe")
    embed_norm = os.path.normpath(embed_python_path).lower()

    current_exe = sys.executable
    is_embed = os.path.normpath(current_exe).lower() == embed_norm

    if not is_embed:
        # 当前运行的是系统 Python，直接返回自身信息（数据准确）
        # 注意：能通过 run_command 执行 detect_env.py 的系统 Python 必然不是 Store 桩
        # （Store 桩会弹出应用商店而非执行脚本）
        return {
            "available": True,
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": current_exe,
            "is_store_stub": False
        }

    # 当前是嵌入式 Python，需探测系统是否有真实 Python
    try:
        result = subprocess.run(
            ["where", "python"],
            capture_output=True, text=True, timeout=5,
            shell=True
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                line_norm = os.path.normpath(line).lower()
                # 排除嵌入式 Python 路径
                if line_norm == embed_norm:
                    continue
                # 排除 Windows Store 桩（路径含 windowsapps，不区分大小写）
                if "windowsapps" in line_norm:
                    continue
                # 找到真实系统 Python，获取其版本
                ver = _get_python_version(line)
                return {
                    "available": True,
                    "version": ver,
                    "executable": line,
                    "is_store_stub": False
                }
            # where 有结果但全是桩或嵌入式
            return {
                "available": False,
                "version": None,
                "executable": None,
                "is_store_stub": True
            }
        return {
            "available": False,
            "version": None,
            "executable": None,
            "is_store_stub": False
        }
    except Exception:
        return {
            "available": False,
            "version": None,
            "executable": None,
            "is_store_stub": False
        }


def check_system_pptx_available(system_python):
    """检测系统 Python 是否有 python-pptx

    通过子进程执行系统 Python 的 import pptx 检测，
    确保检测的是系统 Python 的 pptx 而非当前嵌入式 Python 的。
    """
    if not system_python["available"] or system_python.get("is_store_stub"):
        return {"available": False, "version": None}

    exe = system_python["executable"]
    if not exe:
        return {"available": False, "version": None}

    try:
        result = subprocess.run(
            [exe, "-c", "import pptx; print(pptx.__version__)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"available": True, "version": result.stdout.strip()}
        return {"available": False, "version": None}
    except Exception:
        return {"available": False, "version": None}


def check_embed_python(skill_dir):
    """检测嵌入式 Python 是否存在"""
    embed_python_path = os.path.join(skill_dir, "vendor", "python", "python.exe")
    exists = os.path.isfile(embed_python_path)
    return {
        "available": exists,
        "path": embed_python_path if exists else None
    }


def check_embed_python_test(embed_python):
    """验证嵌入式 Python 可启动性

    执行 embed_python_path --version，确认 Python 运行时可用。
    返回版本字符串（成功）或 null（失败）。
    """
    if not embed_python["available"]:
        return None
    return _get_python_version(embed_python["path"])


def check_embed_pptx(skill_dir):
    """检测嵌入式 Python 中是否有 python-pptx

    不仅检查目录存在，还检查关键文件 vendor/libs/pptx/__init__.py 以验证可导入性。
    """
    pptx_init = os.path.join(skill_dir, "vendor", "libs", "pptx", "__init__.py")
    return os.path.isfile(pptx_init)


def check_libs_path(skill_dir):
    """检测 vendor/libs 目录是否存在"""
    libs_path = os.path.join(skill_dir, "vendor", "libs")
    exists = os.path.isdir(libs_path)
    return {
        "available": exists,
        "path": libs_path if exists else None
    }


def check_ppt_templates(skill_dir):
    """检测 PPT 模板目录及可用模板

    扫描 {app_root}/data/ppt-templates/ 目录下所有 .pptx 文件。
    app_root 通过 skill_dir 向上两级推算。
    """
    app_root = get_app_root(skill_dir)
    templates_dir = os.path.join(app_root, "data", "ppt-templates")

    if not os.path.isdir(templates_dir):
        return {
            "available": False,
            "dir": templates_dir,
            "templates": []
        }

    templates = []
    try:
        for name in os.listdir(templates_dir):
            if name.lower().endswith(".pptx"):
                full_path = os.path.join(templates_dir, name)
                if os.path.isfile(full_path):
                    try:
                        size = os.path.getsize(full_path)
                    except OSError:
                        size = 0
                    templates.append({"name": name, "path": full_path, "size": size})
    except Exception:
        pass

    return {
        "available": len(templates) > 0,
        "dir": templates_dir,
        "templates": templates
    }


def determine_route(system_python, system_pptx, embed_python, embed_pptx):
    """根据环境检测结果推荐路线

    路线 A: 系统有真实 Python（非桩）+ 系统 python-pptx 可用
    路线 A_NEED_PIP: 系统有真实 Python（非桩）但无 python-pptx（需 LLM 判断网络）
    路线 B: 嵌入式 Python 可用 + 嵌入式 python-pptx 可用
    路线 C: 嵌入式 Python 可用 + 嵌入式 python-pptx 不可用（纯标准库）
    NONE: 完全无 Python 环境
    """
    # 路线 A：系统有真实 Python + python-pptx 可用
    if system_python["available"] and not system_python.get("is_store_stub") and system_pptx["available"]:
        return "A"
    # 路线 B：嵌入式 Python + python-pptx
    if embed_python["available"] and embed_pptx:
        return "B"
    # 路线 C：嵌入式 Python + 纯标准库兜底
    if embed_python["available"] and not embed_pptx:
        return "C"
    # 系统有真实 Python 但无 pptx（可能需要 pip install，需 LLM 判断网络）
    if system_python["available"] and not system_python.get("is_store_stub"):
        return "A_NEED_PIP"
    return "NONE"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PPT Creator 环境检测脚本")
    parser.add_argument("--skill-dir", help="技能目录绝对路径（优先于 __file__ 自探测）")
    args = parser.parse_args()

    skill_dir = get_skill_dir(args.skill_dir)
    system_python = check_system_python(skill_dir)
    system_pptx = check_system_pptx_available(system_python)
    embed_python = check_embed_python(skill_dir)
    embed_python_test = check_embed_python_test(embed_python)
    embed_pptx = check_embed_pptx(skill_dir)
    libs_path = check_libs_path(skill_dir)
    ppt_templates = check_ppt_templates(skill_dir)
    recommended_route = determine_route(system_python, system_pptx, embed_python, embed_pptx)

    result = {
        "skill_dir": skill_dir,
        "system_python": system_python,
        "system_pptx_available": system_pptx["available"],
        "system_pptx_version": system_pptx["version"],
        "embed_python_available": embed_python["available"],
        "embed_python_path": embed_python["path"],
        "embed_python_test": embed_python_test,
        "embed_pptx_available": embed_pptx,
        "libs_available": libs_path["available"],
        "libs_path": libs_path["path"],
        "ppt_templates": ppt_templates,
        "recommended_route": recommended_route
    }

    # 输出 JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
