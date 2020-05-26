import argparse
import os
import re
from pprint import pprint

from dotenv import load_dotenv
from instabot import Bot

bot = Bot()


def main():
    load_dotenv()
    post_url, login = parse_url_and_login()
    true_users = get_true_users(post_url, login)
    pprint(true_users)


def parse_url_and_login():
    parser = argparse.ArgumentParser(
        description='Программа найдет участников, которые выполнили все условия'
    )
    parser.add_argument('post_url', help='Ссылка на пост конкурса')
    parser.add_argument('login', help='Логин аккаунта проводящего конкурс')
    args = parser.parse_args()
    post_url = args.post_url
    login = args.login
    return post_url, login


def get_true_users(post_url, login):
    log_into_instagram()
    post_id = bot.get_media_id_from_link(post_url)
    users_with_true_comments = find_users_with_true_comments(post_id)
    true_users = check_users_for_like_and_follow(users_with_true_comments, post_id, login)
    return true_users


def log_into_instagram():
    insta_login = os.getenv('INSTA_LOGIN')
    insta_password = os.getenv('INSTA_PASSWORD')
    bot.login(username=insta_login, password=insta_password)


def find_users_with_true_comments(post_id):
    comments = fetch_all_comments(post_id)
    users_with_true_comments = set()
    for user_id, username, comment in comments:
        user_friends = get_users_from_comment(comment)
        if is_some_friend_exist(user_friends):
            users_with_true_comments.add((user_id, username))
    return users_with_true_comments


def fetch_all_comments(post_id):
    comments_info = bot.get_media_comments_all(post_id)
    comments = []
    for comment in comments_info:
        comments.append((
            comment['user_id'],
            comment['user']['username'],
            comment['text'],
        ))
    return comments


def get_users_from_comment(comment):
    username_pattern = r'(?:@)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)'
    # This pattern was taken from: https://blog.jstassen.com/2016/03/code-regex-for-instagram-username-and-hashtags/
    users = re.findall(username_pattern, comment)
    return users


def is_some_friend_exist(user_friends):
    for friend in user_friends:
        if is_user_exist(friend):
            return True


def is_user_exist(username):
    user_id = bot.get_user_id_from_username(username)
    if user_id:
        return True


def check_users_for_like_and_follow(users, post_id, login):
    all_likes = bot.get_media_likers(post_id)
    all_likes = [int(id) for id in all_likes]
    all_followers = bot.get_user_followers(login)
    all_followers = [int(id) for id in all_followers]
    true_users = []
    for user_id, username in users:
        if user_id in all_likes and user_id in all_followers:
            true_users.append((user_id, username))
    return true_users


if __name__ == '__main__':
    main()
