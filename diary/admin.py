from .models import DiaryEntry, Category, Region, SalesStatus, AttributeType, BaseAttribute, Attribute, AttributeValue, DropdownAttribute, User, Row
from django.contrib import admin

@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'region', 'subregion', 'address', 'manager', 'phone', 'email',
        'ta_date', 'meeting_date', 'fu_date', 'status', 'possibility', 'amount', 'created_at'
    ]
    search_fields = ['name', 'manager', 'subregion', 'address']
    list_filter = ['category', 'region', 'status', 'possibility']
    ordering = ['-created_at']

admin.site.register(Category)
admin.site.register(Region)

# Register additional models
admin.site.register(AttributeType)
admin.site.register(BaseAttribute)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(DropdownAttribute)
admin.site.register(User)
admin.site.register(Row)