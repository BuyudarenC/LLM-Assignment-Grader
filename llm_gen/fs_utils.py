import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger

def get_directory_structure(directory_path: Path) -> str:
    """
    获取目录结构
    
    Args:
        directory_path: 要获取结构的目录路径
    
    Returns:
        目录结构字符串
    """
    try:
        # 运行tree命令获取目录结构
        result = subprocess.run(
            ["tree", str(directory_path)], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"获取目录结构失败: {e}")
        return "无法获取目录结构"
    except Exception as e:
        logger.error(f"获取目录结构时出现异常: {e}")
        return "无法获取目录结构"

def get_git_history(directory_path: Path) -> str:
    """
    获取Git提交历史
    
    Args:
        directory_path: Git仓库目录路径
    
    Returns:
        Git历史字符串
    """
    try:
        # 检查是否为git仓库
        is_git_repo = subprocess.run(
            ["git", "-C", str(directory_path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True
        )
        
        if is_git_repo.returncode != 0:
            return "该目录不是Git仓库"
        
        # 运行git log命令获取提交历史
        result = subprocess.run(
            ["git", "-C", str(directory_path), "log", "--oneline", "--graph"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Git仓库中没有提交记录"
    except Exception as e:
        logger.error(f"获取Git历史时出现异常: {e}")
        return "无法获取Git历史"

def find_directories_by_pattern(base_dir: Path, pattern: str) -> List[str]:
    """
    在基础目录中查找匹配模式的目录
    
    Args:
        base_dir: 基础目录路径
        pattern: 匹配模式（正则表达式）
    
    Returns:
        匹配的目录路径列表
    """
    pattern_re = re.compile(pattern, re.IGNORECASE)
    found_dirs = []
    
    for root, dirs, files in os.walk(base_dir):
        for dir_name in dirs:
            if pattern_re.search(dir_name):
                found_dirs.append(os.path.join(root, dir_name))
    
    return found_dirs 