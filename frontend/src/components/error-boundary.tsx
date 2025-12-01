import { Component } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import type { ErrorInfo, ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
}

/**
 * Error Boundary component to catch JavaScript errors in child components.
 * Provides a fallback UI when an error occurs.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    this.setState({ errorInfo })

    // In production, you would send this to an error reporting service
    // Example: Sentry.captureException(error, { extra: errorInfo })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center p-8">
          <div className="w-full max-w-md rounded-lg border border-destructive/20 bg-destructive/5 p-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-6 w-6" />
              <h2 className="text-lg font-semibold">Something went wrong</h2>
            </div>

            <p className="mt-3 text-sm text-muted-foreground">
              An unexpected error occurred. Please try again or contact support
              if the problem persists.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <div className="mt-4 rounded border bg-muted/50 p-3">
                <p className="font-mono text-xs text-destructive">
                  {this.state.error.message}
                </p>
                {this.state.error.stack && (
                  <pre className="mt-2 max-h-32 overflow-auto text-xs text-muted-foreground">
                    {this.state.error.stack}
                  </pre>
                )}
              </div>
            )}

            <Button
              onClick={this.handleReset}
              variant="outline"
              className="mt-4 w-full"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

/**
 * Functional component wrapper for route-level error handling
 */
export function RouteErrorFallback({
  error,
  reset,
}: {
  error: Error
  reset?: () => void
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>

        <h1 className="text-2xl font-bold">Page Error</h1>
        <p className="mt-2 text-muted-foreground">
          Sorry, something went wrong loading this page.
        </p>

        {import.meta.env.DEV && (
          <div className="mt-4 rounded-lg border bg-muted/50 p-4 text-left">
            <p className="font-mono text-sm text-destructive">
              {error.message}
            </p>
          </div>
        )}

        <div className="mt-6 flex justify-center gap-3">
          {reset && (
            <Button onClick={reset} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          )}
          <Button onClick={() => (window.location.href = '/')}>Go Home</Button>
        </div>
      </div>
    </div>
  )
}
