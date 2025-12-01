/**
 * TypeScript types matching backend schemas
 */

// ============ Common Types ============

export interface PaginatedResponse<T> {
  items: Array<T>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SuccessResponse {
  success: boolean;
  message: string;
}

// ============ Auth Types ============

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  HR_MANAGER = 'hr_manager',
  HR_STAFF = 'hr_staff',
  MANAGER = 'manager',
  EMPLOYEE = 'employee',
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending',
  LOCKED = 'locked',
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface CompanyRegisterRequest {
  company_name: string;
  subdomain: string;
  company_email: string;
  company_phone?: string;
  admin_email: string;
  admin_password: string;
  admin_first_name: string;
  admin_last_name: string;
  timezone?: string;
  country?: string;
}

export interface CompanyRegisterResponse {
  tenant_id: string;
  tenant_domain: string;
  user_id: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface CurrentUserResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  tenant_id: string;
  roles: Array<string>;
  permissions: Array<string>;
}

export interface UserResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  avatar_url: string | null;
  status: UserStatus;
  is_active: boolean;
  email_verified: boolean;
  employee_id: string | null;
  roles: Array<string>;
}

export interface UserSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  status: UserStatus;
  is_active: boolean;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// ============ Employee Types ============

export enum EmploymentType {
  FULL_TIME = 'full_time',
  PART_TIME = 'part_time',
  CONTRACT = 'contract',
  INTERN = 'intern',
  FREELANCE = 'freelance',
}

export enum EmploymentStatus {
  ACTIVE = 'active',
  ON_NOTICE = 'on_notice',
  ON_LEAVE = 'on_leave',
  TERMINATED = 'terminated',
  RESIGNED = 'resigned',
}

export enum Gender {
  MALE = 'male',
  FEMALE = 'female',
  OTHER = 'other',
  PREFER_NOT_TO_SAY = 'prefer_not_to_say',
}

export enum MaritalStatus {
  SINGLE = 'single',
  MARRIED = 'married',
  DIVORCED = 'divorced',
  WIDOWED = 'widowed',
}

export interface DepartmentCreate {
  name: string;
  code: string;
  description?: string;
  parent_id?: string;
  head_id?: string;
}

export interface DepartmentUpdate {
  name?: string;
  code?: string;
  description?: string;
  parent_id?: string;
  head_id?: string;
  is_active?: boolean;
}

export interface DepartmentResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  code: string;
  description: string | null;
  parent_id: string | null;
  head_id: string | null;
  is_active: boolean;
}

export interface DepartmentSummary {
  id: string;
  name: string;
  code: string;
}

export interface PositionCreate {
  title: string;
  code: string;
  description?: string;
  level?: number;
  min_salary?: number;
  max_salary?: number;
  department_id?: string;
}

export interface PositionUpdate {
  title?: string;
  code?: string;
  description?: string;
  level?: number;
  min_salary?: number;
  max_salary?: number;
  department_id?: string;
  is_active?: boolean;
}

export interface PositionResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  title: string;
  code: string;
  description: string | null;
  level: number;
  min_salary: number | null;
  max_salary: number | null;
  department_id: string | null;
  is_active: boolean;
}

export interface PositionSummary {
  id: string;
  title: string;
  code: string;
  level: number;
}

export interface EmployeeCreate {
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  personal_email?: string;
  date_of_birth?: string;
  gender?: Gender;
  marital_status?: MaritalStatus;
  nationality?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  employment_type?: EmploymentType;
  date_of_joining: string;
  probation_end_date?: string;
  department_id?: string;
  position_id?: string;
  reporting_manager_id?: string;
  pan_number?: string;
  aadhaar_number?: string;
  bank_name?: string;
  bank_account_number?: string;
  ifsc_code?: string;
}

export interface EmployeeUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  personal_email?: string;
  date_of_birth?: string;
  gender?: Gender;
  marital_status?: MaritalStatus;
  nationality?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  employment_type?: EmploymentType;
  employment_status?: EmploymentStatus;
  date_of_leaving?: string;
  probation_end_date?: string;
  department_id?: string;
  position_id?: string;
  reporting_manager_id?: string;
  pan_number?: string;
  aadhaar_number?: string;
  passport_number?: string;
  bank_name?: string;
  bank_account_number?: string;
  ifsc_code?: string;
  avatar_url?: string;
  bio?: string;
}

