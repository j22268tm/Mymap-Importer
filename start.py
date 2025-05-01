import traceback
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

# --- Constants ---
DEFAULT_TIMEOUT = 20
SHORT_TIMEOUT = 10
LONG_TIMEOUT = 25 # For Picker and import processing
INITIAL_LAYER_NAME = "無題のレイヤ"

# --- Initialization ---

def load_config():
    """Loads configuration from .env file."""
    print("--- 設定読み込み ---")
    dotenv.load_dotenv()
    config = {
        "id": os.getenv("GOOGLE_EMAIL"),
        "password": os.getenv("GOOGLE_PASSWORD"),
        "url": os.getenv("MAP_URL"),
        "file_name": os.getenv("FILE_NAME")
    }
    if not all(config.values()):
        raise ValueError("環境変数 (GOOGLE_EMAIL, GOOGLE_PASSWORD, MAP_URL, FILE_NAME) が .env ファイルに設定されていません。")
    print("環境変数を読み込みました。")
    return config

def initialize_driver():
    """Initializes and returns the Chrome WebDriver."""
    print("--- WebDriver初期化 ---")
    options = webdriver.ChromeOptions()
    # 必要に応じてオプションを追加 (例: options.add_argument('--headless'))
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    # driver.implicitly_wait(5) # implicitly_wait は非推奨。WebDriverWait を使用します。
    print("WebDriverを初期化しました。")
    return driver

# --- Login ---

def login(driver, url, username, password):
    """Logs into Google account."""
    print("--- ログイン処理 ---")
    driver.get(url)
    wait = WebDriverWait(driver, SHORT_TIMEOUT)
    try:
        print("メールアドレスを入力します...")
        email_input = wait.until(EC.visibility_of_element_located((By.ID, "identifierId")))
        email_input.send_keys(username)
        email_input.send_keys(Keys.RETURN)
        print("メールアドレスを入力しました。")

        print("パスワードを入力します...")
        # パスワードフィールドが表示されるまで待機
        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
        # 少し待機して入力可能にする（場合によっては必要）
        time.sleep(1)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        print("パスワードを入力しました。")

        # ログイン後の要素が表示されるまで待機 (例: マップのタイトルなど、より具体的な要素が良い)
        # ここでは、レイヤーオプションボタンが表示されることを期待する
        print("ログイン後のページ読み込みを待機中...")
        option_button_locator = (By.XPATH, '//*[@id="ly0-layer-header"]/div[3]') # 不安定な可能性あり
        wait.until(EC.element_to_be_clickable(option_button_locator))
        print("ログイン成功を確認しました。")

    except TimeoutException as e:
        print(f"エラー: ログイン要素が見つかりませんでした（タイムアウト）。{e}")
        driver.save_screenshot("login_error.png")
        raise
    except Exception as e:
        print(f"ログイン中に予期せぬエラーが発生しました: {e}")
        driver.save_screenshot("login_unexpected_error.png")
        raise

# --- Initial Operations ---

def click_layer_options(driver):
    """Clicks the options menu for the first layer."""
    print("--- レイヤーオプションクリック ---")
    wait = WebDriverWait(driver, SHORT_TIMEOUT)
    # オプションボタンのXPathは変わりやすい可能性があるので注意
    option_button_locator = (By.XPATH, '//*[@id="ly0-layer-header"]/div[3]')
    # 代替案 (より安定している可能性):
    # option_button_locator = (By.CSS_SELECTOR, "div[aria-label='レイヤ オプション']") # テキストが異なる場合あり

    try:
        print("レイヤーオプションボタンを検索・クリックします...")
        optionElement = wait.until(EC.element_to_be_clickable(option_button_locator))
        optionElement.click()
        print("レイヤーオプションをクリックしました。")
        time.sleep(1) # メニューが表示されるのを待つ
    except TimeoutException:
        print("エラー: レイヤーオプションボタンが見つかりませんでした。")
        driver.save_screenshot("layer_option_button_error.png")
        raise
    except Exception as e:
        print(f"レイヤーオプションクリック中にエラー: {e}")
        driver.save_screenshot("layer_option_click_error.png")
        raise

# --- Branch 1: Layer Name Check ---

