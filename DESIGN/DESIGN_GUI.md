# Design GUI

## 1. Purpose

`DESIGN_GUI.md` defines the shared GUI rules for web and mobile products across projects.

This file exists to:

- establish a consistent baseline for layout, hierarchy, spacing, components, and interaction behavior
- reduce UI drift between products, teams, and implementation styles
- support product-specific design without changing the core visual language
- provide a reference for designers, developers, reviewers, and AI assistants before making UI decisions

This guide is platform-aware but product-agnostic.

It is intended to work across:

- dashboards
- internal tools
- CRUD systems
- operational workflows
- detail pages
- form-heavy products
- mobile applications
- consumer-facing product screens

This document is intentionally prescriptive.

When a pattern is defined here, it should be treated as the default unless there is a clear functional, accessibility, performance, or maintainability reason to deviate.

This is not a brand book, a feature specification, or a full component inventory.

It is a shared rule set for building clear, usable, and consistent interfaces.

## 2. Design Philosophy

The GUI should feel:

- clean
- product-first
- calm
- modern
- practical
- slightly premium
- not decorative

The interface must prioritize clarity, usability, and structure before visual novelty.

Every screen should feel intentional, but never over-designed.

The design language should be flexible enough to support both dense workflows and polished modern products without changing its core character.

### Principles

- Favor utility over ornament.
- Prefer restrained elegance over visual drama.
- Keep the interface quiet so the content stays central.
- Use hierarchy to guide attention, not effects.
- Design for repeated use, not one-time visual impact.
- Keep the system durable across product cycles.
- Preserve consistency across screens, states, and flows.

### What The System Should Not Be

- flashy
- trend-driven
- decorative
- presentation-first
- emotionally exaggerated
- template-like
- dependent on novelty to feel modern

### Quality Bar

A good screen should feel clear on first scan, comfortable on repeated use, and credible in a real product environment.

It should look refined without feeling precious, and minimal without feeling empty.

## 3. Core Visual Language

### Typography

Use a neutral modern sans-serif as the default type system.

Preferred direction:

- `Inter` as the default recommendation
- `SF Pro`, `Segoe UI`, or platform-native equivalents when needed
- `Plus Jakarta Sans` or `Manrope` only when the product needs a slightly softer tone without becoming playful

Typography should feel:

- clear
- quiet
- highly legible
- product-oriented

Rules:

- use a restrained type scale
- rely on regular, medium, and semibold as the primary weights
- keep hierarchy explicit through size, weight, and spacing
- use sentence case by default
- keep body copy stable in dense interfaces

Avoid:

- decorative display fonts
- condensed fonts
- handwritten or expressive fonts
- AI-styled typography
- heavy uppercase styling
- wide letter spacing used as decoration
- oversized hero typography inside product UI

### Color System

The base UI should be light by default.

Use color to communicate structure and meaning, not decoration.

Base palette behavior:

- white and soft off-white surfaces
- cool gray and slate neutrals
- deep slate or navy for primary text
- muted slate for secondary text
- restrained blue for primary actions and active states
- muted green only for positive states
- muted amber only for warnings
- muted red only for destructive or critical states

Suggested color roles:

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

- keep the palette neutral and balanced
- use one primary accent color consistently
- define semantic colors clearly
- maintain accessible contrast in all states
- prefer flat color layers and soft tonal shifts

Avoid:

- gradient-heavy UI
- neon accents
- purple AI-style palettes
- black-heavy dramatic surfaces
- glow effects
- loud decorative color combinations

### Spacing

Spacing should feel consistent and quiet.

The UI should breathe, but never feel empty.

Rules:

- use a predictable spacing scale such as `4, 8, 12, 16, 24, 32, 48`
- keep section rhythm stable
- use tighter spacing only when density is functionally required
- prefer structural spacing over expressive composition

Avoid:

- one-off spacing values without reason
- oversized section gaps
- giant card padding
- very tall controls
- floating isolated content blocks

### Radius

Rounded corners should be modern but restrained.

Rules:

- use small-to-medium radius as the default
- apply the same radius scale across related component families
- reserve larger radius for major containers only when separation needs emphasis

Avoid:

- over-rounded bubble UI
- pill shapes everywhere
- playful geometry that weakens the product tone

### Borders

Use borders as structure, not decoration.

Rules:

- prefer low-contrast borders for separation
- use borders consistently across inputs, cards, tables, and overlays
- keep border thickness stable across the system
- use border changes for hover, focus, and selected states in a restrained way

Avoid:

- heavy outlines without purpose
- inconsistent border weights

### Shadows

Shadows should support elevation, not create spectacle.

Rules:

- use soft, low-opacity shadows
- keep shadow usage minimal in dense interfaces
- rely on borders and spacing before adding shadow complexity
- define a small number of shadow tiers for surfaces, overlays, and floating controls

Avoid:

- glow
- colored shadows
- long shadow spread
- layered theatrical depth

### Icons

Use a single coherent icon set across the product.

Preferred direction:

- Lucide or an equivalent minimal system icon set

Rules:

- keep icon style aligned with typography
- maintain consistent stroke weight, size, and alignment
- use icons to support recognition, not replace labels where clarity matters

Avoid:

- decorative icon containers by default
- over-detailed illustration-style icons
- mixing incompatible icon styles

### Motion

Motion should clarify state changes, not attract attention.

Rules:

- keep transitions short, subtle, and purposeful
- use motion for feedback, overlays, navigation changes, and state change clarity
- respect reduced-motion preferences
- prefer fades, small translates, and simple easing

Avoid:

- animated gradients
- decorative loops
- bouncy motion
- parallax
- theatrical page transitions

### Hard Design Tokens

Use these tokens as the system default.

Do not invent ad hoc values when a token already exists.

#### Font Family Tokens

- `font.sans`: `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- `font.mono`: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace`

#### Color Tokens

All colors are light-theme first and calibrated for a calm product UI.

Use semantic tokens for interface logic.

