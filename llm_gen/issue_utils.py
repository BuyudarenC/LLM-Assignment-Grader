#!/usr/bin/env python3
import os
import requests
import re
from pathlib import Path
from loguru import logger
from urllib.parse import urlparse, quote_plus

class GitLabIssueCreator:
    """用于在GitLab仓库中创建issue的工具类"""
    
    def __init__(self, api_token=None, api_url="https://git.cuc.edu.cn/api/v4"):
        """
        初始化GitLab API连接
        
        Args:
            api_token: GitLab API令牌
            api_url: GitLab API URL
        """
        # 如果未提供token，尝试从环境变量获取
        self.api_token = api_token or os.environ.get('GITLAB_API_TOKEN')
        
        if not self.api_token:
            logger.warning("未设置GitLab API令牌，请通过GITLAB_API_TOKEN环境变量或参数提供")
            
        self.api_url = api_url
        self.headers = {
            'PRIVATE-TOKEN': self.api_token,
            'Content-Type': 'application/json'
        }
    
    def get_project_id(self, repo_url):
        """
        从仓库URL获取GitLab项目ID
        
        Args:
            repo_url: 仓库URL，例如 https://git.cuc.edu.cn/ccs/2025-penetration/username.git
            
        Returns:
            项目ID或None（如果无法获取）
        """
        try:
            # 从URL中提取项目路径
            parsed_url = urlparse(repo_url)
            
            # 移除.git后缀和开头的/
            path = parsed_url.path
            if path.endswith('.git'):
                path = path[:-4]
            if path.startswith('/'):
                path = path[1:]
            
            # 将路径编码为URL安全格式
            encoded_path = quote_plus(path)
            
            # 查询API获取项目信息
            response = requests.get(f"{self.api_url}/projects/{encoded_path}", headers=self.headers)
            
            if response.status_code == 200:
                return response.json()['id']
            else:
                logger.error(f"获取项目ID失败: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"解析仓库URL时出错: {e}")
            return None
    
    def create_issue(self, repo_url, title, description):
        """
        在指定仓库创建issue
        
        Args:
            repo_url: 仓库URL
            title: issue标题
            description: issue描述（支持Markdown格式）
            
        Returns:
            成功创建返回True，否则返回False
        """
        if not self.api_token:
            logger.error("缺少GitLab API令牌，无法创建issue")
            return False
        
        project_id = self.get_project_id(repo_url)
        if not project_id:
            return False
        
        try:
            # 创建issue API
            url = f"{self.api_url}/projects/{project_id}/issues"
            
            # 准备数据
            data = {
                'title': title,
                'description': description
            }
            
            # 发送请求
            response = requests.post(url, json=data, headers=self.headers)
            
            if response.status_code in [200, 201]:
                issue_url = response.json().get('web_url')
                issue_id = response.json().get('iid')
                logger.success(f"Issue创建成功: #{issue_id}, {issue_url}")
                return True
            else:
                logger.error(f"创建Issue失败: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"创建Issue时出错: {e}")
            return False

def get_repo_url_from_git_dir(git_dir):
    """
    从git目录获取远程仓库URL，支持常规仓库和git worktree
    
    Args:
        git_dir: Git目录路径
        
    Returns:
        远程仓库URL或None
    """
    try:
        git_path = Path(git_dir)
        git_config_path = None
        found_config = False
        
        # 尝试各种可能的配置文件位置
        possible_paths = [
            git_path / ".git" / "config",           # 常规仓库
            git_path / "config",                    # 裸仓库
        ]
        
        # 检查是否是git worktree引用文件
        git_file_path = git_path / ".git"
        if git_file_path.exists() and git_file_path.is_file():
            try:
                # 读取.git文件内容获取实际的git目录
                with open(git_file_path, 'r') as f:
                    gitdir_line = f.read().strip()
                
                # 提取gitdir路径
                if gitdir_line.startswith("gitdir: "):
                    gitdir_path = gitdir_line[len("gitdir: "):]
                    
                    # 处理相对路径
                    if not os.path.isabs(gitdir_path):
                        gitdir_path = os.path.normpath(os.path.join(str(git_path), gitdir_path))
                    
                    # 构造worktree的config文件路径
                    main_git_path = Path(gitdir_path)
                    
                    # 直接添加worktree配置文件路径
                    worktree_config = main_git_path / "config"
                    if worktree_config.exists():
                        possible_paths.append(worktree_config)
                    
                    # 添加主仓库的配置文件
                    if "worktrees" in str(main_git_path):
                        main_repo_path = str(main_git_path).split("worktrees")[0]
                        main_config = Path(main_repo_path) / "config"
                        if main_config.exists():
                            possible_paths.append(main_config)
                            logger.info(f"检测到git worktree，找到主仓库配置: {main_config}")
            except Exception as e:
                logger.warning(f"解析git worktree引用时出错: {e}")
        
        # 首先，尝试使用git命令获取URL（最可靠的方法）
        try:
            import subprocess
            result = subprocess.run(
                ["git", "-C", str(git_path), "config", "--get", "remote.origin.url"],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                repo_url = result.stdout.strip()
                if repo_url:
                    logger.info(f"通过git命令获取到远程URL: {repo_url}")
                    return repo_url
        except Exception as e:
            logger.debug(f"通过git命令获取远程URL失败: {e}")
        
        # 如果git命令失败，尝试从配置文件读取
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        config = f.read()
                    
                    # 查找远程仓库URL
                    match = re.search(r'url\s*=\s*(https?://[^\n]+)', config)
                    if match:
                        repo_url = match.group(1).strip()
                        logger.info(f"从配置文件 {path} 获取到远程URL: {repo_url}")
                        return repo_url
                    logger.debug(f"配置文件 {path} 中未找到远程URL")
                except Exception as e:
                    logger.warning(f"读取配置文件 {path} 时出错: {e}")
        
        # 如果还是找不到，遍历上级目录寻找.git目录
        parent_dir = git_path.parent
        if parent_dir != git_path:  # 避免无限循环
            logger.info(f"尝试在父目录 {parent_dir} 中查找git配置")
            parent_url = get_repo_url_from_git_dir(parent_dir)
            if parent_url:
                return parent_url
                
        logger.error(f"无法找到Git远程仓库URL: {git_dir}")
        return None
            
    except Exception as e:
        logger.error(f"获取远程仓库URL时出错: {e}")
        return None

def create_feedback_issue(git_dir, student_name, chapter_id, feedback_content):
    """
    在远程仓库中创建包含评语的issue
    
    Args:
        git_dir: Git目录路径
        student_name: 学生姓名
        chapter_id: 章节ID
        feedback_content: 评语内容
        
    Returns:
        成功创建返回True，否则返回False
    """
    # 获取远程仓库URL
    repo_url = get_repo_url_from_git_dir(git_dir)
    if not repo_url:
        return False
    
    # 创建issue标题
    title = f"【{chapter_id}】作业点评"
    
    # 添加学生信息到评语
    full_content = f"# {student_name} - {chapter_id} 作业点评\n\n{feedback_content}"
    
    # 创建issue
    issue_creator = GitLabIssueCreator()
    return issue_creator.create_issue(repo_url, title, full_content)

if __name__ == "__main__":
    # 命令行测试功能
    import argparse
    
    parser = argparse.ArgumentParser(description='创建包含评语的GitLab issue')
    parser.add_argument('-g', '--git-dir', type=str, required=True,
                        help='Git仓库目录')
    parser.add_argument('-s', '--student', type=str, required=True,
                        help='学生姓名')
    parser.add_argument('-c', '--chapter-id', type=str, required=True,
                        help='章节ID')
    parser.add_argument('-f', '--feedback-file', type=str, required=True,
                        help='评语文件路径')
    parser.add_argument('-t', '--token', type=str,
                        help='GitLab API令牌 (也可通过GITLAB_API_TOKEN环境变量提供)')
    
    args = parser.parse_args()
    
    # 读取评语文件
    try:
        with open(args.feedback_file, 'r', encoding='utf-8') as f:
            feedback_content = f.read()
            
        # 设置API令牌（如果提供）
        if args.token:
            os.environ['GITLAB_API_TOKEN'] = args.token
            
        # 创建issue
        success = create_feedback_issue(args.git_dir, args.student, args.chapter_id, feedback_content)
        if success:
            print(f"成功为学生 {args.student} 创建了 {args.chapter_id} 章节的评语issue")
        else:
            print("创建issue失败")
            
    except Exception as e:
        print(f"处理时出错: {e}") 