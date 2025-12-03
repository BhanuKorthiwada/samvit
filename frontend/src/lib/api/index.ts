/**
 * API Module Exports
 */

export { apiClient } from './client'
export * from './types'
export { authService } from '@/lib/api/services/auth'
export {
  departmentService,
  positionService,
  employeeService,
} from '@/lib/api/services/employees'
export { shiftService, attendanceService } from '@/lib/api/services/attendance'
export {
  leavePolicyService,
  leaveBalanceService,
  leaveRequestService,
  holidayService,
} from './services/leave'
export { tenantService, platformTenantService } from './services/tenant'
export { aiService } from './services/ai'
export { policyService, policyChatService } from './services/policies'
