#!/usr/bin/env python3
"""
CSV to Hyper File Converter

Convert CSV files to Tableau Hyper format using Tableau Hyper API.
Supports reading from directory structure and mapping data types according to rules.
"""

import os
import json
import shutil
import pandas as pd
from pathlib import Path
from tableauhyperapi import HyperProcess, Connection, SqlType, TableDefinition, Inserter, CreateMode

# Global constants for directory structure
CSV_ROOT_DIR = Path("output/csv")
HYPER_ROOT_DIR = Path("output/hyper")
SUBFOLDERS = ["key_brands", "market_share", "shopcash"]
RULES_PATH = "tableau_processor/date_rules.json"


def convert_datatype_to_hyper_type(column_name, value, dtype):
    """
    转换数据类型到Hyper API兼容类型
    
    参数:
        column_name: 列名
        value: 列值
        dtype: pandas数据类型
        
    返回:
        TableDefinition.Column对象
    """
    if pd.api.types.is_integer_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.big_int())
    elif pd.api.types.is_float_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.double())
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.date())
    elif pd.api.types.is_bool_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.bool())
    else:
        return TableDefinition.Column(column_name, SqlType.text())


def process_csv_directory(rules_path=RULES_PATH):
    """
    处理CSV目录结构并转换为对应的Hyper文件结构
    
    参数:
        rules_path: 日期字段规则JSON文件的路径
        
    返回:
        生成的Hyper文件路径列表
    """
    # 确保主要输出目录存在
    HYPER_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 清理输出目录
    for folder in SUBFOLDERS:
        folder_path = HYPER_ROOT_DIR / folder
        if folder_path.exists():
            for item in folder_path.glob("*"):
                if item.is_file() and item.name != ".gitkeep":
                    os.remove(item)
                elif item.is_dir():
                    shutil.rmtree(item)
    
    # 加载日期字段规则
    rules = {}
    if Path(rules_path).exists():
        with open(rules_path, 'r') as f:
            rules = json.load(f)
    
    results = []
    
    # 处理所有子目录
    for folder in SUBFOLDERS:
        csv_folder = CSV_ROOT_DIR / folder
        hyper_folder = HYPER_ROOT_DIR / folder
        
        if not csv_folder.exists():
            print(f"文件夹不存在: {csv_folder}")
            continue
        
        # 创建对应的hyper输出目录
        hyper_folder.mkdir(parents=True, exist_ok=True)
        
        # 处理文件夹中的所有CSV文件
        for csv_file in csv_folder.glob("*.csv"):
            file_name = csv_file.stem
            hyper_file = hyper_folder / f"{file_name}.hyper"
            
            # 读取CSV文件
            df = pd.read_csv(csv_file)
            
            # 处理每一列，检查是否需要转换为日期格式
            for col in df.columns:
                # 检查该列是否在规则中
                for rule_col, folder_rules in rules.items():
                    if col == rule_col and folder in folder_rules:
                        # 检查文件名是否匹配规则中的模式
                        should_convert = False
                        for file_pattern in folder_rules[folder]:
                            if file_pattern in file_name:
                                should_convert = True
                                break
                        
                        # 如果需要转换，将其转换为日期格式
                        if should_convert:
                            try:
                                df[col] = pd.to_datetime(df[col])
                                print(f"将列 {col} 转换为日期格式 (文件: {file_name})")
                            except Exception as e:
                                print(f"无法将字段 {col} 转换为日期: {e}")
            
            # 确保输出目录存在
            hyper_file = Path(hyper_file)
            hyper_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件已存在则删除
            if hyper_file.exists() and hyper_file.is_file():
                os.remove(hyper_file)
            
            # 创建表定义
            columns = []
            for column_name, dtype in df.dtypes.items():
                columns.append(convert_datatype_to_hyper_type(column_name, df[column_name], dtype))
            
            table_def = TableDefinition("Extract.Extract", columns)
            
            # 创建Hyper文件并写入数据
            with HyperProcess(telemetry=False) as hyper:
                with Connection(hyper.endpoint, hyper_file, CreateMode.CREATE_AND_REPLACE) as connection:
                    connection.catalog.create_schema("Extract")
                    connection.catalog.create_table(table_def)
                    
                    with Inserter(connection, "Extract.Extract") as inserter:
                        for _, row in df.iterrows():
                            inserter.add_row([row[col] if pd.notna(row[col]) else None for col in df.columns])
            
            results.append(hyper_file)
            print(f"已生成: {hyper_file}")
    
    print(f"转换完成，共生成 {len(results)} 个 Hyper 文件")
    return results


if __name__ == "__main__":
    # 调用主函数处理所有CSV文件
    results = process_csv_directory()
    print(f"生成的文件总数: {len(results)}")