from django import conf
from django.shortcuts import render
import os
import json
import marko
from marko.ext import codehilite
import mimetypes

from django.http import HttpResponse, FileResponse
import binascii
from sys import byteorder
from itertools import islice

# global
_dir_prefix = '../pages/blog'
att_extensions = ['png', 'jpg', 'gif', 'svg']

def get_info_png(filepath):
    val = {}
    if not os.path.isfile(filepath): return None

    with open(filepath, 'rb') as fp:
        fp.seek(16)
        byte_chunk = fp.read(4)
        val['width'] = int.from_bytes(byte_chunk, byteorder='big')
        byte_chunk = fp.read(4)
        val['height'] = int.from_bytes(byte_chunk, byteorder='big')
    return val


def redirect_404(request, conf):
    # print('redirect 404')  # , conf['title'])
    # return render(request, "post.html")
    return HttpResponse('post not found', status=404)


def view_attach(request, post_name, attach_name):
    attfilepath = os.path.join(_dir_prefix, post_name, attach_name)
    if os.path.isfile(attfilepath):
        for ext in att_extensions:
            if ext in attach_name:
                print("Img file", attfilepath)
                response = FileResponse(open(attfilepath, 'rb'))
                content_type = mimetypes.guess_type(attfilepath)
                response['Content-Type'] = content_type[0]
                return response



def view_post(request, post_name):
    # print(post_name)
    # FIXIT
    if '.css.map' in post_name[-8:]:
        return HttpResponse(open(os.path.join(_dir_prefix, post_name)).read())
    for ext in att_extensions:
        if ext in post_name[-3:]:
            # redirect
            response = HttpResponse(status=302)
            response['Location'] = '{}/{}'.format(request.META['HTTP_REFERER'], post_name)
            return response


    conf_json = os.path.join(_dir_prefix, post_name, 'conf.json')
    post_md = os.path.join(_dir_prefix, post_name, 'post.md')

    if not os.path.isfile(conf_json) or not os.path.isfile(post_md):
        redirect_404(request, conf_json)

    conf = {}
    md = ''
    with open(conf_json) as fp:
        conf = json.load(fp)
    if 'published' in conf and not conf['published']:
        redirect_404(request, conf_json)

    with open(post_md) as fp:
        md = fp.read()
        func_markdown = marko.Markdown(extensions=['codehilite'])
        md = func_markdown(md)

    if 'media_order' in conf:
        filepath = os.path.join(_dir_prefix, post_name, conf['media_order'])

        filename, file_extension = os.path.splitext(filepath)
        print('MMMMM', filepath, filename, file_extension)
        if file_extension == '.png':
            media_dimension = get_info_png(filepath)
        elif file_extension == '.jpg' or file_extension == '.svg':
            media_dimension = {
                'height': 1000,
                'width': 2000
            }
        print(media_dimension)
        conf['media_dimension'] = media_dimension

    ordered_list = json.load(open(os.path.join(_dir_prefix, 'ordered_list.json')))
    cidx = 0
    this_post_path = os.path.join(_dir_prefix, post_name)[9:]
    for item in ordered_list:
        # print(f'[{item["path"]}] : [{this_post_path}]')
        if item['path'] == this_post_path:
            cidx = item['idx']
            break
    else:
        cidx = None
    # print('current idx:', cidx)
    navigation = {}
    if cidx and cidx - 1 > 0:
        navigation['prev'] = ordered_list[cidx - 1]['path']
    if cidx and cidx + 1 < len(ordered_list):
        navigation['next'] = ordered_list[cidx + 1]['path']
    # print(navigation)
    return render(request, "post.html", {'conf': conf, 'md': md, 'post_name': post_name, 'navigation': navigation})


def view_index(request):
    lastst_three = []
    ordered_list = json.load(open(os.path.join(_dir_prefix, 'ordered_list.json')))
    for item in ordered_list[::-1][:5]:
        conf_json = os.path.join(_dir_prefix[:-5], item['path'], 'conf.json')
        with open(conf_json) as fp:
            conf = json.load(fp)
        conf['url'] = item['path']
        lastst_three.append(conf)

    tag_dict = json.load(open(os.path.join(_dir_prefix, 'tag_list.json')))
    tag_cloud = []
    for tagitem in islice(tag_dict.items(), 20):  # top ten
        tag = tagitem[0]
        tag_cloud.append((tag, len(tag_dict[tag])))

    return render(request, "index.html", {'lastst_three': lastst_three, 'tag_cloud': tag_cloud})