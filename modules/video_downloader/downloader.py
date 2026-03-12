import os
import sys
import json
import time
import requests
import re
import asyncio
import hashlib

# 添加 f2 模块路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../f2-main')))
from f2.apps.douyin.handler import DouyinHandler

def get_cookies(cookies_file='cookies.txt'):
    """获取cookies
    
    Args:
        cookies_file: cookies文件路径
        
    Returns:
        dict: cookies字典
    """
    cookies = {}
    if os.path.exists(cookies_file):
        with open(cookies_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                # 尝试两种格式：
                # 1. 制表符分隔的格式（浏览器导出）
                parts = line.split('\t')
                if len(parts) >= 7:
                    # Netscape格式：域名\t标志\t路径\t安全标志\t过期时间\t名称\t值
                    cookie_name = parts[5].strip()
                    cookie_value = parts[6].strip()
                    if cookie_name and cookie_value:
                        cookies[cookie_name] = cookie_value
                else:
                    # 2. key=value格式（本系统保存）
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key and value:
                            cookies[key] = value
    
    # 打印调试信息
    if cookies:
        print(f"成功加载 {len(cookies)} 个cookies")
        # 打印一些关键cookies
        key_cookies = ['sessionid', 'passport_csrf_token', 'tt_webid', 'odin_tt']
        for key in key_cookies:
            if key in cookies:
                print(f"  {key}: {cookies[key][:20]}...")
    else:
        print("未加载到cookies，使用默认值")
        cookies = {
            'tt_webid': '1234567890123456789',
            'tt_webid_v2': '1234567890123456789',
            'sessionid': '1234567890123456789',
            'passport_csrf_token': '1234567890123456789'
        }
    return cookies

def get_video_id_from_modal_url(url, cookies_file='cookies.txt'):
    """从模态URL中提取视频ID
    
    Args:
        url: 模态URL
        cookies_file: cookies文件路径
        
    Returns:
        str: 视频ID
    """
    cookies = get_cookies(cookies_file)
    
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "Referer": "https://www.douyin.com/",
    })
    
    try:
        resp = session.get(url, timeout=10, allow_redirects=True)
        
        aweme_id_match = re.search(r'aweme_id\s*[:=]\s*["\'](\d+)["\']', resp.text)
        if aweme_id_match:
            video_id = aweme_id_match.group(1)
            return video_id
        
        modal_id_match = re.search(r'modal_id=(\d+)', url)
        if modal_id_match:
            modal_id = modal_id_match.group(1)
            return modal_id
        
    except Exception as e:
        print(f'Error extracting video ID from modal URL: {e}')
    
    raise Exception('Cannot get video ID from modal URL')

async def fetch_video_info_async(original_url, cookies_file='cookies.txt'):
    """异步获取视频信息
    
    Args:
        original_url: 原始视频URL
        cookies_file: cookies文件路径
        
    Returns:
        tuple: (play_url, desc, video_id, video)
    """
    cookies = get_cookies(cookies_file)
    kwargs = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
            "Referer": "https://www.douyin.com/",
        },
        "cookie": '; '.join([f"{k}={v}" for k, v in cookies.items()]),
        "proxies": {"http://": None, "https://": None},
    }
    
    current_url = original_url
    video_id_match = re.search(r'/video/(\d+)', current_url)
    if not video_id_match:
        session = requests.Session()
        session.cookies.update(cookies)
        session.headers.update(kwargs['headers'])
        try:
            resp = session.get(current_url, timeout=10, allow_redirects=True)
            current_url = resp.url
            video_id_match = re.search(r'/video/(\d+)', current_url)
            if not video_id_match:
                video_id_match = re.search(r'aweme_id=(\d+)', current_url)
                if not video_id_match:
                    video_id_match = re.search(r'video/(\d+)', current_url)
                if not video_id_match:
                    raise Exception('Cannot get video ID from resolved URL')
        except Exception as e:
            raise Exception(f'Cannot get video ID: {e}')
    
    video_id = video_id_match.group(1)
    video = await DouyinHandler(kwargs).fetch_one_video(aweme_id=video_id)
    
    play_url_list = video.video_play_addr
    desc = video.desc or 'Video'
    
    if play_url_list and isinstance(play_url_list, list):
        play_url = play_url_list[0]
        return play_url, desc, video_id, video
    
    raise Exception('No video download URL found')

