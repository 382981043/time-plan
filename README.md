# SmartPlan 时间规划助手

基于 Flask + MySQL 的时间规划与任务复盘系统 MVP，帮助个人用户按照 **SMART 法则** 制定每日任务计划，按照 **重要紧急四象限** 管理任务，并在每天结束后完成任务复盘，由 AI 或 Mock 逻辑自动生成结构化的今日小结。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3 | 主语言 |
| Flask 3.x | Web 框架，提供 REST API 和静态文件服务 |
| PyMySQL | MySQL 数据库驱动 |
| Flask-CORS | 跨域请求支持 |
| PBKDF2-SHA256 | 密码哈希（Python 标准库 hashlib，无额外依赖） |
| MySQL | 关系型数据库 |
| 原生 HTML/CSS/JS | 单文件 SPA，零前端框架依赖 |
| Google Fonts | Inter + Noto Sans SC 字体 |

## 项目结构

```
smart-plan-flask/
├── app.py                 # Flask 启动入口
├── config.py              # 配置读取
├── requirements.txt       # Python 依赖
├── README.md              # 项目说明
├── .env.example           # 环境变量示例
├── .gitignore
├── db/
│   └── schema.sql         # MySQL 建表语句
├── services/
│   ├── __init__.py
│   ├── db_service.py      # 数据库连接服务
│   ├── auth_service.py    # 认证业务逻辑
│   ├── task_service.py    # 任务业务逻辑
│   ├── review_service.py  # 复盘业务逻辑
│   └── ai_service.py      # AI 今日小结生成
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py     # 认证接口
│   ├── task_routes.py     # 任务接口
│   ├── review_routes.py   # 任务复盘接口
│   └── daily_review_routes.py  # 每日复盘接口
├── utils/
│   ├── __init__.py
│   ├── password.py        # PBKDF2-SHA256 密码工具
│   ├── token.py           # HMAC 简易 Token 工具
│   └── response.py        # 统一响应格式
└── static/
    ├── index.html         # SPA 入口
    ├── app.js             # 前端逻辑
    └── style.css          # 样式
```

## 快速开始

### 1. 创建 MySQL 数据库

确保已安装 MySQL，然后执行建表 SQL：

```bash
mysql -u root -p < db/schema.sql
```

或者手动创建：

```sql
CREATE DATABASE IF NOT EXISTS smart_plan DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
USE smart_plan;
-- 然后执行 db/schema.sql 中的建表语句
```

### 2. 创建 Python 虚拟环境

```bash
cd smart-plan-flask

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

方式一：直接修改 `config.py` 中的默认值（最简单）。

方式二：设置环境变量（Windows PowerShell）：

```powershell
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DATABASE="smart_plan"
$env:JWT_SECRET="your_secret_key"
```

方式三：复制 `.env.example` 为 `.env` 并手动 source（需要 python-dotenv 或手动设置）。

### 5. 启动应用

```bash
python app.py
```

### 6. 访问系统

浏览器打开：**http://127.0.0.1:5000**

## API 接口概览

### Auth
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| GET | /api/auth/me | 获取当前用户 |

### Tasks
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tasks | 获取任务列表 |
| GET | /api/tasks/:id | 获取任务详情 |
| POST | /api/tasks | 新增任务 |
| PUT | /api/tasks/:id | 编辑任务 |
| DELETE | /api/tasks/:id | 删除任务 |

### Task Review
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tasks/:id/review | 获取任务复盘 |
| POST | /api/tasks/:id/review | 新增/更新任务复盘 |

### Daily Review
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/daily-reviews | 获取某日复盘 |
| POST | /api/daily-reviews | 保存每日复盘 |
| POST | /api/daily-reviews/generate | 生成 AI 今日小结 |

## 前端页面路由

| Hash 路由 | 页面 |
|-----------|------|
| #/login | 登录页 |
| #/register | 注册页 |
| #/dashboard | 今日计划页 |
| #/task-form | 新增任务 |
| #/task-form?id=1 | 编辑任务 |
| #/quadrant | 四象限视图 |
| #/task-review?id=1 | 任务复盘 |
| #/daily-review | 今日复盘 |
| #/profile | 个人中心 |

## AI 今日小结

- 如果配置了 `AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 环境变量，系统将调用兼容 OpenAI 格式的大模型 API 生成今日小结
- 如未配置 API Key 或调用失败，系统自动降级使用 Mock 逻辑生成结构化的今日小结
- Mock 小结同样按照标准格式输出，包含：今日整体表现、完成较好的地方、存在的问题、四象限时间分配分析、SMART 计划质量分析、明日改进建议、一句话总结

## 测试用例

### 测试用例 1：用户注册登录
1. 访问 http://127.0.0.1:5000，自动跳转登录页
2. 点击「立即注册」创建新用户
3. 注册成功后使用邮箱和密码登录
4. **预期**：登录成功后进入今日计划页，可以看到顶部导航栏

### 测试用例 2：创建 SMART 任务
1. 点击右上角「+ 新增任务」
2. 填写任务标题、日期、时间
3. 填写 SMART 五项内容
4. 勾选「重要」和「紧急」
5. 点击保存
6. **预期**：任务创建成功，今日计划页展示该任务，显示"重要且紧急"标签

### 测试用例 3：四象限分类
1. 创建 4 个任务，分别设置不同重要/紧急组合
2. 点击导航栏「四象限」
3. **预期**：4 个任务分别进入对应象限，分类准确

### 测试用例 4：任务复盘
1. 在今日计划页选择一个任务，点击「复盘」
2. 填写实际执行情况、问题、收获和评分
3. 保存复盘
4. **预期**：复盘保存成功，再次进入可看到已填写内容，任务状态同步更新

### 测试用例 5：生成今日小结
1. 创建多个任务并完成部分复盘
2. 进入「今日复盘」页
3. 点击「生成 AI 今日小结」
4. **预期**：展示任务统计，生成结构化 markdown 今日小结（Mock 或 AI 均可）

## 常见问题

**Q: 启动时提示数据库连接失败？**
A: 请检查 MySQL 是否已启动，以及 `config.py` 中的数据库连接信息是否正确。

**Q: 如何创建测试账号？**
A: 直接通过注册页面创建即可，或手动在 MySQL 中插入用户（注意密码需使用 PBKDF2-SHA256 哈希）。

**Q: 可以不使用 MySQL 吗？**
A: MVP 阶段仅支持 MySQL。如需切换数据库，可修改 `services/db_service.py` 中的连接逻辑。

**Q: AI 今日小结不工作？**
A: 这是正常的——系统会降级使用 Mock 小结。如需真实 AI 生成，请配置 `AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 环境变量。

## 后续扩展建议

- 增加任务拖拽排序和日历视图
- 支持周/月计划视图
- 增加数据统计图表（完成率趋势、时间分布等）
- 支持多人协作和团队看板
- 集成更多大模型（Claude、Gemini 等）
- 增加邮件/微信提醒通知
- 打包为 Docker 镜像方便部署
