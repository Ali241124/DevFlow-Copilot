
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("data/evaluation_images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1000, 700
BACKGROUND = "#F4F6F8"
DARK = "#202B3C"
BLUE = "#2563EB"
WHITE = "#FFFFFF"
GREY = "#64748B"
BORDER = "#D8DEE8"
GREEN = "#16A34A"


def get_font(size=20, bold=False):
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf",
         "C:/Windows/Fonts/segoeui.ttf"]
        if bold else
        ["C:/Windows/Fonts/arial.ttf",
         "C:/Windows/Fonts/segoeui.ttf"]
    )

    for font_path in candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


def create_page(title, subtitle):
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 85), fill=WHITE)
    draw.text((45, 25), "DEVFLOW DEMO", fill=BLUE, font=get_font(25, True))
    draw.text((45, 125), title, fill=DARK, font=get_font(34, True))
    draw.text((45, 175), subtitle, fill=GREY, font=get_font(19))

    return image, draw


def draw_field(draw, x, y, label, placeholder):
    draw.text((x, y), label, fill=DARK, font=get_font(18, True))
    draw.rounded_rectangle(
        (x, y + 32, x + 410, y + 83),
        radius=8,
        fill=WHITE,
        outline=BORDER,
        width=2
    )
    draw.text(
        (x + 15, y + 46),
        placeholder,
        fill=GREY,
        font=get_font(17)
    )


def draw_button(draw, x, y, text, width=410):
    draw.rounded_rectangle(
        (x, y, x + width, y + 55),
        radius=8,
        fill=BLUE
    )
    draw.text(
        (x + 20, y + 13),
        text,
        fill=WHITE,
        font=get_font(19, True)
    )


def save(image, filename):
    image.save(OUTPUT_DIR / filename)
    print(f"Created: {filename}")


# IMG-001: Login page
image, draw = create_page(
    "Welcome back",
    "Sign in to access your account."
)

draw_field(draw, 45, 245, "Email address", "Enter your email")
draw_field(draw, 45, 365, "Password", "Enter your password")
draw_button(draw, 45, 490, "Login")

draw.text(
    (45, 570),
    "Forgot password?",
    fill=BLUE,
    font=get_font(17)
)
draw.text(
    (45, 615),
    "Don't have an account? Sign up",
    fill=DARK,
    font=get_font(17)
)

save(image, "IMG-001-login.png")


# IMG-002: Registration page
image, draw = create_page(
    "Create your account",
    "Register to get started."
)

draw_field(draw, 45, 220, "Full name", "Enter your full name")
draw_field(draw, 45, 330, "Email address", "Enter your email")
draw_field(draw, 45, 440, "Password", "Create a password")
draw_button(draw, 45, 555, "Create account")

save(image, "IMG-002-registration.png")


# IMG-003: Task dashboard
image, draw = create_page(
    "My Tasks",
    "Manage and track your daily work."
)

draw_button(draw, 650, 120, "+ Create Task", width=300)

tasks = [
    ("Design homepage", "In Progress"),
    ("Fix login validation", "Pending"),
    ("Write API tests", "Completed"),
    ("Prepare documentation", "Pending")
]

for index, (task, status) in enumerate(tasks):
    y = 235 + index * 95

    draw.rounded_rectangle(
        (45, y, 950, y + 70),
        radius=9,
        fill=WHITE,
        outline=BORDER
    )

    draw.text(
        (70, y + 20),
        task,
        fill=DARK,
        font=get_font(20, True)
    )

    draw.text(
        (680, y + 22),
        status,
        fill=GREEN if status == "Completed" else BLUE,
        font=get_font(18)
    )

save(image, "IMG-003-task-dashboard.png")


# IMG-004: Shopping cart
image, draw = create_page(
    "Shopping Cart",
    "Review your items before checkout."
)

products = [
    ("Wireless Headphones", "$45.00", "Quantity: 1"),
    ("USB Keyboard", "$30.00", "Quantity: 2"),
    ("Laptop Stand", "$25.00", "Quantity: 1")
]

for index, (name, price, quantity) in enumerate(products):
    y = 235 + index * 110

    draw.rounded_rectangle(
        (45, y, 950, y + 85),
        radius=9,
        fill=WHITE,
        outline=BORDER
    )

    draw.text((70, y + 12), name, fill=DARK, font=get_font(20, True))
    draw.text((70, y + 48), quantity, fill=GREY, font=get_font(16))
    draw.text((760, y + 25), price, fill=DARK, font=get_font(20, True))

draw.text(
    (620, 590),
    "Total: $130.00",
    fill=DARK,
    font=get_font(25, True)
)
draw_button(draw, 45, 625, "Proceed to Checkout", width=410)

save(image, "IMG-004-shopping-cart.png")


# IMG-005: Expense dashboard
image, draw = create_page(
    "Expense Dashboard",
    "Overview of your spending."
)

draw.rounded_rectangle(
    (45, 230, 950, 355),
    radius=12,
    fill=WHITE,
    outline=BORDER
)

draw.text(
    (75, 255),
    "Total Spending",
    fill=GREY,
    font=get_font(20)
)
draw.text(
    (75, 295),
    "$1,250.00",
    fill=DARK,
    font=get_font(34, True)
)

categories = [
    ("Food", "$450.00"),
    ("Transport", "$200.00"),
    ("Shopping", "$400.00"),
    ("Bills", "$200.00")
]

draw.text(
    (45, 395),
    "Spending by Category",
    fill=DARK,
    font=get_font(24, True)
)

for index, (category, amount) in enumerate(categories):
    x = 45 + (index % 2) * 460
    y = 445 + (index // 2) * 95

    draw.rounded_rectangle(
        (x, y, x + 420, y + 65),
        radius=8,
        fill=WHITE,
        outline=BORDER
    )

    draw.text((x + 18, y + 18), category, fill=DARK, font=get_font(18))
    draw.text((x + 280, y + 18), amount, fill=BLUE, font=get_font(18, True))

save(image, "IMG-005-expense-dashboard.png")

print("\nAll five evaluation screenshots generated.")