| Token | Hex | Usage |
|---|---:|---|
| `color.bg` | `#F5F7FB` | App background |
| `color.surface` | `#FFFFFF` | Primary surfaces, cards, panels |
| `color.surfaceSubtle` | `#F3F6FB` | Secondary surfaces, quiet containers |
| `color.surfaceMuted` | `#E2E8F0` | Dividers, inactive fills |
| `color.textPrimary` | `#0F172A` | Main text |
| `color.textSecondary` | `#475569` | Supporting text |
| `color.textMuted` | `#64748B` | Helper text, placeholders |
| `color.textDisabled` | `#94A3B8` | Disabled text |
| `color.borderDefault` | `#E2E8F0` | Standard borders |
| `color.borderStrong` | `#CBD5E1` | Active or emphasized borders |
| `color.focusRing` | `#7DD3FC` | Focus ring and keyboard emphasis |
| `color.primary` | `#0284C7` | Primary actions, links, active states |
| `color.primaryHover` | `#0369A1` | Hover state for primary actions |
| `color.primarySoft` | `#F0F9FF` | Selected backgrounds, soft emphasis |
| `color.success` | `#15803D` | Positive states |
| `color.successSoft` | `#F0FDF4` | Positive backgrounds |
| `color.warning` | `#B45309` | Warning states |
| `color.warningSoft` | `#FFFBEB` | Warning backgrounds |
| `color.danger` | `#BE123C` | Destructive actions, errors |
| `color.dangerSoft` | `#FFF1F2` | Error backgrounds |
| `color.info` | `#0284C7` | Informational states |
| `color.infoSoft` | `#F0F9FF` | Informational backgrounds |

Rules:

- use flat color layers and soft tonal shifts
- keep one primary accent color consistent across the product
- use semantic colors for meaning, not decoration

#### Typography Scale

Use a restrained typographic scale with readable line heights and stable weights.

| Token | Size | Line Height | Weight | Usage |
|---|---:|---:|---:|---|
| `type.display` | `36px` | `44px` | `700` | Rare large emphasis |
| `type.h1` | `30px` | `38px` | `700` | Page titles |
| `type.h2` | `24px` | `32px` | `600` | Section headings |
| `type.h3` | `20px` | `28px` | `600` | Card titles, subsection headers |
| `type.body` | `16px` | `24px` | `400` | Default body text |
| `type.bodyStrong` | `16px` | `24px` | `500` | Emphasized body text |
| `type.bodySmall` | `14px` | `20px` | `400` | Secondary content, dense UI |
| `type.bodySmallStrong` | `14px` | `20px` | `500` | Small emphasis text |
| `type.caption` | `12px` | `16px` | `500` | Labels, metadata, hints |
| `type.overline` | `11px` | `16px` | `600` | Rare utility labels |

Rules:

- keep hierarchy explicit through size, weight, and spacing
- use sentence case by default
- avoid decorative letter spacing except for rare utility labels

#### Spacing Scale

Use the nearest spacing token instead of custom values whenever possible.

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
| `radius.none` | `0px` | Flush edges, data grids |
| `radius.sm` | `6px` | Small controls, compact badges |
| `radius.md` | `10px` | Inputs and buttons |
| `radius.lg` | `12px` | Cards, menus, standard surfaces |
| `radius.xl` | `16px` | Panels, modals, large containers |
| `radius.2xl` | `20px` | Major layout blocks |
| `radius.full` | `999px` | Only when a pill shape is clearly required |

#### Border Thickness

| Token | Value | Usage |
|---|---:|---|
| `border.1` | `1px` | Default borders, inputs, cards, dividers |
| `border.2` | `2px` | Focus states, selected states, strong emphasis |
| `border.3` | `3px` | Rare emphasis only |

#### Shadow Tiers

Shadows should support elevation, not spectacle.

| Token | Value | Usage |
|---|---|---|
| `shadow.0` | `none` | Flat surfaces |
| `shadow.1` | `0 1px 2px rgba(15, 23, 42, 0.04)` | Subtle raised cards |
| `shadow.2` | `0 4px 12px rgba(15, 23, 42, 0.06)` | Floating menus, compact panels |
| `shadow.3` | `0 10px 24px rgba(15, 23, 42, 0.08)` | Modals, drawers, prominent surfaces |
| `shadow.4` | `0 18px 40px rgba(15, 23, 42, 0.10)` | Highest elevation only |

#### Control Heights

| Token | Value | Usage |
|---|---:|---|
| `control.xs` | `28px` | Tiny chips, compact filters |
| `control.sm` | `32px` | Dense lists, compact buttons |
| `control.md` | `40px` | Default buttons, inputs, selects |
| `control.lg` | `44px` | Touch-friendly controls |
| `control.xl` | `48px` | Large forms, high-visibility actions |

#### Icon Sizes

| Token | Value | Usage |
|---|---:|---|
| `icon.xs` | `12px` | Dense data labels, tiny affordances |
| `icon.sm` | `14px` | Inline metadata, compact UI |
| `icon.md` | `16px` | Default icon size |
| `icon.lg` | `20px` | Prominent actions, headers |
| `icon.xl` | `24px` | Rare emphasis, empty states |

#### Motion Durations and Easings

| Token | Value | Usage |
|---|---:|---|
| `motion.fast` | `120ms` | Micro-interactions, hover feedback |
| `motion.base` | `160ms` | Standard transitions |
| `motion.medium` | `220ms` | Panels, menus, state changes |
| `motion.slow` | `280ms` | Modals, drawers, larger reveals |
| `motion.standardEasing` | `cubic-bezier(0.2, 0, 0, 1)` | Default easing |
| `motion.enterEasing` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrance transitions |
| `motion.exitEasing` | `cubic-bezier(0.4, 0, 1, 1)` | Exit transitions |

#### Content Width Tokens

| Token | Value | Usage |
|---|---:|---|
| `container.narrow` | `720px` | Reading-heavy forms, focused flows |
| `container.default` | `960px` | Standard pages |
| `container.wide` | `1280px` | Detail pages, dashboards |
| `container.full` | `1440px` | Comparison-heavy and data-heavy screens |

## 4. Component Rules

### Buttons

Buttons should be compact, clear, and action-oriented.

Rules:

- primary buttons use a clean blue fill with white text
- secondary buttons use a white or very light gray surface with a subtle border
- destructive buttons use muted red, never aggressive saturated red
- button height, padding, and radius must stay consistent across the system
- labels must describe a specific action

Avoid:

- oversized pill buttons
- decorative button styling
- vague labels such as `Explore`, `Continue`, or `Open workspace`

### Inputs, Selects, and Textareas

All form controls should share one visual language.

Rules:

- keep height, padding, border, radius, and focus behavior consistent
- use focus states based on border and a soft ring
- keep placeholder text readable and clearly secondary
- make read-only fields visibly different from editable controls
- keep textareas structured and calm, with enough internal spacing

