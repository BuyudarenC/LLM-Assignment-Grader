import os
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional

def find_and_merge_markdown(output_path: str = "合并实验报告.md", 
                           search_dir: str = "./",
                           log_file: Optional[str] = None) -> str:
    """
    查找并合并作业报告markdown文件，优先级：
    1. 目录深度最深的文件（最高优先级）
    2. 同深度中的非README文件优先于README文件
    3. 同深度非README文件中优先选择特定命名的文件
    
    Args:
        output_path: 输出文件路径
        search_dir: 开始搜索的目录路径
        log_file: 日志文件路径，如果为None则只输出到控制台
        
    Returns:
        合并后的文件路径或空字符串（如果未找到文件）
    """
    # 设置日志（如果指定）
    if log_file:
        logger.add(log_file, rotation="10 MB")
    
    search_path = Path(search_dir)
    logger.info(f"开始在 {search_path} 中查找并合并markdown文件")
    
    # 找到所有MD文件（包括README）
    md_files = find_markdown_files(search_path)
    
    if not md_files:
        logger.warning("未找到任何markdown报告文件")
        return ""
        
    # 选择最佳报告
    selected_reports = select_best_reports(md_files)
    
    if not selected_reports:
        logger.warning("没有选择到任何报告文件")
        return ""
    
    # 合并内容
    merged_content = ""
    for report in selected_reports:
        section_title = f"### {report['dir_name']} - {report['file_name']}"
        merged_content += f"{section_title}\n\n{report['content']}\n\n"
    
    # 保存合并后的文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        
        logger.info(f"已成功创建合并报告: {output_path}, 共合并了 {len(selected_reports)} 个文件")
        return output_path
    except Exception as e:
        logger.error(f"保存合并报告时出错: {e}")
        return ""

def find_markdown_files(search_path: Path) -> List[Dict]:
    """找到目录下所有的Markdown文件，包括README文件"""
    reports = []
    
    # 递归查找所有.md和.markdown文件
    for extension in ['*.md', '*.markdown']:
        for md_path in search_path.rglob(extension):
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 计算相对路径和深度
                rel_path = md_path.relative_to(search_path)
                depth = len(rel_path.parts) - 1  # 减去文件名本身
                
                # 记录是否为README文件
                is_readme = md_path.name.lower() in ('readme.md', 'readme.markdown')
                
                reports.append({
                    'path': md_path,
                    'dir_name': md_path.parent.name,
                    'file_name': md_path.name,
                    'content': content,
                    'depth': depth,
                    'is_readme': is_readme
                })
                logger.info(f"找到文件: {md_path} (深度: {depth}, {'README' if is_readme else '普通文件'})")
            except Exception as e:
                logger.error(f"读取文件 {md_path} 时出错: {e}")
    
    return reports

def select_best_reports(reports: List[Dict]) -> List[Dict]:
    """
    选择最佳报告文件，优先级：
    1. 深度最大的文件
    2. 同深度下非README文件优于README
    """
    if not reports:
        return []
        
    # 按深度分组
    by_depth = {}
    for report in reports:
        depth = report['depth']
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(report)
    
    # 获取最大深度的文件
    max_depth = max(by_depth.keys()) if by_depth else 0
    candidates = by_depth.get(max_depth, [])
    
    logger.info(f"找到 {len(candidates)} 个最深层文件，深度为 {max_depth}")
    
    # 同深度下优先选择非README文件
    non_readme_files = [r for r in candidates if not r['is_readme']]
    
    # 如果有非README文件，就从中选择
    if non_readme_files:
        logger.info(f"在最深层中找到并选择 {len(non_readme_files)} 个非README文件")
        return non_readme_files
    
    # 如果最深层只有README文件，也返回它们
    logger.info("最深层只有README文件，选择它们")
    return candidates

if __name__ == "__main__":
    # 可以在这里配置参数
    output_file = "0x01.md"
    search_directory = "/home/OS-Fuzz/2025/cailin/hw0x01"
    log_file = "markdown_merger.log"  # 如果不需要日志文件，设为None
    
    find_and_merge_markdown(
        output_path=output_file,
        search_dir=search_directory,
        log_file=log_file
    )