#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple, Union

def extract_scores(output_dir: str, assignment_id: str = "0x01") -> Dict[str, int]:
    """
    从每个学生目录下提取指定作业的总分
    
    Args:
        output_dir: 包含学生评分目录的路径
        assignment_id: 作业ID，如"0x01"
        
    Returns:
        学生名字到总分的映射字典
    """
    results = {}
    output_path = Path(output_dir)
    
    # 遍历output目录下的所有子目录（每个子目录是一个学生）
    for student_dir in output_path.iterdir():
        if not student_dir.is_dir():
            continue
            
        student_name = student_dir.name
        json_file = student_dir / f"{assignment_id}.json"
        
        if not json_file.exists():
            logger.warning(f"未找到学生 {student_name} 的 {assignment_id}.json 文件")
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 从JSON中提取总分
            if "评分结果" in data and "总分" in data["评分结果"]:
                score = data["评分结果"]["总分"]
                results[student_name] = score
            else:
                logger.warning(f"警告: {student_name} 的JSON文件格式不包含总分字段")
                
        except Exception as e:
            logger.error(f"处理 {student_name} 的JSON文件时出错: {e}")
    
    return results

def save_scores_to_csv(scores: Dict[str, int], output_file: str, assignment_id: str = "0x01") -> str:
    """
    将分数保存为CSV文件
    
    Args:
        scores: 学生名字到总分的映射字典
        output_file: 输出CSV文件路径
        assignment_id: 作业ID，如"0x01"
        
    Returns:
        保存的CSV文件路径
    """
    # 转换为DataFrame
    df = pd.DataFrame(list(scores.items()), columns=['学生姓名', f'{assignment_id}总分'])
    
    # 按分数降序排序
    df = df.sort_values(by=f'{assignment_id}总分', ascending=False)
    
    # 保存为CSV
    df.to_csv(output_file, index=False, encoding='utf-8-sig')  # 使用utf-8-sig兼容Excel打开
    
    logger.info(f"已将{len(scores)}名学生的成绩保存至 {output_file}")
    return output_file

def process_all_scores(
    output_dir: str = "./output", 
    assignment_id: str = "0x01", 
    output_csv: Optional[str] = None, 
    save_to_csv: bool = True,
    log_file: Optional[str] = None
) -> Tuple[Dict[str, int], Optional[str]]:
    """
    封装的工具函数，用于提取并可选地保存所有学生的分数
    
    Args:
        output_dir: 学生评分目录路径
        assignment_id: 作业ID
        output_csv: CSV输出路径，如果为None则使用默认值
        save_to_csv: 是否将结果保存为CSV
        log_file: 日志文件路径
        
    Returns:
        包含两个元素的元组: (分数字典, CSV文件路径或None)
    """
    # 设置日志文件（如果提供）
    if log_file:
        logger.add(log_file, rotation="10 MB")
        
    logger.info(f"开始处理 {assignment_id} 作业的学生分数")
    
    # 提取分数
    scores = extract_scores(output_dir, assignment_id)
    
    if not scores:
        logger.warning("未找到任何学生分数")
        return {}, None
        
    # 显示分数摘要
    logger.info(f"找到 {len(scores)} 名学生的分数:")
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for student, score in sorted_scores[:5]:
        logger.info(f"{student}: {score}")
        
    if len(scores) > 5:
        logger.info("...")
    
    # 保存为CSV（如果需要）
    csv_path = None
    if save_to_csv:
        # 设置默认输出文件名
        if output_csv is None:
            output_csv = f"{assignment_id}_scores.csv"
        csv_path = save_scores_to_csv(scores, output_csv, assignment_id)
        
    return scores, csv_path

def get_scores_dataframe(scores: Dict[str, int], assignment_id: str = "0x01") -> pd.DataFrame:
    """
    将分数字典转换为DataFrame对象，方便进一步处理
    
    Args:
        scores: 学生名字到总分的映射字典
        assignment_id: 作业ID，如"0x01"
        
    Returns:
        包含学生姓名和分数的DataFrame
    """
    df = pd.DataFrame(list(scores.items()), columns=['学生姓名', f'{assignment_id}总分'])
    return df.sort_values(by=f'{assignment_id}总分', ascending=False)

def main():
    parser = argparse.ArgumentParser(description='提取学生JSON评分文件中的总分')
    parser.add_argument('--output_dir', default='./output', help='学生评分目录的路径')
    parser.add_argument('--assignment_id', default='0x01', help='作业ID，如"0x01"')
    parser.add_argument('--output_csv', default=None, help='输出CSV文件路径，默认为"[assignment_id]_scores.csv"')
    parser.add_argument('--no_save', action='store_true', help='设置此标志以不保存CSV文件')
    parser.add_argument('--log_file', default=None, help='日志文件路径')
    
    args = parser.parse_args()
    
    # 使用封装函数
    process_all_scores(
        output_dir=args.output_dir, 
        assignment_id=args.assignment_id, 
        output_csv=args.output_csv,
        save_to_csv=not args.no_save,
        log_file=args.log_file
    )

if __name__ == "__main__":
    main() 