#!/bin/bash

# 显示使用方法
usage() {
    echo "用法: $0 [-d CLONE_DIR] [-f REPO_FILE]"
    echo "  -d CLONE_DIR   克隆目标目录 (默认: ./clones)"
    echo "  -f REPO_FILE   仓库URL文件 (默认: repo_urls.txt)"
    echo "  -h             显示此帮助信息"
    echo ""
    echo "注意: 需要在项目根目录创建 .env 文件，包含以下内容:"
    echo "  GIT_USERNAME=your_username"
    echo "  GIT_TOKEN=your_personal_access_token"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认设置"
    echo "  $0 -d /path/to/repos                  # 指定克隆目录"
    echo "  $0 -d ./my_repos -f my_urls.txt       # 指定克隆目录和URL文件"
    exit 1
}

# 加载 .env 文件
load_env() {
    if [ -f ".env" ]; then
        # 导出 .env 文件中的变量
        export $(grep -v '^#' .env | xargs)
        echo "已加载 .env 文件"
    else
        echo "错误: 找不到 .env 文件"
        echo "请在项目根目录创建 .env 文件，包含以下内容:"
        echo "  GIT_USERNAME=your_username"
        echo "  GIT_TOKEN=your_personal_access_token"
        echo ""
        echo "可以复制 .env.example 文件并重命名为 .env，然后填入实际的凭据"
        exit 1
    fi
}

# 验证环境变量
validate_credentials() {
    if [ -z "$GIT_USERNAME" ] || [ -z "$GIT_TOKEN" ]; then
        echo "错误: .env 文件中缺少必要的变量"
        echo "请确保 .env 文件包含以下变量:"
        echo "  GIT_USERNAME=your_username"
        echo "  GIT_TOKEN=your_personal_access_token"
        exit 1
    fi
    echo "凭据验证成功，用户: $GIT_USERNAME"
}

# 设置默认值
CLONE_DIR="./clones"
REPO_FILE="repo_urls.txt"

# 解析命令行参数
while getopts ":d:f:h" opt; do
  case $opt in
    d) CLONE_DIR="$OPTARG" ;;
    f) REPO_FILE="$OPTARG" ;;
    h) usage ;;
    \?) echo "无效选项: -$OPTARG" >&2; usage ;;
    :) echo "选项 -$OPTARG 需要参数" >&2; usage ;;
  esac
done

# 加载环境变量和验证凭据
load_env
validate_credentials

# 检查仓库URL文件是否存在
if [ ! -f "$REPO_FILE" ]; then
    echo "错误: 仓库URL文件不存在: $REPO_FILE"
    exit 1
fi

# 创建克隆目录（如果不存在）
if [ ! -d "$CLONE_DIR" ]; then
    echo "创建克隆目录: $CLONE_DIR"
    mkdir -p "$CLONE_DIR"
fi

# 进入克隆目录
cd "$CLONE_DIR" || {
    echo "错误: 无法进入目录 $CLONE_DIR"
    exit 1
}

echo "开始处理仓库，克隆到目录: $(pwd)"
echo "使用仓库文件: $REPO_FILE"
echo "=================================="

while read url; do
  # 跳过空行和注释行
  [[ -z "$url" || "$url" =~ ^[[:space:]]*# ]] && continue
  
  # 从URL提取仓库名称(不包含.git)
  repo_name=$(basename "$url" .git)
  
  # 从URL中提取域名和路径部分(用于安全显示)
  domain=$(echo "$url" | grep -o -E 'git\.cuc\.edu\.cn/[^/]+/[^/]+/[^/]+' | sed 's#git.cuc.edu.cn/##')
  safe_url="https://git.cuc.edu.cn/$domain"
  
  # 用 sed 插入 token (不打印到控制台)
  url_with_token=$(echo "$url" | sed "s#https://#https://$GIT_USERNAME:$GIT_TOKEN@#")
  
  if [ -d "$repo_name" ]; then
    echo "仓库 $repo_name 已存在，正在检查更新..."
    # 进入仓库目录
    cd "$repo_name"
    
    # 更新远程URL为带token的URL(不会显示在日志中)
    git remote set-url origin "$url_with_token" &>/dev/null
    
    # 执行git pull获取更新
    echo "正在更新 $repo_name..."
    git pull origin master || git pull origin main || echo "无法更新，可能没有默认分支或无更新"
    
    # 返回上级目录
    cd ..
  else
    echo "克隆仓库 $repo_name ($safe_url)..."
    # 克隆仓库
    git clone "$url_with_token" && echo "克隆 $repo_name 完成" || echo "克隆 $repo_name 失败"
  fi
done < "../$REPO_FILE"

echo "=================================="
echo "所有仓库处理完成！"
echo "仓库位置: $(pwd)"