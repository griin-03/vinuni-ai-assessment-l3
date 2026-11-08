# Đầu vào build landing

Snapshot HTML và bundle công khai dùng để chuyển nội dung sang VinAssess, được tách khỏi thư mục backup cá nhân để một lần clone mới có thể chạy `npm run content`.

Không sửa trực tiếp thư mục này cho nghiệp vụ mới. Sửa `content/vinassess.vi.json`, `content/ocean-palette.json`, `scripts/build-landing.mjs` hoặc `assets/css/vinassess.css`. Thay đổi phải được kiểm tra cả HTML và sau hydration để tránh nhãn SSR/client lệch nhau.

Nguồn: Fervid, snapshot 02/11/2026. Xem `THIRD_PARTY_NOTICES.md`; không coi snapshot này là mã nguồn React/TypeScript gốc hay tài nguyên tự do tái phân phối.
