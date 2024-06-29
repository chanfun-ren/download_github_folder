#!/usr/bin/python3

import asyncio
import aiohttp
import os
import sys
from urllib.parse import urlparse

async def fetch_contents(url, session):
    """异步获取 GitHub API 的内容"""
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            raise Exception(f"Failed to fetch {url}, status code: {response.status}")

async def download_file(file_url, save_path, session):
    """异步下载文件并保存到指定路径"""
    async with session.get(file_url) as response:
        if response.status == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
            print(f"Downloaded: {save_path}")
        else:
            print(f"Failed to download {file_url}")

async def process_github_repo(owner, repo, path, branch='main'):
    """处理 GitHub 仓库中的所有文件和目录"""
    async with aiohttp.ClientSession() as session:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        items = await fetch_contents(api_url, session)
        
        tasks = []
        if items:
            for item in items['tree']:
                if item['path'].startswith(path) and item['type'] == 'blob':
                    file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
                    save_path = item['path']
                    task = asyncio.create_task(download_file(file_url, save_path, session))
                    tasks.append(task)
            # 等待所有下载任务完成
            await asyncio.gather(*tasks)

def parse_github_url(url):
    """从给定的 GitHub URL 解析用户、仓库名、分支和路径"""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    owner = path_parts[1]
    repo = path_parts[2]
    branch = path_parts[4]
    path = '/'.join(path_parts[5:])
    return owner, repo, path, branch

async def main():
    if len(sys.argv) < 2:
        print("Usage: python async_down.py <github_folder_url>")
        return

    github_url = sys.argv[1]
    owner, repo, path, branch = parse_github_url(github_url)
    await process_github_repo(owner, repo, path, branch)

if __name__ == "__main__":
    asyncio.run(main())
