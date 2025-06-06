import json
from pathlib import Path
from typing import Optional, Tuple
import argparse
import os
from loguru import logger
from extract import find_and_merge_markdown
from llm_utils import query_deepseek_v3, query_qwen3
from fs_utils import get_directory_structure, get_git_history, find_directories_by_pattern
from prompt_utils import generate_prompt_from_template, get_prompt_template_path, save_prompt_to_file, parse_llm_response
from feedback_utils import extract_feedback
from issue_utils import create_feedback_issue
from extract_scores import process_all_scores
from datetime import datetime

def extract_student_report(student_dir: Path, 
                          output_dir: Path, 
                          assignment_pattern: str) -> Tuple[bool, Optional[Path], Optional[Path]]:
    """
    第一步: 提取学生的markdown报告
    
    Args:
        student_dir: 学生目录路径
        output_dir: 输出目录路径
        assignment_pattern: 作业模式，用于匹配作业文件夹
    
    Returns:
        成功标志, 输出文件路径, 找到的作业目录路径
    """
    student_name = student_dir.name
    logger.info(f"处理学生: {student_name}")
    
    # 创建学生对应的输出目录
    student_output_dir = output_dir / student_name
    student_output_dir.mkdir(exist_ok=True)
    
    # 设置输出文件路径
    output_file = student_output_dir / f"{assignment_pattern}.md"
    
    # 在学生目录中查找匹配作业模式的文件夹
    found_assignments = find_directories_by_pattern(student_dir, assignment_pattern)
    
    if not found_assignments:
        logger.warning(f"学生 {student_name} 没有找到匹配 {assignment_pattern} 的作业文件夹")
        return False, None, None
    
    # 提取找到的第一个匹配文件夹中的报告
    try:
        assignment_dir = found_assignments[0]
        logger.info(f"在 {assignment_dir} 中查找作业报告")
        
        # 调用提取函数
        result_file = find_and_merge_markdown(
            output_path=str(output_file),
            search_dir=assignment_dir,
            log_file=None
        )
        
        if result_file:
            logger.success(f"成功提取学生 {student_name} 的报告到 {output_file}")
            return True, Path(result_file), Path(assignment_dir)
        else:
            logger.error(f"提取学生 {student_name} 的报告失败")
            return False, None, None
            
    except Exception as e:
        logger.error(f"处理学生 {student_name} 时出错: {e}")
        return False, None, None