def get_video_play_url(url, cookies_file='cookies.txt'):
    """获取视频播放URL
    
    Args:
        url: 视频URL
        cookies_file: cookies文件路径
        
    Returns:
        tuple: (play_url, desc)
    """
    original_url = url.strip().strip('`')
    
    url_match = re.search(r'https?://[^\s]+', original_url)
    if url_match:
        original_url = url_match.group(0)
    
    if 'modal_id' in original_url:
        try:
            video_id = get_video_id_from_modal_url(original_url, cookies_file)
            original_url = f'https://www.douyin.com/video/{video_id}'
        except Exception as e:
            pass
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_video_info_async(original_url, cookies_file))
        loop.close()
        return result[0], result[1]
    except Exception as e:
        raise Exception(f'Failed to get video play URL: {e}')

async def fetch_comments_async(aweme_id, cookies_file='cookies.txt', max_comments=100, max_replies=5):
    """获取视频评论
    
    Args:
        aweme_id: 视频ID
        cookies_file: cookies文件路径
        max_comments: 最大评论数
        max_replies: 每评论最大回复数
        
    Returns:
        list: 评论列表
    """
    cookies = get_cookies(cookies_file)
    kwargs = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
            "Referer": "https://www.douyin.com/",
        },
        "cookie": '; '.join([f"{k}={v}" for k, v in cookies.items()]),
        "proxies": {"http://": None, "https://": None},
    }
    
    handler = DouyinHandler(kwargs)
    comments = []
    
    async for comment_batch in handler.fetch_post_comment(aweme_id, cursor=0, page_counts=20, max_counts=max_comments):
        comment_data = comment_batch._to_dict()
        if comment_data.get('comment_id'):
            for i in range(len(comment_data['comment_id'])):
                comment = {
                    'comment_id': comment_data['comment_id'][i],
                    'text': comment_data['comment_text_raw'][i],
                    'user': comment_data['nickname_raw'][i],
                    'like_count': comment_data['like_count'][i] if 'like_count' in comment_data else 0,
                    'reply_count': comment_data['reply_count'][i] if 'reply_count' in comment_data else 0,
                    'create_time': comment_data['create_time'][i] if 'create_time' in comment_data else None
                }
                comments.append(comment)
                
                # 获取评论回复
                if comment_data.get('reply_count') and comment_data['reply_count'][i] > 0:
                    try:
                        async for reply_batch in handler.fetch_post_comment_reply(
                            aweme_id, comment_data['comment_id'][i], cursor=0, page_counts=3, max_counts=max_replies
                        ):
                            reply_data = reply_batch._to_dict()
                            if reply_data.get('reply_id'):
                                comment['replies'] = []
                                for j in range(len(reply_data['reply_id'])):
                                    reply = {
                                        'reply_id': reply_data['reply_id'][j],
                                        'text': reply_data['reply_text_raw'][j],
                                        'user': reply_data['nickname_raw'][j],
                                        'like_count': reply_data['like_count'][j] if 'like_count' in reply_data else 0,
                                        'create_time': reply_data['create_time'][j] if 'create_time' in reply_data else None
                                    }
                                    comment['replies'].append(reply)
                    except Exception as e:
                        print(f'Error fetching replies: {e}')
    
    return comments

def save_video_data(video, comments, output_dir):
    """保存视频数据到JSON文件
    
    Args:
        video: 视频对象
        comments: 评论列表
        output_dir: 输出目录
        
    Returns:
        str: 保存的文件路径
    """
    video_data = {
        'aweme_id': video.aweme_id,
        'desc': video.desc,
        'desc_raw': video.desc_raw,
        'nickname': video.nickname,
        'nickname_raw': video.nickname_raw,
        'sec_user_id': video.sec_user_id,
        'create_time': video.create_time,
        'duration': video.duration,
        'digg_count': video.digg_count,
        'comment_count': video.comment_count,
        'share_count': video.share_count,
        'collect_count': video.collect_count,
        'music_author': video.music_author,
        'music_play_url': video.music_play_url,
        'hashtag_names': video.hashtag_names,
        'hashtag_ids': video.hashtag_ids,
        'aweme_type': video.aweme_type,
        'is_original': video.is_original,
        'comments': comments,
        'timestamp': time.time()
    }
    
    data_file = os.path.join(output_dir, f'video_data_{video.aweme_id}.json')
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(video_data, f, ensure_ascii=False, indent=2)
    
    return data_file

