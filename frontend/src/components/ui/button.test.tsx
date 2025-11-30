import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './button'

describe('Button component', () => {
  describe('rendering', () => {
    it('renders with default props', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
    })

    it('renders children correctly', () => {
      render(<Button>Submit Form</Button>)
      expect(screen.getByText('Submit Form')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(<Button className="custom-class">Button</Button>)
      expect(screen.getByRole('button')).toHaveClass('custom-class')
    })
  })

  describe('variants', () => {
    it('applies default variant styles', () => {
      render(<Button variant="default">Default</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary')
    })

    it('applies destructive variant styles', () => {
      render(<Button variant="destructive">Delete</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive')
    })

    it('applies outline variant styles', () => {
      render(<Button variant="outline">Outline</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border')
    })

    it('applies ghost variant styles', () => {
      render(<Button variant="ghost">Ghost</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-accent')
    })
  })

  describe('sizes', () => {
    it('applies default size', () => {
      render(<Button size="default">Default Size</Button>)
      expect(screen.getByRole('button')).toHaveClass('h-9')
    })

    it('applies small size', () => {
      render(<Button size="sm">Small</Button>)
      expect(screen.getByRole('button')).toHaveClass('h-8')
    })

    it('applies large size', () => {
      render(<Button size="lg">Large</Button>)
      expect(screen.getByRole('button')).toHaveClass('h-10')
    })

    it('applies icon size', () => {
      render(<Button size="icon">🔍</Button>)
      expect(screen.getByRole('button')).toHaveClass('size-9')
    })
  })

  describe('interactions', () => {
    it('handles click events', async () => {
      const user = userEvent.setup()
      let clicked = false
      render(<Button onClick={() => (clicked = true)}>Click</Button>)

      await user.click(screen.getByRole('button'))
      expect(clicked).toBe(true)
    })

    it('does not fire click when disabled', async () => {
      const user = userEvent.setup()
      let clicked = false
      render(
        <Button disabled onClick={() => (clicked = true)}>
          Disabled
        </Button>
      )

      await user.click(screen.getByRole('button'))
      expect(clicked).toBe(false)
    })
  })

  describe('accessibility', () => {
    it('has correct button role', () => {
      render(<Button>Accessible</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('supports aria-label', () => {
      render(<Button aria-label="Close dialog">×</Button>)
      expect(screen.getByLabelText('Close dialog')).toBeInTheDocument()
    })

    it('shows disabled state', () => {
      render(<Button disabled>Disabled</Button>)
      expect(screen.getByRole('button')).toBeDisabled()
    })
  })

  describe('asChild prop', () => {
    it('renders as child element when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      )
      expect(screen.getByRole('link', { name: /link button/i })).toBeInTheDocument()
    })
  })
})
