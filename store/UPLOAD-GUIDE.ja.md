# Chromeウェブストアへのアップロード手順

準備日：2026年10月31日（日本時間）
対象パッケージ：Presenter Cursor v1.0.2

掲載文と画像は準備済みです。この作業では、ストアへのアップロード、開発者登録、支払い、審査申請、公開は行っていません。

## 1. 使うファイル

一式ZIP `presenter-cursor-webstore-kit-1.0.2.zip` をPCへダウンロードして展開します。

| ファイル | 使用する場所 |
| --- | --- |
| `extension-upload/presenter-cursor-chrome-1.0.2.zip` | **「新しいアイテム」でアップロードする拡張本体。ZIPのまま使用** |
| `description.ja.txt` | ストアの詳細な説明に、そのまま貼り付け |
| `listing.ja.txt` | 名前、短い説明、カテゴリ候補、各URLを確認 |
| `privacy-practices.ja.md` | 単一用途、権限、リモートコード、データ使用の申告 |
| `privacy-policy.ja.md` | 公開するプライバシーポリシー本文 |
| `reviewer-notes.en.txt` | 審査担当者向けテスト手順（英語） |
| `assets/icon-128.png` | ストアアイコン：128×128 PNG |
| `assets/screenshots/01-control-panel.png` | スクリーンショット1：1280×800 PNG |
| `assets/screenshots/02-spotlight.png` | スクリーンショット2：1280×800 PNG |
| `assets/screenshots/03-pen-annotations.png` | スクリーンショット3：1280×800 PNG |
| `assets/screenshots/04-laser-clicks-keycast.png` | スクリーンショット4：1280×800 PNG |
| `assets/screenshots/05-settings.png` | スクリーンショット5：1280×800 PNG |
| `assets/promo-small-440x280.png` | 小さいプロモーション画像：440×280 PNG、任意 |
| `assets/promo-marquee-1400x560.png` | マーキープロモーション画像：1400×560 PNG、任意 |

**一式ZIPそのものや、GitHubの「Download ZIP」で取得したソース全体を、拡張パッケージとしてアップロードしないでください。** 本体ZIPの直下にはmanifest.jsonがあります。本体ZIPに掲載文・素材・テスト用コードは含まれていません。

## 2. 開発者登録

1. 公開を管理するGoogleアカウントを決めます。
2. そのGoogleアカウントで2段階認証を有効にします。
3. [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole/)を開きます。
4. 初回は規約を確認し、開発者登録を行い、登録画面で示される一度きりの登録料を支払います。料金・通貨は画面で確認してください。
5. 開発者名と、継続して受信・確認できるメールアドレスを設定・確認します。今回のポリシー文案の提供者名は `hiroki-chii` です。別の公開名を使う場合は、ポリシー側の名前も合わせてください。

アカウントの所有者情報、事業者・トレーダーに関する設問が表示された場合は、ご本人の実際の状況に合わせて回答します。準備ファイルには氏名・住所・支払い情報を埋め込んでいません。