def check_layer_status(driver):
    """Checks the name of the first layer and determines if it's an initial import."""
    print("--- 既存レイヤー名判定 ---")
    wait = WebDriverWait(driver, SHORT_TIMEOUT)
    # レイヤー名要素の特定 (より安定したセレクタを検討推奨)
    layer_name_locator = (By.XPATH, '//*[@id="ly0-layer-header"]/div[2]') # 元のXPath (不安定かも)
    # layer_name_locator_alt = (By.CSS_SELECTOR, ".ZdMwHb-r4nke-haAclf") # クラス名で試す

    try:
        layer_name_element = wait.until(EC.visibility_of_element_located(layer_name_locator))
        layer_name = layer_name_element.text.strip()
        print(f"現在のレイヤー名: 「{layer_name}」")

        if layer_name == INITIAL_LAYER_NAME:
            print(f"レイヤー名が「{INITIAL_LAYER_NAME}」です。初期インポート処理を実行します。")
            return True # is_initial_import = True
        else:
            print(f"レイヤー名が「{INITIAL_LAYER_NAME}」ではありません。削除処理を実行します。")
            return False # is_initial_import = False
    except TimeoutException:
         print("エラー: レイヤー名要素が見つかりませんでした。XPathを確認してください。")
         driver.save_screenshot("layer_name_not_found_error.png")
         raise
    except Exception as e:
        print(f"レイヤー名取得中にエラー: {e}")
        driver.save_screenshot("layer_name_get_error.png")
        raise

# --- Deletion Process ---

def delete_layer(driver):
    """Deletes the current layer."""
    print("--- レイヤー削除処理 ---")
    wait = WebDriverWait(driver, SHORT_TIMEOUT)
    # 削除メニュー項目のXPath (IDは不安定な可能性)
    delete_layer_locator = (By.XPATH, '//*[@id=":1b"]/div') # :1b は非常に不安定
    # 代替案 (テキストで検索):
    delete_layer_locator_alt = (By.XPATH, "//div[contains(@class, 'goog-menuitem')][normalize-space()='このレイヤを削除']")

    # 確認ダイアログの削除ボタン
    accept_delete_locator = (By.XPATH, '//*[@id="confirm-delete-layer-dialog"]/div[3]/button[1]') # IDは不安定な可能性
    # 代替案 (テキストで検索):
    accept_delete_locator_alt = (By.XPATH, "//button[normalize-space()='削除']") # 他の削除ボタンと被らないか注意

    try:
        print("「このレイヤを削除」メニュー項目をクリックします...")
        try:
            delete_layer_item = wait.until(EC.element_to_be_clickable(delete_layer_locator))
        except TimeoutException:
            print(f"代替ロケータ ({delete_layer_locator_alt}) で削除メニュー項目を試します。")
            delete_layer_item = wait.until(EC.element_to_be_clickable(delete_layer_locator_alt))
        delete_layer_item.click()
        print("「このレイヤを削除」をクリックしました。")
        time.sleep(1) # 確認ダイアログ表示待機

        print("確認ダイアログの「削除」ボタンをクリックします...")
        try:
            accept_delete_button = wait.until(EC.element_to_be_clickable(accept_delete_locator))
        except TimeoutException:
            print(f"代替ロケータ ({accept_delete_locator_alt}) で確認ダイアログの削除ボタンを試します。")
            accept_delete_button = wait.until(EC.element_to_be_clickable(accept_delete_locator_alt))

        accept_delete_button.click()
        print("確認ダイアログの「削除」をクリックしました。")
        # 削除後、新しい「無題のレイヤ」が生成されるのを少し待つ
        print("新しい「無題のレイヤ」の生成を待機します...")
        time.sleep(3) # 少し長めに待つ

    except TimeoutException:
        print("エラー: 削除処理中の要素が見つかりませんでした（タイムアウト）。")
        driver.save_screenshot("delete_layer_timeout_error.png")
        raise
    except Exception as e:
        print(f"削除処理中に予期せぬエラーが発生しました: {e}")
        driver.save_screenshot("delete_layer_unexpected_error.png")
        raise

# --- Import Process ---

