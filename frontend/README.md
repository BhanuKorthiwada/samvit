# SAMVIT Frontend

Modern React frontend for the SAMVIT HRMS (Human Resource Management System).

## Features

- ⚡ **Vite** - Lightning-fast dev server and builds
- ⚛️ **React 19** - Latest React with concurrent features
- 🔷 **TypeScript** - Full type safety
- 🎨 **Tailwind CSS 4** - Utility-first styling
- 🧭 **TanStack Router** - Type-safe file-based routing
- 📊 **TanStack Query** - Data fetching and caching
- 📋 **TanStack Table** - Powerful data tables
- 📝 **React Hook Form** - Performant forms with Zod validation
- 🎯 **Radix UI** - Accessible UI primitives
- 📈 **Recharts** - Beautiful charts
- 🌙 **Dark Mode** - System-aware theming
- 🛡️ **Error Boundaries** - Graceful error handling

## Quick Start

### Prerequisites

- Node.js 20+
- pnpm 9+

### Installation

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The app runs at **http://localhost:3010**

### Available Scripts

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start dev server on port 3010 |
| `pnpm build` | Type-check and build for production |
| `pnpm preview` | Preview production build locally |
| `pnpm test` | Run tests in watch mode |
| `pnpm test:run` | Run tests once |
| `pnpm test:coverage` | Run tests with coverage |
| `pnpm typecheck` | Run TypeScript type checking |
| `pnpm lint` | Lint source files |
| `pnpm lint:fix` | Lint and auto-fix issues |
| `pnpm format` | Format source files |
| `pnpm format:check` | Check formatting |
| `pnpm check` | Run typecheck + lint + format check |

## Project Structure

```
src/
├── components/         # Reusable components
│   ├── ui/            # shadcn/ui components
│   ├── ErrorBoundary.tsx
│   └── Header.tsx
├── contexts/          # React contexts
│   └── AuthContext.tsx
├── hooks/             # Custom React hooks
├── lib/               # Utilities and helpers
│   ├── api/           # API client and services
│   ├── env.ts         # Type-safe environment variables
│   └── utils.ts       # Utility functions
├── routes/            # File-based routes (TanStack Router)
│   ├── __root.tsx     # Root layout
│   └── index.tsx      # Home page
├── styles.css         # Global styles and Tailwind
└── main.tsx           # App entry point
```

## Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# API Configuration
VITE_API_URL=/api/v1

# Feature Flags
VITE_ENABLE_DEVTOOLS=true
```

Environment variables are validated at runtime using Zod. Access them via:

```typescript
import { env, isDev, isProd } from '@/lib/env'

console.log(env.VITE_API_URL)  // Type-safe access
```

## API Integration

The frontend proxies API requests to the backend:

- Development: `http://localhost:3010/api/*` → `http://localhost:8000/api/*`
- Production: Configure your reverse proxy

### Multi-Tenancy

SAMVIT uses **domain-based multi-tenancy**. Each tenant accesses the system via their own subdomain:

- `acme.samvit.bhanu.dev` → Acme Corporation
- `globex.samvit.bhanu.dev` → Globex Inc

The browser automatically includes the correct `Host` header, so no explicit tenant identification is needed in API calls. The backend resolves the tenant from the domain.

For local development, add entries to `/etc/hosts`:
```
127.0.0.1 acme.samvit.bhanu.dev
127.0.0.1 globex.samvit.bhanu.dev
```

### Making API Calls

```typescript
import { apiClient } from '@/lib/api/client'

// GET request
const employees = await apiClient.get('/employees')

// POST request
const newEmployee = await apiClient.post('/employees', {
  first_name: 'John',
  last_name: 'Doe',
})
```

## Routing

