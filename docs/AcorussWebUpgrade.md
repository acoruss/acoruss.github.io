Acoruss Website Upgrade

Goal: move https://acoruss.com from a static single page website to a fully-fledged agency website with integrated backend web functionality.

Expected outcome: An agency grade website with intuitive layout, call to actions that convert and website information that is clear and up to date.

Non-goals: logo changes.

Current state

Static single page website with clear CTAs and copy. It has well broken-down sections with clear messaging and structure. The footer is minimalist highlighting internal and external links well. Consistent color and theme.

Hosting: GitHub pages hosting.

Code: Tailwind CSS built with NPM, Single index.html, main.js and style.css files. Additional privacy-policy.html and terms-of-service.html. Public folder with logos.

What is not right

White background all through.

There’s a lot of whitespaces on the hero section.

We show the services that we offer, but we are missing pricing for these services.

Links to the call to actions like booking a 15-minute intro call does not work.

How we work process is numbered but a better design could communicate this.

Ongoing support is not clearly shown, appears like a small section on its own which makes its intention not clear.

Our projects lead to dead URLs.

We don’t show more of the projects that we have worked on.

Our core values clicking through opens both dropdowns and show content for the one you clicked; this signals a bug in that design.

Our leadership has no images.

Contact us form does not work.

Terms of service and privacy policy seem outdated and are not with the same design as the website.

AI copy messaging that suggests lack of grounding on beliefs.

Solution

Move https://acoruss.com to a full web application with backend capabilities. This allows us to:

Enable payments, processing, and auditing.

Create a lead qualification for customers who make inquiries or have difficulty converting.

Deliver engagement from our CTAs to our email or a backend portal.

Incorporate updating projects content through a backend portal.

Future proof for additional tooling like AI chatbots or WhatsApp integration.

Backend details

Dockerized Django app, tailwind CSS for UI, vanilla js.

Storage: Postgres DB, images in Minio locally and azure storage in prod

Stored data: super adminuser details, leads, inquiries, projects, pricing, audit logs, payments details for projects

Admins: users with super admin role

Admin workflows: create/edit/delete projects, view inquiries, export leads

Forms protected with CSRF tokens.

Requirements

Website copy content

“Our leaders” section images

Email integration details

Deliver to info@acoruss.com

Send confirmation email to user.

Spam protection (recaptcha)

Retries + failure visibility in admin

Calendar booking

Payment processing gateway

Website Copy, Layout and Design Details

Responsive first design. In big screens, the text and layouts are optimized and in smaller screens, the text also reduces and is optimized to look and feel minimal, well laid out.

Base html page with; navigation bar, main content section and footer.

The index, terms of service and privacy policy pages inherit from the base.html and puts content in the main content section.

