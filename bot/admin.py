from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, ServiceProvider, News, Advertisement,
    Fixture, Result, FantasyLeaderboard, Announcement,
    Payment
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'provider_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def provider_count(self, obj):
        return obj.providers.count()
    provider_count.short_description = 'Providers'


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'display_badge', 'plan_type', 'category', 
        'is_approved', 'is_active', 'created_at'
    ]
    list_filter = ['plan_type', 'badge_type', 'is_approved', 'is_active', 'category']
    search_fields = ['name', 'description', 'telegram_handle', 'keywords']
    readonly_fields = ['telegram_user_id', 'created_at', 'updated_at']
    list_editable = ['is_approved', 'is_active']
    
    fieldsets = (
        ('Telegram Info', {
            'fields': ('telegram_user_id',)
        }),
        ('Business Information', {
            'fields': ('name', 'description', 'keywords', 'category')
        }),
        ('Plan & Badge', {
            'fields': ('plan_type', 'badge_type', 'is_verified')
        }),
        ('Contact Information', {
            'fields': ('phone', 'telegram_handle', 'instagram_handle', 'hall_of_residence')
        }),
        ('Catalogue', {
            'fields': ('catalogue',)
        }),
        ('Status', {
            'fields': ('is_approved', 'is_active', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_providers', 'reject_providers', 'verify_providers', 'set_premium']

    def display_badge(self, obj):
        badge = obj.get_display_badge()
        if badge:
            return badge
        return '-'
    display_badge.short_description = 'Badge'

    @admin.action(description='Approve selected providers')
    def approve_providers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} provider(s) approved.')

    @admin.action(description='Reject selected providers')
    def reject_providers(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} provider(s) rejected.')

    @admin.action(description='Set as Verified (badge + approved)')
    def verify_providers(self, request, queryset):
        updated = queryset.update(
            is_verified=True, 
            badge_type='VERIFIED', 
            is_approved=True
        )
        self.message_user(request, f'{updated} provider(s) verified.')

    @admin.action(description='Set as Premium (badge + approved)')
    def set_premium(self, request, queryset):
        updated = queryset.update(
            badge_type='PREMIUM', 
            plan_type='PREMIUM',
            is_approved=True
        )
        self.message_user(request, f'{updated} provider(s) set to Premium.')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'created_at']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['is_published']
    date_hierarchy = 'created_at'


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'ad_type', 'slot_position', 'is_active', 'expires_at']
    list_filter = ['ad_type', 'is_active', 'slot_position']
    list_editable = ['is_active']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'ad_type', 'slot_position')
        }),
        ('Media', {
            'fields': ('media_file', 'caption', 'external_link')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
    )


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'match_date', 'venue', 'competition', 'has_result']
    list_filter = ['competition', 'match_date']
    search_fields = ['home_team', 'away_team', 'venue']
    date_hierarchy = 'match_date'

    def has_result(self, obj):
        return hasattr(obj, 'result')
    has_result.boolean = True
    has_result.short_description = 'Result'


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['fixture', 'home_score', 'away_score', 'created_at']
    search_fields = ['fixture__home_team', 'fixture__away_team']
    autocomplete_fields = ['fixture']


@admin.register(FantasyLeaderboard)
class FantasyLeaderboardAdmin(admin.ModelAdmin):
    list_display = ['rank', 'player_name', 'telegram_handle', 'points', 'last_updated']
    list_display_links = ['player_name']
    list_editable = ['points', 'rank']
    search_fields = ['player_name', 'telegram_handle']
    ordering = ['rank']



@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_pinned', 'created_at']
    list_filter = ['is_pinned', 'created_at']
    list_editable = ['is_pinned']
    search_fields = ['title', 'content']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'provider', 'plan_type', 'display_amount', 'status', 'created_at', 'verified_at']
    list_filter = ['status', 'plan_type', 'created_at']
    search_fields = ['reference', 'provider__name']
    readonly_fields = ['reference', 'provider', 'amount', 'plan_type', 'authorization_url', 
                       'paystack_response', 'created_at', 'verified_at']
    date_hierarchy = 'created_at'

    def display_amount(self, obj):
        return f"₦{obj.amount_naira:,.0f}"
    display_amount.short_description = 'Amount'
