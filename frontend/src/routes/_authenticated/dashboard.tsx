import { createFileRoute } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import {
  AlertCircle,
  Calendar,
  CheckCircle,
  Clock,
  TrendingUp,
  UserCheck,
  Users,
} from 'lucide-react';
import type { DailyAttendanceReport, EmployeeStats, LeaveRequestResponse } from '@/lib/api/types';
import { useAuth } from '@/contexts/AuthContext';
import { attendanceService, employeeService, leaveRequestService } from '@/lib/api';

export const Route = createFileRoute('/_authenticated/dashboard')({
  component: DashboardPage,
});

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'cyan' | 'green' | 'yellow' | 'red' | 'purple';
  subtitle?: string;
}

function StatCard({ title, value, icon: Icon, color, subtitle }: StatCardProps) {
  const colorClasses = {
    cyan: 'bg-cyan-500/10 text-cyan-400',
    green: 'bg-green-500/10 text-green-400',
    yellow: 'bg-yellow-500/10 text-yellow-400',
    red: 'bg-red-500/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400',
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
          {subtitle && <p className="text-slate-500 text-sm mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<EmployeeStats | null>(null);
  const [attendanceReport, setAttendanceReport] = useState<DailyAttendanceReport | null>(null);
  const [pendingLeaves, setPendingLeaves] = useState<Array<LeaveRequestResponse>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsData, attendanceData, leavesData] = await Promise.all([
          employeeService.getStats().catch(() => null),
          attendanceService.getDailyReport().catch(() => null),
          leaveRequestService.getPendingApprovals().catch(() => []),
        ]);

        setStats(statsData);
        setAttendanceReport(attendanceData);
        setPendingLeaves(leavesData);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">
            Welcome back, {user?.first_name}!
          </h1>
          <p className="text-slate-400 mt-1">{today}</p>
        </div>
        <div className="flex items-center gap-2 text-cyan-400">
          <Clock className="w-5 h-5" />
          <span className="font-medium">
            {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Employees"
          value={stats?.total ?? '-'}
          icon={Users}
          color="cyan"
          subtitle={`${stats?.active ?? 0} active`}
        />
        <StatCard
          title="Present Today"
          value={attendanceReport?.present ?? '-'}
          icon={UserCheck}
          color="green"
          subtitle={`${attendanceReport?.attendance_percentage.toFixed(1) ?? 0}% attendance`}
        />
        <StatCard
          title="On Leave"
          value={attendanceReport?.on_leave ?? stats?.on_leave ?? '-'}
          icon={Calendar}
          color="yellow"
        />
        <StatCard
          title="Late Today"
          value={attendanceReport?.late ?? '-'}
          icon={Clock}
          color="red"
        />
      </div>

      {/* Quick Actions and Pending Items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            <button className="p-4 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 rounded-lg transition-colors flex flex-col items-center gap-2">
              <Clock className="w-6 h-6" />
              <span className="text-sm font-medium">Clock In</span>
            </button>
            <button className="p-4 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg transition-colors flex flex-col items-center gap-2">
              <Calendar className="w-6 h-6" />
              <span className="text-sm font-medium">Apply Leave</span>
            </button>
            <button className="p-4 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 rounded-lg transition-colors flex flex-col items-center gap-2">
              <Users className="w-6 h-6" />
              <span className="text-sm font-medium">View Team</span>
            </button>
            <button className="p-4 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 rounded-lg transition-colors flex flex-col items-center gap-2">
              <TrendingUp className="w-6 h-6" />
              <span className="text-sm font-medium">View Reports</span>
            </button>
          </div>
        </div>

        {/* Pending Leave Approvals */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-4">Pending Approvals</h2>
          {pendingLeaves.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-slate-400">
              <CheckCircle className="w-12 h-12 mb-2" />
              <p>No pending approvals</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingLeaves.slice(0, 5).map((leave) => (
                <div
                  key={leave.id}
                  className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
                >
                  <div>
                    <p className="text-white font-medium">Leave Request</p>
                    <p className="text-sm text-slate-400">
                      {new Date(leave.start_date).toLocaleDateString()} -{' '}
                      {new Date(leave.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 text-xs font-medium rounded">
                    {leave.total_days} days
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Attendance Overview (if we have data by department) */}
      {stats?.by_department && Object.keys(stats.by_department).length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-4">Employees by Department</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(stats.by_department).map(([dept, count]) => (
              <div key={dept} className="text-center p-4 bg-slate-700/30 rounded-lg">
                <p className="text-2xl font-bold text-white">{count}</p>
                <p className="text-sm text-slate-400 mt-1">{dept}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
