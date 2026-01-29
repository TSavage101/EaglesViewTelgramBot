from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator


class Category(models.Model):
    """
    Dynamic categories created by service providers.
    Categories are created automatically when providers register with new keywords.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    """
    Business or individual offering services on Purple Board.
    """
    PLAN_CHOICES = [
        ('BASIC', 'Basic - ₦1,500'),
        ('VERIFIED', 'Verified - ₦3,000'),
        ('PREMIUM', 'Premium - ₦5,000'),
    ]

    BADGE_CHOICES = [
        ('NONE', 'No Badge'),
        ('VERIFIED', '✅ Verified'),
        ('PREMIUM', '⭐ Premium'),
    ]

    # Telegram info
    telegram_user_id = models.BigIntegerField(unique=True, help_text="Telegram user ID")
    
    # Business info
    name = models.CharField(max_length=200, help_text="Business/Provider name")
    description = models.TextField(max_length=500, help_text="Short description of services")
    keywords = models.JSONField(
        default=list,
        help_text="List of keywords for search (e.g., ['lash', 'makeup', 'beauty'])"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='providers'
    )
    
    # Plan & Badge
    plan_type = models.CharField(max_length=10, choices=PLAN_CHOICES, default='BASIC')
    badge_type = models.CharField(max_length=10, choices=BADGE_CHOICES, default='NONE')
    is_verified = models.BooleanField(default=False, help_text="Has been verified by admin")
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    telegram_handle = models.CharField(max_length=100, blank=True, help_text="@username")
    instagram_handle = models.CharField(max_length=100, blank=True, help_text="@username")
    
    # Premium-only field
    hall_of_residence = models.CharField(
        max_length=100,
        blank=True,
        help_text="Hall of residence (Premium only)"
    )
    
    # Catalogue
    catalogue = models.FileField(
        upload_to='catalogues/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="PDF catalogue/portfolio"
    )
    
    # Status
    is_approved = models.BooleanField(default=False, help_text="Approved by admin to appear in search")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-plan_type', '-created_at']  # Premium first, then by date

    def __str__(self):
        badge = ""
        if self.badge_type == 'VERIFIED':
            badge = " ✅"
        elif self.badge_type == 'PREMIUM':
            badge = " ⭐"
        return f"{self.name}{badge}"

    def get_display_badge(self):
        """Return the badge emoji for display."""
        if self.badge_type == 'PREMIUM':
            return '⭐'
        elif self.badge_type == 'VERIFIED':
            return '✅'
        return ''

    def get_contact_card(self):
        """Return formatted contact information."""
        lines = [f"📋 {self.name}"]
        if self.badge_type != 'NONE':
            lines[0] += f" {self.get_display_badge()}"
        lines.append(f"\n📝 {self.description}")
        
        if self.phone:
            lines.append(f"📞 {self.phone}")
        if self.telegram_handle:
            lines.append(f"💬 {self.telegram_handle}")
        if self.instagram_handle:
            lines.append(f"📸 {self.instagram_handle}")
        
        # Premium-only: hall of residence
        if self.plan_type == 'PREMIUM' and self.hall_of_residence:
            lines.append(f"🏠 {self.hall_of_residence}")
        
        return "\n".join(lines)


class News(models.Model):
    """
    News updates posted by admin.
    """
    NEWS_CATEGORIES = [
        ('GENERAL', 'General'),
        ('CAMPUS', 'Campus'),
        ('TECH', 'Tech'),
        ('SPORTS', 'Sports'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=NEWS_CATEGORIES, default='GENERAL')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "News"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Advertisement(models.Model):
    """
    Advertisements for the Home Page.
    4 slots total: 2 video, 2 picture.
    """
    AD_TYPES = [
        ('VIDEO', 'Video Ad'),
        ('PICTURE', 'Picture Ad'),
    ]

    SLOT_CHOICES = [
        (1, 'Slot 1 - Video'),
        (2, 'Slot 2 - Video'),
        (3, 'Slot 3 - Picture'),
        (4, 'Slot 4 - Picture'),
    ]

    title = models.CharField(max_length=100)
    ad_type = models.CharField(max_length=10, choices=AD_TYPES)
    media_file = models.FileField(upload_to='ads/')
    caption = models.TextField(max_length=500, blank=True)
    external_link = models.URLField(blank=True, help_text="Link to open when ad is clicked")
    slot_position = models.IntegerField(choices=SLOT_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['slot_position']

    def __str__(self):
        return f"{self.title} (Slot {self.slot_position})"


# ============ CHANCELLORS SECTION MODELS ============

class Fixture(models.Model):
    """
    Sports fixtures for Chancellors section.
    """
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=200, blank=True)
    competition = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['match_date']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"


class Result(models.Model):
    """
    Match results linked to fixtures.
    """
    fixture = models.OneToOneField(Fixture, on_delete=models.CASCADE, related_name='result')
    home_score = models.PositiveIntegerField()
    away_score = models.PositiveIntegerField()
    summary = models.TextField(blank=True, help_text="Match summary or highlights")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fixture.home_team} {self.home_score} - {self.away_score} {self.fixture.away_team}"


class FantasyLeaderboard(models.Model):
    """
    Fantasy league standings.
    """
    player_name = models.CharField(max_length=100)
    telegram_handle = models.CharField(max_length=100, blank=True)
    points = models.IntegerField(default=0)
    rank = models.PositiveIntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rank']

    def __str__(self):
        return f"#{self.rank} {self.player_name} - {self.points} pts"


class Announcement(models.Model):
    """
    Important announcements for Chancellors section.
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title
