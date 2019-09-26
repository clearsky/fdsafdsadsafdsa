from core.tools import SpiderTools
from conf import setting
from lxml import etree
import requests
import re
import os
import json
from core.tools import VedioTools, BDTools
from core.error import VedioError
import logging.config
from concurrent.futures import ThreadPoolExecutor
import warnings

warnings.filterwarnings("ignore")
logging.config.dictConfig(setting.LOGGING_DIC)
logger = logging.getLogger(__name__)


def thread_pool_callback(worker):
    logger.info("called thread pool executor callback function")
    worker_exception = worker.exception()
    if worker_exception:
        logger.exception("Worker return exception: {}".format(worker_exception))
        os._exit(-3)


@SpiderTools.reconnect()
def get_vedio_by_vid(vid):
    """
    通过vid获取视频解密后的二进制数据
    如果vid不指向一个mp4，则返回为空
    :param vid:vid
    :return:视频数据或空
    """
    type = 3  # 清晰度
    types = ['表情', '高清', '超清']
    while type:
        t_vid = vid[:-1] + str(type)
        m3u8_url = 'http://hls.videocc.net/605ea32bee/{}/{}.m3u8'.format(vid[-3], t_vid)
        try:
            # 测试m3u8的url
            if not m3u8_url:
                raise VedioError.M3u8UrlNoneError()
            res = requests.get(m3u8_url).text
            if not res:
                raise VedioError.M3u8UrlResIsNoneError(m3u8_url)

            ts_info_generator = VedioTools.get_vedio_by_m3u8_url(m3u8_url)  # 返回一个生成器
        except VedioError.M3u8UrlNoneError:
            logging.error('m3u8地址不能为空')
            exit(-1)
        except VedioError.M3u8UrlResIsNoneError:
            logging.debug('vid不是指向一个{}视频:{}'.format(types[type - 1], t_vid))
            type -= 1
            continue
        else:
            video_generator = VedioTools.decrypt_ts(ts_info_generator=ts_info_generator)
            return video_generator


@SpiderTools.reconnect()
def get_audio_by_vid(vid):
    vid = vid[:-1]+'1'
    url = 'https://plvod01.videocc.net/605ea32bee/{}/{}.mp3'.format(vid[-3], vid)
    audio_data = requests.get(url=url, headers=setting.HEADERS_FOR_XINLI001, verify=False).content
    return audio_data


@SpiderTools.reconnect()
def get_one_page_text(player_id, class_id, headers):
    """
    通过player_id和class_id生成对应的课程页，获取课程文本信息
    :param player_id: 用于生成课程页链接
    :param class_id: 用于生成课程页链接
    :param headers: 请求头
    :return:如果有文本信息，就返回文本byte类型信息，如果没有就返回None
    """
    url = "https://m.xinli001.com/lesson/playView?play_id={}&id={}".format(player_id, class_id)
    page_res = requests.get(url=url, headers=headers, verify=False)
    page_xpath_data = etree.HTML(page_res.text)
    text_data = None
    try:
        p_data = page_xpath_data.xpath('//div[@class="video-detail"]')[0]
        text_data = etree.tostring(p_data, encoding='utf-8')
    except Exception:
        logging.info('当前页面没有文本信息:{}'.format(url))
    finally:
        if text_data:
            return text_data.decode('utf-8')
        return text_data


def get_one_read_page_text(book_info):
    """
    获取有声书页面的文本信息
    :param book_info: 请求接口返回的json种的bookinfo
    :return: 返回有声书页面的文本信息
    """
    return book_info['draft']


@SpiderTools.reconnect()
def parse_page_text(text_data, headers, video_name, is_read=None):
    """
    解析设置html页面的格式
    :param text_data: html内容
    :param headers: 壹心理请求头
    :param video_name: 视频的名字
    :return:html数据和图片数据
    """
    res = re.findall('<img .+?>', text_data)
    img_info_list = []
    if res:
        for img in res:  # 替换页面图片路径
            src = re.findall('src=".+?"', img)
            if src:
                for src_item in src:
                    img_name = src_item.split('/')[-1].replace('"', '')
                    img_url = src_item[5:-1]
                    new_src = 'src="{}"'.format(img_name)
                    text_data = text_data.replace(src_item, new_src)
                    img_data = requests.get(url=img_url, headers=headers, verify=False).content
                    img_info = {
                        'name': img_name,
                        'data': img_data
                    }
                    img_info_list.append(img_info.copy())
    if is_read:
        html_data = setting.AUDIO_HTML.format(video_name, text_data)
    else:
        html_data = setting.NORMAL_HTML.format(video_name, text_data)
    return html_data, img_info_list


