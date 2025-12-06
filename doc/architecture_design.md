# ContentForge Desktop 重构设计文档

## 1. 目标与范围
- 将现有脚本集合重构为 **前后端分离的 Windows 桌面应用**，前端提供统一 UI，后端复用 Python 脚本执行。
- 所有功能入口由 UI 按钮触发，实时打印 stdout/stderr 到可复制的 Console 框，并可配置脚本执行目录。
- 目录与模块调整遵循 `structure.txt`：合并/重命名既有模块，保留有效脚本、移除过时 CLI 包装。

## 2. 目标目录结构（重构后）
```
project-root/
├── backend/                  # 新增：Python 服务 (FastAPI + 子进程执行)
│   ├── app.py                # 入口，启动 API 与 WebSocket 日志流
│   ├── routers/              # 模块路由 (downloaders, comic, ebook, org, settings)
│   ├── services/
│   │   ├── runner.py         # 子进程执行与日志捕获
│   │   └── scripts_catalog.py# 脚本元数据、命令模板、平台可用性
│   └── models.py             # DTO/配置模型
├── frontend/                 # React(Vite) 前端源码，构建为静态资源供 WebView 加载
│   ├── src/
│   └── package.json
├── downloaders/              # 合并 acquisition + downloader，含 bomtoon 与 diritto 子目录
├── comic_processing/         # 原 02_comic_processing（去掉数字前缀）
├── ebook_workshop/           # 原 03_ebook_workshop 并入原 04_file_repair + extract_epub_css.py
├── file_organization/        # 原 05_library_organization 重命名
├── shared_assets/
├── shared_utils/
└── doc/
```
- **删除/归档**：`04_file_repair/` 整体并入 `ebook_workshop/`；各 `*_start_up.py` 及 `main.py` 仅保留为兼容参考，正式发布可移除；`acquisition/` 与 `downloader/` 逻辑合并至 `downloaders/`（内部区分 bomtoon 与 diritto）。

## 3. 高层架构
- **前端**：React + Vite 组件化 UI，构建为静态资源，由轻量级 WebView (pywebview) 加载；调用本地 API（HTTP）+ WebSocket 实时日志。侧边导航 + 主区卡片/表单 + 底部 Console（可复制/清空/暂停滚动）。模块命名与导航均不再带数字前缀。
- **后端**：FastAPI 服务，负责配置管理、脚本编排、进程生命周期、日志流转、文件选取校验。
- **脚本执行**：后端以子进程调用现有 Python 脚本；命令参数由前端表单组装后传入；工作目录可 per-run 覆盖全局默认。
- **日志通路**：子进程 stdout/stderr 逐行读取，通过 WebSocket 推送到前端 Console，并写入滚动日志文件（便于问题回溯、复制）。
- **状态存储**：`shared_assets/cfg.json` 持久化默认工作目录、AI 配置、最近任务、常用路径等；前后端共享，避免每次启动重新填写。

### 典型交互流程
1) 用户在某界面选择输入/输出路径、参数 → 2) 前端 `POST /tasks` 创建任务并打开 WebSocket 订阅 → 3) 后端创建子进程运行脚本，实时推送日志 → 4) 进程结束后返回成功/错误状态；前端允许复制日志、重新运行。若接口化可行（例如漫画获取 API），则优先通过 API 直接操作，子进程模式作为回退。

## 4. 后端设计
- **技术栈**：Python 3.12、FastAPI、Uvicorn、Pydantic、`asyncio.create_subprocess_exec` 或 `subprocess.Popen`（行缓冲）。
- **模块划分**
  - `routers/*`: 按业务分组提供 API（如 `/downloaders/bomtoon`, `/downloaders/diritto`, `/comic/pipeline`, `/ebook/repair`, `/org/translate`, `/settings`）。
  - `services/runner.py`: 通用执行器，封装启动、取消、超时、工作目录校验、环境变量（如 LANG）及平台检测。
  - `services/scripts_catalog.py`: 维护脚本清单、命令模板、输入约束、平台可用性（如 `update_token.py` 仅 macOS）。
  - `models.py`: 请求/响应模型，含参数校验（路径存在、枚举值、必填字段）。
- **日志流**：
  - 子进程以 `bufsize=1, text=True` 打开 stdout/stderr；后台任务逐行读取并推送 WebSocket；落盘到 `logs/<date>/<task-id>.log`。
  - 支持前端命令：复制全部、导出文件、清屏、暂停/恢复自动滚动。