def download_with_f2(url, fn, cookies_file='cookies.txt', max_comments=100, max_replies=5):
    """使用f2下载视频
    
    Args:
        url: 视频URL
        fn: 保存路径
        cookies_file: cookies文件路径
        max_comments: 最大评论数
        max_replies: 每评论最大回复数
        
    Returns:
        tuple: (fn, title, video, comments, data_file)
    """
    original_url = url.strip().strip('`')
    
    url_match = re.search(r'https?://[^\s]+', original_url)
    if url_match:
        original_url = url_match.group(0)
    
    if 'modal_id' in original_url:
        try:
            video_id = get_video_id_from_modal_url(original_url, cookies_file)
            original_url = f'https://www.douyin.com/video/{video_id}'
        except Exception as e:
            pass
    
    async def fetch_and_download():
        cookies = get_cookies(cookies_file)
        kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "Referer": "https://www.douyin.com/",
            },
            "cookie": '; '.join([f"{k}={v}" for k, v in cookies.items()]),
            "proxies": {"http://": None, "https://": None},
        }
        
        current_url = original_url
        video_id_match = re.search(r'/video/(\d+)', current_url)
        if not video_id_match:
            session = requests.Session()
            session.cookies.update(cookies)
            session.headers.update(kwargs['headers'])
            try:
                resp = session.get(current_url, timeout=10, allow_redirects=True)
                current_url = resp.url
                video_id_match = re.search(r'/video/(\d+)', current_url)
                if not video_id_match:
                    video_id_match = re.search(r'aweme_id=(\d+)', current_url)
                    if not video_id_match:
                        video_id_match = re.search(r'video/(\d+)', current_url)
                    if not video_id_match:
                        raise Exception('Cannot get video ID')
            except Exception as e:
                raise Exception(f'Cannot get video ID: {e}')
        
        video_id = video_id_match.group(1)
        
        # 一次性获取视频信息和评论，避免多次访问
        handler = DouyinHandler(kwargs)
        
        # 获取视频信息
        video = await handler.fetch_one_video(aweme_id=video_id)
        
        play_url_list = video.video_play_addr
        title = video.desc or 'Video'
        
        if play_url_list and isinstance(play_url_list, list):
            play_url = play_url_list[0]
            
            session = requests.Session()
            session.headers.update(kwargs['headers'])
            session.cookies.update(cookies)
            
            resp = session.get(play_url, stream=True, timeout=60)
            if resp.status_code != 200:
                raise Exception(f'Download failed: {resp.status_code}')
            
            with open(fn, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 获取评论
            comments = await fetch_comments_async(video_id, cookies_file, max_comments, max_replies)
            
            # 保存数据
            output_dir = os.path.dirname(fn)
            data_file = save_video_data(video, comments, output_dir)
            
            return fn, title, video, comments, data_file
        
        raise Exception('No video download URL found')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_and_download())
        loop.close()
        return result
    except Exception as e:
        raise Exception(f'F2 download failed: {e}')

