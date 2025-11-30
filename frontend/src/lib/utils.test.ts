import { describe, expect, it } from 'vitest'
import { cn } from './utils'

describe('cn utility', () => {
  describe('basic class merging', () => {
    it('returns empty string for no arguments', () => {
      expect(cn()).toBe('')
    })

    it('returns single class unchanged', () => {
      expect(cn('text-red-500')).toBe('text-red-500')
    })

    it('merges multiple classes', () => {
      expect(cn('px-4', 'py-2')).toBe('px-4 py-2')
    })
  })

  describe('tailwind conflict resolution', () => {
    it('resolves conflicting padding classes', () => {
      expect(cn('px-4', 'px-8')).toBe('px-8')
    })

    it('resolves conflicting color classes', () => {
      expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
    })

    it('resolves conflicting background classes', () => {
      expect(cn('bg-white', 'bg-black')).toBe('bg-black')
    })
  })

  describe('conditional classes', () => {
    it('handles undefined values', () => {
      expect(cn('base', undefined, 'active')).toBe('base active')
    })

    it('handles null values', () => {
      expect(cn('base', null, 'active')).toBe('base active')
    })

    it('handles falsy class values', () => {
      const isHidden = false as boolean
      expect(cn('base', isHidden && 'hidden', 'active')).toBe('base active')
    })

    it('handles truthy class values', () => {
      const isActive = true as boolean
      expect(cn('base', isActive && 'active')).toBe('base active')
    })
  })

  describe('object syntax', () => {
    it('includes classes with truthy values', () => {
      expect(cn({ 'text-red-500': true, 'bg-white': true })).toBe(
        'text-red-500 bg-white'
      )
    })

    it('excludes classes with falsy values', () => {
      expect(cn({ 'text-red-500': true, 'bg-white': false })).toBe(
        'text-red-500'
      )
    })
  })

  describe('array syntax', () => {
    it('handles array of classes', () => {
      expect(cn(['px-4', 'py-2'])).toBe('px-4 py-2')
    })

    it('handles mixed array and string', () => {
      expect(cn('base', ['px-4', 'py-2'], 'text-center')).toBe(
        'base px-4 py-2 text-center'
      )
    })
  })
})
