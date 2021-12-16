import argparse
import csv
import os

from tqdm import tqdm
import zenhan
from pyknp import Juman


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cleaned_dir', help='クリーニングしたディレクトリ')
    parser.add_argument('mrph_dir', help='分かち書きしたディレクトリ')
    args = parser.parse_args()

    jumanpp = Juman()

    for tsv in tqdm(os.listdir(args.cleaned_dir)):
        cleaned_tsv = os.path.join(args.cleaned_dir, tsv)
        mrph_tsv = os.path.join(args.mrph_dir, tsv)

        mrph_rows = []
        with open(cleaned_tsv, encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                mrph_row = []
                for text in row:
                    result = jumanpp.analysis(zenhan.h2z(text))
                    mrph_row.append(' '.join(mrph.midasi for mrph in result.mrph_list()))
                
                mrph_rows.append(mrph_row)
        
        with open(mrph_tsv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            writer.writerows(mrph_rows)


if __name__ == '__main__':
    main()