This project uses [TanStack Router](https://tanstack.com/router) with file-based routing. Routes are automatically generated from files in `src/routes/`.

| File | Route |
|------|-------|
| `__root.tsx` | Root layout (wraps all routes) |
| `index.tsx` | `/` |
| `about.tsx` | `/about` |
| `employees/index.tsx` | `/employees` |
| `employees/$id.tsx` | `/employees/:id` |

### Adding a New Route

Create a new file in `src/routes/` and TanStack Router will automatically register it:

```typescript
// src/routes/dashboard.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard')({
  component: DashboardPage,
})

function DashboardPage() {
  return <h1>Dashboard</h1>
}
```

### Adding Links

Use the `Link` component for SPA navigation:

```tsx
import { Link } from '@tanstack/react-router'

function Navigation() {
  return (
    <nav>
      <Link to="/">Home</Link>
      <Link to="/employees">Employees</Link>
      <Link to="/employees/$id" params={{ id: '123' }}>
        Employee Details
      </Link>
    </nav>
  )
}
```

More information: [Link documentation](https://tanstack.com/router/latest/docs/framework/react/api/router/linkComponent)

### Using Layouts

The root layout in `src/routes/__root.tsx` wraps all routes. Use `<Outlet />` to render child routes:

```tsx
import { Outlet, createRootRoute } from '@tanstack/react-router'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import Header from '@/components/Header'

export const Route = createRootRoute({
  component: RootLayout,
  errorComponent: ({ error }) => <ErrorFallback error={error} />,
})

function RootLayout() {
  return (
    <ErrorBoundary>
      <Header />
      <main>
        <Outlet />
      </main>
    </ErrorBoundary>
  )
}
```

More information: [Layouts documentation](https://tanstack.com/router/latest/docs/framework/react/guide/routing-concepts#layouts)

## Data Fetching

There are multiple ways to fetch data in SAMVIT.

### Option 1: Route Loaders

Load data before rendering a route using the `loader` function:

```tsx
// src/routes/employees/index.tsx
import { createFileRoute } from '@tanstack/react-router'
import { apiClient } from '@/lib/api/client'

export const Route = createFileRoute('/employees/')({
  loader: async () => {
    const response = await apiClient.get('/employees')
    return response.data
  },
  component: EmployeesPage,
})

function EmployeesPage() {
  const employees = Route.useLoaderData()
  
  return (
    <ul>
      {employees.map((employee) => (
        <li key={employee.id}>{employee.first_name} {employee.last_name}</li>
      ))}
    </ul>
  )
}
```

More information: [Loader documentation](https://tanstack.com/router/latest/docs/framework/react/guide/data-loading)

### Option 2: TanStack Query (React Query)

For more complex data fetching with caching, refetching, and mutations:

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

// Fetch employees
function useEmployees() {
  return useQuery({
    queryKey: ['employees'],
    queryFn: () => apiClient.get('/employees'),
  })
}

// Create employee mutation
function useCreateEmployee() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateEmployeeInput) => 
      apiClient.post('/employees', data),
    onSuccess: () => {
      // Invalidate and refetch employees list
      queryClient.invalidateQueries({ queryKey: ['employees'] })
    },
  })
}

// Usage in component
function EmployeesPage() {
  const { data: employees, isLoading, error } = useEmployees()
  const createEmployee = useCreateEmployee()
  
  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>
  
  return (
    <div>
      <button onClick={() => createEmployee.mutate({ first_name: 'John', last_name: 'Doe' })}>
        Add Employee
      </button>
      <ul>
        {employees?.map((emp) => (
          <li key={emp.id}>{emp.first_name}</li>
        ))}
      </ul>
    </div>
  )
}
```

#### Setting Up Query Provider

The Query provider should be set up in `main.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

root.render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
      <ReactQueryDevtools buttonPosition="bottom-left" />
    </QueryClientProvider>
  </StrictMode>
)
```

More information: [TanStack Query documentation](https://tanstack.com/query/latest/docs/framework/react/overview)

## State Management

For global state management, use [TanStack Store](https://tanstack.com/store/latest):

### Creating a Store

```tsx
import { Store } from '@tanstack/store'

// Define store with initial state
interface AppState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
}

export const appStore = new Store<AppState>({
  sidebarOpen: true,
  theme: 'light',
})
```

### Using Store in Components

```tsx
import { useStore } from '@tanstack/react-store'
import { appStore } from '@/stores/appStore'

function Sidebar() {
  const sidebarOpen = useStore(appStore, (state) => state.sidebarOpen)
  
  if (!sidebarOpen) return null
  
  return <aside>Sidebar content</aside>
}

function ToggleButton() {
  return (
    <button
      onClick={() => 
        appStore.setState((prev) => ({ 
          ...prev, 
          sidebarOpen: !prev.sidebarOpen 
        }))
      }
    >
      Toggle Sidebar
    </button>
  )
}
```

### Derived State

Create computed values that update when dependencies change:

```tsx
import { Store, Derived } from '@tanstack/store'

const cartStore = new Store({
  items: [
    { id: 1, name: 'Item 1', price: 10, quantity: 2 },
    { id: 2, name: 'Item 2', price: 20, quantity: 1 },
  ],
})

// Derived state for total
const cartTotalStore = new Derived({
  fn: () => 
    cartStore.state.items.reduce(
      (total, item) => total + item.price * item.quantity,
      0
    ),
  deps: [cartStore],
})
cartTotalStore.mount()