出典：[開発者登録](https://developer.chrome.com/docs/webstore/register)、[2段階認証の要件](https://developer.chrome.com/docs/webstore/program-policies/policies#2-step-verification)。

## 3. 本体ZIPをアップロード

1. ダッシュボードで「新しいアイテム（Add new item）」を選択します。
2. `extension-upload/presenter-cursor-chrome-1.0.2.zip` を選択し、アップロードします。
3. 解析後の「パッケージ」で、名前とバージョン `1.0.2` を確認します。
4. アップロードでmanifestのエラーが出た場合は、表示された文言を控えます。ZIPをさらにZIPで包み直す必要はありません。

出典：[初回公開の手順](https://developer.chrome.com/docs/webstore/publish)。

## 4. ストア掲載情報を入力

1. 「ストアの掲載情報（Store listing）」を開き、言語を日本語にします。
2. 名前・短い説明がmanifestから取り込まれている場合は、そのまま使用できます。`listing.ja.txt` と同じ内容です。
3. 「詳細な説明」に `description.ja.txt` の全文を貼り付けます。
4. カテゴリは仕事効率化／Productivityに相当する、機能に合う候補を選びます。実際の管理画面で名称が異なる場合はその選択肢に合わせます。
5. アイコンに `assets/icon-128.png` を登録します。
6. スクリーンショットは `01` から `05` の順で登録します。5枚とも1280×800、透明部分のないPNGです。
7. 任意で小さいプロモーション画像とマーキー画像を登録します。動画は用意していないため空欄で構いません。
8. ホームページとサポートURLを `listing.ja.txt` から登録します。所有権を認証したサイトの選択欄は、GitHubリポジトリURLを記載するホームページ欄とは別です。認証サイトがなければ任意欄は空欄のままにします。

現行の公式資料では、必須の画像は128×128のストアアイコンと最低1枚のスクリーンショットです。スクリーンショットは最大5枚で、プロモーション画像は任意です。今回の5枚は掲載用としてそのまま使用できます。

出典：[掲載情報と画像の要件](https://developer.chrome.com/docs/webstore/cws-dashboard-listing)、[画像の作成方針](https://developer.chrome.com/docs/webstore/best-listing)。

## 5. プライバシー項目を入力

`privacy-practices.ja.md` の文章と表を見ながら、次の項目を入力します。

1. 単一用途の説明。
2. storage・activeTab・scriptingの権限の理由。サイトアクセスの説明欄が出る場合はその説明も入力。
3. リモートコードは「使用しない」。
4. データ使用は、端末内で扱う画面画像・キーやポインター操作・現在のURL確認も開示します。「外部送信しない」ことを理由に、すべてを未申告にしません。項目名と説明を実際の画面で照合します。
5. 使用目的と第三者提供についての確認欄を読んで、実態に合うものにチェックします。
6. プライバシーポリシーURLを設定します。

登録用URL：

https://github.com/hiroki-chii/cursorExtensionChrome/blob/main/store/privacy-policy.ja.md

このURLはGitHubへ反映後に使用できます。ログアウトしたブラウザでも閲覧でき、提供者名・拡張名・問い合わせ先が正しいことを確認してください。本文を別の公開Webページに載せる場合は、そちらのURLでも構いません。

出典：[プライバシー項目の入力](https://developer.chrome.com/docs/webstore/cws-dashboard-privacy)、[端末内処理も開示対象](https://developer.chrome.com/docs/webstore/program-policies/user-data-faq)。

## 6. 配信と審査用情報

1. 配信範囲を選びます。一般公開したい場合はPublic／公開、URLを知っている人だけに案内したい場合はUnlisted／限定公開に相当する設定を選びます。意図する範囲をご自身で指定してください。
2. 公開する国・地域を選びます。日本語向けの掲載文を用意しています。
3. 「テスト手順（Test instructions）」に `reviewer-notes.en.txt` を貼り付けます。
4. ログインは不要です。テスト用アカウント、認証情報、追加のサーバー設定はありません。

## 7. 手元のChromeで最終確認

提出用ZIPの中身を読み込んだ、通常のChromeで確認します。

- 拡張アイコンから各ツールが起動する。
- 何も描かずにペンを終了しても、履歴が増えない。
- 下部メニューの戻す・やり直す・消去・終了が動作する。
- ズームで撮影でき、ホイールとEscで操作できる。
- ショートカットの競合はChromeの設定で変更できる。
- 全機能OFFと設定の保持が動作する。

作成環境では管理ポリシーにより拡張の実読み込みが禁止されているため、拡張APIを代替したChromiumで描画とUIを検証しています。ストア提出前に、特にactiveTab・captureVisibleTab・ネイティブのコマンド登録を、手元のChromeで確認してください。

## 8. 審査へ提出・公開

1. 保存し、管理画面に表示される未入力・検証エラーを解消します。
2. 「審査のために送信（Submit for Review）」を押します。
3. 承認後の公開方法を選びます。最初に掲載内容を確認してから公開したい場合は、自動公開を外して手動公開にします。
4. 審査結果を、ダッシュボードと登録メールで確認します。審査日数は内容によって異なります。
5. 修正依頼があれば、指摘された掲載文・申告・コードを直して再提出します。
6. 手動公開を選んだ場合は、承認後、管理画面で公開します。公式資料では承認後の公開待機期間に期限があるため、表示される期限を確認します。

公開後は、GitHubのREADMEなどにストアの実際のインストールURLを追加すると案内しやすくなります。まだストアIDは発行されていないため、準備ファイルに架空のストアURLは記載していません。

出典：[審査への提出と公開タイミング](https://developer.chrome.com/docs/webstore/publish)。

## 画像について

操作パネル・詳細設定・キャンバス効果は、本体に同梱しているHTML/CSS/JavaScriptをChromiumで実行して撮影しました。サンプルページの数値は架空のもので、拡張の性能や利用者数を示すものではありません。操作パネルの画像は実際のUIを紹介用レイアウトに配置しています。

スクリーンショット撮影時のChrome APIは専用の代替処理です。実際のストアインストールやタブ撮影APIの連携が確認済みであることを示す画像ではありません。素材生成用のソース、APIの代替処理は `source/` とリポジトリの `scripts/prepare_webstore.py` に分けてあり、アップロードする拡張本体には含めていません。

## 素材の再作成

```bash
python3 -m pip install -r tests/requirements.txt
python3 -m playwright install chromium
python3 scripts/prepare_webstore.py
```

画像を再撮影せず、既存の確認済み画像と文面から一式ZIPだけを作り直す場合：

```bash
python3 scripts/prepare_webstore.py --package-only
```
