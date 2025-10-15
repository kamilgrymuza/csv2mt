#!/usr/bin/env node
/**
 * Simple SEO enhancement script for landing page
 * Adds noscript content and pre-rendered text for search engines
 * Works in Vercel's build environment (no dependencies needed)
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

console.log('📄 Enhancing landing page for SEO...')

const distPath = path.resolve(__dirname, '../dist')
const indexHtmlPath = path.join(distPath, 'index.html')

// Read the built index.html
let html = fs.readFileSync(indexHtmlPath, 'utf-8')

// Add SEO-friendly noscript content with key landing page info
const noscriptContent = `
  <noscript>
    <div style="max-width: 1200px; margin: 0 auto; padding: 40px 20px; font-family: system-ui, -apple-system, sans-serif;">
      <header style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 2.5rem; font-weight: bold; color: #111; margin-bottom: 16px;">
          Convert Bank Statements to MT940 Format Instantly
        </h1>
        <p style="font-size: 1.25rem; color: #666; max-width: 800px; margin: 0 auto;">
          Seamlessly convert your bank statements from CSV, PDF, or Excel to standard MT940 format.
          AI-powered tool for instant, secure financial data processing.
        </p>
      </header>

      <main>
        <section style="margin-bottom: 40px;">
          <h2 style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 24px;">Key Features</h2>
          <div style="display: grid; gap: 24px;">
            <div>
              <h3 style="font-size: 1.25rem; font-weight: bold; color: #111; margin-bottom: 8px;">
                AI-Powered Multi-Format Support
              </h3>
              <p style="color: #666;">
                Convert CSV, PDF, and Excel (XLS/XLSX) bank statements effortlessly using advanced AI technology.
              </p>
            </div>
            <div>
              <h3 style="font-size: 1.25rem; font-weight: bold; color: #111; margin-bottom: 8px;">
                Secure & Private
              </h3>
              <p style="color: #666;">
                Your data is processed securely and never stored on our servers.
              </p>
            </div>
            <div>
              <h3 style="font-size: 1.25rem; font-weight: bold; color: #111; margin-bottom: 8px;">
                Batch Conversion
              </h3>
              <p style="color: #666;">
                Convert multiple files at once with our premium plan.
              </p>
            </div>
          </div>
        </section>

        <section style="margin-bottom: 40px;">
          <h2 style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 24px;">Pricing</h2>
          <div style="display: grid; gap: 24px; max-width: 800px;">
            <div style="border: 2px solid #e5e7eb; border-radius: 8px; padding: 24px;">
              <h3 style="font-size: 1.5rem; font-weight: bold; color: #111; margin-bottom: 8px;">Free</h3>
              <p style="color: #666; margin-bottom: 16px;">Perfect for occasional conversions</p>
              <p style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 16px;">$0<span style="font-size: 1rem; font-weight: normal; color: #666;"> / month</span></p>
              <ul style="list-style: none; padding: 0;">
                <li style="margin-bottom: 8px; color: #374151;">✓ Up to 5 conversions</li>
                <li style="margin-bottom: 8px; color: #374151;">✓ Basic support</li>
              </ul>
            </div>
            <div style="border: 2px solid #3b82f6; border-radius: 8px; padding: 24px;">
              <h3 style="font-size: 1.5rem; font-weight: bold; color: #111; margin-bottom: 8px;">Premium</h3>
              <p style="color: #666; margin-bottom: 16px;">For professionals and businesses</p>
              <p style="font-size: 2rem; font-weight: bold; color: #111; margin-bottom: 16px;">$4.99<span style="font-size: 1rem; font-weight: normal; color: #666;"> / month</span></p>
              <ul style="list-style: none; padding: 0;">
                <li style="margin-bottom: 8px; color: #374151;">✓ Unlimited conversions</li>
                <li style="margin-bottom: 8px; color: #374151;">✓ Batch processing</li>
                <li style="margin-bottom: 8px; color: #374151;">✓ Priority support</li>
              </ul>
            </div>
          </div>
        </section>

        <div style="background: #f3f4f6; padding: 24px; border-radius: 8px; text-align: center;">
          <p style="color: #111; font-size: 1.125rem; margin-bottom: 8px;">
            <strong>Please enable JavaScript to use the full application.</strong>
          </p>
          <p style="color: #666;">
            CSV2MT requires JavaScript for file uploads and conversions.
          </p>
        </div>
      </main>
    </div>
  </noscript>
`

// Insert noscript content right after opening body tag
html = html.replace(/<body>/, `<body>\n${noscriptContent}`)

// Write back
fs.writeFileSync(indexHtmlPath, html)

console.log('✅ SEO enhancement complete!')
console.log('   - Added comprehensive noscript content')
console.log('   - Landing page info visible to search engines')
console.log('   - HTML ready for Vercel deployment')
