import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  Bot,
  Building2,
  Calendar,
  Clock,
  LayoutDashboard,
  Search,
  Settings,
  User,
  Users,
  Wallet,
} from 'lucide-react'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'

interface CommandItem {
  title: string
  url: string
  icon: React.ElementType
  keywords?: string[]
}

const commands: CommandItem[] = [
  {
    title: 'Dashboard',
    url: '/dashboard',
    icon: LayoutDashboard,
    keywords: ['home', 'overview'],
  },
  {
    title: 'Employees',
    url: '/employees',
    icon: Users,
    keywords: ['staff', 'team', 'people'],
  },
  {
    title: 'Departments',
    url: '/departments',
    icon: Building2,
    keywords: ['teams', 'groups'],
  },
  {
    title: 'Attendance',
    url: '/attendance',
    icon: Clock,
    keywords: ['presence', 'check-in'],
  },
  {
    title: 'Leave',
    url: '/leave',
    icon: Calendar,
    keywords: ['vacation', 'time-off', 'pto'],
  },
  {
    title: 'Payroll',
    url: '/payroll',
    icon: Wallet,
    keywords: ['salary', 'payment'],
  },
  {
    title: 'AI Assistant',
    url: '/ai-assistant',
    icon: Bot,
    keywords: ['chat', 'help', 'ai'],
  },
  {
    title: 'Profile',
    url: '/profile',
    icon: User,
    keywords: ['account', 'me'],
  },
  {
    title: 'Settings',
    url: '/settings',
    icon: Settings,
    keywords: ['preferences', 'config'],
  },
]

export function CommandMenu() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const handleSelect = (url: string) => {
    setOpen(false)
    navigate({ to: url as any })
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className='inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground'
      >
        <Search className='h-4 w-4' />
        <span className='hidden sm:inline'>Search...</span>
        <kbd className='pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex'>
          <span className='text-xs'>⌘</span>K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder='Search pages...' />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading='Pages'>
            {commands.map((item) => {
              const Icon = item.icon
              return (
                <CommandItem
                  key={item.url}
                  value={`${item.title} ${item.keywords?.join(' ') || ''}`}
                  onSelect={() => handleSelect(item.url)}
                >
                  <Icon className='mr-2 h-4 w-4' />
                  <span>{item.title}</span>
                </CommandItem>
              )
            })}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
