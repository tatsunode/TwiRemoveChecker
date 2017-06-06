from django.contrib import admin
from app.models import Account, Key

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'name', 'screen_name','url', 'followed_you', 'description','created_at', 'unfollow_datetime')
    list_filter = ('followed_you',)


class KeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')

admin.site.register(Account, AccountAdmin)
admin.site.register(Key, KeyAdmin)
