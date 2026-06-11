# Design GUI (VN)

## 1. Purpose

`DESIGN_GUI_VN.md` định nghĩa toàn bộ rule GUI dùng chung cho các sản phẩm web và mobile trên nhiều project khác nhau.

File này tồn tại để:

- thiết lập một baseline nhất quán cho `layout`, `hierarchy`, `spacing`, `component`, và `interaction behavior`
- giảm tình trạng UI bị lệch giữa các product, team, và style triển khai
- cho phép từng product có cá tính riêng mà không phá vỡ `core visual language`
- làm tài liệu tham chiếu cho designer, developer, reviewer, và AI assistant trước khi đưa ra quyết định về UI

Guide này có tính `platform-aware` nhưng `product-agnostic`.

Nó được thiết kế để dùng cho:

- dashboard
- internal tool
- CRUD system
- operational workflow
- detail page
- form-heavy product
- mobile application
- consumer-facing product screen

Tài liệu này mang tính `prescriptive`.

Khi một pattern đã được định nghĩa ở đây, pattern đó phải được coi là mặc định, trừ khi có lý do rất rõ ràng liên quan tới `functional requirement`, `accessibility`, `performance`, hoặc `maintainability`.

Đây không phải là `brand book`, không phải `feature specification`, và cũng không phải một `component inventory` đầy đủ.

Đây là một bộ rule dùng chung để xây dựng giao diện rõ ràng, dễ dùng, và nhất quán.

## 2. Design Philosophy

GUI nên mang cảm giác:

- clean
- product-first
- calm
- modern
- practical
- slightly premium
- not decorative

Giao diện phải ưu tiên `clarity`, `usability`, và `structure` trước `visual novelty`.

Mỗi screen phải cho cảm giác được thiết kế có chủ đích, nhưng không được `over-designed`.

`Design language` này phải đủ linh hoạt để hỗ trợ cả workflow dày đặc lẫn product hiện đại, nhưng vẫn giữ nguyên bản sắc cốt lõi.

### Principles

- Ưu tiên `utility` hơn `ornament`.
- Ưu tiên sự tinh gọn có kiểm soát hơn `visual drama`.
- Giữ giao diện đủ yên để content vẫn là trung tâm.
- Dùng `hierarchy` để dẫn hướng sự chú ý, không dùng effect.
- Thiết kế cho việc sử dụng lặp lại hằng ngày, không phải để gây ấn tượng một lần.
- Giữ system đủ bền để dùng qua nhiều chu kỳ phát triển của product.
- Duy trì tính nhất quán giữa screen, state, và flow.

### What The System Should Not Be

- flashy
- trend-driven
- decorative
- presentation-first
- emotionally exaggerated
- template-like
- dependent on novelty to feel modern

### Quality Bar

Một screen tốt phải rõ ngay từ lần quét đầu tiên, thoải mái khi dùng lặp lại, và đủ đáng tin trong môi trường product thực tế.

Nó phải refined nhưng không precious, và minimal nhưng không trống rỗng.

## 3. Core Visual Language

### Typography

Sử dụng `neutral modern sans-serif` làm hệ `type` mặc định.

Hướng ưu tiên:

- `Inter` là lựa chọn mặc định
- `SF Pro`, `Segoe UI`, hoặc các `platform-native equivalent` khi cần
- `Plus Jakarta Sans` hoặc `Manrope` chỉ dùng khi product cần cảm giác mềm hơn một chút nhưng không được playful

`Typography` nên mang cảm giác:

- clear
- quiet
- highly legible
- product-oriented

Rules:

- dùng `type scale` có kiểm soát
- chỉ dựa vào `regular`, `medium`, và `semibold` làm `primary weight`
- thể hiện `hierarchy` bằng `size`, `weight`, và `spacing`
- mặc định dùng `sentence case`
- giữ `body copy` ổn định trong các giao diện dày đặc

Avoid:

- decorative display font
- condensed font
- handwritten hoặc expressive font
- AI-styled typography
- heavy uppercase styling
- wide letter spacing dùng để trang trí
- hero typography quá khổ trong product UI

### Color System

Base UI mặc định phải là `light theme`.

Dùng màu để truyền đạt `structure` và `meaning`, không dùng để trang trí.

Hành vi của `base palette`:

- surface trắng và off-white dịu
- neutral thuộc nhóm cool gray và slate
- deep slate hoặc navy cho `primary text`
- muted slate cho `secondary text`
- blue tiết chế cho `primary action` và `active state`
- muted green chỉ cho `positive state`
- muted amber chỉ cho `warning`
- muted red chỉ cho `destructive` hoặc `critical state`

Các `color role` gợi ý:

- `Background`: soft off-white
- `Surface`: white
- `Surface Alt`: very light gray-blue
- `Text Primary`: deep slate or navy
- `Text Secondary`: muted slate
- `Border`: soft neutral gray
- `Primary`: medium blue
- `Primary Soft`: pale blue
- `Success`: muted green
- `Warning`: muted amber
- `Danger`: muted red

Rules:

- giữ `palette` neutral và cân bằng
- chỉ dùng một `primary accent color` một cách nhất quán
- định nghĩa `semantic color` rõ ràng
- duy trì `accessible contrast` ở mọi state
- ưu tiên `flat color layer` và `soft tonal shift`

Avoid:

- gradient-heavy UI
- neon accent
- purple AI-style palette
- black-heavy dramatic surface
- glow effect
- phối màu trang trí quá gắt

### Spacing

`Spacing` phải cho cảm giác nhất quán và yên tĩnh.

UI cần đủ thoáng để dễ đọc, nhưng không được tạo cảm giác rỗng.

Rules:

- dùng `spacing scale` có tính dự đoán như `4, 8, 12, 16, 24, 32, 48`
- giữ `section rhythm` ổn định
- chỉ siết `spacing` khi `density` thực sự cần
- ưu tiên `structural spacing` thay vì bố cục mang tính biểu diễn

Avoid:

- giá trị `spacing` lẻ không có lý do
- khoảng cách section quá lớn
- `card padding` quá nhiều
- `control` quá cao
- content block trôi nổi, cô lập

### Radius

`Rounded corner` phải hiện đại nhưng tiết chế.

Rules:

- mặc định dùng `small-to-medium radius`
- áp cùng một `radius scale` cho các họ `component` liên quan
- chỉ dùng `radius` lớn hơn cho `container` quan trọng khi thật sự cần nhấn tách lớp

Avoid:

- bubble UI quá tròn
- pill shape ở mọi nơi
- hình học playful làm yếu đi chất product

### Borders

Dùng `border` như một công cụ tạo `structure`, không phải trang trí.

Rules:

- ưu tiên `low-contrast border` để tách lớp
- dùng border nhất quán trên input, card, table, và overlay
- giữ `border thickness` ổn định toàn hệ thống
- thay đổi border ở `hover`, `focus`, và `selected state` theo cách tiết chế

Avoid:

- outline nặng không có lý do
- border weight không nhất quán

### Shadows

`Shadow` phải phục vụ `elevation`, không tạo cảm giác phô diễn.

Rules:

- dùng shadow mềm, opacity thấp
- hạn chế dùng shadow trong giao diện nhiều dữ liệu
- ưu tiên border và spacing trước khi thêm shadow phức tạp
- chỉ định một số ít `shadow tier` cho surface, overlay, và floating control

Avoid:

- glow
- colored shadow
- shadow lan quá dài
- layered depth kiểu theatrical

### Icons

Chỉ dùng một `icon set` nhất quán trong toàn product.

Hướng ưu tiên:

- Lucide hoặc một `minimal system icon set` tương đương

Rules:

- giữ style của icon phù hợp với typography
- nhất quán về `stroke weight`, `size`, và `alignment`
- dùng icon để hỗ trợ nhận diện, không thay thế label trong các chỗ cần rõ nghĩa

Avoid:

- decorative icon container mặc định
- icon quá nhiều chi tiết kiểu illustration
- trộn nhiều `icon style` không tương thích

### Motion

`Motion` phải làm rõ `state change`, không được dùng để gây chú ý.

Rules:

- giữ transition ngắn, nhẹ, và có mục đích
- chỉ dùng motion cho feedback, overlay, điều hướng, và làm rõ thay đổi state
- tôn trọng `reduced-motion preference`
- ưu tiên fade, translate nhẹ, và easing đơn giản

