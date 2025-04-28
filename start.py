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
# id,password は.envから取得

dotenv.load_dotenv()

# timeoutの設定
default_timeout = 20

id = os.getenv("GOOGLE_EMAIL")
password = os.getenv("GOOGLE_PASSWORD")
url = os.getenv("MAP_URL")
file_name = os.getenv("FILE_NAME")
options = webdriver.ChromeOptions()

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
    time.sleep(2)

    # --- 置換処理の場合 ---
    # 置換処理が必要ないパターン(初期インポート)
    initial_layer_name = "無題のレイヤ"
    is_initial_import = False # 初期インポートかどうかのフラグ
    wait = WebDriverWait(driver, 10) # 短めの待機用
    wait_long = WebDriverWait(driver, 25) # 長めの待機用 (Pickerやインポート後処理)

    print('既存レイヤーを確認します。')
    # レイヤー名要素の特定 (より安定したセレクタを検討推奨)
    layer_name_locator = (By.XPATH, '//*[@id="ly0-layer-header"]/div[2]') # 元のXPath (不安定かも)
    # layer_name_locator_alt = (By.XPATH, "//div[@class='ZdMwHb-r4nke-haAclf']") # こちらがレイヤー名か要確認

    try:
        layer_name_element = wait.until(EC.visibility_of_element_located(layer_name_locator))
        layer_name = layer_name_element.text.strip() # 前後の空白を除去
        print(f"現在のレイヤー名: 「{layer_name}」")

        if layer_name == initial_layer_name:
            print("初期インポート処理を実行します。")
            is_initial_import = True

            print("インポートボタンをクリックします...")
            # インポートボタンのXPathも変わりやすい可能性あり。テキストなどで指定できないか検討。
            import_button_locator = (By.XPATH, '//*[@id=":1e"]/div') # :1e のようなIDは非常に不安定
            # より安定しそうなXPathの例 (テキストが'インポート'の場合)
            import_button_locator_alt = (By.XPATH, "//div[contains(@class, 'goog-menuitem') and contains(., 'インポート')]")

            try:
                importElement = wait.until(EC.element_to_be_clickable(import_button_locator))
            except TimeoutException:
                print(f"代替ロケータ ({import_button_locator_alt}) でインポートボタンが見つかりませんでした。元のロケータを試します。")
                importElement = wait.until(EC.element_to_be_clickable(import_button_locator_alt)) # 元のロケータ

            importElement.click()
            print("インポートボタンをクリックしました。")
            time.sleep(3) # Picker iframeが表示されるのを少し待つ


        else:
            print("既存レイヤーへの置換処理を実行します。")
            is_initial_import = False
    except TimeoutException:
         print("エラー: レイヤー名要素が見つかりませんでした。XPathを確認してください。")
         driver.save_screenshot("layer_name_not_found_error.png")
         raise

    # --- 置換処理の場合のみ、メニュー項目「すべてのアイテムを置換」をクリック ---
    if not is_initial_import:
        print("置換メニューから「すべてのアイテムを置換」を選択します...")
        # 提供されたHTML要素からXPathを作成

        # TODO: ここのXPATH指定でコケる
        replace_menu_item_locator = (By.XPATH, '/html/body/div[24]/div[1]/div')
        try:
            # メニュー項目が表示されるまで少し待つ
            replace_menu_item = wait.until(EC.element_to_be_clickable(replace_menu_item_locator))
            replace_menu_item.click()
            print("「すべてのアイテムを置換」を選択しました。")
        except TimeoutException:
            print("エラー: 置換メニュー項目「すべてのアイテムを置換」が見つかりませんでした。")
            driver.save_screenshot("replace_menu_item_error.png")
            raise
        except Exception as menu_err:
             print(f"置換メニュー項目のクリック中にエラー: {menu_err}")
             driver.save_screenshot("replace_menu_item_click_error.png")
             raise



    # --- Google Picker iframe の処理 (共通処理) ---
    time.sleep(3) # Picker iframe表示待機
    print("Google Picker iframe を特定します...")
    # iframe の特定 (複数のロケータを試す場合は前回のコードを参照)
    iframe_locator = (By.XPATH, "//iframe[contains(@data-postorigin, '/picker?')]")

    print(f"Google Picker iframe ({iframe_locator}) を待機し、切り替えます...")
    try:
        wait_long.until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
        print("Google Picker iframe に切り替えました。")
    except TimeoutException:
        print(f"エラー: Google Picker iframe ({iframe_locator}) が見つかりませんでした。")
        driver.save_screenshot("picker_iframe_not_found.png")
        raise

    # --- iframe内処理: ファイル選択 -> 挿入 (共通処理) ---
    try:
        print(f"iframe ({iframe_locator}) 内の処理を開始します...")
        # 1. 「Google ドライブ」タブをクリック
        gdrive_tab_locator = (By.XPATH, "(//div[@role='tab'] | //button[@role='tab'])[contains(., 'Google ドライブ')]")
        gdrive_tab_button = wait_long.until(EC.element_to_be_clickable(gdrive_tab_locator))
        gdrive_tab_button.click()
        print("「Google ドライブ」タブをクリックしました。")
        time.sleep(1)

        # 2. ファイルを選択
        file_locator = (By.XPATH, f"//span[normalize-space()='{file_name}']/ancestor::div[@aria-labelledby][1]")
        file_element_clickable = wait_long.until(EC.element_to_be_clickable(file_locator))
        file_element_clickable.click()
        print(f"ファイル '{file_name}' をクリックしました。")
        time.sleep(2)

        # 3. 挿入ボタンをクリック
        insert_button_locator = (By.XPATH, "//button[.//span[normalize-space()='挿入']]")
        insert_button = wait_long.until(EC.element_to_be_clickable(insert_button_locator))
        insert_button.click()
        print("挿入ボタンをクリックしました。")

        # 4. iframeから抜ける
        print("Picker iframe からデフォルトコンテンツに戻ります...")
        driver.switch_to.default_content()
        print("デフォルトコンテンツに戻りました。")
        time.sleep(2)
    
    except TimeoutException as picker_timeout:
        print(f"エラー: iframe ({iframe_locator}) 内の要素処理中にタイムアウト: {picker_timeout}")
        driver.save_screenshot("picker_element_timeout.png")
        raise
    except Exception as picker_err:
        print(f"エラー: iframe ({iframe_locator}) 内の処理中にエラー: {picker_err}")
        traceback.print_exc()
        driver.save_screenshot("picker_unexpected_error.png")
        raise



    # --- インポート後の処理分岐 ---
    if is_initial_import:

        # --- 初期インポートの場合: 位置/タイトル設定画面の処理 ---
        print("初期インポートのため、位置情報とタイトルの設定に進みます。")

        # 5. チェックボックス確認・選択 & 「続行」ボタンクリック
        try:
            print("位置情報カラムのチェックボックスを確認・選択します...")
            checkbox_labels = ['Latitude', 'Longitude']
            for label in checkbox_labels:
                # (チェックボックス処理は前回の回答と同じ)
                try:
                    checkbox_locator = (By.XPATH, f"//span[normalize-space()='{label}']/preceding-sibling::span[1]/span[@role='checkbox']")
                    checkbox_element = wait_long.until(EC.visibility_of_element_located(checkbox_locator))
                    checkbox_clickable = wait_long.until(EC.element_to_be_clickable(checkbox_locator))
                    is_checked = checkbox_element.get_attribute('aria-checked') == 'true'
                    print(f"  「{label}」: {'チェック済み' if is_checked else '未チェック'}")
                    if not is_checked:
                        print(f"  「{label}」にチェックを入れます。")
                        checkbox_clickable.click()
                        time.sleep(0.5)
                except Exception as chk_err:
                     print(f"警告: チェックボックス「{label}」の処理でエラー: {chk_err}") # エラーでも続行する可能性考慮

            print("「続行」ボタンを検索・クリックします...")
            time.sleep(2)
            continue_button_locator = (By.XPATH, "//button[@name='location_step_ok' or normalize-space()='続行']")
            continue_button = wait_long.until(EC.element_to_be_clickable(continue_button_locator))
            continue_button.click()
            print("「続行」ボタンをクリックしました。")
            time.sleep(2)
        except Exception as step5_err:
            print(f"エラー: 位置情報設定ステップでエラー: {step5_err}")
            traceback.print_exc()
            driver.save_screenshot("step5_error.png")
            raise

        # 6. 「Spot Name」ラジオボタンの選択
        try:
            print("ラジオボタン「Spot Name」を検索・クリックします...")
            radio_button_locator = (By.XPATH, f"//div[@role='radio'][.//span[normalize-space()='Spot Name']]")
            radio_button = wait_long.until(EC.element_to_be_clickable(radio_button_locator))
            radio_button.click()
            print("ラジオボタン「Spot Name」をクリックしました。")
            time.sleep(2)
        except Exception as step6_err:
            print(f"エラー: ラジオボタン「Spot Name」の処理でエラー: {step6_err}")
            traceback.print_exc()
            driver.save_screenshot("step6_error.png")
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
            driver.save_screenshot("step7_error.png")
            raise

    else: # is_initial_import が False (置換処理) の場合
        print("置換処理が完了しました。位置・タイトルの設定はスキップされます。")
        # 置換の場合、特に後続のクリック操作は不要と想定
        # もし置換後にも完了ダイアログ等が出る場合は、ここに追加

    # --- すべての処理が完了 ---
    print("インポート（または置換）処理が正常に完了しました。")
    print("最終的なマップへの反映を待機します...")
    time.sleep(5) # 最終確認用待機


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