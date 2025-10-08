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
      Sentry.captureException(error, {
        contexts: {
          response: {
            status: error.response.status,
            statusText: error.response.statusText,
            data: error.response.data,
          },
          request: {
            url: error.config?.url,
            method: error.config?.method,
            params: error.config?.params,
          },
        },
        tags: {
          http_status: error.response.status,
          endpoint: error.config?.url,
        },
      })
    }
    return Promise.reject(error)
  }
)

// Export both the instance and isAxiosError for backward compatibility
export default axiosInstance
export const isAxiosError = axios.isAxiosError
