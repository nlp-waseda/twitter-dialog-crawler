import argparse
import os
from datetime import datetime

# from dotenv import load_dotenv
from dotenv import dotenv_values
from tqdm import tqdm
import tweepy


def filter_status(status):
    if status.source not in ['Twitter for Android', 'Twitter for iPhone', 'Twitter Web App']:  # by human
        return False
    
    if len(status.entities['hashtags']) > 0:  # has hashtags
        return False

    if len(status.entities['urls']) > 0:  # has urls
        return False

    if 'media' in status.entities:  # has media
        return False

    return True


def filter_dialog(full_texts, user_ids):
    if len(full_texts) < 2:  # not dialog
        return False
    
    if len(set(user_ids)) != 2:  # not bi-party
        return False

    if any(user_ids[i] == user_ids[i+1] for i in range(len(user_ids) - 1)):  # not alternating
        return False
    
    return True


def get_user_ids(api, q):
    user_ids = set()

    # try:
    search_results = api.search(q=q, lang='ja', result_type='recent', count=100, tweet_mode='extended')
    for status in tqdm(search_results, desc='get user ids'):
        if filter_status(status):
            user_ids.add(status.author.id)

    # except tweepy.TweepError as e:
    #     raise

    return user_ids


def get_user_timeline(api, user_ids, text_map, user_map, reply_tree):
    in_reply_to_user_ids = set()

    for user_id in tqdm(user_ids, desc='get user timeline'):
        try:
            user_timeline = api.user_timeline(user_id=user_id, count=200, tweet_mode='extended')
            for status in user_timeline:
                if filter_status(status):
                    text_map[status.id] = ' '.join(status.full_text.split())
                    user_map[status.id] = status.author.id

                    if status.in_reply_to_status_id is not None:
                        in_reply_to_user_ids.add(status.in_reply_to_user_id)
                        reply_tree[status.id] = status.in_reply_to_status_id

        except tweepy.TweepError:
            pass

    return in_reply_to_user_ids


def build_dialogs(text_map, user_map, reply_tree):
    dialogs = []

    status_ids = set(reply_tree.keys()) - set(reply_tree.values())  # is leaf
    for status_id in tqdm(status_ids, desc='build dialogs'):
        full_texts = []
        user_ids = []

        while True:
            if status_id not in text_map.keys():  # continues
                break

            full_texts.append(text_map[status_id])
            user_ids.append(user_map[status_id])

            if status_id not in reply_tree.keys():  # is root
                if filter_dialog(full_texts, user_ids):
                    dialogs.append(reversed(full_texts))
                
                break

            status_id = reply_tree[status_id]

    return dialogs


def write_dialogs(dialogs, output_dir):
    output_tsv = f'{datetime.now():%Y%m%d%H%M%S%f}.tsv'
    with open(os.path.join(output_dir, output_tsv), 'w', encoding='utf-8') as f:
        for dialog in dialogs:
            f.write('\t'.join(dialog) + '\n')

    print(f'{len(dialogs)} dialogs written.')


def main(args):
    # load_dotenv()

    # consumer_key = os.environ['CONSUMER_KEY']
    # consumer_secret = os.environ['CONSUMER_SECRET']
    # access_token = os.environ['ACCESS_TOKEN']
    # access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

    config = dotenv_values(args.dotenv_path)

    consumer_key = config['CONSUMER_KEY']
    consumer_secret = config['CONSUMER_SECRET']
    access_token = config['ACCESS_TOKEN']
    access_token_secret = config['ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    while True:
        try:
            user_ids = get_user_ids(api, q=args.q)

            text_map = {}  # status_id -> full_text
            user_map = {}  # status_id -> user_id

            reply_tree = {}  # status_id -> in_reply_to_status_id

            in_reply_to_user_ids = get_user_timeline(api, user_ids, text_map, user_map, reply_tree)
            get_user_timeline(api, in_reply_to_user_ids - user_ids, text_map, user_map, reply_tree)

            # traverse tree
            dialogs = build_dialogs(text_map, user_map, reply_tree)

            write_dialogs(dialogs, args.output_dir)
        
        except tweepy.TweepError:
            continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir')
    parser.add_argument('--dotenv_path', default='.env')
    parser.add_argument('--q', default='い')
    args = parser.parse_args()

    main(args)
