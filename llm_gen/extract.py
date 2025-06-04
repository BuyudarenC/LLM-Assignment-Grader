import os
import glob
import re
from loguru import logger
from typing import List, Dict, Optional, Tuple

def find_and_merge_markdown(output_path: str = "合并实验报告.md", 
                           search_dir: str = "./",
                           log_file: Optional[str] = None) -> str:
    """
    查找并合并作业报告markdown文件
    
    Args:
        output_path: 输出文件路径
        search_dir: 开始搜索的目录路径
        log_file: 日志文件路径，如果为None则只输出到控制台
        
    Returns:
        合并后的文件路径
    """
    # 设置日志文件（如果指定）
    if log_file:
        logger.add(log_file, rotation="10 MB")
    
    logger.info(f"开始在 {search_dir} 中查找并合并markdown文件")
    
    # 查找所有可能的作业报告
    all_reports = []
    
    # 作业目录的常见模式
    hw_dir_patterns = [
        r'hw0x\d+',       # hw0x01, hw0x02, ...
        r'chap0x\d+',     # chap0x01, chap0x02, ...
        r'0x\d+',         # 0x01, 0x02, ...
        r'实验\d+',        # 实验1, 实验2, ...
        r'实验[一二三四五六七八九十]',  # 实验一, 实验二, ...
        r'作业\d+',        # 作业1, 作业2, ...
        r'chapter\d+',    # chapter1, chapter2, ...
        r'homework\d+',   # homework1, homework2, ...
        r'lab\d+',        # lab1, lab2, ...
        r'assignment\d+', # assignment1, assignment2, ...
        r'作业',          # 作业
        r'实验报告',       # 实验报告
    ]
    
    # 编译正则表达式
    hw_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in hw_dir_patterns]
    
    # 跟踪是否在作业目录中
    in_hw_dir = {}  # 映射：目录路径 -> 作业根目录名
    
    # 从指定目录开始递归搜索
    for root, dirs, files in os.walk(search_dir):
        # 检查当前目录名是否匹配任何作业目录模式
        dirname = os.path.basename(root)
        parent_dir = os.path.dirname(root)
        
        is_hw_dir = False
        hw_root_name = None
        
        # 检查当前目录是否匹配模式
        for pattern in hw_patterns:
            if pattern.search(dirname):
                is_hw_dir = True
                hw_root_name = dirname
                break
        
        # 如果当前目录不匹配，检查父目录是否在跟踪的作业目录中
        if not is_hw_dir and parent_dir in in_hw_dir:
            is_hw_dir = True
            hw_root_name = in_hw_dir[parent_dir]  # 继承父目录的作业根目录名
        
        # 如果是作业目录或其子目录，更新跟踪状态
        if is_hw_dir:
            in_hw_dir[root] = hw_root_name
            
            # 查找该目录下的所有markdown文件
            md_files = [f for f in files if f.endswith('.md') or f.endswith('.markdown')]
            
            if md_files:
                # 优先选择非README.md的文件
                non_readme = [f for f in md_files if f.lower() != 'readme.md' and f.lower() != 'readme.markdown']
                target_files = non_readme if non_readme else md_files
                
                for md_file in target_files:
                    file_path = os.path.join(root, md_file)
                    dir_name = os.path.basename(root)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 获取相对于搜索目录的路径
                        rel_path = os.path.relpath(root, search_dir)
                        # 拆分路径来识别目录层次结构
                        path_parts = rel_path.split(os.sep)
                        
                        all_reports.append({
                            'path': file_path,
                            'dir_name': dir_name,
                            'file_name': md_file,
                            'content': content,
                            'depth': len(path_parts),  # 目录深度
                            'path_parts': path_parts,  # 路径部分，用于分组
                            'rel_path': rel_path,  # 相对路径
                            'hw_root_name': hw_root_name  # 作业根目录名
                        })
                        logger.info(f"找到文件: {file_path}")
                    except Exception as e:
                        logger.error(f"读取文件 {file_path} 时出错: {e}")
    
    # 按目录深度排序，深度更大的可能是更具体的报告
    all_reports.sort(key=lambda x: x['depth'], reverse=True)
    
    # 如果找到了报告，进行智能分组和合并
    if all_reports:
        # 按作业主题分组报告
        grouped_reports = group_reports_by_topic(all_reports, hw_patterns)
        logger.info(f"按主题分组后共有 {len(grouped_reports)} 个主题组")
        
        # 合并所有选定的报告
        merged_content = ""
        
        # 跟踪已处理的报告总数
        total_reports = 0
        
        # 处理每组报告
        for group_name, reports in grouped_reports.items():
            logger.info(f"处理主题组: {group_name}, 包含 {len(reports)} 个文件")
            
            # 从每组中选出最合适的报告
            selected_reports = select_best_reports_from_group(reports)
            total_reports += len(selected_reports)
            
            # 添加组标题（如果有多个组）
            if len(grouped_reports) > 1:
                merged_content += f"## {group_name}\n\n"
            
            # 合并组内选定的报告
            for report in selected_reports:
                # 如果组名已经包含在标题中，则不重复
                if group_name in report['dir_name']:
                    section_title = f"### {report['dir_name']} - {report['file_name']}"
                else:
                    section_title = f"### {group_name} - {report['dir_name']} - {report['file_name']}"
                
                merged_content += f"{section_title}\n\n"
                merged_content += report['content'] + "\n\n"
        
        # 保存合并后的文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            logger.info(f"已成功创建合并报告: {output_path}")
            logger.info(f"共合并了 {total_reports} 个文件")
            
            return output_path
        except Exception as e:
            logger.error(f"保存合并报告时出错: {e}")
            return ""
    else:
        logger.warning("未找到任何markdown报告文件")
        return ""

