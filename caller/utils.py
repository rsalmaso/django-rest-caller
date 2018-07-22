# Copyright (C) 2018, Raffaele Salmaso <raffaele@salmaso.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import json
from io import StringIO
from urllib.parse import quote_plus, urlencode
from wsgiref.handlers import BaseHandler

from django.core.handlers.wsgi import WSGIHandler as BaseAppHandler


class CallHandler(BaseHandler):
    def __init__(self, *, environ, multithread=True, multiprocess=False):
        self.stdin = StringIO()
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.environ = environ
        self.wsgi_multithread = multithread
        self.wsgi_multiprocess = multiprocess
        self.headers_sent = True
        self.content = ""

    def setup_environ(self):
        pass

    def get_stdin(self):
        return self.stdin

    def get_stderr(self):
        return self.stderr

    def add_cgi_vars(self):
        return self.environ

    def _write(self, data):
        self.content = data

    def _flush(self):
        pass


class AppHandler(BaseAppHandler):
    caller_exception = None

    def process_exception_by_middleware(self, exception, request):
        """
        Grab called exception, so can be reraised and shown it
        instead of JSONDecodeError in CallNode.render() method
        """
        self.caller_exception = exception
        super().process_exception_by_middleware(exception, request)


def call(request, url, qs=None):
        environ = request.environ.copy()
        environ["PATH_INFO"] = url
        environ["REQUEST_METHOD"] = "GET"
        environ["CONTENT_TYPE"] = "application/json"
        environ["QUERY_STRING"] = urlencode(qs, quote_via=quote_plus) if qs else ""

        handler = CallHandler(environ=environ)
        app = AppHandler()
        handler.run(app)
        response = handler.content.decode("utf-8") if isinstance(handler.content, bytes) else handler.content

        try:
            return json.loads(response)
        except Exception:
            if app.caller_exception:
                raise app.caller_exception
            raise
