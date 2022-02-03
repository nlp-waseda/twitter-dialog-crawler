import argparse
import os
from datetime import datetime
from typing import List, Optional, Set, Tuple

import tweepy
from dotenv import dotenv_values
from tqdm import tqdm


def filter_status(status: tweepy.Status) -> bool:
    # not manual
    if status.source not in [
        'Twitter for Android',
        'Twitter for iPhone',
        'Twitter Web App'
    ]:
        return False

    # has hashtags
    if len(status.entities['hashtags']) > 0:
        return False

    # has URLs
    if len(status.entities['urls']) > 0:
        return False

    # has images
    if 'media' in status.entities:
        return False

    return True


def filter_dialog(full_texts: List[str], user_ids: List[str]) -> bool:
    # not dialog
    if len(full_texts) < 2:
        return False
    
    # not bi-party
    if len(set(user_ids)) != 2:
        return False

    # not in turns
    if any(user_ids[i] == user_ids[i+1] for i in range(len(user_ids) - 1)):
        return False
    
    return True


class Crawler:
    def __init__(self, dotenv_path: str) -> None:
        config = dotenv_values(dotenv_path)

        consumer_key = config['CONSUMER_KEY']
        consumer_secret = config['CONSUMER_SECRET']
        access_token = config['ACCESS_TOKEN']
        access_token_secret = config['ACCESS_TOKEN_SECRET']

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        self.api = tweepy.API(
            auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )

        self._status_id_to_full_text = {}
        self._status_id_to_user_id = {}

        self._status_id_to_in_reply_to_status_id = {}

        self._dialogs = set()
    
    def _get_user_ids(self, q: str) -> Set[str]:
        user_ids = set()

        try:
            search_results = self.api.search(
                q=q,
                lang='ja',
                result_type='recent',
                count=10,
                tweet_mode='extended'
            )

            for status in tqdm(search_results, desc='Get user IDs'):
                if filter_status(status):
                    user_ids.add(status.author.id)
        
        except tweepy.TweepError:
            pass

        return user_ids

    def _get_user_timeline(self, user_ids: Set[str]) -> Set[str]:
        in_reply_to_user_ids = set()

        for user_id in tqdm(user_ids, desc='Get user timelines'):
            try:
                user_timeline = self.api.user_timeline(
                    user_id=user_id,
                    count=20,
                    tweet_mode='extended'
                )

                for status in user_timeline:
                    if filter_status(status):
                        self._status_id_to_full_text[status.id] \
                                = ' '.join(status.full_text.split())
                        self._status_id_to_user_id[status.id] = status.author.id

                        if status.in_reply_to_status_id is not None:
                            in_reply_to_user_ids.add(status.in_reply_to_user_id)

                            self._status_id_to_in_reply_to_status_id[status.id] \
                                    = status.in_reply_to_status_id

            except tweepy.TweepError:
                pass

        return in_reply_to_user_ids
    
    def _make_dialogs(self) -> Set[Tuple[str]]:
        dialogs = set()

        # leaves
        status_ids = set(self._status_id_to_in_reply_to_status_id.keys()) \
                - set(self._status_id_to_in_reply_to_status_id.values())

        for status_id in tqdm(status_ids, desc='Build dialogs'):
            full_texts = []
            user_ids = []

            while True:
                # no root
                if status_id not in self._status_id_to_full_text.keys():
                    break

                full_texts.append(self._status_id_to_full_text[status_id])
                user_ids.append(self._status_id_to_user_id[status_id])

                # root
                if status_id not in self._status_id_to_in_reply_to_status_id.keys():
                    if filter_dialog(full_texts, user_ids):
                        dialogs.add(tuple(reversed(full_texts)))

                    break

                # parent
                status_id = self._status_id_to_in_reply_to_status_id[status_id]

        return dialogs
    
    def crawl(self, q: Optional[str] = 'あ') -> None:
        # init
        self._status_id_to_full_text = {}
        self._status_id_to_user_id = {}

        self._status_id_to_in_reply_to_status_id = {}

        self._dialogs = set()

        # get texts
        user_ids = self._get_user_ids(q=q)

        in_reply_to_user_ids = self._get_user_timeline(user_ids)
        _ = self._get_user_timeline(in_reply_to_user_ids - user_ids)

        # build dialogs
        self._dialogs = self._make_dialogs()

    def save(self, output_path: str) -> None:
        with open(output_path, 'w', encoding='utf-8') as f:
            for dialog in self._dialogs:
                f.write('\t'.join(dialog) + '\n')

        print(f'Save {len(self._dialogs)} dialogs to {output_path}.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', help='output directory')
    parser.add_argument('--dotenv_path', default='.env', help='path to .env')
    parser.add_argument('--q', default='あ', help='search query for crawling')
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    crawler = Crawler(args.dotenv_path)

    while True:
        crawler.crawl(q=args.q)

        output_path = os.path.join(
            args.output_dir,
            f'{datetime.now():%Y%m%d%H%M%S%f}.tsv'
        )
        crawler.save(output_path)


if __name__== '__main__':
    main()
