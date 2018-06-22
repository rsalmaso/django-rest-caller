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
from io import BytesIO
from urllib.parse import quote_plus, urlencode
from wsgiref.handlers import BaseHandler

from django import template
from django.core.servers.basehttp import get_internal_wsgi_application as get_wsgi_application
from django.template import TemplateSyntaxError
from django.urls import reverse
from django.utils.translation import gettext as _

register = template.Library()


class CallHandler(BaseHandler):
    def __init__(self, *, environ, multithread=True, multiprocess=False):
        self.stdin = BytesIO()
        self.stdout = BytesIO()
        self.stderr = BytesIO()
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
        self.stdout.flush()
        self._flush = self.stdout.flush


class CallNode(template.Node):
    def __init__(self, *, view, args, kwargs, params, varname):
        self.view = view
        self.args = args
        self.kwargs = kwargs
        self.params = params
        self.varname = varname

    def render(self, context):
        self.context = context

        args = [arg.resolve(context) for arg in self.args] if self.args else None
        kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()} if self.kwargs else None
        url = reverse(self.view.resolve(context), args=args, kwargs=kwargs)

        request = context["request"]
        # calling a rest framework view it assumes that it's the original HttpRequest
        request = getattr(request, "_request", request)

        environ = request.environ.copy()
        environ["PATH_INFO"] = url
        environ["REQUEST_METHOD"] = "GET"
        environ["CONTENT_TYPE"] = "application/json"
        environ["QUERY_STRING"] = urlencode(
            {param[0]: str(param[1].resolve(context)) for param in self.params},
            quote_via=quote_plus,
        )

        handler = CallHandler(environ=environ)
        app = get_wsgi_application()
        handler.run(app)
        response = handler.content

        varname = self.varname.resolve(context)
        context[varname] = json.loads(response)
        return ""


@register.tag
def call(parser, token):
    """
    Example::
        {% call 'api:post-list' with amount=2 as "posts" %}
        {# for javascript integration #}
        {{ posts|json_script:"posts-data" }}
        {# as context object #}
        <ul>
          {% for post in posts %}
            <li><a href="{{ post.link }}">{{ post.title }}</a></li>
          {% endfor %}
        </ul>

        {% call 'api:post-detail' pk=1 as "post" %}
        {# for javascript integration #}
        {{ post|json_script:"post-data" }}
        {# as context object #}
        <div>
          <h2>{{ post.title }}</h2>
          <p>{{ post.text }}</p>
        </div>
    """
    bits = token.split_contents()
    if len(bits) < 4:
        raise TemplateSyntaxError(_("'call' templatetag has less than 3 arguments (needs 'urlconf as varname')"))

    if bits[-2] != "as":
        raise TemplateSyntaxError(_("Missing `as 'varname' as last parameters in 'call' templatag"))

    view, args, kwargs, params, varname = template.Variable(bits[1]), [], {}, [], template.Variable(bits[-1])

    is_param = False
    for bit in bits[2:-2]:
        if bit == 'with':
            is_param = True
        elif is_param:
            key, value = bit.split("=")
            params.append([key, template.Variable(value)])
        else:
            try:
                key, value = bit.split("=")
            except ValueError:
                args.append(template.Variable(bit))
            else:
                kwargs[key] = template.Variable(value)

    if args and kwargs:
        raise TemplateSyntaxError("Cannot mix args and kwargs in 'call' templatetag!")

    args = args if args else None
    kwargs = kwargs if kwargs else None

    return CallNode(view=view, args=args, kwargs=kwargs, params=params, varname=varname)


# backport of django 2.1 json_script filter
from django.template import defaultfilters  # noqa: E402 isort:skip
if not hasattr(defaultfilters, "json_script"):
    _json_script_escapes = {
        ord('>'): '\\u003E',
        ord('<'): '\\u003C',
        ord('&'): '\\u0026',
    }

    @register.filter(is_safe=True)
    def json_script(value, element_id):
        from django.core.serializers.json import DjangoJSONEncoder
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe

        json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
        return format_html(
            '<script id="{}" type="application/json">{}</script>',
            element_id, mark_safe(json_str)
        )
