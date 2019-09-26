class BaseSpiderError(Exception):
    def __str__(self):
        info = '错误信息:{}'.format(self.error_info)
        return info


class MaxRteiesButFail(BaseSpiderError):
    def __init__(self, msg):
        """
        获取百度王牌的UploadId失败后抛出的异常
        :param msg: 文件百度网盘路径
        :param res_info: 网页接口请求返回值
        """
        self.error_info = '多次重试后仍旧失败:{}'.format(msg)