# ContentForge Desktop UI 设计说明

## 通用布局与交互
- **框架**：左侧固定导航，右侧为主内容区；顶部显示当前工作目录与状态；底部全局 Console（实时日志、复制、清空、暂停滚动、导出，可作为交互式终端接受用户输入）。
- **工作目录选择**：每个界面顶部提供目录选择器与“设为默认”按钮；未填时使用全局默认。
- **运行/终止按钮**：提交后变为“运行中…/终止”，任务结束恢复；显示命令预览（脚本 + 参数）。
- **表单校验**：必填项高亮；对路径、ID、范围做前置校验，防止空跑。
- **反馈**：成功/失败 toast；错误摘要附带复制按钮；日志可一键复制。
- **帮助按钮**：每个界面统一提供“帮助”按钮，弹出该模块使用说明（文档将后续补充）。

## 界面分组
对应 `UI_design` 目录的视觉稿，按侧边导航描述（最后一个模块为 Downloaders：Bomtoon 与 Diritto）。

### 1) Dashboard（contentforge_dashboard）
- **信息卡片**：默认工作目录、AI 配置状态、上次运行结果、最近 5 条任务（状态/耗时/入口）。
- **快捷操作**：
  - 打开设置（修改工作目录、AI Key）。
  - 重新运行上次任务（带参数回填确认）。
- **Console**：显示最近一次任务或全局消息，可切换“全局/当前模块”视图。
### 2) Comic Processing - Image to PDF（comic_processing_-_image_to_pdf）
- **输入区**：源图片目录、输出目录、可选 DPI/质量参数；允许保存为预设。
- **流程选择**：仅暴露 V5 智能融合流程；隐藏/不提供 V2、V4 入口。
- **工具按钮**：
  - `快速图片转 PDF` (`convert_img_to_pdf.py`)
  - `PDF 合并` (`merge_pdfs.py`)
  - `PDF 转图片/长图分割` (`convert_long_pdf.py`)
- **Console**：显示进度百分比（如脚本输出页码或文件名时附带进度条）。

### 3) Ebook Workshop - Format Conversion（ebook_workshop_-_format_conversion）
采用分栏或标签页呈现：
- **创建/转换**：
  - `TXT → EPUB`：TXT 路径、封面、样式下拉（读取 `shared_assets/epub_css`）、章节规则选择、输出目录。
  - `Markdown 文件夹 → HTML`：源文件夹、是否压缩资源。
  - `EPUB → TXT`：EPUB 路径、是否保留章节分隔。
- **编辑/修复**：
  - `EPUB 重命名`、`繁转简`、`竖排修复+繁转简`、`EPUB 清理`（封面/字体/CSS 选项）。
  - `批量替换`、`CSS 样式美化`、`EPUB 分割`、`EPUB 合并`、`解包/封装`、`标点补全 (v1/v2)`。
- **Console**：按任务分节输出，支持折叠长日志。

### 4) File Repair（file_repair）
作为 Ebook Workshop 的子标签/分组，聚合原 04 模块：
- `修复封面` (`cover_repair.py`)
- `修复 CSS 链接/字体` (`css_fixer.py`)
- `TXT 编码修复` (`fix_txt_encoding.py`)
- `TXT 重新排版` (`txt_reformat.py`)
- `提取 EPUB CSS` (`extract_epub_css.py` 从 org 模块迁入)
表单均包含输入/输出路径，支持批量文件夹模式。

### 5) Library Organization（library_organization）
- **智能整理/翻译重命名**：输入根目录，勾选“翻译/加拼音前缀/仅重排”；AI Key 状态提示与快捷跳转设置。
- **纯整理（不翻译）**：新增按钮/表单，复用上方参数但默认关闭翻译，仅做分类与重排。
- **文件夹加解密**：选择模式（加密/解密）、目标目录、密码输入框（可显示/隐藏）。
- **Console**：突出显示重命名/加密结果摘要，可导出操作报告。

### 6) Downloaders（bomtoon + diritto，最后一个子界面）
- **Bomtoon**（参考 acquisition_screen 设计稿）：
  - 凭证管理：按钮“更新/生成登录凭证”（macOS 专用；Windows 显示禁用提示）。
  - 发现漫画：关键词搜索、列出已购、按 Comic ID 列出章节。
  - 下载漫画：输入 Comic ID、输出目录；模式按钮：特定章节（多选章ID）/ 全部 / 序号范围；可选先自动列出章节（默认开启）。
  - 实现策略：优先尝试通过 API 复刻原脚本；若不可行，Console 需支持交互式输入（类 PowerShell）与脚本对话。
  - Console：紧贴表单右/下方，显示步骤化日志，提供命令复制。
- **Diritto**（无独立设计稿）：
  - 表单：批量输入小说链接/ID（多行文本或列表框）、输出目录、可选并发配置。
  - 行为：运行按钮触发 `diritto_downloader.py`（暂不修复内部 bug，只做交互外壳）；日志显示下载进度与失败章节，可导出。

### 7) Settings（全局）
- 默认工作目录选择与验证（持久化到 `cfg.json`）。
- AI 翻译配置（API Key/Base URL/Model），带测试按钮（持久化到 `cfg.json`）。
- 日志保留策略（天数/大小）。
- 前端首选项：主题色、语言、是否自动滚动 Console（持久化到 `cfg.json`）。

## Console 行为细则
- 每个界面均固定放置 Console；支持：复制全部、清空、暂停滚动、导出到文件、错误高亮（stderr）。
- 任务结束后 Console 保留历史，侧边“最近任务”列表可点击回放日志并复用参数。

## 适配说明
- Mac-only 功能（`update_token.py`）在 Windows 下置灰并显示说明；其余按钮在 Windows 全量可用。
- Chrome 依赖的脚本需在界面提示检测结果，并允许用户选择 Chrome 路径。
