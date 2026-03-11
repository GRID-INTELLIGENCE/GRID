# Migrating from `ecdsa` to `cryptography` Library

## Executive Summary

The `python-ecdsa` library is vulnerable to the **Minerva timing attack** (CVE-2024-23342) on P-256 curves. The python-ecdsa project considers side-channel attacks out of scope with no planned fix. This guide provides a migration path to the `cryptography` library, which uses OpenSSL's constant-time implementations.

**Risk Level**: HIGH  
**Effort**: 1-2 sprints  
**Impact**: Eliminates timing side-channel vulnerability in signature operations

---

## Background: The Minerva Attack

### What is the Minerva Timing Attack?

The Minerva attack exploits timing variations in ECDSA signature generation:

1. **ECDSA signing** requires generating a random nonce `k` for each signature
2. **Modular inversion** of `k` has timing variations depending on the value
3. **Statistical analysis** of signature timing can leak bits of the nonce
4. **Key recovery** becomes possible with enough signature samples

### Affected Operations in `ecdsa`

| Operation | Vulnerable | Fixed in `cryptography` |
|-----------|------------|------------------------|
| `SigningKey.sign()` | ✅ Yes | ✅ Constant-time |
| `SigningKey.sign_digest()` | ✅ Yes | ✅ Constant-time |
| `SigningKey.get_verifying_key()` | ❌ No | ✅ Safe |
| `VerifyingKey.verify()` | ❌ No | ✅ Safe |
| `ECDH key agreement` | ✅ Yes | ✅ Constant-time |

---

## Migration Steps

### Step 1: Add `cryptography` to Dependencies

```python
# pyproject.toml or requirements.txt
cryptography>=44.0.0
```

```bash
pip install cryptography>=44.0.0
```

### Step 2: Identify Usage Patterns

Search your codebase for `ecdsa` usage:

```bash
grep -r "from ecdsa" --include="*.py" .
grep -r "import ecdsa" --include="*.py" .
```

Common patterns to look for:

```python
# Pattern 1: Direct signing
from ecdsa import SigningKey, SECP256R1
sk = SigningKey.generate(curve=SECP256R1)
signature = sk.sign(message)

# Pattern 2: DER-encoded signatures
from ecdsa import SigningKey, SECP256R1
signature = sk.sign_digest(digest, sigencode=ecdsa.util.sigencode_der)

# Pattern 3: Key serialization
pem = sk.to_pem()
der = sk.to_der()

# Pattern 4: Verification
from ecdsa import VerifyingKey
vk = VerifyingKey.from_pem(pem_data)
valid = vk.verify(signature, message)
```

### Step 3: Replace with `cryptography` API

#### 3.1 Key Generation

**Before (ecdsa):**
```python
from ecdsa import SigningKey, SECP256R1

sk = SigningKey.generate(curve=SECP256R1())
vk = sk.get_verifying_key()
```

**After (cryptography):**
```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

# P-256 = SECP256R1 = prime256v1
sk = ec.generate_private_key(ec.SECP256R1())
vk = sk.public_key()
```

#### 3.2 Signing

**Before (ecdsa):**
```python
signature = sk.sign(message)  # Raw signing (NOT RECOMMENDED)
# or
digest = hashlib.sha256(message).digest()
signature = sk.sign_digest(digest)
```

**After (cryptography):**
```python
from cryptography.hazmat.primitives.asymmetric.utils import encode_rfc6979_signature

# Preferred: Use deterministic ECDSA (RFC 6979) - immune to nonce issues
signature = sk.sign(
    message,
    ec.ECDSA(hashes.SHA256())  # Automatically hashes message
)

# Or with explicit pre-hashed digest:
digest = hashlib.sha256(message).digest()
signature = sk.sign(digest, ec.ECDSA(hashes.SHA256()))
```

**Important**: `cryptography` always applies the hash algorithm. If you pre-hash, use `Prehashed`:

```python
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes

# Pre-hashed signing
digest = hashlib.sha256(message).digest()
signature = sk.sign(
    digest,
    ec.ECDSA(utils.Prehashed(hashes.SHA256()))
)
```

#### 3.3 Signature Encoding (DER vs Raw)

**ecdsa** provides flexible encoding:

