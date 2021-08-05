import argparse
import csv
import os

from tqdm import tqdm
import zenhan
from pyknp import Juman


def main(args):
    jumanpp = Juman()
    
    for tsv in tqdm(os.listdir(args.data_dir)):
        mrph_rows = []
        with open(os.path.join(args.data_dir, tsv), newline='') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                mrph_row = []
                for text in row:
                    result = jumanpp.analysis(zenhan.h2z(text))
                    mrph_row.append(' '.join(mrph.midasi for mrph in result.mrph_list()))
                
                mrph_rows.append(mrph_row)
        
        with open(os.path.join(args.output_dir, tsv), 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            writer.writerows(mrph_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    main(args)
