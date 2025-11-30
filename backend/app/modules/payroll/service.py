"""Payroll service."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessRuleViolationError, EntityNotFoundError
from app.modules.payroll.models import (
    EmployeeSalary,
    EmployeeSalaryComponent,
    PayrollPeriod,
    PayrollStatus,
    Payslip,
    PayslipItem,
    SalaryComponent,
    SalaryStructure,
)
from app.modules.payroll.schemas import (
    EmployeeSalaryCreate,
    PayrollPeriodCreate,
    SalaryComponentCreate,
    SalaryComponentUpdate,
    SalaryStructureCreate,
)


class PayrollService:
    """Service for payroll operations."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create_component(self, data: SalaryComponentCreate) -> SalaryComponent:
        """Create a salary component."""
        component = SalaryComponent(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            component_type=data.component_type.value,
            description=data.description,
            is_fixed=data.is_fixed,
            calculation_formula=data.calculation_formula,
            percentage_of=data.percentage_of,
            is_taxable=data.is_taxable,
            is_pf_applicable=data.is_pf_applicable,
            is_esi_applicable=data.is_esi_applicable,
        )
        self.session.add(component)
        await self.session.flush()
        await self.session.refresh(component)
        return component

    async def get_component(self, component_id: str) -> SalaryComponent:
        """Get salary component by ID."""
        result = await self.session.execute(
            select(SalaryComponent).where(
                SalaryComponent.id == component_id,
                SalaryComponent.tenant_id == self.tenant_id,
            )
        )
        component = result.scalar_one_or_none()
        if not component:
            raise EntityNotFoundError("SalaryComponent", component_id)
        return component

    async def list_components(self, active_only: bool = True) -> list[SalaryComponent]:
        """List all salary components."""
        query = select(SalaryComponent).where(
            SalaryComponent.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.where(SalaryComponent.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_component(
        self,
        component_id: str,
        data: SalaryComponentUpdate,
    ) -> SalaryComponent:
        """Update a salary component."""
        component = await self.get_component(component_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)
        await self.session.flush()
        await self.session.refresh(component)
        return component

    async def create_structure(self, data: SalaryStructureCreate) -> SalaryStructure:
        """Create a salary structure."""
        structure = SalaryStructure(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
        )
        self.session.add(structure)
        await self.session.flush()
        await self.session.refresh(structure)
        return structure

    async def get_structure(self, structure_id: str) -> SalaryStructure:
        """Get salary structure by ID."""
        result = await self.session.execute(
            select(SalaryStructure)
            .options(selectinload(SalaryStructure.components))
            .where(
                SalaryStructure.id == structure_id,
                SalaryStructure.tenant_id == self.tenant_id,
            )
        )
        structure = result.scalar_one_or_none()
        if not structure:
            raise EntityNotFoundError("SalaryStructure", structure_id)
        return structure

    async def list_structures(self, active_only: bool = True) -> list[SalaryStructure]:
        """List all salary structures."""
        query = select(SalaryStructure).where(
            SalaryStructure.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.where(SalaryStructure.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def assign_salary(self, data: EmployeeSalaryCreate) -> EmployeeSalary:
        """Assign salary structure to employee."""
        # Deactivate current salary
        await self._deactivate_current_salary(data.employee_id)

        monthly_gross = data.annual_ctc / 12

        employee_salary = EmployeeSalary(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            structure_id=data.structure_id,
            annual_ctc=data.annual_ctc,
            monthly_gross=monthly_gross,
            effective_from=data.effective_from,
            is_current=True,
        )
        self.session.add(employee_salary)
        await self.session.flush()

        # Add components
        for comp in data.components:
            salary_component = EmployeeSalaryComponent(
                tenant_id=self.tenant_id,
                employee_salary_id=employee_salary.id,
                component_id=comp.component_id,
                amount=comp.amount,
            )
            self.session.add(salary_component)

        await self.session.flush()
        await self.session.refresh(employee_salary)
        return employee_salary

    async def get_employee_salary(self, employee_id: str) -> EmployeeSalary | None:
        """Get current salary for an employee."""
        result = await self.session.execute(
            select(EmployeeSalary)
            .options(selectinload(EmployeeSalary.components))
            .where(
                EmployeeSalary.tenant_id == self.tenant_id,
                EmployeeSalary.employee_id == employee_id,
                EmployeeSalary.is_current.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_employee_salary_history(
        self,
        employee_id: str,
    ) -> list[EmployeeSalary]:
        """Get salary history for an employee."""
        result = await self.session.execute(
            select(EmployeeSalary)
            .where(
                EmployeeSalary.tenant_id == self.tenant_id,
                EmployeeSalary.employee_id == employee_id,
            )
            .order_by(EmployeeSalary.effective_from.desc())
        )
        return list(result.scalars().all())

    async def _deactivate_current_salary(self, employee_id: str) -> None:
        """Deactivate current salary for an employee."""
        result = await self.session.execute(
            select(EmployeeSalary).where(
                EmployeeSalary.tenant_id == self.tenant_id,
                EmployeeSalary.employee_id == employee_id,
                EmployeeSalary.is_current.is_(True),
            )
        )
        current = result.scalar_one_or_none()
        if current:
            current.is_current = False
            current.effective_to = date.today()

    async def create_period(self, data: PayrollPeriodCreate) -> PayrollPeriod:
        """Create a payroll period."""
        name = f"Payroll - {data.month:02d}/{data.year}"

        period = PayrollPeriod(
            tenant_id=self.tenant_id,
            name=name,
            month=data.month,
            year=data.year,
            start_date=data.start_date,
            end_date=data.end_date,
            payment_date=data.payment_date,
            status=PayrollStatus.DRAFT.value,
        )
        self.session.add(period)
        await self.session.flush()
        await self.session.refresh(period)
        return period

    async def get_period(self, period_id: str) -> PayrollPeriod:
        """Get payroll period by ID."""
        result = await self.session.execute(
            select(PayrollPeriod).where(
                PayrollPeriod.id == period_id,
                PayrollPeriod.tenant_id == self.tenant_id,
            )
        )
        period = result.scalar_one_or_none()
        if not period:
            raise EntityNotFoundError("PayrollPeriod", period_id)
        return period

    async def list_periods(self, year: int | None = None) -> list[PayrollPeriod]:
        """List payroll periods."""
        query = select(PayrollPeriod).where(PayrollPeriod.tenant_id == self.tenant_id)
        if year:
            query = query.where(PayrollPeriod.year == year)
        query = query.order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_payslips(self, period_id: str) -> list[Payslip]:
        """Generate payslips for a payroll period."""
        period = await self.get_period(period_id)

        if period.status != PayrollStatus.DRAFT.value:
            raise BusinessRuleViolationError(
                "invalid_status",
                "Can only generate payslips for draft periods",
            )

        # Get all active employee salaries
        result = await self.session.execute(
            select(EmployeeSalary)
            .options(selectinload(EmployeeSalary.components))
            .where(
                EmployeeSalary.tenant_id == self.tenant_id,
                EmployeeSalary.is_current.is_(True),
            )
        )
        employee_salaries = list(result.scalars().all())

        payslips = []
        for emp_salary in employee_salaries:
            payslip = await self._create_payslip(period, emp_salary)
            payslips.append(payslip)

        period.status = PayrollStatus.PROCESSING.value

        await self.session.flush()
        return payslips

    async def _create_payslip(
        self,
        period: PayrollPeriod,
        employee_salary: EmployeeSalary,
    ) -> Payslip:
        """Create a payslip for an employee."""
        # Calculate working days (simplified - would need actual calendar)
        working_days = 22  # Simplified

        # Create payslip
        payslip = Payslip(
            tenant_id=self.tenant_id,
            employee_id=employee_salary.employee_id,
            period_id=period.id,
            working_days=working_days,
            present_days=working_days,  # Simplified
            status=PayrollStatus.DRAFT.value,
        )
        self.session.add(payslip)
        await self.session.flush()

        # Add items from employee salary components
        gross = 0.0
        deductions = 0.0

        for emp_comp in employee_salary.components:
            component = await self.get_component(emp_comp.component_id)

            item = PayslipItem(
                tenant_id=self.tenant_id,
                payslip_id=payslip.id,
                component_id=emp_comp.component_id,
                amount=float(emp_comp.amount),
            )
            self.session.add(item)

            if component.component_type == "earning":
                gross += float(emp_comp.amount)
            elif component.component_type == "deduction":
                deductions += float(emp_comp.amount)

        payslip.gross_earnings = gross
        payslip.total_deductions = deductions
        payslip.net_pay = gross - deductions

        await self.session.refresh(payslip)
        return payslip

    async def get_payslip(self, payslip_id: str) -> Payslip:
        """Get payslip by ID."""
        result = await self.session.execute(
            select(Payslip)
            .options(selectinload(Payslip.items))
            .where(
                Payslip.id == payslip_id,
                Payslip.tenant_id == self.tenant_id,
            )
        )
        payslip = result.scalar_one_or_none()
        if not payslip:
            raise EntityNotFoundError("Payslip", payslip_id)
        return payslip

    async def get_employee_payslips(
        self,
        employee_id: str,
        year: int | None = None,
    ) -> list[Payslip]:
        """Get payslips for an employee."""
        query = (
            select(Payslip)
            .join(PayrollPeriod)
            .where(
                Payslip.tenant_id == self.tenant_id,
                Payslip.employee_id == employee_id,
            )
        )
        if year:
            query = query.where(PayrollPeriod.year == year)
        query = query.order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def approve_payroll(self, period_id: str) -> PayrollPeriod:
        """Approve payroll for a period."""
        period = await self.get_period(period_id)

        if period.status != PayrollStatus.PROCESSING.value:
            raise BusinessRuleViolationError(
                "invalid_status",
                "Only processing payrolls can be approved",
            )

        period.status = PayrollStatus.APPROVED.value

        # Update all payslips
        result = await self.session.execute(
            select(Payslip).where(
                Payslip.period_id == period_id,
                Payslip.tenant_id == self.tenant_id,
            )
        )
        payslips = result.scalars().all()
        for payslip in payslips:
            payslip.status = PayrollStatus.APPROVED.value

        await self.session.flush()
        await self.session.refresh(period)
        return period

    async def get_payroll_summary(self, period_id: str) -> dict:
        """Get payroll summary for a period."""
        period = await self.get_period(period_id)

        result = await self.session.execute(
            select(Payslip).where(
                Payslip.period_id == period_id,
                Payslip.tenant_id == self.tenant_id,
            )
        )
        payslips = list(result.scalars().all())

        return {
            "period_id": period.id,
            "month": period.month,
            "year": period.year,
            "total_employees": len(payslips),
            "total_gross": sum(float(p.gross_earnings) for p in payslips),
            "total_deductions": sum(float(p.total_deductions) for p in payslips),
            "total_net_pay": sum(float(p.net_pay) for p in payslips),
            "status": period.status,
        }
