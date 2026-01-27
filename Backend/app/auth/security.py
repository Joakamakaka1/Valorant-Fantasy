from passlib.context import CryptContext

# Contexto de bcrypt para hasheo de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashea una contraseña en texto plano usando bcrypt.
    
    Bcrypt tiene un límite de 72 bytes para las contraseñas.
    Las contraseñas más largas se truncan automáticamente.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        str: Contraseña hasheada con bcrypt
    """
    # Bcrypt solo puede manejar contraseñas de hasta 72 bytes
    # Truncar correctamente a nivel de bytes para evitar cortar caracteres multibyte
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncar a 72 bytes y decodificar de forma segura (ignorando caracteres incompletos)
        truncated_password = password_bytes[:72].decode('utf-8', errors='ignore')
    else:
        truncated_password = password
    return pwd_context.hash(truncated_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra un hash bcrypt.
    
    Args:
        plain_password: Contraseña en texto plano a verificar
        hashed_password: Hash bcrypt almacenado en la base de datos
        
    Returns:
        bool: True si la contraseña es correcta, False en caso contrario
    """
    # Aplicar el mismo truncamiento que en el hasheo
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        truncated_password = password_bytes[:72].decode('utf-8', errors='ignore')
    else:
        truncated_password = plain_password
    return pwd_context.verify(truncated_password, hashed_password)