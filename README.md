# Twitter Dialog Crawler

ツイッターからマルチターン対話をクローリングします。
さらにクローリングされたマルチターン対話をクリーニングします。

## 使い方

### API

収集にはAPIが必要です。
`CONSUMER_KEY`などを記載した`.env`を用意してください。

```
CONSUMER_KEY=
CONSUMER_SECRET=
ACCESS_TOKEN=
ACCESS_TOKEN_SECRET=
```

### クローリング

`crawl.py`でマルチターン対話を収集します。
コマンドライン引数によって出力ディレクトリを指定してください。

APIでユーザのタイムラインを取得し、ツイートとリプライの関係を保持します。
そして構築された木を走査することで、マルチターン対話を獲得します。

マルチターン対話はTSVファイルに保存されます。
各行はタブで区切られた一連の発話です。

```
python crawl.py $OUTPUT_DIR
```

## 参考

### Pythonでつくる対話システム

- https://www.ohmsha.co.jp/book/9784274224799/
- https://github.com/dsbook/dsbook

### パッケージ

- https://saurabh-kumar.com/python-dotenv/
- https://www.tweepy.org/
