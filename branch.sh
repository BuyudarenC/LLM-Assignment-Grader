#!/bin/bash

# 遍历当前目录下的所有文件夹
for repo_dir in */ ; do
  # 进入仓库目录
  cd "$repo_dir" || continue

  # 获取所有远程分支名（去掉origin/HEAD和origin/前缀）
  for branch in $(git branch -r | grep -v '\->' | grep 'origin/' | sed 's#origin/##'); do
    # worktree 目录名：分支名
    worktree_dir="${branch}"
    # 如果目录已存在则跳过
    if [ -d "$worktree_dir" ]; then
      echo "目录 $repo_dir$worktree_dir 已存在，跳过"
      continue
    fi
    # 添加 worktree
    git worktree add "$worktree_dir" "origin/$branch"
  done

  cd ..
done