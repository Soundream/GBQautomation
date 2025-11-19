from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from tableau_processor.hyper_generator import process_csv_directory
from tableau_processor.xml_metadata_extractor import scan_task_folders
from tableau_processor.csv_hyper_mover import move_and_generate_metadata
from tableau_processor.compare_keys import compare_metadata_keys
from tableau_processor.smart_meta_replacer import replace_metadata
from tableau_processor.filter_axis_updater import update_axes_and_filters


def run_full_pipeline(base_dir: str | Path | None = None, projects: Optional[List[str]] = None) -> Dict[str, object]:
    """
    可被外部调用的统一流水线：生成Hyper→提取模板metadata→移动并生成current metadata→对比→替换TWB引用。
    不包含 axis/filter 的最终更新（由 tableau_robot.update_axes_and_filters 负责）。
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1]
    else:
        base_dir = Path(base_dir)

    if projects is None:
        projects = ["shopcash", "market_share", "key_brands"]

    results: Dict[str, object] = {}

    # 1) 生成 Hyper
    cwd = os.getcwd()
    try:
        os.chdir(str(base_dir))
        results["hyper"] = process_csv_directory()
    finally:
        os.chdir(cwd)

    # 2) 生成模板 metadata
    results["template_metadata"] = scan_task_folders(base_path=str(base_dir))

    # 3) 移动 CSV/HYPER，生成 current_metadata
    results["current_metadata"] = move_and_generate_metadata(base_path=str(base_dir))

    # 4) 比对 metadata（结构性报告）
    tmpl = str(base_dir / "tableau_processor" / "template_metadata.json")
    curr = str(base_dir / "tableau_processor" / "current_metadata.json")
    results["metadata_compare"] = compare_metadata_keys(
        current_file=curr,
        template_file=tmpl,
        verbose=False,
        as_table=False,
        diff_only=False,
    )

    # 暂停等待确认后再继续后续替换与更新步骤
    try:
        _ = input("已生成 metadata 比对结果。输入任意内容并回车以继续执行替换与轴/筛选更新：")
    except EOFError:
        # 在极少数无交互环境下，直接继续
        pass

    # 5) 替换 TWB 引用
    replace_metadata(projects=projects)
    results["metadata_replace"] = {"status": "ok", "projects": projects}

    # 6) 更新 axis 与 filters（强制执行）
    results["axes_filters"] = update_axes_and_filters(base_dir=base_dir)

    return results


__all__ = ["run_full_pipeline"]


if __name__ == "__main__":
    # 直接运行时：不接受命令行参数，使用默认 base_dir 自动推断仓库根并跑完整流程
    result = run_full_pipeline(base_dir=None, projects=["shopcash","market_share","key_brands"])  # noqa: F841


