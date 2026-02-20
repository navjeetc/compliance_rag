# Compliance PDF Sources

This document contains links to the compliance PDF files used in this project. The PDFs are stored in Google Drive for easy access and sharing.

## Google Drive Folder

**All PDFs are available in this public folder:**  
https://drive.google.com/drive/folders/1GQM54O5lpZLKA6zmkiUotpd0HESRQ6_U

## PDF Files

### 1. CJIS Security Policy v6.0
- **Filename:** `cjis.pdf`
- **Description:** Criminal Justice Information Services (CJIS) Security Policy
- **Google Drive:** Available in the folder above
- **Local Path:** `data/raw/cjis.pdf`

### 2. SOC 2 Compliance
- **Filename:** `SOC2.pdf`
- **Description:** SOC 2 (Service Organization Control 2) compliance documentation
- **Google Drive:** Available in the folder above
- **Local Path:** `data/raw/SOC2.pdf`

### 3. NIST SP 800-53
- **Filename:** `nist.pdf`
- **Description:** NIST Special Publication 800-53 Revision 5.1 - Security and Privacy Controls
- **Google Drive:** Available in the folder above
- **Local Path:** `data/raw/nist.pdf`

### 4. HIPAA Simplification
- **Filename:** `hipaa.pdf`
- **Description:** HIPAA (Health Insurance Portability and Accountability Act) simplification guide
- **Google Drive:** Available in the folder above
- **Local Path:** `data/raw/hipaa.pdf`

## Setup Instructions

To use these PDFs in the project:

1. Download the PDFs from the Google Drive links above
2. Place them in the `data/raw/` directory
3. Ensure the filenames match exactly as listed above
4. Run the PDF processing pipeline with: `python scripts/03_run_indexing.py --test`

## Notes

- These PDFs are excluded from git via `.gitignore` due to their large file size
- Total size: ~9.8 MB
- Anyone cloning this repository will need to download these PDFs separately from Google Drive
