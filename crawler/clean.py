import argparse
import csv
import glob
import html
import re
from typing import Optional

from tqdm import tqdm


class Cleaner:
    def __init__(
        self,
        min_length: Optional[int] = 4,
        max_repeat: Optional[int] = 4,
        remove_non_ja: Optional[bool] = False,
        include_ascii_in_ja: Optional[bool] = False
    ) -> None:
        self.min_length = min_length
        self.max_repeat = max_repeat

        self.remove_non_ja = remove_non_ja
        self.include_ascii_in_ja = include_ascii_in_ja

        if include_ascii_in_ja:
            non_ja = r'[^\u0000-\u007f\u3000-\u30ff\u4e00-\u9fff]'
        
        else:
            non_ja = r'[^\u3000-\u30ff\u4e00-\u9fff]'

        self.non_ja_pattern = re.compile(non_ja)

        self._dialogs = set()
        self._cleaned_dialogs = set()

    def load(self, data_dir: str) -> None:
        for data_tsv in glob.glob(f'{data_dir}/*.tsv'):
            with open(data_tsv, encoding='utf-8', newline='') as f:
                reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    self._dialogs.add(tuple(row))

        print(f'Load {len(self._dialogs)} dialogs from {data_dir}.')

    def save(self, output_tsv: str) -> None:
        with open(output_tsv, 'w', encoding='utf-8') as f:
            for cleaned_dialog in self._cleaned_dialogs:
                f.write('\t'.join(cleaned_dialog) + '\n')
        
        print(f'Save {len(self._cleaned_dialogs)} dialogs to {output_tsv}.')
    
    def _clean_text(self, text: str) -> str:
        # remove screen name
        text = re.sub(r'@[A-Za-z0-9_]{1,15}', '', text)
        text = ' '.join(text.split())

        # unescape
        text = html.unescape(text)

        if self.remove_non_ja:
            text = self.non_ja_pattern.sub('', text)

        return text

    def _filter_text(self, text: str) -> bool:
        # length
        if len(text) < self.min_length:
            return False

        # repeat
        if re.search(r'(.+)\1{' + str(self.max_repeat) + r'}', text):
            return False
        
        if not self.remove_non_ja and self.non_ja_pattern.search(text):
            return False

        return True

    def clean(self) -> None:
        for dialog in tqdm(self._dialogs):
            for text in dialog:
                cleaned_dialog = []

                for text in dialog:
                    cleaned_text = self._clean_text(text)

                    if not self._filter_text(cleaned_text):
                        break

                    cleaned_dialog.append(cleaned_text)

                else:
                    self._cleaned_dialogs.add(tuple(cleaned_dialog))
        
        num_raw = len(self._dialogs)
        num_cleaned = len(self._cleaned_dialogs)
        
        print(
            f'Get {num_cleaned} cleaned dialogs '
            f'({num_cleaned / num_raw:%} of the raw).'
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'data_dir',
        help='path to directory for crawled (raw) dialogs'
    )
    parser.add_argument(
        'output_tsv',
        help='path to TSV for cleaned dialogs'
    )
    parser.add_argument(
        '--min_length',
        default=4,
        type=int,
        help='min number of characters per utterance'
    )
    parser.add_argument(
        '--max_repeat',
        default=4,
        type=int,
        help='max number of repeat for characters or words'
    )
    parser.add_argument(
        '--remove_non_ja',
        action='store_true',
        help=(
            'not exclude dialogs with non-Japanese characters '
            'but remove the characters in the dialogs'
        )
    )
    parser.add_argument(
        '--include_ascii_in_ja',
        action='store_true',
        help='include ASCII in Japanese characters'
    )
    args = parser.parse_args()

    cleaner = Cleaner(
        min_length=args.min_length,
        max_repeat=args.max_repeat,
        remove_non_ja=args.remove_non_ja,
        include_ascii_in_ja=args.include_ascii_in_ja
    )
    cleaner.load(args.data_dir)

    cleaner.clean()
    cleaner.save(args.output_tsv)


if __name__ == '__main__':
    main()
