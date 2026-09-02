#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPT Creator - 纯标准库 PPTX 生成脚本

使用 Python 标准库（zipfile + xml.etree.ElementTree）生成 PowerPoint 演示文稿。
作为 python-pptx 不可用时的兜底方案。

用法：
    python generate_stdlib.py --input slides.json --output output.pptx --skill-dir /path/to/ppt-creator
    python generate_stdlib.py --input slides.json --source existing.pptx --output modified.pptx --skill-dir /path/to/ppt-creator
    python generate_stdlib.py --input slides.json --output output.pptx --skill-dir /path/to/ppt-creator --aspect-ratio 16:9 --template template.pptx

参数：
    --input        : slides JSON 文件路径（必填）
    --output       : 输出 PPTX 文件路径（必填）
    --skill-dir    : 技能目录绝对路径（用于推算 app_root 以备份）
    --source       : 修改模式时，源 PPTX 文件路径（可选）
    --aspect-ratio : 宽高比，16:9（默认）或 4:3（仅 create 模式生效）
    --template     : 模板 PPTX 文件路径（仅 create 模式）

限制：
    - 不支持图表（chart）布局
    - 修改已有 PPT 时依赖 XML 解析，不同来源的 PPTX 格式差异可能导致失败
    - 建议修改操作优先使用路线 A/B（python-pptx）
"""

import os
import sys
import json
import argparse
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import copy
import re
import shutil
import glob
import time
from html import escape


# ============================================================
# OOXML 命名空间
# ============================================================

NSMAP = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dcterms': 'http://purl.org/dc/terms/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}

for prefix, uri in NSMAP.items():
    ET.register_namespace(prefix, uri)


# ============================================================
# 常量配置
# ============================================================

DEFAULT_THEME = {
    "primaryColor": "2B579A",
    "fontFamily": "微软雅黑"
}

# 宽高比尺寸（EMU）
ASPECT_RATIOS = {
    "16:9": {"cx": "12192000", "cy": "6858000", "type": "screen16x9"},
    "4:3": {"cx": "9144000", "cy": "6858000", "type": "screen4x3"},
}

# 支持的布局类型
SUPPORTED_LAYOUTS = {"title", "content", "two_content", "table", "image", "section", "blank"}


# ============================================================
# JSON 校验
# ============================================================

def validate_slides_json(data):
    """校验 slides JSON 格式

    校验顶层必填字段和每个 slide 的 layout 字段。
    校验失败时输出明确错误信息并 sys.exit(1)。
    """
    if not isinstance(data, dict):
        print("错误：JSON 顶层必须为对象", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data.get("title"), str):
        print("错误：缺少必填字段 title 或类型不是 string", file=sys.stderr)
        sys.exit(1)

    slides = data.get("slides")
    if not isinstance(slides, list) or len(slides) == 0:
        print("错误：缺少必填字段 slides 或不是非空数组", file=sys.stderr)
        sys.exit(1)

    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            print(f"错误：第 {i+1} 张幻灯片不是对象", file=sys.stderr)
            sys.exit(1)
        layout = slide.get("layout")
        if layout not in SUPPORTED_LAYOUTS:
            print(f"错误：第 {i+1} 张幻灯片 layout '{layout}' 不在支持列表内: {SUPPORTED_LAYOUTS}", file=sys.stderr)
            print("注意：纯标准库模式不支持 chart 布局，建议使用路线 A/B", file=sys.stderr)
            sys.exit(1)

    aspect_ratio = data.get("theme", {}).get("aspectRatio")
    if aspect_ratio and aspect_ratio not in ASPECT_RATIOS:
        print(f"错误：aspectRatio '{aspect_ratio}' 不在支持列表内: {list(ASPECT_RATIOS.keys())}", file=sys.stderr)
        sys.exit(1)


# ============================================================
# 修改前备份（模块 8）
# ============================================================

def get_app_root(skill_dir_path):
    """从 skill_dir 推算 app_root（向上两级）"""
    return os.path.dirname(os.path.dirname(skill_dir_path))


def backup_source(source_path, skill_dir_path):
    """修改前自动备份源文件到 {app_root}/data/ppt-backups/"""
    if not os.path.isfile(source_path):
        return

    app_root = get_app_root(skill_dir_path)
    backup_dir = os.path.join(app_root, "data", "ppt-backups")

    try:
        os.makedirs(backup_dir, exist_ok=True)
    except OSError as e:
        print(f"警告：创建备份目录失败: {e}", file=sys.stderr)
        return

    source_filename = os.path.basename(source_path)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{source_filename}_{timestamp}.pptx"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        shutil.copy2(source_path, backup_path)
        print(f"备份已创建: {backup_path}", file=sys.stderr)
    except OSError as e:
        print(f"警告：备份源文件失败: {e}", file=sys.stderr)
        return

    cleanup_old_backups(backup_dir, source_filename)


def cleanup_old_backups(backup_dir, source_filename, max_keep=5, max_total_mb=500):
    """双层清理：按源文件分组 + 总量控制"""
    pattern = os.path.join(backup_dir, f"{source_filename}_*.pptx")
    backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for old_backup in backups[max_keep:]:
        try:
            os.remove(old_backup)
        except OSError:
            pass

    all_backups = sorted(
        glob.glob(os.path.join(backup_dir, "*_*.pptx")),
        key=os.path.getmtime,
        reverse=True
    )
    try:
        total_size_mb = sum(os.path.getsize(f) for f in all_backups) / (1024 * 1024)
    except OSError:
        return

    if total_size_mb > max_total_mb:
        for old_file in reversed(all_backups):
            if total_size_mb <= max_total_mb:
                break
            try:
                file_size_mb = os.path.getsize(old_file) / (1024 * 1024)
                os.remove(old_file)
                total_size_mb -= file_size_mb
            except OSError:
                pass


# ============================================================
# 辅助函数
# ============================================================

def hex_to_rgb_tuple(hex_color):
    """将十六进制颜色转换为 RGB 元组"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    return (0x2B, 0x57, 0x9A)