Avoid:

- animated gradient
- decorative loop
- bouncy motion
- parallax
- theatrical page transition

#### Pattern cho thao tác chuyển item giữa 2 danh sách

Áp dụng cho các màn như `Quản lý thành viên`, `Phân quyền`, `Phân công`:

- khi thêm/gỡ item, UI phải cập nhật ngay trong popup
- không reload cả page để đồng bộ dữ liệu
- dùng transition ngắn `160ms - 240ms` cho `enter/exit`
- dùng `layout animation` để các row còn lại dồn vị trí mượt
- cho phép dùng `ghost row` mờ `200ms - 300ms` ở danh sách nguồn để tạo cảm giác chuyển trạng thái rõ ràng

Không dùng:

- full-screen loading hoặc flash trắng sau mỗi thao tác
- animation kéo dài, nảy mạnh, hoặc mang tính trình diễn

### Hard Design Tokens

Hãy dùng các token này làm mặc định của hệ thống.

Không được tự nghĩ ra giá trị `ad hoc` khi token đã tồn tại.

#### Font Family Tokens

- `font.sans`: `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- `font.mono`: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace`

#### Color Tokens

Tất cả màu đều được thiết kế theo hướng `light-theme first` và cân chỉnh cho một `calm product UI`.

Hãy dùng `semantic token` cho logic giao diện.

| Token | Hex | Usage |
|---|---:|---|
| `color.bg` | `#F5F7FB` | App background |
| `color.surface` | `#FFFFFF` | Primary surface, card, panel |
| `color.surfaceSubtle` | `#F3F6FB` | Secondary surface, quiet container |
| `color.surfaceMuted` | `#E2E8F0` | Divider, inactive fill |
| `color.textPrimary` | `#0F172A` | Main text |
| `color.textSecondary` | `#475569` | Supporting text |
| `color.textMuted` | `#64748B` | Helper text, placeholder |
| `color.textDisabled` | `#94A3B8` | Disabled text |
| `color.borderDefault` | `#E2E8F0` | Standard border |
| `color.borderStrong` | `#CBD5E1` | Active hoặc emphasized border |
| `color.focusRing` | `#7DD3FC` | Focus ring, keyboard emphasis |
| `color.primary` | `#0284C7` | Primary action, link, active state |
| `color.primaryHover` | `#0369A1` | Hover state cho primary action |
| `color.primarySoft` | `#F0F9FF` | Selected background, soft emphasis |
| `color.success` | `#15803D` | Positive state |
| `color.successSoft` | `#F0FDF4` | Positive background |
| `color.warning` | `#B45309` | Warning state |
| `color.warningSoft` | `#FFFBEB` | Warning background |
| `color.danger` | `#BE123C` | Destructive action, error |
| `color.dangerSoft` | `#FFF1F2` | Error background |
| `color.info` | `#0284C7` | Informational state |
| `color.infoSoft` | `#F0F9FF` | Informational background |

Rules:

- dùng `flat color layer` và `soft tonal shift`
- giữ một `primary accent color` nhất quán toàn product
- dùng `semantic color` cho meaning, không cho trang trí

#### Typography Scale

Dùng `typographic scale` tiết chế, `line height` dễ đọc, và `weight` ổn định.

| Token | Size | Line Height | Weight | Usage |
|---|---:|---:|---:|---|
| `type.display` | `36px` | `44px` | `700` | Nhấn mạnh lớn, hiếm dùng |
| `type.h1` | `30px` | `38px` | `700` | Page title |
| `type.h2` | `24px` | `32px` | `600` | Section heading |
| `type.h3` | `20px` | `28px` | `600` | Card title, subsection header |
| `type.body` | `16px` | `24px` | `400` | Body text mặc định |
| `type.bodyStrong` | `16px` | `24px` | `500` | Body text nhấn mạnh |
| `type.bodySmall` | `14px` | `20px` | `400` | Secondary content, dense UI |
| `type.bodySmallStrong` | `14px` | `20px` | `500` | Small emphasis text |
| `type.caption` | `12px` | `16px` | `500` | Label, metadata, hint |
| `type.overline` | `11px` | `16px` | `600` | Utility label hiếm dùng |

Rules:

- thể hiện `hierarchy` bằng size, weight, spacing
- mặc định dùng `sentence case`
- tránh decorative letter spacing, trừ một số utility label hiếm gặp

#### Spacing Scale

Hãy dùng token spacing gần nhất thay vì tự tạo giá trị riêng.

| Token | Value |
|---|---:|
| `space.0` | `0px` |
| `space.1` | `4px` |
| `space.2` | `8px` |
| `space.3` | `12px` |
| `space.4` | `16px` |
| `space.5` | `20px` |
| `space.6` | `24px` |
| `space.8` | `32px` |
| `space.10` | `40px` |
| `space.12` | `48px` |
| `space.16` | `64px` |
| `space.20` | `80px` |

#### Radius Scale

| Token | Value | Usage |
|---|---:|---|
| `radius.none` | `0px` | Flush edge, data grid |
| `radius.sm` | `6px` | Small control, compact badge |
| `radius.md` | `10px` | Input và button |
| `radius.lg` | `12px` | Card, menu, standard surface |
| `radius.xl` | `16px` | Panel, modal, large container |
| `radius.2xl` | `20px` | Major layout block |
| `radius.full` | `999px` | Chỉ dùng khi pill shape thật sự cần |

#### Border Thickness

| Token | Value | Usage |
|---|---:|---|
| `border.1` | `1px` | Border mặc định, input, card, divider |
| `border.2` | `2px` | Focus state, selected state, strong emphasis |
| `border.3` | `3px` | Nhấn mạnh hiếm gặp |

#### Shadow Tiers

`Shadow` phải phục vụ `elevation`, không phục vụ trình diễn.

| Token | Value | Usage |
|---|---|---|
| `shadow.0` | `none` | Flat surface |
| `shadow.1` | `0 1px 2px rgba(15, 23, 42, 0.04)` | Card nhô rất nhẹ |
| `shadow.2` | `0 4px 12px rgba(15, 23, 42, 0.06)` | Floating menu, compact panel |
| `shadow.3` | `0 10px 24px rgba(15, 23, 42, 0.08)` | Modal, drawer, prominent surface |
| `shadow.4` | `0 18px 40px rgba(15, 23, 42, 0.10)` | Elevation cao nhất |

#### Control Heights

| Token | Value | Usage |
|---|---:|---|
| `control.xs` | `28px` | Tiny chip, compact filter |
| `control.sm` | `32px` | Dense list, compact button |
| `control.md` | `40px` | Button, input, select mặc định |
| `control.lg` | `44px` | Touch-friendly control |
| `control.xl` | `48px` | Large form, high-visibility action |

#### Icon Sizes

| Token | Value | Usage |
|---|---:|---|
| `icon.xs` | `12px` | Dense data label, tiny affordance |
| `icon.sm` | `14px` | Inline metadata, compact UI |
| `icon.md` | `16px` | Icon mặc định |
| `icon.lg` | `20px` | Prominent action, header |
| `icon.xl` | `24px` | Nhấn mạnh hiếm gặp, empty state |

#### Motion Durations and Easings

| Token | Value | Usage |
|---|---:|---|
| `motion.fast` | `120ms` | Micro-interaction, hover feedback |
| `motion.base` | `160ms` | Standard transition |
| `motion.medium` | `220ms` | Panel, menu, state change |
| `motion.slow` | `280ms` | Modal, drawer, reveal lớn hơn |
| `motion.standardEasing` | `cubic-bezier(0.2, 0, 0, 1)` | Default easing |
| `motion.enterEasing` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrance transition |
| `motion.exitEasing` | `cubic-bezier(0.4, 0, 1, 1)` | Exit transition |

#### Content Width Tokens

| Token | Value | Usage |
|---|---:|---|
| `container.narrow` | `720px` | Reading-heavy form, focused flow |
| `container.default` | `960px` | Standard page |
| `container.wide` | `1280px` | Detail page, dashboard |
| `container.full` | `1440px` | Screen nhiều data hoặc comparison-heavy |

