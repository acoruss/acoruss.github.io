---
name: Acoruss
description: Technology consulting agency empowering businesses through software, AI, and strategy.
colors:
  warm-maroon: "#7A1C1C"
  deep-ember: "#3D1C1C"
  amber-gold: "#C8956A"
  charred-earth: "#0F0D0B"
  warm-smoke: "#1A1612"
  ash-brown: "#2C2520"
  warm-cream: "#F5F0EB"
  parchment: "#E8E2DA"
  soft-blue: "#5B9BD5"
  muted-sage: "#5B9B6B"
  warm-gold: "#D4A843"
  ember-red: "#C94444"
typography:
  display:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 5vw, 3.75rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 3vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "0.05em"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  full: "9999px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  section: "80px"
components:
  button-primary:
    backgroundColor: "{colors.warm-maroon}"
    textColor: "#FFFFFF"
    rounded: "{rounded.full}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "#8B2222"
    textColor: "#FFFFFF"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.warm-cream}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  button-ghost-hover:
    backgroundColor: "rgba(255, 255, 255, 0.1)"
    textColor: "{colors.warm-cream}"
  card-surface:
    backgroundColor: "rgba(15, 13, 11, 0.6)"
    textColor: "{colors.warm-cream}"
    rounded: "{rounded.lg}"
    padding: "20px"
  card-surface-hover:
    backgroundColor: "rgba(15, 13, 11, 0.7)"
  nav-pill:
    backgroundColor: "rgba(26, 22, 18, 0.75)"
    textColor: "{colors.warm-cream}"
    rounded: "{rounded.full}"
    padding: "12px 20px"
  input-field:
    backgroundColor: "{colors.warm-smoke}"
    textColor: "{colors.warm-cream}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
---

# Design System: Acoruss

## 1. Overview

**Creative North Star: "The Fireside Counsel"**

A trusted advisor's space: warm, composed, assured. The interface evokes the feeling of sitting in a well-appointed study with someone who has solved this problem before. Every surface carries the warmth of dark timber and ember-glow accents. The system never shouts, never dazzles with cheap tricks; it earns trust through craft, consistency, and restraint in the right places.

This system rejects displaced or scattered designs, generic template aesthetics, flashy gimmickry, and cold corporate impersonality. It is an agency's own proof of work: if the site itself doesn't feel expertly made, nothing it claims matters.

The color strategy is **Committed**: warm maroon carries identity across dark surfaces, with amber-gold as a secondary voice for emphasis. The palette works in tight harmony; no color arrives without purpose.

**Key Characteristics:**
- Dark warm ground with layered glass surfaces
- Single-font system (Inter) using weight and scale for hierarchy
- Pill-shaped primary CTAs that feel solid and inviting
- Godrays and subtle radial gradients for atmospheric depth
- Scroll-triggered fade animations at restrained energy
- Glass-effect navbar floating above content

## 2. Colors

A palette of embers and ash: warm darks dominate, punctuated by maroon identity and amber-gold sparks.

