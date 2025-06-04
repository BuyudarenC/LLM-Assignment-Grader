# 📘 LLMGrader

基于大语言模型的自动化课程评分系统，专为技术类实验课程设计

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 📑 目录

- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
- [安装](#-安装)
- [使用方法](#-使用方法)
- [项目结构](#-项目结构)
- [配置说明](#-配置说明)
- [安全机制](#-安全机制)
- [贡献指南](#-贡献指南)
- [致谢](#-致谢)
- [许可证](#-许可证)

---

## 🎯 项目介绍

LLMGrader 是一个智能化的课程评分系统，利用大语言模型（LLM）自动评估学生提交的技术类实验报告。系统支持批量处理 Markdown 报告、分析项目结构和审查 Git 提交历史，生成标准化的评分结果，显著提升教学评估的效率与一致性。

---

## ✨ 功能特性

- 🔍 **智能报告分析**：深度解析 Markdown 格式的实验报告内容
- 📁 **结构规范检查**：基于 `tree` 命令结果评估项目组织规范性
- 🔄 **Git 流程审查**：通过 `git log` 分析提交历史的合理性
- 🤖 **AI 驱动评分**：集成 DeepSeek/GPT 等先进模型生成结构化评分
- ⚡ **批量处理**：支持同时处理多个学生仓库的作业内容
- 🛡️ **注入防护**：内置多重安全机制防止恶意提示词攻击

---

## 🚀 快速开始

### 前置要求

- Python ≥ 3.8
- Git 命令行工具
- DeepSeek 或 OpenAI API 访问权限

### 快速安装

```bash
# 克隆项目
git clone <repository-url>
cd LLM_auto_homework_check

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
echo "your-api-key-here" > llm_gen/openai.key
```

### 立即运行

```bash
# 一键处理所有章节（推荐）
bash main.sh

# 或者处理特定章节
python3 llm_gen/llm_gen.py -c "0x01"
```

---

## 🔧 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd LLM_auto_homework_check
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

在 `llm_gen/` 目录下创建 `openai.key` 文件：

```bash
echo "your-deepseek-or-openai-api-key" > llm_gen/openai.key
```

---

## 📖 使用方法

### 方法一：全自动批处理（推荐）

使用主脚本自动处理所有章节：

```bash
bash main.sh
```

支持自定义参数：

```bash
bash main.sh -b "/path/to/student/repos" -o "results" -t "/path/to/templates"
```

### 方法二：指定章节处理

```bash
python3 llm_gen/llm_gen.py [选项]
```

#### 命令行参数

| 参数 | 长参数 | 描述 | 默认值 |
|------|--------|------|---------|
| `-b` | `--base-dir` | 仓库基础路径 | `/home/course/2025` |
| `-o` | `--output-dir` | 输出目录 | `output` |
| `-c` | `--chapter-id` | 章节标识符 | `0x01` |
| `-t` | `--template-dir` | 模板目录路径 | `/home/course/2025/zllm/prompt_template` |
| `-s` | `--skip-existing` | 跳过已处理项目 | 默认启用 |
| `-f` | `--force-reprocess` | 强制重新处理 | - |

#### 使用示例

```bash
# 基本用法
python3 llm_gen/llm_gen.py -c "0x02"

# 自定义路径
python3 llm_gen/llm_gen.py -b "/custom/path" -o "my_results" -c "0x03"

# 强制重新处理
python3 llm_gen/llm_gen.py -c "0x01" -f
```

### 学生仓库批量克隆

如需批量处理学生作业，可使用提供的脚本：

```bash
# 1. 获取项目列表
curl --header "PRIVATE-TOKEN: <token>" \
     "https://github.com/api/v4/groups/ccs%2F2025-penetration/projects?per_page=100" \
     > projects.json

# 2. 提取仓库URL
jq -r '.[].http_url_to_repo' projects.json > repo_urls.txt

# 3. 批量克隆
bash clone.sh

# 4. 处理分支
bash branch.sh
```

---

## 📂 项目结构

```
LLM_auto_homework_check/
├── 📁 llm_gen/                 # 核心功能模块
│   ├── 🐍 llm_gen.py           # 主程序入口
│   ├── 🔧 extract.py           # 内容提取器
│   ├── 📁 fs_utils.py          # 文件系统工具
│   ├── 🤖 llm_utils.py         # LLM 接口封装
│   ├── 💬 prompt_utils.py      # 提示词管理
│   └── 📁 prompt_template/     # 评分模板库
├── 🔧 clone.sh                 # 仓库克隆脚本
├── 🌿 branch.sh                # 分支处理脚本
├── ⚡ main.sh                  # 一键执行脚本
├── 📋 requirements.txt         # Python 依赖
└── 📖 README.md               # 项目文档
```

---

## ⚙️ 配置说明

### API 配置

支持的 LLM 提供商：

- **DeepSeek**（推荐）
- **OpenAI GPT 系列**

在 `llm_gen/openai.key` 中配置相应的 API 密钥。

### 模板配置

评分模板存储在 `prompt_template/` 目录下，每个章节对应一个子目录。添加新章节时：

1. 在 `prompt_template/` 下创建新目录
2. 添加对应的评分标准模板文件
3. 系统将自动识别并处理

### 输出格式

系统默认生成 JSON 格式的结构化评分结果，包含：

- 各评分项详细分数
- 总分统计
- 评分依据说明

---

## 🛡️ 安全机制

### 提示词注入防护

系统内置多层防护机制，防止学生在报告中嵌入恶意提示词：

1. **边界隔离**：使用明确标记分割不同内容源
2. **身份锁定**：强化系统评分身份，忽略角色操控指令  
3. **格式约束**：强制 JSON 输出，避免非结构化干扰
4. **内容过滤**：预处理阶段移除潜在的注入代码

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！请遵循以下步骤：

1. **Fork** 项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 **Pull Request**

### 开发指南

- **添加新章节**：在 `prompt_template/` 下新建目录并配置模板
- **自定义评分逻辑**：修改 `llm_utils.py` 中的逻辑实现
- **扩展格式支持**：更新 `extract.py` 以支持新的报告格式

---

## ❓ 常见问题

<details>
<summary><strong>Q: 支持哪些报告格式？</strong></summary>

目前主要支持 Markdown 格式报告。可通过修改 `extract.py` 扩展支持 Jupyter Notebook、PDF 等格式。
</details>

<details>
<summary><strong>Q: 如何更换 LLM 模型？</strong></summary>

在 `llm_utils.py` 中修改模型配置即可。推荐使用 DeepSeek Reasoner 或 GPT-4 系列以获得最佳效果。
</details>

<details>
<summary><strong>Q: 批量处理失败怎么办？</strong></summary>

检查：1) API 密钥配置 2) 网络连接状态 3) 学生仓库权限 4) 磁盘空间充足性
</details>

---

## 🙏 致谢

感谢以下贡献者对项目的支持：

- [@kal1x](https://github.com/kal1x) - 核心开发与架构设计
- [@Lime-Cocoa](https://github.com/Lime-Cocoa) - 功能实现与测试优化

---


<div align="center">

**如果这个项目对您有帮助，请考虑给我们一个 ⭐**

[报告问题](../../issues) · [功能建议](../../issues) · [参与讨论](../../discussions)

</div>

