from django import conf
from django.shortcuts import render
import os
import json


def redirect_404(request, conf):
    print('redirect 404', conf['title'])
    return render(request, "post.html")


def view_post(request, post_name):
    print(post_name)
    _dir_prefix = '../pages/blog'
    conf_json = os.path.join(_dir_prefix, post_name, 'conf.json')
    post_md = os.path.join(_dir_prefix, post_name, 'post.md')

    if not os.path.isfile(conf_json) or not os.path.isfile(post_md):
        redirect_404()

    conf = {}
    md = ''
    with open(conf_json) as fp:
        conf = json.load(fp)
    if 'published' in conf and not conf['published']:
        redirect_404()

    with open(post_md) as fp:
        md = fp.read()

    return render(request, "post.html", {'conf': conf, 'md': md})
