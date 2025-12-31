# 📊 项目亮点/速览

本工具（半成品未全流程验证）实现了BigQuery批量查询、自动数据整理与一键导出CSV，并自动将CSV导入Tableau并自动批量更换所有数据源、筛选器和轴，实现月度竞争对手分析从BigQuery查询到Tableau可视化流程的全自动。

---

## 🛠 工具简介

1. 程序的设计初衷：自动化执行：BigQuery查询→CSV导出→自动将CSV加载至Tableau→替换数据源→更新最近三个月的筛选及坐标轴→重新打包为新TWBX文件。
2. 由于整个程序**未测试跑通全流程**，建议先学会交接文档 `Business Analyst Guide` 中月度报告的手动操作Tableau教程。
3. 由于整个程序未测试跑通全流程，目前建议将“自动将CSV加载至Tableau→替换数据源”这两步保留为人工操作，确保数据导入正确。
    - 由于整个程序都写成了功能模块，所以可以将任意一步替换为人工操作，然后从下一步重新运行。
    - 确保用代码编辑器打开 `GBQautomation` **文件夹**而非单独的PY文件，以理解项目开发思路，并保证各模块路径正确。
    - **建议使用的具体流程为**：
        1. 运行 `data_collection/bq_runner.py` 进行查询并下载最新数据
        2. 打开Tableau，**手动**将下载文件夹 `output/csv` 中的文件依次导入Tableau
        3. **手动**用“替换数据源”功能更新Tableau表格中引用的数据（需要等待Tableau加载许久）
        4. 运行 `tableau_processor/filter_axis_updater.py` 进行筛选条件和坐标轴的更新
        5. 最后**手动**调整各个分类下主图中**公司logo位置**，并修改封面的报告月份
        6. 运行 `tableau_processor/twbx_packager.py` 将项目文件打包回TWBX文件
        7. 用Tableau打开存放在 `output/twbx` 中的TWBX文件进行验证，并导出为PDF，快速翻页检查是否有错漏
4. `key brands` 报告已经搁置许久，所以该项目未真正验证对 `key brands` 的支持性，可能有未预料到的错误。
5. 提醒，最后仍然需要**手动调整**各个分类下主图中**公司logo位置**。

即使未跑通全流程，但是最繁琐的BigQuery查数和每页修改图表筛选和坐标轴的步骤已经得到安全的自动化。

---

## 🧩 首次打开时

1. 保证你具备Google BigQuery访问权限（需要用Jira申请）。
    - 可以在网页BigQuery界面尝试运行一些SQL语句来测试自己是否能正常访问数据库
2. 使用Github Desktop或代码编辑器（推荐Cursor或VScode），克隆项目到本地。
    - 推荐fork本项目到自己的仓库，方便做出修改
    - 也可以直接clone本项目，但是你将只能修改本地代码，无法推送修改到我的Github项目
3. 用代码编辑器打开 `GBQautomation` 文件夹。
4. 在 `auth_credential/apikey.txt.sample` （这只是一个提醒你需要创建apikey的占位文件）旁边新建 `apikey.txt` （真正的apikey）填写API密钥（见团队文档，TXT密钥**不会也不能上传到GitHub**）。
5. 把Tableau模板（上个月的成品）放入 `tableau_processor/tableau_files/templates` 
6. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
7. 打开 `runner.py`，点击运行，它会自动帮你执行Google账号认证（会跳转浏览器，需要登录并授权）。

---

## 📝 代码思路

- 采用模块化设计，主流程（查询数据+导入tableau）在 `runner.py`（暂未投入使用），这个文件会导入并执行2个功能模块 （由于主流程未投入使用，所以暂时直接运行模块PY）。

- 模块0：身份认证。所有认证模块在 `auth_credential/`，使用 Google CLI 认证和 Similar Web API key 认证。

- 模块1：查询数据 `data_collection/`
    - 本模块的主流程为 `bq_runner.py`，导出路径为 `output/csv`
    - SQL单独存储：所有SQL模板和文件命名规则存在 `sql/queries.json` 中，可根据需求增/删/改。
    - 工作流及子模块：
        1. 清空当前的 `output/csv` 文件夹
        2. 补全特殊SQL语句（`sql_processor.py` 会更新 `sql/` 中两个复杂SQL文件的日期）
        3. 遍历 `sql/queries.json` 中的所有SQL语句，下载数据，按规则重命名，并导出为CSV（`bq_runner.py`）
        4. `simple_bq.py` 没有被本项目使用。我保留了这个文件，方便你单独运行它，执行一些其他的查数任务。

- 模块2：导入tableau `tableau_processor/`
    - 本模块的主流程为 `tableau_pipeline.py`（暂未投入使用），导出路径为 `output/twbx`
    - 自动化的最后一公里：将指定CSV批量导入到Tableau，并自动替换原有数据源、同步筛选和坐标轴配置。
    - 工作流及子模块：
        1. 把Tableau解压为数据文件和TWB（xml格式）文件，并存入 `xml_of_twbx/`（`xml_of_twbx/twbx2xml.py`）
        2. 生成CSV文件对应的HYPER文件（属于Tableau的高效数据格式），并存入 `output/hyper`（`hyper_generator.py`）
        3. 移动CSV和HYPER进入Tableau的Data文件夹（`csv_hyper_mover.py`）
        4. 让Tableau表格指向新的数据文件（`smart_meta_replacer.py`）
            - 注1：这一步将所有属于原数据的metadata**原地修改**为新数据的metadata，曲线实现加载。
            - 注2：使用 `xml_metadata_extractor.py` 识别"所有属于原数据的metadata"，存储在 `template_metadata.json`；使用 `csv_hyper_mover.py` 生成随机数作为"新数据的metadata"，存储在 `current_metadata.json`
            - 注3：使用 `compare_keys.py` 检查metadata是否有缺漏
        5. 更新"最近三个月"的月份筛选和坐标轴范围（`filter_axis_updater.py`）
        6. 删除解包产生的 `.DS_Store`，并重新打包回Tableau的TWBX文件（`twbx_packager.py`）

- 一切结束后你还需要手动调整公司图标位置。
    - 可以访问免费网站 [Photopea](https://www.photopea.com/) 来为图标去除白底，并另存为PNG
    - 在有些时候，你需要关注图标结构是否合适，比如，较瘦长的矩形最好使用上下结构的logo，而扁平的使用左右结构
    - 注意，JPEG不支持矢量格式，一定会带有白色背景，所以需要另存为PNG
    - 注意，不要使用把原JPEG格式的网页图片后缀修改为PNG，然后去除背景的方式，这仍然会带有白底。你应该访问 [Photopea](https://www.photopea.com/) 使用官方的另存为PNG的功能。

---

如需帮助或有更多功能诉求，请联系维护人（soundream0502@gmail.com）或提交issue。
