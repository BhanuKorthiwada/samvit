import { createFileRoute } from '@tanstack/react-router';
import { Wallet, FileText, TrendingUp, Calendar } from 'lucide-react';

export const Route = createFileRoute('/_authenticated/payroll')({
  component: PayrollPage,
});

function PayrollPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Payroll</h1>
        <p className="text-slate-400 mt-1">View your salary details and payslips</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-green-500/10 rounded-lg">
              <Wallet className="w-5 h-5 text-green-400" />
            </div>
            <span className="text-slate-400 text-sm font-medium">Net Salary</span>
          </div>
          <p className="text-2xl font-bold text-white">₹ --,---</p>
          <p className="text-xs text-slate-500 mt-1">Last month</p>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
            </div>
            <span className="text-slate-400 text-sm font-medium">Gross Salary</span>
          </div>
          <p className="text-2xl font-bold text-white">₹ --,---</p>
          <p className="text-xs text-slate-500 mt-1">Monthly</p>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-red-500/10 rounded-lg">
              <FileText className="w-5 h-5 text-red-400" />
            </div>
            <span className="text-slate-400 text-sm font-medium">Deductions</span>
          </div>
          <p className="text-2xl font-bold text-white">₹ --,---</p>
          <p className="text-xs text-slate-500 mt-1">This month</p>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <Calendar className="w-5 h-5 text-purple-400" />
            </div>
            <span className="text-slate-400 text-sm font-medium">Pay Date</span>
          </div>
          <p className="text-2xl font-bold text-white">--</p>
          <p className="text-xs text-slate-500 mt-1">Next payment</p>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">Recent Payslips</h2>
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-slate-400">
          <FileText className="w-16 h-16 mb-4" />
          <p className="text-lg font-medium">No payslips available</p>
          <p className="text-sm">Your payslips will appear here once generated</p>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">Salary Structure</h2>
        </div>
        <div className="p-4">
          <div className="text-center text-slate-400 py-8">
            <p>Salary structure not configured</p>
            <p className="text-sm mt-1">Contact HR for more details</p>
          </div>
        </div>
      </div>
    </div>
  );
}