### Primary
- **Warm Maroon** (#7A1C1C): The brand voice. CTAs, headings, active states, and any element that says "this is Acoruss." Used sparingly on dark surfaces for maximum contrast and authority.

### Secondary
- **Deep Ember** (#3D1C1C): Darker sibling of the primary. Card fills in variety contexts, section differentiation, and subtle tonal shifts. Never competes with primary; it recedes.

### Tertiary
- **Amber Gold** (#C8956A): The warm accent. Featured elements, star ratings, emphasis text, hover highlights. Brings warmth and approachability to the maroon's authority.

### Neutral
- **Charred Earth** (#0F0D0B): The deepest dark. Page background, footer ground. Almost black, but warm.
- **Warm Smoke** (#1A1612): Primary surface for cards and elevated containers. The "resting" background for interactive elements.
- **Ash Brown** (#2C2520): Borders, dividers, subtle separators. The lightest of the darks.
- **Warm Cream** (#F5F0EB): Primary text on dark. Off-white with warmth; never clinical.
- **Parchment** (#E8E2DA): Secondary text, body copy at reduced emphasis. Slightly muted.

### Named Rules
**The Ember Hierarchy Rule.** Maroon is identity. Gold is emphasis. The darks are structure. If gold is touching maroon directly, one of them is wrong. They address different emotional registers and should not compete in the same element.

## 3. Typography

**Display Font:** Inter (with ui-sans-serif, system-ui fallback)
**Body Font:** Inter (same stack)

**Character:** A single-font system that derives all personality from weight contrast and optical sizing. Inter's variable axis (opsz 14-32) keeps small text crisp and large text elegant. The system avoids typographic spectacle; authority comes from scale and weight, not decorative faces.

### Hierarchy
- **Display** (700, clamp(2.25rem, 5vw, 3.75rem), line-height 1.1, tracking -0.02em): Hero headlines only. Bold, tight, commanding.
- **Headline** (700, clamp(1.5rem, 3vw, 2.25rem), line-height 1.2, tracking -0.01em): Section headings. Same weight as display, stepped down.
- **Title** (600, 1.25rem, line-height 1.4): Card headings, sub-section titles. Semibold, not bold.
- **Body** (400, 1rem, line-height 1.6, max 65-75ch): Running text. Regular weight, generous leading for readability on dark backgrounds.
- **Label** (500, 0.75rem, tracking 0.05em, uppercase): Section badges, pill labels, metadata. Small, tracked out, uppercase.

### Named Rules
**The Weight Gap Rule.** Adjacent hierarchy levels must differ by at least one full weight step (e.g., 700 to 500, never 600 to 500). If two text elements feel the same weight at a glance, one of them is at the wrong level.

## 4. Elevation

This system uses **layered glass over warm darkness**. Depth is conveyed through translucent surfaces with backdrop-blur, not traditional drop shadows. The dark gradient ground (hero-gradient) establishes the base plane; glass-effect elements float above it with subtle borders at low opacity.

Shadows appear only on hover as a state response, never at rest. The resting state is flat-with-blur; the active state lifts with shadow.

### Shadow Vocabulary
- **Card hover lift** (`0 12px 40px rgba(0, 0, 0, 0.3)`): Applied via `.card-hover:hover`. Elements rise 4px on Y-axis simultaneously.
- **Navbar ambient** (`shadow-sm` via DaisyUI): Minimal shadow on the floating pill navbar. Barely perceptible; border does the heavy lifting.

### Named Rules
**The Flat-at-Rest Rule.** Surfaces are flat at rest. No resting shadows. Shadows appear only as a response to interaction (hover, press, drag). If a card has a shadow without being hovered, the shadow is wrong.

## 5. Components

### Buttons
Solid and grounded. Buttons feel like they have weight.

- **Shape:** Full pill radius (9999px) for primary CTAs; medium radius (12px) for ghost/nav buttons
- **Primary:** Warm maroon fill (#7A1C1C), white text, padding 10px 20px, font-semibold. Often includes a trailing arrow icon.
- **Hover / Focus:** Background lightens slightly (#8B2222), focus ring 2px solid amber-gold with 2px offset. No scale or bounce.
- **Ghost:** Transparent background, warm-cream text, 12px radius. Hover reveals white at 10% opacity.

### Cards / Containers
Glass surfaces that float on the dark ground.

- **Corner Style:** Generous curves (16px radius)
- **Background:** Base-100 at 60% opacity with 4px backdrop-blur (dashboard), or glass-effect (rgba(26,22,18,0.75) + 16px blur + saturate 180%) for marketing surfaces.
- **Border:** 1px, base-300 at 50% opacity (dashboard) or base-content at 5% opacity (marketing). Subtle; structure without division.
- **Internal Padding:** 20px standard, 16px for stat cards.
- **Hover:** translateY(-4px) + shadow (0 12px 40px rgba(0,0,0,0.3)). The card lifts toward you.

### Inputs / Fields
Warm, recessive, ready.

- **Style:** Warm-smoke background (#1A1612), warm-cream text, 12px radius, subtle border.
- **Focus:** 2px solid amber-gold outline with 2px offset. Unmistakable but not aggressive.
- **Error:** Ember-red (#C94444) border, red text below.

### Navigation
A floating glass pill that feels permanent and trustworthy.

- **Style:** Glass-effect background, full-width max 6xl, pill shape (rounded-full), fixed at top with 12-16px inset from edges.
- **Links:** Ghost buttons at 14px, medium weight. No active-state underline; relying on context.
- **Mobile:** Drawer overlay from left, same glass background.
- **CTA:** Primary button (pill, maroon fill) at navbar-end. "Get Started" with arrow icon.

### Section Badges (signature component)
Small uppercase pills that introduce sections. Amber-gold dot indicator on the left, tracked-out text, base-content at muted opacity. They announce topic without demanding attention.

## 6. Do's and Don'ts

### Do:
- **Do** use the warm maroon (#7A1C1C) exclusively for CTAs and primary interactive elements. Its rarity is its power.
- **Do** tint every "black" toward the warm hue. #0F0D0B, not #000000. The system has no true black or true white.
- **Do** use the glass-effect (backdrop-blur 16px + saturate 180%) for floating navigation and elevated marketing surfaces.
- **Do** maintain the weight gap between adjacent text levels (700 → 500 → 400, never adjacent values).
- **Do** use scroll-triggered fade-in-up animations (0.6s ease-out) for content entering the viewport.
- **Do** keep section spacing generous (80px between major sections) to let dark backgrounds breathe.

### Don't:
- **Don't** use displaced or scattered elements that feel like unrelated parts stitched together. Every section must feel like it belongs to the same warm room.
- **Don't** use generic template patterns, stock imagery, or hollow marketing copy. This site is proof of craft.
- **Don't** use flashy gimmickry, excessive particle effects, or spectacle over substance.
- **Don't** use cold, impersonal corporate styling. No clinical whites, no steel grays, no detachment.
- **Don't** use border-left or border-right greater than 1px as colored accent stripes.
- **Don't** use gradient text (background-clip: text).
- **Don't** use bounce or elastic easing. Ease-out with exponential curves only.
- **Don't** use resting shadows. Shadows respond to interaction, never decorate at rest.
- **Don't** use true #000000 or #FFFFFF anywhere. Every neutral is tinted warm.
