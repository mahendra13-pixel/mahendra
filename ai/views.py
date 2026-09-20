from django.shortcuts import render


def ai_links(request):
    return render(request, "ai/ai_links.html")
def developer(request):
    return render(request, "ai/developer.html")    