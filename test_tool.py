#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Webページ画像化ツールのテストスクリプト
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image

# テスト対象のモジュールをインポート
import snapweb

class TestWebpageCaptureTool(unittest.TestCase):
    """Webページ画像化ツールのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用の画像を作成
        self.test_image = Image.new('RGB', (1920, 1080), color='white')
        self.test_image_bytes = BytesIO()
        self.test_image.save(self.test_image_bytes, format='PNG')
        self.test_image_bytes.seek(0)
    
    def test_validate_url(self):
        """URLの検証機能をテスト"""
        # 有効なURL
        self.assertTrue(snapweb.validate_url("https://example.com"))
        self.assertTrue(snapweb.validate_url("http://localhost:8000"))
        
        # 無効なURL
        self.assertFalse(snapweb.validate_url("invalid-url"))
        self.assertFalse(snapweb.validate_url(""))
    
    @patch('snapweb.webdriver.Chrome')
    def test_get_driver(self, mock_chrome):
        """ドライバー初期化機能をテスト"""
        # モックドライバーを設定
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # 関数を実行
        driver = snapweb.get_driver()
        
        # ドライバーが正しく初期化されたことを確認
        self.assertEqual(driver, mock_driver)
        self.assertTrue(mock_chrome.called)
    
    @patch('snapweb.webdriver.Chrome')
    @patch('snapweb.time.sleep')
    def test_capture_full_page(self, mock_sleep, mock_chrome):
        """ページキャプチャ機能をテスト"""
        # モックドライバーを設定
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # スクリーンショットのモックを設定
        mock_driver.get_screenshot_as_png.return_value = self.test_image_bytes.getvalue()
        
        # ページの高さとビューポートの高さを設定
        # スクロール処理のために十分な戻り値を設定
        mock_driver.execute_script.side_effect = [
            1000,  # document.body.scrollHeight
            500,   # window.innerHeight
            500,   # window.innerWidth
            0,     # window.pageYOffset (for first scroll)
            0,     # window.pageYOffset (for second scroll)
            0      # window.pageYOffset (for third scroll)
        ]
        
        # 関数を実行
        screenshots = snapweb.capture_full_page(mock_driver, "https://example.com", 1, 1024, 1024, save_cookies=False)
        
        # 結果を確認
        self.assertEqual(len(screenshots), 1)  # 1回スクロールする（現在の実装では）
        
        # ドライバーのメソッドが正しく呼び出されたことを確認
        mock_driver.get.assert_called_once_with("https://example.com")
        self.assertEqual(mock_driver.get_screenshot_as_png.call_count, 1)
    
    def test_split_and_save_images(self):
        """画像分割・保存機能をテスト"""
        # テスト用の画像リストを作成
        screenshots = [self.test_image, self.test_image]
        
        # 一時的にsaveメソッドをモック化
        original_save = Image.Image.save
        try:
            # saveメソッドをモック化
            Image.Image.save = MagicMock()
            
            # 関数を実行
            saved_files = snapweb.split_and_save_images(screenshots, 1000, 1000)
            
            # 結果を確認
            self.assertEqual(len(saved_files), 8)  # 2枚の画像を分割すると8枚になる
            
            # saveメソッドが正しく呼び出されたことを確認
            self.assertEqual(Image.Image.save.call_count, 8)
            
        finally:
            # saveメソッドを元に戻す
            Image.Image.save = original_save

if __name__ == "__main__":
    unittest.main()