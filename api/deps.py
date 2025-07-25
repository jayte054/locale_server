from typing import Annotated
import logging
from datetime import datetime, timedelta
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends


from config.database import SessionLocal
from services.authService.model.blacklistModel import TokenBlacklist

logger = logging.getLogger("TokenCleanupScheduler")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
bcrypt_context = CryptContext(
    schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12)


class TokenCleanUpScheduler:
    def __init__(self, db_session: db_dependency):
        self._lock = Lock()
        self.scheduler = BackgroundScheduler(
            job_defaults={
                'misfire_grace_time': 60*60,
                'coalesce': True,
                'max_instances': 1
            }
        )
        self.db = db_session

    # Run every 6 hours
    def start(self):
        trigger = IntervalTrigger(hours=6, jitter=30)

        self.scheduler.add_job(
            self.clean_expired_tokens,
            trigger=trigger,
            next_run_time=datetime.now() + timedelta(minutes=1),
            id='token_cleanup',
            replace_existing=True
        )

        try:
            self.scheduler.start()
            logger.info(
                'Token cleanup scheduler started'
            )
        except Exception as e:
            logger.critical(
                f'scheduler failed to start: {str(e)}'
            )
            raise

    # Remove expired tokens from blacklist
    def clean_expired_tokens(self):
        with self._lock:
            try:
                db = SessionLocal()
                batch_size = 1000
                total_deleted = 0

                while True:
                    deleted = db.query(TokenBlacklist)\
                        .filter(TokenBlacklist.expires < datetime.utcnow())\
                        .limit(batch_size)\
                        .delete(synchronize_session=False)

                    if deleted == 0:
                        break

                    total_deleted += deleted
                    db.commit()

                logger.info(
                    f"cleaned up {total_deleted} expired tokens"
                )
            except Exception as e:
                logger.error(
                    f'Token clean up failed: {str(e)}',
                    exc_info=True
                )
                db.rollback()
            except Exception as e:
                logger.critical(f'unexpected error: {str(e)}', exc_info=True)
            finally:
                db.close()

    def shutdown(self):
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info('Scheduler stopped gracefully')
        except Exception as e:
            logger.error(f'Error during shutdown: {str(e)}', exc_info=True)
            raise
