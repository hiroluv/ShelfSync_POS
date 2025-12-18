/ShelfSync
│
├── /assets
│   ├── logo.png
│   └── icons/
│
├── /views               # THE "VIEW" (UI Files)
│   ├── login_windows.ui
│   ├── dashboard_window.ui
│   ├── inventory_window.ui
│   ├── cashier_window.ui
│   ├── reports_window.ui
│   ├── user_accounts_window.ui
│   ├── perishables_window.ui
│   ├── item_sale.ui             # Row widget for Sales list
│   ├── item_user.ui             # Row widget for User list
│   ├── add_stock_dialog.ui      # Popup for Inventory
│   └── add_user_dialog.ui       # Popup for Adding Users
│
├── /controllers         # THE "CONTROLLER" (Logic)
│   ├── __init__.py
│   ├── main_controller.py
│   ├── login_controller.py
│   ├── dashboard_controller.py
│   ├── inventory_controller.py
│   ├── cashier_controller.py
│   ├── reports_controller.py
│   └── users_controller.py      # Handles User UI logic
│
├── /models              # THE "MODEL" (Data & Logic)
│   ├── __init__.py
│   ├── database_manager.py      # The central connection hub (Delegator)
│   ├── db_manager.py            # Manager SQL (Users, Inventory, Audit Logs)
│   ├── db_cashier.py            # Cashier SQL (Products, Transactions)
│   ├── user_model.py            # Business Logic (Password Hashing & Verification)
│   └── entities.py              # Data Classes (User, InventoryItem object definitions)
│
├── /utils               # HELPER SCRIPTS
│   ├── ui_helper.py             # Shadows, overlays, and icon helpers
│   └── toast_notification.py    # Custom popup notifications
│
└── main.py              # Entry point (AppOrchestrator)