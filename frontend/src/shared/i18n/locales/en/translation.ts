const enTranslation = {
  navigation: {
    "dashboard": "Dashboard",
    "module-catalog": "Module Catalog",
    "helpdesk": "AI Help Desk",
    "identity": "Identity & Access",
    "users": "Users",
    "roles": "Roles",
    "permissions": "Permissions",
    "organization": "Organization",
    "companies": "Companies",
    "branches": "Branches",
    "accounting": "Accounting",
    "chart-of-accounts": "Chart of Accounts",
    "fiscal-years": "Fiscal Years",
    "journals": "Journals",
    "journal-entries": "Journal Entries",
    "cost-centers": "Cost Centers",
    "financial-reports": "Financial Reports",
    "treasury": "Treasury",
    "banks": "Banks",
    "cash": "Cash",
    "checks": "Checks",
    "sales": "Sales",
    "customers": "Customers",
    "sales-orders": "Sales Orders",
    "sales-invoices": "Sales Invoices",
    "purchasing": "Purchasing",
    "suppliers": "Suppliers",
    "purchase-orders": "Purchase Orders",
    "purchase-invoices": "Purchase Invoices",
    "inventory": "Inventory",
    "warehouses": "Warehouses",
    "locations": "Locations",
    "products": "Products",
    "stock-transactions": "Stock Transactions",
    "transfers": "Transfers",
    "reservations": "Reservations",
    "commercial-leasing": "Commercial Leasing",
    "lease-contracts": "Lease Contracts",
    "installments": "Installments",
    "revenue-share": "Revenue Share",
    "hospitality": "Hospitality",
    "hotels": "Hotels",
    "hotel-revenue": "Hotel Revenue",
    "hotel-profit-share": "Profit Share",
    "shipping": "Shipping",
    "shipping-status-settings": "Status Settings",
    "shipping-pricing": "Carrier Pricing",
    "shipping-settlements": "Settlements",
    "saas": "SaaS Administration",
    "saas-dashboard": "SaaS Overview",
    "plans": "Plans & Entitlements",
    "reports": "Reports",
    "notifications": "Messages & Notifications",
    "settings": "Settings",
    "company-policies": "Company Policies"
  },

  common: {
    loading: "Loading...",
    processing: "Processing...",
    close: "Close",
    refresh: "Refresh",
    cancel: "Cancel",
    appName: "PrimeERP",
    appDescription: "Business Management Platform",

    loading: "Loading...",
    save: "Save",
    cancel: "Cancel",
    submit: "Submit",

    english: "English",
    arabic: "العربية",

    copyright:
      "All rights reserved.",

    secured:
      "Protected by secure authentication and encrypted communication.",
    new: "New",
    closeNavigation: "Close navigation",
    workspace: "Workspace",
    online: "Online",
    searchNavigation: "Search navigation",
    searchScreens: "Search screens or modules...",
    clearSearch: "Clear search",
    mainNavigation: "Main navigation",
    searchResults: "Search results",
    businessManagement: "Business management",
    noMatchingResults: "No matching results.",
    platformAdministrator: "Platform administrator",
    secureWorkspace: "Secure workspace",
    organizationAccess: "Organization-level access and data isolation",
    integratedBusinessManagement: "Integrated business management",
    connectedBusinessOperations: "Connected business operations",
    systemUser: "System user",
    user: "User",
  },

  userForm: {
    titleCreate: "Create user",
    titleEdit: "Edit user",
    descriptionCreate: "Enter the user details and assign a role and permissions.",
    descriptionEdit: "Update the user details, then save your changes.",
    fullName: "Full name",
    fullNamePlaceholder: "Enter full name",
    username: "Username",
    email: "Email address",
    phone: "Phone number",
    password: "Password",
    newPassword: "New password",
    confirmPassword: "Confirm password",
    confirmNewPassword: "Confirm new password",
    passwordPlaceholderEdit: "Leave blank to keep unchanged",
    passwordPlaceholderCreate: "At least 8 characters",
    confirmPasswordPlaceholder: "Re-enter the password",
    passwordHint: "Password must contain at least 8 characters.",
    role: "Role & permissions",
    loadingRoles: "Loading roles...",
    chooseRole: "Choose a role",
    noRole: "No role",
    noRoles: "No roles are currently available.",
    address: "Address",
    addressPlaceholder: "Enter the user's address",
    saveChanges: "Save changes",
    create: "Create user",
    cancel: "Cancel",
    errors: {
      fullName: "Please enter the full name.",
      username: "Please enter a username.",
      usernameLength: "Username must contain at least 3 characters.",
      email: "Please enter an email address.",
      password: "Please enter a password.",
      passwordLength: "Password must contain at least 8 characters.",
      passwordMax: "Password must not exceed 128 characters.",
      passwordMismatch: "Passwords do not match."
    }
  },

  inventory: {
    home: {
      title: "Inventory & Warehouses",
      description: "Manage company and branch warehouses and storage locations in one workspace.",
      warehouses: "Warehouses",
      warehousesDescription: "Manage central and branch warehouses.",
      locations: "Storage locations",
      locationsDescription: "Manage receiving, storage and shipping locations within each warehouse.",
      items: "Items & stock",
      itemsDescription: "Item catalog, stock balances and costing."
    }
  },

  sales: {
    title: "Sales",
    description: "Create sales documents, approve them, post inventory and collect payments within the sales cycle.",
    customer: "Customer",
    autoNumber: "Document numbers are generated automatically according to company settings.",
    sourceOrderOptional: "Sales order (optional, subject to policy)",
    sourceOrderLine: "Sales order line",
    itemQuantity: "Item {{item}} · Quantity {{quantity}}",
    warehouse: "Issuing / delivery warehouse",
    price: "Price",
    quantity: "Quantity",
    itemId: "Item ID",
    loadingCompanyDate: "Loading company date...",
    createDocument: "Create document",
    types: {
      quotation: "Quotation",
      order: "Sales order",
      delivery: "Delivery note",
      invoice: "Invoice"
    },
    statuses: {
      draft: "Draft",
      pending_approval: "Pending approval",
      approved: "Approved",
      confirmed: "Confirmed",
      partially_fulfilled: "Partially fulfilled",
      fulfilled: "Fulfilled",
      posted: "Posted",
      cancelled: "Cancelled",
      rejected: "Rejected"
    },
    columns: {
      number: "Number",
      date: "Date",
      type: "Type",
      status: "Status",
      total: "Total",
      actions: "Actions"
    },
    actions: {
      confirm: "Confirm",
      cancelRelease: "Cancel order and release reservation",
      approve: "Approve",
      reject: "Reject",
      postInventory: "Post inventory",
      collectFull: "Collect in full",
      details: "Details"
    },
    confirmCancelOrder: "This will cancel the sales order and release reserved quantities. Do you want to continue?",
    documentNumber: "Document #{{number}}",
    detailsSummary: "Customer: {{customer}} — Total: {{total}} — Paid: {{paid}}"
  },

  roles: {
    notifications: {
      created: "Role created successfully.",
      updated: "Role updated successfully.",
      permissionsUpdated: "Role permissions updated successfully.",
      deactivated: "Role deactivated.",
      activated: "Role activated.",
      deleteAssigned: "A role assigned to users cannot be deleted.",
      deleted: "Role deleted successfully."
    },
    title: "Roles & Permissions",
    description: "Create roles and define what each user can view or perform in PrimeERP.",
    newRole: "New role",
    total: "Total roles",
    active: "Active roles",
    assignedUsers: "Assigned users",
    searchPlaceholder: "Search by role name or description...",
    confirmDelete: "Do you want to delete the role \"{{name}}\"?",
    errors: {
      deleteAssigned: "This role cannot be deleted because it is assigned to {{count}} users."
    }
  },
  rolesTable: {
    active: "Active",
    inactive: "Inactive",
    loading: "Loading roles...",
    emptyTitle: "No roles found",
    emptyDescription: "Create your first role and assign its permissions.",
    role: "Role",
    permissions: "Permissions",
    users: "Users",
    status: "Status",
    enabled: "Enable role",
    actions: "Actions",
    noDescription: "No description",
    permissionCount: "{{count}}",
    permissionCount_one: "{{count}} permission",
    permissionCount_other: "{{count}} permissions",
    edit: "Edit role",
    delete: "Delete role"
  },

  roleForm: {
    titleCreate: "Create role",
    titleEdit: "Edit role",
    description: "Set the role name and the permissions granted to users assigned to it.",
    name: "Role name",
    namePlaceholder: "Example: Branch Manager",
    active: "Role is active",
    descriptionLabel: "Description",
    descriptionPlaceholder: "Briefly describe this role's responsibilities",
    permissions: "Role permissions",
    selectedCount: "{{selected}} of {{total}} permissions selected",
    selectAll: "Select or clear all",
    searchPermissions: "Search permissions...",
    loadingPermissions: "Loading permissions...",
    noPermissions: "No permissions available.",
    permissionCount_one: "{{count}} permission",
    permissionCount_other: "{{count}} permissions",
    selectSection: "Select entire section",
    unselectSection: "Clear section selection",
    save: "Save changes",
    create: "Create role",
    cancel: "Cancel",
    resources: {
      users: "Users", roles: "Roles", permissions: "Permissions",
      companies: "Companies", branches: "Branches", sales: "Sales",
      customers: "Customers", suppliers: "Suppliers", products: "Products",
      inventory: "Inventory", purchasing: "Purchasing", accounting: "Accounting",
      restaurant: "Restaurants", pos: "Point of Sale", hr: "Human Resources",
      reports: "Reports", shipping: "Shipping", settings: "Settings",
      other: "Other"
    },
    actions: {
      view: "View", read: "Read", create: "Create", update: "Update",
      delete: "Delete", approve: "Approve", manage: "Full management",
      print: "Print", export: "Export", cancel: "Cancel"
    }
  },

  permissions: {
    title: "Permissions",
    description: "View and manage system permissions and their role assignments.",
    catalog: "Permission catalog",
    refresh: "Refresh",
    loading: "Loading...",
    processing: "Processing...",
    name: "Name",
    resource: "Resource",
    action: "Action",
    descriptionColumn: "Description",
    status: "Status",
    actions: "Action",
    active: "Active",
    inactive: "Inactive",
    activate: "Activate",
    deactivate: "Deactivate",
    empty: "No permissions found.",
    errors: {
      load: "Unable to load permissions.",
      update: "Unable to update the permission."
    }
  },

  usersTable: {
    "loading": "Loading users...",
    "active": "Active",
    "inactive": "Inactive",
    "emptyTitle": "No users found",
    "emptyDescription": "No results match the current search or filters.",
    "user": "User",
    "email": "Email",
    "role": "Role",
    "status": "Status",
    "lastLogin": "Last login",
    "accountEnabled": "Account enabled",
    "actions": "Actions",
    "superuser": "Administrator privileges",
    "platformAdmin": "Platform administrator",
    "noRole": "No role assigned",
    "deactivateUser": "Deactivate user",
    "activateUser": "Activate user",
    "editUser": "Edit user",
    "resetPassword": "Reset password",
    "deleteUser": "Delete user",
    "unavailable": "Unavailable",
    "neverLoggedIn": "Never logged in"
  },

  users: {
    notifications: {
      created: "User created successfully.",
      updated: "User details updated.",
      deactivated: "User deactivated.",
      activated: "User activated.",
      deleted: "User deleted successfully."
    },
    resetPassword: {
      title: "Reset password",
      userLabel: "User",
      newPassword: "New password",
      confirmPassword: "Confirm password",
      forceChange: "Require the user to change it",
      save: "Save password",
      success: "Password reset successfully.",
      errors: {
        passwordLength: "Password must contain at least 6 characters.",
        passwordMismatch: "Passwords do not match.",
        failed: "Unable to reset the password."
      }
    },
    "title": "User Management",
    "description": "Create users, update their details, and manage their status and roles.",
    "newUser": "New user",
    "totalUsers": "Total users",
    "activeUsers": "Active users",
    "searchPlaceholder": "Search by name, username, or email...",
    "confirmDelete": "Do you want to delete user \"{{name}}\"?"
  },

  settingsCenter: {
    "controlCenter": "Control Center",
    "title": "System Settings",
    "description": "Choose a module to display all of its settings. Only one module menu stays expanded at a time.",
    "moduleSettings": "Module settings",
    "selectModule": "Select a module to view its options",
    "settingsModules": "Settings modules",
    "sectionSettings": "{{title}} settings",
    "footer": "PrimeERP · Settings Center",
    "sections": {
      "General": {
        "title": "General",
        "description": "Company details, language, date, time zone, and currency."
      },
      "Accounting": {
        "title": "Accounting",
        "description": "Fiscal periods, accounts, and posting policies."
      },
      "Taxes": {
        "title": "Taxes & e-Invoicing",
        "description": "Taxes, returns, and electronic invoicing."
      },
      "Sales": {
        "title": "Sales & Customers",
        "description": "Pricing, discounts, credit, and sales."
      },
      "Purchasing": {
        "title": "Purchasing & Suppliers",
        "description": "Purchasing, approvals, and supplier policies."
      },
      "Inventory": {
        "title": "Inventory & Warehouses",
        "description": "Valuation, reservations, stocktaking, and replenishment."
      },
      "Human Resources": {
        "title": "HR, Attendance & Payroll",
        "description": "Biometrics, attendance, leave, payroll, and approvals."
      },
      "Approvals": {
        "title": "Approvals & Workflow",
        "description": "Approval workflows, delegation, and escalation."
      },
      "Point of Sale": {
        "title": "POS & Cash Drawer",
        "description": "POS, shifts, and cash drawer settings."
      },
      "Manufacturing": {
        "title": "Manufacturing",
        "description": "Production orders, bills of materials, and costs."
      },
      "CRM": {
        "title": "CRM",
        "description": "Lead stages, customers, and follow-ups."
      },
      "Integrations": {
        "title": "Integrations",
        "description": "External systems, connections, and synchronization."
      },
      "Messaging & Notifications": {
        "title": "Messages & WhatsApp",
        "description": "Message templates, groups, and alerts."
      },
      "Reporting": {
        "title": "Reports & Export",
        "description": "Report, export, and scheduling options."
      }
    }
  },

  accountingHome: {
    title: "Accounting & Finance",
    description: "The financial operations center in PrimeERP.",
    areas: {
      chartOfAccounts: { title: "Chart of Accounts", description: "Accounts, departments, and cost centers" },
      journalEntries: { title: "Journal Entries", description: "Create, review, and post journal entries" },
      financialReports: { title: "Financial Reports", description: "Financial reports and analytics" },
      arApAging: { title: "AR/AP Aging", description: "Analyze receivables and payables by due date" },
      partnerStatements: { title: "Customer & Supplier Statements", description: "Receivable/payable movements, payments, and running balances" }
    }
  },
  productsHome: {
    title: "Product Catalog & Pricing",
    description: "Operational workspace connected to the catalog API: categories, price lists, recipes, and margin impact.",
    activeCompanyRequired: "Select an active company first.",
    loadFailed: "Could not load the product catalog.",
    loading: "Loading catalog...",
    categories: "Categories",
    priceLists: "Price lists",
    recipes: "Recipes",
    belowMargin: "Below 30% margin",
    emptyPriceLists: "No price lists found.",
    recipeSku: "Recipes linked to SKU",
    emptyRecipes: "No recipes found.",
    version: "Version",
    unitCost: "Unit cost",
    components: "components",
    pricingImpact: "Pricing & Margin Impact",
    pricingImpactDescription: "Products below a 30% margin based on current catalog data.",
    product: "Product",
    cost: "Cost",
    price: "Price",
    margin: "Margin",
    recommendedPrice: "Recommended price",
    default: "Default",
    skuCode: "SKU/Code"
  },

  purchasing: {
    title: "Purchasing",
    description: "Create purchase requests, approve orders, receive goods, and move documents into payment.",
    unexpectedError: "An unexpected error occurred.",
    supplier: "Supplier",
    documentNumber: "Document number",
    purchaseOrderLine: "Purchase order line",
    receivedReceipt: "Received receipt",
    unitPrice: "Unit price",
    quantity: "Quantity",
    processing: "Processing...",
    loadingCompanyDate: "Loading company date...",
    createDocument: "Create document",
    loading: "Loading...",
    number: "Number",
    date: "Date",
    type: "Type",
    status: "Status",
    total: "Total",
    actions: "Actions",
    confirm: "Confirm",
    approve: "Approve",
    reject: "Reject",
    receive: "Receive",
    payFull: "Pay in full",
    details: "Details",
    close: "Close",
    document: "Document",
    item: "Item",
    itemId: "Item ID",
    paid: "Paid",
    types: { requisition: "Purchase requisition", rfq: "Request for quotation", order: "Purchase order", receipt: "Goods receipt", bill: "Supplier bill" },
    statuses: { draft: "Draft", pending_approval: "Pending approval", approved: "Approved", confirmed: "Confirmed", partially_received: "Partially received", received: "Received", posted: "Posted", cancelled: "Cancelled", rejected: "Rejected", partially_fulfilled: "Partially fulfilled" }
  },
  crm: {
    title: "Customer Relationship Management",
    pipeline: "Lead → Customer → Quotation → Sales order / Invoice.",
    lead: "Lead",
    saveLead: "Save lead",
    leads: "Leads",
    opportunitiesQuotations: "Opportunities & Quotations",
    loadFailed: "Could not load CRM data.",
    createLeadFailed: "Could not create the lead.",
    fields: { code: "Code", name: "Name", phone: "Phone", email: "Email" }
  },

  register: {
    workspaceLabel:
      "Create your workspace",

    pageTitle:
      "Create your account",

    pageSubtitle:
      "Enter your company and administrator details to start using PrimeERP.",

    companyName:
      "Company name",

    companyPlaceholder:
      "Prime Company",

    fullName:
      "Full name",

    fullNamePlaceholder:
      "Ahmed Gamal",

    email:
      "Business email",

    emailPlaceholder:
      "name@company.com",

    mobile:
      "Mobile number",

    mobilePlaceholder:
      "+20 100 000 0000",

    password:
      "Password",

    passwordPlaceholder:
      "Minimum 8 characters",

    confirmPassword:
      "Confirm password",

    confirmPasswordPlaceholder:
      "Repeat password",

    acceptTerms:
      "I agree to the",

    terms:
      "Terms of Service",

    and:
      "and",

    privacy:
      "Privacy Policy",

    startTrial:
      "Start Free Trial",

    creatingAccount:
      "Creating account...",

    alreadyRegistered:
      "Already registered?",

    alreadyHaveAccount:
      "Already have an account?",

    signIn:
      "Sign in",

    secureMessage:
      "Your information is encrypted and securely stored.",

    featureTitle:
      "Start your business journey",

    heroTitle:
      "Manage your entire business from one powerful platform.",

    heroDescription:
      "Create your PrimeERP workspace and bring your accounting, sales, inventory, employees, and operations together.",

    features: {
      secure:
        "Secure cloud-based ERP workspace",

      branches:
        "Manage multiple branches and companies",

      reports:
        "Centralized reports and business insights",

      trial:
        "Start with a free trial",
    },

    errors: {
      companyRequired:
        "Please enter your company name.",

      fullNameRequired:
        "Please enter your full name.",

      emailRequired:
        "Please enter your business email.",

      mobileRequired:
        "Please enter your mobile number.",

      passwordLength:
        "Password must contain at least 8 characters.",

      passwordsMismatch:
        "Passwords do not match.",

      termsRequired:
        "You must accept the Terms of Service and Privacy Policy.",

      serverConnection:
        "Cannot connect to the server. Make sure the Backend is running.",

      accountExists:
        "An account already exists with this email address.",

      invalidData:
        "Please review the entered information.",

      registrationFailed:
        "Registration failed. Please try again.",

      unexpected:
        "An unexpected error occurred. Please try again.",
    },

    success:
      "Your account has been created successfully.",
  },

  login: {
    welcomeBack:
      "Welcome back",

    pageTitle:
      "Sign in to your account",

    pageSubtitle:
      "Enter your account information to access your PrimeERP workspace.",

    email:
      "Email address",

    emailPlaceholder:
      "name@company.com",

    password:
      "Password",

    passwordPlaceholder:
      "Enter your password",

    rememberMe:
      "Remember me",

    forgotPassword:
      "Forgot password?",

    signIn:
      "Sign in",

    signingIn:
      "Signing in...",

    newToPrimeERP:
      "New to PrimeERP?",

    noAccount:
      "Don't have an account?",

    startTrial:
      "Start Free Trial",

    heroTitle:
      "Everything your business needs in one connected workspace.",

    heroDescription:
      "Sign in to manage your accounting, sales, inventory, employees, branches, and business reports.",

    features: {
      dashboard:
        "Real-time business dashboard",

      security:
        "Secure company and branch access",

      reporting:
        "Centralized financial reporting",

      anywhere:
        "Manage operations from anywhere",
    },

    errors: {
      required:
        "Please enter your email and password.",

      invalidCredentials:
        "Invalid email or password. Please try again.",

      serverConnection:
        "Cannot connect to the server. Make sure the Backend is running.",

      unexpected:
        "An unexpected error occurred. Please try again.",
    },

    success:
      "Welcome back to PrimeERP.",

    registrationSuccess:
      "Account created successfully. Sign in to continue.",
  },
  reports: {
    title: "Reports & Analytics",
    description: "Analyze business metrics with AI, deliver reports, and schedule email or WhatsApp distribution.",
    loadSchedulesFailed: "Could not load report schedules.",
    activeCompanyRequired: "Select an active company first; no default company is used.",
    invalidDateRange: "The start date cannot be later than the end date.",
    invalidMetricsJson: "Metrics JSON is invalid.",
    analyzeFailed: "Could not analyze the report.",
    deliverFailed: "Could not deliver the report.",
    deliverSuccess: "Report sent successfully.",
    createScheduleFailed: "Could not create the schedule.",
    smartAnalysis: "Smart analysis",
    rulesWithoutAi: "Control rules remain available even when no AI provider is enabled.",
    analysisQuestion: "Analysis question",
    analysisPlaceholder: "What are the key risks in the current metrics?",
    fromDate: "From date",
    toDate: "To date",
    metricsJson: "Metrics JSON",
    analyze: "Analyze metrics",
    analyzing: "Analyzing...",
    deliverReport: "Deliver report",
    deliveryRequirement: "SMTP or WhatsApp must be configured in the runtime environment.",
    company: "Company",
    channel: "Channel",
    destination: "Recipient",
    reportTitle: "Report title",
    content: "Content",
    contentPlaceholder: "Analyze the metrics first or enter the report content here.",
    sendNow: "Send now",
    sending: "Sending...",
    analysisResult: "Analysis result",
    scheduleReport: "Schedule report",
    scheduleHelp: "Supported: every:15m, every:2h, daily:09:00, weekly:MON@09:00, monthly:15@09:00, quarterly:1@09:00.",
    saveSchedule: "Save schedule",
    saving: "Saving...",
    currentSchedules: "Current schedules",
    noSchedules: "No schedules exist for this company.",
    schedule: "Schedule",
    status: "Status",
    nextRun: "Next run",
    scheduled: "Scheduled"
  },

  pos: {
    title: "Restaurant & Hotel POS",
    flowDescription: "Service outlet → POS terminal → menu → menu item → preparation station (kitchen/bar) → execution screen.",
    offlineCacheNotice: "You are offline. The latest locally cached POS data is being used.",
    loadShiftFailed: "Could not load the cashier shift.",
    createOutletFailed: "Could not create the outlet.",
    assignWarehouseFailed: "Could not link the consumption warehouse.",
    createStationFailed: "Could not create the preparation station.",
    createTerminalFailed: "Could not create the POS terminal.",
    linkMenuFailed: "Could not link the menu to the terminal.",
    routeItemFailed: "Could not route the menu item to the station.",
    selectTerminal: "Select a POS terminal first.",
    openShiftFailed: "Could not open the cashier shift.",
    enterCountedCash: "Enter the counted cash before closing the shift.",
    syncBeforeClose: "Synchronize locally queued orders before closing the shift.",
    closeShiftFailed: "Could not close the shift.",
    companyDateRequired: "Could not get the company date from the server. A sale cannot use the device date.",
    selectMenuItem: "Select a menu item.",
    savedOffline: "The order was saved locally and will sync when the connection returns.",
    connectionSavedOffline: "The server connection failed. The order was saved locally for automatic synchronization.",
    checkoutFailed: "Could not complete the order.",
    loadKdsFailed: "Could not load the kitchen/bar display.",
    updateOrderFailed: "Could not update the order status.",
    tabs: { sale: "Sale", setup: "Outlet & Device Setup", kds: "Kitchen / Bar" },
    createOutlet: "Add Service Outlet",
    assignWarehouse: "Link Consumption Warehouse",
    createStation: "Add Preparation Station",
    createTerminal: "Link POS Terminal to Outlet",
    linkMenu: "Link Menu and Pricing to Terminal",
    routeItem: "Set Item Preparation Station",
    addOutlet: "Add Outlet",
    saveWarehouse: "Save Consumption Warehouse",
    addStation: "Add Station and Link Outlet",
    addTerminal: "Add Terminal",
    saveMenuLink: "Link Menu",
    saveRouting: "Save Routing",
    cashierShift: "Cashier Shift & Cash Reconciliation",
    selectTerminalHint: "Select a POS terminal to view its shift.",
    openingCash: "Opening cash",
    openShift: "Open Shift",
    countedCash: "Counted cash at closing",
    online: "● Online",
    offline: "● Offline — orders are saved locally",
    pendingSync: "orders waiting to sync"
  },

  hr: {
    activeCompanyRequired: "Select an active company first.",
    loadFailed: "Could not load HR data.",
    attendanceFailed: "Could not record attendance.",
    correctionSubmitFailed: "Could not submit the attendance correction.",
    overtimeSubmitFailed: "Could not submit the overtime request.",
    overtimeDecisionFailed: "Could not decide the overtime request.",
    correctionDecisionFailed: "Could not decide the attendance correction.",
    saveWorkforceFailed: "Could not save the user profile.",
    addEmployeeFailed: "Could not add the employee.",
    saveLeaveBalanceFailed: "Could not save the leave balance.",
    leaveSubmitFailed: "Could not submit the leave request.",
    leaveDecisionFailed: "Could not decide the leave request.",
    title: "Human Resources",
    description: "Employee records, leave balances, and request approval workflows.",
    addEmployee: "Add Employee",
    employeeNumber: "Employee number",
    employeeName: "Employee name",
    basicSalary: "Basic salary",
    saveEmployee: "Save employee",
    setLeaveBalance: "Set leave balance",
    employee: "Employee",
    leaveTypes: { annual: "Annual", sick: "Sick", unpaid: "Unpaid", other: "Other" },
    entitledDays: "Entitled days",
    saveBalance: "Save balance",
    leaveRequest: "Leave request",
    from: "From",
    to: "To",
    daysCount: "Number of days",
    optionalReason: "Reason (optional)",
    submitRequest: "Submit request",
    manualAttendance: "Manual attendance entry",
    manualAttendanceHelp: "Manual entry is available when the company attendance source is set to Manual. Fingerprint and mobile connectors are not connected yet.",
    record: "Record",
    attendanceLog: "Attendance log",
    noAttendance: "No attendance records.",
    requestCorrection: "Request correction",
    correctRecord: "Correct record",
    checkIn: "Check-in",
    checkOut: "Check-out",
    correctionReason: "Correction reason",
    send: "Send",
    cancel: "Cancel",
    correctionRequests: "Attendance correction requests",
    noCorrectionRequests: "No correction requests.",
    proposedCheckIn: "Proposed check-in",
    proposedCheckOut: "Proposed check-out",
    reason: "Reason",
    status: "Status",
    decision: "Decision",
    approve: "Approve",
    reject: "Reject",
    overtimeRequest: "Overtime request",
    overtimeHelp: "Available overtime is calculated from recorded attendance duration minus the company's daily working hours. Pending requests are reserved to prevent requests exceeding recorded hours.",
    attendanceRecord: "Attendance record",
    hours: "Hours",
    overtimeReason: "Overtime reason",
    overtimeRequests: "Overtime requests",
    noRequests: "No requests.",
    leaveBalances: "Leave balances",
    noLeaveBalances: "No leave balances recorded.",
    type: "Type",
    entitled: "Entitled",
    consumed: "Consumed",
    available: "Available",
    leaveRequests: "Leave requests",
    refresh: "Refresh",
    period: "Period",
    days: "Days",
    action: "Action",
    companyUserProfiles: "Company user profiles",
    noCompanyUsers: "No registered users.",
    phone: "Phone",
    address: "Address",
    save: "Save",
    statuses: { pending: "Pending", approved: "Approved", rejected: "Rejected" },
    attendanceSources: { manual: "Manual", fingerprint: "Fingerprint", mobile: "Mobile" }
  },

};

export default enTranslation;