// Usage
function CartTotal() {
  const total = useStore(cartTotalStore)
  return <div>Total: ${total}</div>
}
```

More information: [TanStack Store documentation](https://tanstack.com/store/latest)

## UI Components

This project uses [shadcn/ui](https://ui.shadcn.com/) components built on [Radix UI](https://www.radix-ui.com/) primitives.

### Using Components

```typescript
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

function EmployeeCard({ employee }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{employee.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{employee.department}</p>
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline">View Details</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Employee Details</DialogTitle>
            </DialogHeader>
            {/* Dialog content */}
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  )
}
```

### Available Components

All shadcn/ui components are in `src/components/ui/`:

- **Layout**: Card, Separator, Tabs, Accordion, Collapsible
- **Forms**: Input, Select, Checkbox, Radio, Switch, Slider
- **Feedback**: Alert, Toast (Sonner), Progress, Skeleton
- **Overlay**: Dialog, Popover, Tooltip, Dropdown Menu, Context Menu
- **Navigation**: Navigation Menu, Menubar, Tabs
- **Data Display**: Table, Avatar, Badge

### Styling with cn()

Use the `cn()` utility to merge Tailwind classes:

```tsx
import { cn } from '@/lib/utils'

function MyComponent({ className, variant }) {
  return (
    <div
      className={cn(
        'rounded-lg p-4',
        variant === 'primary' && 'bg-primary text-primary-foreground',
        variant === 'secondary' && 'bg-secondary',
        className
      )}
    >
      Content
    </div>
  )
}
```

## Forms

Forms use [React Hook Form](https://react-hook-form.com/) with [Zod](https://zod.dev/) validation.

### Basic Form

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const employeeSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters'),
  lastName: z.string().min(2, 'Last name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  department: z.string().min(1, 'Please select a department'),
})

type EmployeeFormData = z.infer<typeof employeeSchema>

function EmployeeForm({ onSubmit }: { onSubmit: (data: EmployeeFormData) => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeSchema),
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Label htmlFor="firstName">First Name</Label>
        <Input id="firstName" {...register('firstName')} />
        {errors.firstName && (
          <p className="text-sm text-destructive">{errors.firstName.message}</p>
        )}
      </div>
      
      <div>
        <Label htmlFor="lastName">Last Name</Label>
        <Input id="lastName" {...register('lastName')} />
        {errors.lastName && (
          <p className="text-sm text-destructive">{errors.lastName.message}</p>
        )}
      </div>
      
      <div>
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" {...register('email')} />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>
      
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving...' : 'Save Employee'}
      </Button>
    </form>
  )
}
```

### Form with TanStack Form

For more complex forms, use [TanStack Form](https://tanstack.com/form/latest):

```tsx
import { useForm } from '@tanstack/react-form'
import { zodValidator } from '@tanstack/zod-form-adapter'
import { z } from 'zod'

function AdvancedForm() {
  const form = useForm({
    defaultValues: {
      firstName: '',
      lastName: '',
    },
    onSubmit: async ({ value }) => {
      await apiClient.post('/employees', value)
    },
    validatorAdapter: zodValidator(),
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        form.handleSubmit()
      }}
    >
      <form.Field
        name="firstName"
        validators={{
          onChange: z.string().min(2, 'Too short'),
        }}
      >
        {(field) => (
          <div>
            <Input
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
            />
            {field.state.meta.errors && (
              <p className="text-destructive">{field.state.meta.errors}</p>
            )}
          </div>
        )}
      </form.Field>
      <Button type="submit">Submit</Button>
    </form>
  )
}
```

## Data Tables

Use [TanStack Table](https://tanstack.com/table/latest) for powerful data tables:

```tsx
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from '@tanstack/react-table'

function EmployeesTable({ data }) {
  const columns = [
    {
      accessorKey: 'firstName',
      header: 'First Name',
    },
    {
      accessorKey: 'lastName',
      header: 'Last Name',
    },
    {
      accessorKey: 'email',
      header: 'Email',
    },
    {
      accessorKey: 'department',
      header: 'Department',
    },
  ]

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div>
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Pagination */}
      <div className="flex gap-2">
        <Button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
          Previous
        </Button>
        <Button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
          Next
        </Button>
      </div>
    </div>
  )
}
```

## Styling

This project uses [Tailwind CSS](https://tailwindcss.com/) v4 for styling.

### Theme Configuration

CSS variables are defined in `src/styles.css`:

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.141 0.005 285.823);
  --primary: oklch(0.21 0.006 285.885);
  --primary-foreground: oklch(0.985 0 0);
  /* ... more variables */
}

.dark {
  --background: oklch(0.141 0.005 285.823);
  --foreground: oklch(0.985 0 0);
  /* ... dark mode overrides */
}
```

### Using Theme Colors

```tsx
<div className="bg-background text-foreground">
  <h1 className="text-primary">Title</h1>
  <p className="text-muted-foreground">Description</p>
  <Button className="bg-primary text-primary-foreground">
    Click me
  </Button>
</div>
```

### Dark Mode

Dark mode is handled by [next-themes](https://github.com/pacocoursey/next-themes):

```tsx
import { useTheme } from 'next-themes'

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  
  return (
    <Button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      Toggle Theme
    </Button>
  )
}
```

## Testing

Tests use [Vitest](https://vitest.dev/) and [Testing Library](https://testing-library.com/).

### Writing Tests

```typescript
// src/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it('renders button text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>)
    expect(screen.getByText('Click me')).toBeDisabled()
  })
})
```

### Testing Components with Providers

```tsx
// src/test/utils.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryRouter } from '@tanstack/react-router'
import { render } from '@testing-library/react'

