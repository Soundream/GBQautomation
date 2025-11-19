# 📊 项目亮点/速览

本工具实现了BigQuery批量查询、自动数据整理与一键导出CSV，并自动将CSV导入Tableau并自动批量更换所有数据源、筛选器和轴，实现业务分析从查询到可视化全自动化。

---

## 🛠 工作流

1. 直接运行项目根目录下的 `runner.py`。
2. 程序依次完成：BigQuery查询→CSV导出→自动加载至Tableau→替换数据源→重新打包为新TWBX文件。
3. 最后仍然需要手动调整企业图标位置。

---

## 🧩 首次打开时

1. 保证具备Google BigQuery访问权限（需要申请）。
2. 使用Github Desktop或代码编辑器（推荐Cursor或VScode），克隆本仓库到本地。
3. 用代码编辑器打开 `GBQautomation` 文件夹。
4. 在 `auth_credential/apikey.txt.sample` 旁边新建 `apikey.txt` 填写API密钥（见团队文档，TXT密钥不会也**不能上传到GitHub**）。
5. 把Tableau模板放入 `tableau_processor/tableau_files/templates` 
6. 执行依赖安装：```pip install -r requirements.txt```
7. 打开 `runner.py` ，点击运行，它会自动帮你执行Google账号认证（会跳转浏览器，需要登陆并授权）。

---

## 📝 代码思路

- 采用模块化设计，主流程（查询数据+导入tableau）在 `runner.py`，这个文件会导入并执行2个功能模块。
- 模块0：身份认证。所有认证模块在 `auth_credential/` ，使用 Google CLI 认证和 Similar Web API key 认证。

- 模块1：查询数据 `data_collection/`
    - 本模块的主流程为 `bq_runner.py` ，导出路径为 `output/csv`
    - SQL单独存储：所有SQL模板和文件命名规则存在 `sql/queries.json` 中，可根据需求增/删/改。
    - 工作流及子模块：
        1. 清空当前的 `output/csv` 文件夹
        2. 补全特殊SQL语句（ `sql_processor.py` 会更新 `sql/` 中两个SQL文件的日期）
        3. 遍历 `sql/queries.json` 中的所有SQL语句，下载数据，按规则重命名，并导出为CSV （ `bq_runner.py` ）
        4.  `simple_bq.py` 没有被使用。你可以单独运行它，执行重复性的任务。

- 模块2：导入tableau `tableau_processor/`
    - 本模块的主流程为`tableau_pipeline.py`，导出路径为 `output/twbx`
    - 自动化的最后一公里：将指定CSV批量导入到Tableau，并自动替换原有数据源、同步筛选和坐标轴配置。
    - 工作流及子模块：
        1. 把Tableau解压为数据文件和TWB（xml格式）文件，并存入 `xml_of_twbx/` （ `xml_of_twbx/twbx2xml.py` ）
        2. 生成CSV文件对应的HYPER文件（属于Tableau的高效数据格式），并存入 `output/hyper` （ `hyper_generator.py` ）
        3. 移动CSV和HYPER进入Tableau的Data文件夹 （ `csv_hyper_mover.py` ）
        4. 让Tableau表格指向新的数据文件 （ `smart_meta_replacer.py` ）
            注1：这一步将所有属于原数据的metadata**原地修改**为新数据的metadata，曲线实现加载。
            注2：使用 `xml_metadata_extractor.py` 识别“所有属于原数据的metadata”，存储在 `template_metadata.json`；使用 `csv_hyper_mover.py` 生成随机数作为“新数据的metadata”，存储在 `current_metadata.json`
            注3：使用 `compare_keys.py` 检查metadata是否有缺漏
        5. 更新“最近三个月”的月份筛选和坐标轴范围 （ `filter_axis_updater.py` ）
        6. 删除 `.DS_Store` ，重新打包回Tableau的TWBX文件。

- 一切结束后你还需要手动调整公司图标位置。
    - 可以访问 `https://www.photopea.com/` 来为图标去除白底，并另存为PNG

---

如需帮助或有更多功能诉求，请联系维护人或提交issue。
