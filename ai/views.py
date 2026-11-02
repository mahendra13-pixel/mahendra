from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
import requests

from filemanager.telegram_storage import get_telegram_file_url

from .models import (
    DeveloperProfile, AboutSection, Education, Skill,
    WorkExperience, SlideImage, UsefulLink, ContactMethod,
)


# ============================================================
# ✅ Model / slot registry
#   Each entry: (Model, mixin_map_field, special_map_getter_or_None)
#   - mixin_map_field: the field the mixin's get_telegram_map() reads
#   - special_map_getter: optional method name on the model to read a
#     DIFFERENT map (used for CV, which has its own map)
# ============================================================
_TELEGRAM_MODELS = {
    "profile":    (DeveloperProfile, "photo_telegram_files", None),
    "about":      (AboutSection,     "photo_telegram_files", None),
    "education":  (Education,        "photo_telegram_files", None),
    "experience": (WorkExperience,   "photo_telegram_files", None),
    "slide":      (SlideImage,       "image_telegram_files", None),
    "link":       (UsefulLink,       "image_telegram_files", None),
    "cv":         (DeveloperProfile, "cv_telegram_files",    "get_cv_telegram_map"),
}

_TYPE_MAP = {
    "pdf":  "application/pdf",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
    "gif":  "image/gif",
    "webp": "image/webp",
    "svg":  "image/svg+xml",
    "mp4":  "video/mp4",
    "webm": "video/webm",
    "doc":  "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt":  "text/plain; charset=utf-8",
}


def _stream_telegram(info, inline=True):
    """Fetch a Telegram file and stream it back."""
    if not info or not info.get("file_id"):
        raise Http404("File not available")
    url = get_telegram_file_url(info["file_id"])
    if not url:
        raise Http404("Could not resolve Telegram URL")
    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            raise Http404("Telegram returned an error")
    except Http404:
        raise
    except Exception:
        raise Http404("Could not fetch file from Telegram")

    filename = info.get("file_name", "file")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_type = _TYPE_MAP.get(ext, "application/octet-stream")

    disposition = "inline" if inline else "attachment"
    response = HttpResponse(r.content, content_type=content_type)
    response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    return response


def ai_links(request):
    return render(request, "ai/ai_links.html")


def developer(request):
    profile = DeveloperProfile.objects.first()

    skills_by_category = {}
    for skill in Skill.objects.all():
        skills_by_category.setdefault(skill.category or "Skills", []).append(skill)

    context = {
        "profile": profile,
        "about_sections": AboutSection.objects.filter(is_active=True),
        "education_list": Education.objects.all(),
        "skills_by_category": skills_by_category,
        "experiences": WorkExperience.objects.all(),
        "slides": SlideImage.objects.filter(is_active=True),
        "links": UsefulLink.objects.all(),
        "contacts": ContactMethod.objects.filter(is_active=True),
        "cv_info": profile.cv_info if profile else None,
    }
    return render(request, "ai/developer.html", context)


# ============================================================
# ✅ Generic proxy: /developer/media/<model>/<pk>/<slot>/
#    Public — no login. Serves any Telegram-stored image or CV.
# ============================================================
def serve_telegram_media(request, model_key, pk, slot_key):
    entry = _TELEGRAM_MODELS.get(model_key)
    if not entry:
        raise Http404("Unknown model")

    Model, _field, special_getter = entry
    obj = get_object_or_404(Model, pk=pk)

    # ✅ Use the correct map — CV uses get_cv_telegram_map, others use mixin
    if special_getter:
        tg_map = getattr(obj, special_getter)()
    else:
        tg_map = obj.get_telegram_map()

    info = tg_map.get(slot_key)
    inline = request.GET.get("download") != "1"
    return _stream_telegram(info, inline=inline)


# ============================================================
# ✅ Dedicated CV route (public — no login)
# ============================================================
def serve_cv(request):
    profile = DeveloperProfile.objects.first()
    info = profile.cv_info if profile else None
    inline = request.GET.get("download") != "1"
    return _stream_telegram(info, inline=inline)