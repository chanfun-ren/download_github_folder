#!/usr/bin/python3


import argparse
import aiohttp
import asyncio
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

async def fetch_contents_async(url, session):
    """异步获取 GitHub API 的内容"""
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            raise Exception(f"Failed to fetch {url}, status code: {response.status}")

def fetch_contents_sync(url, session):
    response = session.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch {url}, status code: {response.status_code}")
        return None

async def download_file_async(file_url, save_path, session):
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

def download_file_sync(file_url, save_path, session):
    response = session.get(file_url)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}")

async def process_async(owner, repo, path, branch='main'):
    """处理 GitHub 仓库中的所有文件和目录"""
    async with aiohttp.ClientSession() as session:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        items = await fetch_contents_async(api_url, session)
        
        tasks = []
        if items:
            for item in items['tree']:
                if item['path'].startswith(path) and item['type'] == 'blob':
                    file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
                    save_path = item['path']
                    task = asyncio.create_task(download_file_async(file_url, save_path, session))
                    tasks.append(task)
            # 等待所有下载任务完成
            await asyncio.gather(*tasks)

def process_sync(owner, repo, path, branch='main'):
    with requests.Session() as session:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        items = fetch_contents_sync(api_url, session)
        if items:
            with ThreadPoolExecutor(max_workers=10) as executor:
                for item in items['tree']:
                    if item['path'].startswith(path) and item['type'] == 'blob':
                        file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
                        save_path = item['path']
                        executor.submit(download_file_sync, file_url, save_path, session)

def main():
    parser = argparse.ArgumentParser(description='Download GitHub repository files asynchronously or synchronously.')
    parser.add_argument('url', type=str, help='GitHub URL to download files from')
    parser.add_argument('-t', '--thread', action='store_true', help='Use synchronous (threaded) download')
    parser.add_argument('-c', '--coroutine', action='store_true', help='Use asynchronous (co-routine) download')

    args = parser.parse_args()
    parsed_url = urlparse(args.url)
    owner = parsed_url.path.split('/')[1]
    repo = parsed_url.path.split('/')[2]
    branch = parsed_url.path.split('/')[4]
    path = '/'.join(parsed_url.path.split('/')[5:])

    if args.thread:
        process_sync(owner, repo, path, branch)
    elif args.coroutine:
        asyncio.run(process_async(owner, repo, path, branch))
    else:
        print("No download mode selected, please choose either --sync or --async.")

if __name__ == "__main__":
    main()