def rgb_to_hex(r, g, b):
    """将 RGB 元组转换为十六进制颜色"""
    return f"{r:02X}{g:02X}{b:02X}"


def create_element(tag, attrib=None, text=None):
    """创建 XML 元素"""
    elem = ET.Element(tag, attrib or {})
    if text:
        elem.text = text
    return elem


def add_subelement(parent, tag, attrib=None, text=None):
    """添加子元素"""
    elem = ET.SubElement(parent, tag, attrib or {})
    if text:
        elem.text = text
    return elem


def prettify_xml(elem):
    """美化 XML 输出"""
    rough_string = ET.tostring(elem, encoding='unicode', xml_declaration=False)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)


# ============================================================
# PPTX 结构生成
# ============================================================

def create_content_types(slide_count=0):
    """创建 [Content_Types].xml"""
    root = create_element('Types', {'xmlns': NSMAP['ct']})
    
    # 默认类型
    defaults = [
        ('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
        ('xml', 'application/xml'),
        ('png', 'image/png'),
        ('jpeg', 'image/jpeg'),
        ('jpg', 'image/jpeg'),
        ('gif', 'image/gif'),
        ('bmp', 'image/bmp'),
    ]
    for ext, ct in defaults:
        add_subelement(root, 'Default', {'Extension': ext, 'ContentType': ct})
    
    # 覆盖类型
    overrides = [
        ('/ppt/presentation.xml', 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'),
        ('/ppt/slideMasters/slideMaster1.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'),
        ('/ppt/slideLayouts/slideLayout1.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'),
        ('/ppt/theme/theme1.xml', 'application/vnd.openxmlformats-officedocument.theme+xml'),
        ('/docProps/app.xml', 'application/vnd.openxmlformats-officedocument.extended-properties+xml'),
        ('/docProps/core.xml', 'application/vnd.openxmlformats-package.core-properties+xml'),
    ]
    # 为每个 slide 添加 Override
    for i in range(slide_count):
        overrides.append((f'/ppt/slides/slide{i + 1}.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'))
    
    for part, ct in overrides:
        add_subelement(root, 'Override', {'PartName': part, 'ContentType': ct})
    
    return root


def create_rels():
    """创建 _rels/.rels"""
    root = create_element('Relationships', {'xmlns': NSMAP['rel']})
    add_subelement(root, 'Relationship', {
        'Id': 'rId1',
        'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument',
        'Target': 'ppt/presentation.xml'
    })
    add_subelement(root, 'Relationship', {
        'Id': 'rId2',
        'Type': 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties',
        'Target': 'docProps/core.xml'
    })
    add_subelement(root, 'Relationship', {
        'Id': 'rId3',
        'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties',
        'Target': 'docProps/app.xml'
    })
    return root


def create_core_properties(title, author):
    """创建 docProps/core.xml"""
    root = create_element('cp:coreProperties', {'xmlns:cp': NSMAP['cp'], 'xmlns:dc': NSMAP['dc'], 'xmlns:dcterms': NSMAP['dcterms'], 'xmlns:xsi': NSMAP['xsi']})
    add_subelement(root, 'dc:title', text=title)
    add_subelement(root, 'dc:creator', text=author)
    add_subelement(root, 'cp:lastModifiedBy', text=author)
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    add_subelement(root, 'dcterms:created', {'xsi:type': 'dcterms:W3CDTF'}, text=now)
    add_subelement(root, 'dcterms:modified', {'xsi:type': 'dcterms:W3CDTF'}, text=now)
    return root


def create_app_properties():
    """创建 docProps/app.xml"""
    root = create_element('Properties', {'xmlns': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'})
    add_subelement(root, 'Application', text='UseIO PPT Creator')
    add_subelement(root, 'AppVersion', text='1.0.0')
    return root


def create_theme(primary_color):
    """创建 ppt/theme/theme1.xml"""
    r, g, b = hex_to_rgb_tuple(primary_color)
    accent1 = rgb_to_hex(r, g, b)
    
    theme_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="UseIO Theme">
  <a:themeElements>
    <a:clrScheme name="UseIO">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="44546A"/></a:dk2>
      <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
      <a:accent1><a:srgbClr val="{accent1}"/></a:accent1>
      <a:accent2><a:srgbClr val="5B9BD5"/></a:accent2>
      <a:accent3><a:srgbClr val="70AD47"/></a:accent3>
      <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
      <a:accent5><a:srgbClr val="ED7D31"/></a:accent5>
      <a:accent6><a:srgbClr val="A5A5A5"/></a:accent6>
      <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
      <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="UseIO">
      <a:majorFont><a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/><a:cs typeface="+mj-cs"/></a:majorFont>
      <a:minorFont><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="25400"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="38100"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>'''
    return theme_xml


def create_slide_master(primary_color):
    """创建 ppt/slideMasters/slideMaster1.xml"""
    r, g, b = hex_to_rgb_tuple(primary_color)
    color_hex = rgb_to_hex(r, g, b)
    
    master_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle>
      <a:lvl1pPr algn="ctr">
        <a:defRPr sz="3600" b="1"><a:solidFill><a:srgbClr val="{color_hex}"/></a:solidFill><a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/></a:defRPr>
      </a:lvl1pPr>
    </p:titleStyle>
    <p:bodyStyle>
      <a:lvl1pPr marL="0" indent="0">
        <a:defRPr sz="1800"><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/></a:defRPr>
      </a:lvl1pPr>
    </p:bodyStyle>
    <p:otherStyle>
      <a:lvl1pPr marL="0" indent="0">
        <a:defRPr sz="1800"><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/></a:defRPr>
      </a:lvl1pPr>
    </p:otherStyle>
  </p:txStyles>
</p:sldMaster>'''
    return master_xml


def create_slide_layout():
    """创建 ppt/slideLayouts/slideLayout1.xml"""
    layout_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''
    return layout_xml


def create_presentation_xml(slide_count, aspect_ratio="16:9"):
    """创建 ppt/presentation.xml

    aspect_ratio: 16:9 或 4:3，控制幻灯片尺寸
    """
    ratio = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
    slide_refs = ''.join([f'<p:sldId id="{256 + i}" r:id="rId{8 + i}"/>' for i in range(slide_count)])

    pres_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    {slide_refs}
  </p:sldIdLst>
  <p:sldSz cx="{ratio['cx']}" cy="{ratio['cy']}" type="{ratio['type']}"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''
    return pres_xml


def create_presentation_rels(slide_count):
    """创建 ppt/_rels/presentation.xml.rels"""
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>',
    ]
    for i in range(slide_count):
        rels.append(f'<Relationship Id="rId{8 + i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>')
    
    rels_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n  ' + '\n  '.join(rels) + '\n</Relationships>'
    return rels_xml


def create_slide_master_rels():
    """创建 ppt/slideMasters/_rels/slideMaster1.xml.rels"""
    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''
    return rels_xml


def create_slide_layout_rels():
    """创建 ppt/slideLayouts/_rels/slideLayout1.xml.rels"""
    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''
    return rels_xml


# ============================================================
# 幻灯片内容生成
# ============================================================

def create_shape(id, name, left, top, width, height, text, font_size=1800, bold=False, color="000000", align="l"):
    """创建形状 XML"""
    anchor = {"l": "t", "ctr": "ctr", "r": "t"}.get(align, "t")
    alignment = {"l": "l", "ctr": "ctr", "r": "r"}.get(align, "l")
    
    shape_xml = f'''<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{id}" name="{name}"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{left}" y="{top}"/>
      <a:ext cx="{width}" cy="{height}"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720" anchor="{anchor}"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="{alignment}"/>
      <a:r>
        <a:rPr lang="zh-CN" sz="{font_size}" {'b="1" ' if bold else ''}dirty="0">
          <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
          <a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>
        </a:rPr>
        <a:t>{escape(text)}</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>'''
    return shape_xml


def create_bullet_shape(id, name, left, top, width, height, items, font_size=1800, color="000000"):
    """创建带要点列表的形状 XML"""
    paragraphs = []
    for i, item in enumerate(items):
        paragraphs.append(f'''<a:p>
      <a:pPr marL="457200" indent="-228600"><a:buChar char="•"/></a:pPr>
      <a:r>
        <a:rPr lang="zh-CN" sz="{font_size}" dirty="0">
          <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
          <a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>
        </a:rPr>
        <a:t>{escape(item)}</a:t>
      </a:r>
    </a:p>''')
    
    shape_xml = f'''<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{id}" name="{name}"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{left}" y="{top}"/>
      <a:ext cx="{width}" cy="{height}"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720"/>
    <a:lstStyle/>
    {''.join(paragraphs)}
  </p:txBody>
</p:sp>'''
    return shape_xml


def create_table_xml(id, left, top, width, row_height, headers, rows, primary_color):
    """创建表格 XML"""
    num_rows = len(rows) + 1
    num_cols = len(headers) if headers else 1
    col_width = width // num_cols
    
    r, g, b = hex_to_rgb_tuple(primary_color)
    header_color = rgb_to_hex(r, g, b)
    
    # 表格行
    table_rows = []
    
    # 表头行
    header_cells = []
    for j, header in enumerate(headers):
        header_cells.append(f'''<a:tc>
          <a:txBody><a:bodyPr/><a:lstStyle/><a:p>
            <a:r><a:rPr lang="zh-CN" sz="1400" b="1" dirty="0">
              <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
              <a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>
            </a:rPr><a:t>{escape(header)}</a:t></a:r>
          </a:p></a:txBody>
          <a:tcPr><a:solidFill><a:srgbClr val="{header_color}"/></a:solidFill></a:tcPr>
        </a:tc>''')
    table_rows.append(f'<a:tr h="{row_height}">{"".join(header_cells)}</a:tr>')
    
    # 数据行
    for i, row in enumerate(rows):
        cells = []
        for j, cell_text in enumerate(row):
            if j < num_cols:
                cells.append(f'''<a:tc>
              <a:txBody><a:bodyPr/><a:lstStyle/><a:p>
                <a:r><a:rPr lang="zh-CN" sz="1200" dirty="0">
                  <a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>
                </a:r><a:t>{escape(str(cell_text))}</a:t></a:r>
              </a:p></a:txBody>
              <a:tcPr/>
            </a:tc>''')
        table_rows.append(f'<a:tr h="{row_height}">{"".join(cells)}</a:tr>')
    
    # 列宽
    grid_cols = ''.join([f'<a:gridCol w="{col_width}"/>' for _ in range(num_cols)])
    
    table_xml = f'''<p:graphicFrame>
  <p:nvGraphicFramePr>
    <p:cNvPr id="{id}" name="Table {id}"/>
    <p:cNvGraphicFramePr/>
    <p:nvPr/>
  </p:nvGraphicFramePr>
  <p:xfrm>
    <a:off x="{left}" y="{top}"/>
    <a:ext cx="{width}" cy="{row_height * num_rows}"/>
  </p:xfrm>
  <a:graphic>
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">
      <a:tbl>
        <a:tblPr bandRow="1"/>
        <a:tblGrid>{grid_cols}</a:tblGrid>
        {''.join(table_rows)}
      </a:tbl>
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>'''
    return table_xml


def generate_slide_xml(shapes, bg_color="FFFFFF"):
    """生成单个幻灯片 XML"""
    shapes_str = '\n    '.join(shapes)
    slide_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="{bg_color}"/></a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {shapes_str}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''
    return slide_xml


def create_slide_rels(slide_num):
    """创建幻灯片的关系文件"""
    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''
    return rels_xml


# ============================================================
# 幻灯片类型处理
# ============================================================

def process_title_slide(slide_data, theme, shape_id_start):
    """处理标题页"""
    shapes = []
    shape_id = shape_id_start
    
    title_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "title"), None)
    subtitle_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "subtitle"), None)
    
    if title_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Title {shape_id}",
            457200, 1828800, 8229600, 1828800,
            title_elem.get("text", ""),
            font_size=3600, bold=True,
            color=theme.get("primaryColor", "2B579A"),
            align="ctr"
        ))
    
    if subtitle_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Subtitle {shape_id}",
            457200, 3886200, 8229600, 914400,
            subtitle_elem.get("text", ""),
            font_size=2000,
            color="666666",
            align="ctr"
        ))
    
    return generate_slide_xml(shapes), shape_id


