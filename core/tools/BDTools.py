import requests
import time
import json
import asyncio
import aiohttp
from core.error import BDError
from core.tools import SpiderTools
from conf import setting
import logging.config
logging.config.dictConfig(setting.LOGGING_DIC)
logger = logging.getLogger(__name__)


@SpiderTools.reconnect()
async def fetch(path_list, file_list, path_list2, url, session, headers):
    """

    :param path_list: 待获取文件列表的文件夹路径
    :param file_list: 存储文件路径的列表
    :param path_list2: 存储文件夹路径的列表
    :param url: 查询文件夹下数据列表的百度网盘接口
    :param session: 用于网络请求
    :param headers: 请求头
    :return: 当没有更多文件夹需要获取数据列表时，返回True
    """
    r_count = 0  # 取路径次数
    while True:
        try:
            cur_path = path_list.pop()
            break
        except:
            if r_count >= 5:  # 超过五次没取到，判断取完了
                return True
            await asyncio.sleep(1)  # 没取到，就抛出执行权限，等待疫苗
            r_count += 1
            continue
    parama = {
        'dir': cur_path,
    }
    async with session.get(url, headers=headers, params=parama) as resp:
        if resp.status in [200, 201]:
            data = await resp.text()
            json_data = json.loads(data)
            if json_data['errno'] == 0:
                for item in json_data['list']:
                    if item['isdir']:
                        path_list.append(item['path'])
                        path_list2.append(item['path'])
                        logging.info('dir-{}'.format(item['path']))
                    else:
                        file_list.append(item['path'])
                        logging.info('file-{}'.format(item['path']))
            else:  # 网盘不存在NET_PATH
                logging.info('网站不存在PATH：{}'.format(setting.NET_PATH))


# 获取百度网盘目标文件加下的文件路径和文件夹路径
def get_bd_path_list(headers, start_path):
    """
    获取百度网盘目标文件加下的文件路径和文件夹路径，采用协程方式实现
    :param headers: 请求头
    :param start_path: 目标文件夹路径
    :return: 目标文件夹下的所有文件路径和文件夹路径
    """

    async def wrap():
        url = 'https://pan.baidu.com/api/list'
        path_list = [start_path]
        file_list = []
        path_list2 = []
        async with aiohttp.ClientSession() as session:
            while True:
                res = await fetch(path_list, file_list, path_list2, url, session, headers)
                if res:
                    break
        return file_list, path_list2

    loop = asyncio.get_event_loop()
    bd_files, bd_dirs = loop.run_until_complete(wrap())
    loop.close()
    return bd_files, bd_files


@SpiderTools.reconnect()
def get_upload_id(net_file_path, s, is_split=True):
    url = "https://pan.baidu.com/api/precreate"
    data = {
        "path": net_file_path,
        "target_path": "/".join(net_file_path.split("/")[:-1]) + '/',
        "autoinit": 1,
        "isdir": 0,
        'bdstoken': setting.BDS_TOKEN,
        "block_list": '["5910a591dd8fc18c32a8f3df4fdc1761","a5fc157d78e6ad1c7e114b056c92821e"]'
    }
    if not is_split:
        data['block_list'] = '["5910a591dd8fc18c32a8f3df4fdc1761"]'
    params = {
        "startLogTime": int(time.time() * 1000),
    }
    try:
        resp = s.post(
            url=url,
            headers=setting.HEADERS_FOR_BD,
            params=params,
            data=data,
        )
        json_data = json.loads(resp.text)
        upload_id = json_data["uploadid"]
        if not json_data['errno'] == 0:
            raise BDError.GetUploadIdError(net_file_path, resp.text)
        logging.debug('获取upload成功:{}'.format(upload_id))
        return upload_id
    except Exception:
        raise BDError.GetUploadIdError(net_file_path, None)


@SpiderTools.reconnect()
def upload_data_func(upload_data, net_file_path, upload_id, s, partseq=0):
    url = "https://nj02ct01.pcs.baidu.com/rest/2.0/pcs/superfile2"
    files = {
        'file': ('blob', upload_data, 'application/octet-stream'),
    }
    params = {
        "method": "upload",
        'type': 'tmpfile',
        "path": net_file_path,
        "uploadid": upload_id,
        'app_id': '250528',
        'channel': 'chunlei',
        'clienttype': '0',
        'web': '1',
        'uploadsign': '0',
        'partseq': str(partseq),
        'bdstoken': setting.BDS_TOKEN,
    }

    while True:
        try:
            resp = s.post(
                url=url,
                headers=setting.HEADERS_FOR_BD,
                params=params,
                files=files,
            )
            try:
                x_bs_file_size = resp.headers["x-bs-file-size"]
            except:
                x_bs_file_size = 0
            try:
                content_md5 = resp.headers["Content-MD5"]
            except:
                content_md5 = ''
            logger.debug('上传分片成功,size:{},res:{}'.format(x_bs_file_size, resp.text))
            return x_bs_file_size, content_md5
        except Exception as e:
            logging.error(e)
            logger.error('上传失败，正在重试')
            time.sleep(1)


