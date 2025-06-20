# 多模型作业批改器 - 完整使用指南

支持多种AI模型进行自动化作业批改的智能系统，包括DeepSeek、OpenAI兼容格式和您自己部署的模型。

## 🚀 快速开始

### 方式一：使用默认模型（DeepSeek）
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行批改（使用默认的DeepSeek模型）
python run_simple.py
```

### 方式二：选择不同模型
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 交互式选择模型
python run_multimodel.py
```

### 方式三：配置您的本地模型
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置本地模型
python setup_local_model.py

# 3. 使用多模型运行器
python run_multimodel.py
```

## 📁 文件结构说明

```
homework_check/
├── config.py                # 多模型API配置文件
├── deepseek_grader.py       # 核心批改器类（支持多模型）
├── run_simple.py            # 简单运行脚本（默认模型）
├── run_multimodel.py        # 多模型选择运行脚本
├── setup_local_model.py     # 本地模型配置助手
├── test_retry.py            # 重试机制测试脚本
├── prompt.txt               # 批改提示词模板
├── requirements.txt         # Python依赖包
└── README.md                # 使用说明（本文件）
```

## 🎯 批改系统功能

- ✅ **多模型支持**：支持DeepSeek、OpenAI、本地部署模型等
- ✅ **自动读取**：批量读取学生的 `homework3.md` 文件
- ✅ **智能分析**：获取目录结构和Git提交历史
- ✅ **AI评分**：使用选择的AI模型进行智能评分
- ✅ **结构化输出**：生成JSON格式的详细评分结果
- ✅ **实时保存**：防止中途中断数据丢失
- ✅ **智能重试**：每个学生最多重试3次，提高成功率
- ✅ **统计摘要**：自动生成批改统计报告（包含重试统计）
- ✅ **配置助手**：轻松配置本地部署的模型

## 📊 评分体系（总分100分）

| 评分维度 | 分值 | 评分要点 |
|---------|------|----------|
| 结构完整性 | 15分 | 作业结构是否完整、层次清晰 |
| 思考题回答 | 20分 | 思考题回答质量和深度 |
| 命令执行与说明 | 15分 | 命令使用是否正确、说明是否清楚 |
| 实验过程复现性 | 15分 | 实验步骤是否可复现 |
| 信息提取全面 | 10分 | 关键信息提取是否完整 |
| 格式规范与可读性 | 10分 | 文档格式和可读性 |
| 图片管理规范性 | 10分 | 图片使用和管理规范 |
| Git提交流程合理 | 5分 | Git使用规范性 |

## 🔧 详细使用说明

### 1. 环境准备
确保您的环境满足以下要求：
- Python 3.7+
- 网络连接正常
- 作业目录 `../homework3` 存在

### 2. 运行前检查
```bash
# 检查作业目录
ls ../homework3

# 检查提示词文件
cat prompt.txt

# 检查配置文件
python -c "from config import DEEPSEEK_CONFIG; print('配置正常')"
```

### 3. 执行批改
```bash
# 启动批改程序
python run_simple.py
```

### 4. 查看结果
```bash
# 查看批改结果
cat deepseek_grading_results.jsonl

# 查看统计摘要
cat deepseek_grading_results_summary.txt
```

## 📄 输出文件详解

### deepseek_grading_results.jsonl
每行一个JSON对象，包含：
```json
{
  "student_name": "学生姓名",
  "grading_time": "2024-01-01T12:00:00",
  "grading_result": {
    "结构完整性": {"分数": 13, "理由": "..."},
    "思考题回答": {"分数": 18, "理由": "..."},
    "总分": 85
  },
  "raw_response": "DeepSeek原始响应",
  "model": "deepseek-reasoner"
}
```

### deepseek_grading_results_summary.txt
统计摘要包含：
- 总批改数量
- 平均分、最高分、最低分
- 分数分布统计

## 🎮 高级用法

### 批改单个学生
```python
from config import MODEL_CONFIGS
from deepseek_grader import MultiModelGrader

# 选择要使用的模型
config = MODEL_CONFIGS["deepseek"]  # 或 "local_openai", "openai" 等
grader = MultiModelGrader(config, config['name'])
grader.load_prompt("prompt.txt")

# 批改单个学生
result = grader.grade_single_homework(
    "张三", 
    "../homework3/张三/homework3.md",
    "../homework3/张三"
)
print(result)
```

### 配置本地模型
如果您有自己部署的OpenAI兼容模型：

```bash
# 运行配置助手
python setup_local_model.py
```

配置助手会引导您：
1. 输入API地址（如：http://localhost:8000/v1/chat/completions）
2. 输入模型名称（如：qwen2.5-7b-instruct）
3. 输入API Key（可选，本地部署通常不需要）
4. 测试连接
5. 自动保存配置

### 自定义配置
您可以修改 `config.py` 中的设置：

```python
# 修改默认模型
DEFAULT_MODEL = "user_local"  # 改为您想要的默认模型

# 修改作业目录
HOMEWORK_DIR = "/path/to/your/homework"

# 修改输出文件名
OUTPUT_FILE = "my_grading_results.jsonl"

# 修改请求间隔（避免API限制）
REQUEST_DELAY = 2  # 秒

# 添加新的模型配置
MODEL_CONFIGS["my_model"] = {
    "name": "我的模型",
    "url": "http://my-api.com/v1/chat/completions",
    "key": "my-api-key",
    "model": "my-model-name",
    "headers": {
        "Authorization": "Bearer {key}",
        "Content-Type": "application/json"
    }
}
```

## ⚠️ 注意事项

1. **API限制**：DeepSeek API有调用频率限制，脚本已设置1秒间隔
2. **网络稳定**：确保网络连接稳定，脚本有智能重试机制
3. **文件权限**：确保对作业目录有读取权限
4. **备份数据**：批改结果会实时保存，避免数据丢失
5. **重试机制**：每个学生最多重试3次，递增延迟（2秒→4秒→6秒）

## 🔍 错误排查

### 常见问题及解决方案

**1. 导入错误**
```bash
# 错误：ModuleNotFoundError
pip install requests
```

**2. API调用失败**
```bash
# 检查网络连接
ping api.deepseek.com

# 检查API密钥是否正确
# 登录DeepSeek控制台验证密钥
```

**3. 文件读取失败**
```bash
# 检查作业目录是否存在
ls -la ../homework3

# 检查文件权限
ls -la ../homework3/*/homework3.md
```

**4. JSON解析失败**
- 检查DeepSeek返回的响应格式
- 查看程序日志中的详细错误信息
- 可能需要调整提示词模板

## 📞 获取帮助

如果遇到问题：
1. 查看程序运行日志
2. 检查上述错误排查步骤
3. 确认API密钥和网络连接
4. 验证作业文件格式和路径

## 🎉 开始批改

现在您可以运行以下命令开始批改：

```bash
python run_simple.py
```

系统将自动：
1. 扫描 `../homework3` 目录下的所有学生文件夹
2. 读取每个学生的 `homework3.md` 文件
3. 调用DeepSeek Reasoner模型进行智能评分
4. 保存详细结果到 `deepseek_grading_results.jsonl`
5. 生成统计摘要到 `deepseek_grading_results_summary.txt`

祝您批改顺利！🎊 