Avoid:

- dramatic glow focus states
- oversized fields without functional need
- placeholders that try to carry the full meaning of the field

### Cards

Cards should group information, not decorate empty space.

Rules:

- use white surfaces, light borders, and minimal elevation
- keep card headers concise and relevant
- use cards to create information grouping, not visual fragmentation

Avoid:

- excessive nesting
- card-inside-card patterns without structural value
- large decorative empty cards

### Tables

Tables are preferred for dense operational data.

Rules:

- optimize for scanability first
- keep header hierarchy clear
- preserve stable row rhythm
- use statuses and row actions carefully so readability remains primary

Avoid:

- decorative table chrome
- excessive inline action clutter
- styling that competes with the data itself

### Tabs and Local Navigation

Tabs should be compact, legible, and easy to scan.

Rules:

- use tabs for closely related views
- keep active state clear but restrained
- use subtle blue emphasis instead of loud color blocks

Avoid:

- oversized tabs
- decorative tab systems
- using tabs where page structure would be clearer

### Modals and Drawers

Use overlays only when they improve task flow.

Rules:

- use modals for focused actions, confirmations, and short workflows
- use drawers when underlying page context still matters
- keep titles direct and explicit
- keep overlay content practical and compact

Avoid:

- marketing-style modal intros
- decorative illustrations by default
- long workflows inside cramped dialogs

### Badges, Status, and Alerts

Status UI should communicate meaning with minimum noise.

Rules:

- map colors consistently to meaning
- keep status treatments soft and muted
- keep alerts brief, structured, and actionable
- include impact and next step only when useful

Avoid:

- decorative badges
- inconsistent meaning-color mapping
- oversized alert blocks that interrupt the page unnecessarily

### Empty States

Empty states should help the user move forward.

Rules:

- include one short title
- include one short supporting sentence
- include one relevant action when action is possible

Avoid:

- mascot-style illustrations
- filler copy
- abstract product metaphors
- entertaining the user instead of guiding them

### Hard Component Specs

#### Density Rules

- default desktop control height: `40px` to `44px`
- default touch control height: `44px` to `48px`
- compact density is allowed only in dense tables, toolbars, and admin workflows
- do not mix densities within the same surface unless controls have different functional roles

#### State Rules

Every interactive component should define these states when relevant:

- default
- hover
- active or pressed
- focus
- disabled
- loading
- selected or checked
- error
- read-only

Rules:

- focus must always be visible
- disabled states must remain legible
- loading states must preserve size and avoid layout shift
- selected states must be obvious but restrained
- error states must be clear without overpowering the layout

#### Buttons

Recommended sizes:

- `Small`: `32px` height
- `Medium`: `40px` height
- `Large`: `48px` height

Rules:

- use one primary button per surface
- use secondary buttons for supporting actions
- use destructive buttons only for irreversible or high-risk actions
- keep labels short, specific, and action-based
- use icon-only buttons only when the action is universally recognizable

#### Inputs, Selects, and Textareas

Recommended sizes:

- input and select: `40px` default, `44px` touch
- compact controls: `36px` only in dense layouts
- textarea: minimum `96px` height

Rules:

- place labels above the control by default
- keep helper text short and useful
- show errors immediately below the field
- align border, radius, and focus treatment across field types
- use placeholder text as a hint, not as a label replacement

#### Checkboxes, Radios, and Switches

Recommended sizes:

- checkbox and radio visual size: `16px` to `20px`
- minimum click target: `44px`
- switch track height: `20px` to `24px`

Rules:

- use checkboxes for multiple independent selections
- use radios for a single choice within a fixed set
- use switches only for immediate binary settings
- make the full label area clickable when possible

#### Cards

Recommended spacing:

- padding: `16px` to `24px`
- internal section spacing: `12px` to `16px`

Rules:

- keep headers concise
- use light borders and minimal elevation
- keep actions in predictable areas
- avoid nested cards unless they represent real information layers

#### Tables

Recommended sizes:

- compact row height: `44px` to `48px`
- comfortable row height: `52px` to `56px`
- header height: `40px` to `44px`

Rules:

- keep header labels short and explicit
- right-align numeric values when it improves scanning
- keep row actions minimal and predictable
- support sticky headers for long tables when useful

#### Tabs

Recommended sizes:

- tab height: `36px` to `40px` on desktop
- tab height: `44px` on touch layouts

Rules:

- use tabs only for sibling views in the same task context
- keep labels short and parallel
- support overflow gracefully when tab count grows

#### Badges

Recommended sizes:

- height: `20px` to `24px`

Rules:

- use badges for status, type, priority, or count
- keep text short, usually one to three words
- map colors consistently to meaning

#### Alerts

Rules:

- use alerts for outcomes, blockers, warnings, and critical context
- keep alerts short and actionable
- place alerts near the relevant content or action
- include a title and one supporting sentence when needed

#### Modals

Recommended widths:

- `Small`: `480px`
- `Medium`: `640px`
- `Large`: `800px`

Rules:

- use modals for confirmations, lightweight editing, and short decision flows
- keep titles direct and specific
- use one primary action and one secondary cancel action in most cases
- do not place long forms in modals when a page or drawer is clearer

#### Drawers

Recommended widths:

- desktop: `480px` to `640px`
- mobile: full screen

Rules:

- use drawers for inspect, edit, and detail overlays that benefit from context retention
- keep header, content, and actions structurally clear
- do not overload drawers with unrelated tasks

#### Empty States

Rules:

- keep the layout centered within the relevant region
- explain why the state is empty when it matters
- offer one primary next step
- do not make empty states larger than the content they replace

#### Page Headers

Recommended structure:

- title
- optional description
- supporting controls
- primary action

Rules:

- keep headers compact
- use subtitle text only when it adds real context
- align header actions consistently across the product
- do not turn product pages into hero sections

## 5. Layout Rules and Responsive Standards

### App Shell

The app shell should provide orientation without competing with the page content.

Rules:

- use a shell only when persistent navigation or global utilities are needed
- keep the shell quiet and structured
- prioritize content over chrome
- choose top, side, or bottom navigation based on product structure, not habit

### Desktop Page Structure

Desktop pages should follow a predictable hierarchy:

- header
- controls
- content

Rules:

- keep the page header compact
- place primary actions near the title or in a consistent action area
- keep introductory copy minimal
- let useful content start early in the viewport

Avoid:

- hero-style product openings
- large decorative banners inside product screens

