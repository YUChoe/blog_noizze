from django.shortcuts import render


def view_post(request, post_name):
    print(post_name)
    return render(request, "post.html")
