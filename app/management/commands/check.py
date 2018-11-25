# -*- coding: utf-8 -*-
import os, datetime, time, sys, json
from pytz import timezone
from django.core.management.base import BaseCommand
from app.models import Account, Key
from requests_oauthlib import OAuth1Session


class RateLimitError(Exception):
    """ """


class AccountNotFoundError(Exception):
    """ """


class Command(BaseCommand):

    def handle(self, *args, **options):

        self.twitter_session = None
        self.api_limit_id = 15 
        self.api_limit_user = 900

        # make sesison
        CK, CS, AT, ATS = self.load_keys()
        self.make_twitter_session(CK, CS, AT, ATS)

        self.user_id = self.get_user_id()

        # get current(old) user id list from db & new user id list from api
        old_id_list = self.get_old_id_list()
        # new_id_list = self.get_follower_id_list()
        new_id_list = [72326623, 3321361, 2827937894]

        print("OLD IDs:", old_id_list)
        print("NEW IDs:", new_id_list)

        # find removed user & new user
        removed_id_list = list(set(old_id_list) - set(new_id_list))
        new_id_list = list(set(new_id_list) - set(old_id_list))

        self.handle_removed_accounts(removed_id_list)
        self.handle_new_accounts(new_id_list)

        self.update_user_profile_until_rate_limit()

        return

    def load_keys(self):
        CK = str(Key.objects.get(key='consumer_key').value)
        CS = str(Key.objects.get(key='consumer_secret').value)
        AT = str(Key.objects.get(key='access_token').value)
        ATS = str(Key.objects.get(key='access_token_secret').value)
        return CK, CS, AT, ATS

    def make_twitter_session(self, CK, CS, AT, ATS):
        oauth_session = OAuth1Session(CK, CS, AT, ATS)
        self.twitter_session = oauth_session
    
    def get_user_id(self):
        endpoint = "https://api.twitter.com/1.1/account/verify_credentials.json"
        res = self.twitter_session.get(endpoint)

        if res.status_code == 200:
            response = json.loads(res.text)
            print(response)
            return response["id"]
        else:
            raise ValueError("API failed: status code: " + str(res.statsu_code))

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
            id_list = response_json["ids"]
            self.api_limit_id = int(res.headers["x-rate-limit-remaining"])
            return id_list
        elif res.status_code == 429:
            raise RateLimitError
        else:
            raise ValueError("API failed: status code: " + str(res.statsu_code))

    def get_user_profile(self, user_id):
        endpoint = "https://api.twitter.com/1.1/users/show.json"
        params = {
            "user_id": user_id
        }
        res = self.twitter_session.get(endpoint, params=params)

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

            message = "REMOVED: {} ({}) \nhttps://twitter.com/{}".format(
                removed_account.name,
                removed_account.screen_name,
                removed_account.screen_name
            )
            self.post_direct_message(message)

    def handle_new_accounts(self, new_id_list):
        print("NEW:", new_id_list)

        for new_user_id in new_id_list:
            new_account, is_created = Account.objects.get_or_create(user_id=new_user_id)
            new_account.followed_you = True
            new_account.follow_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
            new_account.save()

            try:
                self.update_user_profile(new_account)
                message = "NEW FOLLOWER: {} ({}) https://twitter.com/{}".format(
                    new_account.name,
                    new_account.screen_name,
                    new_account.screen_name
                )
                self.post_direct_message(message)

            except RateLimitError:
                continue

    def update_user_profile(self, account):

        try:
            profile = self.get_user_profile(account.user_id)
            account.profile_updated_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
            account.screen_name = profile.get("screen_name", "")
            account.name = profile.get("name", "")
            account.description = profile.get("description", "")
            account.followers_count = profile.get("followers_count", 0)
            account.friends_count = profile.get("friends_count", 0)
            account.location = profile.get("location", "")
            account.created_at = profile.get("created_at", "")
            account.save()

        except AccountNotFoundError:
            account.profile_updated_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
            account.deleted = True
            account.followed_you = False
            account.save()

    def update_user_profile_until_rate_limit(self):

        accounts = Account.objects.filter(deleted=False).order_by("-profile_updated_datetime")
        for account in accounts:
            try:
                self.update_user_profile(account)
            except RateLimitError:
                break

    def post_direct_message(self, message):
        endpoint = "https://api.twitter.com/1.1/direct_messages/events/new.json"
        data = {
            "event": {
                "type": "message_create",
                "message_create": {
                    "target": {
                        "recipient_id": self.user_id,
                    },
                    "message_data": {
                        "text": message
                    }
                }
            }
        }
        headers = {
            "content-type": "application/json"
        }
        res = self.twitter_session.post(endpoint, json=data, headers=headers)

        if res.status_code == 200:
            pass
        elif res.status_code == 429:
            raise RateLimitError
        else:
            raise ValueError("API failed: status code: " + str(res.status_code))