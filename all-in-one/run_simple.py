#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的DeepSeek作业批改运行脚本
"""

from config import MODEL_CONFIGS, DEFAULT_MODEL, HOMEWORK_DIR, OUTPUT_FILE, REQUEST_DELAY
from deepseek_grader import MultiModelGrader
import logging

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """运行DeepSeek批改程序"""
    print("🚀 DeepSeek作业批改器启动中...")
    
    try:
        # 使用默认模型配置
        config = MODEL_CONFIGS[DEFAULT_MODEL]
        
        # 检查API配置
        if not config["key"] or config["key"] == "":
            print(f"❌ 错误：{config['name']} API Key未配置")
            print(f"请在config.py中设置MODEL_CONFIGS['{DEFAULT_MODEL}']['key']")
            return
        
        # 初始化批改器
        grader = MultiModelGrader(config, config['name'])
        
        # 加载提示词
        grader.load_prompt("prompt.txt")
        
        # 配置重试次数
        MAX_RETRIES = 3  # 每个学生最多重试3次
        
        # 开始批改
        print(f"🤖 使用模型: {config['name']} ({config['model']})")
        print(f"📂 作业目录: {HOMEWORK_DIR}")
        print(f"📝 输出文件: {OUTPUT_FILE}")
        print(f"⏰ 请求间隔: {REQUEST_DELAY}秒")
        print(f"🔄 重试设置: 每个学生最多重试 {MAX_RETRIES} 次")
        print("-" * 50)
        
        results = grader.grade_all_homeworks(
            homework_dir=HOMEWORK_DIR,
            output_file=OUTPUT_FILE,
            max_retries=MAX_RETRIES
        )
        
        # 生成统计摘要
        if results:
            summary = grader.generate_summary(results)
            print(summary)
            
            # 保存摘要到文件
            summary_file = OUTPUT_FILE.replace('.jsonl', '_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"📊 统计摘要已保存到: {summary_file}")
        
        print("\n🎉 批改任务完成！")
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        print("请确保prompt.txt文件存在于当前目录")
    
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        logging.exception("详细错误信息")

if __name__ == "__main__":
    main() 