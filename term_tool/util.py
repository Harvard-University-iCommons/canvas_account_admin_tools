from Crypto.Cipher import AES
import base64
import os

class util():
    @staticmethod
    def encrypt_string(str):

        key = os.environ['CIPHER_KEY']
        encryption_obj = AES.new(key)
        
        mismatch = len(str) % 16
        if mismatch != 0:
            padding = (16 - mismatch) * ' '
            str += padding

        encrypted = encryption_obj.encrypt(str)
        encoded = base64.b64encode(encrypted)
        return encoded

    @staticmethod
    def decrypt_string(str):
        key = os.environ['CIPHER_KEY']
        encryption_obj = AES.new(key)
        
        decoded = base64.b64decode(str)
        decrypted = encryption_obj.decrypt(decoded)
        return decrypted

        
