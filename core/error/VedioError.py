class BaseVedioError(Exception):
    def __str__(self):
        info = '错误信息:{}'.format(self.error_info)
        return info


class M3u8UrlNoneError(BaseVedioError):
    def __init__(self):
        """
        m3u8连接为空时抛出的异常
        """
        self.error_info = 'm3u8的url不能为空'


class M3u8UrlResIsNoneError(BaseVedioError):
    def __init__(self, msg):
        """
        m3u8的返回值为空时，返回的异常，
        :param msg:m3u8连接
        """
        self.error_info = msg