### Content Width

Content width should be controlled intentionally.

Rules:

- use wider layouts for dense tools, dashboards, and comparison-heavy views
- use narrower layouts for forms, reading-heavy screens, and detail views
- preserve comfortable line length and scanability

Avoid:

- edge-to-edge long-form content
- overly narrow data-heavy screens

### Dashboard Layout

Dashboards should support decision-making, not presentation.

Rules:

- use cards only when they communicate real metrics, status, or trends
- keep the hierarchy clear: key signals first, supporting detail second
- use charts only when they answer a practical question
- keep the page compact enough for repeated daily use

Avoid:

- decorative analytics blocks
- card grids with no operational value

### List Pages

List pages should optimize filtering, scanning, and row-level action.

Rules:

- group filters logically and keep them compact
- use tables or list cards that support quick comparison
- keep secondary controls visible but restrained
- preserve stable row rhythm and clear status cues

Avoid:

- filter panels that dominate the page
- scattered actions that weaken scanability

### Detail Pages

Detail pages should emphasize the main record or object.

Rules:

- give the primary content area the most width
- keep side navigation, metadata, and supporting panels compact
- use progressive disclosure for secondary information

Avoid:

- too many equal-weight regions
- side panels that compete with the main detail

### Form Pages

Forms should feel guided and efficient.

Rules:

- group related fields into clear sections
- use one column by default
- use a second column only when it improves speed and readability
- keep labels, helper text, and validation close to the field
- keep primary actions in a predictable location

Avoid:

- very long unbroken form stacks
- decorative field arrangements

### Mobile Screens

Mobile screens should preserve the same design language in a tighter rhythm.

Rules:

- reduce chrome and density, but keep hierarchy intact
- simplify controls and labels where needed
- prefer stacked layouts and compact surfaces
- keep important actions easy to reach

Avoid:

- importing desktop spacing directly into mobile
- shrinking desktop layouts instead of redesigning hierarchy

### Section Spacing

Section spacing should create structure, not drama.

Rules:

- use consistent vertical rhythm between sections
- remove empty wrappers and unnecessary containers
- keep useful content visible as early as possible

Avoid:

- oversized top padding
- empty spacing used as decoration

### Responsive Standards

The system must be responsive by default.

Recommended breakpoints:

- `Mobile`: 320px to 767px
- `Tablet`: 768px to 1023px
- `Desktop`: 1024px to 1439px
- `Wide Desktop`: 1440px and above

### Responsive Layout Behavior

Rules:

- use one primary column on mobile
- allow two-column layouts on tablet only when readability remains strong
- use wider grids on desktop for efficiency, not decoration
- rebalance spacing, density, and order as layouts collapse

Avoid:

- preserving desktop column counts when they reduce usability
- stacking desktop blocks blindly without rethinking priority

### Tables on Small Screens

Rules:

- allow horizontal scrolling only inside controlled containers when necessary
- prefer stacked record cards or compact list items when that improves scanability
- reduce visible columns to the most important fields on smaller screens

Avoid:

- forcing full desktop tables into narrow layouts

### Forms on Small Screens

Rules:

- collapse multi-column forms to one column on mobile
- keep labels, helper text, and errors close to the field
- preserve visual grouping after stacking

Avoid:

- tight vertical compression that hurts comprehension or editability

### Modal Behavior

Rules:

- use centered modals on desktop for short focused workflows
- use drawers or side panels when screen context matters
- use bottom sheets or full-screen overlays on mobile for longer tasks

Avoid:

- tiny desktop-style modals on phones

### Touch Targets

Rules:

- keep controls easy to tap
- preserve adequate spacing between actions
- maintain usability even when the visual design stays compact

Avoid:

- cramped action clusters
- touch targets that prioritize density over reliability

### Responsive Typography

Rules:

- scale headings down slightly on smaller screens
- keep body text stable and readable
- preserve hierarchy across breakpoints

Avoid:

- oversized headings on mobile product screens
- compressing typography until the interface feels weak

### Hard Responsive Patterns

#### Breakpoint Behavior

- `Mobile`: use a single-column flow, full-width surfaces, and bottom-up hierarchy
- `Tablet`: keep the primary hierarchy intact and allow limited two-column layouts only when both columns remain readable
- `Desktop`: use persistent navigation, multi-column layouts, and denser information structures when they improve task speed
- `Wide Desktop`: increase content width only for comparison-heavy or data-heavy views and never expand line length beyond readability

When a layout collapses, re-rank content by task priority instead of stacking the source order blindly.

#### Navigation

- mobile: prefer bottom navigation only for `3` to `5` primary destinations; otherwise use a top bar with drawer or overflow
- tablet: use a top bar or compact side rail for primary navigation and keep secondary links collapsed by default
- desktop: use persistent side navigation for deep information architecture and top navigation only for shallow products
- wide desktop: keep side navigation fixed and cap content width so extra space does not become extra chrome

#### Form Layout

- mobile: use one column, full-width inputs, labels above fields, and stacked sections
- tablet: use two columns only for short independent fields; keep long fields and destructive actions full width
- desktop: use one or two columns based on task speed and scanability
- wide desktop: keep a controlled form width; do not add columns only because space exists

#### Tables

- mobile: do not force full tables into narrow layouts; use stacked records or compact list rows when needed
- tablet: reduce visible columns and use row expansion for secondary detail
- desktop: keep tables as the default pattern for dense operational data
- wide desktop: maintain stable column priority instead of spreading columns to fill width

#### List-Detail Behavior

- mobile: use separate list and detail screens and preserve list scroll position on return
- tablet: use a list plus slide-over detail panel only when the list remains usable
- desktop: use persistent split view for record-centric workflows when it materially improves speed
- wide desktop: add a third zone only when it clearly improves the workflow

#### Modal Behavior

- mobile: prefer full-screen overlays or bottom sheets
- tablet: use drawers or medium dialogs for focused edits
- desktop: use centered modals for short self-contained tasks and drawers when page context matters
- wide desktop: cap modal width and keep actions within easy reach

#### Sticky Actions

- mobile: use a sticky bottom action bar for primary commit actions when the workflow is long
- tablet: use a sticky footer or stable header action cluster on long pages
- desktop: pin actions only for long forms or review flows
- wide desktop: do not detach actions from the content they affect unless the workflow spans multiple steps

#### Touch Targets

