# Android Media Backup

A web application for backing up media files (photos and videos) from Android devices via ADB.

## Features

1. Scan and list media files from your Android device
2. Select files by date range or manually
3. Backup selected files to your computer
4. View backed up files
5. Optionally delete original files from device after backup

## Prerequisites

- Python 3.7+
- Node.js and npm
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed

## Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Node.js dependencies:
   ```
   cd web
   npm install
   ```

## Usage

1. Connect your Android device via USB and enable USB debugging

2. Run the application:
   ```
   python main.py
   ```

3. The application will automatically:
   - Start the backend server on port 5000
   - Start the frontend development server on port 8080
   - Open your browser to http://localhost:8080

## How It Works

### Step 1: Scan Media Files
- The application scans `/sdcard/DCIM/Camera` by default
- Files are sorted by size (largest first)
- You can select files by date range or manually

### Step 2: Backup Selected Files
- Choose a destination directory on your computer
- Files are copied from your device to your computer
- Progress is displayed during the copy process

### Step 3: View Local Files
- View all backed up files in the web interface
- See file details like size and modification date

### Step 4: Delete Original Files (Optional)
- After confirming successful backup, you can delete the original files from your device

## Technical Details

- Backend: Python with Flask
- Frontend: Vue3 with Element Plus UI components
- Communication: REST API between frontend and backend
- ADB: Used to communicate with Android device

## Logging

All backup operations are logged to `backup_log.json` for reference.

## Troubleshooting

1. If ADB is not found, make sure it's in your PATH or in the `adb/` directory
2. If the device is not recognized, check that USB debugging is enabled
3. Make sure only one device is connected when running the application