class FeatureError(Exception):
    """Base feature module exception."""


class FeatureNotFoundError(FeatureError):
    def __init__(self, feature_identifier: int | str):
        super().__init__(
            f"Feature '{feature_identifier}' was not found."
        )


class FeatureCodeAlreadyExistsError(FeatureError):
    def __init__(self, code: str):
        super().__init__(
            f"Feature code '{code}' already exists."
        )


class FeatureInUseError(FeatureError):
    def __init__(self, code: str):
        super().__init__(
            f"Feature '{code}' is assigned to a plan or subscription "
            "and cannot be deleted."
        )


class InvalidFeatureValueError(FeatureError):
    def __init__(self, message: str):
        super().__init__(message)


class CoreFeatureModificationError(FeatureError):
    def __init__(self, code: str):
        super().__init__(
            f"Core feature '{code}' cannot be deleted."
        )