- mobile minimum tappable area: `44px` by `44px`
- tablet primary controls: `44px` by `44px` or larger
- desktop frequent pointer targets: at least `40px` by `40px`

Never rely on visual size alone. The interactive area must include padding.

#### Content Density

- mobile: prioritize one main task per screen and collapse nonessential chrome
- tablet: use balanced density with selective disclosure
- desktop: favor higher density for operational work while preserving whitespace around primary actions
- wide desktop: increase data density, not decorative spacing

## 6. Content Rules

### Headings

Headings must be concise, specific, and informative.

Rules:

- describe the actual content of the screen or section
- help the user orient quickly
- keep headings short and easy to scan

Avoid:

- decorative subtitles
- slogan-style intros
- vague section names
- cleverness for its own sake
- marketing language
- AI-sounding phrasing

### Labels

Labels must clearly identify the field, action, or control.

Rules:

- use plain nouns or short action-based phrases
- keep terminology stable across the interface
- make every label understandable without extra interpretation

Avoid:

- internal jargon without explanation
- abstract product language
- playful wording in product UI
- labels that restate the obvious without adding clarity

### Helper Text

Helper text should explain only what the user needs to complete the action correctly.

Use helper text for:

- format guidance
- constraints
- expected input
- brief clarification

Rules:

- keep it short
- keep it practical
- omit it when the field is already self-explanatory

Avoid:

- filler text
- motivational tone
- long explanations
- repeated restatements of the label
- AI-style overexplaining

### Error Copy

Error messages must be clear, specific, and actionable.

Rules:

- state what went wrong
- explain how to fix it when useful
- use plain language
- keep the message short enough to scan

Avoid:

- technical dumps
- blame-oriented phrasing
- generic messages such as `Something went wrong`
- overly polite or chatty AI wording

### CTA Naming

CTA labels must describe the exact action that will happen.

Prefer direct labels such as:

- `Save changes`
- `Create project`
- `Delete record`
- `Send invite`
- `Export CSV`

Rules:

- use verbs that match the outcome
- make destructive or irreversible actions explicit

Avoid:

- vague labels such as `Continue` or `Proceed` without context
- slogan-style CTA text
- clever or branded wording
- labels that hide the result of the action

### Empty-State Copy

Empty-state copy should be useful, brief, and calm.

A good empty state explains:

- what is missing
- why the screen is empty, when relevant
- what the user can do next

Rules:

- use one clear title
- use one short supporting sentence
- use one direct CTA when action is possible

Avoid:

- mascot-style language
- inspirational filler
- abstract metaphors
- AI-sounding reassurance

### Tone

All product copy should sound:

- concise
- professional
- neutral
- direct
- confident

The tone should feel human, but not casual or chatty.

Write as if the interface is helping a working user complete a task quickly and correctly.

Avoid:

- decorative subtitles
- vague product copy
- filler text
- slogan-style intros
- overfriendly phrasing
- unnecessary enthusiasm
- marketing tone
- AI-sounding UI writing

### Content Standards

Rules:

- use consistent terminology for the same concept everywhere
- keep wording stable, predictable, and easy to translate
- choose the simplest accurate wording when in doubt

Avoid:

- switching terms casually for the same object or action
- using copy to perform visual decoration

## 7. Context Adaptation

The same design language must adapt to context without changing its core identity.

Tokens, typography, spacing rhythm, border treatment, and interaction states should remain consistent across the system.

Only the hierarchy, density, and navigation pattern should shift based on the task.

### Adaptation Principles

- preserve the same visual foundation across product types
- change structure before changing style
- keep interaction states and semantic color roles consistent
- adapt density to the use case
- optimize for the primary user task, not for a generic screen pattern

### Dashboards

Rules:

- prioritize summary, status, and decision support
- keep metric blocks compact and scannable
- use charts only when they clarify a trend or comparison

Avoid:

- decorative analytics layouts
- KPI cards that do not support action

### CRUD Screens

Rules:

- prioritize scanning, filtering, and row-level action
- keep forms, tables, and bulk actions disciplined
- reduce visual decoration so data remains the focus

Avoid:

- over-styled list views
- scattered filters and actions

### Detail Pages

Rules:

- prioritize the main record or primary content area
- keep supporting metadata secondary and compact
- use tabs, anchor navigation, or side panels only when they improve orientation

Avoid:

- splitting attention across too many equal-weight sections

### Mobile Apps

Rules:

- preserve the same visual language in a tighter vertical rhythm
- reduce chrome and simplify navigation
- prefer stacked sections, sheets, and bottom-aligned actions when appropriate

Avoid:

- importing desktop density directly into mobile
- treating mobile as a separate visual product

### Internal Tools

Rules:

- optimize for speed, precision, and repeated use
- allow higher information density than consumer screens
- keep labels explicit and controls efficient

Avoid:

- excessive decoration
- density so high that readability breaks down

### Consumer Product Screens

Rules:

- optimize for clarity, confidence, and approachability
- use more breathing room than internal tools
- keep primary actions obvious and secondary actions quieter

Avoid:

- noisy UI
- over-packed screens
- artificial attempts to make the product feel trendy

### Consistency Rules

- do not create a separate visual system for each product type
- do not restyle components just to make a screen feel different
- do adapt spacing, hierarchy, and density to fit the task
- do make every screen feel part of the same product family

### Context Check

Before finalizing any screen, confirm:

- the screen matches the task type
- the hierarchy supports the main user goal
- the density matches the expected usage pattern
- the navigation pattern fits the device and context
- the screen still follows the shared design language

## 8. Anti-Patterns

This system must actively reject visual patterns that reduce clarity, add noise, or make the product feel decorative instead of functional.

### Visual Anti-Patterns

Do not use:

- gradient-heavy UI
- glow effects
- glassmorphism
- neon accents
- oversized shadows
- layered shadow stacks
- loud color combinations
- black-heavy dramatic sections
- trend-chasing AI visuals
- decorative illustrations that do not support the task

If a visual treatment exists only to look modern, it is not allowed.

### Layout Anti-Patterns

Do not use:

- oversized decorative cards
- hero-style product openings
- large introductory banners inside product screens
- empty padding used as a design choice
- excessive section gaps
- floating content blocks without structural purpose
- card-inside-card structures that add no value
- layouts that delay useful content

Useful content should appear early.

Decorative spacing is not a substitute for structure.

### Typography and Copy Anti-Patterns

Do not use:

- random subtitles
- decorative uppercase
- wide letter spacing for styling
- theatrical headings
- vague marketing copy
- placeholder labels disguised as product language

