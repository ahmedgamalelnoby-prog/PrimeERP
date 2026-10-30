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
};

export default enTranslation;