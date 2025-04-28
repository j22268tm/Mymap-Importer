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

    # --- 置換処理の場合 ---
    # 置換処理が必要ないパターン(初期インポート)
    initial_layer_name = "無題のレイヤ"

    print('既存レイヤーを確認します。')
    check_layer_name = (By.XPATH,'//*[@id="ly0-layer-header"]/div[2]')

    try:
        layer_name_element = wait.until(EC.visibility_of_element_located(check_layer_name))
        layer_name = layer_name_element.text
        print(f"レイヤー名: {layer_name}")

        if layer_name == initial_layer_name:
            print("置換処理は不要です。")
        else:
            print("置換処理を実行します。")
            # TODO: 置換処理のコードをここに追加
            # 例: レイヤー名を変更する、既存のレイヤーを削除するなど
    except TimeoutException:
        print("レイヤー名の取得に失敗しました。レイヤーが存在しないか、XPathが変更された可能性があります。")
        # スクリーンショットを撮るなどのデバッグ処理を追加
        driver.save_screenshot("layer_name_error.png")
        raise
    print("インポートボタンをクリックします...")
    # インポートボタンのXPathも変わりやすい可能性あり。テキストなどで指定できないか検討。
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
    iframe_locator = (By.XPATH, "//iframe[contains(@data-postorigin, '/picker?')]")

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
            print("挿入ボタンをクリックしました。")
            try:
                # 挿入後、Picker iframe から抜ける処理を追加
                print("Picker iframe からデフォルトコンテンツに戻ります...")
                driver.switch_to.default_content()
                print("デフォルトコンテンツに戻りました。")

            except Exception as click_err:
                # ... (挿入ボタンクリックのエラー処理) ...
                print(f"挿入ボタンのクリック中にエラーが発生しました: {click_err}")
                # エラーが発生した場合でも、finallyブロックで default_content に戻る試みが行われる
                raise # エラーを再発生させる

            print("ファイルの選択・挿入処理が完了しました。") # このログは default_content に戻った後に出力される
            print("ファイルインポート処理の完了を待機しています...")
            # 次のステップ（続行ボタンの待機）に任せるため、ここでの長い固定待機は不要なことが多い

    # --- 5. チェックボックス確認・選択 & 「続行」ボタンクリック (位置情報カラム設定) ---
            try:
                print("位置情報カラムのチェックボックスを確認・選択します...")

                # チェックボックス処理を関数化しても良いが、ここでは直接記述
                checkbox_labels = ['Latitude', 'Longitude']
                for label in checkbox_labels:
                    try:
                        print(f"  チェックボックス「{label}」を探しています...")
                        # ラベルテキスト(span)を探し、その前にある兄弟(span)の中のチェックボックス(span @role='checkbox')を特定
                        checkbox_locator = (By.XPATH, f"//span[normalize-space()='{label}']/preceding-sibling::span//span[@role='checkbox']")
                        # チェックボックス要素が表示され、クリック可能になるまで待機
                        checkbox_element = wait_long.until(EC.visibility_of_element_located(checkbox_locator))
                        checkbox_clickable = wait_long.until(EC.element_to_be_clickable(checkbox_locator))

                        # 現在のチェック状態を取得 (aria-checked属性を確認)
                        is_checked = checkbox_element.get_attribute('aria-checked') == 'true'
                        print(f"  「{label}」の現在の状態: {'チェック済み' if is_checked else '未チェック'}")

                        # もしチェックされていなければクリック
                        if not is_checked:
                            print(f"  「{label}」にチェックを入れます。")
                            try:
                                checkbox_clickable.click()

                            except Exception as chk_click_err:
                                print(f"  「{label}」チェックボックスの通常のクリックに失敗 ({chk_click_err})。JavaScriptで試みます。")
                                driver.execute_script("arguments[0].click();", checkbox_clickable)
                                time.sleep(0.5) # JS実行後の反映を待つ
                        else:
                            print(f"  「{label}」は既にチェック済みのため、操作はスキップします。")

                    except TimeoutException:
                        print(f"エラー: チェックボックス「{label}」が見つかりませんでした（タイムアウト）。CSVのカラム名や画面構成を確認してください。")
                        driver.save_screenshot(f"{label}_checkbox_timeout.png")
                        raise # エラーを上位に伝播
                    except Exception as chk_err:
                        print(f"チェックボックス「{label}」の処理中にエラーが発生しました: {chk_err}")
                        driver.save_screenshot(f"{label}_checkbox_error.png")
                        raise # エラーを上位に伝播

                # --- すべてのチェックボックス操作後、「続行」ボタンをクリック ---
                print("「続行」ボタン (位置情報設定) を検索・待機しています...")
                continue_button_locator = (By.XPATH, "//button[@name='location_step_ok' or normalize-space()='続行']")
                continue_button = wait_long.until(EC.element_to_be_clickable(continue_button_locator))
                print("「続行」ボタンが見つかりました。クリックします。")

                try:
                    continue_button.click()
                except Exception as cont_click_err:
                    print(f"続行ボタンの通常のクリックに失敗 ({cont_click_err})。JavaScriptで試みます。")
                    driver.execute_script("arguments[0].click();", continue_button)

                print("「続行」ボタンをクリックしました。")
                print("タイトル列選択画面の表示を待っています...")
                time.sleep(1) # 次画面の要素待機（より良いのは次の画面の要素を待つこと）

            except TimeoutException as step5_timeout:
                # チェックボックスまたは続行ボタンでタイムアウトした場合
                print(f"エラー: 位置情報設定ステップで要素が見つかりませんでした（タイムアウト）。 {step5_timeout}")
                # スクリーンショットは各箇所で撮っているのでここでは省略可
                raise
            except Exception as step5_err:
                # チェックボックスまたは続行ボタンで予期せぬエラーが発生した場合
                print(f"位置情報設定ステップで予期せぬエラーが発生しました: {step5_err}")
                traceback.print_exc() # エラー詳細表示
                # スクリーンショットは各箇所で撮っているのでここでは省略可
                raise

                # --- 6. 「Spot Name」ラジオボタンの選択 (マーカータイトル列設定) ---
            try:
                print("ラジオボタン「Spot Name」を検索・待機しています...")
                # ラジオボタンの特定: role='radio' を持ち、内部のspanテキストが 'Spot Name' のものを探す (推奨)
                radio_button_locator = (By.XPATH, f"//div[@role='radio'][.//span[normalize-space()='Spot Name']]")

                radio_button = wait_long.until(EC.element_to_be_clickable(radio_button_locator))
                print("ラジオボタン「Spot Name」が見つかりました。クリックします。")

                # クリックを実行 (JavaScriptクリックが必要な場合もある)
                try:
                    radio_button.click()
                except Exception as radio_click_err:
                    print(f"ラジオボタンの通常のクリックに失敗 ({radio_click_err})。JavaScriptで試みます。")
                    driver.execute_script("arguments[0].click();", radio_button)

                print("ラジオボタン「Spot Name」をクリックしました。")
                time.sleep(0.5) # クリック反映を少し待つ

            except TimeoutException:
                print("エラー: ラジオボタン「Spot Name」が見つかりませんでした（タイムアウト）。CSVのカラム名や画面構成を確認してください。")
                driver.save_screenshot("radio_button_timeout.png")
                raise
            except Exception as radio_err:
                print(f"ラジオボタン「Spot Name」のクリック中にエラーが発生しました: {radio_err}")
                driver.save_screenshot("radio_button_error.png")
                raise # エラーを再発生させる


            # --- 7. 「完了」ボタンのクリック ---
            try:
                print("「完了」ボタン (タイトル設定完了) を検索・待機しています...")
                # name属性 または テキスト '完了' でボタンを特定
                finish_button_locator = (By.XPATH, "//button[@name='name_step_ok' or normalize-space()='完了']")
                finish_button = wait_long.until(EC.element_to_be_clickable(finish_button_locator))
                print("「完了」ボタンが見つかりました。クリックします。")

                # クリックを実行
                try:
                    finish_button.click()
                except Exception as finish_click_err:
                    print(f"完了ボタンの通常のクリックに失敗 ({finish_click_err})。JavaScriptで試みます。")
                    driver.execute_script("arguments[0].click();", finish_button)

                print("「完了」ボタンをクリックしました。")
                # これでインポートと設定の主要な自動操作は完了
                print("インポートと設定が完了しました。")
                # 完了後の状態確認や待機 (例: マップにデータが反映されるまで)
                print("最終的なマップへの反映を待機します...")
                time.sleep(5) # 必要に応じて適切な待機処理を追加

            except TimeoutException:
                print("エラー: 「完了」ボタンが見つかりませんでした（タイムアウト）。画面構成を確認してください。")
                driver.save_screenshot("finish_button_timeout.png")
                raise
            except Exception as finish_err:
                print(f"「完了」ボタンのクリック中にエラーが発生しました: {finish_err}")
                driver.save_screenshot("finish_button_error.png")
                raise



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