def click_import_button(driver):
    """Clicks the 'Import' button in the layer options menu."""
    print("--- インポートボタンクリック ---")
    wait = WebDriverWait(driver, SHORT_TIMEOUT)
    # インポートボタンのXPath (IDは非常に不安定)
    import_button_locator = (By.XPATH, '//*[@id=":1e"]/div') # :1e は非常に不安定
    # より安定しそうなXPathの例 (テキストが'インポート'の場合)
    import_button_locator_alt = (By.XPATH, "//div[contains(@class, 'goog-menuitem')][normalize-space()='インポート']")

    try:
        print("インポートボタンを検索・クリックします...")
        try:
            importElement = wait.until(EC.element_to_be_clickable(import_button_locator))
        except TimeoutException:
            print(f"代替ロケータ ({import_button_locator_alt}) でインポートボタンを試します。")
            importElement = wait.until(EC.element_to_be_clickable(import_button_locator_alt))

        importElement.click()
        print("インポートボタンをクリックしました。")
        time.sleep(2) # Picker iframeが表示されるのを少し待つ

    except TimeoutException:
        print("エラー: インポートボタンが見つかりませんでした。")
        driver.save_screenshot("import_button_error.png")
        raise
    except Exception as e:
        print(f"インポートボタンクリック中にエラー: {e}")
        driver.save_screenshot("import_button_click_error.png")
        raise


def handle_google_picker(driver, file_name):
    """Handles the Google Picker iframe for file selection."""
    print("--- Google Picker 処理 ---")
    wait = WebDriverWait(driver, SHORT_TIMEOUT)
    wait_long = WebDriverWait(driver, LONG_TIMEOUT)
    iframe_locator = (By.XPATH, "//iframe[contains(@class, 'picker-frame')]") # クラス名で試す (より安定する可能性)
    # iframe_locator_alt = (By.XPATH, "//iframe[contains(@src, '/picker?')]") # src属性で試す

    try:
        print("Google Picker iframe を特定し、切り替えます...")
        try:
             wait_long.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
        except TimeoutException:
             print(f"代替ロケータ ({iframe_locator}) で Picker iframe を試します。") # 元のコードのロケータを試す場合
             iframe_locator = (By.XPATH, "//iframe[contains(@data-postorigin, '/picker?')]")
             wait_long.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))

        print("Google Picker iframe に切り替えました。")
        time.sleep(1) # iframe内の要素読み込み待機

        # 1. 「Google ドライブ」タブをクリック (表示されるまで待機)
        gdrive_tab_locator = (By.XPATH, "(//div[@role='tab'] | //button[@role='tab'])[normalize-space()='Google ドライブ']")
        print("「Google ドライブ」タブを検索・クリックします...")
        gdrive_tab_button = wait_long.until(EC.element_to_be_clickable(gdrive_tab_locator))
        gdrive_tab_button.click()
        print("「Google ドライブ」タブをクリックしました。")
        time.sleep(1)

        # 2. ファイルを選択 (ファイル名で検索し、クリック可能な親要素を取得)
        # ファイル名を含むspan要素を見つけ、クリック可能な祖先divを探す
        print(f"ファイル '{file_name}' を検索・クリックします...")
        file_locator = (By.XPATH, f"//span[normalize-space()='{file_name}']/ancestor::div[@role='option'][1]") # role='option'を持つ祖先が良いかも
        # file_locator_alt = (By.XPATH, f"//div[contains(@class, 'drive-grid-tile')][.//span[normalize-space()='{file_name}']]") # グリッド表示の場合
        file_element_clickable = wait_long.until(EC.element_to_be_clickable(file_locator))
        file_element_clickable.click()
        print(f"ファイル '{file_name}' をクリックしました。")
        time.sleep(1) # 選択状態の反映待機

        # 3. 挿入/選択ボタンをクリック
        # ボタンのテキストは '挿入' または '選択' の可能性がある
        print("挿入/選択ボタンを検索・クリックします...")
        # insert_button_locator = (By.XPATH, "//button[.//div[normalize-space()='挿入' or normalize-space()='選択']]") # より汎用的なXPath
        insert_button_locator = (By.XPATH, "//button[.//span[normalize-space()='挿入']]") # 元のコードのXPath
        insert_button = wait_long.until(EC.element_to_be_clickable(insert_button_locator))
        # insert_button.send_keys(Keys.ENTER) # クリックが不安定な場合の代替
        insert_button.click()
        print("挿入/選択ボタンをクリックしました。")

        # 4. iframeから抜ける
        print("Picker iframe からデフォルトコンテンツに戻ります...")
        driver.switch_to.default_content()
        print("デフォルトコンテンツに戻りました。")
        time.sleep(2) # メイン画面の処理が始まるのを待つ

    except TimeoutException as picker_timeout:
        print(f"エラー: iframe 内の要素処理中にタイムアウト: {picker_timeout}")
        driver.save_screenshot("picker_element_timeout.png")
        # iframe内のHTMLを出力してみる（デバッグ用）
        try:
            driver.switch_to.frame(driver.find_element(*iframe_locator)) # 再度iframeに入る
            inner_html = driver.page_source
            print(f"--- iframe ({iframe_locator}) 内のHTML (先頭1000文字) ---")
            print(inner_html[:1000])
            print("-----------------------------")
            driver.switch_to.default_content() # 必ず抜ける
        except Exception as html_err:
            print(f"フレーム内のHTML取得中にエラー: {html_err}")
        raise
    except Exception as picker_err:
        print(f"エラー: iframe 内の処理中にエラー: {picker_err}")
        traceback.print_exc()
        driver.save_screenshot("picker_unexpected_error.png")
        raise

