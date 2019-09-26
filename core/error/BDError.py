class BaseBDError(Exception):
    def __str__(self):
        info = '错误信息:{}|返回信息:{}'.format(self.error_info, self.res_info)
        return info


class GetUploadIdError(BaseBDError):
    def __init__(self, msg, res_info):
        """
        获取百度王牌的UploadId失败后抛出的异常
        :param msg: 文件百度网盘路径
        :param res_info: 网页接口请求返回值
        """
        self.error_info = '获取：{}的UpLoadId失败'.format(msg)
        self.res_info = res_info


class UpLoadDataError(BaseBDError):
    def __init__(self, msg, res_info):
        """
        上传文件失败后抛出的异常
        :param msg: 文件百度网盘路径
        :param res_info: 网页接口请求返回值
        """
        self.error_info = '上传文件：{}失败'.format(msg)
        self.res_info = res_info


class CreataBDFileError(BaseBDError):
    def __init__(self, msg, res_info):
        """
        创建百度网盘文件失败后抛出的异常
        :param msg: 文件百度网盘路径
        :param res_info: 网页接口请求返回值
        """
        self.error_info = '创建文件：{}失败'.format(msg)
        self.res_info = res_info


class DeleteError(BaseBDError):
    def __init__(self, msg, res_info):
        self.error_info = '删除操作失败，路径数量：{}'.format(msg)
        self.res_info = res_info

