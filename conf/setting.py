import os
BASE_DIR = os.path.dirname(os.getcwd())

# 日志配置
standard_format = '[%(asctime)s][%(threadName)s:%(thread)d][task_id:%(name)s][%(filename)s:%(lineno)d]' \
                  '[%(levelname)s][%(message)s]' #其中name为getlogger指定的名字

simple_format = '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d]%(message)s'

id_simple_format = '[%(levelname)s][%(asctime)s] %(message)s'
LOGGING_DIC = {
    'version': 1,
    # 禁用已经存在的logger实例
    'disable_existing_loggers': False,
    # 定义日志 格式化的 工具
    'formatters': {
        'standard': {
            'format': standard_format
        },
        'simple': {
            'format': simple_format
        },
        'id_simple': {
            'format': id_simple_format
        },
    },
    # 过滤
    'filters': {},  # jango此处不同
    'handlers': {
        #打印到终端的日志
        'stream': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',  # 打印到屏幕
            'formatter': 'simple'
        },
        #打印到文件的日志,收集info及以上的日志
        'access': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件
            'formatter': 'standard',
            'filename': os.path.join(BASE_DIR, os.path.join('logs', 'xinli001.log')),       # 日志文件路径
            'maxBytes': 1024*1024*5,  # 日志大小 5M
            'backupCount': 5,
            'encoding': 'utf-8',  # 日志文件的编码，再也不用担心中文log乱码了
        },
        #打印到文件的日志,收集error及以上的日志
        'boss': {
                    'level': 'ERROR',
                    'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件
                    'formatter': 'id_simple',
                    'filename': os.path.join(BASE_DIR, os.path.join('logs', 'high_xinli001.log')),  # 日志文件
                    # 'maxBytes': 1024*1024*5,  # 日志大小 5M
                    'maxBytes': 1024*1024*5,  # 日志大小 5M
                    'backupCount': 5,
                    'encoding': 'utf-8',  # 日志文件的编码，再也不用担心中文log乱码了
                },
    },
    # logger实例
    'loggers': {
        # 默认的logger应用如下配置
        '': {
            'handlers': ['stream', 'access','boss'],  # 这里把上面定义的两个handler都加上，即log数据既写入文件又打印到屏幕
            'level': 'INFO',
            'propagate': True,  # 向上（更高level的logger）传递
        },
        # logging.getLogger(__name__)拿到的logger配置
        # 这样我们再取logger对象时logging.getLogger(__name__)，不同的文件__name__不同，这保证了打印日志时标识信息不同，
        # 但是拿着该名字去loggers里找key名时却发现找不到，于是默认使用key=''的配置
    },
}

HEADERS_FOR_BD = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3314.0 Safari/537.36 SE 2.X MetaSr 1.0',
    'Cookie': 'BDUSS=FOWFFhbUwwQVE1SGhKSjNUdldWQmk4Y3hHRn53UGpQVC1-WTNIZTFMaHhJS1JkRVFBQUFBJCQAAAAAAAAAAAEAAACBL3ukY2xlYXJza3lfbmV3AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHGTfF1xk3xdUn; pan_login_way=1; PANWEB=1;\
              STOKEN=24cbc4ccda10ce89432a63e9437e9e52870be0153e8a445af41317e3cac2f092'
}

HEADERS_FOR_XINLI001 = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN',
    'dnt': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36 Maxthon/5.2.7.5000',
}
BLOCK_LENGTH = 4194304
BDS_TOKEN = 'b8831b49eb7b45a169219f66f5a8f640'
AUDIO_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0,minimum-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Document</title>
    <style>
        img {{
            width: 100%;
        }}
        
        body {{
            height: 100%;
        }}
        
        audio {{
            position: fixed;
            width: 100%;
            left: 0;
            top: 0;
        }}
        
        .audio_box {{
            height: 32px;
        }}
        
        .content {{
            width: 50%;
            /* float: right; */
            margin: 0 auto;
        }}
        
        @media screen and (max-width: 540px) {{
            .content {{
                width: 100%;
            }}
        }}
    </style>
</head>

<body>
    <div class="audio_box">
        <audio controls='controls' poster="">
                <source src="{}" type="audio/mpeg" />
                您的浏览器不支持mp3播放
    </audio>
    </div>
    <div class="content">
        {}
    </div>
</body>

</html>
"""
NORMAL_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0,minimum-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Document</title>
    <style>
        img{{
            width: 100%;
        }}
        
        body{{
            height: 100%;
        }}
        
        .video_box {{
            display: inline-block;
            width: 45%;
        }}
        
        video {{
            position: fixed;
            margin: 0 auto;
            width: 45%;
            /* left: 50%;
            transform: translateX(-50%); */
            top: 0;
        }}
        
        .content {{
            width: 50%;
            float: right;
        }}
        
        @media screen and (max-width: 540px) {{
            video {{
                position: fixed;
                width: 100%;
                left: 0;
                top: 0;
            }}
            .content {{
                width: 100%;
                float: none;
            }}
        }}
    </style>
</head>
<body>
<div class="video_box">
    <video controls='controls' poster="">
                <source src="{}" type="video/mp4">
                您的浏览器不支持mp4播放
    </video>
</div>
<script>
    window.onload = function() {{
        var vedio_tag = document.getElementsByTagName('video')[0];
        var vedio_height = vedio_tag.offsetHeight;
        var vedio_box = document.getElementsByClassName('video_box')[0];
        vedio_box.style.height = vedio_height + "px";
        window.onresize = function() {{
            var vedio_tag = document.getElementsByTagName('video')[0];
            var vedio_height = vedio_tag.offsetHeight;
            var vedio_box = document.getElementsByClassName('video_box')[0];
            vedio_box.style.height = vedio_height + "px";
        }}
    }}
</script>
<div class="content">
 {}
</div>
</body>

</html>
"""

GET_TAGS_URLS = {
        '普通': 'https://m.xinli001.com/lesson/tagList?tag_name=free&page=1&size=20&lesson_type=normal',
        '专业': 'https://m.xinli001.com/lesson/tagList?tag_name=2128&page=1&size=20&lesson_type=pro',
        '阅读': 'https://kc.xinli001.com/lingxikc/book/api/tagList?search.channelId=522&channelId=522'
}
GET_CLASSES_URLS = {
        '普通': 'https://m.xinli001.com/lesson/tagList?tag_name={}&page=1&size=200&lesson_type=normal',
        '专业': 'https://m.xinli001.com/lesson/tagList?tag_name={}&page=1&size=200&lesson_type=pro',
        '阅读': 'https://kc.xinli001.com/lingxikc/book/api/bookTagList?search.channelId=522&search.tagId={}&channelId=522'
}
GET_ITEM_URLS = {
        '普通':' https://m.xinli001.com/lesson/getPeriodList?lesson_id={}&__from__=detail',
        '专业': 'https://m.xinli001.com/lesson/getPeriodList?lesson_id={}&__from__=detail',
        '阅读': 'https://kc.xinli001.com/lingxikc/book/api/detail?detail.bookId={}&channelId=522'
}
NET_PATH = '/壹心理7.0'