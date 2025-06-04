#!/bin/bash

# 显示使用方法
usage() {
    echo "用法: $0 [-t TEMPLATE_DIR] [-b BASE_DIR] [-o OUTPUT_DIR]"
    echo "  -t TEMPLATE_DIR  提示词模板目录 (默认: ./llm_gen/prompt_template)"
    echo "  -b BASE_DIR      学生目录基础路径 (默认: home/llmgrader/2025-pentest)"
    echo "  -o OUTPUT_DIR    输出目录 (默认: /home/llmgrader/2025-pentest-score)"
    exit 1
}

# 设置默认值
TEMPLATE_DIR="./llm_gen/prompt_template"
BASE_DIR="/home/llmgrader/2025-pentest"
OUTPUT_DIR="/home/llmgrader/2025-pentest-score"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/llm_gen/llm_gen.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
  echo "错误: 找不到 Python 脚本 $PYTHON_SCRIPT"
  exit 1
fi

# 解析命令行参数
while getopts ":t:b:o:h" opt; do
  case $opt in
    t) TEMPLATE_DIR="$OPTARG" ;;
    b) BASE_DIR="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    h|*) usage ;;
  esac
done

# 检查模板目录是否存在
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "错误: 提示词模板目录不存在: $TEMPLATE_DIR"
    exit 1
fi

echo "开始批量处理所有章节作业..."
echo "使用参数:"
echo "  模板目录: $TEMPLATE_DIR"
echo "  基础目录: $BASE_DIR"
echo "  输出目录: $OUTPUT_DIR"
echo ""

# 递归查找所有提示词模板文件
find "$TEMPLATE_DIR" -name "*.txt" -type f | while read -r template_file; do
    # 获取文件名，不包括路径和扩展名
    filename=$(basename "$template_file")
    chapter_id="${filename%.*}"
    
    # 如果模板在子目录中，也可以使用子目录名作为章节ID
    if [ "$chapter_id" == "template" ]; then
        # 如果文件名是template.txt，使用父目录名作为chapter_id
        parent_dir=$(basename "$(dirname "$template_file")")
        chapter_id="$parent_dir"
    fi
    
    echo "========================================"
    echo "处理章节: $chapter_id"
    echo "使用模板: $template_file"
    
    # 调用Python脚本处理该章节
    (cd "$OUTPUT_DIR" && python3 "$PYTHON_SCRIPT" -c "$chapter_id" -b "$BASE_DIR" -o "$OUTPUT_DIR" -t "$TEMPLATE_DIR")
    
    echo "章节 $chapter_id 处理完成"
    echo "========================================"
    echo ""
done

echo "所有章节处理完成!" 