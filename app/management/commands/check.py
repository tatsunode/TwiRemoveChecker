# -*- coding: utf-8 -*-
import tweepy, os, datetime, time, sys
from pytz import timezone
from django.core.management.base import BaseCommand
from app.models import Account, Key

def get_account_model(account_id):

    try:
        account = Account.objects.get(account_id=account_id)
        return account
    
    except Account.DoesNotExist:
        return None


def is_following_me(account_id):
    
    account = get_account_model(account_id) 
    if account is None:
        return False

    elif not account.followed_you: 
        return False

    elif account.followed_you:
        return True


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
        
        access_keys = self.get_keys()
        
        if len(access_keys) != 4:
            print("No Access Keys", file=sys.stderr)
            return
        print(access_keys)

        consumer_key = str(access_keys[0])
        consumer_secret = str(access_keys[1])
        access_token = str(access_keys[2])
        access_token_secret = str(access_keys[3])

        print(consumer_key, consumer_secret, access_token, access_token_secret)
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        my_account = api.me()

        try:
            follower_id_list = api.followers_ids()
        except tweepy.error.TweepError:
            print("tweepy: id list fetch error")
            return

        # find new account
        for follower_id in follower_id_list:
            print(follower_id)

            if is_following_me(follower_id):
                continue

            try:
                follower = api.get_user(follower_id)
            except tweepy.error.TweepError:
                print("tweepy: user fetch error")
                return

            screen_name = follower.screen_name
            name = follower.name
            description = follower.description
            created_at = follower.created_at

            print("new follower", follower_id, name, screen_name, description)

            account = get_account_model(follower_id)
            if account is None:
                # new follower
                follow_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
                account = Account(
                    followed_you=True,
                    follow_datetime=follow_datetime,
                    screen_name=screen_name,
                    account_id=follower_id,
                    name = name,
                    description=description,
                    created_at=created_at
                )
                account.save()

            else:
                # old follower
                account.followed_you = True
                account.screen_name = screen_name
                account.name = name
                account.description = description
                account.save()

            send_dm(api, my_account, account, is_new_user=True)

        # find remover
        for account in list(Account.objects.filter(followed_you=True)):
            print(account.account_id)
            if int(account.account_id) in follower_id_list:
                account.followed_you = True
                account.save()
                continue

            # removed follower
            account.unfollow_datetime = datetime.datetime.now(timezone('Asia/Tokyo'))
            account.followed_you = False
            account.save()

            send_dm(api, my_account, account, is_new_user=False)

            print("removed follower", account.account_id, account.name, account.screen_name, account.description)


    def get_keys(self):

        try:
            consumer_key = Key.objects.get(key='consumer_key').value
            consumer_secret = Key.objects.get(key='consumer_secret').value
            access_token = Key.objects.get(key='access_token').value
            access_token_secret = Key.objects.get(key='access_token_secret').value

            return [consumer_key, consumer_secret, access_token, access_token_secret]
        
        except Key.DoesNotExist:
            return []