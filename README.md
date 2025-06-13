# ChefMate AI - 后端 (Django)

欢迎来到 ChefMate AI 的后端部分！本项目基于 Django 和 Django REST Framework 构建，提供一个强大的菜谱管理、用户系统和购物清单 API。

## 功能特性

- **用户认证**：基于 `simple-jwt` 的 Token 认证系统，支持注册、登录和 Token 刷新。
- **菜谱管理**：完整的菜谱 CRUD (增删改查) 功能，包括食材、步骤、图片上传。
- **智能推荐**：根据用户已有食材推荐匹配度高的菜谱。
- **个性化**：支持用户收藏菜谱、标记不吃的食材。
- **库存与购物清单**：管理个人食材库存和购物清单，支持一键从菜谱添加。
- **API 文档**：通过 `drf-yasg` 自动生成 Swagger 和 ReDoc API 文档。

## 技术栈

- **框架**: [Django](https://www.djangoproject.com/), [Django REST Framework](https://www.django-rest-framework.org/)
- **数据库**: [PostgreSQL](https://www.postgresql.org/) (推荐), 也可配置为其他 Django 支持的数据库。
- **认证**: [djoser](https://djoser.readthedocs.io/), [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/)
- **API文档**: [drf-yasg](https://drf-yasg.readthedocs.io/)
- **环境配置**: [python-decouple](https://pypi.org/project/python-decouple/)

---

## 环境搭建与运行指南

### 1. 先决条件

- Python 3.9+
- Pip (Python 包管理器)
- PostgreSQL 数据库服务正在运行

### 2. 克隆项目

```bash
git clone https://your-repository-url.com/ChefMateAI.git
cd ChefMateAI
```

### 3. 创建并激活虚拟环境

建议使用虚拟环境来隔离项目依赖。

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```
*(注意：您可能需要先通过 `pip freeze > requirements.txt` 命令在您的项目中生成此文件。)*

### 5. 配置环境变量

在项目的根目录（与 `manage.py` 同级）创建一个名为 `.env` 的文件。这个文件用于存放敏感信息，不会被提交到 Git。

复制以下内容到 `.env` 文件，并根据您的实际情况修改：

```env
# Django 设置
SECRET_KEY='your-strong-secret-key-here'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# 数据库设置 (PostgreSQL 示例)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=chefmate_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### 6. 数据库迁移

确保您的 PostgreSQL 数据库服务已启动，并且您已创建了名为 `chefmate_db` 的数据库。

然后，运行以下命令来创建数据库表结构：

```bash
python manage.py migrate
```

### 7. 创建超级用户

为了访问 Django Admin 后台，您需要创建一个超级用户。

```bash
python manage.py createsuperuser
```
按照提示输入用户名、邮箱和密码。

### 8. 运行开发服务器

一切就绪！现在可以启动后端服务了。

```bash
python manage.py runserver
```

默认情况下，后端 API 将运行在 `http://127.0.0.1:8000/`。

---

## API 端点

项目启动后，您可以访问以下端点：

- **API 根路径**: `http://127.0.0.1:8000/api/`
- **Swagger UI (API 文档)**: `http://127.0.0.1:8000/swagger/`
- **ReDoc (API 文档)**: `http://127.0.0.1:8000/redoc/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`

主要 API 资源包括：
- `/api/users/`
- `/api/recipes/`
- `/api/ingredients/`
- `/api/shopping-list/`
- 等等...

更多详细信息，请查阅自动生成的 API 文档。