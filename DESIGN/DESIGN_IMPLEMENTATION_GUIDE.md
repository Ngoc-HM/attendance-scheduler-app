# Design Implementation Guide

## Mục đích

File này là **hướng dẫn triển khai** cho design spec `DESIGN_GUI.md`.  
Nó trả lời câu hỏi: **"Làm sao để implement đúng spec vào code?"**

Trước khi chỉnh sửa UI bất kỳ file nào trong `app/dashboard/user/`, đọc file này trước.

---

## 1. Cách đọc Design Spec

**Priority order:**

1. `DESIGN/UI_STYLE_GUIDE.md` — Tinh thần thiết kế, nguyên tắc bắt buộc
2. `DESIGN/DESIGN_GUI.md` — Hard token definitions (colors, spacing, radius, etc.)
3. `DESIGN/DESIGN_IMPLEMENTATION_GUIDE.md` (file này) — Cách implement tokens vào Tailwind CSS v4

---

## 2. Tech Stack hiện tại

- **Framework:** Next.js 16 (App Router), React 19
- **Styling:** Tailwind CSS v4 (CSS `@import "tailwindcss"` — KHÔNG có `tailwind.config.ts`)
- **Icons:** Lucide React
- **State:** React Hook Form, Zod
- **Animations:** Framer Motion (dùng có chọn lọc)

**Điều quan trọng:** Tailwind v4 dùng CSS `@theme inline` thay vì `tailwind.config.ts`. Tất cả design tokens phải được khai báo dưới dạng CSS custom properties trong `app/globals.css`.

---

## 3. Màu sắc — Token Mapping

### Approved Color Palette (dùng trực tiếp với Tailwind classes)

| Intent | Tailwind Class | Hex | Usage |
|--------|---------------|-----|-------|
| Background | `slate-50` hoặc `gray-50` | `#F8FAFC` | App canvas |
| Surface/Cards | `white` hoặc `slate-50` | `#FFFFFF` | Cards, panels |
| Primary Action | `sky-600` | `#0284C7` | Buttons, links, active |
| Primary Hover | `sky-700` | `#0369A1` | Hover state |
| Primary Soft | `sky-50` | `#F0F9FF` | Selected bg, soft emphasis |
| Text Primary | `slate-900` | `#0F172A` | Main text |
| Text Secondary | `slate-600` | `#475569` | Supporting text |
| Text Muted | `slate-500` | `#64748B` | Placeholders, hints |
| Border Default | `slate-200` | `#E2E8F0` | Standard borders |
| Border Strong | `slate-300` | `#CBD5E1` | Active borders |
| Success | `emerald-600` | `#059669` | Positive states |
| Success Soft | `emerald-50` | `#ECFDF5` | Positive backgrounds |
| Warning | `amber-500` | `#F59E0B` | Warning states (use sparingly) |
| Warning Soft | `amber-50` | `#FFFBEB` | Warning backgrounds |
| Danger | `rose-600` | `#E11D48` | Errors, destructive |
| Danger Soft | `rose-50` | `#FFF1F2` | Error backgrounds |
| Info | `sky-600` | `#0284C7` | Informational |

### Màu KHÔNG ĐƯỢC DÙNG

| Color | Lý do |
|-------|-------|
| `purple-*` | AI-style, không phù hợp enterprise |
| `violet-*` | AI-style, không phù hợp enterprise |
| `indigo-*` | Gần AI-style, không trong spec |
| `orange-*` | Chỉ dùng cho accent khi cần, không phải primary |
| `green-500` (flat) | Chỉ dùng `emerald-500` |
| `blue-500` (flat) | Dùng `sky-500` hoặc `sky-600` |
| `bg-gradient-to-*` | **Cấm tuyệt đối** — vi phạm spec |
| `bg-[linear-gradient(...)]` | **Cấm tuyệt đối** |
| `text-black` trên nền trắng | Dùng `text-slate-900` |
| `text-white` trên nền màu không phải trắng | OK khi button màu đậm, KHÔNG OK trên card |

### Avatar / Decorative Circles

Dùng **flat solid color** thay vì gradient:

