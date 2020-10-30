# -*- encoding: utf-8 -*-
#%%
from random import randint
import math


class EncryptionKey:
    """
    Iterable class providing infinite looping
    through encoding key
    """

    def __init__(self, key: (str, bytes), encoding="utf-8") -> None:
        """Constructor sets self.key_index to 0
        and self.raw_key to given key str

        Args:
            key (str): key to be used to loop through
        """
        self.key_index = 0
        self.raw_key = key.encode(encoding) if isinstance(key, str) else key
        # store transformed raw_key for encryption
        self.enc_key = b""
        # key length
        length = len(self.raw_key)
        # average of key values
        ave = sum(self.raw_key) // length
        # sum of key values
        keySum = sum(self.raw_key)
        # generate enc key
        for index, char in enumerate(self.raw_key):
            # calclate sinus function to avoid repeating values
            sin = math.sin(index + length) * ave
            # use modulo to keep values in range 0-255
            value = int(char + sin * keySum) % 256
            # append to encoding key
            self.enc_key += int.to_bytes(value, 1, "big")

    def __iter__(self) -> "self":
        """EncryptionKey class is an iterator by itself

        Returns:
            EncryptionKey instance: this instance of EK
        """
        self.key_index = 0
        return self

    def __next__(self) -> str:
        """Iterator __next__ function

        Returns:
            str: self.next()
        """
        return self.next()

    def next(self) -> bytes:
        """Increase and resets key index

        Returns:
            str: single next byte from key
        """
        if not self.enc_key:
            return 0
        else:
            self.key_index = (self.key_index + 1) % len(self.enc_key)
            return self.enc_key[self.key_index]

    def getKey(self) -> str:
        """Simple getter for self.raw_key

        Returns:
            str: raw key bytes
        """
        return self.raw_key

    def reset(self) -> None:
        """Reset iterator key index"""
        self.key_index = 0

    @staticmethod
    def getNewKey(length: int = 16) -> str:
        """Function for generating new random key
        string consisting of ascii characters within
        the range of <33, 127>

        Args:
            length (int, optional): length of key to generate. Defaults to 16.

        Returns:
            str: new string key
        """
        key = ""
        for _ in range(16):
            key += chr(randint(33, 127))
        return key


def encrypt(data: bytes, key: str) -> bytes:
    """Simple encryption of given byte string
    by simply moving forward each byte value
    by n, where n means value for coresponding
    byte of key

    Args:
        data (bytes): data to encode
        key (EncryptionKey): encoding key

    Returns:
        bytes: encoded byte string
    """
    key = EncryptionKey(key)
    assert isinstance(data, bytes)
    for byte, delta in zip(data, key):
        # for each byte in data and each byte in key
        # modulo forces output byte to be in range 0-255
        yield int.to_bytes((byte + delta) % 256, 1, "big")
    return


def decrypt(data: bytes, key: str) -> bytes:
    """Functon applies silmple decryption to given
    byte string

    Args:
        data (bytes): data to decode
        key (EncryptionKey): encoding key

    Returns:
        bytes: decoded output byte string
    """
    key = EncryptionKey(key)
    for byte, delta in zip(data, key):
        # modulo forces output byte to be in range 0-255
        yield int.to_bytes((byte - delta) % 256, 1, "big")
    return


if __name__ == "__main__":
    key = EncryptionKey(EncryptionKey.getNewKey())
    data = b"".join(encrypt("hey", key))
    print(data)
    key.reset()
    print(decrypt(data, key).decode("utf-8"))

# %%
