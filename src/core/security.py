"""자격 증명 암호화/복호화 보안 모듈."""

import base64
import os
from cryptography.fernet import Fernet
from typing import Optional

from .exceptions import ConfigurationError


class SecurityManager:
    """자격 증명 암호화/복호화를 관리하는 클래스."""
    
    def __init__(self, encryption_key: Optional[str] = None) -> None:
        """암호화 키로 보안 관리자 초기화."""
        if encryption_key:
            self._fernet = Fernet(encryption_key.encode())
        else:
            self._fernet = None
    
    def encrypt_credential(self, plaintext: str) -> str:
        """자격 증명을 암호화하여 반환."""
        if not self._fernet:
            raise ConfigurationError("암호화 키가 설정되지 않았습니다")
        
        encrypted_bytes = self._fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted_bytes).decode()
    
    def decrypt_credential(self, encrypted_text: str) -> str:
        """암호화된 자격 증명을 복호화하여 반환."""
        if not self._fernet:
            raise ConfigurationError("암호화 키가 설정되지 않았습니다")
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_text.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise ConfigurationError(f"자격 증명 복호화 실패: {str(e)}")
    
    @staticmethod
    def generate_key() -> str:
        """새로운 암호화 키를 생성하여 반환."""
        return Fernet.generate_key().decode()
    
    def is_encryption_available(self) -> bool:
        """암호화 기능 사용 가능 여부 확인."""
        return self._fernet is not None


def get_secure_credential(
    env_var_name: str, 
    security_manager: Optional[SecurityManager] = None
) -> str:
    """환경 변수에서 자격 증명을 안전하게 가져오기."""
    credential = os.getenv(env_var_name)
    
    if not credential:
        raise ConfigurationError(f"환경 변수가 설정되지 않았습니다: {env_var_name}")
    
    # 암호화된 자격 증명인 경우 복호화
    if security_manager and security_manager.is_encryption_available():
        try:
            return security_manager.decrypt_credential(credential)
        except ConfigurationError:
            # 복호화 실패 시 원본 값 반환 (평문으로 저장된 경우)
            return credential
    
    return credential