def configure_initial_import(driver):
    """Configures the location and title columns after initial import."""
    print("--- 初期インポート設定 (位置/タイトル) ---")
    wait_long = WebDriverWait(driver, LONG_TIMEOUT)

    # 5. 位置情報カラムの選択 & 「続行」
    try:
        print("位置情報カラムのチェックボックスを確認・選択します...")
        checkbox_labels = ['Latitude', 'Longitude'] # スプレッドシートのカラム名に合わせる
        for label in checkbox_labels:
            try:
                # チェックボックス本体を見つける (span内のspan[@role='checkbox'])
                checkbox_locator = (By.XPATH, f"//span[normalize-space()='{label}']/ancestor::div[contains(@class,'import-dialog-select-column-row')]//span[@role='checkbox']")
                checkbox_element = wait_long.until(EC.visibility_of_element_located(checkbox_locator))
                checkbox_clickable = wait_long.until(EC.element_to_be_clickable(checkbox_locator)) # クリック対象
                is_checked = checkbox_element.get_attribute('aria-checked') == 'true'
                print(f"  「{label}」: {'チェック済み' if is_checked else '未チェック'}")
                if not is_checked:
                    print(f"  「{label}」にチェックを入れます。")
                    # JavaScriptでクリックする方が安定する場合がある
                    # driver.execute_script("arguments[0].click();", checkbox_clickable)
                    checkbox_clickable.click()
                    time.sleep(0.5) # チェック反映待ち
            except Exception as chk_err:
                 # チェックボックスが見つからない場合などはエラーとせず警告に留めることも検討
                 print(f"警告: チェックボックス「{label}」の処理で問題が発生しました: {chk_err}")

        print("「続行」ボタンを検索・クリックします...")
        # ボタンのテキストは環境によって変わる可能性があるので注意
        continue_button_locator = (By.XPATH, "//button[@name='location_step_ok' or normalize-space()='続行']")
        continue_button = wait_long.until(EC.element_to_be_clickable(continue_button_locator))
        continue_button.click()
        print("「続行」ボタンをクリックしました。")
        time.sleep(2) # 次の画面表示待機
    except Exception as step5_err:
        print(f"エラー: 位置情報設定ステップでエラー: {step5_err}")
        traceback.print_exc()
        driver.save_screenshot("step5_location_error.png")
        raise

    # 6. タイトルカラムの選択
    try:
        print("タイトルカラムのラジオボタン「Spot Name」を検索・クリックします...") # スプレッドシートのカラム名に合わせる
        title_column_name = "Spot Name" # ここをファイルのカラム名に合わせる
        radio_button_locator = (By.XPATH, f"//div[@role='radio'][.//span[normalize-space()='{title_column_name}']]")
        radio_button = wait_long.until(EC.element_to_be_clickable(radio_button_locator))
        radio_button.click()
        print(f"ラジオボタン「{title_column_name}」をクリックしました。")
        time.sleep(1) # 選択反映待ち
    except Exception as step6_err:
        print(f"エラー: ラジオボタン「{title_column_name}」の処理でエラー: {step6_err}")
        traceback.print_exc()
        driver.save_screenshot("step6_title_error.png")
        raise

    # 7. 「完了」ボタンのクリック
    try:
        print("「完了」ボタンを検索・クリックします...")
        finish_button_locator = (By.XPATH, "//button[@name='name_step_ok' or normalize-space()='完了']")
        finish_button = wait_long.until(EC.element_to_be_clickable(finish_button_locator))
        finish_button.click()
        print("「完了」ボタンをクリックしました。")
    except Exception as step7_err:
        print(f"エラー: 「完了」ボタンの処理でエラー: {step7_err}")
        traceback.print_exc()
        driver.save_screenshot("step7_finish_error.png")
        raise

