#!/usr/bin/env python
# encoding: utf-8

import tornado.ioloop
import tornado.httpserver
import tornado.web
from tornado.util import ObjectDict
from tornado.options import options, define, parse_command_line
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.gen import coroutine
import json
import bencode
import urllib
import os.path
import hashlib
import base64


define('debug', default=True, type=bool)
define('port', default=8888, type=int)


def torrent2magnet(torrent, rich=False):
    metadata = bencode.bdecode(torrent)
    hashcontents = bencode.bencode(metadata['info'])
    digest = hashlib.sha1(hashcontents).digest()
    b32hash = base64.b32encode(digest)
    magnet = 'magnet:?xt=urn:btih:{}'.format(b32hash)

    if rich:
        params = ObjectDict()
        params.xt = 'urn:btih:{}'.format(b32hash)
        params.dn = metadata['info']['name']
        params.tr = metadata['announce']
        if 'length' in metadata['info']:
            params.xl = metadata['info']['length']
        paramstr = urllib.urlencode(params)
        magnet = 'magnet:?{}'.format(paramstr)

    return magnet, metadata['info']

class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('index.html')


class APIBaseHandler(tornado.web.RequestHandler):

    def write(self, chunk):
        if isinstance(chunk, dict):
            value = json.dumps(chunk)
        else:
            value = chunk
        self.set_header('Content-Type', 'application/json; charset:utf-8')
        self.set_status(200)
        super(APIBaseHandler, self).write(value)

    def success(self, data):
        response = {
                'meta': {
                    'code': 0,
                    'msg': 'success!'
                },
                'data': data
            }
        self.write(response)

    def fail(self, code, msg):
        response = {
                'meta': {
                    'code': code,
                    'msg': msg
                },
                'data': None
            }
        self.write(response)

class TorrentLinkHandler(APIBaseHandler):

    @coroutine
    def post(self):
        torrent_link = self.get_argument('torrent_link', None)
        if not torrent_link:
            self.fail('3000', 'torrent link is required.')
            return

        http_client = AsyncHTTPClient()

        try:
            response = yield http_client.fetch(torrent_link)
        except ValueError as e:
            self.fail('5000', e.message)
            return
        except HTTPError as e:
            self.fail('5001', str(e))
            return
        except Exception as e:
            self.fail('5002', str(e))
            return

        try:
            magnet, info = torrent2magnet(response.body)
        except bencode.BTFailure as e:
            self.fail('4000', str(e))
            return
        else:
            data = {
                'magnet': magnet,
                # 'info': info
            }
            self.success(data)

class TorrentFileHandler(APIBaseHandler):

    def post(self):
        torrent_file = self.request.files['file'][0]

        try:
            magnet, info = torrent2magnet(torrent_file.body)
        except bencode.BTFailure as e:
            self.fail('4000', str(e))
            return
        else:
            data = {
                'magnet': magnet,
                # 'info': info
            }
            self.success(data)

class TorrentBTTianTangHandler(APIBaseHandler):

    @coroutine
    def post(self):
        url = self.get_argument("url")
        id = self.get_argument("id")
        uhash = self.get_argument("uhash")
        x = self.get_argument("imageField.x")
        y = self.get_argument("imageField.y")

        http_client = AsyncHTTPClient()

        if url[0] == '/':
            url = url[1:]
        download_url = "http://www.bttiantang.com/{}".format(url)
        data = {
            "action": "download",
            "id": id,
            "uhash": uhash,
            "imageField.x": x,
            "imageField.y": y,
        }
        response = yield http_client.fetch(download_url, method="POST", body=urllib.urlencode(data))

        try:
            magnet, info = torrent2magnet(response.body)
        except bencode.BTFailure as e:
            self.fail('4000', str(e))
            return
        else:
            data = {
                'magnet': magnet,
                # 'info': info
            }
            self.success(data)

class Application(tornado.web.Application):

    def __init__(self):
        settings = ObjectDict()

        settings.debug = options.debug
        settings.autoescape = None
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        settings.template_path = os.path.join(self.base_dir, 'templates')

        handlers = [
                (r'/', IndexHandler),
                (r'/api/torrent/link', TorrentLinkHandler),
                (r'/api/torrent/file', TorrentFileHandler),
                (r'/api/torrent/bttiantang', TorrentBTTianTangHandler),
            ]

        super(Application, self).__init__(handlers, **settings)


if __name__ == '__main__':
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    print 'Server is running on http://127.0.0.0:{port}'.format(
                port=options.port
            )
    tornado.ioloop.IOLoop.instance().start()
