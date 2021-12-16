# Twitter対話クローラ

Twitterからマルチターンの対話を収集するためのクローラです。

## 使い方

### API

収集にはAPIが必要です。
APIを取得したら、Consumer KeyやAccess Tokenなどを記載した`.env`を用意してください。

```
CONSUMER_KEY=
CONSUMER_SECRET=
ACCESS_TOKEN=
ACCESS_TOKEN_SECRET=
```

### 収集

`crawl.py`で対話を収集します。

コマンドライン引数で、対話を出力するディレクトリを指定してください。
`.env`を使い分ける場合は、`--dotenv_path`で使いたいファイルを指定してください。
またユーザIDの取得における検索クエリを与えたい場合は、`--q`でそれを指定してください。

対話はTSV形式で保存されます。
各行はタブで区切られた一連の発話です。

```
python crawl.py $OUTPUT_DIR --dotenv_path $DOTENV_PATH --q $Q
```

### クリーニング

収集した対話は`clean.py`によってクリーニングします。

`crawl.py`の出力ディレクトリと、新たな出力ディレクトリをそれぞれ指定してください。
日本語でない文字を含むものや短すぎるもの、繰り返しが多いものを除去します。
ASCIIを日本語に含める場合は、`--allow_ascii`を指定してください。

対話は発話の数ごとにTSV形式で保存されます。

```
python clean.py $RAW_DIR $CLEANED_DIR --allow_ascii
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
