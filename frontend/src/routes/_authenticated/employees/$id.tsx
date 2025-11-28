import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/employees/$id')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_authenticated/employees/$id"!</div>
}
