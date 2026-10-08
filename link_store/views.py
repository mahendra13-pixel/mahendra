from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import LinkCard
import os


MAX_LINKS = 9
FILE_SUFFIXES = ['', '_b', '_c', '_d']   # 4 files per slot


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin)
def link_store_view(request):

    # ---------- DELETE ----------
    if request.method == "POST" and "delete_id" in request.POST:
        card = get_object_or_404(LinkCard, pk=request.POST["delete_id"])
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
                    setattr(card, f"link_name_{i}",
                            request.POST.get(f"link_name_{i}", "").strip() or None)
                    setattr(card, f"link_desc_{i}",
                            request.POST.get(f"link_desc_{i}", "").strip() or None)
                    setattr(card, f"link_url_{i}",
                            request.POST.get(f"link_url_{i}", "").strip() or None)

                    # Loop over 4 file suffixes for this slot
                    for suffix in FILE_SUFFIXES:
                        field_name = f"link_file_{i}{suffix}"
                        clear_flag = request.POST.get(f"clear_file_{i}{suffix}") == "on"
                        new_file = request.FILES.get(field_name)

                        if clear_flag:
                            old = getattr(card, field_name, None)
                            if old:
                                try:
                                    if os.path.isfile(old.path):
                                        os.remove(old.path)
                                except Exception:
                                    pass
                            setattr(card, field_name, None)

                        if new_file:
                            old = getattr(card, field_name, None)
                            if old:
                                try:
                                    if os.path.isfile(old.path):
                                        os.remove(old.path)
                                except Exception:
                                    pass
                            setattr(card, field_name, new_file)

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
        for i in range(1, MAX_LINKS + 1):
            files = []
            for suffix in FILE_SUFFIXES:
                files.append({
                    "suffix": suffix,
                    "file": getattr(editing_card, f"link_file_{i}{suffix}", None),
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

    field_name = f"link_file_{slot}{suffix}"
    f = getattr(card, field_name, None)

    if not f:
        return JsonResponse({"status": "error", "message": "No file found"}, status=404)

    try:
        if os.path.isfile(f.path):
            os.remove(f.path)
    except Exception:
        pass

    setattr(card, field_name, None)
    card.save()

    return JsonResponse({"status": "success", "message": "File deleted."})