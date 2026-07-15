# 后端项目分析指南（Java / Python）

本文档补充 **JVM（以 Java 为主）** 与 **Python** 仓库的分析要点，与 `frontend-analysis-guide.md` 配合使用；全栈仓库两段都应覆盖。

## Java / JVM

### 1. 识别构建与模块

**关键文件**：

- **Maven**：`pom.xml`（根模块与多模块 `<modules>`）
- **Gradle**：`build.gradle`、`build.gradle.kts`，以及 `settings.gradle*`

**快速判断**：

- 存在 `pom.xml` → Maven；查看 `<packaging>`、`artifactId`、`parent`（如 `spring-boot-starter-parent`）
- 存在 `build.gradle*` → Gradle；关注 `plugins { id("org.springframework.boot") }` 或 `springBoot` 版本

### 2. Spring Boot 常见痕迹

- 依赖含 `spring-boot-starter-web`、`spring-boot-starter-data-*`、`spring-boot-starter-security` 等
- 主类：含 `SpringBootApplication` 的 `*Application.java`（常在 `src/main/java/...`）
- 配置：`src/main/resources/application.yml` / `application.properties`，以及 `application-{profile}.*`

### 3. 结构线索

- **分层**：`controller` / `web`、`service`、`repository` / `dao`、`domain` / `model`、`config`、`exception`
- **API**：`@RestController`、`@RequestMapping`，或 Spring MVC/WebFlux 路由类
- **数据**：JPA 实体与 Repository、MyBatis Mapper XML、`schema.sql` / Flyway / Liquibase

### 4. 命令与版本

- **Maven**：`mvnw` / `mvnw.cmd`、`mvn -v`；脚本常定义在 `pom.xml` 的插件与 `properties`（Java 版本）
- **Gradle**：`gradlew` / `gradlew.bat`；Java toolchain 在 `build.gradle*`
- 从 CI 配置（`.github/workflows`、`Jenkinsfile`）交叉验证构建命令

### 5. 测试

- JUnit 4/5、Mockito、Spring Boot Test、`@SpringBootTest`
- 典型目录：`src/test/java`、`src/test/resources`

---

## Python

### 1. 识别依赖与工具

**关键文件**：

| 文件 | 含义 |
|------|------|
| `pyproject.toml` | 现代标准：PEP 621 `project`、工具 `[tool.poetry]` / `[tool.uv]` / `[tool.setuptools]` |
| `requirements.txt` / `requirements-*.txt` | pip 冻结或分层依赖 |
| `Pipfile` + `Pipfile.lock` | pipenv |
| `setup.py` / `setup.cfg` | 传统打包安装 |

**快速判断框架**：

- **Django**：`django` 依赖，常见 `manage.py`、`*/settings.py`、`urls.py`
- **FastAPI**：`fastapi`、`uvicorn`，常见 `main.py` 或 `app/` 包内 `APIRouter`
- **Flask**：`flask`，常见 `app.py` 或 `application` 工厂

### 2. 目录与入口

- **包布局**：`src/` 布局（`src/package_name/`）或平铺项目根下的包名目录
- **ASGI/WSGI**：`uvicorn`、`gunicorn` 启动参数；`Dockerfile` 中的 `CMD`
- **环境变量**：`.env.example`、`settings` 中的 `os.environ` / `pydantic-settings`

### 3. 结构线索

- **路由**：FastAPI `APIRouter`、Flask `Blueprint`、Django `urlpatterns`
- **配置**：`settings.py`、`config.py`、Pydantic `BaseSettings`
- **数据**：SQLAlchemy/Django ORM 模型、`migrations/`（Alembic/Django）

### 4. 命令与版本

- 从 `README`、`Makefile`、`pyproject.toml` 的 `[project.scripts]` 或文档字符串提取
- 虚拟环境：`venv`、`.venv`、`poetry env`、`uv run` 等（文档中说明推荐方式即可）

### 5. 测试

- **pytest**：`pytest.ini`、`pyproject.toml` `[tool.pytest]`、`tests/` 或 `test_*.py`
- **unittest**：`python -m unittest`

---

## 输出与注意事项

1. 与前端指南相同：**先读依赖与配置文件**，再 Glob 代表性源码。
2. **不要假设** 一定是 Spring 或 Django：以依赖与目录为准命名技术栈。
3. 多模块仓库：说明**模块边界**（Maven module、Gradle subproject、Python 多个包）。
4. 最终章节填充仍以 `assets/explaining-pm-template.md` 中「后端适用」小节为准，无关章节删除。
