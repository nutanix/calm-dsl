from Crypto.Cipher import AES
import scrypt
import os


# Crypto class for encryption/decryption


class Crypto:
    @staticmethod
    def encrypt_AES_GCM(msg, password, kdf_salt=None, nonce=None):
        """Used for encryption of msg"""

        kdf_salt = kdf_salt or os.urandom(16)
        nonce = nonce or os.urandom(16)

        # Encoding of message
        msg = msg.encode()
        secret_key = Crypto.generate_key(kdf_salt, password)
        aes_cipher = AES.new(secret_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, auth_tag = aes_cipher.encrypt_and_digest(msg)

        return (kdf_salt, ciphertext, nonce, auth_tag)

    @staticmethod
    def decrypt_AES_GCM(encryptedMsg, password, kdf_salt=None, nonce=None):
        """Used for decryption of msg"""

        (stored_kdf_salt, ciphertext, stored_nonce, auth_tag) = encryptedMsg
        kdf_salt = kdf_salt or stored_kdf_salt
        nonce = nonce or stored_nonce

        secret_key = Crypto.generate_key(kdf_salt, password)
        aes_cipher = AES.new(secret_key, AES.MODE_GCM, nonce=nonce)
        plaintext = aes_cipher.decrypt_and_verify(ciphertext, auth_tag)

        # decoding byte data to normal string data
        plaintext = plaintext.decode("utf8")

        return plaintext

    @staticmethod
    def generate_key(kdf_salt, password, iterations=16384, r=8, p=1, buflen=32):
        """Generates the key that is used for encryption/decryption"""

        secret_key = scrypt.hash(
            password, kdf_salt, N=iterations, r=r, p=p, buflen=buflen
        )
        return secret_key