def process_content_slide(slide_data, theme, shape_id_start):
    """处理内容页"""
    shapes = []
    shape_id = shape_id_start
    
    title_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "title"), None)
    bullets_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "bullets"), None)
    
    if title_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Title {shape_id}",
            457200, 228600, 8229600, 914400,
            title_elem.get("text", ""),
            font_size=2800, bold=True,
            color=theme.get("primaryColor", "2B579A")
        ))
    
    if bullets_elem:
        shape_id += 1
        shapes.append(create_bullet_shape(
            shape_id, f"Content {shape_id}",
            457200, 1371600, 8229600, 4572000,
            bullets_elem.get("items", []),
            font_size=1800
        ))
    
    return generate_slide_xml(shapes), shape_id


def process_two_content_slide(slide_data, theme, shape_id_start):
    """处理双栏页"""
    shapes = []
    shape_id = shape_id_start
    
    title_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "title"), None)
    left_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "left_bullets"), None)
    right_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "right_bullets"), None)
    
    if title_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Title {shape_id}",
            457200, 228600, 8229600, 914400,
            title_elem.get("text", ""),
            font_size=2800, bold=True,
            color=theme.get("primaryColor", "2B579A")
        ))
    
    if left_elem:
        shape_id += 1
        shapes.append(create_bullet_shape(
            shape_id, f"Left {shape_id}",
            457200, 1371600, 4038600, 4572000,
            left_elem.get("items", []),
            font_size=1600
        ))
    
    if right_elem:
        shape_id += 1
        shapes.append(create_bullet_shape(
            shape_id, f"Right {shape_id}",
            4654550, 1371600, 4038600, 4572000,
            right_elem.get("items", []),
            font_size=1600
        ))
    
    return generate_slide_xml(shapes), shape_id


