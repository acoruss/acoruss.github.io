// Import styles
import './style.css'

// Mobile menu functionality
document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  const mobileMenuButton = document.getElementById('mobile-menu-btn')
  const mobileMenu = document.getElementById('mobile-menu')
  
  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden')
    })

    // Close menu when clicking on links
    const menuLinks = mobileMenu.querySelectorAll('a')
    menuLinks.forEach(link => {
      link.addEventListener('click', () => {
        mobileMenu.classList.add('hidden')
      })
    })
  }

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute('href'))
      if (target) {
        const offsetTop = target.offsetTop - 80 // Account for fixed nav
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        })
        
        // Close mobile menu if open
        if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
          mobileMenu.classList.add('hidden')
        }
      }
    })
  })

  // Add scroll effect to navigation
  window.addEventListener('scroll', () => {
    const nav = document.querySelector('nav')
    if (nav) {
      if (window.scrollY > 50) {
        nav.classList.add('shadow-lg')
      } else {
        nav.classList.remove('shadow-lg')
      }
    }
  })

  // Initialize animations and blog
  observeElements()
  
  // Load blog posts asynchronously without blocking
  setTimeout(() => {
    loadBlogPosts()
  }, 100) // Small delay to ensure page loads smoothly
})

// Intersection Observer for animations
function observeElements() {
  const elements = document.querySelectorAll('.animate-fade-in, .animate-slide-up')
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationDelay = Math.random() * 0.3 + 's'
        entry.target.classList.add('animate-fade-in')
      }
    })
  }, { threshold: 0.1 })

  elements.forEach(el => observer.observe(el))
}

// Blog RSS Feed Loader
class BlogLoader {
  constructor() {
    this.rssUrl = 'https://acoruss.substack.com/feed'
    this.proxyUrl = 'https://api.allorigins.win/raw?url='
    this.cache = null
    this.cacheTime = 5 * 60 * 1000 // 5 minutes cache
    this.lastCacheTime = 0
  }

  async fetchRSSFeed() {
    // Check cache first
    if (this.cache && (Date.now() - this.lastCacheTime) < this.cacheTime) {
      return this.cache
    }

    try {
      const response = await fetch(this.proxyUrl + encodeURIComponent(this.rssUrl))
      if (!response.ok) throw new Error('Failed to fetch RSS feed')

      const xmlText = await response.text()
      const parser = new DOMParser()
      const xmlDoc = parser.parseFromString(xmlText, 'text/xml')

      // Check for parsing errors
      const parseError = xmlDoc.querySelector('parsererror')
      if (parseError) throw new Error('Failed to parse RSS feed')

      const items = Array.from(xmlDoc.querySelectorAll('item')).map(item => ({
        title: this.getTextContent(item, 'title'),
        link: this.getTextContent(item, 'link'),
        description: this.stripHtml(this.getTextContent(item, 'description')),
        pubDate: this.getTextContent(item, 'pubDate'),
        creator: this.getTextContent(item, 'dc\\:creator') || 'Acoruss',
        guid: this.getTextContent(item, 'guid')
      }))

      this.cache = items
      this.lastCacheTime = Date.now()
      return items
    } catch (error) {
      console.error('Error fetching blog posts:', error)
      return this.getFallbackData()
    }
  }

  getTextContent(parent, selector) {
    const element = parent.querySelector(selector)
    return element ? element.textContent.trim() : ''
  }

  stripHtml(html) {
    const temp = document.createElement('div')
    temp.innerHTML = html
    return temp.textContent || temp.innerText || ''
  }