## 4. Component Rules

### Buttons

`Button` phải gọn, rõ nghĩa, và định hướng hành động.

Rules:

- `primary button` dùng blue clean fill với text trắng
- `secondary button` dùng surface trắng hoặc gray rất nhạt với border nhẹ
- `destructive button` dùng muted red, không dùng đỏ gắt
- `button height`, `padding`, và `radius` phải nhất quán toàn hệ thống
- label phải mô tả hành động cụ thể

Avoid:

- pill button quá lớn
- button có style mang tính trang trí
- label mơ hồ như `Explore`, `Continue`, hoặc `Open workspace`

### Inputs, Selects, and Textareas

Toàn bộ `form control` phải thuộc về cùng một `visual language`.

Rules:

- giữ nhất quán về height, padding, border, radius, và focus behavior
- `focus state` dựa trên border và soft ring
- placeholder phải dễ đọc và rõ ràng là thông tin phụ
- `read-only field` phải nhìn khác hẳn field editable
- `textarea` phải gọn, có cấu trúc, và có đủ khoảng thở bên trong

Avoid:

- focus glow quá mạnh
- field quá cao khi không cần
- placeholder gánh toàn bộ meaning của field

### Cards

`Card` dùng để nhóm thông tin, không dùng để trang trí chỗ trống.

Rules:

- dùng surface trắng, border nhẹ, elevation tối thiểu
- `card header` phải ngắn và bám đúng purpose
- card phải giúp nhóm nội dung, không làm vỡ cấu trúc thị giác

Avoid:

- nesting quá nhiều
- pattern card trong card mà không có giá trị cấu trúc
- card lớn nhưng rỗng, chỉ mang tính trang trí

### Tables

`Table` là lựa chọn ưu tiên cho `dense operational data`.

Rules:

- tối ưu cho scanability trước tiên
- giữ header hierarchy rõ
- giữ row rhythm ổn định
- dùng status và row action có kiểm soát để dữ liệu vẫn là trung tâm

Avoid:

- table chrome quá trang trí
- quá nhiều action inline
- style khiến table ồn hơn chính dữ liệu

### Tabs and Local Navigation

`Tab` phải gọn, dễ đọc, và dễ quét.

Rules:

- chỉ dùng tab cho các view song song trong cùng một task context
- giữ `active state` rõ nhưng tiết chế
- dùng blue emphasis nhẹ thay vì block màu đậm

Avoid:

- tab quá lớn
- hệ tab mang tính trang trí
- dùng tab khi page structure sẽ rõ hơn

### Modals and Drawers

Chỉ dùng `overlay` khi nó thực sự giúp workflow tốt hơn.

Rules:

- dùng modal cho action tập trung, xác nhận, hoặc workflow ngắn
- dùng drawer khi vẫn cần nhìn underlying page context
- title phải trực diện, rõ nghĩa
- content trong overlay phải thực dụng và gọn

Avoid:

- modal intro kiểu marketing
- decorative illustration mặc định
- workflow dài nhưng nhét trong dialog chật

### Badges, Status, and Alerts

`Status UI` phải truyền đạt meaning với mức noise tối thiểu.

Rules:

- map màu nhất quán với meaning
- giữ status treatment mềm và tiết chế
- alert phải ngắn, có cấu trúc, và actionable
- chỉ hiển thị impact và next step khi thực sự cần

Avoid:

- badge mang tính trang trí
- mapping màu không nhất quán
- alert block quá lớn, làm gián đoạn page không cần thiết

### Empty States

`Empty state` phải giúp user đi tiếp.

Rules:

- có một title ngắn
- có một supporting sentence ngắn
- có một action liên quan khi action đó thực sự khả dụng

Avoid:

- mascot-style illustration
- filler copy
- abstract product metaphor
- cố giải trí thay vì dẫn hướng

### Hard Component Specs

#### Density Rules

- `desktop control height` mặc định: `40px` đến `44px`
- `touch control height` mặc định: `44px` đến `48px`
- `compact density` chỉ được dùng trong dense table, toolbar, và admin workflow
- không trộn nhiều mức density trong cùng một surface nếu các control không khác role

#### State Rules

Mọi `interactive component` đều nên có các state sau khi phù hợp:

- default
- hover
- active hoặc pressed
- focus
- disabled
- loading
- selected hoặc checked
- error
- read-only

Rules:

- focus luôn phải nhìn thấy được
- disabled state vẫn phải legible
- loading state không được làm layout shift
- selected state phải rõ nhưng tiết chế
- error state phải đủ rõ mà không lấn át layout

#### Buttons

Recommended sizes:

- `Small`: `32px` height
- `Medium`: `40px` height
- `Large`: `48px` height

Rules:

- mỗi surface chỉ nên có một primary button
- secondary button cho hành động hỗ trợ
- destructive button chỉ dùng cho hành động không thể hoàn tác hoặc có rủi ro cao
- label phải ngắn, cụ thể, và action-based
- icon-only button chỉ dùng khi action có thể nhận biết phổ quát

#### Inputs, Selects, and Textareas

Recommended sizes:

- input và select: `40px` mặc định, `44px` cho touch
- compact control: `36px` chỉ trong layout dày đặc
- textarea: tối thiểu `96px`

Rules:

- mặc định đặt label phía trên control
- helper text phải ngắn và hữu ích
- error hiển thị ngay dưới field
- border, radius, focus treatment phải đồng bộ giữa các field type
- placeholder chỉ là hint, không phải label thay thế

#### Checkboxes, Radios, and Switches

Recommended sizes:

- checkbox và radio visual size: `16px` đến `20px`
- minimum click target: `44px`
- switch track height: `20px` đến `24px`

Rules:

- checkbox cho nhiều lựa chọn độc lập
- radio cho một lựa chọn duy nhất trong một tập cố định
- switch chỉ dùng cho binary setting có hiệu lực ngay
- càng nhiều càng tốt, toàn bộ vùng label nên clickable

#### Cards

Recommended spacing:

- padding: `16px` đến `24px`
- khoảng cách giữa các phần bên trong: `12px` đến `16px`

Rules:

- header phải ngắn gọn
- dùng border nhẹ và elevation tối thiểu
- action đặt ở vị trí predictable
- tránh nested card trừ khi đó là các lớp thông tin thật sự khác nhau

#### Tables

Recommended sizes:

- compact row height: `44px` đến `48px`
- comfortable row height: `52px` đến `56px`
- header height: `40px` đến `44px`

Rules:

- header label phải ngắn và rõ
- căn phải số liệu khi giúp scan tốt hơn
- row action phải ít và predictable
- có thể dùng sticky header cho table dài khi thực sự có ích

#### Tabs

Recommended sizes:

- tab height: `36px` đến `40px` trên desktop
- tab height: `44px` trên touch layout

Rules:

- chỉ dùng tab cho sibling view trong cùng task context
- label phải ngắn và song song về cấu trúc
- xử lý overflow tab một cách mềm mại khi số lượng tăng

#### Badges

Recommended sizes:

- height: `20px` đến `24px`

Rules:

- badge dùng cho status, type, priority, hoặc count
- text nên ngắn, thường chỉ một đến ba từ
- mapping màu phải nhất quán theo meaning

#### Alerts

Rules:

- alert dùng cho outcome, blocker, warning, hoặc critical context
- alert phải ngắn và actionable
- alert phải đặt gần content hoặc action liên quan
- khi cần, chỉ nên có title và một supporting sentence

#### Modals

Recommended widths:

- `Small`: `480px`
- `Medium`: `640px`
- `Large`: `800px`

Rules:

- modal dành cho confirm, chỉnh sửa nhẹ, hoặc luồng quyết định ngắn
- title phải trực diện và cụ thể
- trong đa số trường hợp chỉ nên có một primary action và một secondary cancel action
- không đặt long form trong modal nếu page hoặc drawer rõ ràng hơn

#### Drawers

Recommended widths:

- desktop: `480px` đến `640px`
- mobile: full screen

Rules:

- drawer dùng cho inspect, edit, hoặc detail overlay khi cần giữ context của page
- header, content, và action phải có cấu trúc rõ
- không được nhồi nhiều task không liên quan vào cùng một drawer

#### Empty States

Rules:

