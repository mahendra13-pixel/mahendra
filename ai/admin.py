import json
from django.contrib import admin, messages
from django.core.files.storage import default_storage

from filemanager.telegram_storage import upload_to_telegram, delete_telegram_message
from filemanager.utils import sanitize_filename

from .models import (
    DeveloperProfile, AboutSection, Education, Skill,
    WorkExperience, SlideImage, UsefulLink, ContactMethod,
)


# ============================================================
# ✅ Shared helper — push an uploaded file to Telegram (mixin map)
# ============================================================
def _push_to_telegram(request, obj, slot, upload_field, delete_field, label="File"):
    """
    Handles upload / replace / delete for one Telegram slot.
    Uses the model's mixin map (get_telegram_map / set_telegram_file).
    Reads the actual uploaded file from request.FILES (not the DB path),
    so it never crashes on a stale/missing file path in production.
    """
    do_delete = getattr(obj, delete_field)
    existing = obj.get_telegram_map().get(slot)
    uploaded = request.FILES.get(upload_field)

    # Nothing uploaded this save → just clear stale DB field and return
    if not uploaded:
        setattr(obj, upload_field, None)
        setattr(obj, delete_field, False)

        if do_delete and existing:
            if existing.get("message_id"):
                try:
                    delete_telegram_message(existing["message_id"])
                except Exception:
                    pass
            obj.remove_telegram_file(slot)
        return

    # 1) Delete or replace existing
    if existing:
        if existing.get("message_id"):
            try:
                delete_telegram_message(existing["message_id"])
            except Exception:
                pass
        obj.remove_telegram_file(slot)

    # 2) Upload
    if uploaded.size > 20 * 1024 * 1024:
        messages.error(request, f"{label} '{uploaded.name}' exceeds 20 MB.")
    else:
        try:
            info = upload_to_telegram(
                uploaded, filename=sanitize_filename(uploaded.name)
            )
            if info:
                obj.set_telegram_file(slot, info)
                messages.success(request, f"✅ {label} uploaded to Telegram.")
            else:
                messages.warning(request, f"⚠️ {label} upload returned no info.")
        except Exception as e:
            messages.warning(request, f"⚠️ {label} upload failed: {e}")

    # 3) Clear widget fields
    setattr(obj, upload_field, None)
    setattr(obj, delete_field, False)


# ============================================================
# ✅ CV helper — uses the CV-specific map (cv_telegram_files)
# ============================================================
def _push_cv_to_telegram(request, obj):
    del_cv = getattr(obj, "delete_cv", False)
    existing_cv = obj.get_cv_telegram_map().get("cv")
    uploaded = request.FILES.get("upload_cv")

    # Nothing uploaded this save → just clear stale DB field and return
    if not uploaded:
        obj.upload_cv = None
        obj.delete_cv = False

        if del_cv and existing_cv:
            if existing_cv.get("message_id"):
                try:
                    delete_telegram_message(existing_cv["message_id"])
                except Exception:
                    pass
            obj.remove_cv_telegram_file("cv")
        return

    # 1) Delete or replace existing
    if existing_cv:
        if existing_cv.get("message_id"):
            try:
                delete_telegram_message(existing_cv["message_id"])
            except Exception:
                pass
        obj.remove_cv_telegram_file("cv")

    # 2) Upload
    if uploaded.size > 20 * 1024 * 1024:
        messages.error(request, f"CV '{uploaded.name}' exceeds 20 MB.")
    else:
        try:
            info = upload_to_telegram(
                uploaded, filename=sanitize_filename(uploaded.name)
            )
            if info:
                obj.set_cv_telegram_file("cv", info)
                messages.success(request, "✅ CV uploaded to Telegram.")
            else:
                messages.warning(request, "⚠️ CV upload returned no info.")
        except Exception as e:
            messages.warning(request, f"⚠️ CV upload failed: {e}")

    # 3) Clear widget fields
    obj.upload_cv = None
    obj.delete_cv = False


def _cleanup_temp_file(name):
    """Best-effort delete of a temp upload file from disk."""
    if not name:
        return
    try:
        default_storage.delete(name)
    except Exception:
        pass


def _safe_finalize(obj, update_fields):
    """
    Bulletproof DB clear of widget fields — never raises.
    Called from every save_model's finally block.
    """
    try:
        obj.save(update_fields=update_fields)
    except Exception:
        # Never mask the original error; the admin view will still
        # show the real exception if super().save_model failed.
        pass


# ============================================================
# ✅ DeveloperProfile — profile photo + CV
# ============================================================
@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "headline", "has_cv")
    readonly_fields = ("cv_status",)
    fieldsets = (
        (None, {"fields": ("name", "headline", "workplace")}),
        ("Profile photo (Telegram)", {
            "fields": ("upload_photo", "delete_photo"),
        }),
        ("CV (Telegram)", {
            "fields": ("cv_status", "upload_cv", "delete_cv"),
        }),
    )

    def has_add_permission(self, request):
        return not DeveloperProfile.objects.exists()

    @admin.display(boolean=True, description="Has CV")
    def has_cv(self, obj):
        return bool(obj and obj.has_cv)

    @admin.display(description="Current CV")
    def cv_status(self, obj):
        if not obj:
            return "Save the profile first, then upload a CV."
        info = obj.cv_info
        if not info:
            return "No CV uploaded."
        size_kb = (info.get("file_size") or 0) / 1024
        return f"{info.get('file_name', 'cv')} ({size_kb:.1f} KB)"

    def save_model(self, request, obj, form, change):
        tmp_names = []

        try:
            super().save_model(request, obj, form, change)

            # Capture what Django wrote to disk
            if obj.upload_photo:
                tmp_names.append(obj.upload_photo.name)
            if obj.upload_cv:
                tmp_names.append(obj.upload_cv.name)

            _push_to_telegram(
                request, obj,
                slot="photo",
                upload_field="upload_photo",
                delete_field="delete_photo",
                label="Profile photo",
            )
            _push_cv_to_telegram(request, obj)
        finally:
            # Always clear widget fields in DB
            obj.upload_photo = None
            obj.delete_photo = False
            obj.upload_cv = None
            obj.delete_cv = False
            _safe_finalize(obj, [
                "photo_telegram_files", "cv_telegram_files",
                "upload_photo", "delete_photo", "upload_cv", "delete_cv",
            ])
            # Cleanup leaked temp files
            for n in tmp_names:
                _cleanup_temp_file(n)


