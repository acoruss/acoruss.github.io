---
target: all public pages
total_score: 24
p0_count: 0
p1_count: 2
timestamp: 2026-05-25T21-31-53Z
slug: src-templates-all-public-pages
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | No loading states on tab switches; newsletter email input has no feedback |
| 2 | Match System / Real World | 3 | Good use of familiar language; "SOW" jargon in process step 4 |
| 3 | User Control and Freedom | 3 | No back-to-top; tab switches lose scroll position |
| 4 | Consistency and Standards | 2 | Every page uses identical hero pattern (badge + heading + paragraph); repetitive |
| 5 | Error Prevention | 2 | Newsletter email input isn't a real form; contact form lacks inline validation |
| 6 | Recognition Rather Than Recall | 3 | Navigation is clear; tab panels require recall of which tab was active |
| 7 | Flexibility and Efficiency | 2 | No keyboard shortcuts; no quick-jump anchors on long pages |
| 8 | Aesthetic and Minimalist Design | 2 | Card grid repetition across pages; information density could be higher |
| 9 | Error Recovery | 2 | Contact form has no visible error states in template; no inline error messaging |
| 10 | Help and Documentation | 2 | No FAQ; pricing page doesn't explain what "Discovery Call" includes |
| **Total** | | **24/40** | **Needs Work** |

## Anti-Patterns Verdict

**LLM assessment**: The site is competent but has visible AI-generation tells:

1. **Identical card grids** (banned pattern): The "Why Choose Us" section on index, "Our Values" on about, and the projects grid all use the same icon + heading + text card repeated 3-6 times in an identical grid. This is the #1 AI slop tell.
2. **Repetitive hero pattern**: Every single page opens with the exact same structure: section badge (dot + uppercase text) → h1 with one accent-colored word → subtitle paragraph. Seven pages, seven identical compositions. A visitor browsing multiple pages will notice the formula.
3. **Glass navbar is purposeful** (not decorative glassmorphism): passes the "rare and purposeful" test.
4. **No gradient text**: clean.
5. **No side-stripe borders**: clean.
6. **Category-reflex check**: "tech agency → dark theme + warm gold" is a recognizable first-order reflex. The palette works but doesn't surprise.

**Deterministic scan**: Unavailable (bundled detector not found in this environment). Manual review only.

## Overall Impression

The site is cohesive, warm, and technically well-built. The dark-warm palette and glass-effect navbar create genuine atmosphere. But the structural repetition across pages drains personality: every page feels stamped from the same template, and card grids dominate where more varied layouts would show craft. For an agency whose principle is "practice what you preach," the uniform layout undermines the claim of bespoke work.

The single biggest opportunity: **break the layout monotony.** Vary section compositions across pages so each page feels designed, not generated.

## What's Working

1. **The hero section on index**: Floating testimonial cards flanking the headline create asymmetry and social proof simultaneously. The godrays effect adds atmospheric depth without being gimmicky. This is the strongest moment on the site.

2. **The bento grid in services on index**: Mixing a tall 2-row card with shorter ones breaks the identical-grid pattern. The accent-colored "Strategy" card at the bottom adds variety. This approach should be expanded to other pages.

3. **Contact form**: Well-structured with clear labels, progressive disclosure (optional fields second), honeypot spam protection, and proper field grouping. The sidebar with contact details provides good information architecture.

## Priority Issues

### [P1] Identical Card Grids Across All Pages
**What**: "Why Choose Us" (3 cards), "Our Values" (6 cards), Projects (3+ cards per tab), Products (3 cards), Pricing (6 step circles) all use the same icon-title-text card in a uniform grid.
**Why it matters**: This is the #1 AI-generation tell. An agency claiming craft cannot display the same card template 25+ times across its site. Visitors scanning multiple pages will subconsciously register "template."
**Fix**: Replace at least 3 of these grids with different compositions: a comparison table, a timeline, numbered steps with connecting lines, an accordion, a featured spotlight with supporting details, or asymmetric 2-column layouts.
**Suggested command**: `impeccable layout`

