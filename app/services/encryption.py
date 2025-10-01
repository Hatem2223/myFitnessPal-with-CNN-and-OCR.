"""
AES-256 Encryption Service for Document Security
"""
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64

class EncryptionService:
    """Handle AES-256 encryption and decryption of documents"""
    
    def __init__(self, key=None):
        """
        Initialize encryption service
        
        Args:
            key: Base64-encoded 32-byte key. If not provided, uses environment variable.
        """
        if key is None:
            key = os.getenv('ENCRYPTION_KEY')
            if key is None:
                # Generate a new key if none exists (for development only)
                self.key = os.urandom(32)
                print(f"WARNING: Generated new encryption key. Set ENCRYPTION_KEY in .env to: {base64.b64encode(self.key).decode()}")
            else:
                self.key = base64.b64decode(key)
        else:
            self.key = base64.b64decode(key) if isinstance(key, str) else key
        
        if len(self.key) != 32:
            raise ValueError("Encryption key must be 32 bytes (256 bits)")
    
    def encrypt_file(self, file_path, output_path):
        """
        Encrypt a file using AES-256-CBC
        
        Args:
            file_path: Path to the file to encrypt
            output_path: Path where encrypted file will be saved
        
        Returns:
            tuple: (success: bool, encrypted_size: int)
        """
        try:
            # Read the file
            with open(file_path, 'rb') as f:
                plaintext = f.read()
            
            # Generate random IV
            iv = os.urandom(16)
            
            # Pad the plaintext
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext) + padder.finalize()
            
            # Encrypt
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Write IV + ciphertext to output file
            with open(output_path, 'wb') as f:
                f.write(iv + ciphertext)
            
            return True, len(iv + ciphertext)
        
        except Exception as e:
            print(f"Encryption error: {str(e)}")
            return False, 0
    
    def decrypt_file(self, encrypted_path, output_path):
        """
        Decrypt a file using AES-256-CBC
        
        Args:
            encrypted_path: Path to the encrypted file
            output_path: Path where decrypted file will be saved
        
        Returns:
            bool: Success status
        """
        try:
            # Read encrypted file
            with open(encrypted_path, 'rb') as f:
                data = f.read()
            
            # Extract IV and ciphertext
            iv = data[:16]
            ciphertext = data[16:]
            
            # Decrypt
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            return True
        
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return False
    
    def encrypt_bytes(self, data):
        """
        Encrypt bytes and return encrypted bytes
        
        Args:
            data: Bytes to encrypt
        
        Returns:
            bytes: Encrypted data with IV prepended
        """
        # Generate random IV
        iv = os.urandom(16)
        
        # Pad the data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return iv + ciphertext
    
    def decrypt_bytes(self, encrypted_data):
        """
        Decrypt bytes
        
        Args:
            encrypted_data: Encrypted bytes with IV prepended
        
        Returns:
            bytes: Decrypted data
        """
        # Extract IV and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Decrypt
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext
    
    def encrypt_string(self, text):
        """
        Encrypt a string and return base64-encoded result
        
        Args:
            text: String to encrypt
        
        Returns:
            str: Base64-encoded encrypted data
        """
        encrypted = self.encrypt_bytes(text.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_string(self, encrypted_text):
        """
        Decrypt a base64-encoded encrypted string
        
        Args:
            encrypted_text: Base64-encoded encrypted string
        
        Returns:
            str: Decrypted string
        """
        encrypted = base64.b64decode(encrypted_text)
        decrypted = self.decrypt_bytes(encrypted)
        return decrypted.decode('utf-8')

# Global encryption service instance
encryption_service = EncryptionService()
