import asyncio
import logging
import sys

from app.controller.business_message import router as business_message_router
from app.controller.private import router as private_router
from app.loader import dp, bot
from app.utils.content import cron_delete_messages

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def main() -> None:
    dp.include_router(business_message_router)
    dp.include_router(private_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()

    loop.create_task(cron_delete_messages())
    loop.create_task(main())
    loop.run_forever()
