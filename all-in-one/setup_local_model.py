#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地模型配置助手
帮助用户快速配置自己部署的OpenAI兼容模型
"""

import json
import os

def get_user_input(prompt, default=""):
    """获取用户输入，支持默认值"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("❌ 此项必须填写，请重新输入")

def test_model_connection(config):
    """测试模型连接"""
    print("\n🧪 测试模型连接...")
    
    try:
        import requests
        
        # 构建测试请求
        data = {
            "model": config["model"],
            "messages": [
                {"role": "user", "content": "请回复'连接测试成功'"}
            ],
            "max_tokens": 50
        }
        
        headers = {}
        for key, value in config["headers"].items():
            if "{key}" in value and config["key"]:
                headers[key] = value.format(key=config["key"])
            elif "{key}" not in value:
                headers[key] = value
        
        # 如果没有key，移除Authorization
        if not config["key"] or config["key"] == "no-key":
            headers.pop("Authorization", None)
        
        print(f"连接地址: {config['url']}")
        print(f"模型名称: {config['model']}")
        
        response = requests.post(
            config["url"],
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                print("✅ 连接测试成功！")
                print(f"模型响应: {result['choices'][0]['message']['content']}")
                return True
            else:
                print("❌ 连接测试失败：响应格式异常")
                print(f"响应内容: {result}")
                return False
        else:
            print(f"❌ 连接测试失败：HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🛠️  本地模型配置助手")
    print("=" * 50)
    print("此工具将帮助您配置自己部署的OpenAI兼容模型")
    print()
    
    # 获取配置信息
    print("📝 请填写您的模型配置信息:")
    print()
    
    api_url = get_user_input(
        "API地址", 
        "http://"
    )
    
    model_name = get_user_input(
        "模型名称（如: qwen2.5-7b-instruct）"
    )
    
    # API Key（可选）
    print("\n💡 提示：如果您的本地模型不需要API Key，直接按回车跳过")
    api_key = input("API Key (可选): ").strip()
    if not api_key:
        api_key = "no-key"
    
    # 显示名称
    display_name = get_user_input(
        "显示名称", 
        f"本地模型 ({model_name})"
    )
    
    # 构建配置
    config = {
        "name": display_name,
        "url": api_url,
        "key": api_key,
        "model": model_name,
        "headers": {
            "Authorization": "Bearer {key}",
            "Content-Type": "application/json"
        }
    }
    
    print(f"\n📋 您的配置:")
    print(f"   显示名称: {config['name']}")
    print(f"   API地址: {config['url']}")
    print(f"   模型名称: {config['model']}")
    print(f"   API Key: {'已设置' if api_key != 'no-key' else '无'}")
    
    # 测试连接
    if input("\n是否测试连接? (Y/n): ").strip().lower() != 'n':
        if not test_model_connection(config):
            if input("连接测试失败，是否继续保存配置? (y/N): ").strip().lower() != 'y':
                print("👋 配置已取消")
                return
    
    # 保存配置
    print(f"\n💾 保存配置...")
    
    try:
        # 读取现有配置
        with open("config.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成新的配置条目
        config_entry = f'''
    # 用户自定义本地模型
    "user_local": {{
        "name": "{config['name']}",
        "url": "{config['url']}",
        "key": "{config['key']}",
        "model": "{config['model']}",
        "headers": {{
            "Authorization": "Bearer {{key}}",
            "Content-Type": "application/json"
        }}
    }},'''
        
        # 在MODEL_CONFIGS中添加配置
        if '"user_local":' in content:
            # 替换现有配置
            import re
            pattern = r'"user_local": \{[^}]+\},'
            content = re.sub(pattern, config_entry.strip() + ',', content, flags=re.DOTALL)
        else:
            # 添加新配置
            insert_pos = content.find('}\n\n# 默认使用的模型')
            if insert_pos != -1:
                content = content[:insert_pos] + config_entry + '\n' + content[insert_pos:]
        
        # 保存文件
        with open("config.py", 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 配置已保存到 config.py")
        print(f"\n🚀 现在您可以运行:")
        print(f"   python run_multimodel.py")
        print(f"   然后选择 'user_local' 模型进行批改")
        
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        print("\n📝 请手动添加以下配置到 config.py 的 MODEL_CONFIGS 中:")
        print(json.dumps({"user_local": config}, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main() 