def process_table_slide(slide_data, theme, shape_id_start):
    """处理表格页"""
    shapes = []
    shape_id = shape_id_start
    
    title_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "title"), None)
    table_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "table"), None)
    
    if title_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Title {shape_id}",
            457200, 228600, 8229600, 914400,
            title_elem.get("text", ""),
            font_size=2800, bold=True,
            color=theme.get("primaryColor", "2B579A")
        ))
    
    if table_elem:
        shape_id += 1
        shapes.append(create_table_xml(
            shape_id,
            457200, 1371600, 8229600, 365760,
            table_elem.get("headers", []),
            table_elem.get("rows", []),
            theme.get("primaryColor", "2B579A")
        ))
    
    return generate_slide_xml(shapes), shape_id


def process_section_slide(slide_data, theme, shape_id_start):
    """处理章节分隔页"""
    shapes = []
    shape_id = shape_id_start
    
    title_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "title"), None)
    subtitle_elem = next((e for e in slide_data.get("elements", []) if e.get("type") == "subtitle"), None)
    
    if title_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Section {shape_id}",
            457200, 2286000, 8229600, 1828800,
            title_elem.get("text", ""),
            font_size=4000, bold=True,
            color=theme.get("primaryColor", "2B579A"),
            align="ctr"
        ))
    
    if subtitle_elem:
        shape_id += 1
        shapes.append(create_shape(
            shape_id, f"Subtitle {shape_id}",
            457200, 4343400, 8229600, 914400,
            subtitle_elem.get("text", ""),
            font_size=2400,
            color="666666",
            align="ctr"
        ))
    
    return generate_slide_xml(shapes), shape_id


