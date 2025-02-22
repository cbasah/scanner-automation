from datetime import datetime
import img2pdf
import os
import sane
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def set_default_scanner(sane):
    # Get all available devices
    devices = sane.get_devices()
    print("Available scanners:")
    for i, device in enumerate(devices):
        print(f"{i + 1}. {device[0]} ({device[1]})")

    # Select default scanner
    choice2 = int(input("Select a scanner: "))
    scanner_name = devices[choice2 - 1][0]
    update_config_file("SANE_DEFAULT_DEVICE", scanner_name)
    print(f"Default scanner set to {devices[choice2 - 1][1]}")


def get_default_scanner(sane):
    # Get default scanner
    scanner_name = get_config_from_file("SANE_DEFAULT_DEVICE")
    if scanner_name:
        devices = sane.get_devices()
        for i, device in enumerate(devices):
            if device[0] == scanner_name:
                return sane.open(device[0])

    return None


def get_scan_size():
    # return scan size in mm
    choice = 0

    while choice not in [1, 2, 3, 4]:
        print("Select scan size:")
        print("1. A4")
        print("2. A5")
        print("3. A6")
        print("4. Shell Malaysia Receipt")
        choice = int(input("Enter your choice: "))

        if choice == 1:
            return 210, 297
        elif choice == 2:
            return 148, 210
        elif choice == 3:
            return 105, 148
        elif choice == 4:
            return 60, 190
        else:
            print("Invalid choice. Try again.")


def set_email_config():
    email_recipient = input("Enter email recipient: ")
    update_config_file("EMAIL_RECIPIENT", email_recipient)

    email_sender = input("Enter email sender: ")
    update_config_file("EMAIL_SENDER", email_sender)

    smtp_server = input("Enter SMTP server: ")
    update_config_file("SMTP_SERVER", smtp_server)

    smtp_port = input("Enter SMTP TLS port: ")
    update_config_file("SMTP_TLS_PORT", smtp_port)

    smtp_username = input("Enter SMTP username: ")
    update_config_file("SMTP_USERNAME", smtp_username)

    smtp_password = input("Enter SMTP password: ")
    update_config_file("SMTP_PASSWORD", smtp_password)


def update_config_file(key, value):
    config = {}
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)
    config[key] = value
    with open("config.json", "w") as f:
        json.dump(config, f)


def get_config_from_file(key):
    with open("config.json", "r") as f:
        config = json.load(f)

    return config.get(key)


def get_filename_prefix():
    return input("Enter filename prefix: ")


def send_attachment(pdf_path):
    # Get email settings from config file
    email_sender = get_config_from_file("EMAIL_SENDER")
    email_recipient = get_config_from_file("EMAIL_RECIPIENT")
    smtp_server = get_config_from_file("SMTP_SERVER")
    smtp_port = get_config_from_file("SMTP_TLS_PORT")
    smtp_username = get_config_from_file("SMTP_USERNAME")
    smtp_password = get_config_from_file("SMTP_PASSWORD")

    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = email_recipient
    message["Subject"] = "Scanned Document"

    # Attach the PDF file
    with open(pdf_path, "rb") as attachment:
        part = MIMEBase("application", "pdf")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {pdf_path}",
        )
        message.attach(part)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

    print(f"Email with {pdf_path} attached sent successfully to {email_recipient}")


def start_scanning_session(sane):
    # Select first available scanner
    scanner = get_default_scanner(sane)
    if not scanner:
        print("No scanner selected. Exiting...")
        return

    scanner.mode = "color"
    scanner.resolution = 300

    (width, height) = get_scan_size()
    scanner.br_x = width
    scanner.br_y = height

    # Get filename prefix
    filename_prefix = get_filename_prefix()
    total_files_scanned = 0

    choice = None
    while choice != "e":
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp_str}"

        # Start scanning
        print("Scanning document...")
        image = scanner.scan()

        # Save as image first (optional)
        image_path = f"{filename}.jpg"
        image.save(image_path, "JPEG")

        # Convert to PDF
        pdf_path = f"{filename}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_path))

        # Clean up (optional)
        os.remove(image_path)

        # Send PDF file as email attachment
        send_attachment(pdf_path)

        print(f"Scan complete. Saved as {pdf_path}")
        total_files_scanned += 1

        print("Press 'e' to complete scanning session or "
              "any other key to continue scanning.")
        choice = input("Enter your choice: ").lower()

    print(f"Total files scanned: {total_files_scanned}")
    scanner.close()
    sane.exit()


def run():
    # Initialize SANE
    sane.init()
    choice1 = 0

    while choice1 not in [3, 4]:
        print("Selection an option:")
        print("1. Set default scanner")
        print("2. Set email configuration")
        print("3. Start a scanning session")
        print("4. Exit")
        choice1 = int(input("Enter your choice: "))

        if choice1 == 1:
            set_default_scanner(sane)
        elif choice1 == 2:
            set_email_config()
        elif choice1 == 3:
            start_scanning_session(sane)

    sane.exit()
    print("Exiting...")


run()
