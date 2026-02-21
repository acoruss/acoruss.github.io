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

- Font family: Urbanist (Google Fonts)
- Headings: font-bold, text-4xl/5xl on desktop, text-3xl/4xl on mobile
- Section badges: text-xs uppercase tracking-wider
- Body text: text-base-content/70 for secondary text, full opacity for primary

#### Animations

- Scroll-triggered fade-in via `data-animate` attribute and IntersectionObserver
- Smooth transitions on links and buttons (150ms ease)
- Dot pattern overlay on hero section via `.dot-pattern` utility

### Dashboard

Use Website rules and color palette.
