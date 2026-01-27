import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

# Configure Cloudinary
cloudinary.config( 
  cloud_name = settings.CLOUDINARY_CLOUD_NAME, 
  api_key = settings.CLOUDINARY_API_KEY, 
  api_secret = settings.CLOUDINARY_API_SECRET,
  secure = True
)

class ImageService:
    
    @staticmethod
    def upload_image(file: UploadFile) -> str:
        """
        Uploads an image to Cloudinary and returns the secure URL.
        Validates the file type before uploading.
        """
        # Validate content type
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not supported. Please upload a valid image (jpeg, png, webp)."
            )
        
        try:
            # Upload to Cloudinary
            # The file.file object is a SpooledTemporaryFile which Cloudinary accepts
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder="aurevia_profiles",  # Optional: organize in a folder
                resource_type="image"
            )
            
            return upload_result.get("secure_url")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Image upload failed: {str(e)}"
            )

image_service = ImageService()