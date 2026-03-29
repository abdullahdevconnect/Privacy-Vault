"""
量子密码实现模块
包含:
1. QKD (量子密钥分发) 模拟器 - 模拟BB84协议
2. 后量子密码算法 - 基于格的密码学(Kyber风格)
3. 混合加密方案
"""
import os
import secrets
import hashlib
import time
import base64
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import hmac
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


class Basis(Enum):
    RECTILINEAR = 0  # 直线基 |+
    DIAGONAL = 1     # 对角基 x+


@dataclass
class Qubit:
    value: int
    basis: Basis
    phase: float = 0.0


@dataclass
class QuantumState:
    qubits: List[Qubit]
    timestamp: float
    entropy: float


class QKDSimulator:
    """
    BB84量子密钥分发协议模拟器
    模拟Alice和Bob之间的量子密钥交换过程
    """
    
    def __init__(self, key_length: int = 256):
        self.key_length = key_length
        self.alice_basis: List[Basis] = []
        self.bob_basis: List[Basis] = []
        self.alice_bits: List[int] = []
        self.bob_bits: List[int] = []
        self.eve_detected: bool = False
    
    def _generate_random_basis(self, count: int) -> List[Basis]:
        return [Basis(secrets.randbelow(2)) for _ in range(count)]
    
    def _generate_random_bits(self, count: int) -> List[int]:
        return [secrets.randbelow(2) for _ in range(count)]
    
    def _simulate_quantum_channel(
        self, 
        alice_qubits: List[Qubit], 
        eve_interception: bool = False
    ) -> List[Qubit]:
        received_qubits = []
        for qubit in alice_qubits:
            if eve_interception and secrets.randbelow(100) < 25:
                eve_basis = Basis(secrets.randbelow(2))
                if eve_basis != qubit.basis:
                    qubit = Qubit(
                        value=secrets.randbelow(2),
                        basis=qubit.basis,
                        phase=qubit.phase + 0.1
                    )
            noise = secrets.randbelow(1000) / 10000
            received_qubits.append(Qubit(
                value=qubit.value,
                basis=qubit.basis,
                phase=qubit.phase + noise
            ))
        return received_qubits
    
    def _measure_qubit(self, qubit: Qubit, measurement_basis: Basis) -> int:
        if qubit.basis == measurement_basis:
            return qubit.value
        return secrets.randbelow(2)
    
    def generate_key(self, eve_interception: bool = False) -> Tuple[bytes, Dict[str, Any]]:
        raw_bits_needed = self.key_length * 4
        self.alice_basis = self._generate_random_basis(raw_bits_needed)
        self.bob_basis = self._generate_random_basis(raw_bits_needed)
        self.alice_bits = self._generate_random_bits(raw_bits_needed)
        alice_qubits = [
            Qubit(value=bit, basis=basis) 
            for bit, basis in zip(self.alice_bits, self.alice_basis)
        ]
        received_qubits = self._simulate_quantum_channel(alice_qubits, eve_interception)
        self.bob_bits = [
            self._measure_qubit(q, basis) 
            for q, basis in zip(received_qubits, self.bob_basis)
        ]
        matching_indices = [
            i for i in range(raw_bits_needed) 
            if self.alice_basis[i] == self.bob_basis[i]
        ]
        sample_size = min(len(matching_indices) // 4, 50)
        sample_indices = set(secrets.SystemRandom().sample(
            matching_indices, sample_size
        ))
        error_count = sum(
            1 for i in sample_indices 
            if self.alice_bits[i] != self.bob_bits[i]
        )
        error_rate = error_count / sample_size if sample_size > 0 else 0
        self.eve_detected = error_rate > 0.11
        key_indices = [i for i in matching_indices if i not in sample_indices]
        key_bits = [self.alice_bits[i] for i in key_indices[:self.key_length]]
        key_bytes = bytes([
            int(''.join(map(str, key_bits[i:i+8])), 2) 
            for i in range(0, len(key_bits), 8)
        ])
        stats = {
            'raw_bits': raw_bits_needed,
            'matching_bases': len(matching_indices),
            'error_rate': error_rate,
            'eve_detected': self.eve_detected,
            'final_key_length': len(key_bytes) * 8
        }
        return key_bytes, stats


class LatticeBasedCrypto:
    """
    基于格的后量子密码学实现
    模拟Kyber算法的核心思想(Learning With Errors问题)
    """
    
    def __init__(self, dimension: int = 256, modulus: int = 3329):
        self.n = dimension
        self.q = modulus
        self._private_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
    
    def _poly_gen(self, seed: bytes, length: int) -> List[int]:
        result = []
        for i in range(length):
            h = hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()
            result.append(int.from_bytes(h[:2], 'big') % self.q)
        return result
    
    def _add_polynomials(self, a: List[int], b: List[int]) -> List[int]:
        return [(x + y) % self.q for x, y in zip(a, b)]
    
    def _mul_polynomials(self, a: List[int], b: List[int]) -> List[int]:
        result = [0] * self.n
        for i in range(len(a)):
            for j in range(len(b)):
                if i + j < self.n:
                    result[(i + j)] = (result[(i + j)] + a[i] * b[j]) % self.q
        return result
    
    def _generate_error(self, magnitude: int = 3) -> List[int]:
        return [
            secrets.randbelow(2 * magnitude + 1) - magnitude 
            for _ in range(self.n)
        ]
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        seed = secrets.token_bytes(32)
        s = self._poly_gen(seed + b'secret', self.n)
        a_seed = secrets.token_bytes(32)
        a = self._poly_gen(a_seed, self.n)
        e = self._generate_error()
        t = self._add_polynomials(self._mul_polynomials(a, s), e)
        private_key = self._serialize_poly(s) + seed
        public_key = self._serialize_poly(a) + self._serialize_poly(t) + a_seed
        self._private_key = private_key
        self._public_key = public_key
        return public_key, private_key
    
    def _serialize_poly(self, poly: List[int]) -> bytes:
        return b''.join(x.to_bytes(2, 'big') for x in poly)
    
    def _deserialize_poly(self, data: bytes) -> List[int]:
        return [int.from_bytes(data[i:i+2], 'big') for i in range(0, len(data), 2)]
    
    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        a_data = public_key[:self.n * 2]
        t_data = public_key[self.n * 2:self.n * 4]
        a = self._deserialize_poly(a_data)
        t = self._deserialize_poly(t_data)
        r = self._poly_gen(secrets.token_bytes(32), self.n)
        e1 = self._generate_error()
        e2 = self._generate_error()
        u = self._add_polynomials(self._mul_polynomials(a, r), e1)
        shared_secret = self._add_polynomials(self._mul_polynomials(t, r), e2)
        ciphertext = self._serialize_poly(u)
        ss_bytes = hashlib.sha256(self._serialize_poly(shared_secret)).digest()
        return ciphertext, ss_bytes
    
    def decapsulate(self, ciphertext: bytes, private_key: bytes) -> bytes:
        s = self._deserialize_poly(private_key[:self.n * 2])
        u = self._deserialize_poly(ciphertext[:self.n * 2])
        shared_secret = self._mul_polynomials(u, s)
        ss_bytes = hashlib.sha256(self._serialize_poly(shared_secret)).digest()
        return ss_bytes


class PostQuantumCipher:
    """
    后量子密码封装器
    使用对称加密 + 密钥派生
    """
    
    def __init__(self):
        self._master_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        self._private_key: Optional[bytes] = None
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        self._private_key = secrets.token_bytes(32)
        self._public_key = hashlib.sha256(self._private_key).digest()
        return self._public_key, self._private_key
    
    def set_master_key(self, master_key: bytes) -> None:
        self._master_key = master_key
    
    def encrypt(self, plaintext: bytes, public_key: bytes = None) -> Dict[str, bytes]:
        if not self._master_key:
            raise ValueError("主密钥未设置")
        
        salt = secrets.token_bytes(16)
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'quantum_vault',
            backend=default_backend()
        ).derive(self._master_key)
        
        nonce = secrets.token_bytes(12)
        cipher = ChaCha20Poly1305(key)
        encrypted_data = cipher.encrypt(nonce, plaintext, None)
        
        return {
            'encrypted_data': encrypted_data,
            'nonce': nonce,
            'salt': salt
        }
    
    def decrypt(self, encrypted_package: Dict[str, bytes], private_key: bytes = None) -> bytes:
        if not self._master_key:
            raise ValueError("主密钥未设置")
        
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=encrypted_package['salt'],
            info=b'quantum_vault',
            backend=default_backend()
        ).derive(self._master_key)
        
        cipher = ChaCha20Poly1305(key)
        plaintext = cipher.decrypt(
            encrypted_package['nonce'], 
            encrypted_package['encrypted_data'], 
            None
        )
        return plaintext


