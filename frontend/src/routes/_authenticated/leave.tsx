import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import {
  AlertCircle,
  Calendar,
  CalendarDays,
  Clock,
  FileText,
  Plus,
  X,
} from 'lucide-react'
import type {
  LeaveBalanceResponse,
  LeavePolicyResponse,
  LeaveRequestResponse,
} from '@/lib/api/types'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  leaveBalanceService,
  leavePolicyService,
  leaveRequestService,
} from '@/lib/api'

export const Route = createFileRoute('/_authenticated/leave')({
  component: LeavePage,
})

function LeavePage() {
  const [balances, setBalances] = useState<Array<LeaveBalanceResponse>>([])
  const [requests, setRequests] = useState<Array<LeaveRequestResponse>>([])
  const [policies, setPolicies] = useState<Array<LeavePolicyResponse>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isApplyOpen, setIsApplyOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Apply leave form state
  const [selectedPolicy, setSelectedPolicy] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [reason, setReason] = useState('')
  const [formError, setFormError] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setIsLoading(true)
    try {
      const [balanceData, requestData, policyData] = await Promise.all([
        leaveBalanceService.getMyBalances().catch(() => []),
        leaveRequestService.getMyRequests().catch(() => []),
        leavePolicyService.list().catch(() => []),
      ])

      setBalances(balanceData)
      setRequests(requestData)
      setPolicies(policyData)
    } catch (err) {
      setError('Failed to load leave data')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')

    if (!selectedPolicy) {
      setFormError('Please select a leave type')
      return
    }
    if (!startDate || !endDate) {
      setFormError('Please select start and end dates')
      return
    }
    if (!reason.trim()) {
      setFormError('Please provide a reason')
      return
    }

    setIsSubmitting(true)
    try {
      await leaveRequestService.create({
        policy_id: selectedPolicy,
        start_date: startDate,
        end_date: endDate,
        reason: reason.trim(),
      })

      setIsApplyOpen(false)
      setSelectedPolicy('')
      setStartDate('')
      setEndDate('')
      setReason('')
      fetchData()
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : 'Failed to submit leave request',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelRequest = async (requestId: string) => {
    try {
      await leaveRequestService.cancel(requestId)
      fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel request')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-500/10 text-green-400'
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-400'
      case 'rejected':
        return 'bg-red-500/10 text-red-400'
      case 'cancelled':
      case 'withdrawn':
        return 'bg-slate-500/10 text-slate-400'
      default:
        return 'bg-slate-500/10 text-slate-400'
    }
  }

  const getLeaveTypeColor = (type: string) => {
    switch (type) {
      case 'casual':
        return 'bg-blue-500/10 text-blue-400'
      case 'sick':
        return 'bg-red-500/10 text-red-400'
      case 'earned':
        return 'bg-green-500/10 text-green-400'
      case 'maternity':
      case 'paternity':
        return 'bg-purple-500/10 text-purple-400'
      default:
        return 'bg-cyan-500/10 text-cyan-400'
    }
  }

  const getPolicyName = (policyId: string) => {
    const policy = policies.find((p) => p.id === policyId)
    return policy?.name || 'Unknown'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">
            Leave Management
          </h1>
          <p className="text-slate-400 mt-1">
            Apply for leave and track your requests
          </p>
        </div>
        <Dialog open={isApplyOpen} onOpenChange={setIsApplyOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Apply Leave
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-slate-800 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-white">Apply for Leave</DialogTitle>
              <DialogDescription>
                Submit a new leave request for approval
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleApplyLeave} className="space-y-4 mt-4">
              {formError && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">{formError}</span>
                </div>
              )}

              <div>
                <Label htmlFor="leaveType">Leave Type</Label>
                <select
                  id="leaveType"
                  value={selectedPolicy}
                  onChange={(e) => setSelectedPolicy(e.target.value)}
                  className="mt-1.5 w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white"
                >
                  <option value="">Select leave type</option>
                  {policies.map((policy) => (
                    <option key={policy.id} value={policy.id}>
                      {policy.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="startDate">Start Date</Label>
                  <Input
                    id="startDate"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="endDate">End Date</Label>
                  <Input
                    id="endDate"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate}
                    className="mt-1.5"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="reason">Reason</Label>
                <textarea
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Please provide a reason for your leave request..."
                  rows={3}
                  className="mt-1.5 w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 resize-none"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsApplyOpen(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Request'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Leave Balances */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          Leave Balances
        </h2>
        {balances.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="py-8">
              <div className="flex flex-col items-center justify-center text-slate-400">
                <CalendarDays className="w-12 h-12 mb-2" />
                <p>No leave balances found</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {balances.map((balance) => (
              <Card key={balance.id} className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">
                    {getPolicyName(balance.policy_id)}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-white">
                      {balance.available}
                    </span>
                    <span className="text-sm text-slate-500">
                      / {balance.opening_balance + balance.credited}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Used: {balance.used} | Pending: {balance.pending}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Leave Requests */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Leave Requests</CardTitle>
          <CardDescription>Your leave request history</CardDescription>
        </CardHeader>
        <CardContent>
          {requests.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <FileText className="w-16 h-16 mb-4" />
              <p className="text-lg font-medium">No leave requests</p>
              <p className="text-sm">
                Apply for leave to see your requests here
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-700/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                      Leave Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                      Duration
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                      Days
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                      Status
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-300 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {requests.map((request) => (
                    <tr key={request.id} className="hover:bg-slate-700/30">
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getLeaveTypeColor(policies.find((p) => p.id === request.policy_id)?.leave_type || '')}`}
                        >
                          {getPolicyName(request.policy_id)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-slate-500" />
                          <span>
                            {new Date(request.start_date).toLocaleDateString()}{' '}
                            - {new Date(request.end_date).toLocaleDateString()}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 text-slate-300">
                          <Clock className="w-4 h-4 text-slate-500" />
                          <span>{request.total_days} day(s)</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2.5 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}
                        >
                          {request.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {request.status === 'pending' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCancelRequest(request.id)}
                            className="text-red-400 hover:text-red-300"
                          >
                            Cancel
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
