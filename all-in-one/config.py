#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型API配置文件
支持DeepSeek、OpenAI兼容格式和其他模型
"""

# 所有支持的模型配置
MODEL_CONFIGS = {
    # DeepSeek官方API
    "deepseek": {
        "name": "DeepSeek官方API",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "key": "apikey",
        "model": "deepseek-reasoner",
        "headers": {
            "Authorization": "Bearer {key}",
            "Content-Type": "application/json"
        }
    },
    
    # 本地部署的OpenAI兼容模型
    "local_openai": {
        "name": "本地OpenAI兼容模型",
        "url": "http://",  # 修改为您的本地地址
        "key": "apikey",  # 本地部署可能不需要key，或使用自定义key
        "model": "qwen3",  # 修改为您的模型名称
        "headers": {
            "Authorization": "Bearer {key}",
            "Content-Type": "application/json"
        }
    },
    
    # OpenAI官方API
    "openai": {
        "name": "OpenAI官方API",
        "url": "https://api.openai.com/v1/chat/completions",
        "key": "",  # 填入您的OpenAI API Key
        "model": "gpt-4",
        "headers": {
            "Authorization": "Bearer {key}",
            "Content-Type": "application/json"
        }
    },
    
    # 其他OpenAI兼容的服务
    "custom_openai": {
        "name": "自定义OpenAI兼容服务",
        "url": "https://your-api-endpoint.com/v1/chat/completions",  # 修改为您的API地址
        "key": "your-api-key",  # 修改为您的API Key
        "model": "your-model-name",  # 修改为您的模型名称
        "headers": {
            "Authorization": "Bearer {key}",
            "Content-Type": "application/json"
        }
    }
}

# 默认使用的模型（可修改）
DEFAULT_MODEL = "deepseek"

# 其他配置
HOMEWORK_DIR = "repos"  # 作业目录
OUTPUT_FILE = "deepseek_grading_results.jsonl"  # 输出文件
REQUEST_DELAY = 1  # 请求间隔（秒） 