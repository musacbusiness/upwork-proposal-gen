"""
Image Generation Module - Generate images for LinkedIn posts using Replicate

Uses Replicate's Stable Diffusion models to create professional images that accompany
LinkedIn posts, tailored to the post content and business aesthetic.
"""

import json
import logging
from typing import Dict, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
import base64
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class ImageGenerator:
    """Generate LinkedIn post images using Replicate API"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize image generator
        
        Args:
            api_key: Replicate API token (defaults to REPLICATE_API_TOKEN env var)
        """
        self.api_key = api_key or os.getenv('REPLICATE_API_TOKEN')
        self.base_url = "https://api.replicate.com/v1"
        # Using Google Nano Banana Pro for high-quality business images
        self.model_version = "google/nano-banana-pro"
        self.logger = logger
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024, 
                      negative_prompt: str = None) -> Optional[Dict]:
        """
        Generate an image using Replicate
        
        Args:
            prompt: Detailed image prompt
            width: Image width (default 1024 for SDXL)
            height: Image height (default 1024 for square format)
            negative_prompt: What to avoid in the image
        
        Returns:
            Dict with image URL and metadata, or None if failed
        """
        if not self.api_key:
            self.logger.error("REPLICATE_API_TOKEN not configured")
            return None
        
        try:
            # Enhance prompt for better results
            enhanced_prompt = self._enhance_prompt(prompt)
            
            payload = {
                "version": self.model_version,
                "input": {
                    "prompt": enhanced_prompt,
                    "width": width,
                    "height": height,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "negative_prompt": negative_prompt or "low quality, blurry, distorted, ugly, text, watermark"
                }
            }
            
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self.logger.info(f"Requesting image generation from Replicate")
            
            # Create prediction
            response = requests.post(
                f"{self.base_url}/predictions",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                prediction = response.json()
                prediction_id = prediction.get('id')
                
                # Poll for completion
                self.logger.info(f"Prediction created: {prediction_id}, waiting for completion...")
                image_url = self._wait_for_prediction(prediction_id, headers)
                
                if image_url:
                    image_obj = {
                        "image_url": image_url,
                        "prompt": enhanced_prompt,
                        "generated_at": datetime.now().isoformat(),
                        "width": width,
                        "height": height,
                        "status": "GENERATED"
                    }
                    
                    self.logger.info("Image generated successfully")
                    return image_obj
                else:
                    self.logger.error("Failed to get image URL from prediction")
                    return None
            else:
                self.logger.error(f"Image generation failed: {response.status_code} - {response.text}")
                return None
                
        except requests.Timeout:
            self.logger.error("Image generation request timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error generating image: {e}")
            return None
    
    def _wait_for_prediction(self, prediction_id: str, headers: dict, max_wait: int = 120) -> Optional[str]:
        """
        Poll Replicate API until prediction is complete
        
        Args:
            prediction_id: ID of the prediction to poll
            headers: Request headers with auth
            max_wait: Maximum seconds to wait
        
        Returns:
            Image URL or None if failed/timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/predictions/{prediction_id}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'succeeded':
                        output = result.get('output')
                        if output and isinstance(output, list) and len(output) > 0:
                            return output[0]  # First image URL
                        elif isinstance(output, str):
                            return output
                    elif status == 'failed':
                        self.logger.error(f"Prediction failed: {result.get('error')}")
                        return None
                    
                    # Still processing, wait and retry
                    time.sleep(2)
                else:
                    self.logger.error(f"Error polling prediction: {response.status_code}")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Error polling prediction: {e}")
                return None
        
        self.logger.error("Prediction timed out")
        return None
    
    def _enhance_prompt(self, prompt: str) -> str:
        """
        Enhance prompt for natural, engaging graphics
        
        Creates authentic, non-AI-looking visuals with varied color schemes
        """
        # Remove overly corporate/sterile language
        # Focus on authentic, engaging, editorial-style photography/graphics
        natural_additions = (
            ", photorealistic, natural lighting, authentic feel, "
            "editorial photography style, vibrant and dynamic, "
            "high-end professional photography, depth of field, "
            "cinematic composition, engaging visual storytelling, "
            "magazine quality, contemporary design"
        )
        
        return prompt + natural_additions
    
    def download_image(self, image_url: str, filename: str = None, 
                      output_dir: str = "../.tmp/linkedin_images/") -> str:
        """
        Download image from URL and save to file
        
        Args:
            image_url: URL of the image to download
            filename: Output filename (auto-generated if not provided)
            output_dir: Directory to save images
        
        Returns:
            Path to saved image file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            filename = f"linkedin_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                self.logger.info(f"Downloaded image to {filepath}")
                return filepath
            else:
                self.logger.error(f"Failed to download image: {response.status_code}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error downloading image: {e}")
            return None
    
    def generate_for_post(self, post: Dict, save_locally: bool = True) -> Dict:
        """
        Generate image for a LinkedIn post
        
        Args:
            post: Post object with image_prompt
            save_locally: Whether to save image to disk
        
        Returns:
            Updated post object with image URL/path
        """
        image_prompt = post.get('image_prompt')
        if not image_prompt:
            self.logger.warning("No image prompt provided for post")
            return post
        
        try:
            # Generate image
            image_obj = self.generate_image(image_prompt)
            
            if image_obj:
                image_url = image_obj.get('image_url')
                
                if save_locally and image_url:
                    # Download and save locally
                    filename = f"{post.get('title', 'post')[:30].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    image_path = self.download_image(image_url, filename=filename)
                    
                    if image_path:
                        post['image_local_path'] = image_path
                        post['image_url'] = image_url  # Keep both local and remote
                    else:
                        post['image_url'] = image_url  # Just use remote URL
                else:
                    post['image_url'] = image_url
                
                post['image_generated_at'] = image_obj.get('generated_at')
                post['image_status'] = "READY"
                
                self.logger.info(f"Image generated for post: {post.get('title')}")
            else:
                post['image_status'] = "FAILED"
                self.logger.warning(f"Failed to generate image for post: {post.get('title')}")
            
            return post
            
        except Exception as e:
            self.logger.error(f"Error in generate_for_post: {e}")
            post['image_status'] = "ERROR"
            return post
    
    def generate_batch_images(self, posts: list, save_locally: bool = True) -> list:
        """
        Generate images for multiple posts
        
        Args:
            posts: List of post objects
            save_locally: Whether to save images to disk
        
        Returns:
            Updated posts with image data
        """
        updated_posts = []
        
        for i, post in enumerate(posts):
            self.logger.info(f"Generating image {i+1}/{len(posts)}")
            
            # Add delay between requests to avoid rate limiting
            if i > 0:
                time.sleep(2)
            
            updated_post = self.generate_for_post(post, save_locally=save_locally)
            updated_posts.append(updated_post)
        
        self.logger.info(f"Generated images for {len(updated_posts)} posts")
        return updated_posts
    



if __name__ == "__main__":
    generator = ImageGenerator()
    
    # Test image generation
    test_prompt = "Professional business automation dashboard with AI elements, modern design"
    result = generator.generate_image(test_prompt)
    
    if result:
        print(f"Image generated: {result.get('generated_at')}")
    else:
        print("Image generation failed")
