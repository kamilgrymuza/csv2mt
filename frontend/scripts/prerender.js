#!/usr/bin/env node
/**
 * Pre-render script for bilingual landing pages
 * Generates separate HTML files for English (/en/) and Polish (/pl/) versions
 * Works in Vercel's build environment (no dependencies needed)
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

console.log('📄 Pre-rendering bilingual landing pages...')

const distPath = path.resolve(__dirname, '../dist')
const indexHtmlPath = path.join(distPath, 'index.html')

// Read the base index.html
const baseHtml = fs.readFileSync(indexHtmlPath, 'utf-8')

// Create language-specific noscript content
function getNoscriptContent(lang) {
  const content = {
    en: {
      title: 'Convert Bank Statements to MT940 Format Instantly',
      subtitle: 'Seamlessly convert your bank statements from CSV, PDF, or Excel to standard MT940 format. AI-powered tool for instant, secure financial data processing.',
      featuresTitle: 'Key Features',
      feature1Title: 'AI-Powered Multi-Format Support',
      feature1Desc: 'Convert CSV, PDF, and Excel (XLS/XLSX) bank statements effortlessly using advanced AI technology.',
      feature2Title: 'Secure & Private',
      feature2Desc: 'Your data is processed securely and never stored on our servers.',
      feature3Title: 'Batch Conversion',
      feature3Desc: 'Convert multiple files at once with our premium plan.',
      pricingTitle: 'Pricing',
      freePlan: 'Free',
      freePlanDesc: 'Perfect for occasional conversions',
      freePrice: '$0',
      premiumPlan: 'Premium',
      premiumPlanDesc: 'For professionals and businesses',
      premiumPrice: '$4.99',
      perMonth: '/ month',
      freeFeature1: '✓ Up to 5 conversions',
      freeFeature2: '✓ Basic support',
      premiumFeature1: '✓ Unlimited conversions',
      premiumFeature2: '✓ Batch processing',
      premiumFeature3: '✓ Priority support',
      jsRequired: 'Please enable JavaScript to use the full application.',
      jsDesc: 'CSV2MT requires JavaScript for file uploads and conversions.'
    },
    pl: {
      title: 'Konwertuj wyciągi bankowe do formatu MT940 natychmiast',
      subtitle: 'Bezproblemowo konwertuj swoje wyciągi bankowe z formatów CSV, PDF lub Excel do standardowego formatu MT940. Narzędzie oparte na AI do natychmiastowego, bezpiecznego przetwarzania danych finansowych.',
      featuresTitle: 'Główne funkcje',
      feature1Title: 'Wsparcie wielu formatów oparte na AI',
      feature1Desc: 'Konwertuj wyciągi bankowe CSV, PDF i Excel (XLS/XLSX) bez wysiłku, korzystając z zaawansowanej technologii AI.',
      feature2Title: 'Bezpieczne i prywatne',
      feature2Desc: 'Twoje dane są przetwarzane bezpiecznie i nigdy nie są przechowywane na naszych serwerach.',
      feature3Title: 'Konwersja wsadowa',
      feature3Desc: 'Konwertuj wiele plików jednocześnie dzięki naszemu planowi premium.',
      pricingTitle: 'Cennik',
      freePlan: 'Darmowy',
      freePlanDesc: 'Idealny do okazjonalnych konwersji',
      freePrice: '0 zł',
      premiumPlan: 'Premium',
      premiumPlanDesc: 'Dla profesjonalistów i firm',
      premiumPrice: '19,99 zł',
      perMonth: '/ miesiąc',
      freeFeature1: '✓ Do 5 konwersji',
      freeFeature2: '✓ Podstawowe wsparcie',
      premiumFeature1: '✓ Nieograniczone konwersje',
      premiumFeature2: '✓ Przetwarzanie wsadowe',
      premiumFeature3: '✓ Priorytetowe wsparcie',
      jsRequired: 'Włącz JavaScript, aby korzystać z pełnej aplikacji.',
      jsDesc: 'CSV2MT wymaga JavaScript do przesyłania i konwersji plików.'
    }
  }

  const t = content[lang]

  return `
  <noscript>
    <div style="max-width: 1200px; margin: 0 auto; padding: 40px 20px; font-family: system-ui, -apple-system, sans-serif;">
      <header style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 2.5rem; font-weight: bold; color: #111; margin-bottom: 16px;">
          ${t.title}
        </h1>
        <p style="font-size: 1.25rem; color: #666; max-width: 800px; margin: 0 auto;">
          ${t.subtitle}
        </p>
      </header>

      <main>
        <section style="margin-bottom: 40px;">
          <h2 style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 24px;">${t.featuresTitle}</h2>
          <div style="display: grid; gap: 24px;">
            <div>
              <h3 style="font-size: 1.25rem; font-weight: bold; color: #111; margin-bottom: 8px;">
                ${t.feature1Title}
              </h3>
              <p style="color: #666;">${t.feature1Desc}</p>
            </div>
            <div>
              <h3 style="font-size: 1.25rem; font-weight: bold; color: #111; margin-bottom: 8px;">
                ${t.feature2Title}
              </h3>
              <p style="color: #666;">${t.feature2Desc}</p>
            </div>
            <div>
              <h3 style="font-size: 1.25rem; font-weight: bold; color: #111; margin-bottom: 8px;">
                ${t.feature3Title}
              </h3>
              <p style="color: #666;">${t.feature3Desc}</p>
            </div>
          </div>
        </section>

        <section style="margin-bottom: 40px;">
          <h2 style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 24px;">${t.pricingTitle}</h2>
          <div style="display: grid; gap: 24px; max-width: 800px;">
            <div style="border: 2px solid #e5e7eb; border-radius: 8px; padding: 24px;">
              <h3 style="font-size: 1.5rem; font-weight: bold; color: #111; margin-bottom: 8px;">${t.freePlan}</h3>
              <p style="color: #666; margin-bottom: 16px;">${t.freePlanDesc}</p>
              <p style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 16px;">${t.freePrice}<span style="font-size: 1rem; font-weight: normal; color: #666;"> ${t.perMonth}</span></p>
              <ul style="list-style: none; padding: 0;">
                <li style="margin-bottom: 8px; color: #374151;">${t.freeFeature1}</li>
                <li style="margin-bottom: 8px; color: #374151;">${t.freeFeature2}</li>
              </ul>
            </div>
            <div style="border: 2px solid #3b82f6; border-radius: 8px; padding: 24px;">
              <h3 style="font-size: 1.5rem; font-weight: bold; color: #111; margin-bottom: 8px;">${t.premiumPlan}</h3>
              <p style="color: #666; margin-bottom: 16px;">${t.premiumPlanDesc}</p>
              <p style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 16px;">${t.premiumPrice}<span style="font-size: 1rem; font-weight: normal; color: #666;"> ${t.perMonth}</span></p>
              <ul style="list-style: none; padding: 0;">
                <li style="margin-bottom: 8px; color: #374151;">${t.premiumFeature1}</li>
                <li style="margin-bottom: 8px; color: #374151;">${t.premiumFeature2}</li>
                <li style="margin-bottom: 8px; color: #374151;">${t.premiumFeature3}</li>
              </ul>
            </div>
          </div>
        </section>

        <div style="background: #f3f4f6; padding: 24px; border-radius: 8px; text-align: center;">
          <p style="color: #111; font-size: 1.125rem; margin-bottom: 8px;">
            <strong>${t.jsRequired}</strong>
          </p>
          <p style="color: #666;">${t.jsDesc}</p>
        </div>
      </main>
    </div>
  </noscript>
`
}

// Generate language-specific HTML
function generateLangHtml(lang) {
  let html = baseHtml

  // Add noscript content
  const noscriptContent = getNoscriptContent(lang)
  html = html.replace(/<body>/, `<body>\n${noscriptContent}`)

  // Update canonical URL
  html = html.replace(
    /<link rel="canonical" href="https:\/\/csv2mt\.com\/" \/>/,
    `<link rel="canonical" href="https://csv2mt.com/${lang}/" />`
  )

  // Add hreflang tags
  const hreflangTags = `
    <!-- Language alternates -->
    <link rel="alternate" hreflang="en" href="https://csv2mt.com/en/" />
    <link rel="alternate" hreflang="pl" href="https://csv2mt.com/pl/" />
    <link rel="alternate" hreflang="x-default" href="https://csv2mt.com/en/" />`

  html = html.replace(/<\/head>/, `${hreflangTags}\n  </head>`)

  // Update lang attribute in html tag
  html = html.replace(/<html([^>]*)>/, `<html$1 lang="${lang}">`)

  return html
}

// Create /en/ and /pl/ directories
const enDir = path.join(distPath, 'en')
const plDir = path.join(distPath, 'pl')

if (!fs.existsSync(enDir)) fs.mkdirSync(enDir, { recursive: true })
if (!fs.existsSync(plDir)) fs.mkdirSync(plDir, { recursive: true })

// Generate and write English version
const enHtml = generateLangHtml('en')
fs.writeFileSync(path.join(enDir, 'index.html'), enHtml)
console.log('✅ Generated /en/index.html')

// Generate and write Polish version
const plHtml = generateLangHtml('pl')
fs.writeFileSync(path.join(plDir, 'index.html'), plHtml)
console.log('✅ Generated /pl/index.html')

// Update root index.html to point to /en/ as default
let rootHtml = baseHtml
rootHtml = rootHtml.replace(
  /<link rel="canonical" href="https:\/\/csv2mt\.com\/" \/>/,
  '<link rel="canonical" href="https://csv2mt.com/en/" />'
)
const rootHreflangTags = `
    <!-- Language alternates -->
    <link rel="alternate" hreflang="en" href="https://csv2mt.com/en/" />
    <link rel="alternate" hreflang="pl" href="https://csv2mt.com/pl/" />
    <link rel="alternate" hreflang="x-default" href="https://csv2mt.com/en/" />`
rootHtml = rootHtml.replace(/<\/head>/, `${rootHreflangTags}\n  </head>`)
fs.writeFileSync(indexHtmlPath, rootHtml)

console.log('✅ Pre-rendering complete!')
console.log('   - /en/index.html: English version with noscript content')
console.log('   - /pl/index.html: Polish version with noscript content')
console.log('   - Both versions have proper hreflang tags')
console.log('   - Canonical URLs point to language-specific pages')
console.log('   - Ready for search engine crawlers!')
