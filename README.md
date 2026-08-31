# Sheep Manga

這是一個給 Tachimanga / Mihon 使用的個人擴展倉庫骨架。

## 目前目標

- 以 leijie115/tachimanga 的來源清單為基礎。
- 不保留舊的「嗨皮漫畫 / happymh.com」。
- 改成「嘻皮漫畫 / https://m.hipmh.com」。
- 所有由本倉庫發布的 APK 都用同一把簽章金鑰簽署。
- 產生新版 repo.json，包含 signingKeyFingerprint。

## 重要

目前這是「第一版建置骨架」，不是已完成可直接貼進 Tachimanga 的成品。
原因是新版倉庫驗證需要穩定簽章金鑰，而且嘻皮漫畫與舊 Happymh 的 API 相容性仍需要實機驗證。

## 第一次使用

1. 把此專案全部上傳到 `sheep0614-Lin/Sheep-manga`。
2. 在 GitHub Repository > Settings > Secrets and variables > Actions 新增：
   - `KEYSTORE_B64`
   - `KEY_STORE_PASSWORD`
   - `KEY_ALIAS`
   - `KEY_PASSWORD`
3. 手動執行 GitHub Actions 的 `Build Sheep Manga`。
4. 工作流程會：
   - clone 擴展原始碼 upstream
   - 將可取得的來源模組複製進建置環境
   - 將 Happymh 模組複製成 Hipmh 並修改名稱/網域
   - 編譯可成功編譯的 extension APK
   - 輸出 artifacts

## 簽章金鑰

不要每次重新產生 keystore。必須永久保存同一把金鑰，否則 signingKeyFingerprint 會改變，
Tachimanga / Mihon 會把新 APK 視為不同或不可信的簽章。

`scripts/make_keystore.sh` 提供建立第一把金鑰的範例。

## 嘻皮漫畫

現有 Happymh extension 使用 `https://m.happymh.com` 的 API。
此專案會建立 Hipmh 版本並改成 `https://m.hipmh.com`，但兩個網站不保證 API 完全相同。
所以「能編譯」不等於「已確認所有搜尋、章節、圖片都可讀」。