If a subtitle does not clarify the screen, remove it.

### Clarity Anti-Patterns

Do not make choices that reduce readability, scanability, or user confidence.

This includes:

- low-contrast text
- weak hierarchy
- ambiguous visual states
- decorative containers that compete with content
- controls that look more styled than usable
- interfaces that hide priority behind novelty

Clarity always takes precedence over style.

### Enforcement Rule

If a design choice improves novelty, mood, or visual trend alignment at the expense of clarity, it must be rejected.

If the interface becomes harder to read, harder to scan, or harder to use, the pattern is not acceptable.

## 9. Execution Rules

Before designing or editing any interface:

- read this guide first
- read the relevant existing UI files, components, and patterns in the project
- treat this document as the default decision framework for UI work

Rules:

- prefer reusing existing components, tokens, layouts, and interaction patterns
- extend or compose an existing component before creating a new pattern
- optimize for consistency across screens, states, and flows
- prioritize consistency over novelty, visual experimentation, or personal preference
- use the smallest change that satisfies the requirement while staying aligned with the current system

### Exceptions

Deviations from this guide are allowed only when the standard approach cannot satisfy a clear:

- functional requirement
- accessibility requirement
- performance requirement
- maintainability requirement

Every exception must be explicitly justified.

The justification should state:

- which rule is being relaxed
- why the standard approach is insufficient
- why the proposed alternative is the safest option

Exceptions should stay limited in scope and should not become a new default unless the change is intentional and documented.

### When Project Style Conflicts

If the current project style conflicts with this guide:

- preserve the established local style in the affected area first so the experience remains coherent
- raise the conflict explicitly if it creates a real usability, accessibility, or consistency problem
- propose a controlled migration path instead of mixing incompatible patterns in one flow

When in doubt, preserve the local project convention unless this guide defines a stricter requirement that must take precedence.

### Default Review Checklist

Before shipping a new screen or UI change, verify:

- the layout is clear and appropriately dense for the task
- typography is readable and restrained
- color is functional rather than decorative
- components reuse existing patterns where possible
- copy is concise and free of filler
- responsive behavior is intentional
- the final screen feels like part of the same product family

---

## 10. Minimal Text & Placeholder Ban

Every word on screen must earn its place. If removing a word does not break the task, remove it.

### Core Rules

- Write labels as nouns or verb phrases, never sentences.
- Helper text is optional. Omit it when the field is self-explanatory.
- Empty states need: an icon, a 3–5 word title, one short sentence, and one action button.
- Card headers are nouns, not descriptions.
- KPIs are a number plus a one-word label.
- Table headers are 1–2 words. No "Column" suffix.
- Modal titles describe the action or record, not the view name.

### Banned Copy Patterns

Never use:

- `workspace`, `design principle`, `internal intake experience`, `review command center`
- `explore your data`, `welcome to the dashboard`, `manage everything in one place`
- `get started with your journey`, `here you can see...`, `below is the list of...`
- `overview of your recent...`, `this section allows you to...`
- Decorative Vietnamese intros before every table or form

If a subtitle does not clarify the screen, remove it.

### Button Labels

Use verb + object:

- ✅ `Save changes`, `Create project`, `Export CSV`
- ❌ `Continue`, `Proceed`, `Explore`, `Open workspace`

### Form Labels

- ✅ `Project name`, `Start date`
- ❌ `Please enter your project name`, `Input the start date here`

---

## 11. Accessibility & WCAG

The interface must work for all users, including keyboard-only and screen-reader users.

### Contrast

- Normal text: minimum 4.5:1 against background.
- Large text (18px+ bold or 24px+ regular): minimum 3:1.
- UI components and graphical objects: minimum 3:1.

All tokens in this guide are calibrated to meet these ratios in light mode.

### Focus Visibility

- Every interactive element must have a visible focus indicator.
- Default Tailwind `focus:ring-2 focus:ring-sky-500 focus:ring-offset-2` is acceptable.
- Do not suppress focus outlines with `outline-none` unless a replacement is provided.

### Keyboard Navigation

- All controls reachable via Tab in a logical order.
- Enter/Space activates buttons, links, and switches.
- Escape closes modals, drawers, and dropdowns.
- Trap focus inside open modals.

### Screen Readers

- Use semantic HTML (`<button>`, `<a>`, `<label>`, `<table>`) before ARIA.
- Icon-only buttons require `aria-label`.
- Dynamic content (toasts, live lists) uses `aria-live="polite"`.
- Form errors link to fields with `aria-describedby`.

### Motion

- Respect `prefers-reduced-motion`.
- Disable non-essential animations for users who request reduced motion.
- Essential feedback (button press, state change) may remain but must be instant or very short.

### Color Independence

- Never rely on color alone to communicate status.
- Pair status colors with icons or text labels.
- Example: a red "Rejected" badge must include the word "Rejected" or a ban icon, not just red color.

---

## 12. Notifications, Toasts & Snackbars

Use transient notifications for outcomes that do not require a modal.

### Positioning

- Desktop: top-right corner, stacked vertically.
- Mobile: bottom-center, single or stacked with max 2 visible.

### Duration

- Success / Info: 4 seconds.
- Warning: 6 seconds.
- Error: 8 seconds or persistent until dismissed.
- Action-required: persistent with explicit dismiss button.

### Content Structure

Each toast contains:

1. Semantic icon (16px) matching intent.
2. One-line message (max 2 lines on mobile).
3. Optional text action (e.g., `Undo`, `View`).
4. Dismiss affordance.

No multi-paragraph toasts. No marketing copy inside toasts.

### Stacking & Limits

- Max 3 visible toasts at once.
- Older toasts fade out first.
- New toasts slide in (`translate-y` + opacity, 200ms).

### Colors

| Intent | Icon | Background | Border | Text |
|---|---|---|---|---|
| Success | CheckCircle | `bg-emerald-50` | `border-emerald-200` | `text-emerald-800` |
| Error | XCircle | `bg-rose-50` | `border-rose-200` | `text-rose-800` |
| Warning | AlertTriangle | `bg-amber-50` | `border-amber-200` | `text-amber-800` |
| Info | Info | `bg-sky-50` | `border-sky-200` | `text-sky-800` |

Avoid colored shadows or glow behind toasts.

---

## 13. Loading & Skeleton States

Never show a blank white space while data loads. The user must see that something is happening and where content will appear.

