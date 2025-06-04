#!/bin/bash

while read url; do
  # 从URL提取仓库名称(不包含.git)
  repo_name=$(basename "$url" .git)
  
  # 从URL中提取域名和路径部分(用于安全显示)
  domain=$(echo "$url" | grep -o -E 'git\.cuc\.edu\.cn/[^/]+/[^/]+/[^/]+' | sed 's#git.cuc.edu.cn/##')
  safe_url="https://git.cuc.edu.cn/$domain"
  
  # 用 sed 插入 token (不打印到控制台)
  url_with_token=$(echo "$url" | sed "s#https://#https://username:access_token@#")
  
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
done < repo_urls.txt