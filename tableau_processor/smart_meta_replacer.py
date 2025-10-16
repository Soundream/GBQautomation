import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


SHOPCASH_KEY = "shopcash"
# 当前脚本所在目录（tableau_processor）
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_META_PATH = BASE_DIR / "template_metadata.json"
CURRENT_META_PATH = BASE_DIR / "current_metadata.json"


def load_json(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_replacements(template_meta: Dict, current_meta: Dict, project: str) -> Dict[str, List[Dict[str, str]]]:
    """
    为指定项目构建按 twb_file 聚合的替换映射。
    返回: { twb_file_name: [{old,new,dataset,field}, ...] }
    仅处理四个关键字段: caption, federated_name, textscan_name, object_id
    """
    replacements_by_twb: Dict[str, List[Dict[str, str]]] = {}

    tmpl = template_meta.get(project, {})
    curr = current_meta.get(project, {})

    intersect_keys = sorted(set(tmpl.keys()) & set(curr.keys()))
    if not intersect_keys:
        return {}

    for dataset_key in intersect_keys:
        t = tmpl[dataset_key]
        c = curr[dataset_key]
        twb_file = t.get("twb_file")
        if not twb_file:
            # 若模板未声明 twb_file，跳过该数据集
            continue

        pairs: List[Dict[str, str]] = []
        for field in ("caption", "federated_name", "textscan_name", "object_id"):
            old_val = t.get(field)
            new_val = c.get(field)
            if isinstance(old_val, str) and isinstance(new_val, str) and old_val != new_val:
                pairs.append({
                    "old": old_val,
                    "new": new_val,
                    "dataset": dataset_key,
                    "field": field,
                })

        if not pairs:
            continue

        if twb_file not in replacements_by_twb:
            replacements_by_twb[twb_file] = []
        # 追加，可能有多个数据集对应同一个 twb
        replacements_by_twb[twb_file].extend(pairs)

    return replacements_by_twb


def twb_paths_from_current_meta(current_meta: Dict, project: str, twb_filename: str) -> List[Path]:
    """
    基于 current_metadata 中任一数据集的 file_path，推导 .twb 所在目录：
    <project_root> = file_path 的 parents[2]，即 .../[project] .../
    最终 twb 完整路径为 <project_root>/<twb_filename>
    不做遍历或搜索，遵循上游组件的路径约定。
    """
    curr = current_meta.get(project, {})
    for dataset in curr.values():
        file_path = dataset.get("file_path")
        if not file_path:
            continue
        p = Path(file_path)
        # .../<project_dir>/Data/<subdir>/<file>
        # 回退到 <project_dir>
        try:
            twb_dir = p.parents[2]
        except IndexError:
            continue
        twb_path = twb_dir / twb_filename
        return [twb_path]
    return []


def replace_in_file(file_path: Path, pairs: List[Tuple[str, str]]) -> int:
    """
    对给定 twb 文件执行全局字符串替换。返回执行的替换次数（累计命中数）。
    注意：Tableau XML 中 datasource/worksheet 两处都会出现相关值，这里做全文替换以覆盖全部。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    total_hits = 0
    for old, new in pairs:
        if not old:
            continue
        hits = content.count(old)
        if hits > 0:
            content = content.replace(old, new)
            total_hits += hits

    if total_hits > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return total_hits


def analyze_in_file(file_path: Path, repls: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """
    统计每条替换规则在文件中的命中情况，不进行写回。
    返回 [{old, new, hits_old, hits_new}] 列表。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    report = []
    for r in repls:
        old = r.get("old", "")
        new = r.get("new", "")
        dataset = r.get("dataset", "")
        field = r.get("field", "")
        hits_old = content.count(old) if old else 0
        hits_new = content.count(new) if new else 0
        report.append({
            "old": old,
            "new": new,
            "dataset": dataset,
            "field": field,
            "hits_old": hits_old,
            "hits_new": hits_new,
        })
    return report


def run_for_projects(projects: List[str], dry_run: bool = False) -> None:
    template_meta = load_json(TEMPLATE_META_PATH)
    current_meta = load_json(CURRENT_META_PATH)

    for project in projects:
        replacements_map = build_replacements(template_meta, current_meta, project)
        if not replacements_map:
            print(f"[smart_meta_replacer] 未发现需要替换的 {project} 元数据。")
            continue

        for twb_file, repls in replacements_map.items():
            twb_paths = twb_paths_from_current_meta(current_meta, project, twb_file)
            if not twb_paths:
                print(f"[smart_meta_replacer] 未定位 TWB 文件: {project} -> {twb_file}")
                continue

            # 去重，避免同一 old->new 出现多次
            unique_pairs = []
            seen = set()
            for r in repls:
                key = (r["old"], r["new"])
                if key not in seen:
                    seen.add(key)
                    unique_pairs.append(key)

            for path in twb_paths:
                if dry_run:
                    analysis = analyze_in_file(path, repls)
                    total_hits = sum(item.get("hits_old", 0) for item in analysis)
                    print(f"[smart_meta_replacer][DRY] {project} -> {path.name} @ {path.parent}")
                    for item in analysis:
                        ds = item.get("dataset", "")
                        field = item.get("field", "")
                        ho = item["hits_old"]
                        hn = item["hits_new"]
                        note = "" if ho > 0 else "(未命中旧值)"
                        print(
                            f"  - [{ds}.{field}] old→new 命中 {ho} / 现有新值 {hn} {note}"
                        )
                    print(f"  合计可替换命中: {total_hits}，规则数: {len(repls)}；执行去重后替换对数: {len(unique_pairs)}")
                else:
                    hits = replace_in_file(path, unique_pairs)
                    print(
                        f"[smart_meta_replacer] {project} 替换 {path.name} @ {path.parent} 命中 {hits} 次，规则数 {len(unique_pairs)}"
                    )


def replace_metadata(projects: List[str] | None = None) -> None:
    """供其他脚本 import 后直接调用的入口，不进行 dry-run。
    默认为仅处理 shopcash；可传入 ["shopcash","market_share","key_brands"].
    """
    if projects is None or len(projects) == 0:
        projects = [SHOPCASH_KEY]
    run_for_projects(projects, dry_run=False)


def replace_shopcash() -> None:
    """便捷方法：仅处理 shopcash，不进行 dry-run。"""
    replace_metadata([SHOPCASH_KEY])


if __name__ == "main" or __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replace Tableau TWB metadata from template to current.")
    parser.add_argument("--dry-run", action="store_true", help="仅统计不写回，输出命中详情")
    # 可选：自定义项目列表
    parser.add_argument("--projects", nargs="*", default=[SHOPCASH_KEY], help="项目列表，默认仅 shopcash")
    args = parser.parse_args()

    run_for_projects(args.projects, dry_run=args.dry_run)


