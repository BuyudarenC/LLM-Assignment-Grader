#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DeepSeek批改器的重试机制
"""

from config import DEEPSEEK_CONFIG
from deepseek_grader import DeepSeekGrader
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_retry_mechanism():
    """测试重试机制"""
    print("🧪 测试DeepSeek批改器重试机制")
    print("=" * 50)
    
    # 创建批改器实例
    grader = DeepSeekGrader(DEEPSEEK_CONFIG)
    
    # 加载提示词
    try:
        grader.load_prompt("prompt.txt")
        print("✅ 提示词加载成功")
    except Exception as e:
        print(f"❌ 提示词加载失败: {e}")
        return
    
    # 测试API配置
    print(f"📡 API配置:")
    print(f"   URL: {DEEPSEEK_CONFIG['url']}")
    print(f"   Model: {DEEPSEEK_CONFIG['model']}")
    print(f"   Key: {DEEPSEEK_CONFIG['key'][:10]}...{DEEPSEEK_CONFIG['key'][-10:]}")
    
    # 创建一个简单的测试提示
    test_prompt = """
请对以下作业内容进行评分（总分100分）：

# 测试作业
这是一个测试作业。

请按照以下JSON格式返回评分结果：
{
  "结构完整性": {"分数": 15, "理由": "结构完整"},
  "思考题回答": {"分数": 20, "理由": "回答完整"},
  "总分": 85
}
    """
    
    # 测试重试机制
    print("\n🔄 测试重试机制...")
    print("注意：如果API正常，应该第一次就成功")
    
    for attempt in range(3):
        try:
            print(f"\n📝 测试尝试 {attempt + 1}/3")
            response = grader.call_deepseek_api(test_prompt)
            
            if response:
                print("✅ API调用成功")
                print(f"响应长度: {len(response)} 字符")
                
                # 测试JSON解析
                result = grader.parse_grading_result(response)
                if result:
                    print("✅ JSON解析成功")
                    print(f"解析结果: {result}")
                    return True
                else:
                    print("❌ JSON解析失败")
            else:
                print("❌ API调用失败")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n❌ 重试机制测试失败")
    return False

def test_single_homework_with_retry():
    """测试单个作业批改的重试功能"""
    print("\n🎯 测试单个作业批改重试")
    print("=" * 50)
    
    grader = DeepSeekGrader(DEEPSEEK_CONFIG)
    
    try:
        grader.load_prompt("prompt.txt")
        
        # 模拟测试（需要实际的作业文件）
        print("💡 要测试完整的重试机制，需要实际的学生作业文件")
        print("   您可以运行: python run_simple.py")
        print("   观察重试过程中的日志输出")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 DeepSeek重试机制测试")
    print("=" * 60)
    
    # 基础功能测试
    success = test_retry_mechanism()
    
    if success:
        print("\n🎉 重试机制基础测试通过！")
        test_single_homework_with_retry()
    else:
        print("\n😞 重试机制测试失败，请检查：")
        print("1. 网络连接是否正常")
        print("2. DeepSeek API密钥是否有效")
        print("3. 提示词文件是否存在")
    
    print("\n" + "=" * 60)
    print("测试完成") 