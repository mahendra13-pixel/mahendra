import re
import json
from django.db import models


# ============================================================
# ✅ Mixin: Telegram map helpers (single map — used for photos)
# ============================================================
class TelegramFileMixin(models.Model):
    """
    Adds get/set/remove_telegram_file + delete() cleanup for the *_telegram_files
    JSON field. Each concrete model declares its own TextField.
    """
    class Meta:
        abstract = True

    TELEGRAM_FIELD = None  # e.g. "photo_telegram_files"

    def get_telegram_map(self):
        raw = getattr(self, self.TELEGRAM_FIELD, None)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_telegram_file(self, slot_key, info):
        data = self.get_telegram_map()
        data[slot_key] = info
        setattr(self, self.TELEGRAM_FIELD, json.dumps(data))

    def remove_telegram_file(self, slot_key):
        data = self.get_telegram_map()
        data.pop(slot_key, None)
        setattr(self, self.TELEGRAM_FIELD, json.dumps(data))

    def delete(self, *args, **kwargs):
        try:
            from filemanager.telegram_storage import delete_telegram_message
            for _sk, info in self.get_telegram_map().items():
                if info and info.get("message_id"):
                    delete_telegram_message(info["message_id"])
        except Exception:
            pass
        super().delete(*args, **kwargs)


# ============================================================
# ✅ DeveloperProfile — profile photo (mixin) + CV (own map)
# ============================================================
class DeveloperProfile(TelegramFileMixin):
    """Single profile card. Only one row is used (the first)."""
    TELEGRAM_FIELD = "photo_telegram_files"

    name = models.CharField(max_length=100)
    headline = models.CharField(
        max_length=200,
        help_text="e.g. Python Developer · Full-Stack · IT Officer Assistant",
    )
    workplace = models.CharField(
        max_length=200, blank=True,
        help_text="e.g. Grande International Hospital, Nepal",
    )

    # Legacy local file — unused, kept for backward compatibility
    photo = models.ImageField(upload_to="developer/profile/", blank=True, null=True)

    # ✅ Telegram storage (two separate JSON maps)
    photo_telegram_files = models.TextField(blank=True, null=True, default='')
    cv_telegram_files = models.TextField(blank=True, null=True, default='')

    # ✅ Admin widget fields (never persisted — cleared in save_model)
    upload_photo = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="Profile photo")
    delete_photo = models.BooleanField(default=False, verbose_name="Delete profile photo")
    upload_cv = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="CV file")
    delete_cv = models.BooleanField(default=False, verbose_name="Delete CV")

    def __str__(self):
        return self.name

    # ---------- CV map helpers (SEPARATE from mixin) ----------
    def get_cv_telegram_map(self):
        if not self.cv_telegram_files:
            return {}
        try:
            return json.loads(self.cv_telegram_files)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_cv_telegram_file(self, slot_key, info):
        data = self.get_cv_telegram_map()
        data[slot_key] = info
        self.cv_telegram_files = json.dumps(data)

    def remove_cv_telegram_file(self, slot_key):
        data = self.get_cv_telegram_map()
        data.pop(slot_key, None)
        self.cv_telegram_files = json.dumps(data)

    # ---------- Template convenience ----------
    @property
    def photo_info(self):
        return self.get_telegram_map().get("photo")

    @property
    def cv_info(self):
        return self.get_cv_telegram_map().get("cv")

    @property
    def has_cv(self):
        return bool(self.cv_info)

    # ---------- Cleanup both maps on delete ----------
    def delete(self, *args, **kwargs):
        try:
            from filemanager.telegram_storage import delete_telegram_message
            for _sk, info in self.get_cv_telegram_map().items():
                if info and info.get("message_id"):
                    delete_telegram_message(info["message_id"])
        except Exception:
            pass
        super().delete(*args, **kwargs)


# ============================================================
# ✅ AboutSection
# ============================================================
class AboutSection(TelegramFileMixin):
    TELEGRAM_FIELD = "photo_telegram_files"

    title = models.CharField(max_length=150, default="About")
    content = models.TextField()
    photo = models.ImageField(upload_to="developer/about/", blank=True, null=True)
    photo_telegram_files = models.TextField(blank=True, null=True, default='')

    upload_photo = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="Photo")
    delete_photo = models.BooleanField(default=False, verbose_name="Delete photo")

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def photo_info(self):
        return self.get_telegram_map().get("photo")


# ============================================================
# ✅ Education
# ============================================================
class Education(TelegramFileMixin):
    TELEGRAM_FIELD = "photo_telegram_files"

    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    start_year = models.CharField(max_length=10, blank=True)
    end_year = models.CharField(max_length=10, blank=True, help_text="Leave blank if ongoing")
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="developer/education/", blank=True, null=True)
    photo_telegram_files = models.TextField(blank=True, null=True, default='')

    upload_photo = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="Photo")
    delete_photo = models.BooleanField(default=False, verbose_name="Delete photo")

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-id"]
        verbose_name_plural = "Education"

    def __str__(self):
        return f"{self.degree} - {self.institution}"

    @property
    def photo_info(self):
        return self.get_telegram_map().get("photo")


