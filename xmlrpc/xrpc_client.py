import socket
from xmlrpc.client import Fault, ServerProxy


remote_server = 'http://localhost:8000'

class Broker(ServerProxy):
    def proxy(self, classname, func, *args, **kwargs):
        options = {'kwargs': {}}
        for k in kwargs:
            options['kwargs'][k] = kwargs[k]
        try:
            params = [classname, func] + list(args) + [options]
            print(params)
            ret = self._ServerProxy__request('proxy', tuple(params))
            return ret
        except Fault as fault:
            raise socket.error(fault.faultString)
        
broker = Broker(remote_server)
ret = broker.proxy('Test', 'test', 1, b='yangbo')
print(ret)