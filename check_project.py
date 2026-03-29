"""
项目检查脚本
检查所有模块是否正常导入
"""
import sys
print('Python version:', sys.version)
print()
print('Testing imports...')

errors = []

try:
    from core import AgentEngine, Config
    print('[OK] core module')
except Exception as e:
    errors.append(f'core: {e}')
    print(f'[ERROR] core: {e}')

try:
    from crypto import QuantumCrypto, KeyManager
    print('[OK] crypto module')
except Exception as e:
    errors.append(f'crypto: {e}')
    print(f'[ERROR] crypto: {e}')

try:
    from crypto.math_crypto import MathCipher, MathKeyDerivation
    print('[OK] crypto.math_crypto module')
except Exception as e:
    errors.append(f'crypto.math_crypto: {e}')
    print(f'[ERROR] crypto.math_crypto: {e}')

try:
    from auth import Authenticator, AccessControlManager
    print('[OK] auth module')
except Exception as e:
    errors.append(f'auth: {e}')
    print(f'[ERROR] auth: {e}')

try:
    from sandbox import Vault, SandboxIsolation
    print('[OK] sandbox module')
except Exception as e:
    errors.append(f'sandbox: {e}')
    print(f'[ERROR] sandbox: {e}')

try:
    from api import create_app
    print('[OK] api module')
except Exception as e:
    errors.append(f'api: {e}')
    print(f'[ERROR] api: {e}')

print()
if errors:
    print(f'Found {len(errors)} errors:')
    for e in errors:
        print(f'  - {e}')
else:
    print('All modules imported successfully!')
