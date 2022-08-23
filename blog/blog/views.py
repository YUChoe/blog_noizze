from django import conf
from django.shortcuts import render
import os
import json
import marko
from marko.ext import codehilite
import mimetypes
import re
import datetime

from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect
import binascii
from sys import byteorder
from itertools import islice
from collections import OrderedDict
import operator


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


def replace_strange_char(md):
    md = md.replace('‘', "'")
    md = md.replace('’', "'")
    md = md.replace('“', '"')
    md = md.replace('”', '"')
    return md


def replace_youtube(md):
    name_regex = "[^]]*"
    url_regex = "http[s]?://[^)]+"
    markup_regex = '\[({0})]\(\s*({1})\s*\)'.format(name_regex, url_regex)

    matches = []
    for match in re.findall(markup_regex, md):
        if ('youtu.be' in match[1] or
                'youtube' in match[1]):
            print('Youtube:', match)
            matches.append(match)

    template_iframe = """<iframe width="560" height="315" src="https://www.youtube.com/embed/{0}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>"""
    for match in matches:
        youtube_idx = match[1].replace('watch?v=', '').split('/')[-1]
        md = md.replace('![{}]({})'.format(match[0], match[1]), template_iframe.format(youtube_idx, match[0]))

    return md

def view_tags_redirect(request, tag_name):
    return redirect(f'/tags/{tag_name}')

def view_tags(request, tag_name):
    tag_dict = json.load(open(os.path.join(_dir_prefix, 'tag_list.json')))
    if tag_name not in tag_dict:
        return HttpResponse(f'tag[{tag_name} not found', status=404)
    
    print(isinstance(tag_dict[tag_name], list))
    tag_dict[tag_name].sort(reverse=True)
    print(f'tag[{tag_name}] has {tag_dict[tag_name]}')

    current_post_list = []
    ordered_list = json.load(open(os.path.join(_dir_prefix, 'ordered_list.json')))

    for idx in tag_dict[tag_name]:
        for item in ordered_list:
            if item['idx'] == idx:
                conf_json = os.path.join(_dir_prefix[:-5], item['path'], 'conf.json')
                conf = json.load(open(conf_json))
                conf['url'] = item['path']
                dt = datetime.datetime.fromtimestamp(item['timestamp'])
                conf['date_shorter'] = dt.strftime('%b. %d, %Y')
                # print('  ', conf['date_shorter'])
                current_post_list.append(conf)
                print(item['idx'], conf['title'])

    return render(request, "index.html", {'current_post_list': current_post_list, 'navigation': [], 'tag_cloud': []})


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

    with open(post_md, encoding='utf-8') as fp:
        # print("Reading:", post_md)
        md = fp.read()
        md = replace_strange_char(md)
        md = replace_youtube(md)
        func_markdown = marko.Markdown(extensions=['codehilite'])
        try:
            md = func_markdown(md)
        except ValueError as e:
            # error log
            print(e)
    """
    if 'media_order' in conf:
        conf['media_order'] = conf['media_order'].split(',')[0]  # show only the first media
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
    """
    ordered_list = json.load(open(os.path.join(_dir_prefix, 'ordered_list.json')))
    cidx = 0
    this_post_path = os.path.join(_dir_prefix, post_name)[9:]
    if os.name == 'nt':
        this_post_path = '/'.join([_dir_prefix, post_name])
        this_post_path = this_post_path[9:]

    for item in ordered_list:
        # print(f'    [{item["path"]}] : [{this_post_path}]')
        if item['path'] == this_post_path:
            cidx = item['idx']
            dt = datetime.datetime.fromtimestamp(item['timestamp'])
            conf['date'] = dt.strftime('%b. %d, %Y')
            break
    else:
        cidx = None

    print('Navigation: current idx:', cidx)
    navigation = {}
    navigation['curr_url'] = ordered_list[cidx]['path']
    navigation['canonical'] = 'https://blog.noizze.net/{}'.format(navigation['curr_url'])
    print('        current_url:', navigation['curr_url'])
    print('        canonical:', navigation['canonical'])

    if cidx and cidx - 1 > 0:
        navigation['prev'] = ordered_list[cidx - 1]['path']
        # print('        prev:', navigation['prev'])
        prev_conf_path = os.path.join(_dir_prefix[:-5], ordered_list[cidx - 1]['path'], 'conf.json')
        # print('        prev_conf_path:', prev_conf_path)
        if os.path.isfile(prev_conf_path):
            prev_conf = json.load(open(prev_conf_path))
            navigation['prev_title'] = prev_conf['title']
        # print('        prev_title:', (navigation['prev_title'] if 'prev_title' in navigation else ''))
    if cidx and cidx + 1 < len(ordered_list):
        navigation['next'] = ordered_list[cidx + 1]['path']
        # print('        next:', navigation['next'])
        next_conf_path = os.path.join(_dir_prefix[:-5], ordered_list[cidx + 1]['path'], 'conf.json')
        # print('        next_conf_path:', next_conf_path)
        if os.path.isfile(next_conf_path):
            next_conf = json.load(open(next_conf_path))
            navigation['next_title'] = next_conf['title']
        print('        next_title:', (navigation['next_title'] if 'next_title' in navigation else ''))

    return render(request, "post.html", {'conf': conf, 'md': md, 'post_name': post_name, 'navigation': navigation})


