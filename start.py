import selenium
import dotenv
import os
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# id,password は.envから取得

dotenv.load_dotenv()

id = os.getenv("GOOGLE_EMAIL")
password = os.getenv("GOOGLE_PASSWORD")
url = os.getenv("MAP_URL")

options = webdriver.ChromeOptions()
# options.add_argument("--user-data-dir=/Users/korucha/Library/Application Support/Google/Chrome/Default")
# options.add_argument("--profile-directory=Default")

driver = webdriver.Chrome(options=options)
driver.maximize_window() # 念のためウィンドウを最大化
driver.implicitly_wait(5) # 要素が見つからない場合に少し待つ (推奨はWebDriverWait)

driver.get(url)

# --- ログイン処理 ---
try:
    print("ログイン処理を開始します...")
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.ID, "identifierId")))
    email_input.send_keys(id)
    email_input.send_keys(Keys.RETURN)
    print("メールアドレスを入力しました。")

    password_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
    # パスワード入力フィールドが表示される前に少し待機が必要な場合がある
    # time.sleep(1) # 短い固定待機 (デバッグ用)
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    print("パスワードを入力しました。")
    # ログイン後のページ読み込みを待つ (より良いのは特定の要素が表示されるまで待つこと)
    print("ログイン後のページ読み込みを待機中...")
    time.sleep(7) # 固定待機は不安定要素。後の要素検索でカバーできることが多い。

    # --- レイヤーオプションとインポートボタンのクリック ---
    print("レイヤーオプションをクリックします...")
    # オプションボタンのXPathは変わりやすい可能性があるので注意
    option_button_locator = (By.XPATH, '//*[@id="ly0-layer-header"]/div[3]')
    optionElement = wait.until(EC.element_to_be_clickable(option_button_locator))
    optionElement.click()
    print("レイヤーオプションをクリックしました。")

    print("インポートボタンをクリックします...")
    # インポートボタンのXPathも変わりやすい可能性あり。テキストなどで指定できないか検討。
    # 例: (By.XPATH, "//div[contains(text(), 'インポート')]")
    import_button_locator = (By.XPATH, '//*[@id=":1e"]/div') # :1e のようなIDは非常に不安定
    # より安定しそうなXPathの例 (テキストが'インポート'の場合)
    import_button_locator_alt = (By.XPATH, "//div[contains(@class, 'goog-menuitem') and contains(., 'インポート')]")

    try:
      importElement = wait.until(EC.element_to_be_clickable(import_button_locator_alt)) # まず代替案を試す
    except TimeoutException:
      print(f"代替ロケータ ({import_button_locator_alt}) でインポートボタンが見つかりませんでした。元のロケータを試します。")
      importElement = wait.until(EC.element_to_be_clickable(import_button_locator)) # 元のロケータ

    importElement.click()
    print("インポートボタンをクリックしました。")
    time.sleep(3) # Picker iframeが表示されるのを少し待つ

    # --- Google Picker iframe の特定と切り替え ---
    print("Google Picker iframe を特定します...")
    # ★★★ ここに、開発者ツールで確認した最も安定性の高いロケータを設定してください ★★★
    # 例1: title属性を使う場合 (最も推奨)
    # iframe_locator = (By.XPATH, "//iframe[@title='インポートするファイルの選択']") # 実際のtitle属性値に置き換えてください
    # 例2: data-postorigin属性を使う場合
    iframe_locator = (By.XPATH, "//iframe[contains(@data-postorigin, '/picker?')]")
    # 例3: 親要素からの相対パス (親要素の特定が必要)
    # iframe_locator = (By.XPATH, "//div[@id='stable-parent-id']/iframe")

    # --- 1. 正しいiframeへの切り替え ---
    wait_long = WebDriverWait(driver, 20) # Picker読み込み用に長めの待機時間
    print(f"Google Picker iframe ({iframe_locator}) を待機し、切り替えます...")
    wait_long.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
    print("Google Picker iframe に切り替えました。")

    # --- 2. フレーム内の「Google ドライブ」ボタンを操作 ---
    print("フレーム内の「Google ドライブ」ボタンを検索しています...")
    try:
        button_locator = (By.XPATH, "//button[@role='tab' and contains(., 'Google ドライブ')]")
        print(f"ロケータ: {button_locator} で要素を待機します。")
        google_drive_button = wait_long.until(EC.element_to_be_clickable(button_locator))
        print("「Google ドライブ」ボタンが見つかり、クリック可能です。")
        google_drive_button.click()
        print("「Google ドライブ」ボタンをクリックしました。")

        # --- Google ドライブ内のファイル選択などの後続処理 ---
        print("Google ドライブ内のファイルを選択する処理に進みます...")
        # (ここにファイル選択などのコードを追加)
        # 例: 特定のファイル名をクリック
        # file_locator = (By.XPATH, "//div[@role='option' and contains(@aria-label, 'ファイル名')]")
        # file_element = wait_long.until(EC.element_to_be_clickable(file_locator))
        # file_element.click()
        # print("ファイルをクリックしました。")
        #
        # # 選択ボタンをクリック
        # select_button_locator = (By.XPATH, "//button[contains(text(), '選択')]") # ボタンのテキストは要確認
        # select_button = wait_long.until(EC.element_to_be_clickable(select_button_locator))
        # select_button.click()
        # print("選択ボタンをクリックしました。")

        time.sleep(5) # 処理完了を待つ (デバッグ用)


    except TimeoutException:
        print("エラー: フレーム内の「Google ドライブ」ボタン、または後続の要素が見つかりませんでした（タイムアウト）。")
        try:
            inner_html = driver.page_source # 現在のフレームのHTML
            print(f"--- iframe ({iframe_locator}) 内のHTML (先頭1000文字) ---")
            print(inner_html[:1000])
            print("-----------------------------")
        except Exception as html_err:
            print(f"フレーム内のHTML取得中にエラー: {html_err}")
    except Exception as e:
        print(f"Picker内での操作中に予期せぬエラーが発生しました: {e}")

except TimeoutException as te:
    print(f"エラー: 要素が見つかりませんでした（タイムアウト）。{te}")
    driver.save_screenshot("error_screenshot.png") # エラー時のスクリーンショット
except NoSuchElementException as nse:
    print(f"エラー: 要素が見つかりませんでした。{nse}")
    driver.save_screenshot("error_screenshot.png")
except Exception as e:
    print(f"予期せぬエラーが発生しました: {e}")
    driver.save_screenshot("error_screenshot.png")
finally:
    # --- 3. デフォルトコンテンツに戻る ---
    # エラーが発生しても、必ずデフォルトコンテキストに戻る
    try:
        driver.switch_to.default_content()
        print("デフォルトコンテンツに戻りました。")
    except Exception as switch_err:
        print(f"デフォルトコンテンツへの切り替え中にエラー: {switch_err}")

    print("処理を終了します。5秒後にブラウザを閉じます。")
    time.sleep(5) # デバッグ用に閉じるのを待つ
    driver.quit()