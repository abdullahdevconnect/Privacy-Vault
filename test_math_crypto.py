"""
测试基于数学函数的加密模块
"""
import sys
sys.path.insert(0, '.')

from crypto.math_crypto import (
    MathKeyDerivation, 
    MathCipher, 
    KeyDerivationConfig,
    MERSENNE_PRIMES,
    get_mersenne_prime,
    gamma_expand
)
import base64

print("=" * 60)
print("基于数学函数的加密演示")
print("=" * 60)

# 1. 梅森素数
print("\n1. 梅森素数")
print("梅森素数形式: M_p = 2^p - 1")
for i, m in enumerate(MERSENNE_PRIMES[:5]):
    p = int(__import__('math').log2(m + 1))
    print(f"  M_{p} = 2^{p} - 1 = {m:,}")

# 2. 伽马函数
print("\n2. 伽马函数")
print("伽马函数: Γ(z) = ∫₀^∞ t^(z-1) e^(-t) dt")
import math
for v in [1, 2, 3, 5, 10]:
    gamma_val = math.gamma(v)
    factorial = math.factorial(v - 1)
    print(f"  Γ({v}) = {gamma_val:.2f} = ({v}-1)! = {factorial}")

# 3. 密钥派生
print("\n3. 密钥派生")
derivation = MathKeyDerivation()
password = "MySecretPassword123"
key, salt = derivation.derive_key(password)
print(f"  密码: {password}")
print(f"  盐值: {base64.b64encode(salt).decode()[:20]}...")
print(f"  密钥: {base64.b64encode(key).decode()[:20]}...")

# 相同密码和盐值产生相同密钥
key2, _ = derivation.derive_key(password, salt)
print(f"  相同密码+盐值产生相同密钥: {key == key2}")

# 4. 加密演示
print("\n4. 加密演示")
cipher = MathCipher(password)
cipher.initialize()

plaintext = "这是需要加密的敏感数据"
encrypted = cipher.encrypt(plaintext.encode('utf-8'))
print(f"  原始数据: {plaintext}")
print(f"  加密后: {base64.b64encode(encrypted['encrypted_data']).decode()[:30]}...")

decrypted = cipher.decrypt(encrypted)
print(f"  解密后: {decrypted.decode('utf-8')}")

# 5. 不同上下文派生不同密钥
print("\n5. 不同上下文派生不同密钥")
key_a, _ = derivation.derive_key_with_context(password, "context_a")
key_b, _ = derivation.derive_key_with_context(password, "context_b")
print(f"  上下文A密钥: {base64.b64encode(key_a).decode()[:20]}...")
print(f"  上下文B密钥: {base64.b64encode(key_b).decode()[:20]}...")
print(f"  不同上下文产生不同密钥: {key_a != key_b}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
