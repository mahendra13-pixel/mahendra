import json
from django.contrib import admin, messages

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
    """
    new_file = getattr(obj, upload_field)
    do_delete = getattr(obj, delete_field)
    existing = obj.get_telegram_map().get(slot)

    # 1) Delete or replace
    if (do_delete or new_file) and existing:
        if existing.get("message_id"):
            try:
                delete_telegram_message(existing["message_id"])
            except Exception:
                pass
        obj.remove_telegram_file(slot)

    # 2) Upload
    if new_file:
        if new_file.size > 20 * 1024 * 1024:
            messages.error(request, f"{label} '{new_file.name}' exceeds 20 MB.")
        else:
            try:
                info = upload_to_telegram(
                    new_file, filename=sanitize_filename(new_file.name)
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
    cv_file = getattr(obj, "upload_cv", None)
    del_cv = getattr(obj, "delete_cv", False)
    existing_cv = obj.get_cv_telegram_map().get("cv")

    # 1) Delete or replace
    if (del_cv or cv_file) and existing_cv:
        if existing_cv.get("message_id"):
            try:
                delete_telegram_message(existing_cv["message_id"])
            except Exception:
                pass
        obj.remove_cv_telegram_file("cv")

    # 2) Upload
    if cv_file:
        if cv_file.size > 20 * 1024 * 1024:
            messages.error(request, f"CV '{cv_file.name}' exceeds 20 MB.")
        else:
            try:
                info = upload_to_telegram(
                    cv_file, filename=sanitize_filename(cv_file.name)
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
        # 1) Save base object
        super().save_model(request, obj, form, change)

        # 2) Profile photo (mixin map)
        _push_to_telegram(
            request, obj,
            slot="photo",
            upload_field="upload_photo",
            delete_field="delete_photo",
            label="Profile photo",
        )

        # 3) CV (its OWN map)
        _push_cv_to_telegram(request, obj)

        # 4) Persist both maps
        obj.save(update_fields=["photo_telegram_files", "cv_telegram_files"])


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
        super().save_model(request, obj, form, change)
        _push_to_telegram(
            request, obj,
            slot="photo",
            upload_field="upload_photo",
            delete_field="delete_photo",
            label="Photo",
        )
        obj.save(update_fields=["photo_telegram_files"])


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
        super().save_model(request, obj, form, change)
        _push_to_telegram(
            request, obj,
            slot="photo",
            upload_field="upload_photo",
            delete_field="delete_photo",
            label="Photo",
        )
        obj.save(update_fields=["photo_telegram_files"])


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
        super().save_model(request, obj, form, change)
        _push_to_telegram(
            request, obj,
            slot="photo",
            upload_field="upload_photo",
            delete_field="delete_photo",
            label="Photo",
        )
        obj.save(update_fields=["photo_telegram_files"])


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
        super().save_model(request, obj, form, change)
        _push_to_telegram(
            request, obj,
            slot="image",
            upload_field="upload_image",
            delete_field="delete_image",
            label="Image",
        )
        obj.save(update_fields=["image_telegram_files"])


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
        super().save_model(request, obj, form, change)
        _push_to_telegram(
            request, obj,
            slot="image",
            upload_field="upload_image",
            delete_field="delete_image",
            label="Image",
        )
        obj.save(update_fields=["image_telegram_files"])


# ============================================================
# ✅ ContactMethod
# ============================================================
@admin.register(ContactMethod)
class ContactMethodAdmin(admin.ModelAdmin):
    list_display = ("kind", "value", "label", "order", "is_active")
    list_editable = ("order", "is_active")