```tsx
// ❌ SAI - gradient avatar
<div className="bg-[linear-gradient(135deg,#0284c7_0%,#1d4ed8_100%)]">

// ✅ ĐÚNG - solid color
<div className="bg-sky-600">
// hoặc bg-slate-900 cho dark variant
```

---

## 4. Border Radius — ĐÚNG và SAI

**Scale được phép:** 6px / 10px / 12px / 16px / 20px / 9999px (full)

| Token | Tailwind Class | Value | Usage |
|-------|---------------|-------|-------|
| `radius.sm` | `rounded-sm` | 6px | Badges, chips |
| `radius.md` | `rounded` hoặc `rounded-md` | 10px | Buttons, inputs |
| `radius.lg` | `rounded-lg` | 12px | Cards, menus |
| `radius.xl` | `rounded-xl` | 16px | Panels, modals |
| `radius.2xl` | `rounded-2xl` | 20px | Major blocks |
| `radius.full` | `rounded-full` | 9999px | Avatar, pill (dùng hạn chế) |

### Những giá trị CẤM

- `rounded-[28px]` — 28px không có trong scale
- `rounded-[24px]` — 24px không có trong scale
- `rounded-[32px]` — 32px không có trong scale
- `rounded-[20px]` — 20px không có trong scale (dùng `rounded-2xl`)
- `rounded-full` — Chỉ khi pill shape thật sự cần thiết, không phải button

### Ví dụ đúng

```tsx
// Card
<div className="rounded-lg bg-white border border-slate-200 shadow-sm">

// Button
<button className="h-11 px-4 rounded-lg bg-sky-600 text-white">

// Input
<input className="h-11 rounded-md border border-slate-200">

// Modal
<div className="rounded-xl bg-white shadow-xl">

// Badge
<span className="rounded-sm px-2 py-0.5 text-xs font-medium bg-sky-50 text-sky-700">
```

---

## 5. Typography — Scale chuẩn

| Level | Font Size | Tailwind | Weight | Usage |
|-------|-----------|---------|--------|-------|
| H1 | 30px | `text-[30px]` hoặc `text-3xl` | 700 | Page titles |
| H2 | 24px | `text-2xl` | 600 | Section headings |
| H3 | 20px | `text-xl` | 600 | Card titles |
| Body | 16px | `text-base` | 400 | Default |
| Body Small | 14px | `text-sm` | 400 | Table cells, metadata |
| Caption | 12px | `text-xs` | 500 | Labels, hints |

**Quy tắc:**
- Không dùng `text-[36px]` cho heading
- Không dùng `text-[28px]` cho heading
- Không dùng `text-4xl` hoặc larger trong nội dung page
- `text-black` / `text-white` là **cấm** — dùng `text-slate-900`, `text-white`

---

## 6. Control Heights

| Control | Tailwind | Height |
|---------|----------|--------|
| Input / Select | `h-11` | 44px (default touch) |
| Button (md) | `h-10` | 40px |
| Button (lg) | `h-11` | 44px |
| Button (sm) | `h-8` | 32px |
| Dense/compact | `h-9` | 36px (chỉ khi cần thiết) |

**Sai phạm thường gặp:**
- `h-12` (48px) cho inputs → nên là `h-11` (44px)
- `h-12` (48px) cho buttons → nên là `h-10` hoặc `h-11`

---

## 7. Shadows — ĐÚNG và SAI

**Dùng Tailwind shadow utilities:**
- `shadow-sm` — Cards nhẹ, hover states
- `shadow-md` — Modals, drawers
- `shadow-lg` — **Chỉ khi cần emphasis thật sự**, KHÔNG phải default

**KHÔNG DÙNG:**
- `shadow-[0_20px_60px_-45px_rgba(15,23,42,0.35)]` — Quá nặng, không trong spec
- `shadow-2xl` — Trừ khi modal/drawer cần emphasis
- Colored shadows, glow effects

---

## 8. Audit Results — Violations đã tìm thấy

Dưới đây là violations cụ thể trong từng file (sau audit toàn bộ 20+ user pages).

### CRITICAL — Cần sửa ngay

