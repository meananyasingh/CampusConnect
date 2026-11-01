from django.contrib import admin

from .models import TalentPool, TalentPoolMember


class TalentPoolMemberInline(admin.TabularInline):
    model = TalentPoolMember
    extra = 0
    readonly_fields = ("added_by", "created_at", "updated_at")


@admin.register(TalentPool)
class TalentPoolAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "created_by", "created_at")
    list_filter = ("company",)
    search_fields = ("name", "company__name")
    inlines = (TalentPoolMemberInline,)

