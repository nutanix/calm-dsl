from Crypto.Cipher import AES
import scrypt
import os


# Crypto class for encryption/decryption


class Crypto:

    @staticmethod
    def encrypt_AES_GCM(msg, password):
        """Used for encryption of msg"""

        kdf_salt = os.urandom(16)
        msg = msg.encode()
        secret_key = Crypto.generate_key(kdf_salt, password)
        aes_cipher = AES.new(secret_key, AES.MODE_GCM)
        ciphertext, auth_tag = aes_cipher.encrypt_and_digest(msg)
        iv = aes_cipher.nonce

        return (kdf_salt, ciphertext, iv, auth_tag)

    @staticmethod
    def decrypt_AES_GCM(encryptedMsg, password):
        """Used for decryption of msg"""

        (kdf_salt, ciphertext, iv, auth_tag) = encryptedMsg
        secret_key = scrypt.hash(password, kdf_salt, N=16384, r=8, p=1, buflen=32)
        aes_cipher = AES.new(secret_key, AES.MODE_GCM, iv)
        plaintext = aes_cipher.decrypt_and_verify(ciphertext, auth_tag)

        return plaintext

    @staticmethod
    def generate_key(kdf_salt, password, iterations=16384, r=8, p=1, buflen=32):
        """Generates the key that is used for encryption/decryption"""

        secret_key = scrypt.hash(password, kdf_salt, N=iterations, r=r, p=p, buflen=buflen)
        return secret_key
