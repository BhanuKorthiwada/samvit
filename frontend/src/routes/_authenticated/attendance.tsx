import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import {
  AlertCircle,
  Calendar,
  Clock,
  Play,
  Square,
  TrendingUp,
} from 'lucide-react'
import type { AttendanceResponse } from '@/lib/api/types'
import { attendanceService } from '@/lib/api'

export const Route = createFileRoute('/_authenticated/attendance')({
  component: AttendancePage,
})

function AttendancePage() {
  const [attendanceRecords, setAttendanceRecords] = useState<
    Array<AttendanceResponse>
  >([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isClockedIn, setIsClockedIn] = useState(false)
  const [clockInTime, setClockInTime] = useState<string | null>(null)
  const [isClocking, setIsClocking] = useState(false)

  const today = new Date()
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0)

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        const records = await attendanceService.getMyAttendance(
          startOfMonth.toISOString().split('T')[0],
          endOfMonth.toISOString().split('T')[0],
        )
        setAttendanceRecords(records)

        const todayRecord = records.find(
          (r) => r.date === today.toISOString().split('T')[0],
        )
        if (todayRecord?.clock_in && !todayRecord.clock_out) {
          setIsClockedIn(true)
          setClockInTime(todayRecord.clock_in)
        }
      } catch (err) {
        setError('Failed to load attendance data')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleClockIn = async () => {
    setIsClocking(true)
    try {
      const entry = await attendanceService.clockIn({})
      setIsClockedIn(true)
      setClockInTime(entry.timestamp)
      const records = await attendanceService.getMyAttendance(
        startOfMonth.toISOString().split('T')[0],
        endOfMonth.toISOString().split('T')[0],
      )
      setAttendanceRecords(records)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clock in')
    } finally {
      setIsClocking(false)
    }
  }

  const handleClockOut = async () => {
    setIsClocking(true)
    try {
      await attendanceService.clockOut({})
      setIsClockedIn(false)
      setClockInTime(null)
      const records = await attendanceService.getMyAttendance(
        startOfMonth.toISOString().split('T')[0],
        endOfMonth.toISOString().split('T')[0],
      )
      setAttendanceRecords(records)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clock out')
    } finally {
      setIsClocking(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present':
        return 'bg-green-500/10 text-green-400'
      case 'absent':
        return 'bg-red-500/10 text-red-400'
      case 'half_day':
        return 'bg-yellow-500/10 text-yellow-400'
      case 'on_leave':
        return 'bg-purple-500/10 text-purple-400'
      case 'late':
        return 'bg-orange-500/10 text-orange-400'
      default:
        return 'bg-slate-500/10 text-slate-400'
    }
  }

  const presentDays = attendanceRecords.filter(
    (r) => r.status === 'present',
  ).length
  const absentDays = attendanceRecords.filter(
    (r) => r.status === 'absent',
  ).length
  const lateDays = attendanceRecords.filter((r) => r.is_late).length
  const totalWorkHours = attendanceRecords.reduce(
    (sum, r) => sum + (r.work_hours || 0),
    0,
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">
          Attendance
        </h1>
        <p className="text-slate-400 mt-1">
          Track your work hours and attendance
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
          <button
            onClick={() => setError('')}
            className="ml-auto text-sm underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="flex-1 text-center sm:text-left">
            <p className="text-slate-400 text-sm font-medium">
              {today.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
            <p className="text-4xl font-bold text-white mt-2">
              {new Date().toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
            {isClockedIn && clockInTime && (
              <p className="text-sm text-cyan-400 mt-2">
                Clocked in at {new Date(clockInTime).toLocaleTimeString()}
              </p>
            )}
          </div>

          <button
            onClick={isClockedIn ? handleClockOut : handleClockIn}
            disabled={isClocking}
            className={`flex items-center gap-3 px-8 py-4 rounded-xl font-medium text-lg transition-all ${
              isClockedIn
                ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30'
                : 'bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30'
            } disabled:opacity-50`}
          >
            {isClocking ? (
              <div className="w-6 h-6 border-2 border-current/20 border-t-current rounded-full animate-spin" />
            ) : isClockedIn ? (
              <Square className="w-6 h-6" />
            ) : (
              <Play className="w-6 h-6" />
            )}
            {isClocking
              ? 'Processing...'
              : isClockedIn
                ? 'Clock Out'
                : 'Clock In'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/10 rounded-lg">
              <Clock className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{presentDays}</p>
              <p className="text-sm text-slate-400">Present Days</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/10 rounded-lg">
              <Calendar className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{absentDays}</p>
              <p className="text-sm text-slate-400">Absent Days</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/10 rounded-lg">
              <AlertCircle className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{lateDays}</p>
              <p className="text-sm text-slate-400">Late Days</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {totalWorkHours.toFixed(1)}
              </p>
              <p className="text-sm text-slate-400">Work Hours</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">
            This Month&apos;s Attendance
          </h2>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
          </div>
        ) : attendanceRecords.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <Clock className="w-16 h-16 mb-4" />
            <p className="text-lg font-medium">No attendance records</p>
            <p className="text-sm">
              Clock in to start recording your attendance
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                    Clock In
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                    Clock Out
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase">
                    Work Hours
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {attendanceRecords
                  .sort(
                    (a, b) =>
                      new Date(b.date).getTime() - new Date(a.date).getTime(),
                  )
                  .map((record) => (
                    <tr key={record.id} className="hover:bg-slate-700/30">
                      <td className="px-6 py-4 text-white">
                        {new Date(record.date).toLocaleDateString('en-US', {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 text-xs font-medium rounded-full ${getStatusColor(record.status)}`}
                        >
                          {record.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {record.clock_in
                          ? new Date(record.clock_in).toLocaleTimeString(
                              'en-US',
                              { hour: '2-digit', minute: '2-digit' },
                            )
                          : '-'}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {record.clock_out
                          ? new Date(record.clock_out).toLocaleTimeString(
                              'en-US',
                              { hour: '2-digit', minute: '2-digit' },
                            )
                          : '-'}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {record.work_hours
                          ? `${record.work_hours.toFixed(1)} hrs`
                          : '-'}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
