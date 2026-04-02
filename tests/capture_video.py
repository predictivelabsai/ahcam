"""
Capture Product Demo Video

Playwright script that walks through the entire AHCAM platform,
capturing frames for an animated GIF and MP4 video.

Usage:
    python app.py &
    python tests/capture_video.py

Output:
    docs/demo_video.mp4
    docs/demo_video.gif
    docs/frames/*.png
"""

import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
FRAMES_DIR = ROOT / "docs" / "frames"
BASE_URL = "http://localhost:5011"
EMAIL = "demo@ashlandhill.com"
PASSWORD = "demo1234"

frame_num = 0


async def capture(page, label, pause=1.0):
    """Capture a frame with a pause for natural pacing."""
    global frame_num
    await asyncio.sleep(pause)
    path = FRAMES_DIR / f"{frame_num:03d}_{label}.png"
    await page.screenshot(path=str(path), type="png")
    print(f"  [{frame_num:03d}] {label}")
    frame_num += 1


async def nav_module(page, path, title, pause=0.8):
    """Navigate to a module via JS (avoids event.currentTarget issues)."""
    await page.evaluate(f"""
        () => {{
            var c=document.getElementById('center-content');
            var ch=document.getElementById('center-chat');
            if(c&&ch){{ch.style.display='none';c.style.display='block';}}
            htmx.ajax('GET', '{path}', {{target:'#center-content', swap:'innerHTML'}});
            var h=document.getElementById('center-title');
            if(h) h.textContent='{title}';
        }}
    """)
    await asyncio.sleep(pause)


async def show_chat(page):
    """Switch back to chat view."""
    await page.evaluate("""
        () => {
            var c=document.getElementById('center-content');
            var ch=document.getElementById('center-chat');
            if(c) c.style.display='none';
            if(ch) ch.style.display='block';
            var h=document.getElementById('center-title');
            if(h) h.textContent='AI Chat';
        }
    """)


async def send_chat(page, msg, wait=3.0):
    """Type and send a chat command."""
    await page.evaluate(f"""
        () => {{
            var ta=document.getElementById('chat-input');
            var fm=document.getElementById('chat-form');
            if(ta&&fm){{ ta.value={repr(msg)}; fm.requestSubmit(); }}
        }}
    """)
    await asyncio.sleep(wait)
    await page.evaluate("() => { var m=document.getElementById('chat-messages'); if(m) m.scrollTop=m.scrollHeight; }")


async def run():
    from playwright.async_api import async_playwright

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # ===== LOGIN =====
        await page.goto(f"{BASE_URL}/login")
        await asyncio.sleep(1)
        await capture(page, "login", 0.5)

        await page.fill('input[name="email"]', EMAIL)
        await page.fill('input[name="password"]', PASSWORD)
        await capture(page, "login_filled", 0.5)

        await page.click('button[type="submit"]')
        await asyncio.sleep(2)

        # ===== WELCOME (new chat) =====
        await page.goto(f"{BASE_URL}/?new=1")
        await asyncio.sleep(2)
        await capture(page, "welcome_screen", 1.5)
        await capture(page, "welcome_screen_hold", 1.0)

        # ===== CHAT: help =====
        await send_chat(page, "help", 3)
        await capture(page, "chat_help", 1.0)

        await page.evaluate("() => { var m=document.getElementById('chat-messages'); if(m) m.scrollTop=m.scrollHeight; }")
        await capture(page, "chat_help_scroll", 0.5)

        # ===== CHAT: production:list =====
        await send_chat(page, "production:list", 3)
        await capture(page, "chat_productions", 1.0)

        # ===== CHAT: account:list =====
        await send_chat(page, "account:list", 3)
        await capture(page, "chat_accounts", 1.0)

        # ===== CHAT: transaction:list =====
        await send_chat(page, "transaction:list", 3)
        await capture(page, "chat_transactions", 1.0)

        # ===== CHAT: stakeholder:search distributor =====
        await send_chat(page, "stakeholder:search distributor", 3)
        await capture(page, "chat_stakeholders", 1.0)

        # ===== MODULE: Productions =====
        await nav_module(page, "/module/productions", "Productions")
        await capture(page, "module_productions", 1.5)

        # ===== MODULE: New Production Form =====
        await nav_module(page, "/module/production/new", "New Production")
        await capture(page, "module_production_new", 1.0)

        # ===== MODULE: Stakeholders =====
        await nav_module(page, "/module/stakeholders", "Stakeholders")
        await capture(page, "module_stakeholders", 1.0)

        # ===== MODULE: Collection Accounts =====
        await nav_module(page, "/module/accounts", "Collection Accounts")
        await capture(page, "module_accounts", 1.5)

        # ===== MODULE: Account Detail (first account) =====
        acct_id = await page.evaluate("""
            async () => {
                const r = await fetch('/module/accounts');
                const html = await r.text();
                const m = html.match(/hx-get="\\/module\\/account\\/([^"]+)"/);
                return m ? m[1] : null;
            }
        """)
        if acct_id:
            await nav_module(page, f"/module/account/{acct_id}", "Account Detail")
            await capture(page, "module_account_detail", 1.0)

        # ===== MODULE: Waterfall Engine =====
        await nav_module(page, "/module/waterfall", "Waterfall Engine")
        await capture(page, "module_waterfall", 1.5)

        # ===== MODULE: Waterfall Detail (first production with rules) =====
        wf_id = await page.evaluate("""
            async () => {
                const r = await fetch('/module/waterfall');
                const html = await r.text();
                const m = html.match(/hx-get="\\/module\\/waterfall\\/([^"]+)"/);
                return m ? m[1] : null;
            }
        """)
        if wf_id:
            await nav_module(page, f"/module/waterfall/{wf_id}", "Waterfall Detail")
            await capture(page, "module_waterfall_detail", 1.0)

        # ===== MODULE: Transactions =====
        await nav_module(page, "/module/transactions", "Transactions")
        await capture(page, "module_transactions", 1.0)

        # ===== MODULE: Record Transaction Form =====
        await nav_module(page, "/module/transaction/new", "Record Transaction")
        await capture(page, "module_transaction_new", 1.0)

        # ===== MODULE: Disbursements =====
        await nav_module(page, "/module/disbursements", "Disbursements")
        await capture(page, "module_disbursements", 1.0)

        # ===== MODULE: Contract Parser =====
        await nav_module(page, "/module/contracts", "Contract Parser")
        await capture(page, "module_contracts", 1.0)

        # ===== MODULE: Parse Contract Form =====
        await nav_module(page, "/module/contract/new", "Parse Contract")
        await capture(page, "module_contract_new", 1.0)

        # ===== MODULE: Reports =====
        await nav_module(page, "/module/reports", "Reports")
        await capture(page, "module_reports", 1.0)

        # ===== MODULE: Forecasting =====
        await nav_module(page, "/module/forecasting", "Revenue Forecasting")
        await capture(page, "module_forecasting", 1.0)

        # ===== MODULE: Anomaly Detection =====
        await nav_module(page, "/module/anomaly", "Anomaly Detection")
        await capture(page, "module_anomaly", 1.0)

        # ===== BACK TO WELCOME =====
        await page.goto(f"{BASE_URL}/?new=1")
        await asyncio.sleep(2)
        await capture(page, "final_welcome", 1.5)

        await browser.close()

    print(f"\n  Captured {frame_num} frames to docs/frames/")