export interface EmployeeResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  personal_email: string | null;
  date_of_birth: string | null;
  gender: string | null;
  marital_status: string | null;
  nationality: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string;
  postal_code: string | null;
  employment_type: EmploymentType;
  employment_status: EmploymentStatus;
  date_of_joining: string;
  date_of_leaving: string | null;
  probation_end_date: string | null;
  department_id: string | null;
  position_id: string | null;
  reporting_manager_id: string | null;
  avatar_url: string | null;
  bio: string | null;
  is_active: boolean;
}

export interface EmployeeSummary {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  department_id: string | null;
  position_id: string | null;
  employment_status: EmploymentStatus;
  is_active: boolean;
}

export interface EmployeeStats {
  total: number;
  active: number;
  on_leave: number;
  by_department: Record<string, number>;
  by_employment_type: Record<string, number>;
}

// ============ Attendance Types ============

export enum AttendanceStatus {
  PRESENT = 'present',
  ABSENT = 'absent',
  HALF_DAY = 'half_day',
  ON_LEAVE = 'on_leave',
  HOLIDAY = 'holiday',
  WEEKEND = 'weekend',
  LATE = 'late',
}

export enum ClockType {
  CLOCK_IN = 'clock_in',
  CLOCK_OUT = 'clock_out',
  BREAK_START = 'break_start',
  BREAK_END = 'break_end',
}

export interface ShiftCreate {
  name: string;
  code: string;
  start_time: string;
  end_time: string;
  break_duration_minutes?: number;
  grace_period_minutes?: number;
  is_night_shift?: boolean;
  is_default?: boolean;
}

export interface ShiftUpdate {
  name?: string;
  start_time?: string;
  end_time?: string;
  break_duration_minutes?: number;
  grace_period_minutes?: number;
  is_night_shift?: boolean;
  is_default?: boolean;
  is_active?: boolean;
}

export interface ShiftResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  code: string;
  start_time: string;
  end_time: string;
  break_duration_minutes: number;
  grace_period_minutes: number;
  is_night_shift: boolean;
  is_default: boolean;
  is_active: boolean;
}

export interface ClockInRequest {
  employee_id?: string;
  location?: string;
  notes?: string;
}

export interface ClockOutRequest {
  employee_id?: string;
  location?: string;
  notes?: string;
}

export interface TimeEntryResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  employee_id: string;
  entry_type: ClockType;
  timestamp: string;
  source: string;
  location: string | null;
  notes: string | null;
}

export interface AttendanceRegularize {
  clock_in?: string;
  clock_out?: string;
  reason: string;
}

export interface AttendanceResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  employee_id: string;
  date: string;
  shift_id: string | null;
  status: AttendanceStatus;
  clock_in: string | null;
  clock_out: string | null;
  work_hours: number | null;
  break_hours: number | null;
  overtime_hours: number | null;
  late_minutes: number;
  early_leave_minutes: number;
  is_late: boolean;
  is_early_leave: boolean;
  is_regularized: boolean;
  regularization_reason: string | null;
}

export interface DailyAttendanceReport {
  date: string;
  total_employees: number;
  present: number;
  absent: number;
  on_leave: number;
  late: number;
  attendance_percentage: number;
}

// ============ Leave Types ============

export enum LeaveType {
  CASUAL = 'casual',
  SICK = 'sick',
  EARNED = 'earned',
  MATERNITY = 'maternity',
  PATERNITY = 'paternity',
  BEREAVEMENT = 'bereavement',
  UNPAID = 'unpaid',
  COMPENSATORY = 'compensatory',
  WORK_FROM_HOME = 'work_from_home',
}

export enum LeaveStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled',
  WITHDRAWN = 'withdrawn',
}

export enum DayType {
  FULL = 'full',
  FIRST_HALF = 'first_half',
  SECOND_HALF = 'second_half',
}

export interface LeavePolicyCreate {
  name: string;
  leave_type: LeaveType;
  description?: string;
  annual_allocation?: number;
  max_accumulation?: number;
  carry_forward_limit?: number;
  min_days?: number;
  max_days?: number;
  advance_notice_days?: number;
  requires_attachment?: boolean;
  attachment_after_days?: number;
  applicable_gender?: string;
  min_tenure_months?: number;
  is_paid?: boolean;
}

export interface LeavePolicyUpdate {
  name?: string;
  description?: string;
  annual_allocation?: number;
  max_accumulation?: number;
  carry_forward_limit?: number;
  min_days?: number;
  max_days?: number;
  advance_notice_days?: number;
  requires_attachment?: boolean;
  is_active?: boolean;
}