### [P1] Every Page Hero Is Identical
**What**: All 7 pages open with: accent badge (dot + text) → extrabold h1 with one accent word → subtitle paragraph → centered alignment. The formula is visible.
**Why it matters**: Structural repetition across pages signals "generated from template." Real brand sites vary their openers: some lead with imagery, some with a provocative question, some with asymmetric layouts.
**Fix**: Keep the pattern for 2-3 inner pages, but vary at least the About and Projects heroes. About could lead with the story (no badge); Projects could open with a featured project hero image. Index already has variety with the testimonials.
**Suggested command**: `impeccable bolder`

### [P2] About Page Stat Numbers Are Underwhelming
**What**: "2025 Officially Launched", "5+ Team Members", "10+ Projects", "10+ Customers" prominently displayed.
**Why it matters**: Small numbers displayed large draw attention to the company's youth. "10+ Customers" in a big accent-colored stat card could create doubt rather than confidence. These numbers will improve with time, but right now they're working against the "confident expert" brand.
**Fix**: Either remove the stat grid until numbers are more impressive, or reframe: "20+ Years Combined Experience" (already mentioned in copy), "100% Project Delivery Rate", qualitative achievements instead of quantity metrics.
**Suggested command**: `impeccable clarify`

### [P2] Newsletter Section Is Deceptive
**What**: The email input appears to be a subscription form but the button is actually a link to Substack. The input does nothing.
**Why it matters**: This is an error-prevention failure (Heuristic 5). A user types their email, clicks "Subscribe," and leaves the site. Their typed email is lost. It violates "practice what you preach" by appearing functional but being decorative.
**Fix**: Either make it a real form that subscribes to Substack via API, or replace the input with a single clear CTA button: "Subscribe on Substack →". Don't fake form UX.
**Suggested command**: `impeccable harden`

### [P2] Pricing Process Steps Violate the Ember Hierarchy Rule
**What**: The 6-step circle indicators alternate amber-gold (#C8956A) and maroon (#7A1C1C) with varying opacities (accent, accent/80, accent/60, primary, primary/80, accent). Gold and maroon touch directly in adjacent elements.
**Why it matters**: The DESIGN.md's Ember Hierarchy Rule states: "If gold is touching maroon directly, one of them is wrong." The alternating treatment creates visual noise rather than a clear progression.
**Fix**: Use a single color family for the progression (e.g., maroon at increasing opacity: /40 → /60 → /80 → /100), or all amber-gold. Not alternating.
**Suggested command**: `impeccable colorize`

## Persona Red Flags

**Sarah (Business Owner, first-time visitor)**: Arrives from Google, lands on index. Hero is strong, immediately understands what Acoruss does. Scrolls to "Why Choose Us": sees generic-looking cards and thinks "every agency says this." Clicks "Projects": sees a grid of cards with no screenshots or visuals. No imagery of actual work. Must click external links to see proof. High risk of abandoning without contacting.

**David (CTO evaluating agencies)**: Goes to Pricing. Sees "$50 Discovery Call fee" immediately. No context on what the call covers, what deliverables come from it, or why it's worth paying for. Clicks Services: 7 tabs is high cognitive load. Tab content is long-form text with no visual hierarchy within each tab. Will skim and miss key differentiators. Wants to see a case study, not a feature list.

**Amina (Startup founder, mobile)**: On index, floating testimonial cards are hidden (desktop only). Social proof disappears on mobile. Tab interfaces on Services/Projects require precise tapping. Long scrolling service panels on mobile with no way to jump between tabs without scrolling back up.

## Minor Observations

- The homepage has `font-extrabold` (800) while DESIGN.md specifies Display as 700. Minor inconsistency.
- Products page repeats xPerience Nairobi content that's also on the Projects page. Redundancy reduces each page's distinctiveness.
- Footer "Stay in the loop" section appears on every page including Contact (where someone already reaching out doesn't need newsletter prompting).
- Missing `aria-label` on several icon-only SVGs within cards.
- Tab panel transitions are instant (no animation). Given the system uses fade-in-up elsewhere, the jarring show/hide stands out.
- Some copy uses em-dashes implicitly via " - " (hyphen surrounded by spaces), which reads as an informal em-dash substitute.

## Questions to Consider

- What if each page had a genuinely different layout shape, proving Acoruss builds bespoke, not from templates?
- What if the Projects page showed screenshots or mockups instead of card descriptions?
- What if the About page led with the team's faces and personalities rather than a logo placeholder?
- What would pricing look like if it didn't try to list every service, but instead focused on the buyer's journey?
