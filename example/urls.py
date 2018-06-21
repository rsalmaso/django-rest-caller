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

from django.contrib import admin
from django.urls import include, re_path as url
from django.views.generic import RedirectView

from . import api, views

api_patterns = [
    url(r'^posts/(?P<slug>.+)$', api.PostDetailView.as_view(), name='post-detail'),
    url(r'^posts$', api.PostListView.as_view(), name='post-list'),
]


blog_patterns = [
    url(r'^(?P<slug>.+)$', views.PostDetailView.as_view(), name='post-detail'),
    url(r'^$', views.PostListView.as_view(), name='post-list'),
]

urlpatterns = [
    url(r'^api/', include((api_patterns, 'api'))),
    url(r'^posts/', include((blog_patterns, 'blog'))),
    url(r'^admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url='/posts/'), name='index'),
]
