# Web ページ画像化ツール

指定された URL の Web ページを画像として保存するツールです。Web ページの内容が不明瞭にならないように、適切に分割して画像化し、固定の命名規則に基づいたファイル名で保存します。また、動的コンテンツにも可能な限り対応します。

## 機能

- 指定した URL の Web ページをキャプチャして画像として保存
- Web ページのサイズに応じて、適切に分割して画像化
- 画像サイズのカスタマイズ（デフォルト: 1024x1024）
- 動的コンテンツのレンダリング待機時間の設定（デフォルト: 5 秒）
- 固定の命名規則に基づいたファイル名での保存（例: webpage_capture_20250329_122628_1.png）

## 必要条件

- Python 3.6 以上
- Google Chrome（Selenium で使用）
- ChromeDriver（Selenium で使用）

## インストール方法

1. リポジトリをクローンまたはダウンロードします。

2. 必要なライブラリをインストールします。

```bash
pip install selenium pillow
```

3. Google Chrome がインストールされていることを確認します。

4. ChromeDriver をインストールします。
   - Windows: [ChromeDriver のダウンロードページ](https://sites.google.com/a/chromium.org/chromedriver/downloads)からダウンロードし、PATH の通ったディレクトリに配置します。
   - または、以下のコマンドでインストールすることもできます。
   ```bash
   pip install webdriver-manager
   ```
   その場合、tool.py のコードを少し修正する必要があります。

## 使用方法

### 基本的な使い方

```bash
python tool.py --url "https://example.com"
```

### カスタム画像サイズを指定する場合

```bash
python tool.py --url "https://example.com" --width 800 --height 600
```

### 動的コンテンツのレンダリング待機時間を指定する場合

```bash
python tool.py --url "https://example.com" --wait 10
```

### すべてのオプションを指定する場合

```bash
python tool.py --url "https://example.com" --width 800 --height 600 --wait 10
```

## オプション

| オプション | 説明                                    | デフォルト値 |
| ---------- | --------------------------------------- | ------------ |
| --url      | キャプチャする Web ページの URL（必須） | -            |
| --width    | 画像の幅（ピクセル）                    | 1024         |
| --height   | 画像の高さ（ピクセル）                  | 1024         |
| --wait     | ページ読み込み後の待機時間（秒）        | 5            |

## 出力

ツールは以下の命名規則に従って画像ファイルを保存します：

```
webpage_capture_<日時>_<連番>.png
```

例：

- webpage_capture_20250329_122628_1.png
- webpage_capture_20250329_122628_2.png

## 注意事項

- 動的コンテンツのレンダリングに時間がかかる場合、処理時間が長くなる可能性があります。
- ページサイズが非常に大きい場合、画像の保存に時間がかかる可能性があります。
- インターネット接続がない場合や無効な URL が指定された場合、エラーメッセージが表示されます。

## トラブルシューティング

### ChromeDriver のエラーが発生する場合

ChromeDriver のバージョンが Google Chrome のバージョンと一致していない可能性があります。最新の ChromeDriver をダウンロードして再試行してください。

または、webdriver-manager を使用して自動的に ChromeDriver を管理することもできます：

```bash
pip install webdriver-manager
```

そして、tool.py の get_driver 関数を以下のように修正します：

```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def get_driver():
    """Seleniumドライバーを初期化する"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ヘッドレスモード
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except WebDriverException as e:
        logger.error(f"Chromeドライバーの初期化に失敗しました: {e}")
        sys.exit(1)
```

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
