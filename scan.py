import os
import sane
import img2pdf
from PIL import Image

# Initialize SANE
sane.init()
devices = sane.get_devices()
if not devices:
    print("No scanner found.")
    exit(1)

# Select first available scanner
scanner = sane.open(devices[2][0])
scanner.mode = "Color"  # Use "Color" if needed
scanner.resolution = 300  # Set DPI
scanner.br_x = 210  # Width (A4: 210mm)
scanner.br_y = 297  # Height (A4: 297mm)

# Start scanning
print("Scanning document...")
image = scanner.scan()
scanner.close()
sane.exit()

# Save as image first (optional)
image_path = "scanned_document.jpg"
image.save(image_path, "JPEG")

# Convert to PDF
pdf_path = "scanned_document.pdf"
with open(pdf_path, "wb") as f:
    f.write(img2pdf.convert(image_path))

# Clean up (optional)
os.remove(image_path)

print(f"Scan complete. Saved as {pdf_path}")