The navigation bar has a logo and the text “Acoruss” on the left hand side and on the right hand side, eight menu items and a call-to-action button “Tell us about your project” that leads to a form (contact us page which opens in its own URL (/contact-us) and inherits from the base html. In a responsive layout (mobile screen), this menu collapses into a hamburger icon. When you click on it, a side menu appears and at the top of the menu is the CTA button then below it, the eight menu items.

The eight menu items with their URLs in brackets are:

Home (/) goes to the home page

Services (/services) opens to a new page which inherits the base html and lists more details about services.

Pricing (/pricing) opens to the pricing page which has pricing details.

Process (#process) goes to the “Our Process” section

Projects (/projects) opens to a new page which inherits the base html and lists more projects

Blog (https://acoruss.substack.com) external link

About (/about-us) goes to the “About Us” page.

Contact (/contact-us) opens to a new page which inherits the base html and lists more

Home section:

Hero text: Empowering Businesses Through Technology

Sub text: We help businesses harness software, AI, and strategic technology - without the heavy costs of building from scratch. From advisory to implementation, we simplify operations and drive sustainable growth.

Two call-to-action buttons: Book A Discovery Call (navigates to our booking calendar), See our Process (goes to #process section)

It is a full screen section. In mobile, it’s also a full-screen section. The background is an animation mp4/webpm loop of businesspeople using tech, from SMEs (say a mama mboga checking an order) to big corporates (viewing graphs and analytics dashboard).

Why choose us section:

Title: The Acoruss Advantage

Subtitle: We bring together expansive and long experience, expert domain knowledge and outstanding aftersalesdeploy services to deliver technological solutions you can trust.

Super sub-title: we don’t just churn code and big words; we walk with you every step of way.

Reasons to choose us will be cards that are also responsive:

Production-grade Quality: industry standard solutions with extra security hardening and customization for your needs.

Experienced Experts: 20+ cumulative years of experience in the industry, working for high profile corporate organizations and startups.

Customer satisfaction: Ensuring your complete satisfaction and reliability first engineering.

Our services section

Title: Out of the box software solutions

Subtitle: From initial consultation to ongoing maintenance, we provide complete software solutions tailored to your needs.

Services:

Only four cards. Each card is a link to a section of services where we have a project. Hovering a card turns the mouse to a hand and clicking navigates to where the link for the “Learn more” button in the site leads.

The services cards will be:

Website development: Simple landing pages to complex corporate or organizational websites, we help you build and run your business online. The “Learn more” button leads to /services#website-development.

Custom Software: We design and build software tailored to your needs - web apps, internal systems, and tools that scale, simplify operations, and deliver measurable results. “Learn more” button leads to /services#custom-software

AI and Automation Solutions: Harness AI and automation to save time, cut costs, and make smarter decisions. From chatbots to workflow automation, we fit solutions to your processes. “Learn more” button leads to /services#ai

Technology Strategy & Consulting: We assess your setup, identify gaps, and design a strategy that aligns with your goals - reducing risk, avoiding wasted spending, and building a competitive edge. “Learn more” button leads to /services#consultation

The “See all our services” call to action button below the four cards will lead to /services page.

How we work section:

Title: How we work

Subtitle: A clear, secure process that keeps projects focused and predictable from start to finish.

Six steps in the process:

Reach out: tell us about your goals and context. Add the CTA button to the contact form.

Discovery Call: 60-minute deep-dive on needs, constraints, and success metrics. A small text showing “Small discovery fee of Ksh. 5000 applies, fully credited if you proceed.”

Proposal and plan: Scope, timeline, pricing, risks & mitigations including security considerations.

Kickoff: Finalize SOW, deposit invoice, communication rhythm, and security baselines.

Build & Iterate: Short sprints with demos. Security baked in; OWASP coding, dependency checks, CI/CD hardening.

Delivery & Handover: User Acceptance Testing, documentation, training, and security review of access & data handling.

Process can be visualized with better tooling and made responsive too.

Ongoing Support Available. This is a small section below the processes. It will have:

Maintenance: Updates, fixes, optimizations, and security patches.

Implementation: Executing consulting outcomes and rolling out new technology with proper controls.

Call to action “Prefer a quick fit check? Book a free 15-minute intro call” that leads to the calendar booking section.

Our Projects section:

Title: Our Projects

Subtitle: Real work that demonstrates how we design, build, and deliver solutions.

Three projects highlighted:

xPerience Nairobi

Intro: Use AI to plan your free time with bespoke activities in Nairobi.

Outcome: Full-featured website, AI chat, create plans and share with friends, discover events with your mood.

Two buttons CTA: “Build Similar Site” (leads to Contact form) and “See the Site” (leads to the site https://experiencenairobi.com with utm_source=acoruss.com)

Martin and Loice Wedding

Intro: custom website to invite guests and rsvp to wedding.

Outcome: fast, mobile-first guest experience site with pizzaz

Two buttons CTA: “Build Similar Site” (leads to Contact form) and “See the Site” (leads to the site https://wedding.martinandloice.life with utm_source=acoruss.com)

SDKs for GavaConnect APIs

Intro: Easily connect with government services through their APIs and simple to use SDKs

Value: Faster integrations, fewer bugs, maintainable codebases

Two buttons CTA: “Build Your SDK” (leads to Contact form) and “See Our SDKs” (leads to the site https://github.com/search?q=topic%3Agavaconnect+org%3Aacoruss&type=Repositorieswith utm_source=acoruss.com)

“See our Projects” CTA button that leads to /projects page.

Latest from our blog section:

Title: Latest from our blog

Subtitle: Insights on technology, strategy, and in novation to help your business thrive in the digital age.

Link to the latest substack article showing:

Date, title, description of article/introduction

“Read more” button leading to the article location.

Substack CTA for staying updated and subscribe.

“Read the Blog” button at the bottom of the section leading to https://acoruss.substack.com.

Contact us section:

Title: contact us

Subtitle: Ready to transform your business with technology? Let's build something amazing together.

Form with:

Full name*, email*, company, message\* fields. All fields with asteriks are required. And a submit button “Send message”

Small text at the bottom of the “Send Message” button saying “We'll use your information to respond to your inquiry. Privacy Policy(linking to /privacy)”

Small card with:

Title: Get in Touch

Email: info@acoruss.com

Location: Nairobi, Kenya

Phone number: +254 705 867 162

Footer section divided into three rows:

Logo and “Acoruss” beside it on the left. Below is the text “We build software and open-source tools that help businesses adopt technology with confidence. From advisory to implementation, we simplify complexity, reduce costs, and protect trust.” Below this text is the social icons for LinkedIn(https://www.linkedin.com/company/acoruss), GitHub(https://github.com/acoruss) and Substack(https://acoruss.substack.com)

Quick links are in the middle, and they have links to: Services, Pricing, Our Process, Blog, Projects, Blog, About Us, Contact Us.

Resources are on the right and they have links to: Blog, Open Source, SDKs, Privacy Policy and Terms of Service

The services page which inherits from the base html will:

Seven cards that behave like tabs. When you click on a card, it shows the details of the card:

Website Development: Subtitle: We help you build and run your business online. Offerings:

Basic or landing page:

simple one-page or few-page site that shares key information like who you are, what you do, and how to contact you.

Ideal for: event promotion, personal brand or portfolio, simple service like consultancy.

What we do: Up to five clear sections (hero, services, about, contact, footer), responsive design, basic contact form or WhatsApp link, simple image and text content you will provide. We can use your ready-to-go template inspirations, our own or customize it for you for a fee.

Pricing: Starting from Ksh. 30,000 up to Ksh. 100,000.

Small business website:

Multi-paged website showcasing the business or services to generate leads and convert users.

Ideal for: small businesses building online presence and support day to day sales and inquiries.

What we do: Up to seven pages (Home, about, services or products, Team or company profile, Portfolio/Projects, Testimonials, Contact page with form and map), responsive design, on page SEO and GEO setup, Google Analytics Tracking, Training or light support after launch.

Pricing: Starting from Ksh. 80,000 up to Ksh. 150,000.

E-Commerce Store:

for selling products or services and managing orders online.

Ideal for: businesses that are scaling their services to capture the online market through selling from their website and executing orders.

What we do: Product listings with images, prices, and descriptions, categories and search or filters, shopping cart and checkout flow, payment integration for M-Pesa, cards, and sometimes bank transfers, order management and basic stock tracking, customer emails for order confirmation and shipping updates, Performance tuning so pages load faster, app install capabilities through PWA, security monitoring and backups. In such setups, we give the option to host, or have you host the application.

Pricing: Starting from Ksh. 130,000 up to Ksh. 500,000 or more, depending on the volume, features and maintaining needs.

Corporate or large organization:

Targeting large companies, government bodies or NGOs, Banks, SACCOs, hospitals, or universities, strong consumer brands that get heavy traffic.

What we do: Dozens of pages, custom layouts for departments, services, or regions, user roles for different teams to manage content, advanced search resources and document libraries, integrations with internal systems like Microsoft Dynamics, SAP, or custom ERPs. We will ensure: Detailed planning and stakeholder workshops, Strong information architecture so users find what they need quickly, Accessible, responsive design across many devices, Robust security, user access control, and audit trails, Team collaboration with designers, developers, security experts, and content teams

Pricing: Starting from Ksh. 350,000 or more as we will discuss the extent of the website and quote depending on the requirements.

Custom Software Development:

Subtitle: We design and build software tailored to your needs - web apps, internal systems, and tools that scale, simplify operations, and deliver measurable results.

What we do: our main domain is web technologies. We have experience in Web Application development, Mobile development, Cloud, integration etc. Our expertise in programming has enabled us to pursue other fields like the Internet of Things (IoT) and Electric Vehicles Technology.

Pricing: Small discovery fee of Ksh. 5000 applies, fully credited if you proceed. Development fee starts with Ksh. 100,000.

AI and Automation:

Subtitle: Harness AI and automation to save time, cut costs, and make smarter decisions.

What we do:

AI Consulting:

Talk to us to assess your AI readiness, identify high-impact opportunities, develop comprehensive roadmaps, and provide expert guidance on technology selection, ensuring your AI initiatives deliver measurable business value while maintaining ethical considerations.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed.

Chatbots:

We create intuitive, smart, and scalable chatbot applications with our AI/ML development services to better comprehend the content of conversations and provide human-like experiences to customers.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed. Development starts at Ksh. 50,000.

Workflow automation

Harness the predictive power of machine learning to build intelligent and adaptive applications.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed. Development starts at Ksh. 100,000.

AI agent Development:

Develop AI agents that go beyond mere automation. We can assist you in AI agent consultation, development, integration, training, and optimization.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed. Development starts at Ksh. 100,000.

Technology Strategy & Consulting:

Subtitle: We assess your setup, identify gaps, and design a strategy that aligns with your goals - reducing risk, avoiding wasted spending, and building a competitive edge.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed.

Security & Trust Engineering:

Subtitle: Protect your infrastructure, data, and applications through secure design, access controls, and resilient workflows. Including AI and SDK security expertise.

What we do: we audit your infrastructure, data schemas, applications, and access controls. We enforce zero-trust policy and ensure only the necessary access is granted through auditable processes.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed. Auditing fee starts with Ksh. 100,000 or more depending on the scale of the audit.

Process Optimization:

Subtitle: We analyze how you work and recommend tools, integrations, and workflows that make operations leaner - lower overheads, faster delivery, and more time for growth.

What we do: we make a discovery to find a fit, then spend some time with you or your team going through the processes. This is at least a day and up to five days. We prepare a report for possible automation or optimizations.

Pricing: Discovery fee of Ksh. 5000 applies, fully credited if you proceed. The daily rate of process analysis is Ksh. 10,000.

Open-Source Development

We build and share open-source SDKs and utilities. Reusable building blocks lower project costs, speed delivery, and increase long-term confidence.

What we do: we contribute to common software we leverage or use through code or donations. We contribute to open-source projects we are invited to or approached to maintain.

Pricing: Free or donation. If we get invited, the discovery fee of Ksh. 5000 applies, fully credited if you proceed. The contribution fee is discussed with the invitee.

The Projects page which inherits from the base html will:

Have six categories that behave like tabs:

Websites

SDKs

Custom Software

Open-Source

Automations

Artificial Intelligence

Each of these categories will have a list of projects.

Each project will have:

Image

Title, description, date of launch

Button to project page (/projects/uuid)

Project page will have been inherited from the base html file. It will have:

Image

Title, date of launch, details of implementation, value, price range

Social share buttons.

standard schema:

Problem

Approach

Stack

Timeline

outcomes (even qualitative)

screenshots

The about us page will inherit from the base html with:

“About Acoruss” title. “Learn about our mission, our team, and our commitment to empowering businesses through technology” sub-title.

Four small cards showing:

2025 officially launched

5+ team members

10+ projects

10+ customers

Below the cards, have a row split into two:

On the left side is “Our Story” with information about our story and how Acoruss came to be. This will be provided.

Right side is our team photo

A CTA to “View Our Completed Projects” leading to our /projects.

A “Key Milestones” section with the sub-title “Our journey has been marked by continuous growth and a commitment to excellence.”

A “Our Values” section with the sub-title “At Acoruss, our core values guide everything we do, from our customer interactions to our final handover”. Then has cards for the values:

Delight our customers: Create trust and lasting impact through exceptional service and results.

Team is key: Collaboration fuels growth and enables us to deliver better solutions.

Quality over quantity: Focus on depth and reliability rather than volume.

Simplicity matters: Technology should simplify business and life, not complicate it.

Innovation with purpose: Empower people and solve real problems, not just showcase technology.

Security by default: OWASP-aligned practices and continuous risk reduction in everything we build.

A “Our Leadership" section with “Meet the passionate leaders driving innovation and security at Acoruss.” as the sub-title. Then lists:

Loice Andia

Co-Founder & Managing Director

Leads strategy and operations while pursuing an MSc in Engineering Business Management (University of Bath). Bridges technical innovation with organizational impact; strengths in data governance, access policy, and risk management.

Button links to LinkedIn(https://www.linkedin.com/in/loice-andia/) and GitHub(https://github.com/lakivisi)

Martin Musale

Co-Founder & Director of Technology

Passionate about developer tools and secure software. Focus on secure architecture, IAM/RBAC, supply-chain security, CI/CD hardening, and threat modeling for web and AI systems - embedding security at every stage.

Button links to LinkedIn(https://linkedin.com/in/musalemartin) and GitHub(https://github.com/musale)

A CTA section with:

Title: Ready to transform your business with technology?

Sub-title: Let's build something amazing together.

CTA button “Contact Us”

“Contact Us” page inheriting from the base html file:

Title: “Ready to transform your business?”

Subtitle: “Let's build something amazing together.”

Contact the form and submit the button.

Pricing page:

Title: “Transparent pricing, scoped to outcomes.”

Subtitle: A short statement explaining that pricing is based on scope, complexity, integrations, and timelines.

Two CTA buttons:

Primary: “Request a quote” → /contact-us

Secondary: “Book discovery call” → booking link

How our pricing works

A 6-step visual strip:

Discovery

Scope & estimate

Proposal & milestones

Build & QA

Launch & handover

Support & iteration

What influences cost (bullets):

Number of pages/screens

Integrations (payments, CRM, auth, messaging)

Content readiness (copy, images, brand assets)

Deadline / urgency

Security/compliance requirements

“Start here” pricing anchors (high-level, not detailed)

Pricing buckets that summarize common outcomes.

Launch / Marketing websites

Who’s it for: individuals and small businesses, often with a single product or service

Timeline: one week

From: Ksh. 30,000 up to Ksh. 100,000

CTA: “See exact pricing” linking to the service page anchor

Business websites that generate leads

Who’s it for: small businesses and individuals building online presence and business.

Timeline: four to six weeks or more. The timeline assumes that the client provides copy/images within seven days.

From: Ksh. 80,000 up to Ksh. 150,000.

CTA: “See exact pricing” linking to the service page anchor

E-commerce & bookings

Who’s it for: businesses that are scaling their services to capture the online market through selling from their website and executing orders.

Timeline: six to eight weeks or more

From: Ksh. 130,000 up to Ksh. 500,000 or more, depending on the volume, features and maintaining needs.

CTA: “See exact pricing” linking to the service page anchor

Web apps & portals

Who’s it for: businesses and individuals who are intent on using web technologies to run or streamline their processes.

Timeline: four to six weeks

From: Ksh. 100,000

CTA: “See exact pricing” linking to the service page anchor

Automation & integrations

Who’s it for: individuals or businesses with processes that would benefit from machine processes like daily reporting and analysis.

Timeline: four to six weeks

From: Ksh. 50,000 up to Ksh. 250,000 or more depending on processes or integration details.

CTA: “See exact pricing” linking to the service page anchor

Security & hardening

Who’s it for: businesses that have built solutions or products that have been compromised before or need audits to determine their security standing.

Timeline: four to six weeks

From: Ksh. 100,000

CTA: “See exact pricing” linking to the service page anchor

Payment structure (standard):

Deposit 30% to start

Milestone billing

Final payment at handover

Change requests:

What counts as “in scope” vs “out of scope”

How change orders are handled

Ownership:

Client owns custom deliverables after full payment.

Acoruss retains ownership of pre-existing frameworks, libraries, internal tooling, and reusable components.

Licenses clarified in SOW.

Ongoing support has no roll-over:

Essentials (basic maintenance):

From Ksh. 10,000.

Includes: 10 hours/month, response within 1 working day, monitoring and backups

Excludes: working on non-working hours

Standard (maintenance + small improvements):

From Ksh 15,000.

Includes: 15 hours/month, response within 12 hours, monitoring and backups

Excludes: working on non-working hours

Priority (faster response + monitoring + proactive work)

From Ksh. 25,000

Includes: 20 hours/month, response within four hours, monitoring and backups

Excludes: working on non-working hours

Discovery fee and what the client receives:

A documented scope

Estimate range + timeline

Technical approach / architecture notes (where relevant)

Policy: credited to the project

FAQ section

Can you work on my budget?
Yes. We tailor our solutions to the budget and needs of the client. In the event the requirements are over the budget, we present a win-win proposal to fit that budget.

What if I already have designs/content?
We encourage clients to come up with their own designs and content. Creating the content or designs incurs more charges for the client, and more time is also spent on revisions.

What timelines should I expect?
Our timelines are arrived at based on the scope of work.

Do you offer retainers?
Yes. You can have Acoruss team on retainer for maintenance and routine work.

What happens after a project launch?
Depending on your type of project, we either do training for large projects or agree to maintenance for small projects. It will be clear on the scope of work.

How do you handle revisions?
Depending on the project, we do at most two revisions. If there is a need for more revisions, we always agree with the client on the final outcomes. If they are different from the agreed scope of work, we come to an agreement on the final outcome.

Final CTA section

Repeat primary CTA: “Request a quote” → /contact-us

Secondary: “Book discovery call”
