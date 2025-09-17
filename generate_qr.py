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

def extract_name_from_filename(filename):
    """
    Extract FIRSTNAME_LASTNAME from filename and format as FIRSTNAME LASTNAME
    Handles formats like:
    - Image MATTHEW_TIAN - Big Backs Laurier.HEIC -> MATTHEW TIAN
    - Image TINA_ZHENG - tina zheng.jpg -> TINA ZHENG
    - MATTHEW_TIAN.jpg -> MATTHEW TIAN
    """
    # Remove file extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Look for pattern FIRSTNAME_LASTNAME in the filename
    import re
    
    # Pattern to match FIRSTNAME_LASTNAME (uppercase letters separated by underscore)
    pattern = r'([A-Z]+)_([A-Z]+)'
    match = re.search(pattern, name_without_ext)
    
    if match:
        first_name = match.group(1)
        last_name = match.group(2)
        return f"{first_name} {last_name}"
    
    # If no pattern found, return the original name (fallback)
    return name_without_ext

# Process images
for filename in os.listdir(IMAGES_FOLDER):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
        continue

    name = os.path.splitext(filename)[0]
    display_name = extract_name_from_filename(filename)
    local_path = os.path.join(IMAGES_FOLDER, filename)
    ext = filename.split('.')[-1].lower()

    # Skip if QR already exists
    qr_path = os.path.join(OUTPUT_FOLDER, f"{name}_qr.png")
    page_key = f"{name}.html"
    page_url = f"{CLOUDFRONT_URL}/{page_key}"

    # -- HEIC Conversion & delete original --
    if ext == 'heic':
        try:
            heif_file = pillow_heif.read_heif(local_path)
            image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            # Save back into images folder as JPG
            new_filename = f"{name}.jpg"
            new_path = os.path.join(IMAGES_FOLDER, new_filename)
            image.save(new_path, format='JPEG')
            os.remove(local_path)
            print(f"✔ Converted {filename} → {new_filename} and deleted original HEIC")
            filename = new_filename
            local_path = new_path
            ext = 'jpg'
        except Exception as e:
            print(f"⚠ Skipping {filename}: cannot read HEIC ({e})")
            continue

    # Determine content type
    content_type = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
    s3_image_key = f"images/{filename}"

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

    # Create member HTML page with animations, oval image, logo, fade-in, spinning glow
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{display_name}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    body {{
        font-family: 'Arial', sans-serif;
        background-color: #fdfbee;
        margin: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        min-height: 100vh;
        text-align: center;
        padding: 20px;
        opacity: 0;
        animation: fadeIn 1.5s forwards;
    }}

    @keyframes fadeIn {{
        to {{ opacity: 1; }}
    }}

    .logo {{
        width: 160px;
        margin-bottom: 20px;
        opacity: 0;
        animation: fadeIn 1.5s forwards 0.3s;
    }}

    .header-text {{
        font-size: 5vw;
        color: #555;
        font-weight: bold;
        margin-bottom: 0.5em;
        letter-spacing: 2px;
        opacity: 0;
        animation: fadeIn 1.5s forwards 0.6s;
    }}

    h1 {{
        font-size: 7vw;  /* slightly smaller */
        margin-bottom: 1em;
        color: #222;
        opacity: 0;
        animation: fadeIn 1.5s forwards 0.9s;
    }}

     .profile {{
         width: 90vw;
         max-width: 400px;
         height: auto;
         border-radius: 50% / 35%; /* Oval shape */
         box-shadow: 
             0 0 20px 0 rgba(212, 175, 55, 0.4),
             0 0 40px 0 rgba(184, 134, 11, 0.3),
             0 0 60px 0 rgba(218, 165, 32, 0.2),
             0 0 80px 0 rgba(205, 133, 63, 0.1);
         animation: fadeIn 1.5s forwards 1.2s;
         position: relative;
     }}

     .profile::before {{
         content: '';
         position: absolute;
         top: -20px;
         left: -20px;
         right: -20px;
         bottom: -20px;
         border-radius: 50% / 35%;
         background: conic-gradient(
             from 0deg,
             rgba(212, 175, 55, 0.1),
             rgba(184, 134, 11, 0.15),
             rgba(218, 165, 32, 0.1),
             rgba(205, 133, 63, 0.15),
             rgba(222, 184, 135, 0.1),
             rgba(212, 175, 55, 0.1)
         );
         filter: blur(15px);
         z-index: -1;
         animation: breatheGlowInner 4s ease-in-out infinite;
     }}

     .profile::after {{
         content: '';
         position: absolute;
         top: -40px;
         left: -40px;
         right: -40px;
         bottom: -40px;
         border-radius: 50% / 35%;
         background: conic-gradient(
             from 0deg,
             rgba(212, 175, 55, 0.05),
             rgba(184, 134, 11, 0.08),
             rgba(218, 165, 32, 0.05),
             rgba(205, 133, 63, 0.08),
             rgba(222, 184, 135, 0.05),
             rgba(212, 175, 55, 0.05)
         );
         filter: blur(30px);
         z-index: -2;
         animation: breatheGlowOuter 4s ease-in-out infinite 0.5s;
     }}

     @keyframes breatheGlowInner {{
         0%, 100% {{ 
             top: -20px;
             left: -20px;
             right: -20px;
             bottom: -20px;
             opacity: 0.3;
             filter: blur(15px);
         }}
         50% {{ 
             top: -30px;
             left: -30px;
             right: -30px;
             bottom: -30px;
             opacity: 0.6;
             filter: blur(25px);
         }}
     }}

     @keyframes breatheGlowOuter {{
         0%, 100% {{ 
             top: -40px;
             left: -40px;
             right: -40px;
             bottom: -40px;
             opacity: 0.2;
             filter: blur(30px);
         }}
         50% {{ 
             top: -60px;
             left: -60px;
             right: -60px;
             bottom: -60px;
             opacity: 0.4;
             filter: blur(50px);
         }}
     }}
</style>
</head>
<body>
    <img src="https://{PAGES_BUCKET}.s3.{REGION}.amazonaws.com/bigbackcircle.png" class="logo" alt="Big Backs Club Logo"/>
    <div class="header-text">MEMBER OF BIG BACKS CLUB</div>
    <h1>{display_name}</h1>
    <img class="profile" src="{image_url}" alt="{display_name}'s photo"/>
</body>
</html>"""

    # Upload member page to S3
    s3.put_object(
        Bucket=PAGES_BUCKET,
        Key=page_key,
        Body=html_content,
        ContentType='text/html'
    )

    # Generate QR code if it doesn't exist
    if not os.path.exists(qr_path):
        qr = qrcode.make(page_url)
        qr.save(qr_path)
        print(f"✅ Uploaded '{display_name}' image, created page, and QR code: {page_url}")
    else:
        print(f"ℹ QR code already exists for {display_name}, HTML page updated")

    # Save for index.html
    member_pages.append((display_name, page_url))

# Generate index.html with all members
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
index_content += "</ul>\n</body>\n</html>"

# Upload index.html to public bucket
s3.put_object(
    Bucket=PAGES_BUCKET,
    Key="index.html",
    Body=index_content,
    ContentType='text/html'
)

print("✅ Uploaded index.html with all members")
print(f"✅ All QR codes and converted images saved to '{OUTPUT_FOLDER}'")
