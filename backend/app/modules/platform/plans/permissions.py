class PlanPermissions:
    VIEW = "platform.plans.view"
    CREATE = "platform.plans.create"
    UPDATE = "platform.plans.update"
    DELETE = "platform.plans.delete"
    RESTORE = "platform.plans.restore"

    ACTIVATE = "platform.plans.activate"
    DEACTIVATE = "platform.plans.deactivate"
    ARCHIVE = "platform.plans.archive"

    SET_DEFAULT = "platform.plans.set_default"
    MANAGE_PRICING = "platform.plans.manage_pricing"
    MANAGE_FEATURES = "platform.plans.manage_features"

    ALL = {
        VIEW,
        CREATE,
        UPDATE,
        DELETE,
        RESTORE,
        ACTIVATE,
        DEACTIVATE,
        ARCHIVE,
        SET_DEFAULT,
        MANAGE_PRICING,
        MANAGE_FEATURES,
    }