def process_blank_slide(slide_data, theme, shape_id_start):
    """处理空白页"""
    return generate_slide_xml([]), shape_id_start


# 幻灯片处理器映射
SLIDE_PROCESSORS = {
    "title": process_title_slide,
    "content": process_content_slide,
    "two_content": process_two_content_slide,
    "table": process_table_slide,
    "section": process_section_slide,
    "blank": process_blank_slide,
    "image": process_blank_slide,  # 图片页在纯标准库模式下简化为空白页
    "chart": process_blank_slide,  # 图表页在纯标准库模式下不支持
}


# ============================================================
# 主逻辑
# ============================================================

def create_pptx(slides_data, theme, title, author, output_path, aspect_ratio="16:9", template_path=None):
    """创建新 PPTX 文件

    若提供 template_path，从模板 PPTX 复制 slideMaster/slideLayout/theme 等基础结构，
    仅替换 slides 部分。否则使用默认空白模板。
    """
    primary_color = theme.get("primaryColor", "2B579A")
    slide_count = len(slides_data)

    # 若使用模板，从模板复制基础结构
    template_files = {}
    if template_path and os.path.isfile(template_path):
        try:
            with zipfile.ZipFile(template_path, 'r') as tzf:
                for name in tzf.namelist():
                    # 复制除 slides/ 和 presentation.xml 之外的所有文件
                    if not name.startswith('ppt/slides/') and name != 'ppt/presentation.xml' and name != 'ppt/_rels/presentation.xml.rels':
                        template_files[name] = tzf.read(name)
            print(f"已加载模板: {template_path}", file=sys.stderr)
        except Exception as e:
            print(f"警告：加载模板失败，使用默认空白模板: {e}", file=sys.stderr)
            template_files = {}

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if template_files:
            # 使用模板的基础结构
            for name, data in template_files.items():
                zf.writestr(name, data)
            # 覆盖 [Content_Types].xml 以包含正确的 slide Override
            zf.writestr('[Content_Types].xml', prettify_xml(create_content_types(slide_count)))
        else:
            # 默认空白模板
            zf.writestr('[Content_Types].xml', prettify_xml(create_content_types(slide_count)))
            zf.writestr('_rels/.rels', prettify_xml(create_rels()))
            zf.writestr('docProps/core.xml', prettify_xml(create_core_properties(title, author)))
            zf.writestr('docProps/app.xml', prettify_xml(create_app_properties()))
            zf.writestr('ppt/theme/theme1.xml', create_theme(primary_color))
            zf.writestr('ppt/slideMasters/slideMaster1.xml', create_slide_master(primary_color))
            zf.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', create_slide_master_rels())
            zf.writestr('ppt/slideLayouts/slideLayout1.xml', create_slide_layout())
            zf.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', create_slide_layout_rels())

        # slides（始终生成新的）
        shape_id_counter = 1
        for i, slide_data in enumerate(slides_data):
            layout = slide_data.get("layout", "content")
            processor = SLIDE_PROCESSORS.get(layout, process_content_slide)
            slide_xml, shape_id_counter = processor(slide_data, theme, shape_id_counter + 100 * i)

            zf.writestr(f'ppt/slides/slide{i + 1}.xml', slide_xml)
            zf.writestr(f'ppt/slides/_rels/slide{i + 1}.xml.rels', create_slide_rels(i + 1))

        # presentation.xml（传入 aspect_ratio）
        zf.writestr('ppt/presentation.xml', create_presentation_xml(slide_count, aspect_ratio))
        zf.writestr('ppt/_rels/presentation.xml.rels', create_presentation_rels(slide_count))


