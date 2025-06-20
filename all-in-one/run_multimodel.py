#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型作业批改运行脚本
支持用户选择不同的模型进行批改
"""

from config import MODEL_CONFIGS, DEFAULT_MODEL, HOMEWORK_DIR, OUTPUT_FILE, REQUEST_DELAY
from deepseek_grader import MultiModelGrader
import logging
import sys

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def show_available_models():
    """显示所有可用的模型"""
    print("🤖 可用的模型列表:")
    print("=" * 60)
    
    for i, (model_key, config) in enumerate(MODEL_CONFIGS.items(), 1):
        status = "✅" if config["key"] and config["key"] not in ["", "your-api-key", "sk-local-key-or-empty"] else "⚠️"
        print(f"{i}. {model_key}")
        print(f"   名称: {config['name']}")
        print(f"   模型: {config['model']}")
        print(f"   地址: {config['url']}")
        print(f"   状态: {status} {'已配置' if status == '✅' else '需要配置API Key'}")
        print()

def get_user_choice():
    """获取用户选择的模型"""
    models = list(MODEL_CONFIGS.keys())
    
    while True:
        try:
            choice = input(f"请选择模型 (1-{len(models)}) 或直接按回车使用默认模型 [{DEFAULT_MODEL}]: ").strip()
            
            if not choice:
                return DEFAULT_MODEL
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(models):
                return models[choice_num - 1]
            else:
                print(f"❌ 请输入 1-{len(models)} 之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n👋 用户取消操作")
            sys.exit(0)

def validate_model_config(model_key):
    """验证模型配置"""
    config = MODEL_CONFIGS[model_key]
    
    print(f"\n🔍 验证模型配置: {config['name']}")
    print("-" * 40)
    
    # 检查必要字段
    required_fields = ["url", "model"]
    for field in required_fields:
        if not config.get(field):
            print(f"❌ 缺少必要配置: {field}")
            return False
    
    # 检查API Key（某些本地模型可能不需要）
    if model_key not in ["local_openai"] and (not config.get("key") or config["key"] in ["", "your-api-key"]):
        print(f"⚠️  警告: {config['name']} 的API Key未配置")
        confirm = input("是否继续? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    print(f"✅ 模型配置验证通过")
    return True

def test_model_connection(grader):
    """测试模型连接"""
    print(f"\n🧪 测试模型连接...")
    
    test_prompt = """
请对以下作业内容进行简单评分测试：

# 测试内容
这是一个连接测试。

请返回如下JSON格式：
{
  "总分": 85,
  "测试状态": "连接成功"
}
    """
    
    try:
        response = grader.call_llm_api(test_prompt)
        if response:
            print("✅ 模型连接测试成功")
            print(f"响应示例: {response[:100]}...")
            return True
        else:
            print("❌ 模型连接测试失败")
            return False
    except Exception as e:
        print(f"❌ 模型连接测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 多模型作业批改器")
    print("=" * 60)
    
    # 显示可用模型
    show_available_models()
    
    # 获取用户选择
    selected_model = get_user_choice()
    
    # 验证配置
    if not validate_model_config(selected_model):
        print("❌ 模型配置验证失败，退出程序")
        return
    
    config = MODEL_CONFIGS[selected_model]
    print(f"\n🎯 已选择模型: {config['name']}")
    
    try:
        # 初始化批改器
        grader = MultiModelGrader(config, config['name'])
        
        # 加载提示词
        grader.load_prompt("prompt.txt")
        
        # 测试连接（可选）
        test_connection = input("\n是否测试模型连接? (Y/n): ").strip().lower()
        if test_connection != 'n':
            if not test_model_connection(grader):
                confirm = input("连接测试失败，是否继续批改? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("👋 用户取消操作")
                    return
        
        # 配置重试次数
        MAX_RETRIES = 3
        
        # 确认开始批改
        print(f"\n📋 批改配置:")
        print(f"   模型: {config['name']} ({config['model']})")
        print(f"   作业目录: {HOMEWORK_DIR}")
        print(f"   输出文件: {OUTPUT_FILE}")
        print(f"   重试次数: {MAX_RETRIES}")
        print(f"   请求间隔: {REQUEST_DELAY}秒")
        
        confirm = input("\n确认开始批改? (Y/n): ").strip().lower()
        if confirm == 'n':
            print("👋 用户取消操作")
            return
        
        print("\n" + "=" * 60)
        print("🎬 开始批改...")
        
        # 开始批改
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
    
    except KeyboardInterrupt:
        print(f"\n⏹️  用户中断操作")
        print("📁 已批改的结果已保存到文件中")
    
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        logging.exception("详细错误信息")

if __name__ == "__main__":
    main() 