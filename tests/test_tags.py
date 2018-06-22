# Copyright (C) 2018, Raffaele Salmaso <raffele@salmaso.org>
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

from django.template.exceptions import TemplateSyntaxError
from django.test import TestCase
from example.models import Post

from .utils import setup

POSTS = (
    {"id": 1, "title": "post 1", "slug": "post-1", "text": "text for post 1"},
    {"id": 2, "title": "post 2", "slug": "post-2", "text": "text for post 2"},
    {"id": 3, "title": "post 3", "slug": "post-3", "text": "text for post 3"},
)


class TestTag(TestCase):
    libraries = {'caller_tags': 'caller.templatetags.caller_tags'}

    def setUp(self):
        self.posts = [Post.objects.create(**post) for post in POSTS]

    def loads(self, value, node=None):
        if node:
            value = value.replace("""<script id="{}" type="application/json">""".format(node), "").replace("""</script>""", "")  # noqa: E501
        return json.loads(value)

    @setup({"posts": "{% load caller_tags %}{% call 'api:post-list' as 'posts' %}{{ posts|json_script:'posts-data' }}"})  # noqa: E501
    def test_list(self):
        request = self.client.get("/").wsgi_request
        output = self.engine.render_to_string("posts", {"request": request})
        data = self.loads(output, "posts-data")
        self.assertEqual(len(data["data"]), 3)

    @setup({"post": "{% load caller_tags %}{% call 'api:post-detail' 1 'post-1' as 'post' %}{{ post|json_script:'post-data' }}"})  # noqa: E501
    def test_detail(self):
        request = self.client.get("/").wsgi_request
        output = self.engine.render_to_string("post", {"request": request})
        data = self.loads(output, "post-data")
        self.assertEqual(data["data"]["slug"], "post-1")

    @setup({
        "posts": "{% load caller_tags %}{% call 'api:post-list' %}",
        "post": "{% load caller_tags %}{% call 'api:post-detail' 1 'post-1' %}",
    })
    def test_need_at_least_urlconf_as_varname_parameters(self):
        request = self.client.get("/").wsgi_request
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("posts", {"request": request})
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("post", {"request": request})

    @setup({
        "post-1": "{% load caller_tags %}{% call 'api:post-detail' id=1 'post-1' as 'post' %}{{ post|json_script:'post-data' }}",  # noqa: E501
        "post-2": "{% load caller_tags %}{% call 'api:post-detail' 1 slug='post-1' as 'post' %}{{ post|json_script:'post-data' }}",  # noqa: E501
        "post-3": "{% load caller_tags %}{% call 'api:post-detail' id=1 slug='post-1' as 'post' %}{{ post|json_script:'post-data' }}",  # noqa: E501
        "post-4": "{% load caller_tags %}{% call 'api:post-detail' 1 'post-1' as 'post' %}{{ post|json_script:'post-data' }}",  # noqa: E501
    })
    def test_cannot_mix_args_and_kwargs(self):
        request = self.client.get("/").wsgi_request
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("post-1", {"request": request})
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("post-2", {"request": request})
        output = self.engine.render_to_string("post-3", {"request": request})
        data = self.loads(output, "post-data")
        self.assertEqual(data["data"]["slug"], "post-1")
        output = self.engine.render_to_string("post-4", {"request": request})
        data = self.loads(output, "post-data")
        self.assertEqual(data["data"]["slug"], "post-1")
