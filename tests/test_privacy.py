# tests/test_privacy.py
"""
PrivacyManager testleri.
Rıza yönetimi ve güvenli silme testleri.

ÖNEMLİ: Bu testler GERÇEK in-memory SQLite kullanır (mock değil).
"""

import os
import pytest
from pathlib import Path
from security.security_manager import PrivacyManager
from database.schema import Item


class TestConsentCheck:
    """check_consent() testleri."""

    def test_consent_granted(self, db_session, sample_items):
        """has_consent=True olan item için True döner."""
        pm = PrivacyManager(db_session)
        assert pm.check_consent(sample_items[0].item_id) is True

    def test_consent_denied(self, db_session, sample_items):
        """has_consent=False olan item için False döner."""
        pm = PrivacyManager(db_session)
        assert pm.check_consent(sample_items[2].item_id) is False

    def test_consent_nonexistent_item(self, db_session):
        """Olmayan item_id için False döner."""
        pm = PrivacyManager(db_session)
        assert pm.check_consent(99999) is False

    def test_consent_check_does_not_modify_db(self, db_session, sample_items):
        """check_consent sadece okuma yapar, DB'yi değiştirmez."""
        pm = PrivacyManager(db_session)
        item = sample_items[2]

        pm.check_consent(item.item_id)

        refreshed = db_session.query(Item).filter(Item.item_id == item.item_id).first()
        assert refreshed.has_consent is False


class TestSetConsent:
    """set_consent() testleri."""

    def test_grant_consent(self, db_session, sample_items):
        """Rıza verilmemiş item'a rıza ver."""
        pm = PrivacyManager(db_session)
        item = sample_items[2]

        pm.set_consent(item.item_id, True)

        updated = db_session.query(Item).filter(Item.item_id == item.item_id).first()
        assert updated.has_consent is True

    def test_revoke_consent(self, db_session, sample_items):
        """Rıza verilmiş item'dan rıza geri al."""
        pm = PrivacyManager(db_session)
        item = sample_items[0]

        pm.set_consent(item.item_id, False)

        updated = db_session.query(Item).filter(Item.item_id == item.item_id).first()
        assert updated.has_consent is False

    def test_set_consent_nonexistent_item(self, db_session):
        """Olmayan item_id için sessizce geçer."""
        pm = PrivacyManager(db_session)
        pm.set_consent(99999, True)

    def test_consent_toggle(self, db_session, sample_items):
        """Rıza durumu True→False→True değiştirilebilir."""
        pm = PrivacyManager(db_session)
        item = sample_items[0]

        pm.set_consent(item.item_id, False)
        assert pm.check_consent(item.item_id) is False

        pm.set_consent(item.item_id, True)
        assert pm.check_consent(item.item_id) is True


class TestSecureDelete:
    """secure_delete() testleri."""

    def test_secure_delete_success(self, db_session, temp_dir):
        """Dosya başarıyla ve güvenli şekilde silinir."""
        pm = PrivacyManager(db_session)

        file_path = temp_dir / "delete_me.txt"
        file_path.write_text("gizli veri")
        assert file_path.exists()

        result = pm.secure_delete(str(file_path))

        assert result is True
        assert not file_path.exists()

    def test_secure_delete_nonexistent(self, db_session):
        """Olmayan dosya silinmeye çalışılınca False döner."""
        pm = PrivacyManager(db_session)
        result = pm.secure_delete("/nonexistent/file.txt")
        assert result is False
