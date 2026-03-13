# 医疗档案管理系统（本地单机版）

一个基于 **Flask + SQLite + 原生 HTML/JS** 的本地医疗档案管理系统，适用于诊所/康复中心等场景。  
项目开箱即用：不依赖 Node.js 或前端构建工具，启动后直接通过浏览器访问。

---

## 1. 项目概览

- **后端**：`Flask`（单进程、本地部署）
- **数据库**：`SQLite`（默认文件：`medical_system.db`）
- **前端**：`static/index.html + static/app.js` 单页应用
- **启动方式**：命令行启动 + 桌面启动器（`.bat` / `.pyw`）
- **数据能力**：客户档案、健康评估、预约管理、上门预约、仪器使用、满意度、查询导出、数据库备份

> 系统会在启动时自动初始化数据库表，并创建必要目录（如 `exports/`、`database_backups/`、`logs/`）。

---

## 2. 主要功能

### 2.1 客户与健康档案
- 客户档案管理（新增、编辑、删除、查询）
- 健康评估档案维护（体征、生活方式、病史与健康需求等）
- 健康记录历史查询与详情查看

### 2.2 预约与服务管理
- 到店预约（客户、项目、设备、人员、时间段）
- 上门预约（固定时间窗口校验）
- 冲突校验：支持按时间段检测设备/人员占用
- 预约状态管理（正常、取消等）

### 2.3 运营与分析
- 首页核心统计与近 7 天预约趋势
- 仪器使用统计（次数、总时长、按项目/客户分析）
- 满意度调查录入与评分统计
- 客户活跃度与业务概览

### 2.4 数据管理
- 综合查询（按关键词检索多个业务模块）
- Excel 导出（客户、预约、仪器使用、查询结果）
- 数据库备份（手动/启动时自动备份）
- 支持自定义数据库备份目录

---

## 3. 快速开始

## 3.1 环境要求
- Python **3.8+**（建议 3.10 及以上）
- Windows / macOS / Linux（桌面启动器主要针对 Windows 体验优化）

## 3.2 安装依赖
在项目根目录执行：

```bash
pip install -r requirements.txt
```

## 3.3 启动方式

### 方式 A：命令行启动（跨平台）

```bash
python app.py
```

启动后访问：

- <http://127.0.0.1:5000>
- 或 <http://localhost:5000>

### 方式 B：桌面启动器（Windows 推荐）

- 双击 `启动医疗系统.bat`（显示命令行窗口）
- 双击 `启动医疗系统.pyw`（无命令行窗口）

启动器能力：
- 自动尝试安装依赖（缺失时）
- 自动打开浏览器
- 启动时自动执行一次数据库备份
- 错误写入 `error_log.txt` 与 `logs/startup.log`

---

## 4. 项目结构（当前仓库）

```text
health-agent/
├─ app.py                 # Flask 主程序，API + 数据库初始化 + 导出/备份逻辑
├─ launch.py              # 桌面启动器（自动开浏览器、依赖兜底、启动日志）
├─ requirements.txt       # Python 依赖
├─ README.md              # 项目说明
├─ 启动医疗系统.bat       # Windows 启动脚本（推荐）
├─ 启动医疗系统.pyw       # Windows 启动脚本（无控制台）
├─ 安装依赖.bat           # Windows 一键安装依赖
├─ static/
│  ├─ index.html          # 单页前端界面
│  └─ app.js              # 前端业务逻辑与 API 调用
├─ medical_system.db      # SQLite 数据文件（运行后持续更新）
├─ database_backups/      # 数据库备份目录（运行时自动创建）
├─ exports/               # Excel 导出目录（运行时自动创建）
└─ logs/                  # 应用与启动日志目录（运行时自动创建）
```

---

## 5. 数据与日志说明

- **主数据库**：`medical_system.db`
- **备份目录**：默认 `database_backups/`，可通过系统设置 API 修改
- **导出目录**：`exports/`
- **应用日志**：`logs/app.log`
- **启动日志**：`logs/startup.log`
- **启动异常日志**：`error_log.txt`

建议定期备份以下内容：
1. `medical_system.db`
2. `database_backups/`
3. `exports/`（如需保留历史报表）

---

## 6. 常见问题

### 6.1 端口被占用怎么办？
默认端口为 `5000`。若已被占用，请先释放端口后重启程序，或修改 `app.py`/`launch.py` 中端口配置。

### 6.2 启动器一闪而过怎么办？
优先查看：
- `error_log.txt`
- `logs/startup.log`

常见原因：
- Python 未正确安装或未加入 PATH
- 依赖安装失败（网络/权限问题）
- 端口冲突

### 6.3 如何迁移到新机器？
最小迁移集：
- 代码目录（含 `static/`）
- `medical_system.db`
- （可选）`database_backups/` 与 `exports/`

新机器安装 Python 后执行 `pip install -r requirements.txt`，再启动即可。

---

## 7. 开发说明

- 前端为原生 JS，不需要构建流程；修改 `static/index.html` / `static/app.js` 后刷新页面即可。
- 后端 API 集中在 `app.py`，使用 SQLite 持久化。
- 如需二次开发，建议先备份数据库并在测试副本上验证。

