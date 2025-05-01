## 環境
Python 3.11.11

## library install
pip install -r requirements.txt

.env.templateの中身を適宜変更
.env.templateを.envに名前変更
start.py実行でインポート開始

## flow
—初期化—

1. Login

—初期動作—

1. Layer Optionのクリック

—分岐1–

1. 既存レイヤの名称を判定
2. “無題のレイヤ”だとインポート処理へ
3. 別の名称だとレイヤの削除処理へ

—削除処理—

1. 削除ボタン
2. 確認画面の選択
3. —初期動作—に戻る

Google Mymapsの仕様で全てのレイヤを削除すると無題のレイヤが自動生成される。

初期動作に戻ることで実質的にレイヤの更新を行う。

—分岐1が無題のレイヤだった場合—

1. インポート処理へ