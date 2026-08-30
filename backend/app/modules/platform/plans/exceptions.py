class PlanError(Exception):
    """Base exception for Plan domain errors."""


class PlanNotFoundError(PlanError):
    def __init__(self, identifier: object) -> None:
        super().__init__(
            f"Plan with identifier {identifier!r} was not found."
        )


class PlanCodeAlreadyExistsError(PlanError):
    def __init__(self, code: str) -> None:
        super().__init__(
            f"Plan code {code!r} already exists."
        )


class DefaultPlanAlreadyExistsError(PlanError):
    def __init__(self) -> None:
        super().__init__(
            "A default plan already exists."
        )


class PlanInUseError(PlanError):
    def __init__(self, plan_id: int) -> None:
        super().__init__(
            f"Plan {plan_id!r} cannot be deleted because it is in use."
        )


class InvalidPlanPriceError(PlanError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidPlanStatusTransitionError(PlanError):
    def __init__(
        self,
        current_status: str,
        target_status: str,
    ) -> None:
        super().__init__(
            "Invalid plan status transition "
            f"from {current_status!r} to {target_status!r}."
        )


class FreePlanPriceError(PlanError):
    def __init__(self) -> None:
        super().__init__(
            "A free plan cannot have monthly or yearly prices greater than zero."
        )


class PlanValidationError(PlanError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class DefaultPlanDeletionError(PlanError):
    def __init__(self) -> None:
        super().__init__(
            "The default plan cannot be deleted."
        )


class ArchivedPlanModificationError(PlanError):
    def __init__(self) -> None:
        super().__init__(
            "An archived plan cannot be modified."
        )