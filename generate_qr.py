import os
import boto3
import qrcode
from PIL import Image
import pillow_heif
from dotenv import load_dotenv

# ----------------- CONFIG -----------------
load_dotenv()  # Load .env file with credentials and URLs

IMAGES_FOLDER = "./images"
OUTPUT_FOLDER = "./output"
IMAGES_BUCKET = os.getenv("IMAGES_BUCKET")
PAGES_BUCKET = os.getenv("PAGES_BUCKET")
REGION = os.getenv("REGION")
CLOUDFRONT_URL = os.getenv("CLOUDFRONT_URL")
# ------------------------------------------

# Initialize S3 client
s3 = boto3.client('s3', region_name=REGION)

# Ensure folders exist
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)
    print(f"Folder '{IMAGES_FOLDER}' created. Add images and rerun script.")
    exit()

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Keep track of member pages for index.html
member_pages = []

# Process images
for filename in os.listdir(IMAGES_FOLDER):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
        continue

    name = os.path.splitext(filename)[0]
    local_path = os.path.join(IMAGES_FOLDER, filename)
    ext = filename.split('.')[-1].lower()

    # Skip if QR already exists
    qr_path = os.path.join(OUTPUT_FOLDER, f"{name}_qr.png")
    page_key = f"{name}.html"
    page_url = f"{CLOUDFRONT_URL}/{page_key}"
    if os.path.exists(qr_path):
        print(f"ℹ QR code already exists for {name}, skipping generation")
        member_pages.append((name, page_url))
        continue

    # Handle HEIC safely
    if ext == 'heic':
        try:
            heif_file = pillow_heif.read_heif(local_path)
            image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            temp_path = os.path.join(OUTPUT_FOLDER, f"{name}.jpg")
            image.save(temp_path, format='JPEG')
            local_path = temp_path
            content_type = 'image/jpeg'
            s3_image_key = f"images/{os.path.basename(temp_path)}"
        except Exception as e:
            print(f"⚠ Skipping {filename}: cannot read HEIC ({e})")
            continue
    else:
        s3_image_key = f"images/{filename}"
        content_type = 'image/jpeg' if ext in ['jpg','jpeg'] else 'image/png'

    # Upload image to S3
    with open(local_path, "rb") as f:
        s3.put_object(
            Bucket=IMAGES_BUCKET,
            Key=s3_image_key,
            Body=f,
            ContentType=content_type
        )

    # Generate pre-signed URL
    image_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': IMAGES_BUCKET, 'Key': s3_image_key},
        ExpiresIn=31536000
    )

    # Create HTML page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{name}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            height: 100vh;
            text-align: center;
        }}
        .header-text {{
            font-size: 5vw;
            color: #777;
            margin-bottom: 1em;
            letter-spacing: 1px;
        }}
        h1 {{
            font-size: 8vw;
            margin-bottom: 1em;
            color: #333;
        }}
        img {{
            width: 90vw;
            max-width: 500px;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="header-text">MEMBER OF BIG BACKS CLUB</div>
    <h1>{name}</h1>
    <img src="{image_url}" alt="{name}'s photo"/>
</body>
</html>"""

    s3.put_object(
        Bucket=PAGES_BUCKET,
        Key=page_key,
        Body=html_content,
        ContentType='text/html'
    )

    # Generate QR code
    qr = qrcode.make(page_url)
    qr.save(qr_path)
    print(f"✅ Uploaded '{name}' image, created page, and QR code: {page_url}")

    # Save for index.html
    member_pages.append((name, page_url))

# Generate index.html
index_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Big Backs Club Members</title>
<style>
body {{ font-family:'Arial',sans-serif; background-color:#f5f5f5; text-align:center; padding:50px; }}
h1 {{ color:#333; }}
ul {{ list-style:none; padding:0; }}
li {{ margin:15px 0; }}
a {{ text-decoration:none; color:#0073e6; font-size:18px; }}
a:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
<h1>Big Backs Club Members</h1>
<ul>
"""

for name, url in member_pages:
    index_content += f'    <li><a href="{url}" target="_blank">{name}</a></li>\n'

index_content += """</ul>
</body>
</html>"""

s3.put_object(
    Bucket=PAGES_BUCKET,
    Key="index.html",
    Body=index_content,
    ContentType='text/html'
)

print("✅ Uploaded index.html with all members")
print(f"✅ All QR codes and temp files saved to '{OUTPUT_FOLDER}'")
