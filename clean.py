import argparse
import csv
import glob
import html
import os
import re
from collections import defaultdict

from tqdm import tqdm


def read_dialogs(data_dir):
    """対話を読み込む。

    :param data_dir: 入力ディレクトリ
    :type data_dir: str
    :return: 読み込んだ対話の集合
    :rtype: set
    """

    dialogs = set()

    for data_tsv in glob.glob(f'{data_dir}/*.tsv'):
        with open(data_tsv, encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                dialogs.add(tuple(row))

    return dialogs


def clean_dialogs(dialogs, allow_ascii, remove_non_ja):
    """対話をクリーニングする。
    
    :param dialogs: 対話の集合
    :type dialogs: set
    :param allow_ascii: ASCIIを日本語として許容するか
    :type allow_ascii: bool
    :param remove_non_ja: 日本語でない文字を削除するか
    :type remove_non_ja: bool
    :return: クリーニングした対話の集合
    :rtype: set
    """

    clean_dialogs = set()

    for texts in tqdm(dialogs):
        for text in texts:
            clean_texts = []

            for text in texts:
                # HTMLのエスケープを除去
                text = html.unescape(text)

                # スクリーンネームを除去
                text = re.sub(r'@[A-Za-z0-9_]{1,15}', '', text)
                text = ' '.join(text.split())

                if allow_ascii:
                    if remove_non_ja:
                        # ASCIIでも日本語でもない文字を削除
                        text = re.sub(r'[^\u0000-\u007f\u3000-\u30ff\u4e00-\u9fff]', '', text)

                    else:
                        # 日本語の文字を含まない
                        if not re.search(r'[\u3000-\u30ff\u4e00-\u9fff]', text):
                            break

                        # ASCIIでも日本語でもない文字を含む
                        if re.search(r'[^\u0000-\u007f\u3000-\u30ff\u4e00-\u9fff]', text):
                            break

                else:
                    if remove_non_ja:
                        # 日本語でない文字を削除
                        text = re.sub(r'[^\u3000-\u30ff\u4e00-\u9fff]', '', text)

                    else:
                        # 日本語でない文字を含む
                        if re.search(r'[^\u3000-\u30ff\u4e00-\u9fff]', text):
                            break

                # 文字数
                if len(text) < 4:
                    break

                # 文字や単語の繰り返し
                if re.search(r'(.+)\1{4}', text):
                    break

                clean_texts.append(' '.join(text.split()))
            
            else:
                clean_dialogs.add(tuple(clean_texts))

    return clean_dialogs


def write_dialogs(output_dir, dialogs):
    """発話の数ごとに対話を書き込む。

    :param output_dir: 出力ディレクトリ
    :type output_dir: str
    :param dialogs: 対話の集合
    :type dialogs: set
    """
    
    n_turns_to_dialog = defaultdict(set)

    for dialog in dialogs:
        n_turns = len(dialog)
        n_turns_to_dialog[n_turns].add(dialog)
    
    for n_turns, dialogs in n_turns_to_dialog.items():
        output_path = os.path.join(output_dir, f'{n_turns}.tsv')
        with open(output_path, 'w', encoding='utf-8') as f:
            for dialog in dialogs:
                f.write('\t'.join(dialog) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw_dir', help='生のディレクトリ')
    parser.add_argument('cleaned_dir', help='クリーニングしたディレクトリ')
    parser.add_argument(
        '--allow_ascii', action='store_true', help='ASCIIを日本語として許容する'
    )
    parser.add_argument(
        '--remove_non_ja', action='store_true', help='日本語でない文字を削除する'
    )
    args = parser.parse_args()

    dialogs = read_dialogs(args.raw_dir)
    n_raw = len(dialogs)

    cleaned_dialogs = clean_dialogs(dialogs, args.allow_ascii, args.remove_non_ja)
    n_clean = len(cleaned_dialogs)

    write_dialogs(args.cleaned_dir, cleaned_dialogs)

    print(f'{n_clean}個の対話を書き込み（生の{n_clean / n_raw:%}）')


if __name__ == '__main__':
    main()
