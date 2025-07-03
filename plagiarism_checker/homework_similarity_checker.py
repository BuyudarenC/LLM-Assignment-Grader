#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux作业相似度分析工具
"""

import os
import re
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import hashlib
from difflib import SequenceMatcher
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']
rcParams['axes.unicode_minus'] = False

class HomeworkSimilarityChecker:
    """作业相似度检查器"""
    
    def __init__(self, base_path: str = "homework"):
        self.base_path = Path(base_path)
        self.homework_data = {}
        self.similarity_results = {}
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('plagiarism_check.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_homework_files(self, homework_type: str = "H3") -> Dict[str, Dict]:
        """提取指定类型的作业文件"""
        homework_files = {}
        
        if not self.base_path.exists():
            self.logger.error(f"路径不存在: {self.base_path}")
            return homework_files
            
        for student_dir in self.base_path.iterdir():
            if not student_dir.is_dir():
                continue
                
            student_name = student_dir.name
            homework_dir = student_dir / homework_type
            
            if not homework_dir.exists():
                continue
                
            # 查找作业文件
            for subdir in homework_dir.iterdir():
                if subdir.is_dir():
                    actual_homework_dir = subdir / homework_type
                    if actual_homework_dir.exists():
                        md_files = list(actual_homework_dir.glob("*.md"))
                        if md_files:
                            homework_files[student_name] = {
                                'md_file': md_files[0],
                                'image_files': list(actual_homework_dir.glob("*.png")),
                                'other_files': list(actual_homework_dir.glob("*")),
                                'dir_path': actual_homework_dir
                            }
                            
        self.logger.info(f"找到 {len(homework_files)} 份 {homework_type} 作业")
        return homework_files

    def extract_content(self, file_path: Path) -> Dict[str, Any]:
        """提取Markdown文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"无法读取文件 {file_path}: {e}")
                return {}
        
        # 提取各种内容
        extracted = {
            'raw_content': content,
            'text_content': self.extract_text_content(content),
            'code_blocks': self.extract_code_blocks(content),
            'commands': self.extract_commands(content),
            'urls': self.extract_urls(content),
            'structure': self.extract_structure(content),
            'word_count': len(content.split()),
            'char_count': len(content),
            'line_count': len(content.split('\n'))
        }
        
        return extracted

    def extract_text_content(self, content: str) -> str:
        """提取纯文本内容（去除代码块、链接等）"""
        # 去除代码块
        content = re.sub(r'```[\s\S]*?```', '', content)
        content = re.sub(r'`[^`]*`', '', content)
        
        # 去除链接
        content = re.sub(r'https?://[^\s\)]+', '', content)
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)
        
        # 去除Markdown标记
        content = re.sub(r'#+\s*', '', content)
        content = re.sub(r'\*+([^*]+)\*+', r'\1', content)
        content = re.sub(r'_+([^_]+)_+', r'\1', content)
        
        # 去除图片引用
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        
        # 清理多余空白
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

    def extract_code_blocks(self, content: str) -> List[str]:
        """提取代码块"""
        code_blocks = []
        
        # 提取代码块
        blocks = re.findall(r'```[\s\S]*?```', content)
        for block in blocks:
            # 去除```标记
            code = re.sub(r'^```.*?\n|```$', '', block, flags=re.MULTILINE).strip()
            if code:
                code_blocks.append(code)
        
        # 提取行内代码
        inline_codes = re.findall(r'`([^`]+)`', content)
        code_blocks.extend(inline_codes)
        
        return code_blocks

    def extract_commands(self, content: str) -> List[str]:
        """提取Linux命令"""
        commands = []
        
        # 常见Linux命令模式
        command_patterns = [
            r'sudo\s+\w+[^\n]*',
            r'(?:ls|cd|mkdir|chmod|chown|grep|find|ps|kill|top|df|du|mount|umount)\s+[^\n]*',
            r'systemctl\s+[^\n]*',
            r'adduser\s+[^\n]*',
            r'usermod\s+[^\n]*',
            r'fdisk\s+[^\n]*',
            r'lvm\w*\s+[^\n]*',
            r'nano\s+[^\n]*',
            r'vim\s+[^\n]*'
        ]
        
        for pattern in command_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            commands.extend(matches)
        
        # 从代码块中提取命令
        code_blocks = self.extract_code_blocks(content)
        for block in code_blocks:
            for line in block.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    commands.append(line)
        
        return list(set(commands))  # 去重

    def extract_urls(self, content: str) -> List[str]:
        """提取URL链接"""
        urls = re.findall(r'https?://[^\s\)]+', content)
        return urls

    def extract_structure(self, content: str) -> Dict[str, Any]:
        """提取文档结构"""
        structure = {
            'headings': [],
            'heading_counts': defaultdict(int),
            'sections': [],
            'list_items': 0,
            'code_block_count': 0,
            'image_count': 0,
            'link_count': 0
        }
        
        # 提取标题
        headings = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)
        for level, title in headings:
            structure['headings'].append((len(level), title.strip()))
            structure['heading_counts'][len(level)] += 1
        
        # 统计各种元素
        structure['list_items'] = len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE))
        structure['code_block_count'] = len(re.findall(r'```', content)) // 2
        structure['image_count'] = len(re.findall(r'!\[.*?\]', content))
        structure['link_count'] = len(re.findall(r'\[.*?\]\(.*?\)', content))
        
        return structure

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（使用TF-IDF + 余弦相似度）"""
        if not text1 or not text2:
            return 0.0
        
        # 中文分词
        text1_seg = ' '.join(jieba.cut(text1))
        text2_seg = ' '.join(jieba.cut(text2))
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1_seg, text2_seg])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            # 回退到简单的序列匹配
            return SequenceMatcher(None, text1, text2).ratio()

    def calculate_code_similarity(self, codes1: List[str], codes2: List[str]) -> float:
        """计算代码相似度"""
        if not codes1 or not codes2:
            return 0.0
        
        # 将所有代码合并
        code_text1 = '\n'.join(codes1).lower()
        code_text2 = '\n'.join(codes2).lower()
        
        # 标准化代码（去除空白、注释等）
        code_text1 = re.sub(r'\s+', ' ', code_text1).strip()
        code_text2 = re.sub(r'\s+', ' ', code_text2).strip()
        
        if not code_text1 or not code_text2:
            return 0.0
        
        return SequenceMatcher(None, code_text1, code_text2).ratio()

    def calculate_command_similarity(self, commands1: List[str], commands2: List[str]) -> float:
        """计算命令相似度"""
        if not commands1 or not commands2:
            return 0.0
        
        # 标准化命令
        norm_commands1 = set()
        norm_commands2 = set()
        
        for cmd in commands1:
            # 提取命令主体（去除参数）
            main_cmd = cmd.split()[0] if cmd.split() else cmd
            norm_commands1.add(main_cmd.lower())
        
        for cmd in commands2:
            main_cmd = cmd.split()[0] if cmd.split() else cmd
            norm_commands2.add(main_cmd.lower())
        
        # 计算Jaccard相似度
        intersection = len(norm_commands1.intersection(norm_commands2))
        union = len(norm_commands1.union(norm_commands2))
        
        return intersection / union if union > 0 else 0.0

    def calculate_structure_similarity(self, struct1: Dict, struct2: Dict) -> float:
        """计算结构相似度"""
        similarities = []
        
        # 标题结构相似度
        headings1 = [h[1].lower() for h in struct1['headings']]
        headings2 = [h[1].lower() for h in struct2['headings']]
        
        if headings1 and headings2:
            heading_sim = len(set(headings1).intersection(set(headings2))) / len(set(headings1).union(set(headings2)))
            similarities.append(heading_sim)
        
        # 文档元素数量相似度
        elements1 = [struct1['list_items'], struct1['code_block_count'], struct1['image_count'], struct1['link_count']]
        elements2 = [struct2['list_items'], struct2['code_block_count'], struct2['image_count'], struct2['link_count']]
        
        element_similarities = []
        for e1, e2 in zip(elements1, elements2):
            if e1 == 0 and e2 == 0:
                element_similarities.append(1.0)
            elif e1 == 0 or e2 == 0:
                element_similarities.append(0.0)
            else:
                element_similarities.append(min(e1, e2) / max(e1, e2))
        
        similarities.extend(element_similarities)
        
        return np.mean(similarities) if similarities else 0.0

    def calculate_overall_similarity(self, content1: Dict, content2: Dict, weights: Dict = None) -> Dict[str, float]:
        """计算综合相似度"""
        if weights is None:
            weights = {
                'text': 0.4,
                'code': 0.2,
                'command': 0.2,
                'structure': 0.2
            }
        
        similarities = {}
        
        # 文本相似度
        similarities['text'] = self.calculate_text_similarity(
            content1['text_content'], content2['text_content']
        )
        
        # 代码相似度
        similarities['code'] = self.calculate_code_similarity(
            content1['code_blocks'], content2['code_blocks']
        )
        
        # 命令相似度
        similarities['command'] = self.calculate_command_similarity(
            content1['commands'], content2['commands']
        )
        
        # 结构相似度
        similarities['structure'] = self.calculate_structure_similarity(
            content1['structure'], content2['structure']
        )
        
        # 计算加权总分
        similarities['overall'] = sum(
            similarities[key] * weights[key] 
            for key in weights.keys()
        )
        
        return similarities

    def check_similarity_batch(self, homework_type: str = "H3", threshold: float = 0.7) -> Dict:
        """批量检查相似度"""
        self.logger.info(f"开始批量检查 {homework_type} 作业相似度...")
        
        # 提取作业文件
        homework_files = self.extract_homework_files(homework_type)
        if len(homework_files) < 2:
            self.logger.warning("作业文件数量不足，无法进行相似度检查")
            return {}
        
        # 提取内容
        homework_contents = {}
        for student, files in homework_files.items():
            content = self.extract_content(files['md_file'])
            if content:
                homework_contents[student] = content
                self.logger.info(f"已提取 {student} 的作业内容")
        
        # 两两比较
        results = {
            'comparisons': [],
            'high_similarity_pairs': [],
            'statistics': {},
            'timestamp': datetime.now().isoformat()
        }
        
        students = list(homework_contents.keys())
        total_comparisons = len(students) * (len(students) - 1) // 2
        current_comparison = 0
        
        for i in range(len(students)):
            for j in range(i + 1, len(students)):
                current_comparison += 1
                student1, student2 = students[i], students[j]
                
                self.logger.info(f"比较进度: {current_comparison}/{total_comparisons} - {student1} vs {student2}")
                
                similarities = self.calculate_overall_similarity(
                    homework_contents[student1], 
                    homework_contents[student2]
                )
                
                comparison_result = {
                    'student1': student1,
                    'student2': student2,
                    'similarities': similarities,
                    'is_suspicious': similarities['overall'] >= threshold
                }
                
                results['comparisons'].append(comparison_result)
                
                if similarities['overall'] >= threshold:
                    results['high_similarity_pairs'].append(comparison_result)
                    self.logger.warning(
                        f"发现高相似度: {student1} vs {student2} = {similarities['overall']:.3f}"
                    )
        
        # 统计信息
        all_similarities = [comp['similarities']['overall'] for comp in results['comparisons']]
        results['statistics'] = {
            'total_comparisons': total_comparisons,
            'high_similarity_count': len(results['high_similarity_pairs']),
            'avg_similarity': np.mean(all_similarities),
            'max_similarity': np.max(all_similarities),
            'min_similarity': np.min(all_similarities),
            'std_similarity': np.std(all_similarities)
        }
        
        self.similarity_results = results
        return results

    def generate_report(self, output_file: str = "similarity_report.html"):
        """生成HTML报告"""
        if not self.similarity_results:
            self.logger.error("没有相似度检查结果，请先运行check_similarity_batch")
            return
        
        html_content = self._generate_html_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"报告已生成: {output_file}")

    def _generate_html_report(self) -> str:
        """生成HTML报告内容"""
        results = self.similarity_results
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>作业相似度检查报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .statistics {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .suspicious {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .normal {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .similarity-bar {{ background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; display: inline-block; width: 200px; }}
        .similarity-fill {{ height: 100%; background: linear-gradient(to right, #28a745, #ffc107, #dc3545); }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .high-sim {{ background-color: #ffebee; }}
        .medium-sim {{ background-color: #fff3e0; }}
        .low-sim {{ background-color: #e8f5e8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>作业相似度检查报告</h1>
        <p>生成时间: {results['timestamp']}</p>
    </div>
    
    <div class="statistics">
        <h2>统计信息</h2>
        <ul>
            <li>总比较次数: {results['statistics']['total_comparisons']}</li>
            <li>高相似度对数: {results['statistics']['high_similarity_count']}</li>
            <li>平均相似度: {results['statistics']['avg_similarity']:.3f}</li>
            <li>最高相似度: {results['statistics']['max_similarity']:.3f}</li>
            <li>最低相似度: {results['statistics']['min_similarity']:.3f}</li>
            <li>相似度标准差: {results['statistics']['std_similarity']:.3f}</li>
        </ul>
    </div>
"""
        
        # 高相似度对
        if results['high_similarity_pairs']:
            html += """
    <h2>🚨 高相似度作业对</h2>
"""
            for pair in results['high_similarity_pairs']:
                sim = pair['similarities']
                html += f"""
    <div class="suspicious">
        <h3>{pair['student1']} vs {pair['student2']}</h3>
        <p><strong>综合相似度: {sim['overall']:.3f}</strong></p>
        <ul>
            <li>文本相似度: {sim['text']:.3f}</li>
            <li>代码相似度: {sim['code']:.3f}</li>
            <li>命令相似度: {sim['command']:.3f}</li>
            <li>结构相似度: {sim['structure']:.3f}</li>
        </ul>
    </div>
"""
        
        # 详细比较表
        html += """
    <h2>详细比较结果</h2>
    <table>
        <thead>
            <tr>
                <th>学生1</th>
                <th>学生2</th>
                <th>综合相似度</th>
                <th>文本</th>
                <th>代码</th>
                <th>命令</th>
                <th>结构</th>
                <th>状态</th>
            </tr>
        </thead>
        <tbody>
"""
        
        # 按相似度排序
        sorted_comparisons = sorted(
            results['comparisons'], 
            key=lambda x: x['similarities']['overall'], 
            reverse=True
        )
        
        for comp in sorted_comparisons:
            sim = comp['similarities']
            css_class = 'high-sim' if sim['overall'] >= 0.7 else 'medium-sim' if sim['overall'] >= 0.5 else 'low-sim'
            status = '🚨 疑似抄袭' if comp['is_suspicious'] else '✅ 正常' if sim['overall'] < 0.3 else '⚠️ 需关注'
            
            html += f"""
            <tr class="{css_class}">
                <td>{comp['student1']}</td>
                <td>{comp['student2']}</td>
                <td>{sim['overall']:.3f}</td>
                <td>{sim['text']:.3f}</td>
                <td>{sim['code']:.3f}</td>
                <td>{sim['command']:.3f}</td>
                <td>{sim['structure']:.3f}</td>
                <td>{status}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>

    <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
        <h3>说明</h3>
        <ul>
            <li><strong>文本相似度</strong>: 基于TF-IDF和余弦相似度计算</li>
            <li><strong>代码相似度</strong>: 比较代码块和命令的相似程度</li>
            <li><strong>命令相似度</strong>: 比较Linux命令使用的相似度</li>
            <li><strong>结构相似度</strong>: 比较文档结构和格式的相似度</li>
            <li><strong>综合相似度</strong>: 加权平均后的总体相似度</li>
            <li><strong>阈值</strong>: 大于0.7为高相似度，需要人工审查</li>
        </ul>
    </div>
</body>
</html>
"""
        return html

    def save_results(self, output_file: str = "similarity_results.json"):
        """保存结果到JSON文件"""
        if not self.similarity_results:
            self.logger.error("没有相似度检查结果")
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.similarity_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"结果已保存到: {output_file}")

    def plot_similarity_distribution(self, output_file: str = "similarity_distribution.png"):
        """绘制相似度分布图"""
        if not self.similarity_results:
            self.logger.error("没有相似度检查结果")
            return
        
        similarities = [comp['similarities']['overall'] for comp in self.similarity_results['comparisons']]
        
        plt.figure(figsize=(12, 8))
        
        # 子图1: 直方图
        plt.subplot(2, 2, 1)
        plt.hist(similarities, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(x=0.7, color='red', linestyle='--', label='高相似度阈值(0.7)')
        plt.xlabel('相似度')
        plt.ylabel('频次')
        plt.title('相似度分布直方图')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 子图2: 箱线图
        plt.subplot(2, 2, 2)
        plt.boxplot(similarities)
        plt.ylabel('相似度')
        plt.title('相似度分布箱线图')
        plt.grid(True, alpha=0.3)
        
        # 子图3: 各维度相似度比较
        plt.subplot(2, 2, 3)
        dimensions = ['text', 'code', 'command', 'structure']
        dim_similarities = {dim: [] for dim in dimensions}
        
        for comp in self.similarity_results['comparisons']:
            for dim in dimensions:
                dim_similarities[dim].append(comp['similarities'][dim])
        
        plt.boxplot([dim_similarities[dim] for dim in dimensions], labels=dimensions)
        plt.ylabel('相似度')
        plt.title('各维度相似度分布')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 子图4: 高相似度对分布
        plt.subplot(2, 2, 4)
        high_sim_pairs = self.similarity_results['high_similarity_pairs']
        if high_sim_pairs:
            high_similarities = [pair['similarities']['overall'] for pair in high_sim_pairs]
            plt.hist(high_similarities, bins=10, alpha=0.7, color='red', edgecolor='black')
            plt.xlabel('相似度')
            plt.ylabel('频次')
            plt.title(f'高相似度对分布 (n={len(high_sim_pairs)})')
            plt.grid(True, alpha=0.3)
        else:
            plt.text(0.5, 0.5, '无高相似度对', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('高相似度对分布')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"相似度分布图已保存: {output_file}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        homework_type = sys.argv[1]
    else:
        homework_type = "H3"
    
    if len(sys.argv) > 2:
        threshold = float(sys.argv[2])
    else:
        threshold = 0.7
    
    # 创建检查器
    checker = HomeworkSimilarityChecker()
    
    # 批量检查相似度
    results = checker.check_similarity_batch(homework_type, threshold)
    
    if results:
        # 生成报告
        checker.generate_report(f"{homework_type}_similarity_report.html")
        
        # 保存结果
        checker.save_results(f"{homework_type}_similarity_results.json")
        
        # 绘制分布图
        checker.plot_similarity_distribution(f"{homework_type}_similarity_distribution.png")
        
        # 输出统计信息
        stats = results['statistics']
        print(f"\n=== {homework_type} 作业相似度检查完成 ===")
        print(f"总计比较: {stats['total_comparisons']} 对")
        print(f"疑似抄袭: {stats['high_similarity_count']} 对")
        print(f"平均相似度: {stats['avg_similarity']:.3f}")
        print(f"最高相似度: {stats['max_similarity']:.3f}")
        
        if results['high_similarity_pairs']:
            print(f"\n🚨 需要关注的高相似度对:")
            for pair in results['high_similarity_pairs'][:5]:  # 只显示前5对
                print(f"  {pair['student1']} vs {pair['student2']}: {pair['similarities']['overall']:.3f}")


if __name__ == "__main__":
    main() 