def view_index(request, page_num=1):
    current_post_list = []
    paging_cnt = 10
    _offset = (page_num - 1) * paging_cnt
    ordered_list = json.load(open(os.path.join(_dir_prefix, 'ordered_list.json')))
    for item in ordered_list[::-1][_offset:_offset + paging_cnt]:
        conf_json = os.path.join(_dir_prefix[:-5], item['path'], 'conf.json')
        with open(conf_json) as fp:
            conf = json.load(fp)
        conf['url'] = item['path']
        dt = datetime.datetime.fromtimestamp(item['timestamp'])
        conf['date_shorter'] = dt.strftime('%b. %d, %Y')
        # print('  ', conf['date_shorter'])
        current_post_list.append(conf)

    # TODO refacto
    navigation = {}  # next_page = [(3, true), (4, false)]
    navigation['current_page'] = page_num
    navigation['prev_prev_page'] = {}
    if (_offset + (paging_cnt * -2)) >= 0 and ordered_list[::-1][(_offset + (paging_cnt * -2))]:
        navigation['prev_prev_page']['page_num'] = page_num - 2
    navigation['prev_page'] = {}
    if (_offset + (paging_cnt * -1)) >= 0 and ordered_list[::-1][(_offset + (paging_cnt * -1))]:
        navigation['prev_page']['page_num'] = page_num - 1
    navigation['next_page'] = {}
    if (_offset + paging_cnt) < len(ordered_list) and ordered_list[::-1][_offset + paging_cnt]:  # TODO: out of Index exception
        navigation['next_page']['page_num'] = page_num + 1
    navigation['next_next_page'] = {}
    if (_offset + (paging_cnt * 2)) < len(ordered_list) and ordered_list[::-1][_offset + (paging_cnt * 2)]:
        navigation['next_next_page']['page_num'] = page_num + 2


    tag_dict = json.load(open(os.path.join(_dir_prefix, 'tag_list.json')))
    tag_cloud = []

    temp = OrderedDict()
    for tag in tag_dict:
        temp[tag] = len(tag_dict[tag])

    sorted_temp = OrderedDict(sorted(temp.items(), key=operator.itemgetter(1), reverse=True))

    for tagitem in islice(sorted_temp.items(), 30):  # top 30
        tag = tagitem[0]
        tag_cloud.append((tag, len(tag_dict[tag])))

    return render(request, "index.html", {'current_post_list': current_post_list, 'navigation': navigation, 'tag_cloud': tag_cloud})