- **任务管理**：
  - `POST /tasks`: 创建任务，返回 task_id；`DELETE /tasks/{id}` 终止子进程；`GET /tasks/{id}` 查询状态（running/succeeded/failed/canceled）。
  - 并发限制：可选令牌桶限制同时运行数，防止并行脚本竞争同一目录。
- **配置管理**：
  - `GET/PUT /settings`: 读写 `shared_assets/cfg.json`；字段：`default_work_dir`, `ai_config(api_key, base_url, model_name)`, `recent_tasks`, `favorite_paths` 等。
  - 路径分发：如果请求未传 `workdir`，后端自动填充 `default_work_dir`。
- **平台兼容**：
  - `update_token.py` 标记为 mac-only，Windows 前端显示禁用提示。
 - 确保路径拼接统一使用 `pathlib` / `os.path.join`，编码使用 UTF-8；必要时为 `diritto_downloader.py` 添加 Windows 兼容逻辑（路径、编码、requests TLS）。
  - **安全/健壮性**：限制可执行的脚本白名单；对输入路径进行存在性与可写性检查；超时与退出码捕获，附带 stderr 摘要。

## 5. 前端设计
- **技术栈**：React + Vite + TypeScript；UI 库建议 Ant Design / MUI；pywebview 负责窗口管理并指向本地 FastAPI/静态资源。
- **布局**：固定侧边导航（Dashboard、Comic、Ebook & Repair、Organization、Downloaders〔Bomtoon + Diritto，放在最后一个模块〕、Settings）；顶部展示当前工作目录与状态；主内容按卡片/表单分块；底部通用 Console。
- **通用组件**
  - `WorkdirPicker`: 选择/保存运行目录，覆盖全局默认。
  - `RunButton`: 触发后禁用为“运行中…”，支持“终止”。
  - `Console`: 日志流显示、关键字高亮、复制、清空、保存文件、暂停自动滚动。
  - `ParamForm`: 每个功能的参数表单，校验必填项，展示脚本名与命令预览。
  - `HelpButton`: 每个界面必备，点击弹出该模块的使用说明（后续补充模块文档）。
- **状态管理**：使用 Zustand/Recoil；缓存最近任务、常用路径、AI 配置；失败/成功弹窗。
- **资源引用**：`shared_assets/epub_css` 用于 EPUB 样式选择下拉；UI 示意参照 `UI_design/*/code.html + screen.png`。

## 6. 模块与脚本映射（按钮设计）
- **Dashboard**：展示默认工作目录、最近任务、快捷入口（打开设置、重跑上次任务）。

- **Comic Processing**
  - V5 智能融合 → `image_processes_pipeline_v5.py`（对外仅暴露此流程，V2/V4 不再在 UI 中出现）。
  - 快速图片转 PDF → `convert_img_to_pdf.py`。
  - PDF 合并 → `merge_pdfs.py`。
  - PDF 转图片/长图分割 → `convert_long_pdf.py`。

- **Ebook Workshop & Repair**
  - 创建/转换：`txt_to_epub_convertor.py`, `convert_md_to_html.py`, `epub_to_txt_convertor.py`。
  - 元数据/文字：`epub_rename.py`, `epub_convert_tc_to_sc.py`, `epub_reformat_and_convert_v2.py`。
  - 清理/样式：`epub_cleaner.py`, `epub_styler.py`, `extract_epub_css.py`（从原 05 移入）。
  - 高级工具：`batch_replacer_v2.py`, `split_epub.py`, `epub_merge.py`, `epub_toolkit.py`, `punctuation_fixer.py` / `punctuation_fixer_v2.py`。
  - 文件修复（原 04）：`cover_repair.py`, `css_fixer.py`, `fix_txt_encoding.py`, `txt_reformat.py`。

- **File Organization (原 05)**
  - 智能整理/翻译/重命名 → `translate_and_org_dirs.py`（需 AI 配置）。
  - 纯整理（不翻译，仅分类/重排）→ 新增脚本，参考翻译版实现，去除翻译调用。
  - 文件夹加解密 → `folder_codec.py`。
  - （原 `extract_epub_css.py` 已迁移到 ebook_workshop，不再暴露在此界面）。

