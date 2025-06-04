#!/usr/bin/env python3
import json
import os
import glob
import sys
from pathlib import Path

def extract_feedback(json_file):
    """从评分JSON文件中提取评语并格式化输出"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取完成情况判断
        pros_items = {
            "推荐的分支结构": "推荐的分支结构",
            "见名知意的文件命名": "见名知意的文件命名",
            "实验报告结构规范内容完整": "实验报告结构规范内容完整",
            "有原创性身份标识": "作业中有适当的「身份标识」证明作业原创性",
            "配图与高亮标记": "有基本的配图与高亮标记，直接在配图中对高亮标记进行文字标注",
            "结果解释": "对实验结果给出了自己的解释",
            "问题与解决方案总结": "在实验报告末总结了遇到的问题与解决方案",
            "参考资料引用规范": "参考文献/资料引用标准规范"
        }

        # 构建输出内容
        output = "## Pros\n\n"
        
        # 完成情况判断部分
        completion_status = data.get("完成情况判断", {})
        for key, display_text in pros_items.items():
            checked = "[x]" if completion_status.get(key, False) else "[ ]"
            output += f"- {checked} {display_text} \n"
        
        # 建议改进部分
        output += "\n## Recommends\n"
        recommendations = data.get("建议改进", {}).get("suggestions", [])
        for rec in recommendations:
            output += f"- {rec}\n"
        
        return output
        
    except Exception as e:
        return f"处理文件 {json_file} 时出错: {e}"

def process_directory(base_dir, output_dir, chapter_id):
    """处理目录下的所有JSON文件"""
    base_path = Path(base_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 查找所有学生的JSON文件
    pattern = f"*/{chapter_id}.json"
    json_files = list(base_path.glob(pattern))
    
    processed = 0
    for json_file in json_files:
        # 提取学生姓名（目录名）
        student_name = json_file.parent.name
        
        # 创建学生输出目录
        student_output_dir = output_path / student_name
        student_output_dir.mkdir(exist_ok=True)
        
        # 处理JSON文件并保存输出
        feedback = extract_feedback(json_file)
        output_file = student_output_dir / f"{chapter_id}_feedback.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(feedback)
        
        print(f"已处理 {student_name} 的评语")
        processed += 1
    
    print(f"共处理了 {processed} 个学生的评语")
    return processed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='从JSON文件中提取评语并格式化输出')
    parser.add_argument('-i', '--input-dir', type=str, required=True,
                        help='输入目录，包含JSON文件的目录')
    parser.add_argument('-o', '--output-dir', type=str, default='feedback',
                        help='输出目录 (默认: feedback)')
    parser.add_argument('-c', '--chapter-id', type=str, default='0x01',
                        help='章节ID (默认: 0x01)')
    
    args = parser.parse_args()
    
    process_directory(args.input_dir, args.output_dir, args.chapter_id) 