def parse_existing_slides(all_files):
    """从现有 PPTX 文件中解析幻灯片的 sldId 和 rId 映射"""
    import re
    
    pres_xml = all_files.get('ppt/presentation.xml', b'').decode('utf-8')
    rels_xml = all_files.get('ppt/_rels/presentation.xml.rels', b'').decode('utf-8')
    
    # 解析 sldId 列表: <p:sldId id="256" r:id="rId8"/>
    sldId_pattern = r'<p:sldId\s+id="(\d+)"\s+r:id="(rId\d+)"/>'
    existing_sldIds = re.findall(sldId_pattern, pres_xml)
    
    # 解析 relationship 列表
    rel_pattern = r'<Relationship\s+Id="(rId\d+)"\s+Type="[^"]*slide"\s+Target="slides/slide(\d+)\.xml"/>'
    existing_rels = re.findall(rel_pattern, rels_xml)
    
    # 找到最大的 sldId 和 rId 数字
    max_sldId_num = 0
    for sldId_str, _ in existing_sldIds:
        max_sldId_num = max(max_sldId_num, int(sldId_str))
    
    max_rId_num = 0
    for rId_str, _ in existing_rels:
        max_rId_num = max(max_rId_num, int(rId_str.replace('rId', '')))
    
    return existing_sldIds, existing_rels, max_sldId_num, max_rId_num


