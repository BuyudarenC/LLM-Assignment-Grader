#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作业查重系统配置文件
"""

# 基础配置
BASE_CONFIG = {
    # 作业目录路径
    'homework_base_path': 'homework',
    
    # 支持的作业类型
    'supported_homework_types': ['H3', 'H4', 'H5', 'chap0x03', 'chap0x04', 'chap0x05'],
    
    # 相似度阈值
    'similarity_threshold': 0.7,
    
    # 输出目录
    'output_dir': 'plagiarism_results',
    
    # 日志配置
    'log_level': 'INFO',
    'log_file': 'plagiarism_check.log'
}

# 相似度计算权重
SIMILARITY_WEIGHTS = {
    'text': 0.4,      # 文本内容权重
    'code': 0.2,      # 代码块权重  
    'command': 0.2,   # 命令权重
    'structure': 0.2  # 结构权重
}

# 文本处理配置
TEXT_CONFIG = {
    # 需要忽略的常见词汇
    'stop_words': [
        '步骤', '方法', '操作', '执行', '运行', '输入', '输出', 
        '命令', '结果', '显示', '查看', '创建', '删除', '修改',
        '安装', '配置', '启动', '停止', '重启', '测试', '验证'
    ],
    
    # 最小文本长度（字符数）
    'min_text_length': 50,
    
    # TF-IDF参数
    'tfidf_max_features': 5000,
    'tfidf_min_df': 1,
    'tfidf_max_df': 0.8
}

# 代码分析配置  
CODE_CONFIG = {
    # 需要检测的Linux命令模式
    'command_patterns': [
        r'sudo\s+\w+[^\n]*',
        r'(?:ls|cd|mkdir|chmod|chown|grep|find|ps|kill|top|df|du|mount|umount)\s+[^\n]*',
        r'systemctl\s+[^\n]*',
        r'adduser\s+[^\n]*',
        r'usermod\s+[^\n]*', 
        r'fdisk\s+[^\n]*',
        r'lvm\w*\s+[^\n]*',
        r'nano\s+[^\n]*',
        r'vim\s+[^\n]*',
        r'pvcreate\s+[^\n]*',
        r'vgcreate\s+[^\n]*',
        r'lvcreate\s+[^\n]*',
        r'lvextend\s+[^\n]*',
        r'resize2fs\s+[^\n]*'
    ],
    
    # 忽略的命令前缀
    'ignore_prefixes': ['#', '//', '/*'],
    
    # 最小命令长度
    'min_command_length': 3
}

# 报告生成配置
REPORT_CONFIG = {
    # HTML模板样式
    'html_style': {
        'font_family': "'Microsoft YaHei', Arial, sans-serif",
        'primary_color': '#007bff',
        'warning_color': '#ffc107', 
        'danger_color': '#dc3545',
        'success_color': '#28a745'
    },
    
    # 相似度级别定义
    'similarity_levels': {
        'high': {'threshold': 0.7, 'color': '#ffebee', 'label': '🚨 疑似抄袭'},
        'medium': {'threshold': 0.5, 'color': '#fff3e0', 'label': '⚠️ 需关注'},
        'low': {'threshold': 0.3, 'color': '#e8f5e8', 'label': '✅ 正常'}
    },
    
    # 图表配置
    'plot_config': {
        'figure_size': (12, 8),
        'dpi': 300,
        'style': 'seaborn',
        'chinese_font': 'SimHei'
    }
}

# 批量处理配置
BATCH_CONFIG = {
    # 并发处理数量
    'max_workers': 4,
    
    # 批处理大小
    'batch_size': 100,
    
    # 超时设置（秒）
    'timeout': 300,
    
    # 重试次数
    'max_retries': 3
}

# 文件扩展名配置
FILE_CONFIG = {
    # 支持的文档格式
    'document_extensions': ['.md', '.txt', '.doc', '.docx'],
    
    # 支持的图片格式
    'image_extensions': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    
    # 支持的代码格式
    'code_extensions': ['.sh', '.py', '.c', '.cpp', '.java'],
    
    # 忽略的文件
    'ignore_files': ['README.md', '.gitignore', '.DS_Store']
}

# 高级分析配置
ADVANCED_CONFIG = {
    # 是否启用深度分析
    'enable_deep_analysis': True,
    
    # 是否检查URL相似度
    'check_url_similarity': True,
    
    # 是否检查图片文件名相似度
    'check_image_similarity': True,
    
    # 是否生成详细日志
    'verbose_logging': True,
    
    # 是否保存中间结果
    'save_intermediate_results': True
} 