| File | Violations | Fix |
|------|-----------|-----|
| `app/dashboard/user/page.tsx` | Gradient KPI cards (`bg-gradient-to-br from-green-500 to-green-600`, `from-purple-500 to-purple-600`...) | Thay bằng flat solid colors với `bg-emerald-50` surface, icon màu accent |
| `app/dashboard/user/project-init/page.tsx` | `rounded-[28px]` (nhiều chỗ), `shadow-[0_20px_60px_-45px_rgba(15,23,42,0.35)]`, `bg-[linear-gradient(135deg,#0284c7_0%,#1d4ed8_100%)]`, `bg-slate-950/55` backdrop | Rounded-xl (16px), shadow-md, solid bg-sky-600, backdrop overlay dùng `bg-slate-900/50` |
| `app/dashboard/user/spaces/page.tsx` | Pervasive `bg-green-600`/`bg-green-50`/`text-green-700` thay vì spec palette | Thay bằng `bg-sky-600`/`bg-sky-50`/`text-sky-700` |
| `app/dashboard/user/project-init/[id]/page.tsx` | `rounded-[28px]`, `rounded-[24px]`, heavy shadow | Radius standard, shadow-sm |

### MAJOR — Cần sửa

| File | Violations | Fix |
|------|-----------|-----|
| `app/dashboard/user/director-projects/page.tsx` | Arbitrary blue/emerald/amber/rose/purple bg/text trong status badges và section headers | Dùng status color mapping chuẩn |
| `app/dashboard/user/projects/[id]/page.tsx` | `rounded-[32px]`, `text-[36px]` title, `shadow-2xl` modal | Rounded-lg/xl, `text-2xl`, shadow-md |
| `app/dashboard/user/projects/page.tsx` | h2 `text-3xl` (30px), indigo/violet/teal/purple palette | `text-2xl`, dùng sky/slate palette |
| `app/dashboard/user/project-init/[id]/supplement/page.tsx` | Purple/orange palette | Dùng sky/slate palette |

### MINOR — Nên sửa

| File | Violations | Fix |
|------|-----------|-----|
| `app/dashboard/user/ai/page.tsx` | H1 `text-xl` (18px), `text-black` | `text-[30px]` cho h1, `text-slate-900` |
| `app/dashboard/user/chat/page.tsx` | H1 `text-xl` | `text-[30px]` cho h1 |
| `app/dashboard/user/company-projects/page.tsx` | `text-black` pervasive | `text-slate-900` |
| `app/dashboard/user/company-structure/page.tsx` | `text-green-600` (không phải spec green) | `text-emerald-600` |
| `app/dashboard/user/customers/page.tsx` | `rounded-full` badge, blue-50/blue-100 ngoài spec | `rounded-sm` badge, sky-50 |
| `app/dashboard/user/documents/page.tsx` | `text-black` pervasive | `text-slate-900` |
| `app/dashboard/user/payments/page.tsx` | `text-black` pervasive | `text-slate-900` |
| `app/dashboard/user/reports/page.tsx` | `text-black` | `text-slate-900` |
| `app/dashboard/user/settings/page.tsx` | `h-12` inputs, `rounded-[24px]` | `h-11`, radius chuẩn |
| `app/dashboard/user/consortium/page.tsx` | Nearly clean — minor shadow on modal | OK, chỉ cần theo dõi |
| `app/dashboard/user/meeting-rooms/page.tsx` | Cleanest page — ~85% compliant | Giữ nguyên, refactor nhỏ nếu cần |

### CLEAN — Không cần sửa

- `app/dashboard/user/project-init/[id]/page.tsx` (redirect page — không có UI)

---

## 9. Status Color Mapping chuẩn

Dùng mapping này cho tất cả status badges trong hệ thống:

