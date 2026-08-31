import json
import os
from typing import Any

class FirebaseRepository:
    def __init__(self, database_url: str | None, service_account_json: str | None):
        self.database_url = database_url
        self.service_account_json = service_account_json
        self._db = None
        self._initialize()

    def _initialize(self) -> None:
        if not self.database_url or not self.service_account_json:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials, db
            if not firebase_admin._apps:
                raw = json.loads(self.service_account_json)
                firebase_admin.initialize_app(credentials.Certificate(raw), {"databaseURL": self.database_url})
            self._db = db
        except Exception as exc:
            raise RuntimeError(f"Firebase initialization failed: {exc}") from exc

    @property
    def enabled(self) -> bool:
        return self._db is not None

    def set(self, path: str, value: Any) -> None:
        if not self._db:
            raise RuntimeError("Firebase is not configured")
        self._db.reference(path.strip("/")).set(value)

    def get(self, path: str) -> Any:
        if not self._db:
            raise RuntimeError("Firebase is not configured")
        return self._db.reference(path.strip("/")).get()