def get_data_and_upload(vid, path, bd_files, course_id=None, player_id=None, book_info=None):
    video_path = '{}.mp4'.format(path).replace('\\', '/')

    if video_path not in bd_files:
        video_data_generator = get_vedio_by_vid(vid=vid)  # 返回一个生成器
        BDTools.upload_file(video_data_generator, video_path)
        bd_files.append(video_path)
    else:
        logging.info('{}已存在'.format(video_path))
    text_path = '{}.html'.format(path)
    if text_path not in bd_files:
        html_path = '{}.html'.format(path).replace('\\', '/')
        if html_path not in bd_files:  # 如果html在网盘上没有
            text = ''  # 初始化文本
            if player_id and course_id and not book_info:  # 获取非阅读课程的text并上传
                text = get_one_page_text(player_id, course_id, setting.HEADERS_FOR_XINLI001)
            if book_info:  # 获取阅读文本
                text = get_one_read_page_text(book_info)
            if text:  # 如果存在文本
                video_name = '{}.mp4'.format(os.path.basename(path))
                html_data, img_datas = parse_page_text(text, setting.HEADERS_FOR_XINLI001, video_name)
                BDTools.upload_file(net_file_path=html_path, binary_data=html_data.encode('utf-8'))
                bd_files.append(html_path)
                for img_data in img_datas:
                    img_path = os.path.join(os.path.dirname(path), img_data['name']).replace('\\', '/')
                    if img_path not in bd_files:  # 如果图片在网盘上没有
                        BDTools.upload_file(binary_data=img_data['data'], net_file_path=img_path)
                        bd_files.append(img_path)
    else:
        logging.info('{}已存在'.format(text_path))


@SpiderTools.reconnect()
def get_course_data(course_name, course_id, course_cover, path, bd_files, what_type):
    # 获取课程cover图片，并上传
    cover_img_path = os.path.join(path, 'cover.jpg').replace('\\', '/')
    if cover_img_path not in bd_files:
        cover_img_data = requests.get(url=course_cover, headers=setting.HEADERS_FOR_XINLI001, verify=False).content
        BDTools.upload_file(binary_data=cover_img_data, net_file_path=cover_img_path)
        bd_files.append(cover_img_path)
    url = setting.GET_ITEM_URLS[what_type].format(course_id)
    course_res = requests.get(url=url, headers=setting.HEADERS_FOR_XINLI001, verify=False).text
    course_datas = json.loads(course_res)['data']

    # 简介部分内容
    try:
        noparent_datas = course_datas['noParentList']
    except Exception:
        pass
    else:
        if noparent_datas:
            for index, noparent_data in enumerate(noparent_datas):
                player_id = noparent_data['id']
                name = noparent_data['title']
                vid = noparent_data['video_id']
                if not vid:
                    continue
                temp_path = os.path.join(path, SpiderTools.get_right_name(name, index + 1))
                get_data_and_upload(vid, temp_path, bd_files, course_id, player_id)

    # 课程部分内容
    try:
        pass_list_datas = course_datas['passList']
    except Exception:
        pass
    else:
        for first_index, pass_data in enumerate(pass_list_datas):
            first_title = pass_data['title']
            first_path = os.path.join(path, SpiderTools.get_right_name(first_title, first_index + 1))
            temp_path = ''
            try:
                children = pass_data['child']
            except Exception:
                temp_path = first_path
                player_id = pass_data['id']
                course_id = pass_data['lesson_id']
                vid = pass_data['video_id']
                get_data_and_upload(vid, temp_path, bd_files, course_id, player_id)
            else:
                for second_index, child in enumerate(children):
                    second_title = child['title']
                    second_path = os.path.join(first_path, SpiderTools.get_right_name(second_title, second_index + 1))
                    try:
                        sons = child['child']
                    except Exception:
                        temp_path = second_path
                        player_id = child['id']
                        course_id = child['lesson_id']
                        vid = child['video_id']
                        get_data_and_upload(vid, temp_path, bd_files, course_id, player_id)
                    else:
                        for third_index, son in enumerate(sons):
                            third_title = son['title']
                            third_path = os.path.join(second_path,
                                                      SpiderTools.get_right_name(third_title, third_index + 1))
                            temp_path = third_path
                            player_id = son['id']
                            course_id = son['lesson_id']
                            vid = son['video_id']
                            get_data_and_upload(vid, temp_path, bd_files, course_id, player_id)


