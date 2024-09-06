from django.shortcuts import render, redirect
# from django.urls import reverse
# from django.views.decorators.cache import never_cache


def vcard_page(request):
    return render(request, 'vcard.html')



