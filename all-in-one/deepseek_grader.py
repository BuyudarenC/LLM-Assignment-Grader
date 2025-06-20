#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型作业批改器
支持DeepSeek、OpenAI兼容格式和其他模型进行作业批改
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiModelGrader:
    def __init__(self, api_config, model_name="unknown"):
        """
        初始化多模型批改器
        
        Args:
            api_config: API配置字典
            model_name: 模型名称（用于显示）
        """
        self.api_config = api_config
        self.model_name = model_name
        self.prompt_template = ""
        
    def load_prompt(self, prompt_file="prompt.txt"):
        """加载提示词模板"""
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
            logger.info(f"已加载提示词模板: {prompt_file}")
        except FileNotFoundError:
            logger.error(f"提示词文件不存在: {prompt_file}")
            raise
        except Exception as e:
            logger.error(f"加载提示词失败: {e}")
            raise
    
    def read_homework_content(self, homework_path):
        """读取学生作业内容"""
        try:
            with open(homework_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"读取作业文件失败 {homework_path}: {e}")
            return None
    
    def get_directory_tree(self, student_dir):
        """获取学生目录结构"""
        try:
            import subprocess
            result = subprocess.run(
                ['tree', student_dir, '/F'], 
                capture_output=True, 
                text=True, 
                encoding='utf-8'
            )
            return result.stdout if result.returncode == 0 else "目录结构获取失败"
        except Exception:
            # 如果tree命令不可用，使用Python实现简单的目录结构
            return self._simple_tree(student_dir)
    
    def _simple_tree(self, directory, prefix="", max_depth=3, current_depth=0):
        """简单的目录树实现"""
        if current_depth >= max_depth:
            return ""
        
        tree_str = ""
        try:
            items = sorted(Path(directory).iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree_str += f"{prefix}{current_prefix}{item.name}\n"
                
                if item.is_dir() and current_depth < max_depth - 1:
                    extension = "    " if is_last else "│   "
                    tree_str += self._simple_tree(
                        item, prefix + extension, max_depth, current_depth + 1
                    )
        except PermissionError:
            tree_str += f"{prefix}[权限不足]\n"
        
        return tree_str
    
    def get_git_log(self, student_dir):
        """获取Git提交日志"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'], 
                cwd=student_dir,
                capture_output=True, 
                text=True, 
                encoding='utf-8'
            )
            return result.stdout if result.returncode == 0 else "无Git历史记录"
        except Exception:
            return "无法获取Git历史记录"
    
    def build_grading_prompt(self, homework_content, tree_output, git_log):
        """构建批改提示词"""
        prompt = self.prompt_template.replace("HOMEWORK", homework_content)
        return prompt
    
    def call_llm_api(self, prompt):
        """调用LLM API（支持OpenAI兼容格式）"""
        try:
            # 构建请求数据
            data = {
                "model": self.api_config["model"],
                "messages": [
                    {"role": "system", "content": "你是一位专业的作业批改助教。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 2000
            }
            
            # 构建请求头
            headers = {}
            for key, value in self.api_config["headers"].items():
                if "{key}" in value and self.api_config["key"]:
                    headers[key] = value.format(key=self.api_config["key"])
                elif "{key}" not in value:
                    headers[key] = value
                # 如果key为空且需要key，则跳过这个header
            
            # 如果没有key或key为空，移除Authorization header（适用于本地部署）
            if not self.api_config["key"] or self.api_config["key"] in ["", "sk-local-key-or-empty"]:
                headers.pop("Authorization", None)
            
            logger.debug(f"调用 {self.model_name} API: {self.api_config['url']}")
            
            # 发送请求
            response = requests.post(
                self.api_config["url"],
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"{self.model_name} API响应格式异常: {result}")
                    return None
            else:
                logger.error(f"{self.model_name} API调用失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"{self.model_name} API调用异常: {e}")
            return None
    
    def parse_grading_result(self, llm_response):
        """解析LLM返回的批改结果"""
        try:
            # 方法1: 直接查找JSON部分
            start_idx = llm_response.find("{")
            end_idx = llm_response.rfind("}") + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = llm_response[start_idx:end_idx]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass  # 继续尝试其他方法
            
            # 方法2: 查找markdown代码块中的JSON
            import re
            
            # 查找 ```json 或 ``` 代码块
            json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
            matches = re.findall(json_pattern, llm_response, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    # 尝试解析找到的内容
                    json_data = json.loads(match.strip())
                    return json_data
                except json.JSONDecodeError:
                    continue
            
            # 方法3: 尝试从整个响应中提取结构化数据
            # 如果响应包含markdown格式，尝试从中提取关键信息
            lines = llm_response.split('\n')
            extracted_data = {}
            
            for line in lines:
                line = line.strip()
                # 寻找类似 "结构完整性": {"score": 13, "reason": "..."} 的模式
                if '"结构完整性"' in line or '"作业内容回答"' in line or '"命令执行与说明"' in line or '"实验过程复现性"' in line or '"格式规范与可读性"' in line or '"总分"' in line:
                    try:
                        # 尝试从行中提取JSON片段
                        start = line.find('{')
                        if start != -1:
                            json_part = '{' + line[start+1:]
                            if json_part.endswith(','):
                                json_part = json_part[:-1]
                            test_data = json.loads(json_part)
                            # 如果解析成功，将其合并到结果中
                            extracted_data.update(test_data)
                    except:
                        continue
            
            if extracted_data:
                return extracted_data
            
            logger.error(f"无法从{self.model_name}响应中提取JSON格式的评分结果")
            logger.error(f"原始响应: {llm_response[:500]}...")
            return None
                
        except Exception as e:
            logger.error(f"解析批改结果时发生异常: {e}")
            logger.error(f"原始响应: {llm_response[:200]}...")
            return None
    
    def grade_single_homework(self, student_name, homework_path, student_dir, max_retries=3):
        """批改单个学生的作业（带重试机制）"""
        logger.info(f"🔍 开始批改学生: {student_name}")
        
        # 读取作业内容
        homework_content = self.read_homework_content(homework_path)
        if homework_content is None:
            logger.error(f"❌ 学生 {student_name} 作业文件读取失败，跳过批改")
            return None
        
        # 获取目录结构和Git日志（这些不需要重试）
        tree_output = self.get_directory_tree(student_dir)
        git_log = self.get_git_log(student_dir)
        
        # 构建提示词
        prompt = self.build_grading_prompt(homework_content, tree_output, git_log)
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                logger.info(f"📝 尝试批改学生 {student_name} (第 {attempt + 1}/{max_retries} 次)")
                
                # 调用LLM API
                llm_response = self.call_llm_api(prompt)
                if llm_response is None:
                    raise Exception(f"{self.model_name} API调用失败")
                
                # 解析结果
                grading_result = self.parse_grading_result(llm_response)
                if grading_result is None:
                    raise Exception("批改结果解析失败")
                
                # 添加元数据
                result = {
                    "student_name": student_name,
                    "grading_time": datetime.now().isoformat(),
                    "grading_result": grading_result,
                    "raw_response": llm_response,
                    "model": self.api_config["model"],
                    "retry_count": attempt  # 记录重试次数
                }
                
                total_score = grading_result.get('总分', 'N/A')
                if attempt > 0:
                    logger.info(f"✅ 学生 {student_name} 批改成功（重试 {attempt} 次后），总分: {total_score}")
                else:
                    logger.info(f"✅ 学生 {student_name} 批改完成，总分: {total_score}")
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_delay = 2 * (attempt + 1)  # 递增延迟：2秒、4秒、6秒
                    logger.warning(f"⚠️  学生 {student_name} 第 {attempt + 1} 次批改失败: {e}")
                    logger.info(f"🔄 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"❌ 学生 {student_name} 的作业批改彻底失败（已重试 {max_retries} 次）: {e}")
                    return None
        
        return None
    
    def grade_all_homeworks(self, homework_dir="../homework3", output_file="deepseek_grading_results.jsonl", max_retries=3):
        """批改所有学生的作业"""
        homework_path = Path(homework_dir)
        
        if not homework_path.exists():
            logger.error(f"❌ 作业目录不存在: {homework_dir}")
            return []
        
        logger.info(f"📁 开始批改所有作业，作业目录: {homework_path.absolute()}")
        logger.info(f"🔄 重试设置: 每个学生最多重试 {max_retries} 次")
        
        results = []
        total_students = 0
        processed_students = 0
        failed_students = []
        
        # 遍历所有学生文件夹
        for student_dir in homework_path.iterdir():
            if not student_dir.is_dir() or student_dir.name.startswith('.'):
                continue
            
            total_students += 1
            student_name = student_dir.name
            homework_file = student_dir / "homework3.md"
            
            if not homework_file.exists():
                logger.warning(f"⚠️  学生 {student_name} 没有homework3.md文件")
                failed_students.append(f"{student_name} (文件不存在)")
                continue
            
            # 批改作业（带重试机制）
            result = self.grade_single_homework(student_name, homework_file, student_dir, max_retries)
            if result:
                results.append(result)
                processed_students += 1
                
                # 实时保存结果（防止中途中断丢失数据）
                self.save_results([result], output_file, mode='a')
            else:
                failed_students.append(f"{student_name} (批改失败)")
            
            # 添加延迟避免API限制（注意：重试机制内部已有延迟）
            time.sleep(1)
            
            logger.info(f"📊 进度: {processed_students}/{total_students}")
        
        # 输出最终统计
        logger.info(f"🎉 批改完成！总共处理 {processed_students}/{total_students} 个学生")
        
        if failed_students:
            logger.warning(f"⚠️  失败的学生 ({len(failed_students)} 个):")
            for failed in failed_students:
                logger.warning(f"   - {failed}")
        
        return results
    
    def save_results(self, results, output_file, mode='w'):
        """保存结果到JSONL文件"""
        try:
            with open(output_file, mode, encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
            
            if mode == 'w':
                logger.info(f"结果已保存到: {output_file}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def load_results(self, input_file):
        """从JSONL文件加载结果"""
        results = []
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
            logger.info(f"从 {input_file} 加载了 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"加载结果失败: {e}")
            return []
    
    def generate_summary(self, results):
        """生成批改统计摘要"""
        if not results:
            return "没有批改结果"
        
        total_count = len(results)
        scores = []
        
        for result in results:
            grading_result = result.get("grading_result", {})
            total_score = grading_result.get("总分", 0)
            if isinstance(total_score, (int, float)):
                scores.append(total_score)
        
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            # 统计重试信息
            retry_stats = {}
            for result in results:
                retry_count = result.get("retry_count", 0)
                retry_stats[retry_count] = retry_stats.get(retry_count, 0) + 1
            
            retry_info = "\n重试统计:"
            for retry_count in sorted(retry_stats.keys()):
                if retry_count == 0:
                    retry_info += f"\n  一次成功: {retry_stats[retry_count]} 人"
                else:
                    retry_info += f"\n  重试{retry_count}次成功: {retry_stats[retry_count]} 人"
            
            summary = f"""
{self.model_name}批改统计摘要：
========================
模型: {self.api_config.get('model', 'unknown')}
API地址: {self.api_config.get('url', 'unknown')}
总批改数量: {total_count}
平均分: {avg_score:.2f}
最高分: {max_score}
最低分: {min_score}
分数分布:
  90-100分: {len([s for s in scores if s >= 90])} 人
  80-89分:  {len([s for s in scores if 80 <= s < 90])} 人
  70-79分:  {len([s for s in scores if 70 <= s < 80])} 人
  60-69分:  {len([s for s in scores if 60 <= s < 70])} 人
  60分以下: {len([s for s in scores if s < 60])} 人{retry_info}
            """
            return summary
        else:
            return "无有效分数数据" 