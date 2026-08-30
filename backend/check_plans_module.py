import sys
import traceback


def check_import(
    module_name: str,
    objects: list[str] | None = None,
) -> bool:
    try:
        module = __import__(
            module_name,
            fromlist=objects or ["*"],
        )

        if objects:
            for object_name in objects:
                getattr(module, object_name)

        print(f"✅ {module_name}")
        return True

    except Exception:
        print(f"❌ {module_name}")
        traceback.print_exc()
        return False


checks = [
    (
        "app.modules.platform.plans.constants",
        [
            "PlanStatus",
            "PlanType",
            "BillingCycle",
            "PlanCurrency",
        ],
    ),
    (
        "app.modules.platform.plans.exceptions",
        None,
    ),
    (
        "app.modules.platform.plans.validators",
        None,
    ),
    (
        "app.modules.platform.plans.permissions",
        None,
    ),
    (
        "app.modules.platform.plans.models",
        [
            "Plan",
        ],
    ),
    (
        "app.modules.platform.plans.schemas",
        [
            "PlanBase",
            "PlanCreate",
            "PlanUpdate",
            "PlanResponse",
            "PlanListResponse",
        ],
    ),
    (
        "app.modules.platform.plans.repository",
        [
            "PlanRepository",
        ],
    ),
    (
        "app.modules.platform.plans.service",
        [
            "PlanService",
        ],
    ),
    (
        "app.modules.platform.plans.router",
        [
            "router",
        ],
    ),
]


results = [
    check_import(
        module_name=module_name,
        objects=objects,
    )
    for module_name, objects in checks
]


if all(results):
    print("\n✅ Plans module validation completed successfully.")
    sys.exit(0)

print("\n❌ Plans module contains errors.")
sys.exit(1)