  formatDate(dateString) {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Recent'
    }
  }

  estimateReadTime(content) {
    const wordsPerMinute = 200
    const words = content.split(' ').length
    const minutes = Math.ceil(words / wordsPerMinute)
    return Math.max(1, minutes)
  }

  truncateText(text, maxLength = 150) {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength).trim() + '...'
  }

  getFallbackData() {
    return [{
      title: 'Hello WWW',
      link: 'https://acoruss.substack.com/p/hello-www',
      description: 'At Acoruss, we believe that technology should empower, not overwhelm. In this first post, we share our vision of making technology more accessible, secure, and cost-effective — helping organizations innovate without the heavy costs of building from scratch.',
      pubDate: 'Mon, 18 Aug 2025 18:25:13 GMT',
      creator: 'Acoruss',
      guid: 'hello-www'
    }]
  }

  renderFeaturedPost(post) {
    if (!post) return ''

    return `
      <div class="lg:col-span-2 bg-gradient-to-br from-brand-50 to-accent-50 rounded-2xl p-8 border border-gray-100 card-hover">
        <div class="flex items-center space-x-2 mb-4">
          <span class="bg-brand-100 text-brand-800 px-3 py-1 rounded-full text-sm font-medium">Featured</span>
          <span class="text-gray-500 text-sm">${this.formatDate(post.pubDate)}</span>
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4 leading-tight">${post.title}</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">${this.truncateText(post.description, 200)}</p>
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-gradient-to-br from-brand-400 to-brand-600 rounded-full flex items-center justify-center">
              <span class="text-sm font-bold text-white">A</span>
            </div>
            <div>
              <p class="font-medium text-gray-900 text-sm">${post.creator}</p>
              <p class="text-gray-500 text-xs">${this.estimateReadTime(post.description)} min read</p>
            </div>
          </div>
          <a href="${post.link}" target="_blank" rel="noopener noreferrer"
            class="bg-brand-900 text-white px-6 py-2 rounded-full hover:bg-brand-800 transition-all duration-200 font-medium text-sm inline-flex items-center space-x-2">
            <span>Read More</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    `
  }

  renderRecentPost(post) {
    return `
      <div class="bg-white rounded-xl p-6 border border-gray-100 hover:shadow-md transition-shadow duration-200">
        <h4 class="font-semibold text-gray-900 mb-2 line-clamp-2">${post.title}</h4>
        <p class="text-gray-600 text-sm mb-4 line-clamp-3">${this.truncateText(post.description, 100)}</p>
        <div class="flex items-center justify-between text-xs text-gray-500">
          <span>${this.formatDate(post.pubDate)}</span>
          <a href="${post.link}" target="_blank" rel="noopener noreferrer" 
             class="text-brand-600 hover:text-brand-700 font-medium">Read →</a>
        </div>
      </div>
    `
  }

  async loadAndRenderBlog() {
    try {
      const posts = await this.fetchRSSFeed()

      if (posts && posts.length > 0) {
        // Render featured post
        const blogContent = document.getElementById('blog-content')
        if (blogContent) {
          const featuredPost = this.renderFeaturedPost(posts[0])
          const subscriptionCard = `
            <div class="bg-gray-900 rounded-2xl p-8 text-white relative overflow-hidden">
              <div class="absolute top-0 right-0 w-20 h-20 bg-brand-400 rounded-full -mr-10 -mt-10 opacity-20"></div>
              <div class="absolute bottom-0 left-0 w-16 h-16 bg-accent-400 rounded-full -ml-8 -mb-8 opacity-20"></div>
              <div class="relative z-10">
                <div class="w-12 h-12 bg-brand-600 rounded-lg flex items-center justify-center mb-4">
                  <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 class="text-xl font-bold mb-3">Stay Updated</h3>
                <p class="text-gray-300 text-sm mb-6 leading-relaxed">Get the latest insights on technology trends, AI adoption, and business optimization delivered to your inbox.</p>
                <a href="https://acoruss.substack.com/subscribe" target="_blank" rel="noopener noreferrer"
                  class="bg-white text-gray-900 px-6 py-3 rounded-full hover:bg-gray-100 transition-all duration-200 font-semibold text-sm w-full text-center block">
                  Subscribe to Blog
                </a>
                <p class="text-xs text-gray-400 mt-3 text-center">Free • No spam • Unsubscribe anytime</p>
              </div>
            </div>
          `

          blogContent.innerHTML = featuredPost + subscriptionCard
          blogContent.classList.remove('hidden')
        }

        // Render recent posts (skip first one as it's featured)
        const recentPosts = posts.slice(1, 4) // Show up to 3 recent posts
        const recentPostsContent = document.getElementById('recent-posts-content')
        if (recentPostsContent && recentPosts.length > 0) {
          const recentPostsHtml = `
            <div class="grid md:grid-cols-3 gap-6">
              ${recentPosts.map(post => this.renderRecentPost(post)).join('')}
            </div>
          `
          recentPostsContent.innerHTML = recentPostsHtml
          recentPostsContent.classList.remove('hidden')
        }

        // Update status
        const statusElement = document.getElementById('blog-status')
        if (statusElement) {
          statusElement.textContent = `Latest insights from our blog • ${posts.length} post${posts.length !== 1 ? 's' : ''} available`
        }
      } else {
        throw new Error('No posts found')
      }
    } catch (error) {
      console.error('Error loading blog posts:', error)
      this.showError()
    } finally {
      this.hideLoading()
    }
  }

  showError() {
    const statusElement = document.getElementById('blog-status')
    if (statusElement) {
      statusElement.textContent = 'Unable to load latest posts. Please visit our blog directly.'
      statusElement.className = 'text-amber-600 text-sm mb-4'
    }
  }

  hideLoading() {
    const loadingElements = [
      document.getElementById('blog-loading'),
      document.getElementById('recent-posts-loading')
    ]

    loadingElements.forEach(element => {
      if (element) element.classList.add('hidden')
    })
  }
}

// Blog loading functionality
async function loadBlogPosts() {
  const blogLoader = new BlogLoader()
  await blogLoader.loadAndRenderBlog()
}

// Performance monitoring
if ('performance' in window) {
  window.addEventListener('load', function() {
    setTimeout(function() {
      const perfData = performance.getEntriesByType('navigation')[0]
      if (perfData) {
        console.log('Page Load Performance:', {
          'DOM Content Loaded': Math.round(perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart),
          'Load Complete': Math.round(perfData.loadEventEnd - perfData.loadEventStart),
          'Total Load Time': Math.round(perfData.loadEventEnd - perfData.navigationStart)
        })
      }
    }, 0)
  })
}
