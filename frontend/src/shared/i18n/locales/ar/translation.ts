const arTranslation = {
  navigation: {
    "dashboard": "لوحة التحكم",
    "module-catalog": "كتالوج الموديولات",
    "helpdesk": "الدعم الفني بالذكاء الاصطناعي",
    "identity": "المستخدمون والصلاحيات",
    "users": "المستخدمون",
    "roles": "الأدوار",
    "permissions": "الصلاحيات",
    "organization": "إدارة المؤسسة",
    "companies": "الشركات",
    "branches": "الفروع",
    "accounting": "الحسابات العامة",
    "chart-of-accounts": "دليل الحسابات",
    "fiscal-years": "السنوات المالية",
    "journals": "دفاتر اليومية",
    "journal-entries": "القيود اليومية",
    "cost-centers": "مراكز التكلفة",
    "financial-reports": "التقارير المالية",
    "treasury": "الخزينة والبنوك",
    "banks": "البنوك",
    "cash": "الخزن النقدية",
    "checks": "الشيكات",
    "sales": "المبيعات",
    "customers": "العملاء",
    "sales-orders": "أوامر البيع",
    "sales-invoices": "فواتير المبيعات",
    "purchasing": "المشتريات",
    "suppliers": "الموردون",
    "purchase-orders": "أوامر الشراء",
    "purchase-invoices": "فواتير المشتريات",
    "inventory": "المخزون",
    "warehouses": "المخازن",
    "locations": "مواقع التخزين",
    "products": "الأصناف",
    "stock-transactions": "حركات المخزون",
    "transfers": "تحويلات المخزون",
    "reservations": "حجوزات المخزون",
    "commercial-leasing": "الإيجارات التجارية",
    "lease-contracts": "عقود الإيجار",
    "installments": "الاستحقاقات",
    "revenue-share": "نسب الإيرادات",
    "hospitality": "إدارة الفنادق",
    "hotels": "الفنادق",
    "hotel-revenue": "إيرادات الفنادق",
    "hotel-profit-share": "نسب الأرباح",
    "shipping": "الشحن",
    "shipping-status-settings": "إعدادات حالات الشحن",
    "shipping-pricing": "تسعير شركات الشحن",
    "shipping-settlements": "تسويات شركات الشحن",
    "saas": "إدارة منصة SaaS",
    "saas-dashboard": "نظرة عامة",
    "plans": "الباقات والاستحقاقات",
    "reports": "التقارير",
    "notifications": "الرسائل والإشعارات",
    "settings": "الإعدادات",
    "company-policies": "سياسات الشركة"
  },

  common: {
    loading: "جاري التحميل...",
    processing: "جارٍ التنفيذ...",
    close: "إغلاق",
    refresh: "تحديث",
    cancel: "إلغاء",
    appName: "برايم ERP",
    appDescription: "منصة إدارة الأعمال",

    save: "حفظ",
    submit: "إرسال",

    english: "English",
    arabic: "العربية",

    copyright:
      "جميع الحقوق محفوظة.",

    secured:
      "النظام محمي باستخدام تسجيل دخول آمن واتصال مشفر.",
    new: "جديد",
    closeNavigation: "إغلاق القائمة",
    workspace: "مساحة العمل",
    online: "متصل",
    searchNavigation: "ابحث في القائمة",
    searchScreens: "ابحث عن شاشة أو موديول...",
    clearSearch: "مسح البحث",
    mainNavigation: "القائمة الرئيسية",
    searchResults: "نتائج البحث",
    businessManagement: "إدارة الأعمال",
    noMatchingResults: "لا توجد نتائج مطابقة.",
    platformAdministrator: "مسؤول المنصة",
    secureWorkspace: "مساحة مؤسسية آمنة",
    organizationAccess: "صلاحيات وعزل بيانات حسب المؤسسة",
    integratedBusinessManagement: "منصة إدارة الأعمال المتكاملة",
    connectedBusinessOperations: "متابعة مترابطة للأعمال والعمليات",
    systemUser: "مستخدم النظام",
    user: "مستخدم",
  },

  userForm: {
    titleCreate: "إضافة مستخدم جديد",
    titleEdit: "تعديل المستخدم",
    descriptionCreate: "أدخل بيانات المستخدم وحدد الدور والصلاحيات.",
    descriptionEdit: "عدّل بيانات المستخدم ثم اضغط حفظ التعديلات.",
    fullName: "الاسم بالكامل",
    fullNamePlaceholder: "أدخل الاسم بالكامل",
    username: "اسم المستخدم",
    email: "البريد الإلكتروني",
    phone: "رقم الهاتف",
    password: "كلمة المرور",
    newPassword: "كلمة مرور جديدة",
    confirmPassword: "تأكيد كلمة المرور",
    confirmNewPassword: "تأكيد كلمة المرور الجديدة",
    passwordPlaceholderEdit: "اتركها فارغة دون تغيير",
    passwordPlaceholderCreate: "8 أحرف على الأقل",
    confirmPasswordPlaceholder: "أعد إدخال كلمة المرور",
    passwordHint: "يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
    role: "الدور والصلاحيات",
    loadingRoles: "جاري تحميل الأدوار...",
    chooseRole: "اختر الدور",
    noRole: "بدون دور",
    noRoles: "لا توجد أدوار متاحة حاليًا.",
    address: "العنوان",
    addressPlaceholder: "أدخل عنوان المستخدم",
    saveChanges: "حفظ التعديلات",
    create: "إضافة المستخدم",
    cancel: "إلغاء",
    errors: {
      fullName: "برجاء إدخال الاسم بالكامل.",
      username: "برجاء إدخال اسم المستخدم.",
      usernameLength: "يجب أن يتكون اسم المستخدم من 3 أحرف على الأقل.",
      email: "برجاء إدخال البريد الإلكتروني.",
      password: "برجاء إدخال كلمة المرور.",
      passwordLength: "يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
      passwordMax: "يجب ألا تزيد كلمة المرور عن 128 حرفًا.",
      passwordMismatch: "كلمتا المرور غير متطابقتين."
    }
  },

  inventory: {
    home: {
      title: "المخزون والمستودعات",
      description: "إدارة مخازن الشركة والفروع ومواقع التخزين من خلال مساحة موحدة.",
      warehouses: "المخازن",
      warehousesDescription: "إدارة المخازن المركزية ومخازن الفروع.",
      locations: "مواقع التخزين",
      locationsDescription: "إدارة مواقع الاستلام والتخزين والشحن داخل كل مخزن.",
      items: "الأصناف والمخزون",
      itemsDescription: "دليل الأصناف والأرصدة والتكلفة."
    }
  },

  sales: {
    title: "المبيعات",
    description: "إنشاء مستندات البيع واعتمادها وترحيل المخزون والتحصيل ضمن دورة البيع.",
    customer: "العميل",
    autoNumber: "يتم إنشاء رقم المستند تلقائيًا وفق إعدادات الشركة.",
    sourceOrderOptional: "أمر بيع (اختياري حسب السياسة)",
    sourceOrderLine: "بند أمر البيع",
    itemQuantity: "الصنف {{item}} · الكمية {{quantity}}",
    warehouse: "مخزن الصرف / التسليم",
    price: "السعر",
    quantity: "الكمية",
    itemId: "رقم الصنف",
    loadingCompanyDate: "جارٍ جلب تاريخ الشركة...",
    createDocument: "إنشاء مستند",
    types: {
      quotation: "عرض سعر",
      order: "طلب بيع",
      delivery: "إذن تسليم",
      invoice: "فاتورة"
    },
    statuses: {
      draft: "مسودة",
      pending_approval: "بانتظار الاعتماد",
      approved: "معتمد",
      confirmed: "مؤكد",
      partially_fulfilled: "تم التنفيذ جزئيًا",
      fulfilled: "تم التنفيذ",
      posted: "مُرحّل",
      cancelled: "ملغي",
      rejected: "مرفوض"
    },
    columns: {
      number: "رقم",
      date: "التاريخ",
      type: "النوع",
      status: "الحالة",
      total: "الإجمالي",
      actions: "الإجراءات"
    },
    actions: {
      confirm: "تأكيد",
      cancelRelease: "إلغاء الطلب وتحرير الحجز",
      approve: "موافقة",
      reject: "رفض",
      postInventory: "ترحيل المخزون",
      collectFull: "تحصيل كامل",
      details: "تفاصيل"
    },
    confirmCancelOrder: "سيتم إلغاء أمر البيع وتحرير الكميات المحجوزة. هل تريد المتابعة؟",
    documentNumber: "المستند رقم {{number}}",
    detailsSummary: "العميل: {{customer}} — الإجمالي: {{total}} — المدفوع: {{paid}}"
  },

  roles: {
    notifications: {
      created: "تم إنشاء الدور بنجاح.",
      updated: "تم تعديل الدور بنجاح.",
      permissionsUpdated: "تم تحديث صلاحيات الدور بنجاح.",
      deactivated: "تم تعطيل الدور.",
      activated: "تم تفعيل الدور.",
      deleteAssigned: "لا يمكن حذف دور مرتبط بمستخدمين.",
      deleted: "تم حذف الدور بنجاح."
    },
    title: "الأدوار والصلاحيات",
    description: "إنشاء الأدوار وتحديد ما يمكن لكل مستخدم عرضه أو تنفيذه داخل PrimeERP.",
    newRole: "دور جديد",
    total: "إجمالي الأدوار",
    active: "الأدوار النشطة",
    assignedUsers: "المستخدمون المرتبطون",
    searchPlaceholder: "البحث باسم الدور أو الوصف...",
    confirmDelete: "هل تريد حذف الدور \"{{name}}\"؟",
    errors: {
      deleteAssigned: "لا يمكن حذف الدور لأنه مرتبط بـ {{count}} مستخدم."
    }
  },
  rolesTable: {
    active: "نشط",
    inactive: "معطل",
    loading: "جاري تحميل الأدوار...",
    emptyTitle: "لا توجد أدوار",
    emptyDescription: "ابدأ بإنشاء أول دور وتحديد صلاحياته.",
    role: "الدور",
    permissions: "الصلاحيات",
    users: "المستخدمون",
    status: "الحالة",
    enabled: "تفعيل الدور",
    actions: "الإجراءات",
    noDescription: "لا يوجد وصف",
    permissionCount: "{{count}}",
    permissionCount_one: "{{count}} صلاحية",
    permissionCount_other: "{{count}} صلاحيات",
    edit: "تعديل الدور",
    delete: "حذف الدور"
  },

  roleForm: {
    titleCreate: "إضافة دور جديد",
    titleEdit: "تعديل الدور",
    description: "حدد اسم الدور والصلاحيات التي سيتم منحها للمستخدمين المرتبطين به.",
    name: "اسم الدور",
    namePlaceholder: "مثال: مدير الفرع",
    active: "الدور نشط",
    descriptionLabel: "الوصف",
    descriptionPlaceholder: "وصف مختصر لمسؤوليات هذا الدور",
    permissions: "صلاحيات الدور",
    selectedCount: "تم اختيار {{selected}} من {{total}} صلاحية",
    selectAll: "تحديد أو إلغاء الكل",
    searchPermissions: "البحث في الصلاحيات...",
    loadingPermissions: "جاري تحميل الصلاحيات...",
    noPermissions: "لا توجد صلاحيات متاحة.",
    permissionCount_one: "{{count}} صلاحية",
    permissionCount_other: "{{count}} صلاحيات",
    selectSection: "تحديد القسم بالكامل",
    unselectSection: "إلغاء تحديد القسم",
    save: "حفظ التعديلات",
    create: "إنشاء الدور",
    cancel: "إلغاء",
    resources: {
      users: "المستخدمون", roles: "الأدوار", permissions: "الصلاحيات",
      companies: "الشركات", branches: "الفروع", sales: "المبيعات",
      customers: "العملاء", suppliers: "الموردون", products: "المنتجات",
      inventory: "المخزون", purchasing: "المشتريات", accounting: "الحسابات",
      restaurant: "المطاعم", pos: "نقاط البيع", hr: "الموارد البشرية",
      reports: "التقارير", shipping: "شركات الشحن", settings: "الإعدادات",
      other: "أخرى"
    },
    actions: {
      view: "عرض", read: "عرض", create: "إضافة", update: "تعديل",
      delete: "حذف", approve: "اعتماد", manage: "إدارة كاملة",
      print: "طباعة", export: "تصدير", cancel: "إلغاء"
    }
  },

  permissions: {
    title: "الصلاحيات",
    description: "عرض وإدارة صلاحيات النظام وربطها بالأدوار.",
    catalog: "دليل الصلاحيات",
    refresh: "تحديث",
    loading: "جاري التحميل...",
    processing: "جارٍ التنفيذ...",
    name: "الاسم",
    resource: "المورد",
    action: "الإجراء",
    descriptionColumn: "الوصف",
    status: "الحالة",
    actions: "إجراء",
    active: "نشطة",
    inactive: "متوقفة",
    activate: "تفعيل",
    deactivate: "تعطيل",
    empty: "لا توجد صلاحيات.",
    errors: {
      load: "تعذر تحميل الصلاحيات.",
      update: "تعذر تحديث الصلاحية."
    }
  },

  usersTable: {
    "loading": "جاري تحميل المستخدمين...",
    "active": "نشط",
    "inactive": "معطل",
    "emptyTitle": "لا يوجد مستخدمون",
    "emptyDescription": "لا توجد نتائج مطابقة للبحث أو عوامل التصفية الحالية.",
    "user": "المستخدم",
    "email": "البريد الإلكتروني",
    "role": "الدور",
    "status": "الحالة",
    "lastLogin": "آخر تسجيل دخول",
    "accountEnabled": "تفعيل الحساب",
    "actions": "الإجراءات",
    "superuser": "مستخدم بصلاحيات مدير",
    "platformAdmin": "مدير المنصة",
    "noRole": "بدون دور",
    "deactivateUser": "تعطيل المستخدم",
    "activateUser": "تفعيل المستخدم",
    "editUser": "تعديل المستخدم",
    "resetPassword": "إعادة تعيين كلمة المرور",
    "deleteUser": "حذف المستخدم",
    "unavailable": "غير متاح",
    "neverLoggedIn": "لم يسجل الدخول"
  },

  users: {
    notifications: {
      created: "تمت إضافة المستخدم بنجاح.",
      updated: "تم تعديل بيانات المستخدم.",
      deactivated: "تم تعطيل المستخدم.",
      activated: "تم تفعيل المستخدم.",
      deleted: "تم حذف المستخدم بنجاح."
    },
    resetPassword: {
      title: "إعادة تعيين كلمة المرور",
      userLabel: "المستخدم",
      newPassword: "كلمة المرور الجديدة",
      confirmPassword: "تأكيد كلمة المرور",
      forceChange: "إجبار المستخدم على تغييرها",
      save: "حفظ كلمة المرور",
      success: "تمت إعادة تعيين كلمة المرور.",
      errors: {
        passwordLength: "كلمة المرور يجب ألا تقل عن 6 أحرف.",
        passwordMismatch: "كلمتا المرور غير متطابقتين.",
        failed: "تعذر إعادة تعيين كلمة المرور."
      }
    },
    "title": "إدارة المستخدمين",
    "description": "إضافة المستخدمين وتعديل بياناتهم والتحكم في حالتهم وأدوارهم.",
    "newUser": "مستخدم جديد",
    "totalUsers": "إجمالي المستخدمين",
    "activeUsers": "المستخدمون النشطون",
    "searchPlaceholder": "البحث بالاسم أو اسم المستخدم أو البريد...",
    "confirmDelete": "هل تريد حذف المستخدم \"{{name}}\"؟"
  },

  settingsCenter: {
    "controlCenter": "مركز التحكم",
    "title": "إعدادات النظام",
    "description": "اختر الموديول من القائمة الجانبية لعرض جميع إعداداته. تظل قائمة موديول واحد فقط مفتوحة في كل مرة.",
    "moduleSettings": "إعدادات الموديولات",
    "selectModule": "اختر موديولًا لعرض خياراته",
    "settingsModules": "قائمة موديولات الإعدادات",
    "sectionSettings": "إعدادات {{title}}",
    "footer": "PrimeERP · مركز الإعدادات",
    "sections": {
      "General": {
        "title": "الإعدادات العامة",
        "description": "بيانات الشركة واللغة والتاريخ والمنطقة الزمنية والعملة."
      },
      "Accounting": {
        "title": "المحاسبة",
        "description": "الفترات المالية والحسابات وسياسات الترحيل."
      },
      "Taxes": {
        "title": "الضرائب والفاتورة الإلكترونية",
        "description": "الضرائب والإقرارات والفوترة الإلكترونية."
      },
      "Sales": {
        "title": "المبيعات والعملاء",
        "description": "التسعير والخصومات والائتمان والمبيعات."
      },
      "Purchasing": {
        "title": "المشتريات والموردون",
        "description": "المشتريات والاعتمادات وسياسات الموردين."
      },
      "Inventory": {
        "title": "المخزون والمستودعات",
        "description": "التقييم والحجز والجرد وإعادة الطلب."
      },
      "Human Resources": {
        "title": "الموارد البشرية والحضور والرواتب",
        "description": "البصمة والحضور والإجازات والرواتب والاعتماد."
      },
      "Approvals": {
        "title": "الموافقات وسير العمل",
        "description": "مسارات الاعتماد والتفويض والتصعيد."
      },
      "Point of Sale": {
        "title": "نقاط البيع ودرج النقدية",
        "description": "إعدادات نقاط البيع والوردية ودرج النقدية."
      },
      "Manufacturing": {
        "title": "التصنيع",
        "description": "أوامر الإنتاج وقوائم المواد والتكاليف."
      },
      "CRM": {
        "title": "إدارة العملاء",
        "description": "مراحل الفرص والعملاء والمتابعة."
      },
      "Integrations": {
        "title": "التكاملات الخارجية",
        "description": "الأنظمة الخارجية والربط والمزامنة."
      },
      "Messaging & Notifications": {
        "title": "الرسائل وWhatsApp",
        "description": "قوالب الرسائل والمجموعات والتنبيهات."
      },
      "Reporting": {
        "title": "التقارير والتصدير",
        "description": "خيارات التقارير والتصدير والجدولة."
      }
    }
  },

  accountingHome: {
    title: "المحاسبة والمالية",
    description: "مركز العمليات المالية في PrimeERP.",
    areas: {
      chartOfAccounts: { title: "دليل الحسابات", description: "الحسابات والأقسام ومراكز التكلفة" },
      journalEntries: { title: "القيود اليومية", description: "إنشاء ومراجعة وترحيل القيود" },
      financialReports: { title: "التقارير المالية", description: "التقارير والتحليلات المالية" },
      arApAging: { title: "أعمار الذمم AR/AP", description: "تحليل المستحقات المدينة والدائنة حسب تاريخ الاستحقاق" },
      partnerStatements: { title: "كشوف حسابات العملاء والموردين", description: "كشف حركة الذمم والمدفوعات والرصيد الجاري" }
    }
  },
  productsHome: {
    title: "كتالوج المنتجات والتسعير",
    description: "واجهة تشغيلية متصلة مباشرةً بكتالوج المنتجات: التصنيفات، قوائم الأسعار، الوصفات وتحليل أثر الهامش.",
    activeCompanyRequired: "اختر شركة فعالة أولاً.",
    loadFailed: "تعذر تحميل كتالوج المنتجات.",
    loading: "جارٍ تحميل الكتالوج...",
    categories: "التصنيفات",
    priceLists: "قوائم الأسعار",
    recipes: "الوصفات",
    belowMargin: "تحت هامش 30%",
    emptyPriceLists: "لا توجد قوائم أسعار.",
    recipeSku: "الوصفات المرتبطة بـ SKU",
    emptyRecipes: "لا توجد وصفات.",
    version: "إصدار",
    unitCost: "تكلفة الوحدة",
    components: "مكونات",
    pricingImpact: "أثر التسعير والهامش",
    pricingImpactDescription: "المنتجات التي تقع تحت هامش 30% وفق بيانات الكتالوج الحالية.",
    product: "المنتج",
    cost: "التكلفة",
    price: "السعر",
    margin: "الهامش",
    recommendedPrice: "السعر المقترح",
    default: "افتراضية",
    skuCode: "SKU/Code"
  },

  purchasing: {
    title: "المشتريات",
    description: "إنشاء طلب الشراء، الاعتماد، الاستلام والتحويل إلى دورة الدفع.",
    unexpectedError: "حدث خطأ غير متوقع.",
    supplier: "المورد",
    documentNumber: "رقم المستند",
    purchaseOrderLine: "بند أمر الشراء",
    receivedReceipt: "إذن استلام مستلم",
    unitPrice: "السعر",
    quantity: "الكمية",
    processing: "جارٍ التنفيذ...",
    loadingCompanyDate: "جارٍ جلب تاريخ الشركة...",
    createDocument: "إنشاء مستند",
    loading: "جارٍ التحميل...",
    number: "رقم",
    date: "التاريخ",
    type: "النوع",
    status: "الحالة",
    total: "الإجمالي",
    actions: "إجراءات",
    confirm: "تأكيد",
    approve: "موافقة",
    reject: "رفض",
    receive: "استلام",
    payFull: "دفع كامل",
    details: "تفاصيل",
    close: "إغلاق",
    document: "المستند",
    item: "الصنف",
    itemId: "كود الصنف",
    paid: "المدفوع",
    types: { requisition: "طلب احتياج", rfq: "طلب عرض سعر", order: "أمر شراء", receipt: "إذن استلام", bill: "فاتورة مورد" },
    statuses: { draft: "مسودة", pending_approval: "بانتظار الموافقة", approved: "معتمد", confirmed: "مؤكد", partially_received: "مستلم جزئياً", received: "مستلم", posted: "مرحّل", cancelled: "ملغي", rejected: "مرفوض", partially_fulfilled: "منفذ جزئياً" }
  },
  crm: {
    title: "إدارة علاقات العملاء",
    pipeline: "عميل محتمل ← عميل ← عرض سعر ← أمر بيع / فاتورة.",
    lead: "عميل محتمل",
    saveLead: "حفظ العميل المحتمل",
    leads: "العملاء المحتملون",
    opportunitiesQuotations: "الفرص وعروض الأسعار",
    loadFailed: "تعذر تحميل بيانات CRM.",
    createLeadFailed: "تعذر إنشاء العميل المحتمل.",
    fields: { code: "الكود", name: "الاسم", phone: "الهاتف", email: "البريد الإلكتروني" }
  },

  register: {
    workspaceLabel:
      "إنشاء مساحة عمل جديدة",

    pageTitle:
      "إنشاء حساب جديد",

    pageSubtitle:
      "أدخل بيانات الشركة ومدير النظام لبدء استخدام برايم ERP.",

    companyName:
      "اسم الشركة",

    companyPlaceholder:
      "اسم الشركة",

    fullName:
      "الاسم بالكامل",

    fullNamePlaceholder:
      "أحمد جمال",

    email:
      "البريد الإلكتروني للعمل",

    emailPlaceholder:
      "name@company.com",

    mobile:
      "رقم الهاتف",

    mobilePlaceholder:
      "+20 100 000 0000",

    password:
      "كلمة المرور",

    passwordPlaceholder:
      "ثمانية أحرف على الأقل",

    confirmPassword:
      "تأكيد كلمة المرور",

    confirmPasswordPlaceholder:
      "أعد كتابة كلمة المرور",

    acceptTerms:
      "أوافق على",

    terms:
      "شروط الاستخدام",

    and:
      "و",

    privacy:
      "سياسة الخصوصية",

    startTrial:
      "ابدأ التجربة المجانية",

    creatingAccount:
      "جاري إنشاء الحساب...",

    alreadyRegistered:
      "مسجل بالفعل؟",

    alreadyHaveAccount:
      "لديك حساب بالفعل؟",

    signIn:
      "تسجيل الدخول",

    secureMessage:
      "بياناتك مشفرة ومحفوظة بصورة آمنة.",

    featureTitle:
      "ابدأ رحلة تطوير أعمالك",

    heroTitle:
      "أدر جميع أعمال شركتك من خلال منصة واحدة قوية.",

    heroDescription:
      "أنشئ مساحة عمل برايم ERP واجمع الحسابات والمبيعات والمخزون والموظفين والعمليات في مكان واحد.",

    features: {
      secure:
        "نظام ERP سحابي وآمن",

      branches:
        "إدارة الشركات والفروع المتعددة",

      reports:
        "تقارير مركزية وتحليلات للأعمال",

      trial:
        "ابدأ بتجربة مجانية",
    },

    errors: {
      companyRequired:
        "برجاء إدخال اسم الشركة.",

      fullNameRequired:
        "برجاء إدخال الاسم بالكامل.",

      emailRequired:
        "برجاء إدخال البريد الإلكتروني.",

      mobileRequired:
        "برجاء إدخال رقم الهاتف.",

      passwordLength:
        "يجب ألا تقل كلمة المرور عن 8 أحرف.",

      passwordsMismatch:
        "كلمتا المرور غير متطابقتين.",

      termsRequired:
        "يجب الموافقة على شروط الاستخدام وسياسة الخصوصية.",

      serverConnection:
        "تعذر الاتصال بالخادم. تأكد من تشغيل الـ Backend.",

      accountExists:
        "يوجد حساب مسجل بالفعل بهذا البريد الإلكتروني.",

      invalidData:
        "برجاء مراجعة البيانات المدخلة.",

      registrationFailed:
        "تعذر إنشاء الحساب. حاول مرة أخرى.",

      unexpected:
        "حدث خطأ غير متوقع. حاول مرة أخرى.",
    },

    success:
      "تم إنشاء حسابك بنجاح.",
  },

  login: {
    welcomeBack:
      "مرحبًا بعودتك",

    pageTitle:
      "تسجيل الدخول إلى حسابك",

    pageSubtitle:
      "أدخل بيانات حسابك للوصول إلى مساحة عمل برايم ERP.",

    email:
      "البريد الإلكتروني",

    emailPlaceholder:
      "name@company.com",

    password:
      "كلمة المرور",

    passwordPlaceholder:
      "أدخل كلمة المرور",

    rememberMe:
      "تذكرني",

    forgotPassword:
      "نسيت كلمة المرور؟",

    signIn:
      "تسجيل الدخول",

    signingIn:
      "جاري تسجيل الدخول...",

    newToPrimeERP:
      "مستخدم جديد؟",

    noAccount:
      "ليس لديك حساب؟",

    startTrial:
      "ابدأ التجربة المجانية",

    heroTitle:
      "كل ما تحتاجه لإدارة أعمالك في مساحة عمل واحدة مترابطة.",

    heroDescription:
      "سجل الدخول لإدارة الحسابات والمبيعات والمخزون والموظفين والفروع وتقارير الأعمال.",

    features: {
      dashboard:
        "لوحة معلومات فورية للأعمال",

      security:
        "وصول آمن للشركات والفروع",

      reporting:
        "تقارير مالية مركزية",

      anywhere:
        "إدارة العمليات من أي مكان",
    },

    errors: {
      required:
        "برجاء إدخال البريد الإلكتروني وكلمة المرور.",

      invalidCredentials:
        "البريد الإلكتروني أو كلمة المرور غير صحيحة.",

      serverConnection:
        "تعذر الاتصال بالخادم. تأكد من تشغيل الـ Backend.",

      unexpected:
        "حدث خطأ غير متوقع. حاول مرة أخرى.",
    },

    success:
      "مرحبًا بعودتك إلى برايم ERP.",

    registrationSuccess:
      "تم إنشاء الحساب بنجاح. سجل الدخول للمتابعة.",
  },
  reports: {
    title: "التقارير والتحليلات",
    description: "تحليل مؤشرات الأعمال بالذكاء الاصطناعي، وإرسال التقارير، وجدولة التسليم عبر البريد أو WhatsApp.",
    loadSchedulesFailed: "تعذر تحميل جدولة التقارير.",
    activeCompanyRequired: "اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.",
    invalidDateRange: "تاريخ البداية لا يمكن أن يكون بعد تاريخ النهاية.",
    invalidMetricsJson: "صيغة Metrics JSON غير صحيحة.",
    analyzeFailed: "تعذر تحليل التقرير.",
    deliverFailed: "تعذر إرسال التقرير.",
    deliverSuccess: "تم إرسال التقرير بنجاح.",
    createScheduleFailed: "تعذر إنشاء الجدولة.",
    smartAnalysis: "تحليل ذكي",
    rulesWithoutAi: "تظل القواعد الرقابية متاحة حتى عند عدم تفعيل مزود AI.",
    analysisQuestion: "سؤال التحليل",
    analysisPlaceholder: "ما أهم المخاطر في المؤشرات الحالية؟",
    fromDate: "من تاريخ",
    toDate: "إلى تاريخ",
    metricsJson: "بيانات المؤشرات JSON",
    analyze: "تحليل المؤشرات",
    analyzing: "جارٍ التحليل...",
    deliverReport: "إرسال تقرير",
    deliveryRequirement: "يتطلب إعداد SMTP أو WhatsApp في بيئة التشغيل.",
    company: "الشركة",
    channel: "القناة",
    destination: "المستلم",
    reportTitle: "عنوان التقرير",
    content: "المحتوى",
    contentPlaceholder: "حلل المؤشرات أولاً أو اكتب محتوى التقرير هنا.",
    sendNow: "إرسال الآن",
    sending: "جارٍ الإرسال...",
    analysisResult: "نتيجة التحليل",
    scheduleReport: "جدولة التقرير",
    scheduleHelp: "الصيغ المدعومة: every:15m و every:2h و daily:09:00 و weekly:MON@09:00 و monthly:15@09:00 و quarterly:1@09:00.",
    saveSchedule: "حفظ الجدولة",
    saving: "جارٍ الحفظ...",
    currentSchedules: "الجدولات الحالية",
    noSchedules: "لا توجد جدولات لهذه الشركة.",
    schedule: "الجدول",
    status: "الحالة",
    nextRun: "التشغيل القادم",
    scheduled: "مجدول"
  },

  pos: {
    closeAndReconcile: "إغلاق وتسوية الوردية",
    cannotClosePending: "لا يمكن إغلاق الوردية مع وجود طلبات لم تتم مزامنتها.",
    shiftClosed: "تم إغلاق الوردية رقم {{id}}.",
    expectedCash: "النقدية المتوقعة",
    counted: "النقدية المعدودة",
    variance: "الفرق",
    menuOrder: "طلب من المنيو",
    posOutlet: "جهاز POS / مكان الخدمة",
    chooseMenuItem: "اختر صنفًا من المنيو",
    quantity: "الكمية",
    submitOrder: "إرسال الطلب وإتمام البيع",
    devices: "الأجهزة",
    latestSales: "أحدث مبيعات POS",
    locallyQueued: "محفوظ محليًا · في انتظار المزامنة",
    chooseStation: "اختر محطة المطبخ/البار",
    refreshQueue: "تحديث الطابور",
    start: "بدء",
    ready: "جاهز",
    served: "تم التسليم",
    newShift: "جديدة",
    customerPartnerId: "كود العميل / الشريك",
    warehouseAuto: "مخزن الاستهلاك (يُحدد تلقائيًا من مكان الخدمة)",
    menu: "المنيو",
    item: "الصنف",
    paymentMethods: { cash: "نقدي", card: "بطاقة", bank: "تحويل بنكي", wallet: "محفظة" },
    orderStatuses: { draft: "مسودة", pending: "قيد الانتظار", preparing: "قيد التحضير", ready: "جاهز", served: "تم التسليم", paid: "مدفوع", cancelled: "ملغي" },
    title: "نقاط البيع للمطاعم والفنادق",
    flowDescription: "مكان الخدمة ← جهاز POS ← المنيو ← صنف المنيو ← محطة التحضير (المطبخ/البار) ← شاشة التنفيذ.",
    offlineCacheNotice: "أنت تعمل دون اتصال؛ يتم استخدام آخر بيانات POS محفوظة محليًا.",
    loadShiftFailed: "تعذر تحميل وردية الكاشير.",
    createOutletFailed: "فشل إنشاء مكان الخدمة.",
    assignWarehouseFailed: "فشل ربط مخزن الاستهلاك.",
    createStationFailed: "فشل إنشاء محطة التحضير.",
    createTerminalFailed: "فشل إنشاء جهاز POS.",
    linkMenuFailed: "فشل ربط المنيو بالجهاز.",
    routeItemFailed: "فشل ربط صنف المنيو بمحطة التحضير.",
    selectTerminal: "اختر جهاز POS أولاً.",
    openShiftFailed: "فشل فتح وردية الكاشير.",
    enterCountedCash: "أدخل النقدية الفعلية قبل إغلاق الوردية.",
    syncBeforeClose: "زامن الطلبات المحفوظة محليًا قبل إغلاق الوردية.",
    closeShiftFailed: "فشل إغلاق الوردية.",
    companyDateRequired: "تعذر جلب تاريخ الشركة من الخادم؛ لا يمكن إتمام البيع بتاريخ الجهاز.",
    selectMenuItem: "اختر صنفًا من المنيو.",
    savedOffline: "تم حفظ الطلب محليًا، وسيتم ترحيله تلقائيًا عند عودة الاتصال.",
    connectionSavedOffline: "تعذر الاتصال بالخادم؛ تم حفظ الطلب محليًا للمزامنة التلقائية.",
    checkoutFailed: "فشل إتمام الطلب.",
    loadKdsFailed: "فشل تحميل شاشة المطبخ/البار.",
    updateOrderFailed: "فشل تحديث حالة الطلب.",
    tabs: { sale: "البيع", setup: "إعداد الأماكن والأجهزة", kds: "المطبخ / البار" },
    createOutlet: "إضافة مكان خدمة",
    assignWarehouse: "ربط مخزن الاستهلاك",
    createStation: "إضافة محطة تحضير",
    createTerminal: "ربط جهاز POS بالمكان",
    linkMenu: "ربط المنيو والأسعار بالجهاز",
    routeItem: "تحديد محطة تحضير كل صنف",
    addOutlet: "إضافة المكان",
    saveWarehouse: "حفظ مخزن الاستهلاك",
    addStation: "إضافة المحطة وربطها بالمكان",
    addTerminal: "إضافة الجهاز",
    saveMenuLink: "ربط المنيو",
    saveRouting: "حفظ مسار الصنف",
    cashierShift: "وردية الكاشير وتسوية النقدية",
    selectTerminalHint: "اختر جهاز POS لعرض ورديته.",
    openingCash: "رصيد بداية الوردية",
    openShift: "فتح وردية",
    countedCash: "النقدية الفعلية عند الإغلاق",
    online: "● متصل",
    offline: "● غير متصل — الطلبات تُحفظ محليًا",
    pendingSync: "طلب في انتظار المزامنة"
  },

  hr: {
    activeCompanyRequired: "اختر شركة فعالة أولاً.",
    loadFailed: "تعذر تحميل بيانات الموارد البشرية.",
    attendanceFailed: "تعذر تسجيل الحضور.",
    correctionSubmitFailed: "تعذر إرسال تصحيح الحضور.",
    overtimeSubmitFailed: "تعذر إرسال طلب الساعات الإضافية.",
    overtimeDecisionFailed: "تعذر اتخاذ قرار الساعات الإضافية.",
    correctionDecisionFailed: "تعذر اعتماد تصحيح الحضور.",
    saveWorkforceFailed: "تعذر حفظ ملف المستخدم.",
    addEmployeeFailed: "تعذر إضافة الموظف.",
    saveLeaveBalanceFailed: "تعذر حفظ رصيد الإجازة.",
    leaveSubmitFailed: "تعذر إرسال طلب الإجازة.",
    leaveDecisionFailed: "تعذر اتخاذ قرار الإجازة.",
    title: "الموارد البشرية",
    description: "ملفات الموظفين، أرصدة الإجازات، ودورة اعتماد الطلبات.",
    addEmployee: "إضافة موظف",
    employeeNumber: "الرقم الوظيفي",
    employeeName: "اسم الموظف",
    basicSalary: "الراتب الأساسي",
    saveEmployee: "حفظ الموظف",
    setLeaveBalance: "إعداد رصيد إجازة",
    employee: "الموظف",
    leaveTypes: { annual: "سنوية", sick: "مرضية", unpaid: "بدون أجر", other: "أخرى" },
    entitledDays: "الرصيد المستحق بالأيام",
    saveBalance: "حفظ الرصيد",
    leaveRequest: "طلب إجازة",
    from: "من",
    to: "إلى",
    daysCount: "عدد الأيام",
    optionalReason: "السبب (اختياري)",
    submitRequest: "إرسال الطلب",
    manualAttendance: "تسجيل حضور يدوي",
    manualAttendanceHelp: "الإدخال اليدوي متاح عندما يكون مصدر الحضور في إعدادات الشركة «يدوي». موصلات البصمة والموبايل لم تُربط بعد.",
    record: "تسجيل",
    attendanceLog: "سجل الحضور",
    noAttendance: "لا توجد سجلات حضور.",
    requestCorrection: "طلب تصحيح",
    correctRecord: "تصحيح السجل",
    checkIn: "وقت الحضور",
    checkOut: "وقت الانصراف",
    correctionReason: "سبب التصحيح",
    send: "إرسال",
    cancel: "إلغاء",
    correctionRequests: "طلبات تصحيح الحضور",
    noCorrectionRequests: "لا توجد طلبات تصحيح.",
    proposedCheckIn: "الحضور المقترح",
    proposedCheckOut: "الانصراف المقترح",
    reason: "السبب",
    status: "الحالة",
    decision: "قرار",
    approve: "موافقة",
    reject: "رفض",
    overtimeRequest: "طلب ساعات إضافية",
    overtimeHelp: "يُحسب الحد المتاح من وقت الحضور والانصراف بعد خصم ساعات العمل اليومية المحددة في إعدادات الشركة. وتُحجز الطلبات المنتظرة لمنع تجاوز إجمالي الساعات المسجلة.",
    attendanceRecord: "سجل الحضور",
    hours: "الساعات",
    overtimeReason: "سبب العمل الإضافي",
    overtimeRequests: "طلبات الساعات الإضافية",
    noRequests: "لا توجد طلبات.",
    leaveBalances: "أرصدة الإجازات",
    noLeaveBalances: "لا توجد أرصدة مسجلة.",
    type: "النوع",
    entitled: "المستحق",
    consumed: "المستخدم",
    available: "المتاح",
    leaveRequests: "طلبات الإجازة",
    refresh: "تحديث",
    period: "الفترة",
    days: "الأيام",
    action: "الإجراء",
    companyUserProfiles: "ملفات مستخدمي الشركة",
    noCompanyUsers: "لا يوجد مستخدمون مسجلون.",
    phone: "الهاتف",
    address: "العنوان",
    save: "حفظ",
    statuses: { pending: "قيد الانتظار", approved: "موافق عليه", rejected: "مرفوض" },
    attendanceSources: { manual: "يدوي", fingerprint: "بصمة", mobile: "موبايل" }
  },

};

export default arTranslation;