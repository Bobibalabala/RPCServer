import threading
import logging
import time
from traceback import format_exception
from xmlrpc.server import SimpleXMLRPCServer

logger = logging.getLogger('rpcserver')
filehandler = logging.FileHandler('rpc_server.log')
filehandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)

HOST = '0.0.0.0'
PORT = 8000

addr = (HOST, PORT)

# server = SimpleXMLRPCServer(addr, allow_none=True)

class ThreadRpcServer(SimpleXMLRPCServer):
    """rpc服务端"""
    def process_req_t(self, request, client_address):
        return super().process_request(request, client_address)

    def process_request(self, request, client_address):
        """处理请求，将请求放到线程中去进行处理"""
        t = threading.Thread(target=self.process_req_t, args=(request, client_address))
        t.daemon = True
        t.start()


class RemoteProxy:
    """用于远程调用方法的代理，即在rpc服务起来之前，先把需要进行远程调用的程序都进行注册"""
    register_dict = {}  # 记录名称和类的关系映射
    def register_class(self, classtype, registername=None):
        """用于注册类，如注册Test1，则客户端将可以通过Test1调用其方法"""
        if registername is None:
            registername = classtype.__name__
        if registername in self.register_dict:
            err = f"The registered name [{registername}] already been used!"
            logger.error(err)
            print(err)
            return
        self.register_dict[registername] = classtype

    def _execute(self, ret, func, args, kwargs):
        """用于执行相应的函数并插入结果"""
        try:
            result = func(*args, **kwargs)
            ret.insert(0, result)
        except Exception as e:
            ret.insert(0, e)

    def proxy(self, classname, methodname, *args, **kwargs):
        """用于远程调用的代理方法，客户端通过该方法调用需要调用的类的方法"""
        if classname not in self.register_dict:
            logger.error(f'{classname} is not registered!')
        if not hasattr(self.register_dict[classname], methodname):
            logger.error(f'class [{classname}] has not method [{methodname}]!')

        func = getattr(self.register_dict[classname], methodname)
        ret = [None]
        task = threading.Thread(target=self._execute(ret, func, args, kwargs))
        task.deamon = True
        task.start()
        timeout = 60
        task.join(timeout)
        if task.is_alive():
            errinfo = f'{classname}.{methodname} running timeout {timeout}s'
            logger.warning(errinfo)
        if isinstance(ret[0], Exception):
            err_info = f"call {classname}.{methodname} raise Exception:\n"
            traces = list()
            traces.append(err_info)
            traces.extend(format_exception(type(ret[0]), ret[0], ret[0].__traceback__))
            trace_info = ''.join(traces)
            logger.error(trace_info)
            raise ret[0]
        return ret[0]


# 示例
class Test:
    @classmethod
    def test(cls,a, b='test'):
        return f'this is a test: a: {a} b: {b}'


server = ThreadRpcServer(addr)
proxy = RemoteProxy()
proxy.register_class(Test)  # 注册类
server.register_instance(proxy)
server.serve_forever()





