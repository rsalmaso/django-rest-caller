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
from urllib.parse import unquote_plus

from caller.utils import call
from django import template
from django.template import TemplateSyntaxError
from django.urls import reverse
from django.utils.translation import gettext as _

register = template.Library()


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
        url = unquote_plus(reverse(self.view.resolve(context), args=args, kwargs=kwargs))

        request = context["request"]
        # calling a rest framework view it assumes that it's the original HttpRequest
        request = getattr(request, "_request", request)

        varname = self.varname.resolve(context)
        context[varname] = call(
            request=request,
            url=url,
            qs={param[0]: str(param[1].resolve(context)) for param in self.params},
        )
        return ""


@register.tag(name="call")
def call_tag(parser, token):
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
            params.append([key, parser.compile_filter(value)])
        else:
            try:
                key, value = bit.split("=")
            except ValueError:
                args.append(parser.compile_filter(bit))
            else:
                kwargs[key] = parser.compile_filter(value)

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