# ============================================================
# ✅ AboutSection
# ============================================================
@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_editable = ("order", "is_active")
    fieldsets = (
        (None, {"fields": ("title", "content", "order", "is_active")}),
        ("Photo (Telegram)", {"fields": ("upload_photo", "delete_photo")}),
    )

    def save_model(self, request, obj, form, change):
        tmp_names = []
        try:
            super().save_model(request, obj, form, change)
            if obj.upload_photo:
                tmp_names.append(obj.upload_photo.name)

            _push_to_telegram(
                request, obj,
                slot="photo",
                upload_field="upload_photo",
                delete_field="delete_photo",
                label="Photo",
            )
        finally:
            obj.upload_photo = None
            obj.delete_photo = False
            _safe_finalize(obj, [
                "photo_telegram_files", "upload_photo", "delete_photo",
            ])
            for n in tmp_names:
                _cleanup_temp_file(n)


# ============================================================
# ✅ Education
# ============================================================
@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("degree", "institution", "start_year", "end_year", "order")
    list_editable = ("order",)
    fieldsets = (
        (None, {"fields": ("degree", "institution", "start_year", "end_year",
                           "description", "order")}),
        ("Photo (Telegram)", {"fields": ("upload_photo", "delete_photo")}),
    )

    def save_model(self, request, obj, form, change):
        tmp_names = []
        try:
            super().save_model(request, obj, form, change)
            if obj.upload_photo:
                tmp_names.append(obj.upload_photo.name)

            _push_to_telegram(
                request, obj,
                slot="photo",
                upload_field="upload_photo",
                delete_field="delete_photo",
                label="Photo",
            )
        finally:
            obj.upload_photo = None
            obj.delete_photo = False
            _safe_finalize(obj, [
                "photo_telegram_files", "upload_photo", "delete_photo",
            ])
            for n in tmp_names:
                _cleanup_temp_file(n)


# ============================================================
# ✅ Skill
# ============================================================
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "level", "order")
    list_editable = ("category", "level", "order")


# ============================================================
# ✅ WorkExperience
# ============================================================
@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ("role", "organization", "start_date", "end_date", "order")
    list_editable = ("order",)
    fieldsets = (
        (None, {"fields": ("role", "organization", "start_date", "end_date",
                           "description", "order")}),
        ("Photo (Telegram)", {"fields": ("upload_photo", "delete_photo")}),
    )

    def save_model(self, request, obj, form, change):
        tmp_names = []
        try:
            super().save_model(request, obj, form, change)
            if obj.upload_photo:
                tmp_names.append(obj.upload_photo.name)

            _push_to_telegram(
                request, obj,
                slot="photo",
                upload_field="upload_photo",
                delete_field="delete_photo",
                label="Photo",
            )
        finally:
            obj.upload_photo = None
            obj.delete_photo = False
            _safe_finalize(obj, [
                "photo_telegram_files", "upload_photo", "delete_photo",
            ])
            for n in tmp_names:
                _cleanup_temp_file(n)


# ============================================================
# ✅ SlideImage
# ============================================================
@admin.register(SlideImage)
class SlideImageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "order", "is_active")
    list_editable = ("order", "is_active")
    fieldsets = (
        (None, {"fields": ("title", "caption", "order", "is_active")}),
        ("Image (Telegram)", {"fields": ("upload_image", "delete_image")}),
    )

    def save_model(self, request, obj, form, change):
        tmp_names = []
        try:
            super().save_model(request, obj, form, change)
            if obj.upload_image:
                tmp_names.append(obj.upload_image.name)

            _push_to_telegram(
                request, obj,
                slot="image",
                upload_field="upload_image",
                delete_field="delete_image",
                label="Image",
            )
        finally:
            obj.upload_image = None
            obj.delete_image = False
            _safe_finalize(obj, [
                "image_telegram_files", "upload_image", "delete_image",
            ])
            for n in tmp_names:
                _cleanup_temp_file(n)


# ============================================================
# ✅ UsefulLink
# ============================================================
@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "order")
    list_editable = ("order",)
    fieldsets = (
        (None, {"fields": ("title", "description", "url", "order")}),
        ("Image (Telegram)", {"fields": ("upload_image", "delete_image")}),
    )

    def save_model(self, request, obj, form, change):
        tmp_names = []
        try:
            super().save_model(request, obj, form, change)
            if obj.upload_image:
                tmp_names.append(obj.upload_image.name)

            _push_to_telegram(
                request, obj,
                slot="image",
                upload_field="upload_image",
                delete_field="delete_image",
                label="Image",
            )
        finally:
            obj.upload_image = None
            obj.delete_image = False
            _safe_finalize(obj, [
                "image_telegram_files", "upload_image", "delete_image",
            ])
            for n in tmp_names:
                _cleanup_temp_file(n)


# ============================================================
# ✅ ContactMethod
# ============================================================
@admin.register(ContactMethod)
class ContactMethodAdmin(admin.ModelAdmin):
    list_display = ("kind", "value", "label", "order", "is_active")
    list_editable = ("order", "is_active")