def is_hw_dir_name(dirname: str, patterns) -> bool:
    """判断目录名是否是作业相关的目录"""
    for pattern in patterns:
        if pattern.search(dirname):
            return True
    return False

def group_reports_by_topic(reports: List[Dict], hw_patterns) -> Dict[str, List[Dict]]:
    """
    将报告按主题分组
    
    Args:
        reports: 报告列表
        hw_patterns: 作业目录匹配的正则表达式列表
        
    Returns:
        按主题分组的报告字典
    """
    # 初始化分组
    groups = {}
    
    for report in reports:
        # 如果报告有关联的作业根目录名，直接使用
        if 'hw_root_name' in report and report['hw_root_name']:
            topic_name = report['hw_root_name']
        else:
            # 尝试找出主题名称
            path_parts = report['path_parts']
            
            # 寻找关键目录名作为主题
            topic_name = None
            for part in path_parts:
                if is_hw_dir_name(part, hw_patterns):
                    topic_name = part
                    break
            
            # 如果没找到明确的主题，使用第一级目录名
            if not topic_name and len(path_parts) > 0:
                topic_name = path_parts[0]
            
            # 如果路径为空，使用目录名
            if not topic_name:
                topic_name = report['dir_name']
        
        # 将报告添加到对应的组
        if topic_name not in groups:
            groups[topic_name] = []
        
        groups[topic_name].append(report)
    
    return groups

def select_best_reports_from_group(reports: List[Dict]) -> List[Dict]:
    """
    从一组报告中选择最佳的报告
    
    策略:
    1. 如果组内有不同层级的报告，只选择最深层级的报告
    2. 优先选择非README.md的文件
    3. 优先选择名为"报告.md"或"实验报告.md"的文件
    
    Args:
        reports: 同一主题的报告列表
        
    Returns:
        筛选后的报告列表
    """
    if not reports:
        return []
    
    # 将报告按子目录（如"实验一"）进行分组
    subdir_groups = {}
    for report in reports:
        dir_name = report['dir_name']
        # 检查是否是类似"实验一"的目录
        if re.search(r'实验[一二三四五六七八九十]|\d+', dir_name):
            if dir_name not in subdir_groups:
                subdir_groups[dir_name] = []
            subdir_groups[dir_name].append(report)
        else:
            # 不是实验子目录的报告，添加到一个特殊组
            if '_other' not in subdir_groups:
                subdir_groups['_other'] = []
            subdir_groups['_other'].append(report)
    
    # 如果有子目录分组，分别处理每个子目录
    if subdir_groups and any(key != '_other' for key in subdir_groups):
        final_reports = []
        
        # 按目录名排序，确保实验顺序一致
        sorted_subdirs = sorted([k for k in subdir_groups.keys() if k != '_other'])
        
        # 处理每个子目录中的报告
        for subdir in sorted_subdirs:
            subdir_reports = subdir_groups[subdir]
            # 在子目录中应用深度和文件名筛选
            selected = _select_by_depth_and_name(subdir_reports)
            final_reports.extend(selected)
            
        # 如果没有找到任何报告，且有其他报告，则使用其他报告
        if not final_reports and '_other' in subdir_groups:
            final_reports = _select_by_depth_and_name(subdir_groups['_other'])
            
        return final_reports
    else:
        # 没有子目录分组，使用常规筛选
        return _select_by_depth_and_name(reports)

def _select_by_depth_and_name(reports: List[Dict]) -> List[Dict]:
    """根据深度和文件名选择最佳报告"""
    if not reports:
        return []
        
    # 按深度分组
    depth_groups = {}
    for report in reports:
        depth = report['depth']
        if depth not in depth_groups:
            depth_groups[depth] = []
        depth_groups[depth].append(report)
    
    # 获取最大深度
    max_depth = max(depth_groups.keys())
    
    # 只使用最深层级的报告
    candidates = depth_groups[max_depth]
    
    # 优先选择非README.md的文件
    non_readme = [r for r in candidates if r['file_name'].lower() != 'readme.md']
    if non_readme:
        candidates = non_readme
    
    # 优先选择特定命名的文件
    specific_files = [r for r in candidates if r['file_name'] in ['报告.md', '实验报告.md']]
    if specific_files:
        candidates = specific_files
    
    return candidates

if __name__ == "__main__":
    # 可以在这里配置参数
    output_file = "0x01.md"
    search_directory = "/home/OS-Fuzz/2025/linminjie/hw0x01"  # 默认为当前目录
    log_file = "markdown_merger.log"  # 如果不需要日志文件，设为None
    
    # 运行合并函数
    find_and_merge_markdown(
        output_path=output_file,
        search_dir=search_directory,
        log_file=log_file
    )