@SpiderTools.reconnect()
def creat_path(end_length, block_list, net_file_path, upload_id, s):
    x_bs_file_size = end_length
    url = "https://pan.baidu.com/api/create"
    params = {
        "isdir": 0,
        "rtype": 1,
        "channel": "chunlei",
        "web": 1,
        "app_id": "250528",
        "clienttype": 0,
        'bdstoken': setting.BDS_TOKEN,
    }
    data = {
        "path": net_file_path,
        "size": x_bs_file_size,
        "uploadid": upload_id,
        "target_path": "/".join(net_file_path.split("/")[:-1]) + '/',
        "block_list": str(block_list).replace("'", '"'),
    }
    try:
        resp = s.post(
            url=url,
            headers=setting.HEADERS_FOR_BD,
            params=params,
            data=data,
        )
        json_data = json.loads(resp.text)
        if not json_data['errno'] == 0:
            raise BDError.CreataBDFileError(net_file_path, resp.text)
        else:
            logger.debug("文件上传成功:{}".format(net_file_path))
            return True
    except Exception as ex:
        raise BDError.CreataBDFileError(net_file_path, None)




# 百度网盘上传文件
@SpiderTools.reconnect()
def upload_file(file_generator=None, net_file_path=None, binary_data=None):
    s = requests.session()
    s.keep_alive = False
    content_length = 0
    md5_list = []
    if file_generator:
        if next(file_generator):
            logging.info('分片上传:{}'.format(net_file_path))
            upload_id = get_upload_id(net_file_path, s)
            logging.info('获取uploadid成功:{}-{}'.format(net_file_path, upload_id))
            for index, data in enumerate(file_generator):
                data_size, data_md5 = upload_data_func(data, net_file_path, upload_id, s, index)
                logging.info('上传分片{}成功:{}'.format(index, net_file_path))
                content_length += int(data_size)
                md5_list.append(data_md5)
        else:
            logging.info('不分片上传:{}'.format(net_file_path))
            upload_id = get_upload_id(net_file_path, s, is_split=False)
            logging.info('获取uploadid成功:{}-{}'.format(net_file_path, upload_id))
            data = next(file_generator)
            data_size, data_md5 = upload_data_func(data, net_file_path, upload_id, s)
            content_length += int(data_size)
            md5_list.append(data_md5)
    else:
        logging.info('不分片上传:{}'.format(net_file_path))
        upload_id = get_upload_id(net_file_path, s, is_split=False)
        logging.info('获取uploadid成功:{}-{}'.format(net_file_path, upload_id))
        data_size, data_md5 = upload_data_func(binary_data, net_file_path, upload_id, s)
        content_length += int(data_size)
        md5_list.append(data_md5)
    creat_path(content_length, md5_list, net_file_path, upload_id, s)
    logging.info('文件上传成功:{}'.format(net_file_path))


# 百度网盘删除文件
@SpiderTools.reconnect()
def delete_file(net_file_path_list, headers):
    """
    百度网盘删除文件,参数为一个列表。
    此操作会删除这个列表里面所有的路径。列表最大长度为2000。
    删除不存在的路径不会报错。
    :param net_file_path_list: 待删除的路径的列表
    :return:上传成功返回True，上传失败返回对应异常
    """
    url = "https://pan.baidu.com/api/filemanager"
    params = {
        "opera": "delete",
        "onnest": "fail",
        "async": '2',
        "channel": "chunlei",
        "web": "1",
        "app_id": "250528",
        'clienttype': '0',
    }
    # 将列表转化为对应json字符串，重要的是转换为字符串才能发送
    net_file_path_list = json.dumps(net_file_path_list)
    data = {
        "filelist": str(net_file_path_list)
    }
    try:
        resp = requests.post(
            url=url,
            params=params,
            headers=headers,
            data=data,
        )

        json_data = json.loads(resp.text)
        print(resp.text)
        if not json_data['errno'] == 0:
            raise BDError.DeleteError(len(net_file_path_list), resp.text)
        else:
            return True
    except Exception:
        raise BDError.DeleteError(len(net_file_path_list), resp.text)


if __name__ == '__main__':
    # files, _ = get_bd_path_list(setting.HEADERS, '/壹心理')
    pass
