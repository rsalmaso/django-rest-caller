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

from django.test import TestCase
from example.models import Post

from .utils import setup

POSTS = (
    {"title": "post 1", "slug": "post-1", "text": "text for post 1"},
    {"title": "post 2", "slug": "post-2", "text": "text for post 2"},
    {"title": "post 3", "slug": "post-3", "text": "text for post 3"},
)


class TestTag(TestCase):
    libraries = {'caller_tags': 'caller.templatetags.caller_tags'}

    def setUp(self):
        self.posts = [Post.objects.create(**post) for post in POSTS]

    @setup({"posts": "{% load caller_tags %}{% call 'api:post-list' as 'posts' %}{{ posts|json_script:'posts-data' }}"})  # noqa: E501
    def test_list(self):
        request = self.client.get("/").wsgi_request
        output = self.engine.render_to_string("posts", {"request": request})
        output = output.replace("""<script id="posts-data" type="application/json">""", "").replace("""</script>""", "")  # noqa: E501
        data = json.loads(output)
        self.assertEqual(len(data["data"]), 3)

    @setup({"post": "{% load caller_tags %}{% call 'api:post-detail' 'post-1' as 'post' %}{{ post|json_script:'post-data' }}"})  # noqa: E501
    def test_detail(self):
        request = self.client.get("/").wsgi_request
        output = self.engine.render_to_string("post", {"request": request})
        output = output.replace("""<script id="post-data" type="application/json">""", "").replace("""</script>""", "")
        data = json.loads(output)
        self.assertEqual(data["data"]["slug"], "post-1")
