import argparse
import csv
import glob
import html
import os
import re

from tqdm import tqdm

screen_name = re.compile(r'@[A-Za-z0-9_]{1,15}')

ja = re.compile(r'[\u3000-\u30ff\u4e00-\u9fff]')
not_ascii_nor_ja = re.compile(r'[^\u0000-\u007f\u3000-\u30ff\u4e00-\u9fff]')

min_length = 4
rep = re.compile(r'(.+)\1{4}')


def clean_text(text):
    text = html.unescape(text)  # html escape

    text = screen_name.sub('', text)  # screen name
    text = ' '.join(text.split())

    return text


def clean_row(row):
    return [clean_text(text) for text in row]


def filter_text(text):
    if not ja.search(text):  # no japanese
        return False

    if not_ascii_nor_ja.search(text):  # not ascii nor japanese
        return False

    if len(text) < min_length:  # length
        return False

    if rep.search(text):  # repetition
        return False

    return True


def filter_row(row):
    return all(filter_text(text) for text in row)


def read_dialogs(data_dir, dialogs):
    n_read = 0

    data_tsvs = glob.glob(f'{data_dir}/*.tsv')
    for data_tsv in tqdm(data_tsvs):
        with open(data_tsv, encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                row = clean_row(row)

                if filter_row(row):
                    dialogs.add('\t'.join(row))
                            
                n_read += 1
    
    return n_read


def write_dialogs(output_dir, dialogs):
    turn_to_dialog = {}
    n_written = 0

    for dialog in dialogs:
        n_turns = len(dialog.split('\t'))
        if n_turns not in turn_to_dialog.keys():
            turn_to_dialog[n_turns] = set()
        
        turn_to_dialog[n_turns].add(dialog)
    
    for n_turns, dialogs in turn_to_dialog.items():
        with open(os.path.join(output_dir, f'{n_turns}.tsv'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(dialogs) + '\n')

        n_written += len(dialogs)
    
    return n_written


def main(args):
    dialogs = set()

    n_read = read_dialogs(args.data_dir, dialogs)
    n_written = write_dialogs(args.output_dir, dialogs)

    print(f'Write {n_written} dialogues ({n_written / n_read:%})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    main(args)
