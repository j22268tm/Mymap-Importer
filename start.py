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
file_name = os.getenv("FILE_NAME")
options = webdriver.ChromeOptions()
# options.add_argument("--user-data-dir=/Users/korucha/Library/Application Support/Google/Chrome/Default")
# options.add_argument("--profile-directory=Default")
# options.add_argument("--headless") # iframeの操作が必要なため、headlessは使用不可

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
        print(f"Google ドライブ内のファイル '{file_name}' を選択する処理に進みます...")
        try:
            file_locator = (By.XPATH, f"//span[normalize-space()='{file_name}']/ancestor::div[@aria-labelledby][1]")
            print(f"ロケータ: {file_locator} でファイル要素 '{file_name}' を待機します。")
            # まず要素が表示されるまで待つ (visibility_of_element_located)
            file_element_row = wait_long.until(EC.visibility_of_element_located(file_locator))
            # 次にその要素がクリック可能になるまで待つ (element_to_be_clickable)
            file_element_clickable = wait_long.until(EC.element_to_be_clickable(file_locator))

            print(f"ファイル '{file_name}' が見つかり、クリック可能です。")
            # クリックを実行
            file_element_clickable.click()
            # 代替クリック方法 (JavaScript Executor, クリックがうまくいかない場合に試す)
            # driver.execute_script("arguments[0].click();", file_element_clickable)

            print(f"ファイル '{file_name}' をクリックしました。")

            # --- 選択ボタンをクリック ---
            print("挿入ボタンを検索しています...")
            # ボタンのテキストが'選択'であることを確認してください ('開く'などの場合もあります)
            # normalize-space() でボタンテキスト前後の空白を無視します
            insert_button_locator = (By.XPATH, "//button[.//span[normalize-space()='挿入']]")
            insert_button = wait_long.until(EC.element_to_be_clickable(insert_button_locator))
            print("挿入ボタンが見つかり、クリック可能です。")
            try:
                insert_button.click()
            except Exception as click_err:
                print(f"挿入ボタンの通常のクリックに失敗しました ({click_err})。JavaScriptでのクリックを試みます。")
                driver.execute_script("arguments[0].click();", insert_button)
            print("挿入ボタンをクリックしました。") # ログメッセージ修正

            print("ファイルの選択・挿入処理が完了しました。")
            print("ファイルインポート処理の完了を待機しています...")
            # インポート完了の確認 (例: ダイアログが閉じる、レイヤーが追加されるなど)
            # ここでは固定待機 (適切なEC条件に置き換えること)
            time.sleep(10)
            print("インポート処理が完了したと見なします。")
        except Exception as file_select_exception:
            print(f"ファイル選択処理中に予期せぬエラーが発生しました: {file_select_exception}")
            driver.save_screenshot("file_select_unexpected_error.png")
            raise # エラーを再発生させる

        except:
            print(f"エラー: ファイル '{file_name}' または選択ボタンが見つかりませんでした（タイムアウト）。")
            # デバッグ情報としてiframe内のHTMLを出力
            try:
                # 現在のフレーム(Picker)のHTMLを取得
                inner_html = driver.page_source
                print(f"--- iframe ({iframe_locator}) 内のHTML (先頭1500文字) ---") # 少し長めに表示
                print(inner_html[:1500])
                print("-----------------------------")
            except Exception as html_err:
                print(f"フレーム内のHTML取得中にエラー: {html_err}")
            driver.save_screenshot("file_select_timeout_error.png")
            raise # エラーを再発生させ、finallyブロックで適切に終了させる



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