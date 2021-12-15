import argparse
import os
from datetime import datetime

from dotenv import dotenv_values
from tqdm import tqdm
import tweepy


def filter_status(status):
    """ステータスをフィルタリングする。
    
    :param status: ステータス
    :type status: tweepy.Status
    :return: ステータスが適切ならば`True`、そうでなければ`False`
    :rtype: bool
    """

    # 人手でない
    if status.source not in [
        'Twitter for Android', 'Twitter for iPhone', 'Twitter Web App'
    ]:
        return False
    
    # ハッシュタグを含む
    if len(status.entities['hashtags']) > 0:
        return False

    # URLを含む
    if len(status.entities['urls']) > 0:
        return False

    # 画像などを含む
    if 'media' in status.entities:
        return False

    return True


def filter_dialog(full_texts, user_ids):
    """一連のテキストとユーザIDをフィルタリングする。
    
    :param full_texts: 一連のテキスト
    :type full_texts: list
    :param user_ids: 一連のユーザID
    :type user_ids: list
    :return: 一連のテキストとユーザIDが適切ならば`True`、そうでなければ`False`
    :rtype: bool
    """

    # 発話が2個未満
    if len(full_texts) < 2:
        return False
    
    # 話者が2人でない
    if len(set(user_ids)) != 2:
        return False

    # 発話が交互でない
    if any(user_ids[i] == user_ids[i+1] for i in range(len(user_ids) - 1)):
        return False
    
    return True


def get_user_ids(api, q):
    """検索によって取得したユーザIDの集合を返す。

    :param api: API
    :type api: tweepy.API
    :param q: 検索クエリ
    :type q: str
    :raises tweepy.TweepyError: 検索におけるTweepyのエラー
    :return: 取得したユーザIDの集合
    :rtype: set
    """

    user_ids = set()

    search_results = api.search(
        q=q, lang='ja', result_type='recent', count=100, tweet_mode='extended'
    )

    for status in tqdm(search_results, desc='ユーザIDを取得'):
        # 適切なステータスのユーザIDを追加
        if filter_status(status):
            user_ids.add(status.author.id)

    return user_ids


def get_user_timeline(
    api,
    user_ids, 
    status_id_to_full_text,
    status_id_to_user_id,
    status_id_to_in_reply_to_status_id
):
    """ユーザIDからタイムラインを取得し、リプライがあったユーザIDを返す。

    :param user_ids: タイムラインを取得するユーザIDの集合
    :type user_ids: set
    :param status_id_to_full_text: ステータスIDからテキストへのマッピング
    :type status_id_to_full_text: dict
    :param status_id_to_user_id: ステータスIDからユーザIDへのマッピング
    :type status_id_to_user_id: dict
    :param status_id_to_in_reply_to_status_id: リプライの木
    :type status_id_to_in_reply_to_status_id: dict
    :return: リプライがあったユーザIDの集合
    :rtype: set
    """

    in_reply_to_user_ids = set()

    for user_id in tqdm(user_ids, desc='タイムラインを取得'):
        try:
            user_timeline = api.user_timeline(
                user_id=user_id, count=200, tweet_mode='extended'
            )

            for status in user_timeline:
                # 適切なステータスを格納
                if filter_status(status):
                    status_id_to_full_text[status.id] \
                            = ' '.join(status.full_text.split())
                    status_id_to_user_id[status.id] = status.author.id

                    # リプライならば宛先も格納
                    if status.in_reply_to_status_id is not None:
                        in_reply_to_user_ids.add(status.in_reply_to_user_id)
                        status_id_to_in_reply_to_status_id[status.id] \
                                = status.in_reply_to_status_id

        except tweepy.TweepError:
            pass

    return in_reply_to_user_ids


def build_dialogs(
    status_id_to_full_text,
    status_id_to_user_id,
    status_id_to_in_reply_to_status_id
):
    """リプライの木を走査し、構築した対話を返す。

    :param status_id_to_full_text: ステータスIDからテキストへのマッピング
    :type status_id_to_full_text: dict
    :param status_id_to_user_id: ステータスIDからユーザIDへのマッピング
    :type status_id_to_user_id: dict
    :param status_id_to_in_reply_to_status_id: リプライの木
    :type status_id_to_in_reply_to_status_id: dict
    :return: 構築した対話の集合
    :rtype: set
    """

    dialogs = set()

    # 葉
    status_ids = set(status_id_to_in_reply_to_status_id.keys()) \
            - set(status_id_to_in_reply_to_status_id.values())

    for status_id in tqdm(status_ids, desc='対話を構築'):
        full_texts = []
        user_ids = []

        while True:
            # 根が無い
            if status_id not in status_id_to_full_text.keys():
                break

            full_texts.append(status_id_to_full_text[status_id])
            user_ids.append(status_id_to_user_id[status_id])

            # 根
            if status_id not in status_id_to_in_reply_to_status_id.keys():
                # 対話として適切なテキストを追加
                if filter_dialog(full_texts, user_ids):
                    dialogs.add(tuple(reversed(full_texts)))
                
                break

            # ステータスIDを更新
            status_id = status_id_to_in_reply_to_status_id[status_id]

    return dialogs


def write_dialogs(dialogs, output_dir):
    """対話をファイルに書き込む。
    
    :param dialogs: 書き込む対話
    :type dialogs: list
    :param output_dir: 出力ディレクトリ
    :type output_dir: str
    """

    now = datetime.now()
    output_tsv = f'{now:%Y%m%d%H%M%S%f}.tsv'

    with open(os.path.join(output_dir, output_tsv), 'w', encoding='utf-8') as f:
        for dialog in dialogs:
            f.write('\t'.join(dialog) + '\n')

    print(f'{len(dialogs)}個の対話を{output_tsv}に書き込み')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', help='出力ディレクトリ')
    parser.add_argument('--dotenv_path', default='.env', help='.envのパス')
    parser.add_argument('--q', default='い', help='検索クエリ')
    args = parser.parse_args()

    # キーとトークン
    config = dotenv_values(args.dotenv_path)

    consumer_key = config['CONSUMER_KEY']
    consumer_secret = config['CONSUMER_SECRET']
    access_token = config['ACCESS_TOKEN']
    access_token_secret = config['ACCESS_TOKEN_SECRET']

    # 認証
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(
        auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True
    )

    # 収集
    while True:
        try:
            user_ids = get_user_ids(api, q=args.q)

            status_id_to_full_text = {}
            status_id_to_user_id = {}

            status_id_to_in_reply_to_status_id = {}

            # 適当なユーザIDのタイムラインを取得
            in_reply_to_user_ids = get_user_timeline(
                api,
                user_ids,
                status_id_to_full_text,
                status_id_to_user_id,
                status_id_to_in_reply_to_status_id
            )

            # 宛先にあったユーザIDのタイムラインを取得
            get_user_timeline(
                api,
                in_reply_to_user_ids - user_ids,
                status_id_to_full_text,
                status_id_to_user_id,
                status_id_to_in_reply_to_status_id
            )

            dialogs = build_dialogs(
                status_id_to_full_text,
                status_id_to_user_id,
                status_id_to_in_reply_to_status_id
            )

            write_dialogs(dialogs, args.output_dir)
        
        except tweepy.TweepError:
            continue


if __name__ == '__main__':
    main()