### Skeleton Patterns

Use `bg-slate-200 animate-pulse` with rounded shapes matching the final content:

- Text lines: `h-4 rounded` with widths `w-full`, `w-3/4`, `w-1/2`.
- Headers: `h-5 rounded w-1/3`.
- Avatar circles: `rounded-full bg-slate-200`.
- Buttons: `h-10 rounded-lg w-24 bg-slate-200`.
- Cards: replicate the real card's padding and shape with skeleton blocks inside.

### Table Skeleton

Show 5–8 skeleton rows. Match column count and approximate widths. Include a skeleton header row. Keep the same table borders so the structure does not shift when real data arrives.

### Card Skeleton

- Skeleton header bar (icon + title).
- 2–4 skeleton text lines inside.
- Preserve card padding, border, and radius.

### Spinner Usage

- Inline actions (button click): replace button text with a 16px spinner inside the same button height. Do not change button size.
- Small areas (filter result count): inline spinner next to text.
- Full page: use skeleton layout matching the final layout. Avoid a generic centered spinner unless the entire layout is unknown.

### Progressive Loading

- Load text and layout first.
- Defer heavy content: charts, large images, embedded previews.
- Show placeholder structure immediately, then hydrate content.

### Error State After Loading

If loading fails, replace skeleton with an inline error inside the same container. Do not leave a spinner spinning forever.

---

## 14. Data Visualization & Charts

Use charts only when they answer a real operational question. Decorative charts are not allowed.

### When to Use

- Line chart: trends over time.
- Bar chart: comparison across categories.
- Pie / donut chart: simple part-of-whole with 5 slices or fewer.
- Table: always preferred for precise values and dense data.

### Color Palette for Charts

Extend the semantic palette. Do not introduce new colors.

| Role | Color |
|---|---|
| Primary series | `sky-600` |
| Secondary series | `slate-400` |
| Success / Positive | `emerald-500` |
| Warning | `amber-500` |
| Danger / Negative | `rose-500` |
| Background grid | `slate-100` |
| Axis text | `slate-500` |

Avoid gradient fills. Use flat colors with slight opacity (e.g., `fill-sky-600/20`) for area under lines.

### Labels & Legends

- Keep legends inside or directly adjacent to the chart, not floating in a separate panel.
- Axis labels: `text-xs text-slate-500`.
- Data labels inside bars only when readable; otherwise use tooltips.

### Tooltips

- One line of data.
- Dark background: `bg-slate-900 text-white text-xs rounded-md px-2 py-1`.
- No shadow spectacle.
- Show value + unit + date/context.

### Empty Chart State

Follow empty-state rules: icon + short title + sentence + action (if applicable). Do not show an empty grid with axes.

---

## 15. Iconography Deep-Dive

A single, consistent icon system keeps the UI quiet and scannable.

### Icon Set

- **Lucide React** is the only approved icon library.
- Do not mix with Material Icons, Font Awesome, Heroicons, or custom filled sets.

### Stroke & Style

- Stroke width: default Lucide stroke (1.5px–2px equivalent).
- All icons must be outline style. Do not use filled icons unless the filled variant exists in Lucide and is used consistently.

### Sizes

| Token | Size | Usage |
|---|---|---|
| Inline | 14px–16px | Buttons, table actions, form hints |
| Default | 16px | Menu items, badges, inline metadata |
| Header | 20px | Page headers, section titles, prominent actions |
| Empty state | 24px–32px | Empty states, confirmation dialogs |
| Decorative | 40px+ | Rare; use only when an icon is the sole content of a large area |

### Color

- Inherit text color by default.
- Status icons use semantic colors (emerald, amber, rose, sky).
- Do not apply arbitrary colors to icons.

### Alignment

- Center icons vertically with adjacent text.
- Icon + label buttons: icon left, text right, gap `8px`.
- Icon-only buttons: square touch target, minimum `40px`.

### Forbidden Patterns

- Emojis as icons (`📁`, `⚠️`).
- Custom SVG illustrations inside UI chrome.
- 3D or skeuomorphic icons.
- Animated or rotating icons except loading spinners.

---

## 16. File Attachment & Upload Patterns

Uploading and managing files is common in enterprise workflows. Keep it practical.

### Upload Zone

- Dashed border: `border-2 border-dashed border-slate-300 rounded-lg`.
- Background: `bg-slate-50` on hover/active.
- Content: upload icon (24px) + one line of text (`Kéo thả hoặc chọn file`) + max-size hint (`Tối đa 10MB — PDF, DOCX`).
- Click anywhere in the zone to open file picker.

### File List

- Display as rows, not cards.
- Row content: file-type icon (16px) + filename + file size + delete action.
- Row style: `border-b border-slate-100 py-2`.
- Truncate long filenames with ellipsis. Tooltip shows full name.

### Upload Progress

- Inline thin bar inside the file row: `h-1 bg-sky-600 rounded-full`.
- Do not use a modal dialog for upload progress.

### Error Handling

- Inline row message: `text-xs text-rose-600`.
- Example: `File vượt quá 10MB`, `Chỉ chấp nhận PDF`.

### Preview

- Image thumbnails: 40×40px rounded (`rounded-md`).
- Non-images: file-type icon + name only. No fake preview.

### Limits & Validation

- Show accepted formats and max size **before** the user selects files.
- Validate immediately on selection, not on form submit.

---

## 17. Navigation Deep-Dive

Navigation must orient users without competing with content.

### Sidebar

- Max 1 visible level of navigation at a time.
- Collapsible submenus with a chevron indicator.
- No mega-menus. No horizontal scroll.
- Active item: `bg-sky-50 text-sky-700 border-r-2 border-sky-600`.
- Do not combine bold + underline + background for active state. Pick one clear treatment.

### Breadcrumbs

- Use only when page depth > 2.
- Format: `Home > Quản lý dự án > Chi tiết`.
- Style: `text-sm text-slate-500`.
- Last segment is plain text, not a link.
- Home icon may replace the word "Home".

### Overflow

- Long sidebar labels: truncate with ellipsis + tooltip.
- Many tabs: horizontal scroll with fade indicator, or dropdown overflow.
- Never wrap tab text to two lines.

### Mobile Navigation

- Drawer slides in from left.
- Overlay: `bg-slate-900/50`.
- Close on backdrop tap or swipe.
- Keep the same menu structure as desktop; do not invent a separate mobile hierarchy.