def process_student(student_dir: Path, 
                   output_dir: Path,
                   assignment_id: str,
                   prompt_template_path: Path,
                   skip_md_extraction: bool = False,
                   create_issue: bool = False) -> bool:
    """
    处理单个学生的完整流程
    
    Args:
        student_dir: 学生目录路径
        output_dir: 输出目录路径
        assignment_id: 作业ID (如 "0x01")
        prompt_template_path: 提示词模板路径
        skip_md_extraction: 是否跳过MD提取步骤（如果已存在MD文件）
        create_issue: 是否创建issue
    
    Returns:
        处理是否成功
    """
    # 准备输出路径
    student_name = student_dir.name
    student_output_dir = output_dir / student_name
    student_output_dir.mkdir(exist_ok=True)
    md_file_path = student_output_dir / f"{assignment_id}.md"
    
    # 第一步: 提取学生报告（如果需要）
    if skip_md_extraction and md_file_path.exists():
        logger.info(f"学生 {student_name} 的MD文件已存在，跳过提取步骤")
        assignment_dir = None  # 我们可能没有作业目录
        
        # 查找可能的作业目录，用于后续步骤
        found_assignments = find_directories_by_pattern(student_dir, assignment_id)
        
        if found_assignments:
            assignment_dir = Path(found_assignments[0])
    else:
        # 需要提取MD
        success, extracted_md_path, found_dir = extract_student_report(
            student_dir, 
            output_dir, 
            assignment_id
        )
        
        if not success or extracted_md_path is None:
            return False
            
        md_file_path = extracted_md_path
        assignment_dir = found_dir
    
    try:
        # 读取报告内容
        with open(md_file_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 后续步骤的输出文件路径
        prompt_path = md_file_path.parent / f"{assignment_id}_prompt.txt"
        json_path = md_file_path.parent / f"{assignment_id}.json"
        feedback_path = md_file_path.parent / f"{assignment_id}_feedback.md"
        
        # 检查评语文件是否已存在
        feedback_exists = feedback_path.exists()
        json_exists = json_path.exists()
        
        # 第二步: 获取目录结构
        if assignment_dir:
            tree_structure = get_directory_structure(assignment_dir)
            
            # 第三步: 获取Git历史
            git_history = get_git_history(assignment_dir)
        else:
            # 如果没有找到作业目录，使用占位符
            tree_structure = "未能找到作业目录，无法获取目录结构"
            git_history = "未能找到作业目录，无法获取Git历史"
        
        # 如果JSON文件已存在但评语文件不存在，只生成评语文件
        if json_exists and not feedback_exists:
            try:
                logger.info(f"学生 {student_name} 的JSON文件已存在但评语文件不存在，生成评语文件")
                feedback = extract_feedback(json_path)
                with open(feedback_path, 'w', encoding='utf-8') as f:
                    f.write(feedback)
                logger.success(f"已生成评语文件: {feedback_path}")
                
                # 如果需要创建issue
                if create_issue and assignment_dir:
                    logger.info(f"正在为学生 {student_name} 创建评语issue...")
                    issue_created = create_feedback_issue(
                        git_dir=str(assignment_dir),
                        student_name=student_name,
                        chapter_id=assignment_id,
                        feedback_content=feedback
                    )
                    if issue_created:
                        logger.success(f"已成功创建评语issue")
                    else:
                        logger.warning(f"创建评语issue失败")
                return True
            except Exception as e:
                logger.error(f"生成评语文件时出错: {e}")
                return False
        
        # 如果JSON和评语文件都已存在，直接返回成功
        if json_exists and feedback_exists:
            logger.info(f"学生 {student_name} 的JSON和评语文件都已存在，跳过处理")
            return True
        
        # 第四步: 生成完整提示词
        prompt = generate_prompt_from_template(
            prompt_template_path,
            report_content,
            tree_structure,
            git_history
        )
        
        # 保存提示词到文件
        if not save_prompt_to_file(prompt, prompt_path):
            logger.warning(f"保存提示词到文件 {prompt_path} 失败")
        else:
            logger.info(f"已生成提示词文件: {prompt_path}")
        
        # 第五步: 调用大模型API
        response = query_deepseek_v3(prompt)
        
        if response:
            try:
                # 解析大模型响应
                response_obj = parse_llm_response(response)
                
                # 保存大模型输出到JSON文件
                with open(json_path, 'w', encoding='utf-8', newline='') as f:
                    json.dump(response_obj, f, ensure_ascii=False, indent=2)
                
                logger.success(f"已生成评分结果: {json_path}")
                
                # 生成评语文件
                try:
                    feedback = extract_feedback(json_path)
                    with open(feedback_path, 'w', encoding='utf-8') as f:
                        f.write(feedback)
                    logger.success(f"已生成评语文件: {feedback_path}")
                    
                    # 如果需要创建issue
                    if create_issue and assignment_dir:
                        logger.info(f"正在为学生 {student_name} 创建评语issue...")
                        issue_created = create_feedback_issue(
                            git_dir=str(assignment_dir),
                            student_name=student_name,
                            chapter_id=assignment_id,
                            feedback_content=feedback
                        )
                        if issue_created:
                            logger.success(f"已成功创建评语issue")
                        else:
                            logger.warning(f"创建评语issue失败")
                except Exception as e:
                    logger.error(f"生成评语文件时出错: {e}")
                
                return True
            except Exception as e:
                logger.error(f"保存JSON时出错: {e}")
                
                # 尝试直接保存原始响应为备份
                backup_path = md_file_path.parent / f"{assignment_id}_response.txt"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(str(response))
                logger.info(f"已保存原始响应到: {backup_path}")
                return False
        else:
            logger.error("调用大模型API失败")
            return False
            
    except Exception as e:
        logger.error(f"处理学生 {student_dir.name} 时出错: {e}")
        return False

def batch_process_students(base_dir: str = '/home/course/2025',
                          output_dir: str = 'output',
                          chapter_id: str = '0x01',
                          template_base_dir: str = './prompt_template',
                          skip_existing: bool = True,
                          force_reprocess: bool = False,
                          create_issue: bool = False,
                          generate_stats: bool = False,
                          name_mapping_file: Optional[str] = None):
    """
    批量处理所有学生
    
    Args:
        base_dir: 学生目录的基础路径
        output_dir: 输出目录
        chapter_id: 章节ID (如 "0x01", "0x02" 等)
        template_base_dir: 提示词模板基础目录
        skip_existing: 是否跳过已经处理过的学生
        force_reprocess: 强制重新处理所有步骤（即使文件已存在）
        create_issue: 是否在远程仓库创建issue
        generate_stats: 是否生成分数统计
        name_mapping_file: 包含学生拼音名到中文名映射的Excel文件路径
    
    Returns:
        成功处理的学生数量
    """
    # 设置日志
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{chapter_id}_{timestamp}.log"
    logger.add(log_file, rotation="10 MB")
    logger.info(f"开始批量处理 {chapter_id} 章节作业")
    
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 获取对应章节的提示词模板路径
    template_path = get_prompt_template_path(chapter_id, template_base_dir)
    
    # 确认模板文件存在
    if not template_path.exists():
        logger.error(f"提示词模板文件不存在: {template_path}")
        return 0
    
    logger.info(f"使用提示词模板: {template_path}")
    
    # 统计信息
    total_students = 0
    skipped_students = 0
    partial_processed = 0
    successful_processes = 0
    
    # 遍历基础目录下的所有文件夹（学生文件夹）
    for student_dir in Path(base_dir).iterdir():
        if not student_dir.is_dir():
            continue
        
        total_students += 1
        student_name = student_dir.name
        
        # 检查是否已经处理过该学生的该章节作业
        student_output_dir = output_path / student_name
        md_file_path = student_output_dir / f"{chapter_id}.md"
        json_file_path = student_output_dir / f"{chapter_id}.json"
        feedback_file_path = student_output_dir / f"{chapter_id}_feedback.md"
        
        # 如果强制重新处理，跳过所有检查
        if force_reprocess:
            if process_student(student_dir, output_path, chapter_id, template_path, False, create_issue):
                successful_processes += 1
            continue
            
        # 检查文件是否存在
        md_exists = md_file_path.exists()
        json_exists = json_file_path.exists()
        feedback_exists = feedback_file_path.exists()
        
        # 情况1: 所有文件都存在，完全跳过
        if skip_existing and md_exists and json_exists and feedback_exists:
            logger.info(f"跳过学生 {student_name}: 已完成全部处理 (MD、JSON和评语文件都存在)")
            skipped_students += 1
            continue
            
        # 情况2: 有MD和JSON但没有评语，只处理评语
        if md_exists and json_exists and not feedback_exists:
            logger.info(f"学生 {student_name}: 仅生成评语文件")
            try:
                feedback = extract_feedback(json_file_path)
                with open(feedback_file_path, 'w', encoding='utf-8') as f:
                    f.write(feedback)
                logger.success(f"已生成评语文件: {feedback_file_path}")
                
                # 如果需要创建issue
                if create_issue:
                    # 查找作业目录
                    found_assignments = find_directories_by_pattern(student_dir, chapter_id)
                    if found_assignments:
                        assignment_dir = found_assignments[0]
                        logger.info(f"正在为学生 {student_name} 创建评语issue...")
                        issue_created = create_feedback_issue(
                            git_dir=assignment_dir,
                            student_name=student_name,
                            chapter_id=chapter_id,
                            feedback_content=feedback
                        )
                        if issue_created:
                            logger.success(f"已成功创建评语issue")
                        else:
                            logger.warning(f"创建评语issue失败")
                
                successful_processes += 1
                continue
            except Exception as e:
                logger.error(f"生成评语文件时出错: {e}")
            
        # 情况3: 只有MD文件，跳过提取步骤，继续后续处理
        if md_exists and not json_exists:
            logger.info(f"学生 {student_name}: MD文件存在但没有JSON，继续后续步骤")
            if process_student(student_dir, output_path, chapter_id, template_path, True, create_issue):
                partial_processed += 1
                successful_processes += 1
            continue
            
        # 情况4: 从头开始处理
        if process_student(student_dir, output_path, chapter_id, template_path, False, create_issue):
            successful_processes += 1
    
    # 输出统计信息
    logger.info(f"批量处理完成, 共处理 {total_students} 名学生, 跳过 {skipped_students} 名, 部分处理 {partial_processed} 名, 全部成功 {successful_processes} 名")
    
    # 生成分数统计（如果需要）
    if generate_stats:
        logger.info("开始生成分数统计...")
        stats_csv = f"{chapter_id}_{timestamp}_scores.csv"
        scores, csv_path = process_all_scores(
            output_dir=output_dir,
            assignment_id=chapter_id,
            output_csv=stats_csv,
            log_file=log_file
        )
        if csv_path:
            logger.success(f"分数统计已保存到: {csv_path}")
        else:
            logger.warning("分数统计生成失败")
    
    return successful_processes

if __name__ == "__main__":
    # 使用argparse处理命令行参数
    parser = argparse.ArgumentParser(description='批量处理学生作业报告')
    parser.add_argument('-b', '--base-dir', type=str, default='/home/course/2025',
                        help='学生目录的基础路径 (默认: /home/course/2025)')
    parser.add_argument('-o', '--output-dir', type=str, default='output',
                        help='输出目录 (默认: output)')
    parser.add_argument('-c', '--chapter-id', type=str, default='0x01',
                        help='章节ID (默认: 0x01)')
    parser.add_argument('-t', '--template-dir', type=str, default='/home/course/2025/prompt_template',
                        help='提示词模板基础目录 (默认: /home/course/2025/prompt_template)')
    parser.add_argument('-s', '--skip-existing', action='store_true', default=True,
                        help='跳过已处理的学生 (默认: True)')
    parser.add_argument('--no-skip-existing', dest='skip_existing', action='store_false',
                        help='不跳过已处理的学生')
    parser.add_argument('-f', '--force-reprocess', action='store_true', default=False,
                        help='强制重新处理所有步骤 (默认: False)')
    parser.add_argument('-i', '--create-issue', action='store_true', default=False,
                        help='在远程仓库创建评语issue (默认: False)')
    parser.add_argument('--gitlab-token', type=str, 
                        help='GitLab API令牌 (也可通过GITLAB_API_TOKEN环境变量提供)')
    parser.add_argument('--stats', action='store_true', default=False,
                        help='生成分数统计 (默认: False)')
    
    args = parser.parse_args()
    
    # 设置GitLab API令牌（如果提供）
    if args.gitlab_token:
        os.environ['GITLAB_API_TOKEN'] = args.gitlab_token
    
    # 执行批量处理
    batch_process_students(
        base_dir=args.base_dir,
        output_dir=args.output_dir,
        chapter_id=args.chapter_id,
        template_base_dir=args.template_dir,
        skip_existing=args.skip_existing,
        force_reprocess=args.force_reprocess,
        create_issue=args.create_issue,
        generate_stats=args.stats,
        name_mapping_file=args.name_mapping
    ) 