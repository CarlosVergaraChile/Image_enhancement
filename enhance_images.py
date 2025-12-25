# Google Drive Image Enhancement and Upload Script
# Batch processes images with contrast, sharpness, brightness, and color enhancements

from google.colab import auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image, ImageEnhance
from io import BytesIO
from tqdm import tqdm

print("\n" + "="*80)
print("IMAGE ENHANCEMENT AND UPLOAD PROCESS")
print("="*80 + "\n")

# Authenticate with Google Drive
print("Authenticating with Google Drive...")
auth.authenticate_user()
drive_service = build('drive', 'v3')
print("✓ Authentication successful\n")

# Define folder IDs
SOURCE_FOLDER_ID = '1I9OB6hrpFP_8LqIEE2OWLXmO7g9mxwFn'  # Source images folder
TARGET_FOLDER_ID = '1CNn5aN3LFoUbSsCao8ai5n2Y8TUsBji2'  # images_enhanced_photoroom

print(f"Source folder ID: {SOURCE_FOLDER_ID}")
print(f"Target folder ID: {TARGET_FOLDER_ID}\n")

# Get all image files from source folder
print("Retrieving list of images from source folder...")
results = drive_service.files().list(
    q=f"'{SOURCE_FOLDER_ID}' in parents and trashed=false",
    pageSize=1000,
    fields='files(id, name, mimeType)'
).execute()

all_files = results.get('files', [])
print(f"Total files found: {len(all_files)}")

# Filter for image files only
image_mimetypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
image_files = [f for f in all_files if f.get('mimeType', '') in image_mimetypes]

print(f"Image files to process: {len(image_files)}")

if len(image_files) == 0:
    print("\n⚠ WARNING: No image files found!")
else:
    print(f"\n{'='*80}")
    print(f"Starting enhancement process for {len(image_files)} images")
    print(f"{'='*80}\n")
    
    processed = 0
    failed = 0
    failed_files = []
    
    for file_info in tqdm(image_files, desc="Processing images"):
        try:
            file_id = file_info['id']
            file_name = file_info['name']
            mime_type = file_info.get('mimeType', 'image/jpeg')
            
            # Download image
            req = drive_service.files().get_media(fileId=file_id)
            img_bytes = req.execute()
            
            # Open image with PIL
            img = Image.open(BytesIO(img_bytes))
            
            # Apply enhancements
            img = ImageEnhance.Contrast(img).enhance(1.3)      # +30% contrast
            img = ImageEnhance.Sharpness(img).enhance(1.5)     # +50% sharpness
            img = ImageEnhance.Brightness(img).enhance(1.1)    # +10% brightness
            
            if img.mode != 'CMYK':
                img = ImageEnhance.Color(img).enhance(1.2)     # +20% color saturation
            
            # Save enhanced image to bytes
            output = BytesIO()
            fmt = img.format or 'JPEG'
            img.save(output, format=fmt)
            output.seek(0)
            
            # Upload to target folder
            media = MediaIoBaseUpload(output, mimetype=mime_type, resumable=True)
            drive_service.files().create(
                body={
                    'name': file_name,
                    'parents': [TARGET_FOLDER_ID]
                },
                media_body=media
            ).execute()
            
            processed += 1
            
        except Exception as e:
            failed += 1
            fname = file_name if 'file_name' in locals() else 'Unknown'
            failed_files.append((fname, str(e)))
            tqdm.write(f"  Error processing {file_info['name']}: {e}")
    
    print(f"\n{'='*80}")
    print("PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults:")
    print(f"  ✓ Successfully processed: {processed} images")
    print(f"  ✗ Failed: {failed} images")
    print(f"  Total: {processed + failed}/{len(image_files)} images")
    
    if failed > 0:
        print(f"\nFailed files:")
        for fname, error in failed_files:
            print(f"  - {fname}: {error}")
    
    print(f"\nAll enhanced images have been saved to the target folder.")
    print(f"{'='*80}\n")
