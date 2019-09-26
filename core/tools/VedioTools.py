import requests
import re
import os
from Crypto.Cipher import AES
from core.error import VedioError
from core.tools.SpiderTools import reconnect
from conf import setting
import logging.config
from core.tools import BDTools
logging.config.dictConfig(setting.LOGGING_DIC)
logger = logging.getLogger(__name__)


@reconnect(not_retry_exception_list=[type(VedioError.M3u8UrlNoneError()), type(VedioError.M3u8UrlResIsNoneError(None))])
def get_vedio_by_m3u8_url(m3u8_url):
    """
    通过m3u8获取ts文件和key
    :param m3u8_url: m3u8的地址
    :return:key的二进制的ts二进制数据的列表
    """
    m3u8_content = requests.get(url=m3u8_url).text
    ts_urls = re.findall('http://.+\.?ts', m3u8_content)  # 找出所有js的下载地址
    key_url = re.findall('http://.+\.?key', m3u8_content)[0]  # 找出key的下载地址
    logging.info('m3u8解析完成:{}'.format(m3u8_url))

    # 第一次返回key
    ts_key = requests.get(url=key_url).content  # key的二进制数据
    logging.debug('key获取完成:{}'.format(m3u8_url))
    yield ts_key

    # 后面返回ts文件
    for ts_url in ts_urls:
        logging.debug('正在下载ts:{}'.format(ts_url))
        ts_content = requests.get(url=ts_url, timeout=15).content  # ts的二进制数据
        yield ts_content

    logging.info('ts数据获取完成:{}'.format(m3u8_url))


def decrypt_ts(ts_info_generator):
    """
    对加密的ts进行解密
    :param ts_info_generator:
    :param ts_key: 解密ts文件需要用到的key
    :param ts_content_list: ts二进制数据列表
    :return:多个ts经过解密合并的数据
    """
    logging.info('获取到key文件')
    ts_key = next(ts_info_generator)
    aes = AES.new(ts_key, AES.MODE_CBC, b'0000000000000000')
    back_data = b''
    last_data = b''
    is_split = False
    is_first = True
    for index, ts_data in enumerate(ts_info_generator):
        if last_data:
            back_data += last_data
            last_data = b''
        try:
            logging.debug('正在解密第{}个ts文件'.format(index))
            length = 16
            count = len(ts_data)
            if count < length:
                add = (length - count)
                ts_data = ts_data + (b'\0' * add)
            elif count > length:
                add = (length - (count % length))
                ts_data = ts_data + (b'\0' * add)
            temp_data = aes.decrypt(ts_data)
            temp_data.rstrip(b'\0')
        except Exception as ex:  # 如果解密出错，爬出异常
            logger.error(ex)
            logging.error(len(ts_data), ts_data)
            os._exit(-1)
        else:
            back_data += temp_data
            if len(back_data) < setting.BLOCK_LENGTH:
                continue
            elif len(back_data) > setting.BLOCK_LENGTH:
                if is_first:
                    is_split = True
                    is_first = False
                    yield True
                back_data = back_data[:setting.BLOCK_LENGTH]
                last_data = back_data[setting.BLOCK_LENGTH:]
                yield back_data
                back_data = b''
    if not is_split:
        yield False
        yield back_data
    else:  # 如果最后还有last_dat
        last_data = last_data + back_data
        back_data = b''
        while last_data:
            back_data += last_data
            last_data = b''
            if len(back_data) > setting.BLOCK_LENGTH:
                back_data = back_data[:setting.BLOCK_LENGTH]
                last_data = back_data[setting.BLOCK_LENGTH:]
            yield back_data
            back_data = b''


if __name__ == '__main__':
    key, ts_list = get_vedio_by_m3u8_url('http://hls.videocc.net/605ea32bee/c/605ea32bee5b5522b2a274b5a5ce754c_2.m3u8')
    aim_data = decrypt_ts(key, ts_list)
    with open('test.mp4', 'wb') as f:
        f.write(aim_data)
