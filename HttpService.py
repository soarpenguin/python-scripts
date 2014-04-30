#python2.5~2.7

import optparse
import socket
import urllib
import urllib2
import httplib2

class HttpService:
    def StringBody(self, url, protocol, body, header):
        try:
            h = httplib2.Http()
            response, content = h.request(url, protocol, body, headers=header)
            if response.status==200:
                return content, True
            return content, False
        except Exception,ex:
            print str(ex)
            return str(ex),False

    def post(self, url, params, timeout=50):
        return self.__service(url, params,timeout=timeout)

    def get(self,url,timeout=50):
        return self.__service(url, timeout=timeout)

    #timeout 50s
    def __service(self, url, params=None, timeout=50):
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout( timeout )

        try:
            request = urllib2.Request( url, urllib.urlencode(params) )
            request.add_header( 'Accept-Language', 'zh-cn' )
            response = urllib2.urlopen( request )
            content = response.read()

            if response.code==200:
                return content, True
            return content, False
        except Exception,ex:
            return str(ex),False
        finally:
            if 'response' in dir():
                response.close()
            socket.setdefaulttimeout( old_timeout )

if __name__ == '__main__':
    get_data = ''
    get_data += 'id=123'

    print get_data
    #StringBody is your content
    post_data = '{"username":"xxx","password":"xxx","modules":[{"path":"heh","version":"1.0.0.0"}]}'
    print post_data

    http_service = HttpService()
    try:
        content, status = http_service.StringBody("http://www.xxx.com?"+get_data, 'POST', post_data, {'content-type':'text/plain'})
        print content
    except Exception,ex:
        print str(ex)
        print 'time out'
    pass
