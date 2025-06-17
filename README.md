# Library Management System

## Overview
This project is a robust Library Management System built with Python and Tkinter, offering an intuitive graphical interface. It caters to both administrators and readers, facilitating tasks such as user management, document handling, borrowing/returning processes, fine management, and statistical reporting with visual charts.

## Project Structure
```
LIBRARY/
├── assets/
│   └── logo.jpg
├── build_main/
│   └── data/
│       ├── borrow_records.json
│       ├── borrowing_logs.json
│       ├── document_categories.json
│       ├── document_logs.json
│       ├── document_requests.json
│       ├── documents.json
│       ├── library_rules.json
│       ├── reader_logs.json
│       ├── reader_types.json
│       ├── return_records.json
│       └── users.json
├── dist/
│   └── main.exe
├── src/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── borrowing_manager.py
│   ├── config.py
│   ├── document_manager.py
│   ├── library_system.py
│   ├── login_register.py
│   ├── reader_manager.py
│   └── main.py
├── main.spec
└── requirements.txt
```

### Directory and File Descriptions
- **`assets/`**: Holds static files, including the `logo.jpg` image.
- **`build_main/`**: Contains compiled outputs and data.
  - **`data/`**: Directory for JSON data files managing library records (e.g., borrow records, documents, users).
- **`dist/`**: Includes the executable `main.exe` for direct application launch.
- **`src/`**: Source code directory.
  - **`__init__.py`**: Package initialization file.
  - **`borrowing_manager.py`**: Handles borrowing and returning logic.
  - **`config.py`**: Configuration settings file.
  - **`document_manager.py`**: Manages document-related functionalities.
  - **`library_system.py`**: Main system logic and GUI implementation.
  - **`login_register.py`**: Manages user authentication and registration.
  - **`reader_manager.py`**: Oversees reader management operations.
  - **`main.py`**: Application entry point.
- **`main.spec`**: PyInstaller configuration for building the executable.
- **`requirements.txt`**: Lists Python package dependencies.

## Features
- **Authentication**: Secure login and registration with role-based access (admin/reader).
- **Reader Management**: Search, renew, suspend, delete, and update reader details.
- **Document Management**: Search, list, and manage library documents.
- **Borrowing/Returning**: Record and track borrow/return transactions.
- **Fine Handling**: View and process fine payments.
- **Statistics**: Generate reports on documents, borrowers, reader types, and fines with graphical representations.
- **Library Rules**: Display and update rules retrieved from an online source.

## Prerequisites
- Python 3.x
- Required packages (install via):
  ```
  pip install -r requirements.txt
  ```

## Installation
1. Clone or download the repository.
2. Change to the project directory:
   ```
   cd LIBRARY
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Launch the application:
   ```
   python src/main.py
   ```
   Alternatively, use the pre-built `main.exe` in `dist/`.

## Usage
- **Admin**: Access full management features (reader, document, borrowing, statistics).
- **Reader**: Manage personal profile, search documents, borrow/return items, and handle fines.
- Use the sidebar menu to navigate the GUI.

## Configuration
- Modify `config.py` to adjust file paths or settings (e.g., `readers_file`, `documents_file`).

## Contributing
Contributions are encouraged! Fork the repository and submit pull requests for improvements or bug fixes.

## License
Distributed under the MIT License. Refer to the `LICENSE` file for more details (if included).

## Contact
For support or issues, please create an issue on the repository or reach out to the maintainers.