# 📘 LLMGrader

基于大语言模型（LLM）的自动化课程评分系统，专为技术类实验课程设计，支持批量处理学生提交的 Markdown 实验报告、项目结构和 Git 提交流程，生成结构化评分结果，提升教学评估效率与一致性。

---

## 🚀 功能亮点

- **Markdown 报告评分**：智能分析学生提交的 Markdown 报告内容
- **目录结构解析**：结合 `tree` 结果判断报告配图、组织规范性
- **Git 提交流程审查**：基于 `git log` 判断提交合理性与过程规范性
- **大模型评分生成**：使用 DeepSeek / GPT 等模型生成结构化 JSON 评分
- **批量任务处理**：支持一次性处理多个学生仓库的作业内容

---

## 🔐 提示词注入防护

系统通过以下机制防止学生在报告中嵌入攻击性提示词操控评分结果：

1. **边界隔离包装**：将 Markdown、tree、git log 分别用明确标记包裹，防止指令穿透
2. **系统身份强化**：在提示词中声明评分身份为"不可更改的助教"，忽略任何角色操控语句
3. **结构化输出约束**：模型强制以 JSON 格式返回评分结果，避免非结构化干扰

---

## 📂 项目结构

```
llmgrader/
├── llm_gen/                # 核心功能模块
│   ├── llm_gen.py          # 批量评分主程序，支持命令行参数配置
│   ├── extract.py          # Markdown + tree + git 信息提取工具
│   ├── fs_utils.py         # 文件系统工具函数
│   ├── llm_utils.py        # 调用 LLM 模型工具（DeepSeek / OpenAI）
│   ├── prompt_utils.py     # 提示词拼接与加载工具
│   └── prompt_template/    # 各章节评分提示词模板目录
├── clone.sh                # 学生仓库批量克隆脚本
├── branch.sh               # 切换/修正学生分支的脚本
├── main.sh                 # 一键批量处理所有章节作业的脚本
└── README.md               # 项目说明文档
```

---

## 🛠️ 使用流程

### 1. 克隆学生仓库

```bash
curl --header "PRIVATE-TOKEN: <your_access_token>" "https://git.cuc.edu.cn/api/v4/groups/ccs%2F2025-penetration/projects?per_page=100" > projects.json
# 获取所有项目URL
jq -r '.[].http_url_to_repo' projects.json > repo_urls.txt
# 克隆所有项目
bash clone.sh
```

### 2. 处理仓库分支

```bash
bash branch.sh
```

### 3. 创建 openai.key

在 `llm_gen/` 目录下创建 `openai.key` 文件，并填入你的 API Key。


### 4. 启动评分

#### 方法一：使用主脚本自动处理所有章节（推荐）

使用 `main.sh` 脚本可以自动遍历所有章节模板并进行批量评分：

```bash
# 使用默认配置运行所有章节评分
bash main.sh

# 自定义参数
bash main.sh -b "/path/to/student/repos" -o "results" -t "/path/to/templates"
```

参数说明：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `-t` | 提示词模板目录路径 | `/home/OS-Fuzz/2025/zllm/prompt_template` |
| `-b` | 学生目录基础路径 | `/home/OS-Fuzz/2025` |
| `-o` | 输出目录 | `output` |
| `-h` | 显示帮助信息 | - |

#### 方法二：手动指定章节评分

使用命令行参数来灵活配置单个章节的评分过程：

```bash
python3 llm_gen/llm_gen.py [-b BASE_DIR] [-o OUTPUT_DIR] [-c CHAPTER_ID] [-t TEMPLATE_DIR] [-s] [-f]
```

参数说明：

| 参数 | 长参数 | 说明 | 默认值 |
| --- | --- | --- | --- |
| `-b` | `--base-dir` | 学生目录的基础路径 | `/home/OS-Fuzz/2025` |
| `-o` | `--output-dir` | 输出目录 | `output` |
| `-c` | `--chapter-id` | 章节ID | `0x01` |
| `-t` | `--template-dir` | 提示词模板基础目录 | `/home/OS-Fuzz/2025/zllm/prompt_template` |
| `-s` | `--skip-existing` | 跳过已处理的学生 (默认启用) | - |
| `-f` | `--force-reprocess` | 强制重新处理所有步骤 | - |

示例：
```bash
# 评分第一章作业，指定基础目录和输出目录
python3 llm_gen/llm_gen.py -b "/path/to/student/repos" -o "results" -c "0x01"

# 强制重新评分，不跳过已处理的学生
python3 llm_gen/llm_gen.py -b "/path/to/student/repos" -o "results" -c "0x01" -f --no-skip-existing
```

---

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

---

## 📁 环境要求

- Python ≥ 3.8
- Git 命令行工具
- DeepSeek 或 OpenAI 接口访问权限

> 请在 `llm_gen/` 目录下创建 `openai.key` 文件以保存你的 API Key。

---

## 🧱 注意事项

- 学生作业必须为 Markdown 格式报告
- 模型默认以 JSON 格式输出评分项及总分
- 推荐使用 DeepSeek Reasoner 或 GPT-4 系列模型以获得更佳效果

---

## 🧠 开发说明

- 添加章节：在 `prompt_template/` 下新建目录并放入对应评分模板
- 自定义评分逻辑：修改 `llm_utils.py` 中 prompt 拼接与调用逻辑
- 扩展格式支持：修改 `extract.py` 以兼容其他报告类型（如 Jupyter、PDF 转 Markdown）

