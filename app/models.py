# -*- coding: utf-8
from django.db import models

class Account(models.Model):
    
    followed_you = models.BooleanField("フォロワー", default=True)
    follow_datetime = models.DateTimeField('フォロー日時')
    unfollow_datetime = models.DateTimeField('リムーブ日時', blank=True, null=True)

    account_id = models.CharField("ユーザーID", max_length=255, default="")
    screen_name = models.CharField("ユーザー名", max_length=255, default="")
    description = models.TextField("プロフィール", default = "")
    name = models.CharField('名前', max_length=255, default="")
    created_at = models.CharField('created_at', max_length=255, default="")

    def __str__(self):
        return str(self.screen_name)

    def url(self):
        return "https://twitter.com/" + str(self.screen_name)

class Key(models.Model):
    
    key = models.CharField('KeyName', max_length=255, default="")
    value = models.CharField('KeyValue', max_length=1023, default="")

    def __str__(self):
        return self.key + ":" + self.value