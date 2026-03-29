"""
密码模块
提供多种加密方案:

1. 量子密码模拟 - 使用软件模拟BB84协议
2. 数学加密 - 使用伽马函数和梅森素数（推荐本地使用）
3. 真实硬件模式 - 连接真实QKD设备
"""
from .quantum_crypto import QuantumCrypto, QKDSimulator, PostQuantumCipher
from .key_manager import KeyManager, QuantumKey
from .math_crypto import (
    MathKeyDerivation,
    MathCipher,
    KeyDerivationConfig,
    MERSENNE_PRIMES,
    get_mersenne_prime,
    gamma_expand
)
from .quantum_hardware import (
    QKDHardwareManager,
    QKDHardwareInterface,
    QKDDeviceType,
    QKDProtocol,
    IDQuantiqueDriver,
    QuantumCTekDriver,
    OpenQKDDriver,
    create_qkd_driver
)

__all__ = [
    # 量子密码
    'QuantumCrypto', 'QKDSimulator', 'PostQuantumCipher', 
    'KeyManager', 'QuantumKey',
    # 数学加密
    'MathKeyDerivation', 'MathCipher', 'KeyDerivationConfig',
    'MERSENNE_PRIMES', 'get_mersenne_prime', 'gamma_expand',
    # 硬件接口
    'QKDHardwareManager', 'QKDHardwareInterface', 'QKDDeviceType', 'QKDProtocol',
    'IDQuantiqueDriver', 'QuantumCTekDriver', 'OpenQKDDriver', 'create_qkd_driver'
]
