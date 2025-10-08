import axios from 'axios'
import * as Sentry from '@sentry/react'

const API_URL = import.meta.env.VITE_API_URL

// Create axios instance
const axiosInstance = axios.create({
  baseURL: API_URL,
})

// Add response interceptor to capture errors in Sentry
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only capture 4xx and 5xx errors
    if (error.response && error.response.status >= 400) {
      // Parse request body if it exists
      let requestBody = null
      if (error.config?.data) {
        try {
          // Handle FormData
          if (error.config.data instanceof FormData) {
            requestBody = 'FormData (binary content not captured)'
          } else if (typeof error.config.data === 'string') {
            requestBody = JSON.parse(error.config.data)
          } else {
            requestBody = error.config.data
          }
        } catch {
          requestBody = error.config.data?.toString() || 'Unable to parse request body'
        }
      }

      // Parse response body if it's a Blob
      let responseData = error.response.data
      if (error.response.data instanceof Blob) {
        responseData = 'Blob (binary content not captured)'
      }

      Sentry.captureException(error, {
        contexts: {
          response: {
            status: error.response.status,
            statusText: error.response.statusText,
            headers: error.response.headers,
            data: responseData,
          },
          request: {
            url: error.config?.url,
            baseURL: error.config?.baseURL,
            method: error.config?.method?.toUpperCase(),
            headers: error.config?.headers,
            params: error.config?.params,
            body: requestBody,
          },
        },
        tags: {
          http_status: error.response.status,
          http_method: error.config?.method?.toUpperCase(),
          endpoint: error.config?.url,
        },
        fingerprint: [
          error.config?.method || 'unknown',
          error.config?.url || 'unknown',
          String(error.response.status),
        ],
      })
    }
    return Promise.reject(error)
  }
)

// Export both the instance and isAxiosError for backward compatibility
export default axiosInstance
export const isAxiosError = axios.isAxiosError
