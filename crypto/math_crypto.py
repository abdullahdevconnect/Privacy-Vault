"""
基于数学函数的加密模块
使用伽马函数和梅森素数进行密钥派生

特点:
1. 完全本地实现，无需量子硬件
2. 使用数学函数增加密钥空间
3. 梅森素数提供良好的随机性质
4. 可理解和可验证的加密过程
"""
import os
import secrets
import hashlib
import math
import json
import base64
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


# ==================== 梅森素数 ====================

MERSENNE_PRIMES = [
    3, 7, 31, 127, 8191, 131071, 524287, 2147483647
]


def get_mersenne_prime(index: int) -> int:
    """获取梅森素数 M_p = 2^p - 1"""
    if 0 <= index < len(MERSENNE_PRIMES):
        return MERSENNE_PRIMES[index]
    return MERSENNE_PRIMES[-1]


# ==================== 伽马函数密钥扩展 ====================

def gamma_expand(value: float, iterations: int = 100) -> float:
    """
    使用伽马函数扩展数值
    
    伽马函数: Γ(z) = ∫₀^∞ t^(z-1) e^(-t) dt
    
    特性:
    - Γ(n) = (n-1)! 对于正整数n
    - Γ(z+1) = z·Γ(z) 递推关系
    - 将小数值扩展到大数值空间
    """
    result = max(0.5, min(value, 10.0))  # 限制在合理范围
    for i in range(iterations):
        # 防止溢出：伽马函数在输入>170时会溢出
        if result > 50:
            # 使用对数映射保持数值稳定
            result = math.log(result + 1) + 1
        elif result < 0.5:
            result = 0.5 + result * 0.1
        else:
            try:
                result = math.gamma(result)
            except OverflowError:
                result = math.log(result + 1) + 1
    return result


def bytes_to_gamma_input(data: bytes) -> float:
    """将字节转换为伽马函数输入值"""
    h = hashlib.sha256(data).digest()
    val = int.from_bytes(h[:8], 'big')
    return (val % 1000000) / 100000.0 + 1.0


# ==================== 密钥派生 ====================

@dataclass
class KeyDerivationConfig:
    """密钥派生配置"""
    gamma_iterations: int = 100
    mersenne_rounds: int = 8
    key_length: int = 32