- layout nên được căn giữa trong đúng vùng liên quan
- nếu quan trọng, hãy giải thích vì sao trạng thái này đang trống
- cung cấp một primary next step
- không làm empty state lớn hơn phần content mà nó thay thế

#### Page Headers

Recommended structure:

- title
- optional description
- supporting control
- primary action

Rules:

- header phải gọn
- subtitle chỉ dùng khi nó thêm được context thật
- action ở header phải được căn hàng nhất quán giữa các page
- không biến product page thành hero section

## 5. Layout Rules and Responsive Standards

### App Shell

`App shell` phải giúp định hướng mà không cạnh tranh với content của page.

Rules:

- chỉ dùng shell khi cần `persistent navigation` hoặc `global utility`
- giữ shell yên, gọn, và có cấu trúc
- ưu tiên content hơn `chrome`
- chọn top, side, hoặc bottom navigation dựa trên cấu trúc product, không theo thói quen

### Desktop Page Structure

Page trên desktop phải có `hierarchy` dễ đoán:

- header
- controls
- content

Rules:

- giữ page header gọn
- đặt primary action gần title hoặc trong một vùng action nhất quán
- giữ phần intro tối thiểu
- để content hữu ích xuất hiện sớm trong viewport

Avoid:

- product opening kiểu hero
- banner trang trí lớn trong product screen

### Content Width

`Content width` phải được kiểm soát có chủ đích.

Rules:

- dùng layout rộng hơn cho tool dày dữ liệu, dashboard, và màn hình nhiều comparison
- dùng layout hẹp hơn cho form, screen nhiều đọc, và detail view
- giữ `line length` và scanability ở mức thoải mái

Avoid:

- content dài chạy edge-to-edge
- màn data-heavy quá hẹp

### Dashboard Layout

Dashboard phải hỗ trợ ra quyết định, không phải trình diễn.

Rules:

- chỉ dùng card khi card đó truyền đạt metric, status, hoặc trend thật sự
- giữ hierarchy rõ: tín hiệu chính trước, chi tiết hỗ trợ sau
- chỉ dùng chart khi nó trả lời được một câu hỏi thực tế
- page phải đủ gọn để dùng lặp lại hằng ngày

Avoid:

- analytics block mang tính trang trí
- card grid không có giá trị vận hành

### List Pages

`List page` phải tối ưu cho filtering, scanning, và row-level action.

Rules:

- nhóm filter có logic và giữ chúng gọn
- dùng table hoặc list card hỗ trợ so sánh nhanh
- secondary control phải dễ thấy nhưng tiết chế
- giữ row rhythm ổn định và status cue rõ ràng

Avoid:

- panel filter chiếm hết page
- action rải rác làm yếu khả năng scan

### Detail Pages

`Detail page` phải làm nổi bật `main record` hoặc `main object`.

Rules:

- dành nhiều width nhất cho vùng content chính
- giữ side navigation, metadata, và panel hỗ trợ ở mức gọn
- dùng `progressive disclosure` cho thông tin phụ

Avoid:

- quá nhiều vùng có weight ngang nhau
- side panel cạnh tranh với phần detail chính

### Form Pages

`Form page` phải cho cảm giác được dẫn dắt và hiệu quả.

Rules:

- nhóm field liên quan thành section rõ ràng
- mặc định dùng một cột
- chỉ dùng hai cột khi nó thật sự tăng tốc và tăng độ đọc được
- giữ label, helper text, và validation gần field
- giữ primary action ở vị trí predictable

Avoid:

- form stack quá dài, liền một mạch
- sắp field theo kiểu trang trí

### Mobile Screens

Screen trên mobile phải giữ nguyên `design language` nhưng với `rhythm` chặt hơn.

Rules:

- giảm chrome và density nhưng vẫn giữ hierarchy
- đơn giản hóa control và label khi cần
- ưu tiên stacked layout và compact surface
- giữ action quan trọng trong vùng dễ với tới

Avoid:

- bê nguyên spacing của desktop sang mobile
- chỉ thu nhỏ desktop layout thay vì thiết kế lại hierarchy

### Section Spacing

`Section spacing` phải phục vụ cấu trúc, không tạo kịch tính.

Rules:

- giữ vertical rhythm ổn định giữa các section
- bỏ wrapper và container thừa
- để content hữu ích xuất hiện sớm nhất có thể

Avoid:

- top padding quá lớn
- khoảng trống dùng như một hình thức trang trí

### Responsive Standards

Hệ thống bắt buộc phải `responsive by default`.

`Breakpoint` khuyến nghị:

- `Mobile`: 320px đến 767px
- `Tablet`: 768px đến 1023px
- `Desktop`: 1024px đến 1439px
- `Wide Desktop`: 1440px trở lên

### Responsive Layout Behavior

Rules:

- mobile chỉ nên có một cột chính
- tablet chỉ nên dùng hai cột khi độ đọc vẫn mạnh
- desktop dùng grid rộng hơn để tăng hiệu quả, không phải để trang trí
- khi layout collapse, phải sắp lại spacing, density, và thứ tự theo ưu tiên

Avoid:

- giữ nguyên số cột của desktop khi nó làm giảm usability
- stack máy móc các block desktop mà không nghĩ lại priority

### Tables on Small Screens

Rules:

- chỉ cho phép `horizontal scroll` trong controlled container khi thật sự cần
- khi scan tốt hơn, ưu tiên stacked record hoặc compact list item
- trên screen nhỏ, chỉ giữ các cột quan trọng nhất

Avoid:

- ép full desktop table vào layout hẹp

### Forms on Small Screens

Rules:

- form nhiều cột phải collapse về một cột trên mobile
- label, helper text, và error phải ở gần field
- vẫn phải giữ được grouping sau khi stack

Avoid:

- nén dọc quá mức làm giảm khả năng hiểu và chỉnh sửa

### Modal Behavior

Rules:

- dùng centered modal trên desktop cho workflow ngắn, tập trung
- dùng drawer hoặc side panel khi screen context quan trọng
- dùng bottom sheet hoặc full-screen overlay trên mobile cho task dài hơn

Avoid:

- modal nhỏ kiểu desktop trên điện thoại

### Touch Targets

Rules:

- control phải dễ bấm
- phải có khoảng cách đủ giữa các action
- ngay cả khi giao diện compact, usability vẫn phải được giữ

Avoid:

- action cluster chật
- `touch target` ưu tiên density hơn độ tin cậy

### Responsive Typography

Rules:

- heading phải giảm nhẹ trên screen nhỏ
- body text phải ổn định và dễ đọc
- hierarchy phải còn nguyên qua các breakpoint

Avoid:

- heading quá lớn trên mobile product screen
- nén typography đến mức giao diện mất cảm giác chắc chắn

### Hard Responsive Patterns

#### Breakpoint Behavior

- `Mobile`: dùng single-column flow, full-width surface, và hierarchy đi từ dưới lên
- `Tablet`: giữ hierarchy chính và chỉ dùng hai cột giới hạn khi cả hai cột vẫn còn readable
- `Desktop`: dùng persistent navigation, multi-column layout, và thông tin dày hơn khi điều đó giúp tăng tốc thao tác
- `Wide Desktop`: chỉ tăng content width cho các màn nhiều comparison hoặc data-heavy, không mở rộng line length vô tội vạ

Khi layout collapse, hãy sắp lại content theo task priority thay vì chỉ stack theo source order.

#### Navigation

- mobile: chỉ dùng bottom navigation khi có `3` đến `5` đích chính; nếu không, dùng top bar với drawer hoặc overflow
- tablet: dùng top bar hoặc compact side rail cho primary navigation và collapse secondary link theo mặc định
- desktop: dùng persistent side navigation cho kiến trúc thông tin sâu, chỉ dùng top navigation cho product nông
- wide desktop: giữ side navigation cố định và cap content width để phần trống không biến thành chrome thừa

#### Form Layout

- mobile: một cột, input full-width, label đặt phía trên, section xếp chồng
- tablet: chỉ dùng hai cột cho field ngắn, độc lập; field dài và destructive action phải full-width
- desktop: dùng một hoặc hai cột tùy theo task speed và scanability
- wide desktop: giữ form width có kiểm soát; không thêm cột chỉ vì còn chỗ

#### Tables

