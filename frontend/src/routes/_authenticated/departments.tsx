import { createFileRoute } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { Building2, Plus, Search, ChevronRight } from 'lucide-react';
import { departmentService } from '@/lib/api';
import type { DepartmentSummary } from '@/lib/api/types';

export const Route = createFileRoute('/_authenticated/departments')({
  component: DepartmentsPage,
});

function DepartmentsPage() {
  const [departments, setDepartments] = useState<DepartmentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const data = await departmentService.list(1, 100);
        setDepartments(data.items);
      } catch (err) {
        setError('Failed to load departments');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredDepartments = departments.filter(
    (dept) =>
      dept.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dept.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Departments</h1>
          <p className="text-slate-400 mt-1">{departments.length} departments</p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg transition-colors">
          <Plus className="w-5 h-5" />
          Add Department
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Search departments..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
        />
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      ) : filteredDepartments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400 bg-slate-800 rounded-xl border border-slate-700">
          <Building2 className="w-16 h-16 mb-4" />
          <p className="text-lg font-medium">No departments found</p>
          <p className="text-sm">Create a department to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDepartments.map((dept) => (
            <div
              key={dept.id}
              className="bg-slate-800 rounded-xl p-5 border border-slate-700 hover:border-slate-600 transition-colors group cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{dept.name}</h3>
                    <p className="text-sm text-slate-400 font-mono">{dept.code}</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
