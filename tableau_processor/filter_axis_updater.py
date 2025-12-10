#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET
from datetime import datetime



# ------------- 公共：全局月份计算 -------------

def _parse_first_market_share_file(base_dir: Path) -> Optional[str]:
    """
    从 /output/csv/market_share 目录中读取第一个文件名，提取前6位 yyyymm。
    注意：不做排序，直接使用目录枚举顺序中的第一个文件。
    返回形如 "202510" 的字符串；若失败返回 None。
    """
    target_dir = base_dir / "output" / "csv" / "market_share"
    if not target_dir.exists() or not target_dir.is_dir():
        return None
    for name in os.listdir(target_dir):
        # 跳过隐藏文件与非文件
        p = target_dir / name
        if not p.is_file():
            continue
        # 提取前6位
        if len(name) >= 6 and name[:6].isdigit():
            return name[:6]
    return None


def _yyyymm_to_year_month(yyyymm: str) -> Tuple[int, int]:
    return int(yyyymm[:4]), int(yyyymm[4:6])


def _prev_month(year: int, month: int) -> Tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _shift_month(year: int, month: int, delta: int) -> Tuple[int, int]:
    """月度平移，delta可正可负。"""
    total = year * 12 + (month - 1) + delta
    new_year = total // 12
    new_month = total % 12 + 1
    return new_year, new_month


