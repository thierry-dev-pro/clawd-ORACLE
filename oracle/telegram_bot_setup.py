#!/usr/bin/env python3
"""
Telegram Bot Webhook Setup Script for ORACLE
Configure real webhook (not polling)
"""
import asyncio
import logging
import sys
from dotenv import load_dotenv
from core.config import settings
import aiohttp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load env
load_dotenv()

class TelegramWebhookSetup:
    def __init__(self):
        self.token = settings.TELEGRAM_TOKEN
        self.base_url = "https://api.telegram.org"
        self.webhook_url = None
        
        if not self.token:
            raise ValueError("❌ TELEGRAM_TOKEN not set in .env")
        
        logger.info("🔐 Telegram Webhook Setup initialized")
    
    async def get_webhook_info(self) -> dict:
        """Get current webhook status"""
        url = f"{self.base_url}/bot{self.token}/getWebhookInfo"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return data.get("result", {})
                    else:
                        logger.error(f"❌ API Error: {data.get('description')}")
                        return {}
        except Exception as e:
            logger.error(f"❌ Failed to get webhook info: {e}")
            return {}
    
    async def delete_webhook(self) -> bool:
        """Delete existing webhook"""
        url = f"{self.base_url}/bot{self.token}/deleteWebhook"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        logger.info("✅ Deleted existing webhook")
                        return True
                    else:
                        logger.warning(f"⚠️ Failed to delete webhook: {data.get('description')}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error deleting webhook: {e}")
            return False
    
    async def set_webhook(self, webhook_url: str, allowed_updates: list = None) -> bool:
        """Set new webhook"""
        self.webhook_url = webhook_url
        
        if allowed_updates is None:
            allowed_updates = [
                "message",
                "edited_message",
                "channel_post",
                "callback_query",
            ]
        
        url = f"{self.base_url}/bot{self.token}/setWebhook"
        
        payload = {
            "url": webhook_url,
            "allowed_updates": allowed_updates,
            "drop_pending_updates": False,  # Keep queued messages
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        logger.info(f"✅ Webhook set to: {webhook_url}")
                        return True
                    else:
                        logger.error(f"❌ Failed to set webhook: {data.get('description')}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error setting webhook: {e}")
            return False
    
    async def get_bot_info(self) -> dict:
        """Get bot information"""
        url = f"{self.base_url}/bot{self.token}/getMe"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return data.get("result", {})
                    else:
                        logger.error(f"❌ Failed to get bot info: {data.get('description')}")
                        return {}
        except Exception as e:
            logger.error(f"❌ Error getting bot info: {e}")
            return {}
    
    async def get_updates(self, limit: int = 1) -> list:
        """Get pending updates (polling mode - for verification)"""
        url = f"{self.base_url}/bot{self.token}/getUpdates"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params={"limit": limit, "timeout": 0},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        updates = data.get("result", [])
                        return updates
                    else:
                        return []
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch updates: {e}")
            return []
    
    async def send_test_message(self, chat_id: int) -> bool:
        """Send a test message to verify bot is working"""
        url = f"{self.base_url}/bot{self.token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": "✅ ORACLE Telegram Bot Webhook is now LIVE\n\n"
                   "🔮 AI-Powered Crypto Intelligence Online\n\n"
                   "Commands:\n"
                   "/start - Introduction\n"
                   "/help - Full command list\n"
                   "/status - System status",
            "parse_mode": "HTML",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        logger.info(f"✅ Test message sent to chat {chat_id}")
                        return True
                    else:
                        logger.error(f"❌ Failed to send test message: {data.get('description')}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error sending test message: {e}")
            return False
    
    async def status_report(self) -> str:
        """Generate status report"""
        report = []
        report.append("\n" + "="*60)
        report.append("🔮 ORACLE Telegram Webhook Status Report")
        report.append("="*60)
        
        # Bot info
        bot_info = await self.get_bot_info()
        if bot_info:
            report.append(f"\n✅ Bot Connected")
            report.append(f"   Name: {bot_info.get('first_name')}")
            report.append(f"   Username: @{bot_info.get('username')}")
            report.append(f"   Bot ID: {bot_info.get('id')}")
        else:
            report.append(f"\n❌ Bot Connection Failed")
        
        # Webhook info
        webhook_info = await self.get_webhook_info()
        if webhook_info.get("url"):
            report.append(f"\n✅ Webhook Active")
            report.append(f"   URL: {webhook_info.get('url')}")
            report.append(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
            report.append(f"   Last error: {webhook_info.get('last_error_message', 'None')}")
            report.append(f"   Last error date: {webhook_info.get('last_error_date', 'Never')}")
        else:
            report.append(f"\n⚠️ Webhook Not Active (Polling Mode)")
        
        report.append(f"\n" + "="*60)
        return "\n".join(report)


async def setup_webhook(webhook_url: str, delete_existing: bool = True):
    """Main setup function"""
    setup = TelegramWebhookSetup()
    
    try:
        # Show bot info
        logger.info("🔍 Checking bot connection...")
        bot_info = await setup.get_bot_info()
        if bot_info:
            logger.info(f"✅ Connected to bot: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
        else:
            logger.error("❌ Cannot connect to bot. Check TELEGRAM_TOKEN")
            return False
        
        # Delete existing webhook if requested
        if delete_existing:
            logger.info("🗑️  Cleaning up existing webhook...")
            await setup.delete_webhook()
        
        # Set new webhook
        logger.info(f"🔗 Setting webhook to: {webhook_url}")
        success = await setup.set_webhook(webhook_url)
        
        if not success:
            logger.error("❌ Failed to set webhook")
            return False
        
        # Verify webhook
        logger.info("🔍 Verifying webhook setup...")
        await asyncio.sleep(1)
        webhook_info = await setup.get_webhook_info()
        
        if webhook_info.get("url") == webhook_url:
            logger.info("✅ Webhook verified successfully!")
        else:
            logger.warning("⚠️ Webhook may not be fully verified yet")
        
        # Show status
        report = await setup.status_report()
        logger.info(report)
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False


async def show_status():
    """Show current webhook status"""
    setup = TelegramWebhookSetup()
    report = await setup.status_report()
    logger.info(report)


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🔮 ORACLE Telegram Webhook Setup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup webhook (requires external URL)
  python telegram_bot_setup.py setup https://your-domain.com/webhook/telegram
  
  # Show current status
  python telegram_bot_setup.py status
  
  # Delete webhook (back to polling)
  python telegram_bot_setup.py delete
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup webhook")
    setup_parser.add_argument(
        "webhook_url",
        help="Webhook URL (e.g., https://your-domain.com/webhook/telegram)"
    )
    setup_parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing webhook if any"
    )
    
    # Status command
    subparsers.add_parser("status", help="Show webhook status")
    
    # Delete command
    subparsers.add_parser("delete", help="Delete webhook (revert to polling)")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        logger.info(f"📡 Setting up webhook...")
        success = asyncio.run(setup_webhook(
            args.webhook_url,
            delete_existing=not args.keep_existing
        ))
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        logger.info("📊 Fetching webhook status...")
        asyncio.run(show_status())
    
    elif args.command == "delete":
        logger.info("🗑️  Deleting webhook...")
        setup = TelegramWebhookSetup()
        success = asyncio.run(setup.delete_webhook())
        if success:
            logger.info("✅ Webhook deleted. Telegram will use polling mode.")
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