# ============================================================
# ✅ Skill (no image)
# ============================================================
class Skill(models.Model):
    name = models.CharField(max_length=80)
    category = models.CharField(max_length=80, blank=True, help_text="e.g. Backend, Frontend, IT Support")
    level = models.PositiveSmallIntegerField(
        blank=True, null=True,
        help_text="Optional, 1-100. Leave blank to show as a plain tag.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "name"]

    def __str__(self):
        return self.name


# ============================================================
# ✅ WorkExperience
# ============================================================
class WorkExperience(TelegramFileMixin):
    TELEGRAM_FIELD = "photo_telegram_files"

    role = models.CharField(max_length=150)
    organization = models.CharField(max_length=200)
    start_date = models.CharField(max_length=30, help_text="e.g. Jan 2026")
    end_date = models.CharField(max_length=30, blank=True, help_text="Leave blank if current")
    description = models.TextField(blank=True, help_text="One point per line")
    photo = models.ImageField(upload_to="developer/experience/", blank=True, null=True)
    photo_telegram_files = models.TextField(blank=True, null=True, default='')

    upload_photo = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="Photo")
    delete_photo = models.BooleanField(default=False, verbose_name="Delete photo")

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-id"]

    def __str__(self):
        return f"{self.role} - {self.organization}"

    @property
    def points(self):
        return [line.strip() for line in self.description.splitlines() if line.strip()]

    @property
    def photo_info(self):
        return self.get_telegram_map().get("photo")


# ============================================================
# ✅ SlideImage
# ============================================================
class SlideImage(TelegramFileMixin):
    TELEGRAM_FIELD = "image_telegram_files"

    title = models.CharField(max_length=150, blank=True)
    caption = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to="developer/slides/", blank=True, null=True)
    image_telegram_files = models.TextField(blank=True, null=True, default='')

    upload_image = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="Image")
    delete_image = models.BooleanField(default=False, verbose_name="Delete image")

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title or f"Slide {self.pk}"

    @property
    def image_info(self):
        return self.get_telegram_map().get("image")


# ============================================================
# ✅ UsefulLink
# ============================================================
class UsefulLink(TelegramFileMixin):
    TELEGRAM_FIELD = "image_telegram_files"

    title = models.CharField(max_length=150)
    description = models.CharField(max_length=300, blank=True)
    url = models.URLField()
    image = models.ImageField(upload_to="developer/links/", blank=True, null=True)
    image_telegram_files = models.TextField(blank=True, null=True, default='')

    upload_image = models.FileField(upload_to="tmp/", blank=True, null=True, verbose_name="Image")
    delete_image = models.BooleanField(default=False, verbose_name="Delete image")

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def image_info(self):
        return self.get_telegram_map().get("image")


# ============================================================
# ✅ ContactMethod (no image)
# ============================================================
class ContactMethod(models.Model):
    EMAIL, PHONE, WHATSAPP, MESSENGER, FACEBOOK, OTHER = (
        "email", "phone", "whatsapp", "messenger", "facebook", "other",
    )
    TYPE_CHOICES = [
        (EMAIL, "Email"),
        (PHONE, "Phone"),
        (WHATSAPP, "WhatsApp"),
        (MESSENGER, "Facebook Messenger"),
        (FACEBOOK, "Facebook Page/Profile"),
        (OTHER, "Other link"),
    ]
    ICONS = {
        EMAIL: "📧", PHONE: "📞", WHATSAPP: "💬",
        MESSENGER: "💭", FACEBOOK: "📘", OTHER: "🔗",
    }

    kind = models.CharField(max_length=20, choices=TYPE_CHOICES)
    label = models.CharField(max_length=80, blank=True, help_text="Optional button text")
    value = models.CharField(
        max_length=250,
        help_text=(
            "Email address / phone number with country code (e.g. 9779742386629) / "
            "Messenger or Facebook username or full URL"
        ),
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value}"

    @property
    def icon(self):
        return self.ICONS.get(self.kind, "🔗")

    @property
    def text(self):
        return self.label or self.get_kind_display()

    @property
    def link(self):
        v = self.value.strip()
        if self.kind == self.EMAIL:
            return f"mailto:{v}"
        if self.kind == self.PHONE:
            return f"tel:{v}"
        if self.kind == self.WHATSAPP:
            digits = re.sub(r"\D", "", v)
            return f"https://wa.me/{digits}"
        if self.kind == self.MESSENGER:
            return v if v.startswith("http") else f"https://m.me/{v}"
        if self.kind == self.FACEBOOK:
            return v if v.startswith("http") else f"https://facebook.com/{v}"
        return v