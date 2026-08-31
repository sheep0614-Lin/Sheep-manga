# 下一步

這份第一版先把最重要、最容易出錯的部分拆開：

1. 先確認 GitHub Actions 能成功編譯 Hipmh APK。
2. 再在手機 Tachimanga 實機測：
   - 首頁/熱門
   - 搜尋
   - 漫畫詳情
   - 章節列表
   - 圖片載入
3. 如果 Hipmh API 與 Happymh 不相容，再針對 m.hipmh.com 重寫 parser / API。
4. Hipmh 驗證完成後，再逐一把 `config/sources.json` 中能取得原始碼的來源納入同一簽章建置。
5. 最後才產生正式 `index.pb` 與發布 repo。

不要現在就把 repo/repo.json 貼進 Tachimanga，因為 fingerprint 還是 placeholder，
而且 repo/index.pb 尚未產生。