| Status | Badge Background | Badge Text | Border |
|--------|-----------------|-----------|--------|
| `initiated` | `bg-slate-100` | `text-slate-700` | `ring-slate-200` |
| `planned` | `bg-sky-100` | `text-sky-700` | `ring-sky-200` |
| `in_progress` / `executed` | `bg-sky-100` | `text-sky-700` | `ring-sky-200` |
| `monitored` | `bg-sky-100` | `text-sky-700` | `ring-sky-200` |
| `review` | `bg-amber-100` | `text-amber-700` | `ring-amber-200` |
| `on_hold` | `bg-slate-100` | `text-slate-600` | `ring-slate-200` |
| `completed` | `bg-emerald-100` | `text-emerald-700` | `ring-emerald-200` |
| `cancelled` | `bg-rose-100` | `text-rose-700` | `ring-rose-200` |
| `approved` | `bg-emerald-100` | `text-emerald-700` | `ring-emerald-200` |
| `rejected` | `bg-rose-100` | `text-rose-700` | `ring-rose-200` |
| `pending` | `bg-amber-100` | `text-amber-700` | `ring-amber-200` |

---

## 10. Overlay / Backdrop chuẩn

```tsx
// ❌ SAI — dùng arbitrary value
<div className="bg-slate-950/55">
<div className="bg-black/50">
<div className="bg-[rgba(0,0,0,0.5)]">

// ✅ ĐÚNG — dùng Tailwind arbitrary với spec palette
<div className="bg-slate-900/50">
<div className="bg-slate-900/40">

// Với backdrop blur
<div className="bg-slate-900/40 backdrop-blur-sm">
```

---

## 11. Quick Reference Checklist

### Trước khi commit UI change, kiểm tra:

**Colors:**
- [ ] Không có `bg-gradient-to-*` hoặc `bg-[linear-gradient(...)]`
- [ ] Không dùng `purple-*`, `violet-*`, `indigo-*`, `orange-*` (trừ khi spec cho phép)
- [ ] Text trên nền trắng dùng `text-slate-900`, không phải `text-black`
- [ ] Text trên nền tối dùng `text-white`

**Border Radius:**
- [ ] Không có `rounded-[xxpx]` với giá trị không phải 6/10/12/16/20/9999
- [ ] Buttons dùng `rounded-lg` (12px) hoặc `rounded-md` (10px)
- [ ] Cards dùng `rounded-lg` (12px) hoặc `rounded-xl` (16px)
- [ ] Modals dùng `rounded-xl` (16px)

**Typography:**
- [ ] H1 page title = `text-[30px]` hoặc `text-3xl`, weight 700
- [ ] H2 section = `text-2xl`, weight 600
- [ ] H3 card = `text-xl`, weight 600
- [ ] Không có `text-[36px]`, `text-[28px]`, `text-4xl` trong page content

**Controls:**
- [ ] Inputs = `h-11` (44px)
- [ ] Buttons = `h-10` (40px) hoặc `h-11` (44px)
- [ ] Không dùng `h-12` (48px) cho inputs

**Shadows:**
- [ ] Cards = `shadow-sm` hoặc `border + shadow-sm`
- [ ] Modals = `shadow-xl` hoặc `shadow-md`
- [ ] Không dùng arbitrary heavy shadows như `shadow-[0_20px_60px...]`

---

## 12. Cách mapping từ Design Token → Tailwind Class

| Design Token | Tailwind Class |
|-------------|---------------|
| `color.primary` → `#0284C7` | `sky-600` |
| `color.primaryHover` → `#0369A1` | `sky-700` |
| `color.primarySoft` → `#F0F9FF` | `sky-50` |
| `color.success` → `#15803D` | `emerald-600` |
| `color.successSoft` → `#F0FDF4` | `emerald-50` |
| `color.warning` → `#B45309` | `amber-600` |
| `color.warningSoft` → `#FFFBEB` | `amber-50` |
| `color.danger` → `#BE123C` | `rose-600` |
| `color.dangerSoft` → `#FFF1F2` | `rose-50` |
| `color.bg` → `#F5F7FB` | `slate-50` |
| `color.textPrimary` → `#0F172A` | `slate-900` |
| `color.textSecondary` → `#475569` | `slate-600` |
| `color.borderDefault` → `#E2E8F0` | `slate-200` |
| `shadow.1` → `0 1px 2px rgba(15,23,42,0.04)` | `shadow-sm` |
| `shadow.2` → `0 4px 12px rgba(15,23,42,0.06)` | `shadow-md` |
| `shadow.3` → `0 10px 24px rgba(15,23,42,0.08)` | `shadow-xl` |