@SpiderTools.reconnect()
def get_tag_data(tag_id, headers, t_pool, path, bd_files, what_type):
    url = setting.GET_CLASSES_URLS[what_type].format(tag_id)
    res = requests.get(url=url, headers=headers, verify=False)
    courses = json.loads(res.text)['data']['items']
    for course in courses:
        course_name = course['title']
        course_id = course['id']
        course_cover = course['cover']
        temp_path = os.path.join(path, SpiderTools.get_right_name(course_name))
        # get_course_data(course_name, course_id, course_cover, temp_path, bd_files, what_type)
        t = t_pool.submit(get_course_data, course_name, course_id, course_cover, temp_path, bd_files, what_type)
        t.add_done_callback(thread_pool_callback)


@SpiderTools.reconnect()
def get_book_data(book_name, book_id, book_cover, path, bd_files):
    logging.info('开始获取有声书:{}的信息'.format(book_name))
    cover_img_path = os.path.join(path, 'cover.jpg').replace('\\', '/')
    if cover_img_path not in bd_files:
        cover_img_data = requests.get(url=book_cover, headers=setting.HEADERS_FOR_XINLI001, verify=False).content
        BDTools.upload_file(binary_data=cover_img_data, net_file_path=cover_img_path)
        bd_files.append(cover_img_path)
    url = setting.GET_ITEM_URLS['阅读'].format(book_id)
    book_res = requests.get(url=url, headers=setting.HEADERS_FOR_XINLI001, verify=False).text
    book_info = json.loads(book_res)['data']['bookInfo']
    vid = book_info['polyvVid']
    video_path = '{}.mp3'.format(os.path.join(path,SpiderTools.get_right_name(book_name))).replace('\\', '/')
    # 解析上传视频
    if video_path not in bd_files:
        video_data = get_audio_by_vid(vid)
        BDTools.upload_file(binary_data=video_data, net_file_path=video_path)
        bd_files.append(video_path)
    html_path = '{}.html'.format(os.path.join(path,SpiderTools.get_right_name(book_name))).replace('\\', '/')

    # 解析上传html
    if html_path not in bd_files:
        text = get_one_read_page_text(book_info)
        html_data, img_datas = parse_page_text(text, setting.HEADERS_FOR_XINLI001, os.path.basename(video_path), is_read=True)
        BDTools.upload_file(net_file_path=html_path, binary_data=html_data.encode('utf-8'))
        bd_files.append(html_path)
        for img_data in img_datas:
            img_path = os.path.join(path, img_data['name']).replace('\\', '/')
            if img_path not in bd_files:  # 如果图片在网盘上没有
                BDTools.upload_file(binary_data=img_data['data'], net_file_path=img_path)
                bd_files.append(img_path)


@SpiderTools.reconnect()
def get_read_tag_data(tag_id, headers, t_pool, path, bd_files):
    url = setting.GET_CLASSES_URLS['阅读'].format(tag_id)
    res = requests.get(url=url, headers=headers, verify=False)
    books = json.loads(res.text)['data']
    for book in books:
        book_name = book['title']
        book_id = book['bookId']
        book_cover = book['cover']
        temp_path = os.path.join(path, SpiderTools.get_right_name(book_name))
        t = t_pool.submit(get_book_data, book_name, book_id, book_cover, temp_path, bd_files)
        t.add_done_callback(thread_pool_callback)


@SpiderTools.reconnect()
def get_normal_course_data(t_pool, headers, path, bd_files, what_type):
    path = os.path.join(path, what_type)
    url = setting.GET_TAGS_URLS[what_type]
    res = requests.get(url=url, headers=headers, verify=False)
    try:
        json_data = json.loads(res.text)
    except Exception as e:
        logging.error('IP被禁止访问')
        logging.error(res.text)
        exit(-3)
    else:
        if what_type != '阅读':
            tags = json_data['data']['tag_list']
            for tag in tags:
                tag_name = tag['name']
                tag_id = tag['custome_tag_id']
                temp_path = os.path.join(path, SpiderTools.get_right_name(tag_name))
                get_tag_data(tag_id, headers, t_pool, temp_path, bd_files, what_type)
        else:
            tags = json_data['data'][1:]
            for tag in tags:
                tag_id = tag['tagId']
                tag_name = tag['name']
                temp_path = os.path.join(path, SpiderTools.get_right_name(tag_name))
                get_read_tag_data(tag_id, headers, t_pool, temp_path, bd_files)


def main():
    t_pool = ThreadPoolExecutor(5)
    path = setting.NET_PATH
    bd_files, _ = BDTools.get_bd_path_list(setting.HEADERS_FOR_BD, path)
    get_normal_course_data(t_pool, setting.HEADERS_FOR_XINLI001, path, bd_files, '普通')
    get_normal_course_data(t_pool, setting.HEADERS_FOR_XINLI001, path, bd_files, '专业')
    get_normal_course_data(t_pool, setting.HEADERS_FOR_XINLI001, path, bd_files, '阅读')
    t_pool.shutdown()


if __name__ == '__main__':
    main()