- mobile: không ép full table vào layout hẹp; dùng stacked record hoặc compact list row khi cần
- tablet: giảm bớt cột hiển thị và dùng row expansion cho chi tiết phụ
- desktop: coi table là pattern mặc định cho dense operational data
- wide desktop: giữ column priority ổn định, không kéo giãn cột để lấp đầy chiều ngang

#### List-Detail Behavior

- mobile: dùng screen riêng cho list và detail, đồng thời giữ lại vị trí scroll của list khi quay về
- tablet: dùng list kèm slide-over detail panel chỉ khi list vẫn usable
- desktop: dùng persistent split view cho workflow record-centric khi nó tăng tốc rõ ràng
- wide desktop: chỉ thêm zone thứ ba khi nó giúp workflow tốt hơn một cách rõ ràng

#### Modal Behavior

- mobile: ưu tiên full-screen overlay hoặc bottom sheet
- tablet: dùng drawer hoặc dialog cỡ vừa cho chỉnh sửa tập trung
- desktop: dùng centered modal cho task ngắn, tự chứa; dùng drawer khi page context quan trọng
- wide desktop: cap modal width và giữ action trong vùng dễ với tới

#### Sticky Actions

- mobile: dùng sticky bottom action bar cho primary commit action khi workflow dài
- tablet: dùng sticky footer hoặc header action cluster ổn định trên page dài
- desktop: chỉ pin action cho form dài hoặc review flow
- wide desktop: không tách action khỏi content mà nó tác động, trừ khi workflow thật sự nhiều bước

#### Touch Targets

- mobile minimum tappable area: `44px` x `44px`
- tablet primary control: `44px` x `44px` hoặc lớn hơn
- desktop frequent pointer target: ít nhất `40px` x `40px`

Không bao giờ chỉ dựa vào `visual size`. `Interactive area` phải có đủ padding.

#### Content Density

- mobile: ưu tiên một task chính cho mỗi screen và collapse chrome không thiết yếu
- tablet: dùng density cân bằng với `selective disclosure`
- desktop: ưu tiên density cao hơn cho công việc vận hành, nhưng vẫn giữ khoảng thở quanh action chính
- wide desktop: tăng data density, không tăng khoảng trống trang trí

## 6. Content Rules

### Headings

`Heading` phải ngắn, cụ thể, và nhiều thông tin.

Rules:

- mô tả đúng content của screen hoặc section
- giúp user định hướng nhanh
- giữ heading ngắn và dễ scan

Avoid:

- decorative subtitle
- slogan-style intro
- tên section mơ hồ
- cố tỏ ra clever
- marketing language
- AI-sounding phrasing

### Labels

`Label` phải định danh rõ field, action, hoặc control.

Rules:

- dùng noun đơn giản hoặc cụm từ ngắn mang tính hành động
- giữ terminology ổn định trên toàn interface
- mỗi label phải hiểu được mà không cần đoán

Avoid:

- internal jargon không có giải thích
- abstract product language
- wording playful trong product UI
- label chỉ lặp lại điều hiển nhiên mà không tăng clarity

### Helper Text

`Helper text` chỉ nên giải thích đúng phần user cần biết để hoàn tất action một cách chính xác.

Hãy dùng helper text cho:

- format guidance
- constraint
- expected input
- clarification ngắn

Rules:

- phải ngắn
- phải thực dụng
- nếu field đã quá rõ thì không cần helper text

Avoid:

- filler text
- motivational tone
- giải thích quá dài
- lặp lại label
- AI-style overexplaining

### Error Copy

`Error message` phải rõ, cụ thể, và actionable.

Rules:

- nói rõ chuyện gì đã sai
- khi cần, nói luôn cách sửa
- dùng plain language
- message phải đủ ngắn để scan

Avoid:

- technical dump
- phrasing mang tính đổ lỗi
- message chung chung như `Something went wrong`
- AI wording quá lịch sự hoặc quá trò chuyện

### CTA Naming

`CTA label` phải mô tả chính xác hành động sắp xảy ra.

Ưu tiên các label trực diện như:

- `Save changes`
- `Create project`
- `Delete record`
- `Send invite`
- `Export CSV`

Rules:

- dùng verb khớp với outcome
- với destructive hoặc irreversible action, label phải nói rõ điều đó

Avoid:

- label mơ hồ như `Continue` hoặc `Proceed` mà không có context
- CTA kiểu slogan
- wording clever hoặc branded
- label che giấu kết quả của action

### Empty-State Copy

`Empty-state copy` phải hữu ích, ngắn, và bình tĩnh.

Một empty state tốt cần giải thích:

- cái gì đang thiếu
- vì sao screen đang trống, nếu điều đó quan trọng
- user có thể làm gì tiếp theo

Rules:

- dùng một title rõ ràng
- dùng một supporting sentence ngắn
- dùng một CTA trực diện khi action khả dụng

Avoid:

- mascot-style language
- inspirational filler
- metaphor trừu tượng
- AI-sounding reassurance

### Tone

Toàn bộ `product copy` nên mang giọng:

- concise
- professional
- neutral
- direct
- confident

Tone phải đủ human, nhưng không được casual hoặc chatty.

Hãy viết như thể interface đang giúp một người dùng làm việc hoàn thành task nhanh và chính xác.

Avoid:

- decorative subtitle
- vague product copy
- filler text
- slogan-style intro
- overfriendly phrasing
- enthusiasm không cần thiết
- marketing tone
- AI-sounding UI writing

### Content Standards

Rules:

- dùng cùng một terminology cho cùng một concept ở mọi nơi
- giữ wording ổn định, dễ đoán, và dễ dịch
- khi phân vân, chọn cách viết đơn giản nhất nhưng vẫn chính xác

Avoid:

- đổi từ tùy hứng cho cùng một object hoặc action
- dùng copy để làm nhiệm vụ trang trí thị giác

## 7. Context Adaptation

`Design language` phải thích ứng theo ngữ cảnh mà không đánh mất bản sắc cốt lõi.

`Token`, typography, spacing rhythm, border treatment, và interaction state phải nhất quán trên toàn hệ thống.

Chỉ `hierarchy`, `density`, và `navigation pattern` được thay đổi theo task.

### Adaptation Principles

- giữ cùng một visual foundation cho mọi product type
- thay đổi structure trước khi thay đổi style
- giữ interaction state và semantic color role nhất quán
- điều chỉnh density theo use case
- tối ưu theo task chính của user, không theo screen pattern chung chung

### Dashboards

Rules:

- ưu tiên summary, status, và decision support
- giữ metric block gọn và dễ scan
- chỉ dùng chart khi nó làm rõ trend hoặc comparison

Avoid:

- analytics layout mang tính trang trí
- KPI card không phục vụ action

### CRUD Screens

Rules:

- ưu tiên scanning, filtering, và row-level action
- giữ form, table, và bulk action trong trạng thái kỷ luật
- giảm visual decoration để data là trung tâm

Avoid:

- list view bị over-styled
- filter và action phân tán

### Detail Pages

Rules:

- ưu tiên main record hoặc primary content area
- giữ metadata phụ ở mức gọn và thứ cấp
- chỉ dùng tab, anchor navigation, hoặc side panel khi nó cải thiện khả năng định hướng

Avoid:

- chia nhỏ sự chú ý vào quá nhiều section ngang vai trò

### Mobile Apps

Rules:

- giữ nguyên design language trong một vertical rhythm chặt hơn
- giảm chrome và đơn giản hóa navigation
- ưu tiên stacked section, sheet, và bottom-aligned action khi phù hợp

Avoid:

- bê nguyên density của desktop sang mobile
- coi mobile như một visual product hoàn toàn khác

### Internal Tools

Rules:

- tối ưu cho speed, precision, và repeated use
- cho phép density cao hơn consumer screen
- label phải rõ và control phải hiệu quả

Avoid:

- trang trí quá mức
- density cao đến mức khó đọc

### Consumer Product Screens

Rules:

- tối ưu cho clarity, confidence, và approachability
- cho phép nhiều khoảng thở hơn internal tool
- primary action phải rõ, secondary action phải yên hơn

Avoid:

- UI ồn
- screen quá chật
- cố làm product trông trendy một cách giả tạo

### Consistency Rules