class QuantumCrypto:
    """
    量子密码主类
    整合QKD和后量子密码
    
    支持两种模式:
    1. 模拟模式 - 使用软件模拟BB84协议（默认）
    2. 真实硬件模式 - 连接真实QKD设备
    """
    
    def __init__(
        self, 
        key_size: int = 256,
        use_hardware: bool = False,
        hardware_config: Optional[Dict[str, Any]] = None
    ):
        self.key_size = key_size
        self.use_hardware = use_hardware
        self.hardware_config = hardware_config or {}
        
        self.qkd = QKDSimulator(key_size)
        self.pq_cipher = PostQuantumCipher()
        self._master_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        self._private_key: Optional[bytes] = None
        
        self._hardware_manager: Optional[Any] = None
        self._hardware_device_id: Optional[str] = None
    
    def set_hardware_mode(
        self, 
        device_type: str = "id_quantique",
        device_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        设置真实硬件模式
        
        参数:
            device_type: 设备类型 ('id_quantique', 'quantum_ctek', 'open_qkd')
            device_config: 设备配置，如 {'host': '192.168.1.100', 'port': 5555}
        """
        from .quantum_hardware import (
            QKDHardwareManager, QKDDeviceType, create_qkd_driver
        )
        
        device_type_map = {
            'id_quantique': QKDDeviceType.ID_QUANTIQUE,
            'quantum_ctek': QKDDeviceType.QUANTUM_CTEK,
            'open_qkd': QKDDeviceType.OPEN_QKD
        }
        
        qkd_device_type = device_type_map.get(device_type, QKDDeviceType.ID_QUANTIQUE)
        device_config = device_config or {'host': '192.168.1.100', 'port': 5555}
        
        self._hardware_manager = QKDHardwareManager()
        driver = create_qkd_driver(qkd_device_type, device_config)
        
        self._hardware_device_id = f"hw_{device_type}"
        self._hardware_manager.register_device(self._hardware_device_id, driver)
        self.use_hardware = True
    
    async def initialize_async(self) -> Dict[str, Any]:
        """
        异步初始化（支持真实硬件）
        """
        if self.use_hardware and self._hardware_manager:
            await self._hardware_manager.connect_device(self._hardware_device_id)
            qkd_key, qkd_stats = await self._hardware_manager.generate_key(
                device_id=self._hardware_device_id,
                key_length=self.key_size
            )
            if qkd_key is None:
                qkd_key, qkd_stats = self.qkd.generate_key()
                qkd_stats['fallback_to_simulator'] = True
        else:
            qkd_key, qkd_stats = self.qkd.generate_key()
        
        self._public_key, self._private_key = self.pq_cipher.generate_keypair()
        self._master_key = hashlib.sha3_256(
            qkd_key + self._private_key[:32]
        ).digest()
        
        return {
            'qkd_stats': qkd_stats,
            'mode': 'hardware' if self.use_hardware else 'simulator',
            'master_key_hash': hashlib.sha256(self._master_key).hexdigest()[:16],
            'public_key_size': len(self._public_key)
        }
    
    def initialize(self) -> Dict[str, Any]:
        """
        同步初始化（使用模拟器）
        """
        qkd_key, qkd_stats = self.qkd.generate_key()
        self._public_key, self._private_key = self.pq_cipher.generate_keypair()
        self._master_key = hashlib.sha3_256(
            qkd_key + self._private_key[:32]
        ).digest()
        self.pq_cipher.set_master_key(self._master_key)
        return {
            'qkd_stats': qkd_stats,
            'mode': 'simulator',
            'master_key_hash': hashlib.sha256(self._master_key).hexdigest()[:16],
            'public_key_size': len(self._public_key)
        }
    
    def save_keys(self, path: Optional[str] = None) -> Dict[str, str]:
        """
        保存密钥到文件
        """
        import base64
        if not self._master_key:
            raise ValueError("密钥未初始化")
        
        keys_data = {
            'master_key': base64.b64encode(self._master_key).decode()
        }
        
        if path:
            import json
            with open(path, 'w') as f:
                json.dump(keys_data, f)
        
        return keys_data
    
    def load_keys(self, path: str) -> bool:
        """
        从文件加载密钥
        """
        import json
        import base64
        
        try:
            with open(path, 'r') as f:
                keys_data = json.load(f)
            
            self._master_key = base64.b64decode(keys_data['master_key'])
            self.pq_cipher.set_master_key(self._master_key)
            self._public_key, self._private_key = self.pq_cipher.generate_keypair()
            return True
        except Exception as e:
            print(f"加载密钥失败: {e}")
            return False
    
    def encrypt_data(self, data: bytes) -> Dict[str, bytes]:
        if not self._master_key:
            raise ValueError("QuantumCrypto未初始化")
        return self.pq_cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_package: Dict[str, bytes]) -> bytes:
        if not self._master_key:
            raise ValueError("QuantumCrypto未初始化")
        return self.pq_cipher.decrypt(encrypted_package)
    
    def derive_key(self, context: str, length: int = 32) -> bytes:
        if not self._master_key:
            raise ValueError("QuantumCrypto未初始化")
        return HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=b'quantum_vault_derivation',
            info=context.encode(),
            backend=default_backend()
        ).derive(self._master_key)
    
    def get_quantum_signature(self, data: bytes) -> bytes:
        if not self._master_key:
            raise ValueError("QuantumCrypto未初始化")
        return hmac.new(
            self._master_key, 
            data, 
            hashlib.sha3_256
        ).digest()
    
    def verify_quantum_signature(self, data: bytes, signature: bytes) -> bool:
        expected = self.get_quantum_signature(data)
        return hmac.compare_digest(expected, signature)
    
    def rotate_keys(self) -> Dict[str, Any]:
        old_key_hash = hashlib.sha256(self._master_key).hexdigest()[:16] if self._master_key else None
        result = self.initialize()
        result['previous_key_hash'] = old_key_hash
        return result
