from functools import wraps
import time
from core.error import SpiderError, VedioError
from conf import setting
import logging.config
from requests.exceptions import ConnectTimeout, TooManyRedirects, ConnectionError

logging.config.dictConfig(setting.LOGGING_DIC)
logger = logging.getLogger(__name__)


# 重试装饰器
def reconnect(max_retries=999, delay=5, not_retry_exception_list=None):
    """
    用于网络请求失败后重试
    :param max_retries: 重试次数
    :param delay: 重试延迟时间
    :param not_retry_exception_list: 不重试的异常类型，是一个列表
    :return:
    """
    if not_retry_exception_list is None:
        not_retry_exception_list = []
    error_type = (ConnectTimeout, ConnectionError, TooManyRedirects, VedioError.M3u8UrlResIsNoneError)
    def wrapper(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            nonlocal delay, max_retries
            while max_retries > 0:
                try:
                    result = func(*args, **kwargs)
                except Exception as ex:
                    exception_type = type(ex)
                    # if not isinstance(exception_type, error_type):
                    #     raise ex
                    # else:
                    logging.error(ex)
                    logging.info('正在重试...')
                    time.sleep(delay)
                    max_retries -= 1
                else:
                    return result  # 成功的情况
            if max_retries <= 0:
                raise SpiderError.MaxRteiesButFail(func.__name__)  # 重试次数用完，仍未成功，抛出异常

        return _wrapper

    return wrapper


def get_right_name(name, number=None):
    name = name.strip().replace('\\', '') \
        .replace('/', '')\
        .replace('/', '')\
        .replace(':', '：')\
        .replace('"', '”')\
        .replace('<', "《")\
        .replace('>', '》')\
        .replace('|', '-')\
        .replace('	', '')\
        .replace('?', '')
    if number:
        name = '{}-{}'.format(number, name)
    return name