# Báo cáo: Animation chuyển tab — hiện trạng & đề xuất

**Ngày:** 2026-06-12 · **Phạm vi:** Flutter `attendance_scheduler_app/lib/design_system/`

## TL;DR
Cơ chế chuyển tab KHÔNG hỏng — đang dùng `PageTransitionSwitcher` + `SharedAxisTransition`
(Material motion), duration lấy từ token. Cảm giác "tệ" đến từ **3 nguyên nhân**:
1. `SharedAxisTransition.horizontal` **scale + mờ + trượt** cả trang → trên desktop trang lớn
   thấy "phóng to giật" (zoomy), không phải trượt mượt.
2. **KHÔNG có token cho Curve/Easing** → mỗi nơi một kiểu chuyển động ("không theo quy củ").
3. **Không có `RepaintBoundary`** (0 cái toàn app) → cả cây widget repaint mỗi frame; các
   `DsSurface` đều có `boxShadow` → tính lại shadow mỗi frame khi scale → góp phần giật.

## Hiện trạng (đã xác minh trong code)

### Tab transition — `navigation.dart:140-191`
- `_DsDirectionalTabTransition`: `PageTransitionSwitcher(duration: DsDuration.navigation /*320ms*/, reverse)`
  + `SharedAxisTransition(type: horizontal)`. Có logic hướng (chọn tab thấp hơn → trượt phải→trái).
- Đánh giá: bài bản, nhưng `horizontal` = fade-through **kèm scale 0.8→1.0**. Với side-nav desktop,
  hiệu ứng scale làm nội dung "nảy/phóng", cảm giác rẻ tiền.

### Token chuyển động — `tokens.dart:62-67`
- CÓ `DsDuration`: fast 120 / base 160 / medium 220 / slow 280 / navigation 320.
- **THIẾU hoàn toàn token Curve/Easing.** Hệ quả: 3 "ngôn ngữ chuyển động" rời rạc:
  | Nơi | Duration | Curve |
  |-----|----------|-------|
  | Chuyển trang (SharedAxis) | 320ms (token) | curve mặc định Material (ẩn) |
  | Pill nav bar (`liquid_navigation_native.dart:36-37`) | 320ms (token) | `Curves.easeOutCubic` |
  | Skeleton/shimmer (`states.dart:46`) | **900ms hardcode** | mặc định |
  | Khác (`components.dart:747-748`) | **8s/4s hardcode** | — |
- Nav pill (easeOutCubic) và trang (SharedAxis) khởi động cùng lúc nhưng **khác curve** → lệch nhịp.

### Hiệu năng
- `grep RepaintBoundary` = **0**. Mọi `DsSurface` có `boxShadow` (`components.dart:375`).
- Khi SharedAxis scale toàn trang, các card đổ bóng bị recompute → jank tăng theo số card.
- Lưu ý: `DsSurface` là Container thường (KHÔNG BackdropFilter) → blur KHÔNG phải thủ phạm.
  BackdropFilter chỉ nằm ở `DsLiquidGlassSurface` (dùng 0 lần trong trang) và `LiquidGlassBar` (nav mobile).

## Đề xuất (ưu tiên cao → thấp)

**A. Thêm token Easing — `DsCurve`** (gốc của "quy củ"): 1 nguồn chân lý.
```dart
abstract final class DsCurve {
  static const standard   = Cubic(0.2, 0.0, 0.0, 1.0); // emphasized-decelerate
  static const emphasized = Cubic(0.05, 0.7, 0.1, 1.0);
  static const exit       = Cubic(0.4, 0.0, 1.0, 1.0);
}
```

**B. Đổi transition trang** từ SharedAxis (scale-zoom) sang **trượt-ngang + mờ nhẹ, KHÔNG scale**
(giữ logic hướng đã có), dùng `DsCurve.standard`. Mượt và "có chủ đích" hơn cho side-nav desktop.
Phương án thay thế nếu vẫn muốn Material: `FadeThroughTransition` (mờ + scale rất nhẹ).

**C. `RepaintBoundary`** bọc child trang trong `_DsDirectionalTabTransition` (và cân nhắc mỗi `DsSurface`)
→ cắt repaint thừa, giảm chi phí shadow mỗi frame.

**D. Đồng bộ nav pill** dùng cùng `DsCurve.standard` + `DsDuration.navigation` như transition trang
→ pill và nội dung di chuyển cùng nhịp.

**E. Chuẩn hóa duration hardcode**: `states.dart` 900ms → token mới (vd `DsDuration.shimmer`).
(Network timeout ở `api_client.dart` giữ nguyên — không phải animation.)

## Tác động
- Sửa trong design_system (tập trung), không đụng logic nghiệp vụ.
- Golden test schedule/login sẽ cần regenerate (transition khác → snapshot khác). i18n không ảnh hưởng.
- Rủi ro thấp; KISS — chủ yếu thêm token + đổi 1 transition builder + bọc RepaintBoundary.

## Câu hỏi cần chốt
1. Kiểu chuyển động trang muốn: **(a) trượt-ngang + mờ** (khuyến nghị, desktop), **(b) chỉ cross-fade**
   (tối giản nhất), hay **(c) giữ Material FadeThrough**?
2. Có muốn mình làm luôn A–E (kèm regenerate golden + chạy test) không, hay chỉ làm A+B trước?