- không tạo `visual system` riêng cho từng product type
- không restyle component chỉ để tạo cảm giác “khác đi”
- hãy điều chỉnh spacing, hierarchy, và density theo task
- mọi screen vẫn phải cho cảm giác cùng một product family

### Context Check

Trước khi chốt bất kỳ screen nào, hãy xác nhận:

- screen đó khớp với loại task đang phục vụ
- hierarchy hỗ trợ đúng user goal chính
- density khớp với usage pattern mong đợi
- navigation pattern phù hợp với device và context
- screen vẫn tuân theo shared design language

## 8. Anti-Patterns

System này bắt buộc phải loại bỏ những pattern làm giảm clarity, tăng noise, hoặc khiến product trông thiên về trang trí thay vì chức năng.

### Visual Anti-Patterns

Không được dùng:

- gradient-heavy UI
- glow effect
- glassmorphism
- neon accent
- shadow quá nặng
- layered shadow stack
- phối màu quá gắt
- black-heavy dramatic section
- AI visual chạy theo trend
- illustration mang tính trang trí nhưng không hỗ trợ task

Nếu một `visual treatment` chỉ tồn tại để “trông hiện đại”, nó không được phép dùng.

### Layout Anti-Patterns

Không được dùng:

- decorative card quá lớn
- product opening kiểu hero
- banner giới thiệu lớn bên trong product screen
- khoảng trống được dùng như một lựa chọn thiết kế chính
- section gap quá lớn
- content block trôi nổi không có mục đích cấu trúc
- card-inside-card mà không tăng giá trị
- layout làm trì hoãn việc chạm tới content hữu ích

Content hữu ích phải xuất hiện sớm.

`Decorative spacing` không thể thay thế cho `structure`.

### Typography and Copy Anti-Patterns

Không được dùng:

- subtitle ngẫu nhiên
- uppercase mang tính trang trí
- wide letter spacing chỉ để làm style
- heading mang tính kịch hóa
- marketing copy mơ hồ
- label kiểu placeholder nhưng giả làm product language

Nếu subtitle không làm rõ screen, hãy bỏ nó đi.

### Clarity Anti-Patterns

Không được đưa ra các lựa chọn làm giảm readability, scanability, hoặc user confidence.

Ví dụ:

- text tương phản quá thấp
- hierarchy yếu
- visual state mơ hồ
- container mang tính trang trí nhưng cạnh tranh với content
- control nhìn “đẹp” hơn “dùng được”
- giao diện che giấu ưu tiên thật bằng novelty

`Clarity` luôn phải đứng trên `style`.

### Enforcement Rule

Nếu một quyết định design làm tăng novelty, mood, hoặc trend alignment nhưng làm giảm clarity, quyết định đó phải bị loại bỏ.

Nếu interface trở nên khó đọc hơn, khó scan hơn, hoặc khó dùng hơn, pattern đó không được chấp nhận.

## 9. Execution Rules

Trước khi thiết kế hoặc sửa bất kỳ interface nào:

- đọc guide này trước
- đọc các file UI, component, và pattern liên quan đang có trong project
- coi tài liệu này là `default decision framework` cho mọi UI work

Rules:

- ưu tiên tái sử dụng component, token, layout, và interaction pattern đang có
- ưu tiên extend hoặc compose component cũ trước khi tạo pattern mới
- tối ưu cho consistency giữa screen, state, và flow
- consistency luôn quan trọng hơn novelty, visual experimentation, hay sở thích cá nhân
- chỉ thực hiện thay đổi nhỏ nhất nhưng đủ để giải quyết yêu cầu, miễn là vẫn bám đúng system hiện tại

### Exceptions

Chỉ được phép lệch khỏi guide này khi cách làm chuẩn không đáp ứng được một yêu cầu rõ ràng về:

- function
- accessibility
- performance
- maintainability

Mọi exception đều phải được giải thích tường minh.

Phần giải thích phải nêu rõ:

- rule nào đang bị nới
- vì sao cách chuẩn không đủ
- vì sao phương án thay thế là lựa chọn an toàn nhất

Exception phải được giới hạn phạm vi và không được trở thành mặc định mới trừ khi thay đổi đó là có chủ đích và đã được ghi lại.

### When Project Style Conflicts

Nếu style hiện tại của project xung đột với guide này:

- trước hết phải giữ sự coherent của khu vực hiện có bằng cách tôn trọng local style ở phần đang sửa
- nếu xung đột gây ra vấn đề thật về usability, accessibility, hoặc consistency thì phải nêu ra rõ ràng
- đề xuất một `controlled migration path` thay vì trộn nhiều pattern không tương thích trong cùng một flow

Khi phân vân, hãy giữ local project convention, trừ khi guide này đã định nghĩa một yêu cầu chặt hơn và yêu cầu đó thực sự phải được ưu tiên.

### Default Review Checklist

Trước khi ship một screen mới hoặc một thay đổi UI, hãy kiểm tra:

- layout đã rõ và có density phù hợp với task chưa
- typography đã readable và restrained chưa
- màu đang phục vụ function hay chỉ để trang trí
- component đã tái sử dụng pattern hiện có khi có thể
- copy đã ngắn gọn và không có filler
- responsive behavior đã được nghĩ có chủ đích
- screen cuối cùng có còn cảm giác thuộc cùng một product family hay không

---

## 10. Tối giản text & Cấm placeholder

Mỗi từ trên màn hình phải đáng giá. Nếu xóa một từ mà nghiệp vụ không bị ảnh hưởng, hãy xóa.

### Quy tắc cốt lõi

- Label là danh từ hoặc cụm động từ, không phải câu.
- Helper text là tùy chọn. Bỏ nếu field đã tự hiểu.
- Empty state cần: icon, tiêu đề 3–5 từ, một câu ngắn, một nút hành động.
- Card header là danh từ, không phải mô tả.
- KPI là con số + một từ nhãn.
- Table header 1–2 từ. Không thêm "Column".
- Modal title mô tả hành động hoặc record, không phải tên view.

### Các cụm cấm tuyệt đối

Không được dùng:

- `workspace`, `design principle`, `internal intake experience`, `review command center`
- `explore your data`, `welcome to the dashboard`, `manage everything in one place`
- `get started with your journey`, `here you can see...`, `below is the list of...`
- `overview of your recent...`, `this section allows you to...`
- Mở đầu kiểu "Ở đây bạn có thể quản lý..." trước mỗi bảng hoặc form

Nếu subtitle không làm rõ screen, hãy xóa.

### Label button

- ✅ `Tạo dự án`, `Xuất CSV`, `Gửi duyệt`
- ❌ `Tiếp tục`, `Proceed`, `Explore`, `Open workspace`

### Label form

- ✅ `Tên dự án`, `Ngày bắt đầu`
- ❌ `Please enter your project name`, `Nhập ngày bắt đầu vào đây`

---

## 11. Accessibility & WCAG

Giao diện phải hoạt động với mọi user, kể cả chỉ dùng bàn phím hoặc screen reader.

### Contrast

- Text thường: tối thiểu 4.5:1 với nền.
- Text lớn (18px+ bold hoặc 24px+ regular): tối thiểu 3:1.
- Component UI và đồ họa: tối thiểu 3:1.

Tất cả token trong guide này đã được cân chỉnh để đáp ứng trên light mode.

### Focus Visibility

- Mọi phần tử tương tác phải có focus indicator nhìn thấy được.
- Dùng `focus:ring-2 focus:ring-sky-500 focus:ring-offset-2` là chấp nhận được.
- Không suppress outline bằng `outline-none` trừ khi đã có thay thế.

### Keyboard Navigation

- Mọi control reachable qua Tab theo thứ tự logic.
- Enter/Space kích hoạt button, link, switch.
- Escape đóng modal, drawer, dropdown.
- Trap focus bên trong modal đang mở.

### Screen Readers

- Dùng semantic HTML (`<button>`, `<a>`, `<label>`, `<table>`) trước khi dùng ARIA.
- Icon-only button phải có `aria-label`.
- Content động (toast, live list) dùng `aria-live="polite"`.
- Form error liên kết với field qua `aria-describedby`.

### Motion

