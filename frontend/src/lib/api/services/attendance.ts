/**
 * Attendance API Service
 */

import type {
  AttendanceRegularize,
  AttendanceResponse,
  ClockInRequest,
  ClockOutRequest,
  DailyAttendanceReport,
  ShiftCreate,
  ShiftResponse,
  ShiftUpdate,
  TimeEntryResponse,
} from '@/lib/api/types';
import apiClient from '@/lib/api/client';

export const shiftService = {
  /**
   * Create a new shift
   */
  async create(data: ShiftCreate): Promise<ShiftResponse> {
    return apiClient.post<ShiftResponse>('/attendance/shifts', data);
  },

  /**
   * List all shifts
   */
  async list(): Promise<Array<ShiftResponse>> {
    return apiClient.get<Array<ShiftResponse>>('/attendance/shifts');
  },

  /**
   * Get shift by ID
   */
  async get(id: string): Promise<ShiftResponse> {
    return apiClient.get<ShiftResponse>(`/attendance/shifts/${id}`);
  },

  /**
   * Update a shift
   */
  async update(id: string, data: ShiftUpdate): Promise<ShiftResponse> {
    return apiClient.patch<ShiftResponse>(`/attendance/shifts/${id}`, data);
  },
};

export const attendanceService = {
  /**
   * Clock in
   */
  async clockIn(data: ClockInRequest = {}): Promise<TimeEntryResponse> {
    return apiClient.post<TimeEntryResponse>('/attendance/clock-in', data);
  },

  /**
   * Clock out
   */
  async clockOut(data: ClockOutRequest = {}): Promise<TimeEntryResponse> {
    return apiClient.post<TimeEntryResponse>('/attendance/clock-out', data);
  },

  /**
   * Get current user's attendance for a date range
   */
  async getMyAttendance(startDate: string, endDate: string): Promise<Array<AttendanceResponse>> {
    return apiClient.get<Array<AttendanceResponse>>('/attendance/my-attendance', {
      start_date: startDate,
      end_date: endDate,
    });
  },

  /**
   * Get an employee's attendance for a date range
   */
  async getEmployeeAttendance(
    employeeId: string,
    startDate: string,
    endDate: string
  ): Promise<Array<AttendanceResponse>> {
    return apiClient.get<Array<AttendanceResponse>>(`/attendance/employee/${employeeId}`, {
      start_date: startDate,
      end_date: endDate,
    });
  },

  /**
   * Regularize attendance
   */
  async regularize(
    employeeId: string,
    date: string,
    data: AttendanceRegularize
  ): Promise<AttendanceResponse> {
    return apiClient.post<AttendanceResponse>(
      `/attendance/regularize/${employeeId}/${date}`,
      data
    );
  },

  /**
   * Get daily attendance report
   */
  async getDailyReport(date?: string): Promise<DailyAttendanceReport> {
    return apiClient.get<DailyAttendanceReport>('/attendance/report/daily', {
      report_date: date,
    });
  },
};