class MathKeyDerivation:
    """
    基于数学函数的密钥派生
    
    流程:
    1. 密码 + 盐值 → 哈希
    2. 哈希 → 伽马函数 → 大数值
    3. 梅森素数模运算 → 密钥种子
    4. 种子 → 最终密钥
    """
    
    def __init__(self, config: Optional[KeyDerivationConfig] = None):
        self.config = config or KeyDerivationConfig()
    
    def derive_key(
        self,
        password: str,
        salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """
        从密码派生密钥
        
        参数:
            password: 用户密码
            salt: 盐值（可选，不提供则生成新的）
        
        返回:
            (密钥, 盐值)
        """
        # 生成盐值
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # 步骤1: 密码 + 盐值 → 哈希
        combined = password.encode('utf-8') + salt
        h = hashlib.sha512(combined).digest()
        
        # 步骤2: 哈希 → 伽马函数扩展
        gamma_input = bytes_to_gamma_input(h)
        gamma_result = gamma_expand(gamma_input, self.config.gamma_iterations)
        
        # 步骤3: 梅森素数混合
        seed = int.from_bytes(h[:16], 'big')
        for i in range(self.config.mersenne_rounds):
            m = get_mersenne_prime(i % len(MERSENNE_PRIMES))
            seed = (seed * int(gamma_result * 1000000) + i) % m
        
        # 步骤4: 生成最终密钥
        key_material = bytearray()
        for i in range(4):
            m = get_mersenne_prime(i % len(MERSENNE_PRIMES))
            val = (seed + i * int(gamma_result * 1000)) % m
            key_material.extend(val.to_bytes(8, 'big'))
        
        # 最终哈希确保密钥长度
        final_key = hashlib.sha256(bytes(key_material)).digest()
        
        return final_key[:self.config.key_length], salt
    
    def derive_key_with_context(
        self,
        password: str,
        context: str,
        salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """
        带上下文的密钥派生
        
        不同上下文产生不同密钥
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        combined = password.encode('utf-8') + salt + context.encode('utf-8')
        h = hashlib.sha512(combined).digest()
        
        gamma_input = bytes_to_gamma_input(h)
        gamma_result = gamma_expand(gamma_input, self.config.gamma_iterations // 2)
        
        seed = int.from_bytes(h[:16], 'big')
        for i in range(self.config.mersenne_rounds):
            m = get_mersenne_prime(i % len(MERSENNE_PRIMES))
            seed = (seed * int(gamma_result * 1000000) + i) % m
        
        key_material = bytearray()
        for i in range(4):
            m = get_mersenne_prime(i % len(MERSENNE_PRIMES))
            val = (seed + i * int(gamma_result * 1000)) % m
            key_material.extend(val.to_bytes(8, 'big'))
        
        return hashlib.sha256(bytes(key_material)).digest()[:self.config.key_length], salt


# ==================== 加密器 ====================

class MathCipher:
    """
    基于数学函数的加密器
    
    使用ChaCha20-Poly1305进行加密
    密钥由伽马函数和梅森素数派生
    """
    
    def __init__(self, password: str = None):
        self.password = password
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None
        self._derivation = MathKeyDerivation()
    
    def initialize(self, password: str = None) -> Dict[str, Any]:
        """
        初始化加密器
        """
        if password:
            self.password = password
        
        if not self.password:
            self.password = secrets.token_urlsafe(32)
        
        self._key, self._salt = self._derivation.derive_key(self.password)
        
        return {
            'status': 'initialized',
            'method': 'gamma_mersenne',
            'salt': base64.b64encode(self._salt).decode(),
            'key_hash': hashlib.sha256(self._key).hexdigest()[:16]
        }
    
    def load_salt(self, salt: bytes, password: str = None) -> None:
        """从盐值恢复密钥"""
        if password:
            self.password = password
        self._key, self._salt = self._derivation.derive_key(self.password, salt)
    
    def set_master_key(self, key: bytes) -> None:
        """直接设置主密钥"""
        self._key = key
    
    def encrypt(self, plaintext: bytes) -> Dict[str, bytes]:
        """
        加密数据
        
        返回包含密文、nonce和盐值的字典
        """
        if not self._key:
            raise ValueError("加密器未初始化")
        
        nonce = secrets.token_bytes(12)
        cipher = ChaCha20Poly1305(self._key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        return {
            'encrypted_data': ciphertext,
            'nonce': nonce,
            'salt': self._salt
        }
    
    def decrypt(self, encrypted_package: Dict[str, bytes]) -> bytes:
        """
        解密数据
        """
        if not self._key:
            raise ValueError("加密器未初始化")
        
        # 检查是否需要重新派生密钥
        salt = encrypted_package.get('salt')
        if salt and salt != self._salt:
            self._key, self._salt = self._derivation.derive_key(self.password, salt)
        
        cipher = ChaCha20Poly1305(self._key)
        return cipher.decrypt(
            encrypted_package['nonce'],
            encrypted_package['encrypted_data'],
            None
        )
    
    def save_state(self, path: str) -> None:
        """保存状态到文件"""
        state = {
            'salt': base64.b64encode(self._salt).decode() if self._salt else None,
            'key_hash': hashlib.sha256(self._key).hexdigest() if self._key else None
        }
        with open(path, 'w') as f:
            json.dump(state, f)
    
    def load_state(self, path: str, password: str) -> None:
        """从文件加载状态"""
        with open(path, 'r') as f:
            state = json.load(f)
        
        if state.get('salt'):
            salt = base64.b64decode(state['salt'])
            self._key, self._salt = self._derivation.derive_key(password, salt)


# ==================== 密钥管理器 ====================

class KeyManager:
    """
    密钥管理器
    管理多个加密密钥
    """
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._keys: Dict[str, bytes] = {}
        self._metadata: Dict[str, Dict] = {}
    
    def generate_key(self, key_id: str, password: str = None) -> bytes:
        """生成新密钥"""
        if password:
            derivation = MathKeyDerivation()
            key, salt = derivation.derive_key(password)
        else:
            key = secrets.token_bytes(32)
            salt = secrets.token_bytes(32)
        
        self._keys[key_id] = key
        self._metadata[key_id] = {
            'created_at': int(time.time()),
            'salt': base64.b64encode(salt).decode()
        }
        
        return key
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """获取密钥"""
        return self._keys.get(key_id)
    
    def delete_key(self, key_id: str) -> bool:
        """删除密钥"""
        if key_id in self._keys:
            del self._keys[key_id]
            del self._metadata[key_id]
            return True
        return False
    
    def list_keys(self) -> List[str]:
        """列出所有密钥ID"""
        return list(self._keys.keys())
    
    def save_keys(self, path: str = None) -> None:
        """保存密钥到文件"""
        path = path or self.storage_path
        data = {
            'keys': {k: base64.b64encode(v).decode() for k, v in self._keys.items()},
            'metadata': self._metadata
        }
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def load_keys(self, path: str = None) -> None:
        """从文件加载密钥"""
        path = path or self.storage_path
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self._keys = {k: base64.b64decode(v) for k, v in data.get('keys', {}).items()}
            self._metadata = data.get('metadata', {})
        except FileNotFoundError:
            pass
    
    def get_key_stats(self) -> Dict[str, Any]:
        """获取密钥统计"""
        return {
            'total_keys': len(self._keys),
            'key_ids': list(self._keys.keys())
        }


# ==================== 导出 ====================

__all__ = [
    'MathKeyDerivation',
    'MathCipher',
    'KeyManager',
    'KeyDerivationConfig',
    'MERSENNE_PRIMES',
    'get_mersenne_prime',
    'gamma_expand'
]


# ==================== 演示 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("基于数学函数的加密演示")
    print("=" * 60)
    
    # 1. 密钥派生
    print("\n1. 密钥派生")
    derivation = MathKeyDerivation()
    password = "MySecretPassword"
    key, salt = derivation.derive_key(password)
    print(f"密码: {password}")
    print(f"盐值: {base64.b64encode(salt).decode()[:20]}...")
    print(f"密钥: {base64.b64encode(key).decode()[:20]}...")
    
    # 相同密码和盐值产生相同密钥
    key2, _ = derivation.derive_key(password, salt)
    print(f"相同密码+盐值产生相同密钥: {key == key2}")
    
    # 2. 加密演示
    print("\n2. 加密演示")
    cipher = MathCipher(password)
    cipher.initialize()
    
    plaintext = "这是需要加密的敏感数据"
    encrypted = cipher.encrypt(plaintext.encode('utf-8'))
    print(f"原始数据: {plaintext}")
    print(f"加密后: {base64.b64encode(encrypted['encrypted_data']).decode()[:30]}...")
    
    decrypted = cipher.decrypt(encrypted)
    print(f"解密后: {decrypted.decode('utf-8')}")
    
    # 3. 梅森素数
    print("\n3. 梅森素数")
    for i, m in enumerate(MERSENNE_PRIMES[:5]):
        p = int(math.log2(m + 1))
        print(f"M_{p} = 2^{p} - 1 = {m}")
    
    # 4. 伽马函数
    print("\n4. 伽马函数")
    for v in [1, 2, 3, 5, 10]:
        print(f"Γ({v}) = {math.gamma(v):.2f} = {math.factorial(v-1)}")
    
    print("\n" + "=" * 60)
