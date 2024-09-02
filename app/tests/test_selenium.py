import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class SeleniumTestCase(unittest.TestCase):
    def setUp(self):
        # ChromeDriverのオプションを設定
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # ヘッドレスモードで実行（GUIなし）
        chrome_options.add_argument("--disable-gpu")  # GPUを無効化
        chrome_options.add_argument("--no-sandbox")  # サンドボックスを無効化
        chrome_options.add_argument("--disable-dev-shm-usage")  # 共有メモリを無効化
        self.driver = webdriver.Chrome(options=chrome_options)

    def tearDown(self):
        # テスト終了後にブラウザを閉じる
        self.driver.quit()

    def test_home_page(self):
        # ホームページにアクセスし、タイトルを確認する
        self.driver.get('https://synapse-tev2.onrender.com')
        self.assertIn("パチペディア", self.driver.title)

    def test_login(self):
        # ログインページにアクセスし、ログインを試行する
        self.driver.get('https://synapse-tev2.onrender.com/login')
        self.driver.find_element(By.NAME, "email").send_keys("test@example.com")
        self.driver.find_element(By.NAME, "password").send_keys("password")
        self.driver.find_element(By.XPATH, '//input[@type="submit"]').click()
        self.assertIn("testuser", self.driver.page_source)

if __name__ == '__main__':
    unittest.main()