export function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}
```

### Testing API Calls

```tsx
import { renderWithProviders } from '@/test/utils'
import { server } from '@/test/mocks/server'
import { http, HttpResponse } from 'msw'

// Mock API response
server.use(
  http.get('/api/v1/employees', () => {
    return HttpResponse.json([
      { id: '1', firstName: 'John', lastName: 'Doe' },
    ])
  })
)

test('displays employees', async () => {
  renderWithProviders(<EmployeesList />)
  
  expect(await screen.findByText('John Doe')).toBeInTheDocument()
})
```

### Running Tests

```bash
pnpm test          # Watch mode
pnpm test:run      # Single run
pnpm test:coverage # With coverage report
```

## Charts & Visualization

Use [Recharts](https://recharts.org/) for data visualization:

```tsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const attendanceData = [
  { month: 'Jan', present: 22, absent: 2 },
  { month: 'Feb', present: 20, absent: 1 },
  { month: 'Mar', present: 23, absent: 0 },
]

function AttendanceChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={attendanceData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="present" stroke="#22c55e" />
        <Line type="monotone" dataKey="absent" stroke="#ef4444" />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

## Error Handling

### Error Boundaries

The app includes error boundaries for graceful error handling:

```tsx
import { ErrorBoundary, RouteErrorFallback } from '@/components/ErrorBoundary'

// Wrap components that might throw
<ErrorBoundary fallback={<p>Something went wrong</p>}>
  <RiskyComponent />
</ErrorBoundary>

// Route-level errors are handled automatically in __root.tsx
export const Route = createRootRoute({
  component: RootComponent,
  errorComponent: ({ error, reset }) => (
    <RouteErrorFallback error={error} reset={reset} />
  ),
})
```

### Toast Notifications

Use [Sonner](https://sonner.emilkowal.ski/) for toast notifications:

```tsx
import { toast } from 'sonner'

// Success toast
toast.success('Employee created successfully')

// Error toast
toast.error('Failed to save changes')

// Promise toast
toast.promise(saveEmployee(data), {
  loading: 'Saving...',
  success: 'Employee saved!',
  error: 'Failed to save employee',
})
```

## Build & Deploy

### Building for Production

```bash
# Type-check and build
pnpm build

# Preview the production build
pnpm preview
```

Build output is in `dist/`.

### Environment-Specific Builds

```bash
# Build with specific env file
pnpm build --mode staging
pnpm build --mode production
```

### Deployment Options

Deploy to any static hosting:

| Platform | Deploy Command |
|----------|---------------|
| **Vercel** | `vercel --prod` |
| **Netlify** | `netlify deploy --prod` |
| **Cloudflare Pages** | `wrangler pages deploy dist` |
| **AWS S3** | `aws s3 sync dist/ s3://your-bucket` |

### Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Development Tools

### DevTools Available

In development mode:

- **TanStack Router Devtools** - Bottom-right corner (routing state)
- **TanStack Query Devtools** - Bottom-left corner (query cache)
- **React DevTools** - Browser extension

Disable devtools via environment variable:

```bash
VITE_ENABLE_DEVTOOLS=false
```

### VS Code Extensions

Recommended extensions for this project:

- ESLint
- Prettier
- Tailwind CSS IntelliSense
- TypeScript Vue Plugin (Volar)

## Learn More

- [TanStack Documentation](https://tanstack.com)
- [React Documentation](https://react.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Radix UI Primitives](https://www.radix-ui.com)

## License

See [LICENSE](../LICENSE) in root directory.