- **Downloaders（Bomtoon + Diritto）**
  - Bomtoon（原 acquisition）：
    - 更新/生成登录凭证 → `update_token.py`（Mac-only，Windows 显示提示）。
    - 列出已购漫画 → `bomtoontwext.py list-comic`。
    - 关键词搜索 → `bomtoontwext.py search <keyword>`。
    - 列出章节 → `bomtoontwext.py list-chapter <comic_id>`。
    - 下载特定章节 → `bomtoontwext.py dl -o <dir> <comic_id> <chapter_ids>`。
    - 下载全部章节 → `bomtoontwext.py dl-all -o <dir> <comic_id>`。
    - 按序号范围下载 → `bomtoontwext.py dl-seq -o <dir> <comic_id> <seq>`。
    - **改造要求**：优先调研是否能复刻上述功能为直接 API 调用；若无法实现，UI 中的 Console 需支持交互式输入（类 PowerShell），以便与原脚本对话，而不仅是只读日志。
  - Diritto（原 downloader）：
    - 小说下载器 → `diritto_downloader.py`（暂不修复 bug；改造为批量输入小说链接/ID 的交互式外壳，日志可导出；核心下载逻辑后续迭代）。

- **Settings**
  - 默认工作目录设置/校验。
  - AI 翻译 API Key/Base URL/Model 管理。
  - 查看/清理日志与缓存。

## 7. 删除与归档清单
- **删除/不再使用的 CLI 包装**：`main.py`、`01_start_up.py`、`02_start_up.py`、`03_start_up.py`、`04_start_up.py`、`05_start_up.py`、`07_start_up.py`（保留核心脚本；如需命令行可在 doc 中提供新用法）。
- **目录**：`04_file_repair/` 移除，内部脚本迁移至 `03_ebook_workshop/`。
- **搬移**：`05_library_organization/` 重命名为 `file_organization/`；其中 `extract_epub_css.py` 移至 `03_ebook_workshop/`。
- **临时文件**：清理 `.DS_Store`、旧日志等无关发布文件。

## 8. 渐进式落地计划
1) 完成目录重排与脚本搬移，更新引用路径与 README。
2) 后端骨架：FastAPI + runner + WebSocket 日志；提供任务创建/查询/取消、设置接口。
3) 前端框架：侧边导航 + Console 组件 + 全局工作目录状态；接入 Dashboard。
4) 按模块逐屏接入按钮与表单，联调脚本参数与日志。
5) 针对 Windows 适配与回归测试（路径、编码、Chrome 依赖、diritto 交互外壳验证）。
6) PyInstaller + pywebview 打包与分发，验证无 Python 环境场景（内置 Python 运行时和依赖）。

## 9. 待解决事项
- `diritto_downloader.py` 需明确 bug 点（抓取失败/分页/编码）后修复。
- `update_token.py` 需评估 Windows 替代方案；如无法支持，在 UI 做能力提示。
- Chrome 依赖的下载功能需检测浏览器路径；必要时允许用户手动选择 Chrome 可执行文件。

## 10. 打包与分发（无需安装的 Windows 可执行，去除 Electron）
- **目标**：产出可直接运行的便携式 `.exe`，无需用户安装 Python 或 Node。
- **方案**：
  - 构建前端（React/Vite）为静态文件，打入 `backend/static/`（或同级资源目录）。
  - 使用 pywebview 作为轻量窗口容器，加载本地 FastAPI 提供的页面或本地静态文件。
  - 使用 PyInstaller（onefile 或 onedir 便携版）将 FastAPI + 脚本执行器 + pywebview + 前端静态资源 + `shared_assets` 一并打包。
  - 在 PyInstaller 产物内嵌入 Python 3.12 运行时及 `requirements.txt` 依赖（通过 `--hidden-import`/`--add-data`）。
- **启动顺序**：单一可执行启动 → 检查/创建日志目录与 `cfg.json`（如不存在则初始化默认值）→ 后端（FastAPI/uvicorn）在线程中启动，暴露本地端口或文件 URL → pywebview 打开窗口指向该地址/文件。
- **更新策略**：提供完整包下载替换（便携版），无需安装；如需增量更新，可后续集成自更新逻辑。
- **帮助文档分发**：随包内置模块帮助文档（后续补充），HelpButton 直接从本地资源加载。