---

## 13. Cách fix gradient cards (pattern phổ biến nhất)

```tsx
// ❌ SAI — gradient KPI card
<div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white">
  <p className="text-green-100 text-sm">Dự án</p>
  <p className="text-3xl font-bold">{count}</p>
  <Building2 className="h-12 w-12 text-green-200" />
</div>

// ✅ ĐÚNG — solid soft surface + accent icon
<div className="bg-emerald-50 rounded-lg p-5 border border-slate-200">
  <div className="flex items-start justify-between gap-3">
    <div>
      <p className="text-sm text-slate-600">Dự án</p>
      <p className="mt-1 text-2xl font-bold text-emerald-700">{count}</p>
    </div>
    <Building2 className="h-8 w-8 text-emerald-600 mt-1" />
  </div>
</div>
```

**Pattern chuẩn cho KPI card:**
1. Background: soft color surface (e.g. `bg-emerald-50`)
2. Border: thin border (e.g. `border-slate-200`)
3. Radius: `rounded-lg` (12px)
4. Icon: accent color của metric (e.g. `text-emerald-600`)
5. Value text: dark variant của accent color (e.g. `text-emerald-700`)
6. Label text: `text-slate-600`

---

## 14. Tổ chức file khi refactor

Khi refactor một page lớn, chia thành các sub-components trong cùng file hoặc file riêng:

```
page.tsx
├── Header (UserPageHeader)
├── StatsSection
├── TableSection
└── ModalConfirm
```

---

## 14.1 Pattern Animation Chuẩn (Ghost Row + Realtime Update)

Áp dụng cho popup có 2 danh sách trái/phải (ví dụ: thêm/gỡ thành viên).

### Mục tiêu

- thao tác có phản hồi ngay
- không nháy màn hình
- người dùng nhìn thấy item đang "chuyển" danh sách

### Quy tắc kỹ thuật

1. Không gọi full-page loading khi thao tác trong popup.
2. Cập nhật local state ngay (optimistic update).
3. Nếu API fail thì rollback local state.
4. Dùng Framer Motion `AnimatePresence` + `motion.div layout` cho row list.
5. Transition ngắn: `duration: 0.16 - 0.24`.
6. Ghost row (khuyến nghị):
   - xuất hiện ở danh sách nguồn khi item bị chuyển
   - style: border dashed, opacity thấp
   - tự biến mất sau `200 - 300ms`

### Ví dụ class và timing

- Row thường: `rounded-lg border border-slate-200 bg-slate-50`
- Ghost row: `border-dashed border-slate-300 bg-slate-100 opacity thấp`
- Motion timing:
  - enter: `opacity 0 -> 1`, `y 8 -> 0`, `~180ms`
  - exit: `opacity 1 -> 0`, `y 0 -> -8`, `~180ms`
  - layout: `layout` animation mặc định (không bounce)

### Cần tránh

- gọi `setLoading(true)` cho cả page sau mỗi thao tác add/remove
- flash trắng do remount toàn màn
- animation quá dài hoặc hiệu ứng nảy mạnh

Hoặc tách component con ra file riêng nếu file vượt ~400 lines.

---

## 15. Những thứ KHÔNG ĐƯỢC LÀM

- KHÔNG thêm gradient vào bất kỳ UI element nào
- KHÔNG tự ý chọn màu không có trong spec palette
- KHÔNG dùng arbitrary radius values (`rounded-[xxpx]`)
- KHÔNG dùng arbitrary heavy shadows
- KHÔNG thay đổi logic nghiệp vụ khi refactor UI
- KHÔNG thêm decorative copy như "Workspace", "Design System", "Command Center"
- KHÔNG dùng emoji thay cho icons

## 16. Những thứ ĐƯỢC LÀM

- Thay gradient → flat solid colors
- Thay arbitrary radius → scale chuẩn 6/10/12/16/20px
- Thay `text-black`/`text-white` → semantic slate colors
- Thay arbitrary heavy shadows → Tailwind shadow utilities
- Cải thiện spacing, alignment, typography hierarchy
- Refactor để dùng component nếu đã có shared component
- Thêm hover/focus states cho interactive elements
