/ShelfSync
│
├── /assets              # (Optional) Store your logos/icons here
│   ├── logo.png
│   └── icons/
│
├── /views               # THE "VIEW" (All your .ui files)
│   ├── login_windows.ui         # The starting point
│   ├── dashboard_window.ui      # The Main Shell (Sidebar + Stack)
│   ├── inventory_window.ui      # Inventory Page
│   ├── item_sale.ui             # <-- The Single Row Widget for Dashboard
│   ├── cashier_window.ui        # Cashier Interface
│   ├── perishables_window.ui    # FIFO Tracking Page
│   ├── reports_window.ui        # Analytics Page
│   ├── user_accounts_window.ui  # User Management Page
│   └── add_stock_dialog.ui      # Popup for adding items
│
├── /controllers         # THE "CONTROLLER" (Python Logic)
│   ├── __init__.py
│   ├── main_controller.py       # Manages the Window Stack & Sidebar Navigation
│   ├── login_controller.py      # Handles Auth & Switch between Manager/Cashier
│   ├── dashboard_controller.py  # Calculates Revenue, Stock Alerts & Populates List
│   ├── inventory_controller.py  # Handles Table logic & "Add Stock" Dialog
│   ├── cashier_controller.py    # Handles Search, Cart, & Checkout logic
│   ├── perishables_controller.py# Handles Expiry Dates & Batch logic
│   ├── reports_controller.py    # Generates Charts & Financial Math
│   └── users_controller.py      # Handles Adding/Removing Users
│
├── /models              # THE "MODEL" (Database Code)
│   ├── __init__.py
│   └── database_manager.py      # All SQL queries (SELECT, INSERT, UPDATE) go here
│
└── main.py              # Entry point (Run this file)