# --- Cleanup ---
def cleanup(driver):
    """Quits the WebDriver."""
    print("--- クリーンアップ ---")
    if driver:
        try:
            # iframe内にいる可能性を考慮してデフォルトコンテンツに戻る
            driver.switch_to.default_content()
            print("デフォルトコンテンツに戻りました。")
        except Exception as switch_err:
            # すでにデフォルトコンテンツにいる場合などはエラーになることがある
            print(f"デフォルトコンテンツへの切り替え中に軽微なエラー: {switch_err}")

        print("処理を終了します。5秒後にブラウザを閉じます。")
        time.sleep(5)
        driver.quit()
        print("ブラウザを閉じました。")

# --- Main Execution ---
if __name__ == "__main__":
    driver = None # Ensure driver is defined in the outer scope for finally
    try:
        # — 初期化 —
        config = load_config()
        driver = initialize_driver()

        # — Login —
        login(driver, config["url"], config["id"], config["password"])

        # --- メイン処理ループ (削除->インポート を考慮) ---
        # Google MyMapsの仕様: 最後のレイヤーを削除すると自動で「無題のレイヤ」が生成される。
        # したがって、削除が必要な場合は削除後、再度オプションを開いてインポートに進む。

        # — 初期動作 —
        click_layer_options(driver)

        # — 分岐1: 既存レイヤの名称を判定 —
        is_initial = check_layer_status(driver) # Trueなら初期、Falseなら既存

        if not is_initial:
            # — 削除処理 — (既存レイヤの場合)
            delete_layer(driver)
            # 削除後に新しい「無題のレイヤ」が生成されるので、再度オプションを開く必要がある
            print("レイヤー削除後、再度オプションを開いてインポートに進みます。")
            click_layer_options(driver)
            # この後、インポート処理に進む (is_initial フラグは不要になった)
            click_import_button(driver)

        else:
            # — 分岐1が無題のレイヤだった場合 (インポート処理へ) —
            click_import_button(driver)


        # --- Google Picker と 後処理 (共通) ---
        handle_google_picker(driver, config["file_name"])

        # 初期インポートの場合のみ設定が必要
        if is_initial:
             configure_initial_import(driver)
        else:
             # 置換(削除->インポート)の場合、設定ステップは通常ない
             print("レイヤー置換処理が完了しました。設定ステップはスキップされます。")

        print("--- 全ての処理が正常に完了しました ---")
        print("最終的なマップへの反映を確認します...")
        time.sleep(5) # 最終確認用待機

    except (ValueError, TimeoutException, NoSuchElementException) as e:
        print(f"\n!!!!!! スクリプト実行中にエラーが発生しました: {e} !!!!!!")
        # エラーのスタックトレースも表示するとデバッグに役立つ
        # traceback.print_exc()
    except Exception as e:
        print(f"\n!!!!!! 予期せぬエラーが発生しました: {e} !!!!!!")
        traceback.print_exc() # 予期せぬエラーの場合はトレースバックを表示
    finally:
        # — 後処理 —
        if driver:
            cleanup(driver)