```python
from ecdsa.util import sigencode_der, sigencode_string

signature_der = sk.sign_digest(digest, sigencode=sigencode_der)
signature_raw = sk.sign_digest(digest, sigencode=sigencode_string)
```

**cryptography** returns DER-encoded by default:

```python
# Returns DER-encoded signature (r || s in ASN.1 format)
signature_der = sk.sign(message, ec.ECDSA(hashes.SHA256()))

# For raw (r || s concatenated, 64 bytes for P-256):
from cryptography.hazmat.primitives.asymmetric.utils import decode_rfc6979_signature
r, s = decode_rfc6979_signature(signature_der)
signature_raw = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
```

#### 3.4 Key Serialization

**Before (ecdsa):**
```python
pem = sk.to_pem()
der = sk.to_der()
pem_vk = vk.to_pem()
```

**After (cryptography):**
```python
from cryptography.hazmat.primitives import serialization

# Private key PEM
pem_private = sk.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()  # Or BestAvailableEncryption(password)
)

# Private key DER
der_private = sk.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Public key PEM
pem_public = vk.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
```

#### 3.5 Verification

**Before (ecdsa):**
```python
valid = vk.verify(signature, message)
```

**After (cryptography):**
```python
vk.verify(signature, message, ec.ECDSA(hashes.SHA256()))
```

---

## Code Migration Examples

### Example 1: JWT Token Signing

**Before (ecdsa):**
```python
import jwt
from ecdsa import SigningKey, SECP256R1

sk = SigningKey.generate(curve=SECP256R1())
token = jwt.encode(payload, sk.to_pem(), algorithm='ES256')
```

**After (cryptography):**
```python
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

sk = ec.generate_private_key(ec.SECP256R1())
pem = sk.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
token = jwt.encode(payload, pem, algorithm='ES256')
```

### Example 2: Message Authentication

**Before (ecdsa):**
```python
from ecdsa import SigningKey, VerifyingKey, SECP256R1
import hashlib

def sign_message(private_key_pem: str, message: bytes) -> bytes:
    sk = SigningKey.from_pem(private_key_pem)
    digest = hashlib.sha256(message).digest()
    return sk.sign_digest(digest)

def verify_signature(public_key_pem: str, message: bytes, signature: bytes) -> bool:
    vk = VerifyingKey.from_pem(public_key_pem)
    try:
        vk.verify(signature, message)
        return True
    except BadSignature:
        return False
```

**After (cryptography):**
```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature
import hashlib

def sign_message(private_key_pem: str, message: bytes) -> bytes:
    sk = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    return sk.sign(message, ec.ECDSA(hashes.SHA256()))

def verify_signature(public_key_pem: str, message: bytes, signature: bytes) -> bool:
    vk = serialization.load_pem_public_key(public_key_pem.encode())
    try:
        vk.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
```

### Example 3: ECDH Key Exchange

**Before (ecdsa):**
```python
from ecdsa import SigningKey, SECP256R1

alice_sk = SigningKey.generate(curve=SECP256R1())
bob_sk = SigningKey.generate(curve=SECP256R1())

# Exchange public keys
alice_shared = alice_sk.get_verifying_key().get_verifying_key()
bob_shared = bob_sk.get_verifying_key()

# Derive shared secret
shared = alice_sk.get_verifying_key().verify(...)  # Complex manual ECDH
```

**After (cryptography):**
```python
from cryptography.hazmat.primitives.asymmetric import ec

alice_sk = ec.generate_private_key(ec.SECP256R1())
bob_sk = ec.generate_private_key(ec.SECP256R1())

# Exchange public keys
alice_pk = alice_sk.public_key()
bob_pk = bob_sk.public_key()

# Derive shared secret (constant-time!)
alice_shared = alice_sk.exchange(ec.ECDH(), bob_pk)
bob_shared = bob_sk.exchange(ec.ECDH(), alice_pk)

assert alice_shared == bob_shared  # Same shared secret
```

---

## Testing Strategy

### Unit Test Changes

