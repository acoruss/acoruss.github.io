# Website

## Rules

1. Always use [Agency Landing](https://blink.daisyui.com/landing/agencylanding/) layout, iconography and typography.
2. Always ensure that the website is mobile responsive.
3. Use warm-toned colors throughout - avoid pure white (#FFFFFF) or pure black (#000000).

### Website

#### Color Palette

| Role              | Color   | Description                                   |
| ----------------- | ------- | --------------------------------------------- |
| Primary           | #7A1C1C | Warm maroon - CTAs, headings, highlights      |
| Primary Content   | #FFFFFF | White text on primary backgrounds             |
| Secondary         | #3D1C1C | Deep warm brown - dark cards, subtle fills    |
| Secondary Content | #F5F0EB | Off-white text on secondary backgrounds       |
| Accent            | #C8956A | Warm amber/gold - featured elements, emphasis |
| Accent Content    | #1A1612 | Dark text on accent backgrounds               |
| Neutral           | #1A1612 | Warm near-black - dark sections, footer       |
| Neutral Content   | #F5F0EB | Warm off-white - text on dark backgrounds     |
| Base 100          | #FDFCFA | Warm white - main page background             |
| Base 200          | #F5F0EB | Warm light cream - cards, inputs              |
| Base 300          | #E8E2DA | Warm light gray - borders, dividers           |
| Base Content      | #2C2520 | Warm dark brown - primary body text           |
| Info              | #4A90D9 | Soft blue - info states                       |
| Success           | #5B8C5A | Muted green - success states                  |
| Warning           | #D4A843 | Warm gold - warning states                    |
| Error             | #C94444 | Warm red - error states                       |

#### Design Patterns

- **Hero Section**: Uses `.hero-gradient` (dark warm gradient: #1A1612 → #2C2520 → #3D1C1C) with light text
- **Glass Navbar**: Floating glass-effect navbar with rounded corners, border opacity, and backdrop blur
- **Section Badges**: Small pill badges (e.g., "WHY US", "OUR SERVICES") with accent dot indicator
- **Cards**: rounded-2xl with border-base-300/60 borders, hover shadow transitions
- **Bento Grid**: Services section uses asymmetric grid layout with featured accent card
- **Process Steps**: Numbered step cards with icon indicators
- **CTA Section**: Dark background with accent-colored headline and contact form
- **Footer**: Dark warm background matching hero, uppercase section headers with muted opacity

#### Typography

- Font family: Inter (Google Fonts) — variable optical sizing, weights 300–800
- Headings: font-bold, text-4xl/5xl on desktop, text-3xl/4xl on mobile
- Section badges: text-xs uppercase tracking-wider
- Body text: text-base-content/70 for secondary text, full opacity for primary

#### Animations

- Scroll-triggered fade-in via `data-animate` attribute and IntersectionObserver
- Smooth transitions on links and buttons (150ms ease)
- Dot pattern overlay on hero section via `.dot-pattern` utility

### Dashboard

Use Website rules and color palette. Dashboard design is inspired by [DaisyUI Nexus](https://nexus.daisyui.com/) dashboards.

#### Layout

- **Sidebar**: Collapsible sidebar (260px → 72px) with `dash-sidebar` / `dash-sidebar-collapsed` classes. Uses localStorage to persist collapsed state. On mobile, slides in as an overlay with backdrop.
- **Top Bar**: Sticky top bar with breadcrumbs (left) and action buttons (right). Includes user avatar dropdown with logout.
- **Content Area**: Padded main area (`p-5 lg:p-6`) that adapts to sidebar width via margin-left transition.

#### Component Classes

| Class | Purpose |
|-------|---------|
| `.dash-card` | Card container: `bg-base-100/60 backdrop-blur rounded-2xl border border-base-300/15 p-5` |
| `.dash-stat-card` | Stat metric card: same as dash-card but `p-4` |
| `.dash-card-header` | Flex header inside cards with justify-between |
| `.dash-sidebar` | Fixed sidebar: 260px, bg-neutral, z-40 |
| `.dash-sidebar-collapsed` | Collapsed sidebar: 72px width |
| `.dash-nav-item` | Nav link: flex, rounded-xl, hover state |
| `.sidebar-label` | Text label that hides when sidebar collapses |
| `.sidebar-full` | Content that hides completely when collapsed |

#### Dashboard Design Patterns

- **Stat Cards**: Grid of metric cards with icon in colored rounded-lg container (e.g. `bg-primary/10`), label, and bold value
- **Tables**: Desktop table with `table-sm`, mobile card fallback using `hidden sm:block` / `sm:hidden`
- **Search Bars**: Input with magnifying glass SVG icon positioned absolutely inside
- **Status Badges**: DaisyUI `badge-success/warning/error` with inline SVG icons
- **Timeline**: Vertical timeline with colored dots (`bg-success/20`) and connecting line (`w-px bg-base-300/30`)
- **Product Grid**: `sm:grid-cols-2 lg:grid-cols-3` card grid with hover border accent
- **Detail Pages**: `lg:grid-cols-3` layout with 2-col main + 1-col sidebar
- **Empty States**: Centered icon + message + action button
- **Avatar Initials**: Rounded-full with `bg-primary/20 text-primary` and first letter of name