- Tôn trọng `prefers-reduced-motion`.
- Tắt animation không thiết yếu cho user yêu cầu giảm motion.
- Feedback thiết yếu (button press, state change) vẫn được giữ nhưng phải instant hoặc rất ngắn.

### Color Independence

- Không bao giờ dùng màu độc lập để truyền đạt status.
- Kết hợp màu status với icon hoặc text label.
- Ví dụ: badge "Từ chối" màu đỏ phải có chữ "Từ chối" hoặc icon ban, không chỉ có màu đỏ.

---

## 12. Notifications, Toasts & Snackbars

Dùng thông báo tạm thời cho kết quả không cần modal.

### Vị trí

- Desktop: góc trên phải, xếp chồng dọc.
- Mobile: giữa dưới, tối đa 2 toast.

### Thời lượng

- Success / Info: 4 giây.
- Warning: 6 giây.
- Error: 8 giây hoặc persistent đến khi dismiss.
- Cần hành động: persistent + nút dismiss rõ ràng.

### Cấu trúc

Mỗi toast chứa:

1. Icon semantic (16px) khớp intent.
2. Message 1 dòng (tối đa 2 dòng trên mobile).
3. Text action tùy chọn (VD: `Hoàn tác`, `Xem`).
4. Nút dismiss.

Không toast nhiều đoạn. Không marketing copy trong toast.

### Xếp chồng & Giới hạn

- Tối đa 3 toast cùng lúc.
- Toast cũ fade out trước.
- Toast mới slide in (`translate-y` + opacity, 200ms).

### Màu sắc

| Intent | Icon | Background | Border | Text |
|---|---|---|---|---|
| Success | CheckCircle | `bg-emerald-50` | `border-emerald-200` | `text-emerald-800` |
| Error | XCircle | `bg-rose-50` | `border-rose-200` | `text-rose-800` |
| Warning | AlertTriangle | `bg-amber-50` | `border-amber-200` | `text-amber-800` |
| Info | Info | `bg-sky-50` | `border-sky-200` | `text-sky-800` |

Không dùng colored shadow hoặc glow sau toast.

---

## 13. Loading & Skeleton States

Không bao giờ để khoảng trắng trống khi data đang load. User phải thấy có chuyện đang xảy ra và content sẽ xuất hiện ở đâu.

### Skeleton Patterns

Dùng `bg-slate-200 animate-pulse` với hình dạng bo tròn khớp content thật:

- Dòng text: `h-4 rounded`, width `w-full`, `w-3/4`, `w-1/2`.
- Header: `h-5 rounded w-1/3`.
- Avatar: `rounded-full bg-slate-200`.
- Button: `h-10 rounded-lg w-24 bg-slate-200`.
- Card: tái tạo padding, border, radius của card thật, bên trong là skeleton block.

### Table Skeleton

- Hiển thị 5–8 skeleton row.
- Khớp số cột và width xấp xỉ.
- Có skeleton header row.
- Giữ border table để layout không shift khi data về.

### Card Skeleton

- Skeleton header bar (icon + title).
- 2–4 skeleton text line bên trong.
- Giữ nguyên padding, border, radius của card.

### Spinner Usage

- Action inline (button click): thay text bằng spinner 16px trong cùng button, không đổi kích thước button.
- Vùng nhỏ (filter count): spinner inline bên cạnh text.
- Full page: dùng skeleton layout khớp layout cuối. Tránh generic centered spinner trừ khi toàn bộ layout chưa biết.

### Progressive Loading

- Load text và layout trước.
- Lazy load nội dung nặng: chart, ảnh lớn, preview embed.
- Hiển thị placeholder structure ngay, sau đó hydrate content.

### Error sau Loading

Nếu load thất bại, thay skeleton bằng inline error trong cùng container. Không để spinner quay vô tận.

---

## 14. Data Visualization & Charts

Chỉ dùng chart khi nó trả lời câu hỏi vận hành thực tế. Chart trang trí bị cấm.

### Khi nào dùng

- Line chart: trend theo thời gian.
- Bar chart: so sánh giữa các nhóm.
- Pie / donut: tỷ lệ đơn giản, tối đa 5 phần.
- Table: luôn ưu tiên cho giá trị chính xác và data dày đặc.

### Palette cho chart

Mở rộng từ semantic palette. Không thêm màu mới.

| Role | Màu |
|---|---|
| Primary series | `sky-600` |
| Secondary series | `slate-400` |
| Success / Positive | `emerald-500` |
| Warning | `amber-500` |
| Danger / Negative | `rose-500` |
| Grid background | `slate-100` |
| Axis text | `slate-500` |

Không dùng gradient fill. Dùng flat color với opacity nhẹ (VD: `fill-sky-600/20`) cho vùng dưới line.

### Labels & Legends

- Legend đặt trong hoặc sát chart, không phải panel riêng.
- Axis label: `text-xs text-slate-500`.
- Data label trong bar chỉ khi đọc được; nếu không thì dùng tooltip.

### Tooltips

- 1 dòng data.
- Dark background: `bg-slate-900 text-white text-xs rounded-md px-2 py-1`.
- Không shadow spectacle.
- Hiển thị value + unit + date/context.

### Empty Chart State

Tuân theo empty-state rules: icon + tiêu đề ngắn + câu mô tả + action (nếu có). Không hiển thị grid trống với trục.

---

## 15. Iconography Deep-Dive

Một hệ icon nhất quán giữ giao diện yên tĩnh và dễ scan.

### Icon Set

- **Lucide React** là thư viện icon duy nhất được chấp nhận.
- Không trộn với Material Icons, Font Awesome, Heroicons, hoặc filled set khác.

### Stroke & Style

- Stroke width: default Lucide (tương đương 1.5px–2px).
- Tất cả icon phải outline style. Không dùng filled variant trừ khi có trong Lucide và dùng nhất quán.

### Kích thước

| Token | Size | Dùng cho |
|---|---|---|
| Inline | 14px–16px | Button, table action, form hint |
| Default | 16px | Menu item, badge, inline metadata |
| Header | 20px | Page header, section title, prominent action |
| Empty state | 24px–32px | Empty state, confirmation dialog |
| Decorative | 40px+ | Hiếm; chỉ khi icon là nội dung duy nhất của vùng lớn |

### Màu sắc

- Mặc định inherit text color.
- Status icon dùng semantic color (emerald, amber, rose, sky).
- Không apply màu tùy tiện lên icon.

### Căn chỉnh

- Căn giữa icon theo chiều dọc với text bên cạnh.
- Button icon + label: icon trái, text phải, gap `8px`.
- Button icon-only: touch target vuông, tối thiểu `40px`.

### Cấm

- Emoji làm icon (`📁`, `⚠️`).
- Custom SVG illustration trong UI chrome.
- Icon 3D hoặc skeuomorphic.
- Icon animated hoặc xoay trừ spinner loading.

---

## 16. File Attachment & Upload Patterns

Upload và quản lý file là nghiệp vụ thường gặp. Giữ thực dụng.

### Upload Zone

- Border dashed: `border-2 border-dashed border-slate-300 rounded-lg`.
- Background hover/active: `bg-slate-50`.
- Nội dung: icon upload (24px) + 1 dòng text (`Kéo thả hoặc chọn file`) + gợi ý kích thước (`Tối đa 10MB — PDF, DOCX`).
- Click bất kỳ đâu trong zone để mở file picker.

### Danh sách file

- Hiển thị dạng row, không phải card.
- Mỗi row: icon loại file (16px) + tên file + dung lượng + nút xóa.
- Row style: `border-b border-slate-100 py-2`.
- Tên file dài: ellipsis + tooltip hiện đầy đủ.

### Tiến trình upload

- Thanh mỏng inline trong row: `h-1 bg-sky-600 rounded-full`.
- Không dùng modal dialog cho tiến trình upload.

### Xử lý lỗi

- Message inline trong row: `text-xs text-rose-600`.
- VD: `File vượt quá 10MB`, `Chỉ chấp nhận PDF`.

### Preview

- Thumbnail ảnh: 40×40px `rounded-md`.
- File không phải ảnh: icon loại file + tên. Không preview giả.

### Giới hạn & Validation

- Hiển thị định dạng chấp nhận và max size **trước** khi user chọn file.
- Validate ngay khi chọn, không chờ submit form.