```python
# test_crypto_migration.py
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature

class TestECDSAMigration:
    def test_key_generation_deterministic(self):
        sk = ec.generate_private_key(ec.SECP256R1())
        assert sk.curve.name == 'secp256r1'
        assert sk.key_size == 256
    
    def test_sign_verify_roundtrip(self):
        sk = ec.generate_private_key(ec.SECP256R1())
        vk = sk.public_key()
        message = b'test message'
        
        signature = sk.sign(message, ec.ECDSA(hashes.SHA256()))
        vk.verify(signature, message, ec.ECDSA(hashes.SHA256()))  # No exception
    
    def test_invalid_signature_rejects(self):
        sk1 = ec.generate_private_key(ec.SECP256R1())
        sk2 = ec.generate_private_key(ec.SECP256R1())
        
        message = b'test message'
        signature = sk1.sign(message, ec.ECDSA(hashes.SHA256()))
        
        with pytest.raises(InvalidSignature):
            sk2.public_key().verify(signature, message, ec.ECDSA(hashes.SHA256()))
    
    def test_pem_serialization_roundtrip(self):
        sk = ec.generate_private_key(ec.SECP256R1())
        pem = sk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        loaded_sk = serialization.load_pem_private_key(pem, password=None)
        assert loaded_sk.private_numbers() == sk.private_numbers()
```

### Integration Test: Timing Attack Resistance

```python
# test_timing_resistance.py
import time
import statistics
from cryptography.hazmat.primitives.asymmetric import ec, hashes

def test_signing_timing_variance():
    """Verify signing operations have consistent timing (no data-dependent branches)."""
    sk = ec.generate_private_key(ec.SECP256R1())
    
    messages = [
        b'\x00' * 32,  # All zeros
        b'\xff' * 32,  # All ones
        b'0123456789abcdef' * 2,  # Mixed
    ]
    
    timings = []
    for msg in messages:
        times = []
        for _ in range(100):
            start = time.perf_counter_ns()
            sk.sign(msg, ec.ECDSA(hashes.SHA256()))
            end = time.perf_counter_ns()
            times.append(end - start)
        timings.append(statistics.mean(times))
    
    # Coefficient of variation should be < 10% (timing-independent)
    cv = statistics.stdev(timings) / statistics.mean(timings)
    assert cv < 0.10, f"Timing variance too high: {cv:.2%}"
```

---

## Rollback Plan

If issues arise post-migration:

1. **Keep both libraries** during transition:
   ```python
   # Dual import for gradual migration
   try:
       from cryptography.hazmat.primitives.asymmetric import ec  # New code
   except ImportError:
       from ecdsa import SigningKey  # Fallback
   ```

2. **Feature flag the migration**:
   ```python
   USE_CRYPTOGRAPHY = os.environ.get('USE_CRYPTOGRAPHY', 'false').lower() == 'true'
   
   def get_signer():
       if USE_CRYPTOGRAPHY:
           return CryptographySigner()
       else:
           return ECDSASigner()
   ```

3. **A/B test in staging** before production rollout

---

## Performance Comparison

| Operation | ecdsa | cryptography | Notes |
|-----------|-------|--------------|-------|
| Key generation | ~1ms | ~1ms | Equivalent |
| Signing (P-256) | ~0.5ms | ~0.3ms | Faster (OpenSSL) |
| Verification | ~1ms | ~0.8ms | Faster (OpenSSL) |
| Memory | Low | Low | Equivalent |
| Thread safety | ⚠️ No | ✅ Yes | cryptography is thread-safe |

---

## Checklist

### Pre-Migration
- [ ] Audit all `ecdsa` usages in codebase
- [ ] Identify signature format requirements (DER vs raw)
- [ ] Document key serialization formats in use
- [ ] Create test cases for current behavior

### Migration
- [ ] Add `cryptography>=44.0.0` to dependencies
- [ ] Update key generation code
- [ ] Update signing code
- [ ] Update verification code
- [ ] Update serialization code
- [ ] Run unit tests
- [ ] Run integration tests

### Post-Migration
- [ ] Remove `ecdsa` from dependencies
- [ ] Verify no imports remain: `grep -r "ecdsa" --include="*.py" .`
- [ ] Update security documentation
- [ ] Add timing resistance tests to CI

---

## References

- [Minerva Attack Paper](https://eprint.iacr.org/2019/028)
- [python-ecdsa Security Advisory](https://github.com/ecdsa/python-ecdsa/security/advisories)
- [cryptography Documentation](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/)
- [RFC 6979 - Deterministic ECDSA](https://datatracker.ietf.org/doc/html/rfc6979)
- [NIST FIPS 186-4 - ECDSA Standard](https://csrc.nist.gov/publications/detail/fips/186/4/final)