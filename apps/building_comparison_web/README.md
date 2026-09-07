# 建筑图片两两对比：静态网页版

## 部署步骤

1. 在 Supabase 创建项目。
2. 执行 `supabase_schema.sql`。
3. 把 200 张建筑图片上传到 Supabase Storage，并在 `images` 表写入 `pic_id` 和 `url`。
4. 修改 `config.js` 中的 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY`。
5. 部署到 Vercel 或 Cloudflare Pages。

## 功能

- 唯一标注者 ID，退出后继续之前的进度。
- 管理员密码进入后台，查看总对比数并下载 CSV。
