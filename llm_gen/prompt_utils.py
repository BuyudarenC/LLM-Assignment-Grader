import os
import re
import tiktoken
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

def estimate_token_count(text: str) -> int:
    """
    估算文本的token数量
    
    Args:
        text: 要估算的文本
        
    Returns:
        估算的token数量
    """
    # 尝试使用tiktoken库(如果可用)进行更准确的估算
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(encoding.encode(text))
    except (ImportError, Exception):
        # 如果tiktoken不可用，使用简单的启发式方法
        # 英文约4个字符一个token，中文每个字约1.5个token
        # 这只是粗略估计
        
        # 计算英文字符和中文字符数量
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        english_chars = total_chars - chinese_chars
        
        # 估算token数量
        english_tokens = english_chars / 4
        chinese_tokens = chinese_chars * 1.5
        
        return int(english_tokens + chinese_tokens)

def generate_prompt_from_template(template_path: Path, 
                                 report_content: str, 
                                 tree_structure: str, 
                                 git_history: str) -> str:
    """
    生成完整的提示词
    
    Args:
        template_path: 提示词模板文件路径
        report_content: 学生报告内容
        tree_structure: 目录结构
        git_history: Git历史
    
    Returns:
        完整的提示词字符串
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 使用明确的分隔符包装学生输入内容，不修改原始内容
        # 这样可以使LLM更清楚地区分指令和待评估内容
        wrapped_report = f"【学生报告开始】\n{report_content}\n【学生报告结束】"
        wrapped_tree = f"【目录结构开始】\n{tree_structure}\n【目录结构结束】"
        wrapped_git = f"【Git历史开始】\n{git_history}\n【Git历史结束】"
        
        # 修复原有拼写错误并替换模板中的占位符
        prompt = template.replace("HMOEWORK", wrapped_report)
        prompt = prompt.replace("TREE", wrapped_tree)
        prompt = prompt.replace("GITLOG", wrapped_git)
        
        # 估算token数量并记录日志
        report_tokens = estimate_token_count(wrapped_report)
        tree_tokens = estimate_token_count(wrapped_tree)
        git_tokens = estimate_token_count(wrapped_git)
        total_tokens = estimate_token_count(prompt)
        
        logger.info(f"提示词token估算: 报告={report_tokens}, 目录结构={tree_tokens}, Git历史={git_tokens}, 总计={total_tokens}")
        
        return prompt
    except Exception as e:
        logger.error(f"生成提示词时出错: {e}")
        return ""

def get_prompt_template_path(chapter_id: str, template_base_dir: str = '/home/OS-Fuzz/2025/zllm/prompt_template') -> Path:
    """
    根据章节ID生成对应的提示词模板路径
    
    Args:
        chapter_id: 章节ID (如 "0x01")
        template_base_dir: 提示词模板基础目录
        
    Returns:
        提示词模板路径
    """
    return Path(template_base_dir) / chapter_id / f"{chapter_id}.txt"

def save_prompt_to_file(prompt: str, output_path: Path) -> bool:
    """
    保存提示词到文件
    
    Args:
        prompt: 提示词内容
        output_path: 输出文件路径
    
    Returns:
        是否保存成功
    """
    try:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write(prompt)
        return True
    except Exception as e:
        logger.error(f"保存提示词到文件时出错: {e}")
        return False

def parse_llm_response(response: Any) -> Dict[str, Any]:
    """
    解析大模型响应为标准格式
    
    Args:
        response: 大模型响应（可能是字符串或对象）
    
    Returns:
        解析后的响应对象
    """
    if isinstance(response, str):
        try:
            import json
            # 尝试解析为JSON对象
            response_obj = json.loads(response)
            return response_obj
        except json.JSONDecodeError:
            # 如果无法解析，保留原始字符串
            logger.warning(f"无法解析响应为JSON对象，保留原始字符串")
            return {"raw_response": response}
    else:
        # 已经是Python对象
        return response 