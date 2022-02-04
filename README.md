# Twitter対話クローラ

Twitterからマルチターンの対話を収集するためのクローラです。

## 使い方

### API

収集にはAPIが必要です。
APIを取得したら、Consumer KeyやAccess Tokenなどを記載した`.env`を用意してください。

### crawl

コマンドライン引数で出力ディレクトリを指定してください。APIを使い分ける場合、`--dotenv_path`で使いたい`.env`を指定してください。ユーザIDの取得における検索クエリは`--q`で指定してください。

対話はTSV形式で保存されます。各行はタブで区切られた一連の発話です。

```bash
python -m crawler.crawl $OUTPUT_DIR --dotenv_path $DOTENV_PATH --q $Q
```

### clean

crawlの出力ディレクトリと出力TSVファイル名を指定してください。日本語でない文字を含む対話や短すぎる発話を含むもの、文字や単語を繰り返す発話を含むものを除去します。

日本語でない文字を含む対話を除外せずにその文字だけを削除する場合、`--remove_non_ja`を指定してください。またASCIIを日本語として扱う場合、`--include_ascii_in_ja`を指定してください。

```bash
python -m crawler.clean $DATA_DIR $OUTPUT_TSV --remove_non_ja --include_ascii_in_ja
```

### 分かち書き

クリーニングした対話を分かち書きします。
半角を全角に正規化し、Juman++で形態素解析をします。

```
python mrph.py $CLEANED_DIR $MRPH_DIR
```

## 参考

### Pythonでつくる対話システム

- https://www.ohmsha.co.jp/book/9784274224799/
- https://github.com/dsbook/dsbook

### パッケージ

- https://saurabh-kumar.com/python-dotenv/
- https://www.tweepy.org/