### Local Navigation (Sub-tabs / Sub-nav)

- Use compact tabs or a vertical mini-nav inside a card.
- Tab height: `36px–40px` desktop.
- Active tab: bottom border or soft background. No loud color block.

---

## 18. Onboarding, Tooltips & Coach Marks

Enterprise users do not need guided tours. Provide contextual help only when necessary.

### Tooltips

- One sentence max.
- Dark style: `bg-slate-900 text-white text-xs rounded-md px-2 py-1`.
- Arrow optional.
- Trigger: hover on desktop, long-press on mobile (or info icon tap).
- Do not put interactive content inside tooltips.

### Coach Marks / Spotlights

- Use only for genuinely new or complex features.
- Single spotlight at a time.
- Must be dismissible (X button or "Đã hiểu").
- No sequential multi-step wizard overlays.
- Darken the rest of the page with `bg-slate-900/40`.

### New-Feature Badge

- `rounded-sm bg-sky-100 text-sky-700 text-xs px-1.5`.
- Remove after first use or within 7 days.

### Empty State as Onboarding

- The primary empty-state action button is the onboarding CTA.
- Do not add a separate "How it works" panel if the empty state already explains the next step.

### No Forced Tours

- Do not block the UI with a mandatory "Welcome" modal.
- Do not dim the entire screen on first login.
- Contextual hints are preferred over sequential instructions.

---

## Tailwind CSS v4 — Implementation Notes

This project uses Tailwind CSS v4. There is **no `tailwind.config.ts`**. All design tokens must be declared as CSS custom properties in `app/globals.css` using `@theme inline`.

### Tech Stack:
- `app/globals.css` — Design token declarations (`@theme inline`)
- `@import "tailwindcss"` — Tailwind v4 import
- No `tailwind.config.ts` exists

### Design Token → Tailwind Class Mapping:

| Design Token | Tailwind Class |
|---|---|
| `color.primary` | `sky-600` |
| `color.primaryHover` | `sky-700` |
| `color.primarySoft` | `sky-50` |
| `color.success` | `emerald-600` or `emerald-700` |
| `color.successSoft` | `emerald-50` |
| `color.warning` | `amber-500` or `amber-600` |
| `color.warningSoft` | `amber-50` |
| `color.danger` | `rose-600` |
| `color.dangerSoft` | `rose-50` |
| `color.bg` | `slate-50` |
| `color.surface` | `white` |
| `color.textPrimary` | `slate-900` |
| `color.textSecondary` | `slate-600` |
| `color.textMuted` | `slate-500` |
| `color.borderDefault` | `slate-200` |
| `color.borderStrong` | `slate-300` |
| `shadow.1` | `shadow-sm` |
| `shadow.2` | `shadow-md` |
| `shadow.3` | `shadow-xl` |

### PROHIBITED Colors:
- `bg-gradient-to-*` (gradient backgrounds)
- `bg-[linear-gradient(...)]`
- `purple-*`, `violet-*`, `indigo-*` (AI-style palette)
- `text-black` on white backgrounds → use `text-slate-900`
- `text-white` on non-dark colored backgrounds

### Border Radius Scale → Tailwind:

| px | Tailwind | Use For |
|---|---|---|
| 6 | `rounded-sm` | Badges, chips |
| 10 | `rounded` or `rounded-md` | Buttons, inputs |
| 12 | `rounded-lg` | Cards, menus |
| 16 | `rounded-xl` | Panels, modals |
| 20 | `rounded-2xl` | Major layout blocks |
| 9999 | `rounded-full` | Avatar, pill (sparingly) |

**PROHIBITED:** `rounded-[28px]`, `rounded-[32px]`, `rounded-[24px]`

### Control Heights:
- Input/Select: `h-11` (44px)
- Button default: `h-10` or `h-11` (40-44px)
- Button small: `h-8` (32px)

### Shadows:
- Cards: `shadow-sm` or `border + shadow-sm`
- Modals: `shadow-xl` or `shadow-md`
- **PROHIBITED:** `shadow-[0_20px_60px...]`, heavy arbitrary shadows

### Overlay/Backdrop:
- `bg-slate-900/40` or `bg-slate-900/50`
- NOT: `bg-slate-950/55`

---

## Current Codebase Audit

Full audit of 20+ user-facing pages in `app/dashboard/user/`.

### CRITICAL — Severe violations, fix first

- **`app/dashboard/user/page.tsx`** — KPI cards use gradient (`from-green-500 to-green-600`, `from-purple-500 to-purple-600`, etc.)
- **`app/dashboard/user/spaces/page.tsx`** — Pervasive green palette outside spec
- **`app/dashboard/user/project-init/page.tsx`** — `rounded-[28px]`, `shadow-[0_20px_60px...]`, `bg-[linear-gradient(...)]`

### MAJOR — Multiple violations

- **`app/dashboard/user/director-projects/page.tsx`** — Arbitrary blue/emerald/amber/rose/purple in status badges
- **`app/dashboard/user/projects/[id]/page.tsx`** — `rounded-[32px]`, `text-[36px]`, `shadow-2xl`
- **`app/dashboard/user/projects/page.tsx`** — h2 `text-3xl` (spec: 24px), indigo/violet/teal palette
- **`app/dashboard/user/project-init/[id]/supplement/page.tsx`** — Purple/orange palette

### MINOR — Small violations

- **`app/dashboard/user/ai/page.tsx`** — H1 `text-xl` (spec: 30px), `text-black`
- **`app/dashboard/user/chat/page.tsx`** — H1 `text-xl`
- **`app/dashboard/user/company-projects/page.tsx`** — `text-black` pervasive
- **`app/dashboard/user/company-structure/page.tsx`** — `text-green-600` outside spec
- **`app/dashboard/user/customers/page.tsx`** — `rounded-full`, blue-50 outside spec
- **`app/dashboard/user/documents/page.tsx`** — `text-black` pervasive
- **`app/dashboard/user/payments/page.tsx`** — `text-black`, h-12 inputs
- **`app/dashboard/user/reports/page.tsx`** — `text-black`
- **`app/dashboard/user/settings/page.tsx`** — `h-12` inputs, `rounded-[24px]`

### Cleanest Pages
- **`app/dashboard/user/meeting-rooms/page.tsx`** — ~85% compliant
- **`app/dashboard/user/consortium/page.tsx`** — nearly clean

See `DESIGN_IMPLEMENTATION_GUIDE.md` for detailed fix patterns.
