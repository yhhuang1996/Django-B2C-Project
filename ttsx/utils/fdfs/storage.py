from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client, get_tracker_conf
from django.conf import settings


class FDFSStorage(Storage):
    """fast dfs文件存储类"""
    def __init__(self, client_conf=None, base_url=None):
        """初始化传参"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        """打开文件"""
        pass

    def _save(self, name, content):
        """保存文件
        :param name:选择的上传文件的名字
        :param content:包含上传文件内容的File对象
        """

        # 创建一个Fdfs_client对象
        # 创建client实例对象的时候不能直接传入配置文件的地址字符串, 否则报错.
        # 需通过模块内get_tracker_conf函数, 获取配置文件后传入.
        conf_path = get_tracker_conf(self.client_conf)
        client = Fdfs_client(conf_path)

        # 上传文件到fdfs系统中
        # 上传成功后返回的字典内, 其中'Remote file_id'键对应的值由旧版模块string类型更改为byte类型.
        # 即, 返回的文件id是byte类型
        """
        @return dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : local_file_name,
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        }
        """
        res = client.upload_by_buffer(content.read())
        if res['Status'] != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fast dfs失败')

        # 获取返回文件的ID
        filename = res['Remote file_id']

        # 如果项目中有自定义上传类, 需要解码返回的文件id为字符串, 否则服务器报错.
        return filename.decode()

    def exists(self, name):
        """判断文件名是否可用，因为文件不在django服务器上，所以文件名一直可用"""
        return False

    def url(self, name):
        """返回访问文件的url路径"""
        return self.base_url + name
