from pathlib import Path
from typing import Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def get_rsa_keys(certs_dir: str = "certs") -> Tuple[str, str]:
    """
    Obtiene las claves RSA pública y privada.
    Si no existen en el directorio 'certs', las genera y guarda.
    
    Returns:
        Tuple[str, str]: (private_key_pem, public_key_pem)
    """
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    certs_path = base_dir / certs_dir
    
    private_key_path = certs_path / "private.pem"
    public_key_path = certs_path / "public.pem"
    
    # Si las claves ya existen, leerlas
    if private_key_path.exists() and public_key_path.exists():
        return (
            private_key_path.read_text(encoding="utf-8"),
            public_key_path.read_text(encoding="utf-8")
        )
    
    # Crear directorio si no existe
    certs_path.mkdir(exist_ok=True)
    
    # Generar clave privada
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Serializar clave privada
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Generar clave pública
    public_key = private_key.public_key()
    
    # Serializar clave pública
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Guardar en archivos
    private_key_path.write_bytes(private_pem)
    public_key_path.write_bytes(public_pem)
    
    return private_pem.decode("utf-8"), public_pem.decode("utf-8")