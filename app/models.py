# -*- coding: utf-8
from django.db import models

class Account(models.Model):

    user_id = models.IntegerField("UserId", primary_key=True)

    followed_you = models.BooleanField("フォロワー", default=True)
    follow_datetime = models.DateTimeField('フォロー日時', blank=True, null=True)
    unfollow_datetime = models.DateTimeField('リムーブ日時', blank=True, null=True)
    profile_updated_datetime = models.DateTimeField('最終プロフィール更新日時', blank=True, null=True)

    screen_name = models.CharField("ScreenName", max_length=255, default="", blank=True, null=True)
    name = models.CharField('Name', max_length=255, default="", blank=True, null=True)
    description = models.TextField("プロフィール", default = "", blank=True, null=True)
    followers_count = models.IntegerField("フォロワー数", default=0)
    friends_count = models.IntegerField("フォロー数", default=0)
    location = models.CharField('Location', max_length=255, blank=True, null=True)
    created_at = models.CharField('created_at', max_length=255, blank=True, null=True)

    deleted = models.BooleanField("Deleted", default=False)

    def __str__(self):
        return str(self.screen_name)

    def url(self):
        return "https://twitter.com/" + str(self.screen_name)

class Key(models.Model):
    
    key = models.CharField('KeyName', max_length=255, default="")
    value = models.CharField('KeyValue', max_length=1023, default="")

    def __str__(self):
        return self.key + ":" + self.value