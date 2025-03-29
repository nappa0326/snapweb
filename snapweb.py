#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Webページ画像化ツール
指定されたURLのWebページを画像として保存するツール
"""

import os
import time
import argparse
import logging
from datetime import datetime
from urllib.parse import urlparse
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from PIL import Image
import io

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def validate_url(url):
    """URLの有効性を検証する"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def get_driver(use_headless=True, load_cookies=True, cookies_file="browser_cookies.pkl"):
    """Seleniumドライバーを初期化する"""
    chrome_options = Options()
    
    if use_headless:
        chrome_options.add_argument("--headless")  # ヘッドレスモード
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 一般的なユーザーエージェントを設定（最新のChromeブラウザを模倣）
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # CAPTCHAを回避するための追加設定
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 自動化制御機能を無効化
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 自動化フラグを除外
    chrome_options.add_experimental_option("useAutomationExtension", False)  # 自動化拡張機能を無効化
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # WebDriverの検出を回避するためのJavaScriptを実行
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 保存されたクッキーがあれば読み込む
        if load_cookies and os.path.exists(cookies_file):
            try:
                import pickle
                with open(cookies_file, "rb") as f:
                    cookies = pickle.load(f)
                    # クッキーを読み込む前に一度ダミーページにアクセスする必要がある
                    driver.get("about:blank")
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                            logger.info(f"クッキーを読み込みました: {cookie.get('name')}")
                        except Exception as e:
                            logger.warning(f"クッキーの読み込みに失敗しました: {e}")
            except Exception as e:
                logger.warning(f"クッキーファイルの読み込みに失敗しました: {e}")
        
        return driver
    except WebDriverException as e:
        logger.error(f"Chromeドライバーの初期化に失敗しました: {e}")
        sys.exit(1)

