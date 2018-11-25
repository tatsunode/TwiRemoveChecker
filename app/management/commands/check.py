# -*- coding: utf-8 -*-
import os, datetime, time, sys
from pytz import timezone
from django.core.management.base import BaseCommand
from app.models import Account, Key
from requests_oauthlib import OAuth1Session

class RateLimitError(Exception):
    """ """

class AccountNotFoundError(Exception):
    """ """

def send_dm(api, my_account, account, is_new_user):

    message = ""
    if is_new_user:
        message = "[new user] " + str(account.screen_name) + " : " + str(account.name) + " : " + str(account.account_id)
    else:
        message = "[remove user] " + str(account.screen_name) + " : " + str(account.name) + " : " + str(account.account_id)
    message += "\n" + "https://twitter.com/intent/user?user_id=" + str(account.account_id)
    api.send_direct_message(user_id=my_account.id, text=message)


class Command(BaseCommand):

    def handle(self, *args, **options):

        self.twitter_session = None
        self.api_limit_id = 15 
        self.api_limit_user = 900

        CK, CS, AT, ATS = self.get_keys()
        self.make_twitter_session(CK, CS, AT, ATS)

        # get current(old) user id list from db & new user id list from api
        old_id_list = self.get_old_id_list()
        # new_id_list = self.get_follower_id_list()
        new_id_list = [1000, 3000, 4000]

        print("OLD IDs:", old_id_list)
        print("NEW IDs:", new_id_list)

        # find removed user & new user
        removed_id_list = list(set(old_id_list) - set(new_id_list))
        new_id_list = list(set(new_id_list) - set(old_id_list))

        self.handle_removed_accounts(removed_id_list)
        self.handle_new_accounts(new_id_list)

        self.send_direct_message()

        self.update_user_profiles()

        return

    def get_keys(self):
        CK = str(Key.objects.get(key='consumer_key').value)
        CS = str(Key.objects.get(key='consumer_secret').value)
        AT = str(Key.objects.get(key='access_token').value)
        ATS = str(Key.objects.get(key='access_token_secret').value)
        return CK, CS, AT, ATS

    def make_twitter_session(self, CK, CS, AT, ATS):
        oauth_session = OAuth1Session(CK, CS, AT, ATS)
        self.twitter_session = oauth_session

    def get_old_id_list(self):
        following_accounts = Account.objects.filter(followed_you=True)
        old_id_list = [ int(account.user_id) for account in following_accounts ]
        return old_id_list

    def get_follower_id_list(self):
        endpoint = "https://api.twitter.com/1.1/followers/ids.json"
        params = {}
        res = self.twitter_session.get(endpoint, params=params)

        # ToDo: Cursor対応, 5000超えたら
        if res.status_code == 200:
            response_json = json.loads(res.text)
            self.id_list = response_json["ids"]
            self.limit = int(res.headers["x-rate-limit-remaining"])
        elif res.status_code == 429:
            raise RateLimitError
        else:
            raise ValueError("API failed: status code: " + str(res.statsu_code))

    def get_user_profile(self, user_id):
        endpoint = "https://api.twitter.com/1.1/users/show.json"
        params = {
            "user_id": user_id
        }
        res = twitter.get(endpoint, params=params)

        if res.status_code == 200:
            response = json.loads(res.text)
            self.api_limit_user = int(res.headers["x-rate-limit-remaining"])
            return response
        elif res.status_code == 429:
            raise RateLimitError
        elif res.status_code == 404:
            raise AccountNotFoundError
        else:
            raise ValueError("API failed: status code: " + str(res.statsu_code))

    def handle_removed_accounts(self, removed_id_list):
        print("REMOVED:", removed_id_list)

        for removed_user_id in removed_id_list:
            removed_account = Account.objects.get(user_id=removed_user_id)
            removed_account.followed_you = False
            removed_account.unfollow_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
            removed_account.save()

    def handle_new_accounts(self, new_id_list):
        print("NEW:", new_id_list)

        for new_user_id in new_id_list:
            new_account, is_created = Account.objects.get_or_create(user_id=new_user_id)
            new_account.followed_you = True
            new_account.follow_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
            new_account.save()

            try:
                self.update_user_profile(new_account)
            except RateLimitError:
                continue
            except AccountNotFoundError:
                # ToDo: update account info
                continue

    def update_user_profile(self, account):

        profile = self.get_user_profile(account.user_id)
        account.profile_updated_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
        account.screen_name = profile.get("screen_name", "")
        account.name = profile.get("name", "")
        account.description = profile.get("description", "")
        account.followers_count = profile.get("followers_count", 0)
        account.friends_count = profile.get("friends_count", 0)
        account.location = profile.get("location", "")
        account.created_at = profile.get("created_at", "")

    def update_user_profiles(self):
        pass

    def send_direct_message(self):
        pass