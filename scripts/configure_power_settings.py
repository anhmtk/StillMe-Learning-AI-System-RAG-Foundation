"""
⚡ StillMe IPC Power Settings Configuration
==========================================

Configures Windows power settings to prevent sleep mode
so StillMe can continue learning in the background.

Features:
- Disable sleep mode
- Keep display on but dimmed
- Prevent hibernation
- Optimize for background learning

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-29
"""

import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def configure_power_settings():
    """Configure Windows power settings for StillMe IPC"""
    try:
        logger.info("⚡ Configuring Windows Power Settings for StillMe IPC...")

        # Get current power scheme
        result = subprocess.run(
            ["powercfg", "/getactivescheme"], capture_output=True, text=True, check=True
        )
        current_scheme = result.stdout.strip()
        logger.info(f"Current power scheme: {current_scheme}")

        # Configure power settings
        power_settings = [
            # Disable sleep mode
            ("powercfg", "/change", "standby-timeout-ac", "0"),
            ("powercfg", "/change", "standby-timeout-dc", "0"),
            # Set display timeout (turn off display but keep system running)
            ("powercfg", "/change", "monitor-timeout-ac", "5"),  # 5 minutes
            ("powercfg", "/change", "monitor-timeout-dc", "3"),  # 3 minutes on battery
            # Disable hibernation
            ("powercfg", "/change", "hibernate-timeout-ac", "0"),
            ("powercfg", "/change", "hibernate-timeout-dc", "0"),
            # Disable hybrid sleep
            ("powercfg", "/change", "hybrid-sleep-ac", "off"),
            ("powercfg", "/change", "hybrid-sleep-dc", "off"),
            # Keep USB selective suspend disabled
            ("powercfg", "/change", "usbselectivesuspend-ac", "off"),
            ("powercfg", "/change", "usbselectivesuspend-dc", "off"),
        ]

        for cmd in power_settings:
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"✅ Configured: {' '.join(cmd[1:])}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Failed to configure {' '.join(cmd[1:])}: {e}")

        # Create custom power plan for StillMe
        logger.info("🎯 Creating custom power plan for StillMe IPC...")

        try:
            # Create new power plan
            result = subprocess.run(
                [
                    "powercfg",
                    "/duplicatescheme",
                    "SCHEME_BALANCED",
                    "StillMe-IPC-Learning",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Extract GUID from result
            guid_line = [
                line
                for line in result.stdout.split("\n")
                if "StillMe-IPC-Learning" in line
            ]
            if guid_line:
                guid = guid_line[0].split("(")[1].split(")")[0]
                logger.info(f"✅ Created power plan: {guid}")

                # Set as active
                subprocess.run(["powercfg", "/setactive", guid], check=True)
                logger.info("✅ Set StillMe power plan as active")

        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Failed to create custom power plan: {e}")

        logger.info("🎉 Power settings configured successfully!")
        logger.info(
            "💡 StillMe IPC will now continue learning even when display is off"
        )
        logger.info(
            "💡 System will not sleep, only display will turn off to save power"
        )

        return True

    except Exception as e:
        logger.error(f"❌ Failed to configure power settings: {e}")
        return False


def restore_default_power_settings():
    """Restore default Windows power settings"""
    try:
        logger.info("🔄 Restoring default Windows power settings...")

        # Restore balanced power plan
        subprocess.run(["powercfg", "/setactive", "SCHEME_BALANCED"], check=True)

        # Reset to default values
        power_settings = [
            ("powercfg", "/change", "standby-timeout-ac", "20"),  # 20 minutes
            ("powercfg", "/change", "standby-timeout-dc", "10"),  # 10 minutes
            ("powercfg", "/change", "monitor-timeout-ac", "10"),  # 10 minutes
            ("powercfg", "/change", "monitor-timeout-dc", "5"),  # 5 minutes
            ("powercfg", "/change", "hibernate-timeout-ac", "180"),  # 3 hours
            ("powercfg", "/change", "hibernate-timeout-dc", "60"),  # 1 hour
        ]

        for cmd in power_settings:
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"✅ Restored: {' '.join(cmd[1:])}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Failed to restore {' '.join(cmd[1:])}: {e}")

        logger.info("✅ Default power settings restored!")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to restore power settings: {e}")
        return False


def show_current_power_settings():
    """Show current power settings"""
    try:
        logger.info("📊 Current Power Settings:")

        # Show active scheme
        result = subprocess.run(
            ["powercfg", "/getactivescheme"], capture_output=True, text=True, check=True
        )
        print(f"Active Scheme: {result.stdout.strip()}")

        # Show power settings
        result = subprocess.run(
            ["powercfg", "/query", "SCHEME_CURRENT"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse and show relevant settings
        lines = result.stdout.split("\n")
        relevant_settings = [
            "standby-timeout-ac",
            "standby-timeout-dc",
            "monitor-timeout-ac",
            "monitor-timeout-dc",
            "hibernate-timeout-ac",
            "hibernate-timeout-dc",
        ]

        for line in lines:
            for setting in relevant_settings:
                if setting in line:
                    print(f"  {line.strip()}")
                    break

        return True

    except Exception as e:
        logger.error(f"❌ Failed to show power settings: {e}")
        return False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="StillMe IPC Power Settings Manager")
    parser.add_argument(
        "action", choices=["configure", "restore", "show"], help="Action to perform"
    )

    args = parser.parse_args()

    if args.action == "configure":
        success = configure_power_settings()
        if success:
            print("\n🎉 Power settings configured for StillMe IPC!")
            print("💡 Your computer will not sleep, only display will turn off")
            print("💡 StillMe can continue learning in the background")
            print(
                "💡 To restore defaults: python scripts/configure_power_settings.py restore"
            )
        else:
            print("\n❌ Failed to configure power settings")
            sys.exit(1)

    elif args.action == "restore":
        success = restore_default_power_settings()
        if success:
            print("\n✅ Default power settings restored!")
        else:
            print("\n❌ Failed to restore power settings")
            sys.exit(1)

    elif args.action == "show":
        show_current_power_settings()


if __name__ == "__main__":
    main()
