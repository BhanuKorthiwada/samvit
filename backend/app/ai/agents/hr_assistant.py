"""HR Assistant Agent implementation."""

from app.ai.agents.base import AgentContext, AgentResponse
from app.ai.agents.tools import AgentTools

# System prompt for HR Assistant
HR_ASSISTANT_SYSTEM_PROMPT = """You are a helpful HR Assistant for an HRMS (Human Resource Management System).
You help employees with:
- Leave management (checking balance, applying for leave)
- Attendance queries
- Payslip information
- Holiday calendar
- Team availability

Be professional, friendly, and concise. If you need to perform an action, use the available tools.
When displaying monetary values, use Indian Rupee format (₹).
Always respect data privacy - employees can only access their own information unless they are managers.

Available actions you can help with:
1. Check leave balance
2. Apply for leave
3. View attendance summary
4. Get payslip details
5. View upcoming holidays
6. Check who is on leave in the team
"""


class HRAssistantAgent:
    """HR Assistant conversational agent."""

    def __init__(self, context: AgentContext):
        self.context = context
        self.tools = AgentTools(
            session=context.session,
            tenant_id=context.tenant_id,
            employee_id=context.employee_id or context.user_id,
        )

    async def process_message(self, user_message: str) -> AgentResponse:
        """
        Process a user message and return a response.

        This is a simplified implementation. In production, this would:
        1. Use an LLM (via LangGraph, Pydantic AI, or Google ADK)
        2. Handle multi-turn conversations
        3. Make intelligent tool selections
        4. Generate natural language responses
        """
        message_lower = user_message.lower()

        # Simple intent detection (would use LLM in production)
        if any(
            word in message_lower
            for word in ["leave balance", "leave left", "remaining leave"]
        ):
            return await self._handle_leave_balance()

        elif any(
            word in message_lower
            for word in ["apply leave", "take leave", "request leave"]
        ):
            return await self._handle_leave_application_prompt()

        elif any(word in message_lower for word in ["attendance", "present", "absent"]):
            return await self._handle_attendance_summary()

        elif any(word in message_lower for word in ["payslip", "salary", "pay"]):
            return await self._handle_payslip()

        elif any(word in message_lower for word in ["holiday", "holidays", "off days"]):
            return await self._handle_holidays()

        elif any(
            word in message_lower
            for word in ["who is on leave", "team leave", "on leave today"]
        ):
            return await self._handle_team_leave()

        else:
            return AgentResponse(
                message=self._get_help_message(),
                follow_up_questions=[
                    "What's my leave balance?",
                    "Show my attendance for this month",
                    "What are the upcoming holidays?",
                ],
            )

    async def _handle_leave_balance(self) -> AgentResponse:
        """Handle leave balance query."""
        result = await self.tools.get_leave_balance()

        if not result.get("balances"):
            return AgentResponse(
                message="I couldn't find any leave balance information for you. Please contact HR if this seems incorrect.",
            )

        balances = result["balances"]
        message_parts = ["Here's your current leave balance:\n"]

        for balance in balances:
            message_parts.append(
                f"• **{balance['leave_type']}**: {balance['available']:.1f} days available "
                f"({balance['used']:.1f} used, {balance['pending']:.1f} pending)"
            )

        return AgentResponse(
            message="\n".join(message_parts),
            data=result,
            follow_up_questions=[
                "I want to apply for leave",
                "What are the upcoming holidays?",
            ],
        )

    async def _handle_leave_application_prompt(self) -> AgentResponse:
        """Prompt user for leave details."""
        return AgentResponse(
            message=(
                "I can help you apply for leave. Please provide the following details:\n\n"
                "1. **Type of leave** (Casual, Sick, Earned, etc.)\n"
                "2. **Start date** (e.g., 2025-01-15)\n"
                "3. **End date** (e.g., 2025-01-17)\n"
                "4. **Reason** (optional)\n\n"
                "You can say something like: 'Apply for sick leave from 2025-01-15 to 2025-01-16 for medical appointment'"
            ),
            follow_up_questions=[
                "What's my leave balance first?",
                "Show me upcoming holidays",
            ],
        )

    async def _handle_attendance_summary(self) -> AgentResponse:
        """Handle attendance summary query."""
        result = await self.tools.get_attendance_summary()

        message = (
            f"Here's your attendance summary for {result['month']}/{result['year']}:\n\n"
            f"• **Present**: {result['present_days']} days\n"
            f"• **Absent**: {result['absent_days']} days\n"
            f"• **On Leave**: {result['leave_days']} days\n"
            f"• **Half Days**: {result['half_days']} days"
        )

        return AgentResponse(
            message=message,
            data=result,
            follow_up_questions=[
                "What's my leave balance?",
                "Get my payslip for this month",
            ],
        )

    async def _handle_payslip(self) -> AgentResponse:
        """Handle payslip query."""
        result = await self.tools.get_payslip()

        if result.get("status") == "not_found":
            return AgentResponse(
                message=result["message"],
                follow_up_questions=[
                    "Check previous month's payslip",
                    "What's my leave balance?",
                ],
            )

        message = (
            f"Here's your payslip for {result['month']}/{result['year']}:\n\n"
            f"• **Gross Earnings**: ₹{result['gross_earnings']:,.2f}\n"
            f"• **Total Deductions**: ₹{result['total_deductions']:,.2f}\n"
            f"• **Net Pay**: ₹{result['net_pay']:,.2f}\n\n"
            f"Status: {result['status'].title()}"
        )

        return AgentResponse(
            message=message,
            data=result,
            follow_up_questions=[
                "Show my attendance summary",
                "What's my leave balance?",
            ],
        )

    async def _handle_holidays(self) -> AgentResponse:
        """Handle holidays query."""
        result = await self.tools.get_upcoming_holidays()

        if not result.get("holidays"):
            return AgentResponse(
                message="There are no upcoming holidays in the calendar. Contact HR if you believe this is incorrect.",
            )

        message_parts = ["Here are the upcoming holidays:\n"]

        for holiday in result["holidays"]:
            optional_tag = " *(Optional)*" if holiday["is_optional"] else ""
            message_parts.append(
                f"• **{holiday['name']}** - {holiday['date']}{optional_tag}"
            )

        return AgentResponse(
            message="\n".join(message_parts),
            data=result,
            follow_up_questions=[
                "I want to apply for leave",
                "What's my leave balance?",
            ],
        )

    async def _handle_team_leave(self) -> AgentResponse:
        """Handle team leave query."""
        result = await self.tools.get_team_on_leave()

        if result["count"] == 0:
            message = f"No team members are on leave on {result['date']}."
        else:
            message = (
                f"{result['count']} team member(s) are on leave on {result['date']}."
            )

        return AgentResponse(
            message=message,
            data=result,
            follow_up_questions=[
                "What's my leave balance?",
                "Show upcoming holidays",
            ],
        )

    def _get_help_message(self) -> str:
        """Get help message."""
        return (
            "Hi! I'm your HR Assistant. I can help you with:\n\n"
            "📅 **Leave Management**\n"
            "   - Check your leave balance\n"
            "   - Apply for leave\n\n"
            "⏰ **Attendance**\n"
            "   - View your attendance summary\n\n"
            "💰 **Payroll**\n"
            "   - Get your payslip details\n\n"
            "🎉 **Holidays**\n"
            "   - View upcoming holidays\n"
            "   - Check who's on leave\n\n"
            "Just ask me anything related to these topics!"
        )


async def create_hr_assistant(context: AgentContext) -> HRAssistantAgent:
    """Factory function to create HR Assistant agent."""
    return HRAssistantAgent(context)