def _fmt_year_month(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _fmt_major_origin(year: int, month: int) -> str:
    # 两年前同月第一天 00:00:00 的格式，如 #2023-09-01 00:00:00#
    return f"#{year:04d}-{month:02d}-01 00:00:00#"


def compute_global_context(base_dir: str | Path | None = None) -> Tuple[str, List[str], str]:
    """
    读取 market_share 的首个 CSV 文件名，获取 yyyymm，取其上一个月作为全局基准月（YYYY-MM）。
    - global_month: 基准月，形如 2025-09（来自首个文件 yyyymm 的上一个月）
    - last3_months: 基于基准月生成 [M-2, M-1, M]
    - major_origin: 基于基准月回退 24 个月的 1 号 00:00:00（两年跨度）
    """
    if base_dir is None:
        # 自动定位仓库根：当前文件位于 <repo>/tableau_processor/ 下，父级即为仓库根
        base_dir = Path(__file__).resolve().parents[1]
    else:
        base_dir = Path(base_dir)
    yyyymm = _parse_first_market_share_file(base_dir)
    if not yyyymm:
        raise FileNotFoundError("未能在 /output/csv/market_share 找到有效文件以解析 yyyymm。")

    y, m = _yyyymm_to_year_month(yyyymm)
    gy, gm = _prev_month(y, m)

    global_month = _fmt_year_month(gy, gm)

    m1y, m1m = _shift_month(gy, gm, -2)
    m2y, m2m = _shift_month(gy, gm, -1)
    last3_months = [
        _fmt_year_month(m1y, m1m),
        _fmt_year_month(m2y, m2m),
        _fmt_year_month(gy, gm),
    ]

    oy, om = _shift_month(gy, gm, -24)
    major_origin = _fmt_major_origin(oy, om)

    return global_month, last3_months, major_origin


# ------------- TWB 修改：仅限 worksheets 内轴与月份筛选 -------------

def _update_axis_major_origin_in_table(table_elem: ET.Element, new_major_origin: str) -> int:
    """
    在 <view> 下查找 <style><style-rule element='axis' ...>，当满足：
      - major-units='months'
      - type='space'
      - scope='cols'
    时，将其 'major-origin' 属性更新为 new_major_origin。
    返回修改计数。
    """
    count = 0
    for style in table_elem.findall("./style"):
        for sr in style.findall("./style-rule"):
            if sr.get("element") != "axis":
                continue
            # 关键属性不在 style-rule 本身，而是在其子节点 <encoding ...>
            enc = sr.find("./encoding")
            if enc is None:
                continue
            if enc.get("attr") != "space":
                continue
            if enc.get("major-units") != "months":
                continue
            if enc.get("type") != "space":
                continue
            if enc.get("scope") != "cols":
                continue
            # 命中：更新 encoding 的 major-origin
            if enc.get("major-origin") != new_major_origin:
                enc.set("major-origin", new_major_origin)
                count += 1
    return count


def _is_month_level(level_value: Optional[str]) -> bool:
    if not level_value:
        return False
    return ":month:" in level_value or level_value.endswith(":month:nk]")


def _update_month_filters(view_elem: ET.Element, last3_months: List[str]) -> int:
    """
    在 <view> 下查找月份筛选：
    结构示例：
      <filter class='categorical' column='[...]'>
        <groupfilter function='union' ...>
          <groupfilter function='member' level='[none:month:nk]' member='&quot;2025-06&quot;' />
          ...
        </groupfilter>
      </filter>
    将 union 内的 member 替换为基于 last3_months 的三项。
    返回修改的筛选数量（命中 union 并改写一次计为1）。
    """
    changed = 0
    for flt in view_elem.findall("./filter"):
        if flt.get("class") != "categorical":
            continue

        # 优先处理 union 结构
        union = None
        container = None
        existing_members: List[ET.Element] = []
        detected_level: Optional[str] = None
        member_value_style: Optional[str] = None  # "hash" -> #YYYY-MM-01#, "quote" -> &quot;YYYY-MM&quot;

        u = flt.find("./groupfilter")
        if u is not None and u.get("function") == "union":
            union = u
            container = union
            existing_members = [child for child in list(union) if child.tag == "groupfilter" and child.get("function") == "member"]
        else:
            # 无 union：直接收集位于 filter 下的 member
            container = flt
            existing_members = [child for child in list(flt) if child.tag == "groupfilter" and child.get("function") == "member"]

        # 过滤出月份维度的 member
        month_members: List[ET.Element] = []
        for mem in existing_members:
            if _is_month_level(mem.get("level")):
                month_members.append(mem)
                if detected_level is None:
                    detected_level = mem.get("level")
                if member_value_style is None:
                    mv = mem.get("member", "")
                    if mv.startswith("#") and mv.endswith("#"):
                        member_value_style = "hash"
                    else:
                        member_value_style = "quote"

        if not month_members or container is None or not detected_level:
            # 非月份筛选或无法安全改写
            continue

        # 根据原有月份 member 数量决定替换数量：1/2/≥3 → 用最近1/2/3个月
        n = len(month_members)
        if n <= 1:
            months_to_write = last3_months[-1:]
        elif n == 2:
            months_to_write = last3_months[-2:]
        else:
            months_to_write = last3_months[-3:]

        # 仅移除原有的月份 member（保留非月份 member 与其他子节点如 <preset>）
        for mem in month_members:
            container.remove(mem)

        # 写入新的月份 member，保持原 level 与 member 值风格
        for ym in months_to_write:
            new_mem = ET.Element("groupfilter")
            new_mem.set("function", "member")
            new_mem.set("level", detected_level)
            if member_value_style == "hash":
                new_mem.set("member", f"#{ym}-01#")
            else:
                # 直接写入双引号，ElementTree 会自动转义为 &quot;
                new_mem.set("member", f'"{ym}"')
            container.append(new_mem)

        changed += 1
    return changed


def update_twb_axes_and_filters(twb_path: Path, major_origin: str, last3_months: List[str]) -> Dict[str, int]:
    """
    仅修改 .twb 的 <worksheets> 下：
      - 轴：当存在满足条件的 axis style-rule 时更新 major-origin
      - 筛选：将月份筛选替换为最近3个月
    返回统计字典：{"axis_updated": n, "filters_updated": m}
    """
    ET.register_namespace('', "http://www.tableausoftware.com/xml/tableau")
    tree = ET.parse(str(twb_path))
    root = tree.getroot()

    axis_updates = 0
    filter_updates = 0

    worksheets = root.find(".//worksheets")
    if worksheets is None:
        return {"axis_updated": 0, "filters_updated": 0}

    for ws in worksheets.findall("./worksheet"):
        table = ws.find("./table")
        if table is None:
            continue
        # 轴样式位于 <table>/<style> 下；筛选位于 <table>/<view> 下
        axis_updates += _update_axis_major_origin_in_table(table, major_origin)
        view = table.find("./view")
        if view is not None:
            filter_updates += _update_month_filters(view, last3_months)

    if axis_updates or filter_updates:
        tree.write(str(twb_path), encoding="utf-8")

    return {"axis_updated": axis_updates, "filters_updated": filter_updates}


# ------------- 遍历三个项目目录 -------------

PROJECT_PREFIXES = ("[shopcash] ", "[market_share] ", "[key_brands] ")


def process_all_projects(base_dir: str | Path | None = None) -> Dict[str, Dict[str, int]]:
    """
    遍历 tableau_processor/xml_of_twbx 下的三个项目文件夹，修改其中的 .twb。
    返回报告：{ twb_path: {"axis_updated": n, "filters_updated": m}, ... }
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1]
    else:
        base_dir = Path(base_dir)
    xml_root = base_dir / "tableau_processor" / "xml_of_twbx"
    if not xml_root.exists():
        raise FileNotFoundError(f"不存在目录: {xml_root}")

    global_month, last3_months, major_origin = compute_global_context(base_dir)
    # global_month 当前未直接使用，仅为将来可能的增强保留

    # 汇总到项目级别（仅显示 shopcash / market_share / key_brands 三个标识）
    report: Dict[str, Dict[str, int]] = {
        "shopcash": {"axis_updated": 0, "filters_updated": 0},
        "market_share": {"axis_updated": 0, "filters_updated": 0},
        "key_brands": {"axis_updated": 0, "filters_updated": 0},
    }
    for entry in os.listdir(xml_root):
        if not entry.startswith(PROJECT_PREFIXES):
            continue
        folder = xml_root / entry
        if not folder.is_dir():
            continue
        # 判定项目标识
        project_key = (
            "shopcash" if entry.startswith("[shopcash]") else
            "market_share" if entry.startswith("[market_share]") else
            "key_brands" if entry.startswith("[key_brands]") else None
        )
        if project_key is None:
            continue

        for name in os.listdir(folder):
            if not name.endswith(".twb"):
                continue
            twb_path = folder / name
            stats = update_twb_axes_and_filters(twb_path, major_origin=major_origin, last3_months=last3_months)
            # 累加到项目级汇总
            report[project_key]["axis_updated"] += stats.get("axis_updated", 0)
            report[project_key]["filters_updated"] += stats.get("filters_updated", 0)

    return report


# ------------- 对外入口：仅执行轴与筛选更新 -------------

def update_axes_and_filters(base_dir: str | Path | None = None) -> Dict[str, Dict[str, int]]:
    """仅执行更新 <worksheets> 内 axis 与月份筛选的核心逻辑。"""
    return process_all_projects(base_dir)


__all__ = [
    "update_axes_and_filters",
]


if __name__ == "__main__":
    import json
    # 直接运行时：不接受命令行参数，使用默认 base_dir 自动推断仓库根
    result = update_axes_and_filters(base_dir=None)
    print(json.dumps(result, ensure_ascii=False, indent=2))