def modify_pptx(source_path, slides_data, modify_action, target_slide, theme, output_path):
    """修改已有 PPTX 文件（完整重写 ZIP）
    
    纯标准库模式下修改已有 PPTX 需要：
    1. 读取源 PPTX 中所有文件
    2. 解析现有幻灯片引用（sldId 和 rId）
    3. 根据修改动作调整幻灯片列表
    4. 更新 presentation.xml 和 presentation.xml.rels（保留原有引用，追加新引用）
    5. 更新 [Content_Types].xml
    6. 输出新 PPTX
    """
    import re
    
    # 读取源 PPTX 所有文件
    with zipfile.ZipFile(source_path, 'r') as zf:
        all_files = {name: zf.read(name) for name in zf.namelist()}
    
    # 解析现有幻灯片引用
    existing_sldIds, existing_rels, max_sldId_num, max_rId_num = parse_existing_slides(all_files)
    existing_slide_count = len(existing_sldIds)
    
    # 生成新幻灯片 XML
    new_slides_xml = []
    shape_id_counter = max_sldId_num + 100
    for i, slide_data in enumerate(slides_data):
        layout = slide_data.get("layout", "content")
        processor = SLIDE_PROCESSORS.get(layout, process_content_slide)
        slide_xml, shape_id_counter = processor(slide_data, theme, shape_id_counter + 1)
        new_slides_xml.append(slide_xml)
    
    # 根据修改动作确定最终状态
    new_sldId_entries = []  # 新增的 sldId 条目
    new_rel_entries = []     # 新增的 relationship 条目
    
    if modify_action == "append":
        for i, slide_xml in enumerate(new_slides_xml):
            new_sldId_num = max_sldId_num + 1 + i
            new_rId_num = max_rId_num + 1 + i
            slide_num = existing_slide_count + i + 1
            all_files[f'ppt/slides/slide{slide_num}.xml'] = slide_xml.encode('utf-8')
            all_files[f'ppt/slides/_rels/slide{slide_num}.xml.rels'] = create_slide_rels(slide_num).encode('utf-8')
            new_sldId_entries.append(f'<p:sldId id="{new_sldId_num}" r:id="rId{new_rId_num}"/>')
            new_rel_entries.append(f'<Relationship Id="rId{new_rId_num}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{slide_num}.xml"/>')
    
    elif modify_action == "insert" and target_slide is not None:
        print(f"警告：纯标准库模式 insert 操作已简化为 append", file=sys.stderr)
        for i, slide_xml in enumerate(new_slides_xml):
            new_sldId_num = max_sldId_num + 1 + i
            new_rId_num = max_rId_num + 1 + i
            slide_num = existing_slide_count + i + 1
            all_files[f'ppt/slides/slide{slide_num}.xml'] = slide_xml.encode('utf-8')
            all_files[f'ppt/slides/_rels/slide{slide_num}.xml.rels'] = create_slide_rels(slide_num).encode('utf-8')
            new_sldId_entries.append(f'<p:sldId id="{new_sldId_num}" r:id="rId{new_rId_num}"/>')
            new_rel_entries.append(f'<Relationship Id="rId{new_rId_num}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{slide_num}.xml"/>')
    
    elif modify_action == "replace" and target_slide is not None:
        idx = target_slide - 1
        if 0 <= idx < existing_slide_count:
            # 替换指定位置的幻灯片文件
            all_files[f'ppt/slides/slide{target_slide}.xml'] = new_slides_xml[0].encode('utf-8')
            # 若有多张新幻灯片，追加到末尾
            for i, slide_xml in enumerate(new_slides_xml[1:], 1):
                new_sldId_num = max_sldId_num + i
                new_rId_num = max_rId_num + i
                slide_num = existing_slide_count + i
                all_files[f'ppt/slides/slide{slide_num}.xml'] = slide_xml.encode('utf-8')
                all_files[f'ppt/slides/_rels/slide{slide_num}.xml.rels'] = create_slide_rels(slide_num).encode('utf-8')
                new_sldId_entries.append(f'<p:sldId id="{new_sldId_num}" r:id="rId{new_rId_num}"/>')
                new_rel_entries.append(f'<Relationship Id="rId{new_rId_num}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{slide_num}.xml"/>')
        else:
            print(f"警告：目标页码 {target_slide} 超出范围（共 {existing_slide_count} 页）", file=sys.stderr)
    
    elif modify_action == "delete" and target_slide is not None:
        idx = target_slide - 1
        if 0 <= idx < existing_slide_count:
            # 获取要删除的 sldId 的 rId
            sldId_str, rId_str = existing_sldIds[idx]
            # 从 presentation.xml 中移除对应的 sldId
            pres_xml = all_files.get('ppt/presentation.xml', b'').decode('utf-8')
            sldId_tag = f'<p:sldId id="{sldId_str}" r:id="{rId_str}"/>'
            pres_xml = pres_xml.replace(sldId_tag, '')
            all_files['ppt/presentation.xml'] = pres_xml.encode('utf-8')
            # 从 rels 中移除对应的 Relationship
            rels_xml = all_files.get('ppt/_rels/presentation.xml.rels', b'').decode('utf-8')
            rel_pattern = f'<Relationship Id="{rId_str}"[^/]*/>'
            rels_xml = re.sub(rel_pattern, '', rels_xml)
            all_files['ppt/_rels/presentation.xml.rels'] = rels_xml.encode('utf-8')
            print(f"已删除第 {target_slide} 页", file=sys.stderr)
        else:
            print(f"警告：目标页码 {target_slide} 超出范围（共 {existing_slide_count} 页）", file=sys.stderr)
    else:
        print(f"警告：未知修改动作 {modify_action}，未做修改", file=sys.stderr)
    
    # 更新 presentation.xml：在现有 sldIdLst 中追加新条目
    if new_sldId_entries and modify_action != "delete":
        pres_xml = all_files.get('ppt/presentation.xml', b'').decode('utf-8')
        new_entries_str = '\n    '.join(new_sldId_entries)
        pres_xml = pres_xml.replace('</p:sldIdLst>', f'    {new_entries_str}\n  </p:sldIdLst>')
        all_files['ppt/presentation.xml'] = pres_xml.encode('utf-8')
    
    # 更新 presentation.xml.rels：追加新关系
    if new_rel_entries:
        rels_xml = all_files.get('ppt/_rels/presentation.xml.rels', b'').decode('utf-8')
        new_rels_str = '\n  '.join(new_rel_entries)
        rels_xml = rels_xml.replace('</Relationships>', f'  {new_rels_str}\n</Relationships>')
        all_files['ppt/_rels/presentation.xml.rels'] = rels_xml.encode('utf-8')
    
    # 更新 [Content_Types].xml：追加新幻灯片的 Override
    if new_sldId_entries:
        ct_xml = all_files.get('[Content_Types].xml', b'').decode('utf-8')
        new_overrides = []
        for i in range(len(new_sldId_entries)):
            slide_num = existing_slide_count + i + 1
            new_overrides.append(f'<Override PartName="/ppt/slides/slide{slide_num}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        new_overrides_str = '\n  '.join(new_overrides)
        ct_xml = ct_xml.replace('</Types>', f'  {new_overrides_str}\n</Types>')
        all_files['[Content_Types].xml'] = ct_xml.encode('utf-8')
    
    # 写入新 PPTX
    final_slide_count = existing_slide_count + len(new_sldId_entries)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in all_files.items():
            zf.writestr(name, data)
    
    print(f"修改完成，最终幻灯片数量: {final_slide_count}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="PPT Creator - 纯标准库 PPTX 生成脚本")
    parser.add_argument("--input", required=True, help="slides JSON 文件路径")
    parser.add_argument("--output", required=True, help="输出 PPTX 文件路径")
    parser.add_argument("--skill-dir", help="技能目录绝对路径（用于推算 app_root 以备份）")
    parser.add_argument("--source", help="修改模式时，源 PPTX 文件路径")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "4:3"],
                        help="宽高比（仅 create 模式生效，默认 16:9）")
    parser.add_argument("--template", help="模板 PPTX 文件路径（仅 create 模式）")
    args = parser.parse_args()

    # 读取 JSON
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # JSON 校验
    validate_slides_json(data)

    title = data.get("title", "演示文稿")
    author = data.get("author", "")
    theme = data.get("theme", DEFAULT_THEME)
    mode = data.get("mode", "create")
    source = data.get("source") or args.source
    template = data.get("template") or args.template
    slides_data = data.get("slides", [])

    if mode == "create" or not source:
        create_pptx(slides_data, theme, title, author, args.output, args.aspect_ratio, template)
        print(f"成功生成 PPTX: {args.output}")
        print(f"幻灯片数量: {len(slides_data)}")
    else:
        if not os.path.isfile(source):
            print(f"错误：源文件不存在: {source}", file=sys.stderr)
            sys.exit(1)

        # 修改前自动备份（模块 8）
        if args.skill_dir:
            backup_source(source, args.skill_dir)

        modify_action = data.get("modify_action", "append")
        target_slide = data.get("target_slide")
        modify_pptx(source, slides_data, modify_action, target_slide, theme, args.output)
        print(f"成功修改 PPTX: {args.output}")


if __name__ == "__main__":
    main()