def download_video(url, output_dir=None, max_comments=100, max_replies=5):
    """下载视频
    
    Args:
        url: 视频URL
        output_dir: 输出目录
        max_comments: 最大评论数
        max_replies: 每评论最大回复数
        
    Returns:
        tuple: (video_path, data_file, video_dir, stats, video_title, video_data_json)
        - video_path: 视频文件路径
        - data_file: JSON数据文件路径
        - video_dir: 视频目录
        - stats: 视频统计数据 {'play', 'like', 'comment', 'collect', 'share'}
        - video_title: 视频标题
        - video_data_json: 完整的视频数据JSON
    """
    url = url.strip().strip('`')
    
    # 统一的父目录
    parent_dir = "video_downloads"
    os.makedirs(parent_dir, exist_ok=True)
    
    # 为每个视频创建独立的子目录
    timestamp = int(time.time())
    video_dir = os.path.join(parent_dir, f"video_{timestamp}")
    os.makedirs(video_dir, exist_ok=True)
    
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    fn = f'tmp_{timestamp}_{url_hash}.mp4'
    fn = os.path.join(video_dir, fn)
    
    data_file = None
    try:
        result = download_with_f2(url, fn, max_comments=max_comments, max_replies=max_replies)
        if len(result) == 5:
            video_path, title, video, comments, data_file = result
            
            # 从video对象中提取统计数据
            stats = {
                'play': 0,  # F2库可能没有直接提供播放量数据
                'like': video.digg_count or 0,
                'comment': video.comment_count or 0,
                'collect': video.collect_count or 0,
                'share': video.share_count or 0
            }
            
            # 读取保存的JSON数据
            video_data_json = None
            if data_file and os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    video_data_json = json.load(f)
            
            print(f"✓ 视频数据已保存到: {data_file}")
            print(f"✓ 已获取 {len(comments)} 条评论")
            return video_path, data_file, video_dir, stats, title, video_data_json
        else:
            video_path, title = result
            return video_path, data_file, video_dir, {'play': 0, 'like': 0, 'comment': 0, 'collect': 0, 'share': 0}, title, None
    except Exception as e:
        raise Exception(f'Download failed: {e}')

def get_video_data(url):
    """获取视频的完整数据
    
    Args:
        url: 视频URL
        
    Returns:
        dict: 视频数据
    """
    # 清理URL，移除可能的反引号或其他无效字符
    original_url = url.strip().strip('`')
    
    # 提取URL中的实际视频链接
    url_match = re.search(r'https?://[^\s]+', original_url)
    if url_match:
        original_url = url_match.group(0)
    
    # 使用f2库获取视频信息
    async def fetch_video_data():
        cookies = get_cookies()
        kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "Referer": "https://www.douyin.com/",
            },
            "cookie": '; '.join([f"{k}={v}" for k, v in cookies.items()]),
            "proxies": {"http://": None, "https://": None},
        }
        
        # 提取视频ID
        current_url = original_url
        video_id_match = re.search(r'/video/(\d+)', current_url)
        if not video_id_match:
            # 尝试处理短链接
            session = requests.Session()
            session.cookies.update(cookies)
            session.headers.update(kwargs['headers'])
            try:
                resp = session.get(current_url, timeout=10, allow_redirects=True)
                current_url = resp.url
                video_id_match = re.search(r'/video/(\d+)', current_url)
                if not video_id_match:
                    # 尝试其他可能的视频ID格式
                    video_id_match = re.search(r'aweme_id=(\d+)', current_url)
                    if not video_id_match:
                        video_id_match = re.search(r'video/(\d+)', current_url)
                    if not video_id_match:
                        raise Exception('Cannot get video ID')
            except Exception as e:
                raise Exception(f'Cannot get video ID: {e}')
        
        video_id = video_id_match.group(1)
        video = await DouyinHandler(kwargs).fetch_one_video(aweme_id=video_id)
        
        # 构建完整的视频数据
        video_data = {
            'aweme_id': video.aweme_id,
            'desc': video.desc,
            'nickname': video.nickname,
            'duration': video.duration,
            'stats': {
                'play': 0,  # F2库可能没有直接提供播放量数据
                'like': video.digg_count or 0,
                'comment': video.comment_count or 0,
                'collect': video.collect_count or 0,
                'share': video.share_count or 0
            }
        }
        
        return video_data
    
    # 运行异步函数
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_video_data())
        loop.close()
        return result
    except Exception as e:
        print(f'Error getting video data: {e}')
        # 返回默认数据
        return {
            'aweme_id': '',
            'desc': '',
            'nickname': '',
            'duration': 0,
            'stats': {'play': 0, 'like': 0, 'comment': 0, 'collect': 0, 'share': 0}
        }
