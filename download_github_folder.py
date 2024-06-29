#!/usr/bin/python3

import requests
import os
import sys
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

def fetch_contents(url, headers={}):
    """从 GitHub API 获取目录或文件的内容"""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch {url}, status code: {response.status_code}")
        return None

def download_file(file_url, save_path):
    """下载文件并保存到指定路径"""
    response = requests.get(file_url)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}")

def process_github_repo(owner, repo, path, branch='main'):
    """递归处理GitHub仓库中的所有文件和目录"""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    items = fetch_contents(api_url)
    if items:
        # 创建线程池
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for item in items['tree']:
                if item['path'].startswith(path) and item['type'] == 'blob':
                    file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
                    save_path = item['path'] # 保存路径
                    # 将下载任务提交到线程池
                    future = executor.submit(download_file, file_url, save_path)
                    futures.append(future)
            # 等待所有下载任务完成
            for future in futures:
                future.result()

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_github_folder.py <github_folder_url>")
        sys.exit(1)

    github_url = sys.argv[1]
    parsed_url = urlparse(github_url)
    path_parts = parsed_url.path.split('/')
    owner = path_parts[1]
    repo = path_parts[2]
    branch = path_parts[4]
    path = '/'.join(path_parts[5:])

    process_github_repo(owner, repo, path, branch)

if __name__ == "__main__":
    main()