---

## 17. Navigation Deep-Dive

Navigation giúp định hướng mà không cạnh tranh với content.

### Sidebar

- Tối đa 1 level hiển thị cùng lúc.
- Submenu collapsible với chevron indicator.
- Không mega-menu. Không horizontal scroll trong sidebar.
- Active item: `bg-sky-50 text-sky-700 border-r-2 border-sky-600`.
- Không kết hợp bold + underline + background cho active state. Chọn một treatment rõ ràng.

### Breadcrumbs

- Chỉ dùng khi depth > 2.
- Format: `Trang chủ > Quản lý dự án > Chi tiết`.
- Style: `text-sm text-slate-500`.
- Phân đoạn cuối là plain text, không phải link.
- Có thể thay "Trang chủ" bằng icon Home.

### Overflow

- Label sidebar dài: ellipsis + tooltip.
- Nhiều tab: horizontal scroll với fade indicator, hoặc dropdown overflow.
- Không bao giờ wrap tab text sang 2 dòng.

### Navigation trên Mobile

- Drawer trượt vào từ trái.
- Overlay: `bg-slate-900/50`.
- Đóng khi tap backdrop hoặc swipe.
- Giữ cùng cấu trúc menu như desktop; không tạo hierarchy mobile riêng.

### Local Navigation (Sub-tabs / Sub-nav)

- Dùng tab gọn hoặc mini-nav dọc trong card.
- Tab height: `36px–40px` trên desktop.
- Active tab: bottom border hoặc soft background. Không block màu đậm.

---

## 18. Onboarding, Tooltips & Coach Marks

User enterprise không cần guided tour. Chỉ cung cấp trợ giúp theo ngữ cảnh khi thật cần.

### Tooltips

- Tối đa 1 câu.
- Dark style: `bg-slate-900 text-white text-xs rounded-md px-2 py-1`.
- Mũi tên tùy chọn.
- Trigger: hover trên desktop, long-press trên mobile (hoặc tap icon info).
- Không đặt nội dung tương tác bên trong tooltip.

### Coach Marks / Spotlights

- Chỉ dùng cho tính năng thực sự mới hoặc phức tạp.
- Chỉ 1 spotlight tại một thời điểm.
- Phải dismiss được (nút X hoặc `Đã hiểu`).
- Không wizard nhiều bước.
- Làm tối phần còn lại bằng `bg-slate-900/40`.

### Badge Tính năng Mới

- `rounded-sm bg-sky-100 text-sky-700 text-xs px-1.5`.
- Tự động xóa sau lần dùng đầu hoặc trong vòng 7 ngày.

### Empty State là Onboarding

- Nút hành động chính trong empty state chính là onboarding CTA.
- Không thêm panel "Hướng dẫn" riêng nếu empty state đã nói rõ bước tiếp theo.

### Cấm Tour Bắt Buộc

- Không block UI bằng modal "Welcome" bắt buộc.
- Không làm tối toàn màn hình khi đăng nhập lần đầu.
- Gợi ý theo ngữ cảnh luôn được ưu tiên hơn hướng dẫn tuần tự.

---

## Tailwind CSS v4 — Ghi chú triển khai

**Dự án này dùng Tailwind CSS v4.** Không có file `tailwind.config.ts`. Tất cả design tokens khai báo trong `app/globals.css` bằng `@theme inline`.

### Tech stack:
- `app/globals.css` — Nơi khai báo design tokens (CSS `@theme inline`)
- `@import "tailwindcss"` — Import Tailwind v4
- KHÔNG có `tailwind.config.ts`

### Bảng mapping Design Token → Tailwind Class:

| Design Token | Tailwind Class |
|---|---|
| Primary | `sky-600` |
| Primary Hover | `sky-700` |
| Primary Soft | `sky-50` |
| Success | `emerald-600` hoặc `emerald-700` |
| Success Soft | `emerald-50` |
| Warning | `amber-500` hoặc `amber-600` |
| Warning Soft | `amber-50` |
| Danger | `rose-600` |
| Danger Soft | `rose-50` |
| Background | `slate-50` |
| Surface | `white` |
| Text Primary | `slate-900` |
| Text Secondary | `slate-600` |
| Text Muted | `slate-500` |
| Border Default | `slate-200` |
| Border Strong | `slate-300` |

### Màu CẤM tuyệt đối:
- `bg-gradient-to-*` (gradient cards)
- `bg-[linear-gradient(...)]`
- `purple-*`, `violet-*`, `indigo-*` (AI-style)
- `text-black` trên nền trắng
- `text-white` trên nền màu không đậm

### Border Radius Scale (dùng Tailwind):

| px | Tailwind | Dùng cho |
|---|---|---|
| 6 | `rounded-sm` | Badges, chips |
| 10 | `rounded` hoặc `rounded-md` | Buttons, inputs |
| 12 | `rounded-lg` | Cards, menus |
| 16 | `rounded-xl` | Panels, modals |
| 20 | `rounded-2xl` | Major layout blocks |
| 9999 | `rounded-full` | Avatar, pill (hạn chế) |

**Cấm:** `rounded-[28px]`, `rounded-[32px]`, `rounded-[24px]` — không nằm trong scale.

### Control Heights:
- Input/Select: `h-11` (44px)
- Button (default): `h-10` hoặc `h-11` (40-44px)
- Button (small): `h-8` (32px)

### Shadows:
- Cards: `shadow-sm` hoặc `border + shadow-sm`
- Modals: `shadow-xl` hoặc `shadow-md`
- Cấm: `shadow-[0_20px_60px...]`, `shadow-2xl` (trừ khi modal cần emphasis)

### Overlay/Backdrop:
- `bg-slate-900/40` hoặc `bg-slate-900/50` (không `bg-slate-950/55`)

---

## Audit — Trạng thái hiện tại các user pages

Đã audit toàn bộ 20+ user-facing pages trong `app/dashboard/user/`.

### CRITICAL — Vi phạm nghiêm trọng, cần sửa trước

- **`app/dashboard/user/page.tsx`** — KPI cards dùng gradient (`from-green-500 to-green-600`, `from-purple-500 to-purple-600`, etc.)
- **`app/dashboard/user/spaces/page.tsx`** — Pervasive màu green không đúng spec palette
- **`app/dashboard/user/project-init/page.tsx`** — `rounded-[28px]`, `shadow-[0_20px_60px...]`, `bg-[linear-gradient(...)]`

### MAJOR — Vi phạm nhiều

- **`app/dashboard/user/director-projects/page.tsx`** — Arbitrary colors (blue/emerald/amber/rose/purple) trong status badges
- **`app/dashboard/user/projects/[id]/page.tsx`** — `rounded-[32px]`, `text-[36px]`, `shadow-2xl`
- **`app/dashboard/user/projects/page.tsx`** — h2 30px (spec: 24px), indigo/violet/teal palette
- **`app/dashboard/user/project-init/[id]/supplement/page.tsx`** — Purple/orange palette

### MINOR — Vi phạm nhỏ

- **`app/dashboard/user/ai/page.tsx`** — H1 `text-xl` (spec: 30px), `text-black`
- **`app/dashboard/user/chat/page.tsx`** — H1 `text-xl`
- **`app/dashboard/user/company-projects/page.tsx`** — `text-black` pervasive
- **`app/dashboard/user/company-structure/page.tsx`** — `text-green-600` không đúng spec
- **`app/dashboard/user/customers/page.tsx`** — `rounded-full`, blue-50 ngoài spec
- **`app/dashboard/user/documents/page.tsx`** — `text-black` pervasive
- **`app/dashboard/user/payments/page.tsx`** — `text-black`, h-12 inputs
- **`app/dashboard/user/reports/page.tsx`** — `text-black`
- **`app/dashboard/user/settings/page.tsx`** — `h-12` inputs, `rounded-[24px]`

### Clean (gần nhất với spec)

- **`app/dashboard/user/meeting-rooms/page.tsx`** — ~85% compliant
- **`app/dashboard/user/consortium/page.tsx`** — nearly clean

**Thứ tự ưu tiên fix:** Critical → Major → Minor

Xem chi tiết đầy đủ và pattern fix trong `DESIGN_IMPLEMENTATION_GUIDE.md`.
