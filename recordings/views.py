from django.shortcuts import render


def recorder_view(request):
    """Local screen recorder — 100% client-side, no uploads."""
    return render(request, 'recordings/recorder.html')