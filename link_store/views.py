from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, Http404, HttpResponse
from .models import LinkCard
from filemanager.telegram_storage import (
    upload_to_telegram,
    delete_telegram_message,
    get_telegram_file_url,
)
from filemanager.utils import sanitize_filename
import requests
import os


MAX_LINKS = 9
FILE_SUFFIXES = ['', '_b', '_c', '_d']   # 4 files per slot
MAX_FILE_SIZE = 20 * 1024 * 1024          # 20 MB


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def link_store_view(request):

    # ---------- DELETE ----------
    if request.method == "POST" and "delete_id" in request.POST:
        card = get_object_or_404(LinkCard, pk=request.POST["delete_id"])

        # Delete all Telegram files attached to this card
        tg_map = card.get_telegram_map()
        for slot_key, info in tg_map.items():
            if info and info.get('message_id'):
                delete_telegram_message(info.get('message_id'))

        card.delete()
        messages.success(request, "✅ Link card permanently deleted.")
        return redirect("link_store:storage_view")

    # ---------- CREATE / EDIT ----------
    if request.method == "POST" and "save_card" in request.POST:
        card_id = request.POST.get("card_id")
        try:
            with transaction.atomic():
                if card_id:
                    card = get_object_or_404(LinkCard, pk=card_id)
                    card.name = request.POST.get("name", "").strip()
                else:
                    card = LinkCard(name=request.POST.get("name", "").strip())

                for i in range(1, MAX_LINKS + 1):
                    # ============================================================
                    # ENFORCE 20 MB UPLOAD LIMIT PER FILE
                    # ============================================================
                    for suffix in FILE_SUFFIXES:
                        check_file = request.FILES.get(f"link_file_{i}{suffix}")
                        if check_file and check_file.size > MAX_FILE_SIZE:
                            messages.error(
                                request,
                                f"❌ '{check_file.name}' is {check_file.size / 1024 / 1024:.1f} MB. Max allowed: 20 MB."
                            )
                            return redirect("link_store:storage_view")

                    setattr(card, f"link_name_{i}",
                            request.POST.get(f"link_name_{i}", "").strip() or None)
                    setattr(card, f"link_desc_{i}",
                            request.POST.get(f"link_desc_{i}", "").strip() or None)
                    setattr(card, f"link_url_{i}",
                            request.POST.get(f"link_url_{i}", "").strip() or None)

                    # ============================================================
                    # HANDLE TELEGRAM FILE OPERATIONS (upload / clear)
                    # ============================================================
                    for suffix in FILE_SUFFIXES:
                        slot_key = f"{i}{suffix}"
                        clear_flag = request.POST.get(f"clear_file_{i}{suffix}") == "on"
                        new_file = request.FILES.get(f"link_file_{i}{suffix}")

                        tg_map = card.get_telegram_map()

                        # CLEAR: delete from Telegram
                        if clear_flag and slot_key in tg_map:
                            delete_telegram_message(tg_map[slot_key].get('message_id'))
                            card.remove_telegram_file(slot_key)

                        # UPLOAD NEW: replace old if any
                        if new_file:
                            if slot_key in tg_map:
                                delete_telegram_message(tg_map[slot_key].get('message_id'))

                            info = upload_to_telegram(
                                new_file,
                                filename=sanitize_filename(new_file.name)
                            )
                            if info:
                                card.set_telegram_file(slot_key, info)
                            else:
                                messages.warning(
                                    request,
                                    f"⚠️ Could not upload '{new_file.name}' to Telegram."
                                )

                card.updated_at = timezone.localtime(timezone.now())
                card.save()
                messages.success(request, "✅ Link card saved successfully.")
        except Exception as e:
            messages.error(request, f"Error saving card: {str(e)}")

        return redirect("link_store:storage_view")

    # ---------- EDIT MODE (open form with pre-filled values) ----------
    edit_id = request.GET.get("edit")
    editing_card = None
    edit_slots = []
    if edit_id:
        editing_card = get_object_or_404(LinkCard, pk=edit_id)
        tg_map = editing_card.get_telegram_map()
        for i in range(1, MAX_LINKS + 1):
            files = []
            for suffix in FILE_SUFFIXES:
                slot_key = f"{i}{suffix}"
                files.append({
                    "suffix": suffix,
                    "slot_key": slot_key,
                    "telegram_info": tg_map.get(slot_key),
                })
            edit_slots.append({
                "index": i,
                "name": getattr(editing_card, f"link_name_{i}", "") or "",
                "desc": getattr(editing_card, f"link_desc_{i}", "") or "",
                "url":  getattr(editing_card, f"link_url_{i}", "") or "",
                "files": files,
            })

    # ---------- DETAIL MODE ----------
    detail_id = request.GET.get("view")
    viewing_card = None
    if detail_id:
        viewing_card = get_object_or_404(LinkCard, pk=detail_id)

    # ---------- LIST + SEARCH ----------
    cards = LinkCard.objects.all().order_by("-created_at")

    search_query = request.GET.get("search")
    if search_query:
        q = Q(name__icontains=search_query)
        for i in range(1, MAX_LINKS + 1):
            q |= Q(**{f"link_name_{i}__icontains": search_query})
            q |= Q(**{f"link_desc_{i}__icontains": search_query})
            q |= Q(**{f"link_url_{i}__icontains": search_query})
        cards = cards.filter(q).distinct()

    paginator = Paginator(cards, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "link_store/link_store_view.html", {
        "page_obj": page_obj,
        "editing_card": editing_card,
        "edit_slots": edit_slots,
        "viewing_card": viewing_card,
        "max_links": range(1, MAX_LINKS + 1),
        "search_query": search_query or "",
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def link_delete_file(request, pk, slot, suffix=''):
    """Delete one file. URL pattern includes slot; suffix passed via query string."""
    card = get_object_or_404(LinkCard, pk=pk)

    # If suffix not in URL, read from query string
    if not suffix:
        suffix = request.GET.get("suffix", "")

    if suffix not in FILE_SUFFIXES:
        return JsonResponse({"status": "error", "message": "Invalid suffix"}, status=400)

    slot_key = f"{slot}{suffix}"
    tg_map = card.get_telegram_map()

    if slot_key not in tg_map:
        return JsonResponse({"status": "error", "message": "No file found"}, status=404)

    # Delete the Telegram message (and its file)
    delete_telegram_message(tg_map[slot_key].get('message_id'))

    # Remove from the map
    card.remove_telegram_file(slot_key)
    card.save()

    return JsonResponse({"status": "success", "message": "File deleted."})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def serve_telegram_file(request, pk, slot_key):
    """Proxy the Telegram file through Django so it displays inline."""
    card = get_object_or_404(LinkCard, pk=pk)
    tg_map = card.get_telegram_map()

    if slot_key not in tg_map:
        raise Http404("File not found")

    file_id = tg_map[slot_key].get('file_id')
    if not file_id:
        raise Http404("File ID missing")

    # Resolve Telegram URL
    url = get_telegram_file_url(file_id)
    if not url:
        raise Http404("Could not resolve Telegram URL")

    # Fetch the file from Telegram
    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            raise Http404("Telegram returned an error")
    except Exception:
        raise Http404("Could not fetch file from Telegram")

    content_type = r.headers.get('Content-Type', 'application/octet-stream')

    # Guess content type from extension for inline viewing
    filename = tg_map[slot_key].get('file_name', 'file')
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    type_map = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'txt': 'text/plain; charset=utf-8',
        'html': 'text/html; charset=utf-8',
        'json': 'application/json',
    }

    if ext in type_map:
        content_type = type_map[ext]

    response = HttpResponse(r.content, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response