# Acoruss Website

> Empowering Businesses Through Technology

The official website for Acoruss - a technology consulting company that helps businesses harness software, AI, and strategic technology without the heavy costs of building from scratch.

## 🚀 Performance Optimizations

This website has been optimized for performance using:

- **Vite** for fast development and optimized production builds
- **Tailwind CSS** with local compilation (no CDN)
- **Tree-shaking** to remove unused CSS
- **Modern JavaScript** with ES modules
- **Playwright MCP** for interactive browser testing

## 🛠️ Development

### Prerequisites

- Node.js 18+
- npm

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Interactive testing with Playwright MCP
# See TESTING.md for complete guide
npm run preview     # Start preview server for testing
```

Use Playwright MCP browser tools to test the website interactively. See `TESTING.md` for detailed test scenarios and procedures.

### Code Quality

```bash
# Format code
npm run format

# Lint code
npm run lint
```

## 📦 Build Process

The website uses Vite for building and bundling:

1. **Development**: `npm run dev` - Hot reload, fast refresh
2. **Production**: `npm run build` - Optimized bundle, tree-shaking, minification
3. **Testing**: Interactive testing with Playwright MCP browser tools

## 🚢 Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the main branch:

1. **Build**: Vite creates optimized production bundle
2. **Deploy**: Built files are deployed to GitHub Pages
3. **Testing**: Manual testing with Playwright MCP tools

## 📊 Performance Monitoring

The website includes:

- Performance timing logs in console
- Lighthouse-friendly optimizations
- Responsive design testing
- Accessibility checks

## 🎨 Design System

Uses a custom design system built with Tailwind CSS:

- **Brand colors**: Red-based palette for primary branding
- **Accent colors**: Teal-based palette for highlights
- **Typography**: Inter font family
- **Components**: Reusable UI components with hover effects

## 📱 Features

- Responsive design (mobile-first)
- Smooth scrolling navigation
- Mobile-friendly menu
- Contact form integration
- Blog RSS feed integration
- Performance optimized images
- SEO-friendly structure

## 🔧 Technologies

- **Frontend**: HTML5, CSS3, Modern JavaScript (ES6+)
- **Styling**: Tailwind CSS v4
- **Build Tool**: Vite
- **Testing**: Playwright MCP
- **Deployment**: GitHub Pages
- **CI/CD**: GitHub Actions