export interface LeavePolicyResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  leave_type: LeaveType;
  description: string | null;
  annual_allocation: number;
  max_accumulation: number;
  carry_forward_limit: number;
  min_days: number;
  max_days: number | null;
  advance_notice_days: number;
  requires_attachment: boolean;
  attachment_after_days: number;
  applicable_gender: string | null;
  min_tenure_months: number;
  is_paid: boolean;
  is_active: boolean;
}

export interface LeaveBalanceResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  employee_id: string;
  policy_id: string;
  year: number;
  opening_balance: number;
  credited: number;
  used: number;
  pending: number;
  available: number;
}

export interface LeaveRequestCreate {
  policy_id: string;
  start_date: string;
  end_date: string;
  start_day_type?: DayType;
  end_day_type?: DayType;
  reason: string;
  attachment_url?: string;
}

export interface LeaveApproval {
  action: 'approve' | 'reject';
  remarks?: string;
}

export interface LeaveRequestResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  employee_id: string;
  policy_id: string;
  start_date: string;
  end_date: string;
  start_day_type: DayType;
  end_day_type: DayType;
  total_days: number;
  reason: string;
  status: LeaveStatus;
  attachment_url: string | null;
  approver_id: string | null;
  approved_at: string | null;
  approver_remarks: string | null;
}

export interface HolidayCreate {
  name: string;
  date: string;
  description?: string;
  is_optional?: boolean;
}

export interface HolidayResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  date: string;
  description: string | null;
  is_optional: boolean;
  is_active: boolean;
}

// ============ Payroll Types ============

export enum PayrollStatus {
  DRAFT = 'draft',
  PROCESSING = 'processing',
  APPROVED = 'approved',
  PAID = 'paid',
  CANCELLED = 'cancelled',
}

export enum ComponentType {
  EARNING = 'earning',
  DEDUCTION = 'deduction',
  REIMBURSEMENT = 'reimbursement',
}

export interface SalaryComponentCreate {
  name: string;
  code: string;
  component_type: ComponentType;
  description?: string;
  is_fixed?: boolean;
  calculation_formula?: string;
  percentage_of?: string;
  is_taxable?: boolean;
  is_pf_applicable?: boolean;
  is_esi_applicable?: boolean;
}

export interface SalaryComponentResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  code: string;
  component_type: ComponentType;
  description: string | null;
  is_fixed: boolean;
  calculation_formula: string | null;
  percentage_of: string | null;
  is_taxable: boolean;
  is_pf_applicable: boolean;
  is_esi_applicable: boolean;
  is_active: boolean;
  is_system: boolean;
}

export interface PayslipResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  employee_id: string;
  period_id: string;
  gross_earnings: number;
  total_deductions: number;
  net_pay: number;
  working_days: number;
  present_days: number;
  leave_days: number;
  lop_days: number;
  status: PayrollStatus;
  is_published: boolean;
}

export interface PayslipItemResponse {
  component_name: string;
  component_code: string;
  component_type: ComponentType;
  amount: number;
}

export interface PayslipDetail extends PayslipResponse {
  items: Array<PayslipItemResponse>;
}

// ============ Tenant Types ============

export enum SubscriptionPlan {
  FREE = 'free',
  STARTER = 'starter',
  PROFESSIONAL = 'professional',
  ENTERPRISE = 'enterprise',
}

export enum TenantStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
  CANCELLED = 'cancelled',
}

export interface TenantCreate {
  name: string;
  domain: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  timezone?: string;
  currency?: string;
}

export interface TenantResponse {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  domain: string;
  email: string;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string;
  postal_code: string | null;
  plan: SubscriptionPlan;
  status: TenantStatus;
  max_employees: number;
  max_users: number;
  timezone: string;
  currency: string;
  date_format: string;
  is_active: boolean;
  logo_url: string | null;
  primary_color: string;
}

export interface TenantPublicInfo {
  id: string;
  name: string;
  domain: string;
  logo_url: string | null;
  primary_color: string;
}

export interface TenantSummary {
  id: string;
  name: string;
  domain: string;
  plan: SubscriptionPlan;
  status: TenantStatus;
  is_active: boolean;
}

// ============ Password Reset Types ============

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

// ============ Signup Types ============

export interface CompanySignupRequest {
  // Company info
  company_name: string;
  domain: string;
  company_email: string;
  company_phone?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  // Admin user info
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

// ============ AI Assistant Types ============

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message: string;
  follow_up_questions?: Array<string>;
  data?: Record<string, unknown>;
  conversation_id?: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  capabilities: Array<string>;
}

export interface SuggestedPromptCategory {
  category: string;
  suggestions: Array<string>;
}

export interface SuggestedPromptsResponse {
  prompts: Array<SuggestedPromptCategory>;
}