def capture_full_page(driver, url, wait_time, width, height, save_cookies=True, cookies_file="browser_cookies.pkl"):
    """ページ全体をキャプチャする"""
    try:
        logger.info(f"URLにアクセス中: {url}")
        driver.get(url)
        
        # 指定された待機時間だけ待機（動的コンテンツのレンダリング用）
        logger.info(f"{wait_time}秒間待機中...")
        time.sleep(wait_time)
        
        # クッキーを保存（次回のアクセスで使用するため）
        if save_cookies:
            try:
                import pickle
                cookies = driver.get_cookies()
                with open(cookies_file, "wb") as f:
                    pickle.dump(cookies, f)
                logger.info(f"クッキーを保存しました: {len(cookies)}個")
            except Exception as e:
                logger.warning(f"クッキーの保存に失敗しました: {e}")
        
        # CAPTCHAの検出を試みる
        try:
            # 一般的なCAPTCHA要素を探す
            captcha_elements = driver.find_elements(By.XPATH,
                "//*[contains(@id, 'captcha') or contains(@class, 'captcha') or contains(@id, 'recaptcha') or contains(@class, 'recaptcha')]")
            
            if captcha_elements:
                logger.warning("ページにCAPTCHAが検出されました。追加の待機時間を設定します。")
                # CAPTCHAが検出された場合、追加の待機時間を設定
                time.sleep(5)  # 追加の待機時間
                
                # ヘッドレスモードでない場合、ユーザーに通知
                if not driver.execute_script("return navigator.webdriver === undefined"):
                    logger.warning("CAPTCHAが表示されています。ヘッドレスモードを無効にして再試行することをお勧めします。")
        except Exception as e:
            logger.warning(f"CAPTCHA検出中にエラーが発生しました: {e}")
        
        # ページの高さを取得
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
        
        # ビューポートの高さと幅を取得
        viewport_height = driver.execute_script("return window.innerHeight")
        viewport_width = driver.execute_script("return window.innerWidth")
        
        logger.info(f"ビューポートサイズ: {viewport_width}x{viewport_height}px")
        logger.info(f"ページの高さ: {total_height}px")
        
        # スクロールしながら撮影する方法でスクリーンショットを取得
        logger.info("スクロールしながらスクリーンショットを取得します...")
        
        # スクロール回数を計算
        num_scrolls = max(1, (total_height + viewport_height - 1) // viewport_height)
        logger.info(f"スクロール回数: {num_scrolls}")
        
        # スクリーンショットを保存するリスト
        screenshots = []
        
        # ページをスクロールしながらスクリーンショットを取得
        for i in range(num_scrolls):
            # 現在のスクロール位置を計算
            scroll_top = i * viewport_height
            
            # スクロール
            driver.execute_script(f"window.scrollTo(0, {scroll_top});")
            logger.info(f"スクロール位置: {scroll_top}px")
            
            # スクロール後に十分待機（スクロールが完了するまで）
            time.sleep(1.0)
            
            # 現在のスクロール位置を確認
            actual_scroll_top = driver.execute_script("return window.pageYOffset;")
            logger.info(f"実際のスクロール位置: {actual_scroll_top}px")
            
            # スクリーンショットを取得
            screenshot = driver.get_screenshot_as_png()
            screenshot_img = Image.open(io.BytesIO(screenshot))
            
            # スクリーンショットの高さを確認
            logger.info(f"スクリーンショットサイズ: {screenshot_img.width}x{screenshot_img.height}px")
            
            # スクリーンショットを追加
            screenshots.append(screenshot_img)
            logger.info(f"スクリーンショット {i+1}/{num_scrolls} を取得しました")
        
        return screenshots
    
    except TimeoutException:
        logger.error("ページの読み込みがタイムアウトしました")
        sys.exit(1)
    except WebDriverException as e:
        logger.error(f"ページのキャプチャ中にエラーが発生しました: {e}")
        sys.exit(1)

def split_and_save_images(screenshots, width, height):
    """スクリーンショットを分割して保存する"""
    # 現在の日時を取得（ファイル名用）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存するファイル名のベース部分
    base_filename = f"webpage_capture_{timestamp}"
    
    saved_files = []
    
    # 各スクリーンショットを処理
    for i, screenshot in enumerate(screenshots):
        # 画像のサイズを取得
        img_width, img_height = screenshot.size
        
        # 横方向の分割数を計算（切り上げ）
        num_horizontal_splits = (img_width + width - 1) // width
        
        # 縦方向の分割数を計算（切り上げ）
        num_vertical_splits = (img_height + height - 1) // height
        
        # 画像を分割して保存
        for h in range(num_vertical_splits):
            for w in range(num_horizontal_splits):
                # 分割範囲を計算
                left = w * width
                upper = h * height
                right = min((w + 1) * width, img_width)
                lower = min((h + 1) * height, img_height)
                
                # 画像を切り抜く
                cropped_img = screenshot.crop((left, upper, right, lower))
                
                # ファイル名を生成
                file_index = len(saved_files) + 1
                filename = f"{base_filename}_{file_index}.png"
                
                # 画像を保存
                cropped_img.save(filename)
                saved_files.append(filename)
                
                logger.info(f"画像を保存しました: {filename}")
    
    return saved_files

def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="Webページを画像として保存するツール")
    parser.add_argument("--url", required=True, help="キャプチャするWebページのURL")
    parser.add_argument("--width", type=int, default=1024, help="画像の幅（デフォルト: 1024）")
    parser.add_argument("--height", type=int, default=1024, help="画像の高さ（デフォルト: 1024）")
    parser.add_argument("--wait", type=int, default=5, help="ページ読み込み後の待機時間（秒）（デフォルト: 5）")
    parser.add_argument("--no-headless", action="store_true", help="ヘッドレスモードを無効にする（ブラウザが表示されます）")
    parser.add_argument("--no-cookies", action="store_true", help="クッキーの読み込み/保存を無効にする")
    parser.add_argument("--cookies-file", default="browser_cookies.pkl", help="クッキーファイルのパス（デフォルト: browser_cookies.pkl）")
    
    args = parser.parse_args()
    
    # URLの検証
    if not validate_url(args.url):
        logger.error("無効なURLが指定されました")
        sys.exit(1)
    
    # 開始時刻をログに記録
    start_time = time.time()
    logger.info("Webページ画像化ツールを開始します")
    logger.info(f"URL: {args.url}")
    logger.info(f"画像サイズ: {args.width}x{args.height}")
    logger.info(f"待機時間: {args.wait}秒")
    logger.info(f"ヘッドレスモード: {'無効' if args.no_headless else '有効'}")
    logger.info(f"クッキーの読み込み/保存: {'無効' if args.no_cookies else '有効'}")
    
    try:
        # Seleniumドライバーを初期化
        use_headless = not args.no_headless
        load_cookies = not args.no_cookies
        driver = get_driver(use_headless=use_headless, load_cookies=load_cookies, cookies_file=args.cookies_file)
        
        # ページ全体をキャプチャ
        screenshots = capture_full_page(
            driver,
            args.url,
            args.wait,
            args.width,
            args.height,
            save_cookies=not args.no_cookies,
            cookies_file=args.cookies_file
        )
        
        # スクリーンショットを分割して保存
        saved_files = split_and_save_images(screenshots, args.width, args.height)
        
        # 終了時刻をログに記録
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"処理が完了しました（所要時間: {elapsed_time:.2f}秒）")
        logger.info(f"保存されたファイル: {', '.join(saved_files)}")
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)
    finally:
        # ドライバーを終了
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main()