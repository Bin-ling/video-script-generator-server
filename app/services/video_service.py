from modules.video_downloader.downloader import download_video, get_video_data

def download_video_wrapper(url, max_comments=100, max_replies=5):
    return download_video(url, max_comments=max_comments, max_replies=max_replies)

download_video = download_video

def get_video_data_wrapper(video_id):
    return get_video_data(video_id)
