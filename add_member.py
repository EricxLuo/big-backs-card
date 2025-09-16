import json
import os
import qrcode

# CONFIG
REPO_URL = "https://yourusername.github.io/big-backs-club"  # <-- change to your GitHub Pages URL
MEMBERS_FILE = "members.json"
IMAGES_DIR = "images"
QRCODES_DIR = "qrcodes"

def add_member(member_id, name, image_filename):
    """Add a member to members.json and generate QR code."""

    # Ensure folders exist
    os.makedirs(QRCODES_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Load members.json (or create if missing)
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, "r", encoding="utf-8") as f:
            members = json.load(f)
    else:
        members = []

    # Check for duplicate ID
    if any(m["id"] == str(member_id) for m in members):
        print(f"❌ Member with id={member_id} already exists.")
        return

    # Add new member
    new_member = {
        "id": str(member_id),
        "name": name,
        "imageUrl": f"{IMAGES_DIR}/{image_filename}"
    }
    members.append(new_member)

    # Save back to JSON
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, indent=2, ensure_ascii=False)

    # Generate QR code URL
    profile_url = f"{REPO_URL}/profile.html?id={member_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(profile_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_filename = os.path.join(QRCODES_DIR, f"{member_id}.png")
    img.save(qr_filename)

    print(f"\n✅ Added {name} (id={member_id})")
    print(f"   Image: {IMAGES_DIR}/{image_filename}")
    print(f"   Profile URL: {profile_url}")
    print(f"   QR Code saved to {qr_filename}\n")


if __name__ == "__main__":
    while True:
        print("➕ Add a new member (or press Enter to quit)\n")

        member_id = input("Enter ID (number): ").strip()
        if not member_id:
            break

        name = input("Enter name: ").strip()
        image_filename = input(f"Enter image filename (place inside '{IMAGES_DIR}/'): ").strip()

        add_member(member_id, name, image_filename)

