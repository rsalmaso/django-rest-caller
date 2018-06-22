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

from django.http import JsonResponse
from django.urls import reverse
from django.views import View

from .models import Post


class PostMixin:
    def get_queryset(self):
        return Post.objects.all()

    def serialize(self, post):
        request = self.request
        return {
            "id": post.pk,
            "title": post.title,
            "text": post.text,
            "slug": post.slug,
            "_links": {
                "path": request.build_absolute_uri(),
                "detail": request.build_absolute_uri(reverse('api:post-detail', args=[post.pk, post.slug])),
                "view": request.build_absolute_uri(reverse('blog:post-detail', args=[post.pk, post.slug])),
            },
        }


class PostListView(PostMixin, View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "url": request.build_absolute_uri(),
            "status": 200,
            "data": [self.serialize(post) for post in self.get_queryset()],
        })


class PostDetailView(PostMixin, View):
    def get(self, request, id, slug, *args, **kwargs):
        status, data = 404, {}
        try:
            post = self.get_queryset().get(pk=int(id), slug=slug)
            status, data = 200, self.serialize(post)
        except Post.DoesNotExist:
            pass
        return JsonResponse({
            "url": request.build_absolute_uri(),
            "status": status,
            "data": data,
        })