def build_video():
    """Assemble frames into MP4 video and GIF."""
    from PIL import Image
    import av
    import numpy as np

    frames = sorted(FRAMES_DIR.glob("*.png"))
    if not frames:
        print("No frames found!")
        return

    images = [np.array(Image.open(f)) for f in frames]
    print(f"  Building video from {len(images)} frames...")

    # --- MP4 ---
    mp4_path = ROOT / "docs" / "demo_video.mp4"
    fps = 2
    hold_frames = 3  # each screenshot held for 1.5 seconds

    container = av.open(str(mp4_path), mode="w")
    h, w = images[0].shape[:2]
    w_enc = w if w % 2 == 0 else w - 1
    h_enc = h if h % 2 == 0 else h - 1
    stream = container.add_stream("libx264", rate=fps)
    stream.width = w_enc
    stream.height = h_enc
    stream.pix_fmt = "yuv420p"

    for img in images:
        img_cropped = img[:h_enc, :w_enc, :3]
        frame = av.VideoFrame.from_ndarray(img_cropped, format="rgb24")
        for _ in range(hold_frames):
            for packet in stream.encode(frame):
                container.mux(packet)

    for packet in stream.encode():
        container.mux(packet)
    container.close()
    total_secs = len(images) * hold_frames / fps
    print(f"  Saved MP4: {mp4_path} ({total_secs:.0f}s)")

    # --- GIF ---
    gif_path = ROOT / "docs" / "demo_video.gif"
    pil_frames = []
    for img in images:
        pil_img = Image.fromarray(img[:, :, :3])
        pil_img = pil_img.resize((w // 2, h // 2), Image.LANCZOS)
        pil_frames.append(pil_img)

    pil_frames[0].save(
        str(gif_path), save_all=True, append_images=pil_frames[1:],
        duration=1500, loop=0, optimize=True,
    )
    print(f"  Saved GIF: {gif_path}")


def main():
    print(f"\n{'='*60}")
    print(f"  AHCAM Product Demo — Video Capture")
    print(f"{'='*60}\n")

    asyncio.run(run())

    print(f"\n{'='*60}")
    print(f"  Building video and GIF...")
    print(f"{'='*60}\n")

    build_video()

    print(f"\n  Done!")
    print(f"  MP4: docs/demo_video.mp4")
    print(f"  GIF: docs/demo_video.gif")
    print(f"  Frames: docs/frames/\n")


if __name__ == "__main__":
    main()
