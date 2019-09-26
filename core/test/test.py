import requests
import re
import os
from Crypto.Cipher import AES

# file_path = r'C:\Users\Administrator\Downloads\605ea32beeb421ee56d828c9b228377a_2.txt'
# file = open(file_path, 'r')
# file_content_lsit = file.readlines()
# file_content = ''
# for line in file_content_lsit:
#     file_content += line
# res = re.findall('http://.+ts', file_content)
# base_path = 'vedio'
# for item in res:
#     name = item.split('/')[-1]
#     path = os.path.join(base_path, name)
#     res = requests.get(item)
#     with open(path, 'wb') as f:
#         f.write(res.content)


key_file = open(r'C:\Users\Administrator\PycharmProjects\壹心理重构\core\test\vedio\605ea32beeb421ee56d828c9b228377a_2.key', 'rb')
key = key_file.read()
mi_file = open(r'C:\Users\Administrator\PycharmProjects\壹心理重构\core\test\vedio\605ea32beeb421ee56d828c9b228377a_2_0.ts', 'rb')
mi = mi_file.read()
aes = AES.new(key, AES.MODE_CBC)
res = aes.decrypt(mi)
with open('test.mp4', 'wb') as f:
    f.write(res)

