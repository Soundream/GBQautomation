# Tableau 文件处理指南

## Tableau 文件结构

Tableau 工作簿 (.twbx) 是一个压缩包，包含以下内容：
- .twb 文件：XML格式的主工作簿定义
- Data/ 目录：包含数据源文件（.hyper, .csv等）
- 其他资源：图片、图标等

## 数据源替换流程

### 1. 提取与分析工作簿

使用 `twbx2xml.py` 解压 Tableau 工作簿：

```python
from tableau_processor.xml_of_twbx import extract_templates

# 解压工作簿模板
extract_templates()  # 使用默认路径
```

### 2. 生成 Hyper 文件

使用 `hyper_generator.py` 将 CSV 数据转换为 Hyper 格式：

```python
from tableau_processor.hyper_generator import process_csv_directory

# 使用默认路径和规则文件处理CSV目录
process_csv_directory()
```

日期规则文件格式示例 (date_rules.json):
```json
{
  "date": {
    "key_brands": ["appannie_app_ratings", "web_traffic"],
    "market_share": ["similarweb_tableau_report"],
    "shopcash": ["appannie_tableau_report"]
  },
  "report_date": {
    "key_brands": ["appannie_app_ratings"]
  }
}
```

规则文件说明：
- 第一级键是列名（如"date"、"report_date"）
- 第二级键是文件夹名（"key_brands"、"market_share"、"shopcash"）
- 值是文件名模式列表，使用子字符串匹配（不包括月份/年份）

### 3. 更新工作簿引用

手动编辑 .twb 文件，或使用字符串替换来更新引用：

```python
# 简单的字符串替换示例
with open("path/to/workbook.twb", "r") as f:
    content = f.read()

# 替换月份引用
updated_content = content.replace("202508", "202509")

with open("path/to/updated_workbook.twb", "w") as f:
    f.write(updated_content)
```

### 4. 重新打包工作簿

将更新后的 .twb 文件和新生成的 .hyper 文件重新打包为 .twbx：

1. 创建一个新目录
2. 复制修改后的 .twb 文件到该目录
3. 创建 Data 子目录
4. 复制 .hyper 文件到 Data 目录
5. 将整个目录压缩为 .zip 文件
6. 将扩展名更改为 .twbx

## 注意事项

- 保持数据结构一致（字段名称和数据类型）
- 特别关注日期字段的正确转换
- 不需要修改 object-id，保留原值
- 计算字段会自动使用新数据重新计算